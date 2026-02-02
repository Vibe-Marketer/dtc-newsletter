#!/usr/bin/env python3
"""
Batch runner orchestrator for Phase 8 manual execution.
DOE-VERSION: 2026.02.02

Orchestrates batch generation of newsletters and products:
1. Discovers trending topics with diversity filter
2. Runs pre-flight API checks
3. Enforces cost budget ($40 max)
4. Wraps existing pipeline_runner and product_factory

Usage:
    python execution/batch_runner.py --check-keys
    python execution/batch_runner.py --discover-only --dry-run
    python execution/batch_runner.py --run-newsletters --dry-run
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

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


# =============================================================================
# E-COM CATEGORIES (from RESEARCH.md)
# =============================================================================

E_COM_CATEGORIES = [
    "shipping_logistics",
    "pricing_margins",
    "conversion_optimization",
    "ads_marketing",
    "inventory_management",
    "customer_retention",
    "product_sourcing",
    "platform_tools",
]

# Keywords for categorizing topics into e-com categories
CATEGORY_KEYWORDS = {
    "shipping_logistics": [
        "ship",
        "shipping",
        "fulfillment",
        "delivery",
        "freight",
        "3pl",
        "warehouse",
        "logistics",
        "package",
        "carrier",
        "usps",
        "fedex",
        "ups",
        "dhl",
    ],
    "pricing_margins": [
        "price",
        "pricing",
        "margin",
        "profit",
        "discount",
        "cost",
        "cogs",
        "markup",
        "revenue",
        "aov",
    ],
    "conversion_optimization": [
        "conversion",
        "checkout",
        "cart",
        "abandon",
        "bounce",
        "landing",
        "cro",
        "a/b",
        "ab test",
        "optimize",
        "funnel",
    ],
    "ads_marketing": [
        "ad",
        "ads",
        "facebook",
        "tiktok",
        "google",
        "instagram",
        "marketing",
        "creative",
        "cpm",
        "cpc",
        "roas",
        "campaign",
        "targeting",
        "audience",
        "ugc",
    ],
    "inventory_management": [
        "inventory",
        "stock",
        "sku",
        "warehouse",
        "reorder",
        "backorder",
        "stockout",
        "moq",
        "lead time",
    ],
    "customer_retention": [
        "retention",
        "churn",
        "loyalty",
        "email",
        "sms",
        "klaviyo",
        "postscript",
        "repeat",
        "ltv",
        "clv",
        "subscriber",
        "lifetime",
    ],
    "product_sourcing": [
        "supplier",
        "sourcing",
        "alibaba",
        "manufacturer",
        "vendor",
        "dropship",
        "wholesale",
        "import",
        "private label",
        "oem",
    ],
    "platform_tools": [
        "shopify",
        "app",
        "plugin",
        "integration",
        "tool",
        "woocommerce",
        "bigcommerce",
        "etsy",
        "amazon seller",
        "fba",
    ],
}


# =============================================================================
# TOPIC CATEGORIZATION
# =============================================================================


def categorize_ecom_topic(topic: str) -> str:
    """
    Classify topic into e-com category using keyword matching.

    Args:
        topic: Topic string (title or description)

    Returns:
        E-com category string (one of E_COM_CATEGORIES)
    """
    topic_lower = topic.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in topic_lower for kw in keywords):
            return category

    # Default to platform_tools if no match
    return "platform_tools"


# =============================================================================
# DIVERSITY FILTER
# =============================================================================


def select_diverse_topics(content: list[dict], count: int = 8) -> list[dict]:
    """
    Select top topics ensuring diversity across e-com sub-areas.

    Algorithm:
    1. Sort by outlier_score descending
    2. Categorize each by e-com sub-area
    3. Select highest from each category first
    4. Fill remaining with next highest overall (allows repeats)

    Args:
        content: List of content dicts with 'title' and 'outlier_score'
        count: Number of topics to select (default: 8)

    Returns:
        List of selected topics with diversity across categories
    """
    if not content:
        return []

    # Categorize all topics
    for item in content:
        title = item.get("title", "")
        item["ecom_category"] = categorize_ecom_topic(title)

    # Sort by outlier_score descending
    sorted_content = sorted(
        content, key=lambda x: x.get("outlier_score", 0), reverse=True
    )

    selected = []
    used_categories = set()

    # First pass: one per category (highest scoring in each)
    for item in sorted_content:
        if item["ecom_category"] not in used_categories:
            selected.append(item)
            used_categories.add(item["ecom_category"])
            if len(selected) >= count:
                break

    # Second pass: fill remaining with next highest overall
    if len(selected) < count:
        for item in sorted_content:
            if item not in selected:
                selected.append(item)
                if len(selected) >= count:
                    break

    return selected


# =============================================================================
# API KEY CHECKS
# =============================================================================


def check_api_keys() -> dict:
    """
    Check required and optional API keys.

    Returns:
        Dict with:
            - ready: bool, True if all required keys present
            - missing_required: list of missing required key names
            - missing_optional: list of missing optional key names
            - available_optional: list of available optional key names
    """
    required = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    }

    optional = {
        "REDDIT_CLIENT_ID": os.getenv("REDDIT_CLIENT_ID"),
        "REDDIT_CLIENT_SECRET": os.getenv("REDDIT_CLIENT_SECRET"),
        "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY"),
        "TUBELAB_API_KEY": os.getenv("TUBELAB_API_KEY"),
        "APIFY_TOKEN": os.getenv("APIFY_TOKEN"),
    }

    missing_required = [k for k, v in required.items() if not v]
    missing_optional = [k for k, v in optional.items() if not v]
    available_optional = [k for k, v in optional.items() if v]

    return {
        "ready": len(missing_required) == 0,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "available_optional": available_optional,
    }


# =============================================================================
# BATCH RUNNER CLASS
# =============================================================================


class BatchRunner:
    """
    Batch orchestrator for Phase 8 execution.

    Coordinates:
    - Topic discovery with diversity filter
    - Pre-flight API checks
    - Cost budget enforcement ($40 max)
    - Newsletter and product batch generation (future plans)
    """

    MAX_BUDGET = 40.0

    def __init__(self, dry_run: bool = False):
        """
        Initialize BatchRunner.

        Args:
            dry_run: If True, simulate operations without API calls
        """
        # Import CostTracker here to avoid circular imports
        from execution.cost_tracker import CostTracker

        self.tracker = CostTracker()
        self.dry_run = dry_run
        self.results = {"newsletters": [], "products": []}

    def discover_topics(self, min_score: float = 3.0, count: int = 8) -> list[dict]:
        """
        Discover trending topics using content_aggregate, then apply diversity filter.

        Args:
            min_score: Minimum outlier score threshold (default: 3.0)
            count: Number of topics to return (default: 8)

        Returns:
            List of topic dicts with outlier_score and ecom_category
        """
        if self.dry_run:
            # Return mock data for dry run
            logger.info("DRY RUN: Returning mock topic data")
            return self._get_mock_topics(count)

        try:
            from execution.content_aggregate import run_aggregation

            # Run aggregation with core sources
            result = run_aggregation(
                sources=["reddit", "youtube"],
                min_score=min_score,
                limit=50,
                save=True,
                show_all=False,
                include_stretch=False,
                skip_dedup=False,
                dedup_weeks=4,
                output_format="both",
            )

            if not result.get("success") or result.get("content_fetched", 0) == 0:
                logger.warning("Content aggregation returned no content")
                return []

            # Load content from JSON file
            json_path = result.get("json_path")
            if not json_path or not Path(json_path).exists():
                logger.warning("No content JSON file available")
                return []

            with open(json_path) as f:
                data = json.load(f)

            content = data.get("contents", [])

            # Filter by minimum score
            filtered = [c for c in content if c.get("outlier_score", 0) >= min_score]

            # Apply diversity filter
            diverse_topics = select_diverse_topics(filtered, count=count)

            logger.info(
                f"Discovered {len(diverse_topics)} diverse topics from {len(filtered)} candidates"
            )
            return diverse_topics

        except Exception as e:
            logger.error(f"Topic discovery failed: {e}")
            return []

    def can_continue(self) -> bool:
        """
        Check if cost budget allows continuing.

        Returns:
            True if current costs are within MAX_BUDGET
        """
        total = self.tracker.get_total()
        return total <= self.MAX_BUDGET

    def run_preflight(self) -> bool:
        """
        Run pre-flight checks.

        Checks:
        1. Required API keys present
        2. Optional keys (with warnings)

        Returns:
            True if all required checks pass
        """
        print("\n" + "=" * 60)
        print("=== Pre-flight Checks ===")
        print("=" * 60)

        api_status = check_api_keys()

        # Required keys
        if api_status["ready"]:
            print("\n[PASS] Required API keys present:")
            print("  - ANTHROPIC_API_KEY: Set")
        else:
            print("\n[FAIL] Missing required API keys:")
            for key in api_status["missing_required"]:
                print(f"  - {key}: MISSING")
            print("\nCannot proceed without required keys.")
            return False

        # Optional keys
        if api_status["available_optional"]:
            print("\n[INFO] Available optional API keys:")
            for key in api_status["available_optional"]:
                print(f"  - {key}: Set")

        if api_status["missing_optional"]:
            print("\n[WARN] Missing optional API keys:")
            for key in api_status["missing_optional"]:
                print(f"  - {key}: Not set (some sources may be unavailable)")

        # Cost budget
        print(f"\n[INFO] Cost budget: ${self.MAX_BUDGET:.2f}")
        print(f"[INFO] Current cost: ${self.tracker.get_total():.2f}")

        print("\n" + "=" * 60)
        print("Pre-flight checks complete.")
        print("=" * 60 + "\n")

        return True

    def _get_mock_topics(self, count: int) -> list[dict]:
        """
        Generate mock topics for dry run testing.

        Args:
            count: Number of mock topics to generate

        Returns:
            List of mock topic dicts
        """
        mock_topics = [
            {
                "title": "TikTok Shop conversion tactics that doubled my store revenue",
                "outlier_score": 5.2,
                "source": "reddit",
                "url": "https://reddit.com/r/ecommerce/mock1",
            },
            {
                "title": "How to negotiate better shipping rates with carriers",
                "outlier_score": 4.8,
                "source": "reddit",
                "url": "https://reddit.com/r/shopify/mock2",
            },
            {
                "title": "Facebook Ads creative testing framework for 2026",
                "outlier_score": 4.5,
                "source": "youtube",
                "url": "https://youtube.com/mock3",
            },
            {
                "title": "Pricing psychology: Why $97 beats $100 every time",
                "outlier_score": 4.2,
                "source": "reddit",
                "url": "https://reddit.com/r/dropship/mock4",
            },
            {
                "title": "Email retention sequences that drive 40% repeat purchases",
                "outlier_score": 3.9,
                "source": "youtube",
                "url": "https://youtube.com/mock5",
            },
            {
                "title": "Finding reliable suppliers on Alibaba: 2026 guide",
                "outlier_score": 3.7,
                "source": "reddit",
                "url": "https://reddit.com/r/ecommerce/mock6",
            },
            {
                "title": "Shopify apps killing your page speed (and conversions)",
                "outlier_score": 3.5,
                "source": "reddit",
                "url": "https://reddit.com/r/shopify/mock7",
            },
            {
                "title": "Inventory management system that saved me $50K",
                "outlier_score": 3.3,
                "source": "youtube",
                "url": "https://youtube.com/mock8",
            },
            {
                "title": "Cart abandonment emails that actually convert",
                "outlier_score": 3.1,
                "source": "reddit",
                "url": "https://reddit.com/r/ecommerce/mock9",
            },
            {
                "title": "Google Shopping feed optimization tips",
                "outlier_score": 3.0,
                "source": "youtube",
                "url": "https://youtube.com/mock10",
            },
        ]

        # Categorize mock topics
        for topic in mock_topics:
            topic["ecom_category"] = categorize_ecom_topic(topic["title"])

        # Apply diversity filter
        return select_diverse_topics(mock_topics[: count * 2], count=count)


# =============================================================================
# CLI INTERFACE
# =============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Batch runner for Phase 8 manual execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check API key status
  python execution/batch_runner.py --check-keys

  # Discover topics (dry run - no API calls)
  python execution/batch_runner.py --discover-only --dry-run

  # Discover topics with live API calls
  python execution/batch_runner.py --discover-only --min-score 3.0

  # Run full preflight checks
  python execution/batch_runner.py --preflight
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operations without API calls",
    )

    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Only discover topics, don't generate content",
    )

    parser.add_argument(
        "--check-keys",
        action="store_true",
        help="Check API key status and exit",
    )

    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run full preflight checks",
    )

    parser.add_argument(
        "--min-score",
        type=float,
        default=3.0,
        help="Minimum outlier score for topic selection (default: 3.0)",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=8,
        help="Number of topics to discover (default: 8)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check keys mode
    if args.check_keys:
        status = check_api_keys()

        print("\n=== API Key Status ===\n")

        if status["ready"]:
            print("[READY] All required keys present\n")
        else:
            print("[NOT READY] Missing required keys\n")

        print("Required:")
        print(
            f"  ANTHROPIC_API_KEY: {'Set' if 'ANTHROPIC_API_KEY' not in status['missing_required'] else 'MISSING'}"
        )

        print("\nOptional:")
        for key in [
            "REDDIT_CLIENT_ID",
            "REDDIT_CLIENT_SECRET",
            "PERPLEXITY_API_KEY",
            "TUBELAB_API_KEY",
            "APIFY_TOKEN",
        ]:
            if key in status["available_optional"]:
                print(f"  {key}: Set")
            else:
                print(f"  {key}: Not set")

        return 0 if status["ready"] else 1

    # Initialize runner
    runner = BatchRunner(dry_run=args.dry_run)

    # Preflight mode
    if args.preflight:
        ready = runner.run_preflight()
        return 0 if ready else 1

    # Discover-only mode
    if args.discover_only:
        print("\n" + "=" * 60)
        print("=== Topic Discovery ===")
        print("=" * 60)
        print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
        print(f"Minimum score: {args.min_score}")
        print(f"Target count: {args.count}")
        print("-" * 60)

        topics = runner.discover_topics(min_score=args.min_score, count=args.count)

        if topics:
            print(f"\nDiscovered {len(topics)} diverse topics:\n")

            # Count categories
            category_counts = {}
            for topic in topics:
                cat = topic.get("ecom_category", "unknown")
                category_counts[cat] = category_counts.get(cat, 0) + 1

            for i, topic in enumerate(topics, 1):
                score = topic.get("outlier_score", 0)
                title = topic.get("title", "No title")[:60]
                category = topic.get("ecom_category", "unknown")
                source = topic.get("source", "unknown")
                print(f"{i}. [{score:.1f}x] [{category}] {title}")
                print(f"   Source: {source}")
                print()

            print("-" * 60)
            print("Category distribution:")
            for cat, count in sorted(category_counts.items()):
                print(f"  {cat}: {count}")
            print(f"\nUnique categories: {len(category_counts)}")
        else:
            print("\nNo topics discovered.")

        print("=" * 60 + "\n")
        return 0

    # Default: show help
    print("Use --help to see available options.")
    print("Common commands:")
    print("  --check-keys     Check API key status")
    print("  --discover-only  Discover trending topics")
    print("  --preflight      Run pre-flight checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
