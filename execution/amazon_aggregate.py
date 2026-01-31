#!/usr/bin/env python3
"""
Amazon Movers & Shakers aggregator for DTC Newsletter.
DOE-VERSION: 2026.01.31

Fetches trending products from Amazon's Movers & Shakers using Apify.
Tracks velocity to surface products before they go viral on social.
"""

import argparse
import os
import sys
import logging
from datetime import datetime, timezone

# Add parent directory to path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from execution.apify_base import fetch_from_apify, fetch_with_retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Movers & Shakers URLs - category agnostic, track what's moving fastest
MOVERS_URLS = [
    "https://www.amazon.com/gp/movers-and-shakers/",
    "https://www.amazon.com/gp/movers-and-shakers/beauty/",
    "https://www.amazon.com/gp/movers-and-shakers/hpc/",  # Health & Personal Care
    "https://www.amazon.com/gp/movers-and-shakers/sporting-goods/",
    "https://www.amazon.com/gp/movers-and-shakers/home-garden/",
]

AMAZON_ACTOR = "junglee/amazon-bestsellers"


def score_amazon_product(product: dict, category_size: int = 100) -> dict:
    """
    Calculate outlier score for an Amazon product.

    Hybrid scoring:
    - Position score: lower rank = higher score (inverted)
    - Velocity score: percentage gain in sales rank

    Args:
        product: Raw product data from Apify
        category_size: Expected items in category for normalization

    Returns:
        Product dict with outlier_score and metadata added
    """
    # Position in Movers & Shakers (1 = best)
    position = product.get("position", 100)
    if isinstance(position, str):
        position = int(position.replace("#", "").strip() or 100)

    # Sales rank change (e.g., "+1,234%" or "1234%")
    rank_change_str = product.get("rankChange", "0%")
    rank_change = 0
    try:
        # Parse percentage (handle "+1,234%" format)
        clean = rank_change_str.replace("+", "").replace(",", "").replace("%", "")
        rank_change = float(clean) if clean else 0
    except (ValueError, AttributeError):
        pass

    # Position score: top 10 = high score, bottom = low
    position_score = max(0, (category_size - position) / category_size)

    # Velocity score: percentage gain normalized (100% = 1.0, 1000% = 10.0)
    velocity_score = rank_change / 100.0

    # Combined score (velocity-weighted)
    # High velocity + good position = highest score
    outlier_score = (position_score * 0.3) + (velocity_score * 0.7)

    return {
        **product,
        "source": "amazon",
        "outlier_score": round(outlier_score, 2),
        "position": position,
        "rank_change_pct": rank_change,
        "url": product.get("url", ""),
    }


def fetch_amazon_movers(
    category_urls: list[str] | None = None,
) -> list[dict]:
    """
    Fetch Movers & Shakers products via Apify.

    Args:
        category_urls: List of M&S category URLs (defaults to MOVERS_URLS)

    Returns:
        List of scored product dicts
    """
    urls = category_urls or MOVERS_URLS

    logger.info(f"Fetching Amazon Movers & Shakers from {len(urls)} categories")

    run_input = {
        "startUrls": [{"url": url} for url in urls],
    }

    items = fetch_from_apify(AMAZON_ACTOR, run_input)

    # Deduplicate by ASIN and score
    seen_asins = set()
    scored_products = []

    for product in items:
        asin = product.get("asin")
        if asin and asin not in seen_asins:
            seen_asins.add(asin)
            scored = score_amazon_product(product)
            scored_products.append(scored)

    # Sort by outlier score descending
    scored_products.sort(key=lambda x: x.get("outlier_score", 0), reverse=True)

    return scored_products


def run_amazon_aggregation(
    min_score: float = 1.0,
) -> dict:
    """
    Run full Amazon aggregation with graceful degradation.

    Args:
        min_score: Minimum outlier score to include

    Returns:
        Dict with success status, products, and metadata
    """
    start_time = datetime.now(timezone.utc)

    print("\n=== Amazon Movers & Shakers Aggregation ===")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Categories: {len(MOVERS_URLS)}")
    print(f"Minimum outlier score: {min_score}x")
    print("-" * 40)

    result = fetch_with_retry(
        source_name="amazon",
        fetch_fn=fetch_amazon_movers,
        cache_key="amazon_movers_shakers",
    )

    if not result["success"]:
        print(f"\nAmazon fetch failed: {result['error']}")
        print("Pipeline will continue without Amazon data.")
        return result

    products = result["items"]

    # Filter by minimum score
    high_score_products = [
        p for p in products if p.get("outlier_score", 0) >= min_score
    ]

    # Group by category for insight
    categories = set()
    for p in high_score_products:
        cat = p.get("category", "Unknown")
        if cat:
            categories.add(cat)

    print(f"\nFetched: {len(products)} products")
    print(f"Above {min_score}x threshold: {len(high_score_products)}")
    print(f"Categories represented: {len(categories)}")

    if high_score_products:
        print(f"\nTop 5 movers:")
        for i, product in enumerate(high_score_products[:5], 1):
            score = product.get("outlier_score", 0)
            title = (
                (product.get("title") or "")[:50] + "..."
                if len(product.get("title") or "") > 50
                else product.get("title", "")
            )
            change = product.get("rank_change_pct", 0)
            pos = product.get("position", "?")
            print(f"  {i}. [{score:.1f}x] #{pos} (+{change:.0f}%) {title}")

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    print(f"\nCompleted in {duration:.1f}s")
    print("-" * 40)

    return {
        **result,
        "items": high_score_products,
        "total_fetched": len(products),
        "categories": list(categories),
        "duration_seconds": duration,
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Aggregate trending products from Amazon Movers & Shakers"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=1.0,
        help="Minimum outlier score (default: 1.0)",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    result = run_amazon_aggregation(min_score=args.min_score)
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
