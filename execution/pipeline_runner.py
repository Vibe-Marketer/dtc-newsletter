#!/usr/bin/env python3
"""
Pipeline runner orchestrator for DTC Newsletter.
DOE-VERSION: 2026.01.31

Main orchestrator that runs the full newsletter pipeline:
1. Content aggregation (Reddit, YouTube, Perplexity)
2. Optional stretch sources (Twitter, TikTok, Amazon)
3. Newsletter generation
4. Affiliate discovery

Features:
- Graceful degradation: continues if sources fail
- Retry with exponential backoff for Claude API calls
- Cost tracking per stage
- Stage announcements for progress

CLI interface for running the complete pipeline.
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any, Callable

# Add parent directory to path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import tenacity for retry with backoff
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Import cost tracking
from execution.cost_tracker import CostTracker, calculate_cost, log_run_cost

# Import output management
from execution.output_manager import (
    save_newsletter,
    get_next_issue_number,
    notify_pipeline_complete,
)


# =============================================================================
# RESULT DATACLASS
# =============================================================================


@dataclass
class PipelineResult:
    """
    Complete pipeline execution result.

    Contains success status, output paths, costs, and any warnings/errors.
    """

    success: bool
    newsletter_path: Optional[Path]
    content_count: int
    costs: dict = field(default_factory=dict)  # stage -> cost
    total_cost: float = 0.0
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)


# =============================================================================
# STAGE ANNOUNCEMENTS
# =============================================================================


def announce(msg: str, quiet: bool = False) -> None:
    """
    Print stage announcement unless quiet mode.

    Args:
        msg: Message to print
        quiet: If True, suppress output
    """
    if not quiet:
        print(msg)


# =============================================================================
# RETRY DECORATOR FOR CLAUDE API CALLS
# =============================================================================


def call_with_retry(func: Callable, *args, **kwargs) -> Any:
    """
    Call a function with retry logic for API errors.

    Retries 3 times with exponential backoff (1s, 2s, 4s) for:
    - openai.APIError
    - openai.APIConnectionError

    Args:
        func: Function to call
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of func(*args, **kwargs)

    Raises:
        Exception after 3 failed attempts
    """
    # Try to get openai exception types
    try:
        import openai

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=4),
            retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError)),
            reraise=True,
        )
        def _call_with_retry():
            return func(*args, **kwargs)

        return _call_with_retry()

    except ImportError:
        # openai not available, call without retry
        return func(*args, **kwargs)


# =============================================================================
# STAGE FUNCTIONS
# =============================================================================


def stage_content_aggregation(
    args: argparse.Namespace,
    tracker: CostTracker,
    quiet: bool = False,
) -> Optional[dict]:
    """
    Stage 1: Content aggregation from core sources.

    Args:
        args: CLI arguments
        tracker: CostTracker for recording costs
        quiet: Suppress output if True

    Returns:
        Dict with content list and topic, or None on failure
    """
    announce("Stage 1: Fetching content from core sources...", quiet)

    try:
        from execution.content_aggregate import run_aggregation

        result = run_aggregation(
            sources=["reddit", "youtube"],
            min_score=2.0,
            limit=50,
            save=True,
            show_all=False,
            include_stretch=args.include_stretch
            if hasattr(args, "include_stretch")
            else False,
            skip_dedup=False,
            dedup_weeks=4,
            output_format="both",
        )

        if result.get("success") and result.get("content_fetched", 0) > 0:
            # Content aggregation doesn't use Claude, so no API cost
            tracker.add_cost("content_aggregation", 0.0)
            announce(
                f"  Content fetched: {result.get('content_fetched', 0)} items",
                quiet,
            )

            # Detect topic from top content
            topic = None
            if result.get("high_outliers", 0) > 0:
                # Try to infer topic from content
                json_path = result.get("json_path")
                if json_path:
                    import json

                    try:
                        with open(json_path) as f:
                            data = json.load(f)
                        if data.get("contents"):
                            top_item = data["contents"][0]
                            topic = top_item.get("title", "")[:50]
                    except Exception:
                        pass

            return {
                "content": result,
                "topic": topic or "dtc-trends",
                "json_path": result.get("json_path"),
            }
        else:
            logger.warning("Content aggregation returned no content")
            tracker.add_cost("content_aggregation", 0.0)
            return None

    except Exception as e:
        logger.error(f"Content aggregation failed: {e}")
        tracker.add_cost("content_aggregation", 0.0)
        return None


def stage_newsletter_generation(
    content_result: dict,
    args: argparse.Namespace,
    tracker: CostTracker,
    quiet: bool = False,
) -> Optional[Any]:
    """
    Stage 2: Newsletter generation from aggregated content.

    Args:
        content_result: Result from stage_content_aggregation
        args: CLI arguments
        tracker: CostTracker for recording costs
        quiet: Suppress output if True

    Returns:
        NewsletterOutput object or None on failure
    """
    if not content_result:
        announce("  Skipping newsletter generation (no content)", quiet)
        return None

    announce("Stage 2: Generating newsletter...", quiet)

    try:
        from execution.newsletter_generator import generate_newsletter
        import json

        # Load content from JSON file
        json_path = content_result.get("json_path")
        if not json_path or not Path(json_path).exists():
            logger.warning("No content JSON file available")
            return None

        with open(json_path) as f:
            data = json.load(f)

        aggregated_content = data.get("contents", [])
        if not aggregated_content:
            logger.warning("No content items in JSON file")
            return None

        # Determine issue number by scanning existing newsletters
        issue_number = get_next_issue_number()

        # Generate newsletter with retry wrapper
        def _generate():
            return generate_newsletter(
                aggregated_content=aggregated_content,
                issue_number=issue_number,
                tool_info=None,  # Will use placeholder
                ps_type=args.ps_type if hasattr(args, "ps_type") else "foreshadow",
            )

        output = call_with_retry(_generate)

        if output:
            # Estimate cost based on typical newsletter generation
            # ~5k input tokens, ~2k output tokens per newsletter
            estimated_cost = (5000 * 3.0 / 1_000_000) + (2000 * 15.0 / 1_000_000)
            warning = tracker.add_cost("newsletter_generation", estimated_cost)
            if warning:
                logger.warning(warning)

            announce(f"  Newsletter generated: Issue #{issue_number}", quiet)
            return output
        else:
            logger.warning("Newsletter generation returned None")
            return None

    except Exception as e:
        logger.error(f"Newsletter generation failed: {e}")
        return None


def stage_affiliate_discovery(
    topic: str,
    tracker: CostTracker,
    quiet: bool = False,
) -> Optional[dict]:
    """
    Stage 3: Affiliate discovery (optional).

    Args:
        topic: Newsletter topic for discovery
        tracker: CostTracker for recording costs
        quiet: Suppress output if True

    Returns:
        Dict with affiliate results or None on failure
    """
    announce("Stage 3: Discovering affiliate opportunities...", quiet)

    try:
        from execution.affiliate_finder import run_monetization_discovery

        output = call_with_retry(
            run_monetization_discovery,
            topic=topic,
            save=True,
            include_rationale=False,
        )

        if output:
            # Estimate cost for affiliate discovery
            # ~3k input tokens, ~1k output tokens
            estimated_cost = (3000 * 3.0 / 1_000_000) + (1000 * 15.0 / 1_000_000)
            warning = tracker.add_cost("affiliate_discovery", estimated_cost)
            if warning:
                logger.warning(warning)

            announce("  Affiliate discovery complete", quiet)
            return {"output": output}
        else:
            logger.warning("Affiliate discovery returned no results")
            return None

    except Exception as e:
        logger.warning(f"Affiliate discovery failed (continuing): {e}")
        return None


# =============================================================================
# MAIN PIPELINE FUNCTION
# =============================================================================


def run_pipeline(
    topic: Optional[str] = None,
    quiet: bool = False,
    verbose: bool = False,
    skip_affiliates: bool = False,
    include_stretch: bool = False,
) -> PipelineResult:
    """
    Run the full newsletter pipeline.

    Stages:
    1. Content aggregation (Reddit, YouTube, Perplexity)
    2. Newsletter generation
    3. Affiliate discovery (optional)

    Each stage has graceful degradation - pipeline continues if sources fail.

    Args:
        topic: Override auto-detected topic
        quiet: Suppress progress output
        verbose: Show debug output
        skip_affiliates: Skip affiliate discovery stage
        include_stretch: Include stretch sources (Twitter, TikTok, Amazon)

    Returns:
        PipelineResult with success status, paths, costs
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    start_time = datetime.now(timezone.utc)
    tracker = CostTracker()
    warnings = []
    errors = []

    announce("=" * 60, quiet)
    announce("=== DTC Newsletter Pipeline ===", quiet)
    announce("=" * 60, quiet)
    announce(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}", quiet)
    announce("-" * 60, quiet)

    # Create args namespace for stage functions
    args = argparse.Namespace()
    args.topic = topic
    args.include_stretch = include_stretch
    args.ps_type = "foreshadow"

    # Stage 1: Content Aggregation
    content_result = stage_content_aggregation(args, tracker, quiet)

    if not content_result:
        errors.append("Content aggregation failed - no content available")
        announce("\nPipeline failed: No content available", quiet)
        return PipelineResult(
            success=False,
            newsletter_path=None,
            content_count=0,
            costs=tracker.to_dict()["costs"],
            total_cost=tracker.get_total(),
            warnings=warnings,
            errors=errors,
        )

    # Use provided topic or auto-detected
    effective_topic = topic or content_result.get("topic", "dtc-trends")
    announce(f"  Topic: {effective_topic}", quiet)

    # Stage 2: Newsletter Generation
    newsletter_output = stage_newsletter_generation(
        content_result, args, tracker, quiet
    )

    newsletter_path = None
    if newsletter_output:
        # Save newsletter using output_manager
        try:
            newsletter_path = save_newsletter(newsletter_output, topic=effective_topic)
            announce(f"  Saved: {newsletter_path}", quiet)
        except Exception as e:
            warnings.append(f"Failed to save newsletter: {e}")
            logger.warning(f"Newsletter save failed: {e}")
    else:
        warnings.append("Newsletter generation failed")

    # Stage 3: Affiliate Discovery (optional)
    if not skip_affiliates:
        affiliate_result = stage_affiliate_discovery(effective_topic, tracker, quiet)
        if not affiliate_result:
            warnings.append("Affiliate discovery failed (non-critical)")

    # Log costs
    announce("\n" + "-" * 60, quiet)
    announce("Cost Summary:", quiet)
    for stage, cost in tracker.to_dict()["costs"].items():
        announce(f"  {stage}: ${cost:.4f}", quiet)
    announce(f"  Total: ${tracker.get_total():.4f}", quiet)

    # Check for cost warnings
    cost_warning = tracker.check_warning()
    if cost_warning:
        announce(f"\n{cost_warning}", quiet)
        warnings.append(cost_warning)

    # Persist costs
    log_run_cost(tracker, "newsletter_pipeline")

    # Calculate content count
    content_count = content_result.get("content", {}).get("content_fetched", 0)

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    announce("\n" + "=" * 60, quiet)
    announce(f"Pipeline complete in {duration:.1f}s", quiet)
    announce("=" * 60, quiet)

    # Determine success
    success = newsletter_path is not None

    # Build result
    result = PipelineResult(
        success=success,
        newsletter_path=newsletter_path,
        content_count=content_count,
        costs=tracker.to_dict()["costs"],
        total_cost=tracker.get_total(),
        warnings=warnings,
        errors=errors,
    )

    # Send notification
    notify_pipeline_complete(result)

    return result


# =============================================================================
# CLI
# =============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the full DTC newsletter pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python execution/pipeline_runner.py

  # Quiet mode (suppress progress)
  python execution/pipeline_runner.py -q

  # Override topic
  python execution/pipeline_runner.py --topic "tiktok shop strategies"

  # Skip affiliate discovery
  python execution/pipeline_runner.py --skip-affiliates

  # Include stretch sources
  python execution/pipeline_runner.py --include-stretch

  # Show what would run (dry run)
  python execution/pipeline_runner.py --dry-run
        """,
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show debug output",
    )

    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Override auto-detected topic",
    )

    parser.add_argument(
        "--skip-affiliates",
        action="store_true",
        help="Skip affiliate discovery stage",
    )

    parser.add_argument(
        "--include-stretch",
        action="store_true",
        help="Include stretch sources (Twitter, TikTok, Amazon)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would run without executing",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Dry run - show what would happen
    if args.dry_run:
        print("\n=== DRY RUN ===\n")
        print("Pipeline would execute the following stages:\n")
        print("1. Content Aggregation")
        print("   - Sources: Reddit, YouTube")
        if args.include_stretch:
            print("   - Stretch sources: Twitter, TikTok, Amazon")
        print("   - Deduplication: 4 weeks lookback")
        print("   - Output: output/content_sheet.json\n")

        print("2. Newsletter Generation")
        print("   - Input: Aggregated content")
        print("   - Sections: 5 (Instant Reward, What's Working, Breakdown, Tool, PS)")
        print("   - Output: output/newsletters/{issue}-{topic}.md\n")

        if not args.skip_affiliates:
            print("3. Affiliate Discovery")
            print("   - Topic-based discovery via Perplexity + Claude")
            print("   - Output: output/monetization/{topic}.md\n")
        else:
            print("3. Affiliate Discovery: SKIPPED\n")

        print("Cost tracking: Enabled")
        print("Cost log: data/cost_log.json\n")
        return 0

    # Run the pipeline
    result = run_pipeline(
        topic=args.topic,
        quiet=args.quiet,
        verbose=args.verbose,
        skip_affiliates=args.skip_affiliates,
        include_stretch=args.include_stretch,
    )

    # Print summary
    if not args.quiet:
        print("\n=== Pipeline Result ===")
        print(f"Success: {result.success}")
        print(f"Content count: {result.content_count}")
        print(f"Total cost: ${result.total_cost:.4f}")

        if result.newsletter_path:
            print(f"Newsletter: {result.newsletter_path}")

        if result.warnings:
            print("\nWarnings:")
            for w in result.warnings:
                print(f"  - {w}")

        if result.errors:
            print("\nErrors:")
            for e in result.errors:
                print(f"  - {e}")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
