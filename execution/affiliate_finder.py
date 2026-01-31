"""
Affiliate discovery and monetization research workflow.
DOE-VERSION: 2026.01.31

Matches directive: directives/affiliate_finder.md

CLI orchestrator that combines affiliate discovery, product alternative
generation, pitch angle creation, and output formatting into a single
workflow for weekly newsletter monetization decisions.
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for direct script execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import modules
from execution.affiliate_discovery import (
    AffiliateProgram,
    AffiliateDiscoveryResult,
    discover_affiliates,
)
from execution.pitch_generator import generate_pitches_batch
from execution.product_alternatives import (
    ProductIdea,
    ProductAlternativesResult,
    generate_product_alternatives,
)
from execution.monetization_output import (
    format_monetization_output,
    save_output,
)

# DOE version for matching
DOE_VERSION = "2026.01.31"

# Default output directory
DEFAULT_OUTPUT_DIR = Path("output/monetization")


def verify_doe_version() -> bool:
    """
    Verify that directive version matches script version.

    Returns:
        True if versions match, False otherwise
    """
    directive_path = Path("directives/affiliate_finder.md")
    if not directive_path.exists():
        logger.warning("Directive file not found: directives/affiliate_finder.md")
        return False

    with open(directive_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for DOE-VERSION in directive
    match = re.search(r"DOE-VERSION:\s*(\d{4}\.\d{2}\.\d{2})", content)
    if not match:
        logger.warning("DOE-VERSION not found in directive")
        return False

    directive_version = match.group(1)
    if directive_version != DOE_VERSION:
        logger.warning(
            f"Version mismatch: script={DOE_VERSION}, directive={directive_version}"
        )
        return False

    return True


def run_monetization_discovery(
    topic: str,
    newsletter_context: str = "",
    save: bool = True,
    output_dir: Optional[Path] = None,
    include_rationale: bool = True,
) -> str:
    """
    Run the full monetization discovery workflow.

    Steps:
    1. Discover affiliates via Perplexity
    2. Generate product alternatives via Perplexity + Claude
    3. Generate pitches for affiliates via Claude
    4. Format combined output
    5. Optionally save to file

    Handles graceful degradation:
    - If <2 affiliates found, adds note recommending product path
    - If Perplexity fails for affiliates, continues with products only
    - If Claude fails for pitches, uses placeholder text

    Args:
        topic: Newsletter topic to find monetization options for
        newsletter_context: Additional context about the newsletter
        save: Whether to save output to file
        output_dir: Custom output directory (default: output/monetization)
        include_rationale: Whether to include ranking rationale

    Returns:
        Formatted markdown output
    """
    output_dir = output_dir or DEFAULT_OUTPUT_DIR

    logger.info(f"Starting monetization discovery for: {topic}")

    # Step 1: Discover affiliates
    affiliates: list[AffiliateProgram] = []
    try:
        logger.info("Discovering affiliate programs...")
        result = discover_affiliates(topic, newsletter_context)
        affiliates = result.affiliates
        logger.info(f"Found {len(affiliates)} affiliate programs")

        if len(affiliates) < 2:
            logger.warning("Few affiliates found. Consider product alternatives.")
    except Exception as e:
        logger.error(f"Affiliate discovery failed: {e}")
        logger.info("Continuing with products only...")

    # Step 2: Generate product alternatives
    products: list[ProductIdea] = []
    try:
        logger.info("Generating product alternatives...")
        product_result = generate_product_alternatives(topic, newsletter_context)
        products = product_result.products
        logger.info(f"Generated {len(products)} product alternatives")
    except Exception as e:
        logger.error(f"Product generation failed: {e}")
        # This is more critical - warn but continue

    # Step 3: Generate pitches for affiliates
    pitches: dict[str, str] = {}
    if affiliates:
        try:
            logger.info("Generating pitch angles...")
            pitches = generate_pitches_batch(affiliates, topic, newsletter_context)
            logger.info(f"Generated {len(pitches)} pitches")
        except Exception as e:
            logger.error(f"Pitch generation failed: {e}")
            logger.info("Using placeholder pitches...")
            # Create placeholder pitches
            for aff in affiliates:
                pitches[aff.name] = f"[Pitch needed for {aff.name}]"

    # Step 4: Format output
    logger.info("Formatting output...")
    output = format_monetization_output(
        affiliates=affiliates,
        products=products,
        topic=topic,
        pitches=pitches,
        include_rationale=include_rationale,
    )

    # Step 5: Save if requested
    if save:
        topic_slug = re.sub(r"[^a-zA-Z0-9]+", "-", topic.lower()).strip("-")
        filepath = save_output(output, topic_slug, output_dir)
        logger.info(f"Output saved to: {filepath}")

    return output


def main() -> int:
    """
    CLI entry point for affiliate finder.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Discover monetization opportunities for newsletter topics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python execution/affiliate_finder.py "email deliverability"
  python execution/affiliate_finder.py "inventory management" --context "This week covers stockouts"
  python execution/affiliate_finder.py "facebook ads" --no-save
  python execution/affiliate_finder.py "shipping" --output-dir custom/output
        """,
    )

    parser.add_argument(
        "topic",
        nargs="?",  # Make optional when using --verify-version
        help="Newsletter topic to find monetization options for",
    )
    parser.add_argument(
        "--context",
        dest="newsletter_context",
        default="",
        help="Additional context about the newsletter content",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save output to file (print only)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Custom output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--no-rationale",
        action="store_true",
        help="Skip ranking rationale generation",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress output",
    )
    parser.add_argument(
        "--verify-version",
        action="store_true",
        help="Verify DOE version match and exit",
    )

    args = parser.parse_args()

    # Handle version verification
    if args.verify_version:
        if verify_doe_version():
            print(f"DOE version verified: {DOE_VERSION}")
            return 0
        else:
            print("DOE version mismatch!")
            return 1

    # Check topic is provided
    if not args.topic:
        parser.error("topic is required unless using --verify-version")

    # Set logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Check for required API keys
    if not os.getenv("PERPLEXITY_API_KEY"):
        logger.error("PERPLEXITY_API_KEY environment variable required")
        return 1

    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable required")
        return 1

    # Run discovery
    try:
        output = run_monetization_discovery(
            topic=args.topic,
            newsletter_context=args.newsletter_context,
            save=not args.no_save,
            output_dir=args.output_dir,
            include_rationale=not args.no_rationale,
        )

        # Print output
        print("\n" + "=" * 60)
        print(output)
        print("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
