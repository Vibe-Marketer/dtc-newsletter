"""
Tests for execution/cost_tracker.py

Tests cover:
- CLAUDE_PRICING values
- calculate_cost() with basic and cache tokens
- CostTracker class functionality
- Cost warning thresholds
- log_run_cost() and get_cumulative_costs()
"""

import json
import pytest
from unittest.mock import MagicMock
from pathlib import Path

from execution.cost_tracker import (
    CLAUDE_PRICING,
    OPERATION_WARNING_THRESHOLD,
    RUN_WARNING_THRESHOLD,
    calculate_cost,
    CostTracker,
    log_run_cost,
    get_cumulative_costs,
    get_run_history,
    COST_LOG_PATH,
)


# =============================================================================
# PRICING TESTS
# =============================================================================


class TestClaudePricing:
    """Tests for CLAUDE_PRICING constant."""

    def test_claude_pricing_has_required_keys(self):
        """Verify pricing dict has all required keys."""
        required_keys = ["input", "output", "cache_read", "cache_write"]
        for key in required_keys:
            assert key in CLAUDE_PRICING, f"Missing key: {key}"

    def test_claude_pricing_values_reasonable(self):
        """Verify pricing values are in reasonable range."""
        # Input should be ~$3/MTok = 0.000003/token
        assert 0.000001 < CLAUDE_PRICING["input"] < 0.00001

        # Output should be ~$15/MTok = 0.000015/token
        assert 0.00001 < CLAUDE_PRICING["output"] < 0.0001

        # Cache read should be 10% of input
        assert CLAUDE_PRICING["cache_read"] < CLAUDE_PRICING["input"]

        # Cache write should be ~1.25x input
        assert CLAUDE_PRICING["cache_write"] > CLAUDE_PRICING["input"]

    def test_claude_pricing_exact_values(self):
        """Verify exact pricing values match Claude Sonnet 4.5."""
        assert CLAUDE_PRICING["input"] == 3.00 / 1_000_000
        assert CLAUDE_PRICING["output"] == 15.00 / 1_000_000
        assert CLAUDE_PRICING["cache_read"] == 0.30 / 1_000_000
        assert CLAUDE_PRICING["cache_write"] == 3.75 / 1_000_000


# =============================================================================
# CALCULATE_COST TESTS
# =============================================================================


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def _make_usage_mock(
        self,
        input_tokens=None,
        output_tokens=None,
        cache_read=None,
        cache_write=None,
    ):
        """Create a usage mock with only the specified attributes."""

        # Use a simple object to avoid MagicMock's auto-attribute creation
        class Usage:
            pass

        usage = Usage()
        if input_tokens is not None:
            usage.input_tokens = input_tokens
        if output_tokens is not None:
            usage.output_tokens = output_tokens
        if cache_read is not None:
            usage.cache_read_input_tokens = cache_read
        if cache_write is not None:
            usage.cache_creation_input_tokens = cache_write
        return usage

    def test_calculate_cost_basic(self):
        """Test cost calculation with basic input/output tokens."""
        # Create usage with only input/output tokens
        usage = self._make_usage_mock(input_tokens=1000, output_tokens=500)

        class Response:
            pass

        response = Response()
        response.usage = usage

        cost = calculate_cost(response)

        # Expected: 1000 * 3/1M + 500 * 15/1M = 0.003 + 0.0075 = 0.0105
        expected = 1000 * CLAUDE_PRICING["input"] + 500 * CLAUDE_PRICING["output"]
        assert cost == pytest.approx(expected)
        assert cost == pytest.approx(0.0105)

    def test_calculate_cost_with_cache_read(self):
        """Test cost calculation with cache read tokens."""
        usage = self._make_usage_mock(
            input_tokens=1000,
            output_tokens=500,
            cache_read=2000,
        )

        class Response:
            pass

        response = Response()
        response.usage = usage

        cost = calculate_cost(response)

        # Expected: base + cache_read
        expected = (
            1000 * CLAUDE_PRICING["input"]
            + 500 * CLAUDE_PRICING["output"]
            + 2000 * CLAUDE_PRICING["cache_read"]
        )
        assert cost == pytest.approx(expected)

    def test_calculate_cost_with_cache_write(self):
        """Test cost calculation with cache creation tokens."""
        usage = self._make_usage_mock(
            input_tokens=1000,
            output_tokens=500,
            cache_write=1500,
        )

        class Response:
            pass

        response = Response()
        response.usage = usage

        cost = calculate_cost(response)

        # Expected: base + cache_write
        expected = (
            1000 * CLAUDE_PRICING["input"]
            + 500 * CLAUDE_PRICING["output"]
            + 1500 * CLAUDE_PRICING["cache_write"]
        )
        assert cost == pytest.approx(expected)

    def test_calculate_cost_with_all_cache_tokens(self):
        """Test cost calculation with both cache read and write tokens."""
        usage = self._make_usage_mock(
            input_tokens=1000,
            output_tokens=500,
            cache_read=2000,
            cache_write=500,
        )

        class Response:
            pass

        response = Response()
        response.usage = usage

        cost = calculate_cost(response)

        expected = (
            1000 * CLAUDE_PRICING["input"]
            + 500 * CLAUDE_PRICING["output"]
            + 2000 * CLAUDE_PRICING["cache_read"]
            + 500 * CLAUDE_PRICING["cache_write"]
        )
        assert cost == pytest.approx(expected)

    def test_calculate_cost_no_usage_attribute(self):
        """Test cost calculation when response has no usage attribute."""

        class Response:
            pass

        response = Response()
        # No usage attribute

        cost = calculate_cost(response)
        assert cost == 0.0

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        usage = self._make_usage_mock(input_tokens=0, output_tokens=0)

        class Response:
            pass

        response = Response()
        response.usage = usage

        cost = calculate_cost(response)
        assert cost == 0.0

    def test_calculate_cost_none_token_values(self):
        """Test cost calculation handles None token values."""

        # Create usage with explicit None values
        class Usage:
            input_tokens = None
            output_tokens = None
            cache_read_input_tokens = None
            cache_creation_input_tokens = None

        class Response:
            usage = Usage()

        cost = calculate_cost(Response())
        assert cost == 0.0


# =============================================================================
# COST TRACKER TESTS
# =============================================================================


class TestCostTracker:
    """Tests for CostTracker class."""

    def test_cost_tracker_init(self):
        """Test CostTracker initialization."""
        tracker = CostTracker()

        assert tracker.run_id is not None
        assert len(tracker.run_id) == 15  # YYYYMMDD-HHMMSS format
        assert tracker.started_at is not None
        assert tracker.get_total() == 0.0

    def test_cost_tracker_add_cost(self):
        """Test adding costs to tracker."""
        tracker = CostTracker()

        tracker.add_cost("stage_1", 0.15)
        tracker.add_cost("stage_2", 0.35)

        assert tracker.get_stage_cost("stage_1") == 0.15
        assert tracker.get_stage_cost("stage_2") == 0.35

    def test_cost_tracker_add_cost_accumulates(self):
        """Test adding multiple costs to same stage accumulates."""
        tracker = CostTracker()

        tracker.add_cost("stage_1", 0.15)
        tracker.add_cost("stage_1", 0.10)

        assert tracker.get_stage_cost("stage_1") == 0.25

    def test_cost_tracker_get_total(self):
        """Test get_total sums all stage costs."""
        tracker = CostTracker()

        tracker.add_cost("stage_1", 0.15)
        tracker.add_cost("stage_2", 0.35)
        tracker.add_cost("stage_3", 0.50)

        assert tracker.get_total() == pytest.approx(1.00)

    def test_cost_tracker_get_stage_cost_not_found(self):
        """Test get_stage_cost returns 0 for unknown stage."""
        tracker = CostTracker()

        assert tracker.get_stage_cost("nonexistent") == 0.0

    def test_cost_tracker_to_dict(self):
        """Test to_dict exports tracker state."""
        tracker = CostTracker()

        tracker.add_cost("stage_1", 0.15)
        tracker.add_cost("stage_2", 0.35)

        result = tracker.to_dict()

        assert "run_id" in result
        assert "started_at" in result
        assert "costs" in result
        assert "total" in result
        assert result["costs"]["stage_1"] == 0.15
        assert result["costs"]["stage_2"] == 0.35
        assert result["total"] == pytest.approx(0.50)


# =============================================================================
# WARNING TESTS
# =============================================================================


class TestCostWarnings:
    """Tests for cost warning functionality."""

    def test_cost_tracker_warning_operation_threshold(self):
        """Test warning returned when operation exceeds threshold."""
        tracker = CostTracker()

        # Add cost above operation threshold ($1)
        warning = tracker.add_cost("expensive_stage", 1.50)

        assert warning is not None
        assert "WARNING" in warning
        assert "expensive_stage" in warning
        assert "$1.50" in warning

    def test_cost_tracker_no_warning_under_operation_threshold(self):
        """Test no warning when operation under threshold."""
        tracker = CostTracker()

        # Add cost below operation threshold
        warning = tracker.add_cost("cheap_stage", 0.50)

        assert warning is None

    def test_cost_tracker_warning_at_exact_threshold(self):
        """Test no warning when operation equals threshold."""
        tracker = CostTracker()

        # Add cost exactly at threshold - should NOT warn
        warning = tracker.add_cost("borderline_stage", OPERATION_WARNING_THRESHOLD)

        assert warning is None

    def test_cost_tracker_warning_run_threshold(self):
        """Test warning returned when run total exceeds threshold."""
        tracker = CostTracker()

        # Add costs totaling above run threshold ($10)
        tracker.add_cost("stage_1", 4.00)
        tracker.add_cost("stage_2", 4.00)
        tracker.add_cost("stage_3", 3.00)  # Total: $11

        warning = tracker.check_warning()

        assert warning is not None
        assert "WARNING" in warning
        assert "$11.00" in warning

    def test_cost_tracker_no_warning_under_run_threshold(self):
        """Test no warning when run total under threshold."""
        tracker = CostTracker()

        tracker.add_cost("stage_1", 2.00)
        tracker.add_cost("stage_2", 2.00)
        tracker.add_cost("stage_3", 2.00)  # Total: $6

        warning = tracker.check_warning()

        assert warning is None


# =============================================================================
# PERSISTENT LOGGING TESTS
# =============================================================================


class TestLogRunCost:
    """Tests for log_run_cost function."""

    def test_log_run_cost_new_file(self, tmp_path, monkeypatch):
        """Test logging to non-existent file creates it."""
        # Override COST_LOG_PATH to use tmp_path
        test_log_path = tmp_path / "cost_log.json"
        monkeypatch.setattr("execution.cost_tracker.COST_LOG_PATH", test_log_path)

        tracker = CostTracker()
        tracker.add_cost("stage_1", 0.15)
        tracker.add_cost("stage_2", 0.35)

        log_run_cost(tracker, "test_workflow")

        # Verify file created
        assert test_log_path.exists()

        # Verify structure
        with open(test_log_path) as f:
            log = json.load(f)

        assert "runs" in log
        assert "cumulative" in log
        assert len(log["runs"]) == 1

        run = log["runs"][0]
        assert run["workflow"] == "test_workflow"
        assert run["total"] == pytest.approx(0.50)
        assert "stage_1" in run["costs"]
        assert "stage_2" in run["costs"]

    def test_log_run_cost_append(self, tmp_path, monkeypatch):
        """Test logging to existing file appends."""
        test_log_path = tmp_path / "cost_log.json"
        monkeypatch.setattr("execution.cost_tracker.COST_LOG_PATH", test_log_path)

        # First run
        tracker1 = CostTracker()
        tracker1.add_cost("stage_1", 0.15)
        log_run_cost(tracker1, "workflow_1")

        # Second run
        tracker2 = CostTracker()
        tracker2.add_cost("stage_1", 0.25)
        log_run_cost(tracker2, "workflow_2")

        # Verify both runs logged
        with open(test_log_path) as f:
            log = json.load(f)

        assert len(log["runs"]) == 2
        assert log["runs"][0]["workflow"] == "workflow_1"
        assert log["runs"][1]["workflow"] == "workflow_2"

    def test_log_run_cost_cumulative_updates(self, tmp_path, monkeypatch):
        """Test cumulative totals update correctly."""
        test_log_path = tmp_path / "cost_log.json"
        monkeypatch.setattr("execution.cost_tracker.COST_LOG_PATH", test_log_path)

        # First run: $0.50
        tracker1 = CostTracker()
        tracker1.add_cost("stage_1", 0.50)
        log_run_cost(tracker1, "workflow_1")

        # Second run: $0.30
        tracker2 = CostTracker()
        tracker2.add_cost("stage_2", 0.30)
        log_run_cost(tracker2, "workflow_2")

        # Verify cumulative
        with open(test_log_path) as f:
            log = json.load(f)

        assert log["cumulative"]["anthropic"] == pytest.approx(0.80)


class TestGetCumulativeCosts:
    """Tests for get_cumulative_costs function."""

    def test_get_cumulative_costs_no_file(self, tmp_path, monkeypatch):
        """Test returns empty dict when file doesn't exist."""
        test_log_path = tmp_path / "nonexistent.json"
        monkeypatch.setattr("execution.cost_tracker.COST_LOG_PATH", test_log_path)

        result = get_cumulative_costs()

        assert result == {}

    def test_get_cumulative_costs_with_data(self, tmp_path, monkeypatch):
        """Test reads cumulative costs from file."""
        test_log_path = tmp_path / "cost_log.json"
        monkeypatch.setattr("execution.cost_tracker.COST_LOG_PATH", test_log_path)

        # Create log file with cumulative data
        log = {"runs": [], "cumulative": {"anthropic": 15.50, "perplexity": 2.00}}
        with open(test_log_path, "w") as f:
            json.dump(log, f)

        result = get_cumulative_costs()

        assert result["anthropic"] == 15.50
        assert result["perplexity"] == 2.00


class TestGetRunHistory:
    """Tests for get_run_history function."""

    def test_get_run_history_no_file(self, tmp_path, monkeypatch):
        """Test returns empty list when file doesn't exist."""
        test_log_path = tmp_path / "nonexistent.json"
        monkeypatch.setattr("execution.cost_tracker.COST_LOG_PATH", test_log_path)

        result = get_run_history()

        assert result == []

    def test_get_run_history_with_data(self, tmp_path, monkeypatch):
        """Test reads run history from file."""
        test_log_path = tmp_path / "cost_log.json"
        monkeypatch.setattr("execution.cost_tracker.COST_LOG_PATH", test_log_path)

        # Create log file with runs
        log = {
            "runs": [
                {"timestamp": "2026-01-30", "workflow": "run_1"},
                {"timestamp": "2026-01-31", "workflow": "run_2"},
            ],
            "cumulative": {},
        }
        with open(test_log_path, "w") as f:
            json.dump(log, f)

        result = get_run_history()

        # Most recent first
        assert len(result) == 2
        assert result[0]["workflow"] == "run_2"
        assert result[1]["workflow"] == "run_1"

    def test_get_run_history_with_limit(self, tmp_path, monkeypatch):
        """Test limit parameter restricts results."""
        test_log_path = tmp_path / "cost_log.json"
        monkeypatch.setattr("execution.cost_tracker.COST_LOG_PATH", test_log_path)

        log = {
            "runs": [
                {"timestamp": "2026-01-28", "workflow": "run_1"},
                {"timestamp": "2026-01-29", "workflow": "run_2"},
                {"timestamp": "2026-01-30", "workflow": "run_3"},
                {"timestamp": "2026-01-31", "workflow": "run_4"},
            ],
            "cumulative": {},
        }
        with open(test_log_path, "w") as f:
            json.dump(log, f)

        result = get_run_history(limit=2)

        assert len(result) == 2
        assert result[0]["workflow"] == "run_4"
        assert result[1]["workflow"] == "run_3"
