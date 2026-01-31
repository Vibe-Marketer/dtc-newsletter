#!/usr/bin/env python3
"""
Stretch sources orchestrator for DTC Newsletter.
DOE-VERSION: 2026.01.31

Runs Twitter, TikTok, and Amazon aggregators with graceful degradation.
Continues pipeline even if some sources fail.
"""

import argparse
import os
import sys
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

# Add parent directory to path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_source_safely(name: str, fetch_fn: Callable) -> dict:
    """
    Run a source fetch with error isolation.

    Args:
        name: Source name for logging
        fetch_fn: Function that returns aggregation result dict

    Returns:
        Result dict with source name added
    """
    try:
        result = fetch_fn()
        return {
            "source": name,
            **result,
        }
    except Exception as e:
        logger.error(f"{name} failed: {e}")
        return {
            "source": name,
            "success": False,
            "items": [],
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def run_all_stretch_sources(
    min_twitter_score: float = 2.0,
    min_tiktok_score: float = 1.5,
    min_amazon_score: float = 1.0,
    parallel: bool = True,
) -> dict:
    """
    Run all stretch sources and collect results.

    Args:
        min_twitter_score: Twitter minimum outlier score
        min_tiktok_score: TikTok minimum outlier score
        min_amazon_score: Amazon minimum outlier score
        parallel: Whether to run sources in parallel

    Returns:
        Dict with results from each source and aggregate stats
    """
    # Import here to avoid circular deps and allow graceful failure
    try:
        from execution.twitter_aggregate import run_twitter_aggregation
    except ImportError:
        run_twitter_aggregation = None
        logger.warning("twitter_aggregate not available")

    try:
        from execution.tiktok_aggregate import run_tiktok_aggregation
    except ImportError:
        run_tiktok_aggregation = None
        logger.warning("tiktok_aggregate not available")

    try:
        from execution.amazon_aggregate import run_amazon_aggregation
    except ImportError:
        run_amazon_aggregation = None
        logger.warning("amazon_aggregate not available")

    # Define source runners
    sources = []
    if run_twitter_aggregation:
        sources.append(
            ("twitter", lambda: run_twitter_aggregation(min_score=min_twitter_score))
        )
    if run_tiktok_aggregation:
        sources.append(
            ("tiktok", lambda: run_tiktok_aggregation(min_score=min_tiktok_score))
        )
    if run_amazon_aggregation:
        sources.append(
            ("amazon", lambda: run_amazon_aggregation(min_score=min_amazon_score))
        )

    if not sources:
        return {
            "success": False,
            "error": "No stretch source modules available",
            "sources_succeeded": [],
            "sources_failed": [],
            "items": [],
        }

    results = {}

    if parallel and len(sources) > 1:
        # Run in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(run_source_safely, name, fn): name
                for name, fn in sources
            }
            for future in as_completed(futures):
                name = futures[future]
                results[name] = future.result()
    else:
        # Run sequentially
        for name, fn in sources:
            results[name] = run_source_safely(name, fn)

    # Aggregate stats
    succeeded = [name for name, r in results.items() if r.get("success")]
    failed = [name for name, r in results.items() if not r.get("success")]

    # Merge all items
    all_items = []
    for name, result in results.items():
        for item in result.get("items", []):
            item["stretch_source"] = name
            all_items.append(item)

    # Sort by outlier score
    all_items.sort(key=lambda x: x.get("outlier_score", 0), reverse=True)

    return {
        "success": len(succeeded) > 0,  # Success if at least one source worked
        "sources_succeeded": succeeded,
        "sources_failed": failed,
        "results": results,
        "items": all_items,
        "total_items": len(all_items),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def merge_stretch_results(
    stretch_result: dict,
    core_items: list[dict],
    stretch_weight: float = 0.8,
) -> list[dict]:
    """
    Merge stretch source items with core source items.

    Stretch items get slightly lower weight since they're less reliable.

    Args:
        stretch_result: Result from run_all_stretch_sources
        core_items: Items from core sources (Reddit, YouTube, etc.)
        stretch_weight: Score multiplier for stretch items (default 0.8)

    Returns:
        Combined list sorted by adjusted outlier score
    """
    combined = []

    # Add core items with source tag
    for item in core_items:
        item["is_stretch"] = False
        combined.append(item)

    # Add stretch items with weight adjustment
    for item in stretch_result.get("items", []):
        item["is_stretch"] = True
        # Adjust score but preserve original
        item["original_outlier_score"] = item.get("outlier_score", 0)
        item["outlier_score"] = item.get("outlier_score", 0) * stretch_weight
        combined.append(item)

    # Sort by outlier score
    combined.sort(key=lambda x: x.get("outlier_score", 0), reverse=True)

    return combined


def run_stretch_aggregation() -> dict:
    """
    Main entry point for stretch aggregation.

    Returns:
        Aggregation result dict
    """
    start_time = datetime.now(timezone.utc)

    print("\n" + "=" * 50)
    print("=== Stretch Sources Aggregation ===")
    print("=" * 50)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("-" * 50)

    result = run_all_stretch_sources()

    print("\n" + "-" * 50)
    print("Summary:")
    print(f"  Sources succeeded: {', '.join(result['sources_succeeded']) or 'none'}")
    print(f"  Sources failed: {', '.join(result['sources_failed']) or 'none'}")
    print(f"  Total items: {result['total_items']}")

    if result["items"]:
        print(f"\nTop 10 across all stretch sources:")
        for i, item in enumerate(result["items"][:10], 1):
            score = item.get("outlier_score", 0)
            source = item.get("stretch_source", "?")
            # Get title/text based on source
            if source == "twitter":
                text = (item.get("text") or "")[:60]
            elif source == "tiktok":
                text = (item.get("desc") or "")[:60]
            elif source == "amazon":
                text = (item.get("title") or "")[:60]
            else:
                text = "Unknown"
            if len(text) == 60:
                text += "..."
            print(f"  {i}. [{source}] [{score:.1f}x] {text}")

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    print(f"\nCompleted in {duration:.1f}s")
    print("=" * 50)

    return {
        **result,
        "duration_seconds": duration,
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Aggregate content from all stretch sources (Twitter, TikTok, Amazon)"
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run sources sequentially instead of parallel",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    result = run_stretch_aggregation()

    # Log what worked/failed for learnings
    if result["sources_failed"]:
        print(f"\nNote: Failed sources: {result['sources_failed']}")
        print("Check .env for APIFY_TOKEN and API quotas.")

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
