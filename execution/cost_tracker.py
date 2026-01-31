"""
Cost tracking module for DTC Newsletter pipeline.
DOE-VERSION: 2026.01.31

Provides cost calculation from Claude API responses, persistent logging,
and warning thresholds for pipeline operations.

Usage:
    from execution.cost_tracker import calculate_cost, log_run_cost, CostTracker

    # Track costs for a pipeline run
    tracker = CostTracker()
    tracker.add_cost("content_aggregate", 0.15)
    tracker.add_cost("newsletter_generate", 0.35)

    # Check for warnings
    warning = tracker.check_warning()
    if warning:
        print(warning)

    # Log to persistent storage
    log_run_cost(tracker, "newsletter_pipeline")
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


# =============================================================================
# PRICING
# =============================================================================

# Claude Sonnet 4.5 pricing (as of 2026-01)
# https://www.anthropic.com/pricing
CLAUDE_PRICING = {
    "input": 3.00 / 1_000_000,  # $3.00 per million tokens
    "output": 15.00 / 1_000_000,  # $15.00 per million tokens
    "cache_read": 0.30 / 1_000_000,  # $0.30 per million (10% of input)
    "cache_write": 3.75 / 1_000_000,  # $3.75 per million (1.25x input)
}


# =============================================================================
# THRESHOLDS
# =============================================================================

# Warn if single operation costs more than this
OPERATION_WARNING_THRESHOLD = 1.00  # $1.00

# Warn if total run costs more than this
RUN_WARNING_THRESHOLD = 10.00  # $10.00


# =============================================================================
# COST LOG PATH
# =============================================================================

COST_LOG_PATH = Path("data/cost_log.json")


# =============================================================================
# COST CALCULATION
# =============================================================================


def calculate_cost(response: Any) -> float:
    """
    Calculate cost from Claude API response.

    Extracts token counts from response.usage and calculates total cost
    based on CLAUDE_PRICING.

    Args:
        response: Claude API response object with .usage attribute

    Returns:
        Total cost in USD as float

    Example:
        response = client.messages.create(...)
        cost = calculate_cost(response)
        print(f"This call cost ${cost:.4f}")
    """
    if not hasattr(response, "usage"):
        return 0.0

    usage = response.usage
    cost = 0.0

    # Input tokens
    if hasattr(usage, "input_tokens"):
        cost += (usage.input_tokens or 0) * CLAUDE_PRICING["input"]

    # Output tokens
    if hasattr(usage, "output_tokens"):
        cost += (usage.output_tokens or 0) * CLAUDE_PRICING["output"]

    # Cache read tokens (if present)
    if hasattr(usage, "cache_read_input_tokens"):
        cost += (usage.cache_read_input_tokens or 0) * CLAUDE_PRICING["cache_read"]

    # Cache write/creation tokens (if present)
    if hasattr(usage, "cache_creation_input_tokens"):
        cost += (usage.cache_creation_input_tokens or 0) * CLAUDE_PRICING["cache_write"]

    return cost


# =============================================================================
# COST TRACKER CLASS
# =============================================================================


class CostTracker:
    """
    Track costs across a pipeline run.

    Maintains per-stage costs and provides warnings when thresholds exceeded.

    Example:
        tracker = CostTracker()
        tracker.add_cost("stage_1", 0.15)
        tracker.add_cost("stage_2", 0.35)

        total = tracker.get_total()  # 0.50
        warning = tracker.check_warning()  # None if under thresholds

        # Log when run completes
        log_run_cost(tracker, "my_workflow")
    """

    def __init__(self):
        """Initialize with empty costs dict and generate run_id from timestamp."""
        self._costs: dict[str, float] = {}
        self._run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self._started_at = datetime.now().isoformat()

    @property
    def run_id(self) -> str:
        """Get the unique run identifier."""
        return self._run_id

    @property
    def started_at(self) -> str:
        """Get the run start timestamp."""
        return self._started_at

    def add_cost(self, stage: str, cost: float) -> Optional[str]:
        """
        Add cost for a pipeline stage.

        Args:
            stage: Name of the stage (e.g., "content_aggregate", "newsletter_generate")
            cost: Cost in USD

        Returns:
            Warning message if operation exceeds threshold, None otherwise
        """
        if stage in self._costs:
            self._costs[stage] += cost
        else:
            self._costs[stage] = cost

        # Check operation threshold
        if cost > OPERATION_WARNING_THRESHOLD:
            return (
                f"WARNING: Operation '{stage}' cost ${cost:.2f} "
                f"(exceeds ${OPERATION_WARNING_THRESHOLD:.2f} threshold)"
            )

        return None

    def get_stage_cost(self, stage: str) -> float:
        """
        Get cost for a specific stage.

        Args:
            stage: Name of the stage

        Returns:
            Cost in USD, or 0.0 if stage not found
        """
        return self._costs.get(stage, 0.0)

    def get_total(self) -> float:
        """
        Get total cost across all stages.

        Returns:
            Sum of all stage costs in USD
        """
        return sum(self._costs.values())

    def check_warning(self) -> Optional[str]:
        """
        Check if any cost thresholds exceeded.

        Returns:
            Warning message if thresholds exceeded, None otherwise
        """
        total = self.get_total()

        if total > RUN_WARNING_THRESHOLD:
            return (
                f"WARNING: Total run cost ${total:.2f} "
                f"(exceeds ${RUN_WARNING_THRESHOLD:.2f} threshold)"
            )

        return None

    def to_dict(self) -> dict:
        """
        Export tracker state as dictionary for logging.

        Returns:
            Dict with run_id, started_at, costs, and total
        """
        return {
            "run_id": self._run_id,
            "started_at": self._started_at,
            "costs": self._costs.copy(),
            "total": self.get_total(),
        }


# =============================================================================
# PERSISTENT LOGGING
# =============================================================================


def log_run_cost(tracker: CostTracker, workflow: str) -> None:
    """
    Persist run costs to data/cost_log.json.

    Creates file if it doesn't exist. Appends run entry and updates
    cumulative totals per service.

    Args:
        tracker: CostTracker instance with run costs
        workflow: Name of the workflow (e.g., "newsletter_pipeline")

    File structure:
        {
            "runs": [
                {
                    "timestamp": "2026-01-31T10:30:00",
                    "run_id": "20260131-103000",
                    "workflow": "newsletter_pipeline",
                    "costs": {"stage_1": 0.15, "stage_2": 0.35},
                    "total": 0.50
                },
                ...
            ],
            "cumulative": {
                "anthropic": 15.50,
                ...
            }
        }
    """
    # Ensure parent directory exists
    COST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load existing log or create new structure
    if COST_LOG_PATH.exists():
        with open(COST_LOG_PATH, "r") as f:
            log = json.load(f)
    else:
        log = {"runs": [], "cumulative": {}}

    # Create run entry
    tracker_data = tracker.to_dict()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "run_id": tracker_data["run_id"],
        "workflow": workflow,
        "costs": tracker_data["costs"],
        "total": tracker_data["total"],
    }

    # Append to runs
    log["runs"].append(entry)

    # Update cumulative - sum all stage costs under "anthropic" service
    # (all our costs are Claude API costs)
    total_cost = tracker_data["total"]
    log["cumulative"]["anthropic"] = (
        log["cumulative"].get("anthropic", 0.0) + total_cost
    )

    # Write back with nice formatting
    with open(COST_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def get_cumulative_costs() -> dict:
    """
    Read cumulative costs from log file.

    Returns:
        Dict of service -> total cost, or empty dict if file doesn't exist
    """
    if not COST_LOG_PATH.exists():
        return {}

    with open(COST_LOG_PATH, "r") as f:
        log = json.load(f)

    return log.get("cumulative", {})


def get_run_history(limit: Optional[int] = None) -> list[dict]:
    """
    Get run history from log file.

    Args:
        limit: Maximum number of runs to return (most recent first).
               None returns all runs.

    Returns:
        List of run entries, most recent first
    """
    if not COST_LOG_PATH.exists():
        return []

    with open(COST_LOG_PATH, "r") as f:
        log = json.load(f)

    runs = log.get("runs", [])

    # Return most recent first
    runs = list(reversed(runs))

    if limit is not None:
        runs = runs[:limit]

    return runs
