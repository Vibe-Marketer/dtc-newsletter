"""
Product Factory - Generate high-value digital products from e-commerce pain points.
DOE-VERSION: 2026.01.31

Usage:
  python execution/product_factory.py --discover  # Find pain points
  python execution/product_factory.py --create --type html_tool --name "Profit Calculator" --problem "..."
"""

import argparse
import json
import logging
import sys
from typing import Optional

from execution.pain_point_miner import (
    search_pain_points,
    categorize_pain_point,
    get_top_pain_points,
    PAIN_SUBREDDITS,
)
from execution.product_packager import ProductPackager
from execution.generators.base_generator import ProductSpec
from execution.claude_client import ClaudeClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Supported product types
PRODUCT_TYPES = [
    "html_tool",
    "automation",
    "gpt_config",
    "sheets",
    "pdf",
    "prompt_pack",
]

# Category to product type suggestions
CATEGORY_PRODUCT_MAP = {
    "shipping": ["automation", "sheets"],
    "inventory": ["automation", "sheets"],
    "conversion": ["html_tool", "gpt_config"],
    "returns": ["automation", "pdf"],
    "pricing": ["html_tool", "sheets"],
    "marketing": ["prompt_pack", "gpt_config"],
    "other": ["pdf", "prompt_pack"],
}


class ProductFactory:
    """
    End-to-end orchestrator for product creation.

    Connects pain point discovery to product generation:
    1. Discover pain points from Reddit (--discover)
    2. Create products from pain points or specs (--create)
    """

    def __init__(
        self,
        claude_client: Optional[ClaudeClient] = None,
        output_dir: str = "output/products",
    ):
        """
        Initialize the product factory.

        Args:
            claude_client: Optional Claude API client for AI-assisted generation.
            output_dir: Directory for product output (default: output/products)
        """
        self.claude_client = claude_client
        self.output_dir = output_dir
        self._packager = ProductPackager(
            claude_client=claude_client,
            output_dir=output_dir,
        )

    def discover_pain_points(self, limit: int = 20) -> list[dict]:
        """
        Discover and rank pain points from Reddit.

        Args:
            limit: Maximum number of pain points to return

        Returns:
            List of pain points with engagement scores and product type suggestions.
            Each dict contains: id, title, body, score, comments, engagement_score,
            url, keyword, subreddit, category, suggested_product_types
        """
        logger.info(f"Discovering top {limit} pain points...")

        # Get pain points with categories
        pain_points = get_top_pain_points(limit=limit)

        # Add suggested product types based on category
        for pp in pain_points:
            pp["suggested_product_types"] = self._suggest_product_types(pp)

        logger.info(f"Found {len(pain_points)} pain points")
        return pain_points

    def create_product(
        self,
        product_type: str,
        solution_name: str,
        problem: str,
        target_audience: str,
        key_benefits: list[str],
    ) -> dict:
        """
        Create a complete product package from specifications.

        Args:
            product_type: Type of product (html_tool, automation, etc.)
            solution_name: Name of the product
            problem: The pain point being solved
            target_audience: Who the product is for
            key_benefits: List of 3-5 key benefits

        Returns:
            Dict with:
                - product_id: Unique identifier
                - path: Path to output directory
                - manifest: Complete manifest dict
                - url: URL if product is hosted (None for files-only)
                - zip_path: Path to downloadable zip

        Raises:
            ValueError: If product_type is not supported
        """
        # Validate product type
        if product_type not in PRODUCT_TYPES:
            valid_types = ", ".join(PRODUCT_TYPES)
            raise ValueError(
                f"Unknown product type: {product_type}. Valid types: {valid_types}"
            )

        logger.info(f"Creating {product_type}: {solution_name}")

        # Create product spec
        spec = ProductSpec(
            problem=problem,
            solution_name=solution_name,
            target_audience=target_audience,
            key_benefits=key_benefits,
            product_type=product_type,
        )

        # Generate product package
        result = self._packager.package(spec)

        logger.info(f"Product created: {result['product_id']}")
        logger.info(f"Output: {result['path']}")

        return result

    def from_pain_point(
        self,
        pain_point: dict,
        product_type: Optional[str] = None,
    ) -> dict:
        """
        Create a product from a discovered pain point.

        Args:
            pain_point: Pain point dict from discover_pain_points()
            product_type: Product type to create (optional, auto-suggested if not provided)

        Returns:
            Dict with product_id, path, manifest, url, zip_path
        """
        # Auto-suggest product type if not provided
        if product_type is None:
            suggested = self._suggest_product_types(pain_point)
            product_type = suggested[0] if suggested else "pdf"
            logger.info(f"Auto-selected product type: {product_type}")

        # Extract problem from pain point
        problem = pain_point.get("title", "")
        if pain_point.get("body"):
            # Include body for more context (first 200 chars)
            body_preview = pain_point["body"][:200]
            problem = f"{problem}\n\nContext: {body_preview}"

        # Generate solution name from title
        title = pain_point.get("title", "Solution")
        # Clean up title for product name
        solution_name = self._generate_solution_name(title, product_type)

        # Default audience and benefits
        target_audience = "E-commerce entrepreneurs"
        key_benefits = [
            "Solves a real problem validated by Reddit engagement",
            "Ready to use immediately",
            "Professional quality deliverables",
        ]

        return self.create_product(
            product_type=product_type,
            solution_name=solution_name,
            problem=problem,
            target_audience=target_audience,
            key_benefits=key_benefits,
        )

    def _suggest_product_types(self, pain_point: dict) -> list[str]:
        """
        Suggest product types based on pain point category and keywords.

        Args:
            pain_point: Pain point dict with category (or will categorize)

        Returns:
            List of suggested product types, best first
        """
        # Get category (may already be set or needs to be computed)
        category = pain_point.get("category")
        if not category:
            category = categorize_pain_point(pain_point)

        # Get suggestions from category map
        suggestions = CATEGORY_PRODUCT_MAP.get(category, CATEGORY_PRODUCT_MAP["other"])

        # Additional keyword-based suggestions
        text = f"{pain_point.get('title', '')} {pain_point.get('body', '')}".lower()

        # Calculator/tool keywords -> html_tool
        if any(kw in text for kw in ["calculator", "calculate", "formula", "roi"]):
            if "html_tool" not in suggestions:
                suggestions = ["html_tool"] + suggestions

        # Automation keywords -> automation
        if any(kw in text for kw in ["automate", "automation", "script", "workflow"]):
            if "automation" not in suggestions:
                suggestions = ["automation"] + suggestions

        # AI/GPT keywords -> gpt_config
        if any(kw in text for kw in ["chatgpt", "gpt", "ai assistant", "ai help"]):
            if "gpt_config" not in suggestions:
                suggestions = ["gpt_config"] + suggestions

        return suggestions

    def _generate_solution_name(self, title: str, product_type: str) -> str:
        """
        Generate a clean solution name from pain point title.

        Args:
            title: Pain point title
            product_type: Type of product being created

        Returns:
            Clean, marketable product name
        """
        # Type-specific suffixes
        type_suffixes = {
            "html_tool": "Calculator",
            "automation": "Automator",
            "gpt_config": "AI Assistant",
            "sheets": "Tracker",
            "pdf": "Framework",
            "prompt_pack": "Prompt Pack",
        }

        # Extract key topic words from title
        # Remove common filler words
        filler_words = {
            "i",
            "my",
            "the",
            "a",
            "an",
            "is",
            "are",
            "with",
            "for",
            "to",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "how",
            "do",
            "can",
            "help",
            "anyone",
            "else",
            "having",
            "issues",
            "problem",
            "struggling",
        }

        words = title.lower().split()
        key_words = [w for w in words if w not in filler_words and len(w) > 2]

        # Take first 2-3 meaningful words
        key_words = key_words[:3]

        # Capitalize and join
        if key_words:
            base_name = " ".join(w.capitalize() for w in key_words)
        else:
            base_name = "E-commerce"

        # Add type-specific suffix
        suffix = type_suffixes.get(product_type, "Solution")

        return f"{base_name} {suffix}"


def main():
    """CLI entry point for Product Factory."""
    parser = argparse.ArgumentParser(
        description="Product Factory - Generate high-value digital products from e-commerce pain points.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover pain points
  python execution/product_factory.py --discover
  python execution/product_factory.py --discover --limit 10
  
  # Create a product
  python execution/product_factory.py --create \\
    --type html_tool \\
    --name "Shopify Profit Calculator" \\
    --problem "E-com owners don't know their true profit margins" \\
    --audience "Shopify store owners doing $10K-100K/mo" \\
    --benefits "Know real profit in 30 seconds,Spot margin leaks,Price confidently"
  
  # Create from pain point file
  python execution/product_factory.py --from-pain-point data/pain_points/conversion.json --type html_tool
        """,
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--discover",
        action="store_true",
        help="Discover pain points from Reddit",
    )
    mode_group.add_argument(
        "--create",
        action="store_true",
        help="Create a product from specifications",
    )
    mode_group.add_argument(
        "--from-pain-point",
        type=str,
        metavar="FILE",
        help="Create product from pain point JSON file",
    )

    # Discovery options
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum pain points to discover (default: 20)",
    )

    # Creation options
    parser.add_argument(
        "--type",
        type=str,
        choices=PRODUCT_TYPES,
        help="Product type to create",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Product name",
    )
    parser.add_argument(
        "--problem",
        type=str,
        help="Problem being solved",
    )
    parser.add_argument(
        "--audience",
        type=str,
        default="E-commerce entrepreneurs",
        help="Target audience (default: E-commerce entrepreneurs)",
    )
    parser.add_argument(
        "--benefits",
        type=str,
        help="Comma-separated list of benefits",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/products",
        help="Output directory for products (default: output/products)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize factory
    try:
        claude_client = ClaudeClient()
    except ValueError as e:
        logger.warning(f"Claude client not available: {e}")
        claude_client = None

    factory = ProductFactory(
        claude_client=claude_client,
        output_dir=args.output_dir,
    )

    # Execute requested mode
    if args.discover:
        # Discovery mode
        pain_points = factory.discover_pain_points(limit=args.limit)

        print(f"\n{'=' * 60}")
        print(f"TOP {len(pain_points)} E-COMMERCE PAIN POINTS")
        print(f"{'=' * 60}\n")

        for i, pp in enumerate(pain_points, 1):
            print(f"{i}. [{pp.get('category', 'other').upper()}] {pp['title'][:70]}...")
            print(
                f"   Engagement: {pp['engagement_score']} (⬆️ {pp['score']} + 💬 {pp['comments']})"
            )
            print(f"   Suggested: {', '.join(pp['suggested_product_types'][:2])}")
            print(f"   URL: {pp['url']}")
            print()

    elif args.create:
        # Creation mode - validate required args
        if not args.type:
            parser.error("--create requires --type")
        if not args.name:
            parser.error("--create requires --name")
        if not args.problem:
            parser.error("--create requires --problem")

        # Parse benefits
        benefits = []
        if args.benefits:
            benefits = [b.strip() for b in args.benefits.split(",")]
        else:
            benefits = ["Solves a real problem", "Ready to use", "Professional quality"]

        result = factory.create_product(
            product_type=args.type,
            solution_name=args.name,
            problem=args.problem,
            target_audience=args.audience,
            key_benefits=benefits,
        )

        print(f"\n{'=' * 60}")
        print("PRODUCT CREATED SUCCESSFULLY")
        print(f"{'=' * 60}\n")
        print(f"Product ID: {result['product_id']}")
        print(f"Type: {args.type}")
        print(f"Name: {args.name}")
        print(f"Path: {result['path']}")
        print(f"Zip: {result['zip_path']}")
        print(f"\nPricing: {result['manifest']['pricing']['price_display']}")
        print(f"Value: {result['manifest']['pricing']['perceived_value']}")
        print()

    elif args.from_pain_point:
        # From pain point file mode
        with open(args.from_pain_point, "r") as f:
            pain_point = json.load(f)

        result = factory.from_pain_point(
            pain_point=pain_point,
            product_type=args.type,
        )

        print(f"\n{'=' * 60}")
        print("PRODUCT CREATED FROM PAIN POINT")
        print(f"{'=' * 60}\n")
        print(f"Product ID: {result['product_id']}")
        print(f"Path: {result['path']}")
        print(f"Zip: {result['zip_path']}")
        print(f"\nPricing: {result['manifest']['pricing']['price_display']}")
        print()


if __name__ == "__main__":
    main()
