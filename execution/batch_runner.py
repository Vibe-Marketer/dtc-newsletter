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

# Import pipeline and validation modules
from execution.pipeline_runner import run_pipeline
from execution.anti_pattern_validator import validate_voice
from execution.product_factory import ProductFactory
from execution.generators.base_generator import ProductSpec

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# NEWSLETTER VALIDATION
# =============================================================================


def validate_newsletter(path: Path) -> dict:
    """
    Full quality validation per CONTEXT.md.

    Validation stages:
    1. Anti-pattern check (no forbidden phrases)
    2. Structural check (5 sections present)
    3. Quality gate (at least 2 concrete numbers)

    Args:
        path: Path to newsletter markdown file

    Returns:
        Dict with:
            - is_valid: bool
            - violations: list of violation descriptions
            - stage: which stage passed/failed ("anti_pattern", "structure", "quality", "passed")
    """
    content = path.read_text()

    # 1. Anti-pattern check
    is_valid, violations = validate_voice(content)
    if not is_valid:
        return {"is_valid": False, "violations": violations, "stage": "anti_pattern"}

    # 2. Structural check - look for section markers or significant content blocks
    # Newsletters have 5 sections: Instant Reward, What's Working Now, The Breakdown, Tool of the Week, PS
    # They're separated by double newlines and often have headers
    sections = [s for s in content.split("\n\n") if s.strip()]
    if len(sections) < 5:
        return {
            "is_valid": False,
            "violations": [f"Only {len(sections)} sections found, need at least 5"],
            "stage": "structure",
        }

    # 3. Quality gate - concrete numbers ($ amounts, percentages)
    has_dollar = "$" in content
    has_percent = "%" in content
    has_digits = any(char.isdigit() for char in content)

    number_indicators = sum([has_dollar, has_percent, has_digits])
    if number_indicators < 2:
        return {
            "is_valid": False,
            "violations": [
                f"Only {number_indicators} number indicators found, need at least 2"
            ],
            "stage": "quality",
        }

    return {"is_valid": True, "violations": [], "stage": "passed"}


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
# PRODUCT TYPE DISTRIBUTION (per CONTEXT.md)
# =============================================================================

# Product type distribution - prioritize hard stuff (html_tool, automation) first
PRODUCT_TYPE_DISTRIBUTION = [
    "html_tool",  # Week 1
    "automation",  # Week 2
    "html_tool",  # Week 3
    "automation",  # Week 4
    "html_tool",  # Week 5 (5th hard product)
    "gpt_config",  # Week 6
    "sheets",  # Week 7
    "prompt_pack",  # Week 8
]

# Fallback types if primary fails
PRODUCT_TYPE_FALLBACKS = {
    "html_tool": ["automation", "sheets"],
    "automation": ["html_tool", "prompt_pack"],
    "gpt_config": ["prompt_pack", "sheets"],
    "sheets": ["pdf", "prompt_pack"],
    "prompt_pack": ["gpt_config", "pdf"],
    "pdf": ["prompt_pack", "sheets"],
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

    def generate_newsletters(self, topics: list[dict]) -> list[dict]:
        """
        Generate 8 newsletters from topics.

        For each topic:
        1. Run pipeline_runner with topic
        2. Validate output (anti-pattern, structure, quality)
        3. If fails: log and continue (don't block batch)
        4. Track cost and check budget

        Args:
            topics: List of topic dicts with 'title' field

        Returns:
            List of result dicts per newsletter with:
            - week: int (1-8)
            - topic: str
            - path: str (if success)
            - status: "success" | "validation_failed" | "failed" | "error" | "dry_run"
            - cost: float
            - violations: list (if validation_failed)
            - errors: list (if failed)
            - error: str (if error)
        """
        results = []

        for i, topic_data in enumerate(topics, 1):
            topic = topic_data.get("title") or topic_data.get("topic", "Unknown")
            print(f"\n[{i}/{len(topics)}] Generating newsletter: {topic[:50]}...")

            # Budget check
            if not self.can_continue():
                print(f"  STOP: Budget exceeded (${self.tracker.get_total():.2f})")
                break

            # Dry run mode
            if self.dry_run:
                results.append(
                    {
                        "week": i,
                        "topic": topic,
                        "path": f"output/newsletters/mock-{i}.md",
                        "status": "dry_run",
                        "cost": 0.0,
                    }
                )
                print(f"  [DRY RUN] Would generate newsletter for: {topic[:40]}")
                continue

            try:
                # Run the pipeline
                result = run_pipeline(topic=topic, quiet=True, skip_affiliates=True)

                if result.success and result.newsletter_path:
                    # Validate the generated newsletter
                    validation = validate_newsletter(result.newsletter_path)

                    if validation["is_valid"]:
                        results.append(
                            {
                                "week": i,
                                "topic": topic,
                                "path": str(result.newsletter_path),
                                "status": "success",
                                "cost": result.total_cost,
                            }
                        )
                        print(f"  [SUCCESS] Saved to: {result.newsletter_path}")
                    else:
                        results.append(
                            {
                                "week": i,
                                "topic": topic,
                                "path": str(result.newsletter_path),
                                "status": "validation_failed",
                                "violations": validation["violations"],
                                "stage": validation["stage"],
                                "cost": result.total_cost,
                            }
                        )
                        print(f"  [VALIDATION FAILED] Stage: {validation['stage']}")
                        for v in validation["violations"]:
                            print(f"    - {v}")
                else:
                    results.append(
                        {
                            "week": i,
                            "topic": topic,
                            "status": "failed",
                            "errors": result.errors,
                            "cost": result.total_cost,
                        }
                    )
                    print(f"  [FAILED] Pipeline errors:")
                    for err in result.errors:
                        print(f"    - {err}")

                # Update cost tracker
                self.tracker.add_cost("newsletter", result.total_cost)

            except Exception as e:
                results.append(
                    {
                        "week": i,
                        "topic": topic,
                        "status": "error",
                        "error": str(e),
                        "cost": 0.0,
                    }
                )
                print(f"  [ERROR] Exception: {e}")

        self.results["newsletters"] = results
        return results

    def save_status(self, filepath: Optional[Path] = None) -> Path:
        """
        Save batch status to JSON file.

        Args:
            filepath: Custom path (default: .tmp/batch_status.json)

        Returns:
            Path to saved status file
        """
        if filepath is None:
            filepath = Path(".tmp/batch_status.json")

        filepath.parent.mkdir(parents=True, exist_ok=True)

        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_cost": self.tracker.get_total(),
            "budget": self.MAX_BUDGET,
            "dry_run": self.dry_run,
            "newsletters": self.results.get("newsletters", []),
            "products": self.results.get("products", []),
        }

        with open(filepath, "w") as f:
            json.dump(status, f, indent=2)

        logger.info(f"Status saved to {filepath}")
        return filepath

    def load_topics(self, filepath: Optional[Path] = None) -> list[dict]:
        """
        Load topics from JSON file.

        Args:
            filepath: Custom path (default: .tmp/topics.json)

        Returns:
            List of topic dicts
        """
        if filepath is None:
            filepath = Path(".tmp/topics.json")

        if not filepath.exists():
            logger.warning(f"Topics file not found: {filepath}")
            return []

        with open(filepath) as f:
            data = json.load(f)

        return data.get("topics", data) if isinstance(data, dict) else data

    def save_topics(self, topics: list[dict], filepath: Optional[Path] = None) -> Path:
        """
        Save topics to JSON file.

        Args:
            topics: List of topic dicts
            filepath: Custom path (default: .tmp/topics.json)

        Returns:
            Path to saved topics file
        """
        if filepath is None:
            filepath = Path(".tmp/topics.json")

        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(topics),
            "topics": topics,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(topics)} topics to {filepath}")
        return filepath


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

    parser.add_argument(
        "--generate-newsletters",
        action="store_true",
        help="Generate newsletters from discovered or saved topics",
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show batch status from saved state",
    )

    parser.add_argument(
        "--topics-file",
        type=str,
        default=None,
        help="Path to topics JSON file (default: .tmp/topics.json)",
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

        # Save topics if discovered
        if topics:
            runner.save_topics(topics)
            print(f"Topics saved to .tmp/topics.json")

        return 0

    # Status mode
    if args.status:
        status_path = Path(".tmp/batch_status.json")
        if not status_path.exists():
            print("\nNo batch status found. Run --generate-newsletters first.")
            return 1

        with open(status_path) as f:
            status = json.load(f)

        print("\n" + "=" * 60)
        print("=== Batch Status ===")
        print("=" * 60)
        print(f"Timestamp: {status.get('timestamp', 'Unknown')}")
        print(
            f"Total cost: ${status.get('total_cost', 0):.2f} / ${status.get('budget', 40):.2f}"
        )
        print(f"Dry run: {status.get('dry_run', False)}")
        print("-" * 60)

        newsletters = status.get("newsletters", [])
        if newsletters:
            print(f"\nNewsletters: {len(newsletters)}")
            success_count = sum(1 for n in newsletters if n.get("status") == "success")
            failed_count = sum(
                1 for n in newsletters if n.get("status") in ["failed", "error"]
            )
            validation_failed = sum(
                1 for n in newsletters if n.get("status") == "validation_failed"
            )

            print(f"  Success: {success_count}")
            print(f"  Validation failed: {validation_failed}")
            print(f"  Failed/Error: {failed_count}")
            print()

            for n in newsletters:
                status_str = n.get("status", "unknown")
                topic = n.get("topic", "Unknown")[:40]
                week = n.get("week", 0)

                if status_str == "success":
                    print(f"  {week}. [OK] {topic}")
                    print(f"       Path: {n.get('path')}")
                elif status_str == "validation_failed":
                    print(f"  {week}. [VALIDATION] {topic}")
                    print(f"       Stage: {n.get('stage')}")
                    for v in n.get("violations", []):
                        print(f"       - {v}")
                elif status_str == "failed":
                    print(f"  {week}. [FAILED] {topic}")
                    for e in n.get("errors", []):
                        print(f"       - {e}")
                elif status_str == "error":
                    print(f"  {week}. [ERROR] {topic}")
                    print(f"       - {n.get('error')}")
                else:
                    print(f"  {week}. [{status_str.upper()}] {topic}")
                print()
        else:
            print("\nNo newsletters generated yet.")

        print("=" * 60 + "\n")
        return 0

    # Generate newsletters mode
    if args.generate_newsletters:
        print("\n" + "=" * 60)
        print("=== Newsletter Generation ===")
        print("=" * 60)
        print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
        print(f"Budget: ${runner.MAX_BUDGET:.2f}")
        print("-" * 60)

        # Check API keys first
        if not args.dry_run:
            api_status = check_api_keys()
            if not api_status["ready"]:
                print("\n[ERROR] Missing required API keys:")
                for key in api_status["missing_required"]:
                    print(f"  - {key}")
                return 1

        # Load topics
        topics_path = (
            Path(args.topics_file) if args.topics_file else Path(".tmp/topics.json")
        )
        if topics_path.exists():
            print(f"Loading topics from: {topics_path}")
            topics = runner.load_topics(topics_path)
        else:
            print("No saved topics found. Discovering topics...")
            topics = runner.discover_topics(min_score=args.min_score, count=args.count)
            if topics:
                runner.save_topics(topics)

        if not topics:
            print("\n[ERROR] No topics available for newsletter generation.")
            return 1

        print(f"\nGenerating {len(topics)} newsletters...\n")

        # Generate newsletters
        results = runner.generate_newsletters(topics)

        # Save status
        runner.save_status()

        # Summary
        print("\n" + "=" * 60)
        print("=== Generation Complete ===")
        print("=" * 60)

        success_count = sum(1 for r in results if r.get("status") == "success")
        failed_count = sum(1 for r in results if r.get("status") in ["failed", "error"])
        validation_failed = sum(
            1 for r in results if r.get("status") == "validation_failed"
        )
        dry_run_count = sum(1 for r in results if r.get("status") == "dry_run")

        print(f"Success: {success_count}")
        print(f"Validation failed: {validation_failed}")
        print(f"Failed/Error: {failed_count}")
        if dry_run_count:
            print(f"Dry run: {dry_run_count}")
        print(f"Total cost: ${runner.tracker.get_total():.2f}")
        print(f"\nStatus saved to: .tmp/batch_status.json")
        print("=" * 60 + "\n")

        return 0 if success_count > 0 or dry_run_count > 0 else 1

    # Default: show help
    print("Use --help to see available options.")
    print("Common commands:")
    print("  --check-keys           Check API key status")
    print("  --discover-only        Discover trending topics")
    print("  --preflight            Run pre-flight checks")
    print("  --generate-newsletters Generate newsletters from topics")
    print("  --status               Show batch status")
    return 0


if __name__ == "__main__":
    sys.exit(main())
