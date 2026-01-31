#!/usr/bin/env python3
"""
Twitter/X content aggregator for DTC Newsletter.
DOE-VERSION: 2026.01.31

Fetches viral tweets from DTC founders and brands using Apify.
Surfaces founder takes, product announcements, and controversy signals.
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

# Curated DTC accounts and search terms
DTC_SEARCH_TERMS = [
    "shopify founder",
    "dtc brand launch",
    "ecommerce revenue",
    "dropshipping 2026",
    "#dtcbrand viral",
]

DTC_ACCOUNTS = [
    "tobi",  # Shopify founder (Tobi Lutke)
    "levelsio",  # Indie maker
    "taborpitcher",  # DTC operator
    "RyanReynolds",  # Celebrity DTC
]

TWITTER_ACTOR = "apidojo/tweet-scraper"


def score_twitter_post(tweet: dict, account_avg_engagement: float = 1000.0) -> dict:
    """
    Calculate outlier score for a tweet.

    Composite score combining:
    - Engagement ratio (likes + retweets + quotes vs account average)
    - Quote tweet ratio boost (high quotes = controversial/viral)

    Args:
        tweet: Raw tweet data from Apify
        account_avg_engagement: Historical average for comparison

    Returns:
        Tweet dict with outlier_score and engagement breakdown added
    """
    likes = tweet.get("likeCount", 0) or 0
    retweets = tweet.get("retweetCount", 0) or 0
    quotes = tweet.get("quoteCount", 0) or 0
    replies = tweet.get("replyCount", 0) or 0

    # Total engagement
    engagement = likes + retweets + quotes + replies

    # Base ratio vs account average
    base_ratio = engagement / max(account_avg_engagement, 1)

    # Quote boost: high quote ratio indicates controversy/discussion
    # Quotes > 30% of retweets = 1.3x boost, else 1.0x
    quote_boost = 1.3 if retweets > 0 and quotes > retweets * 0.3 else 1.0

    # Final score
    outlier_score = base_ratio * quote_boost

    # Extract username safely
    author = tweet.get("author", {})
    if isinstance(author, dict):
        username = author.get("userName", "unknown")
    else:
        username = "unknown"

    # Extract tweet ID safely
    tweet_id = tweet.get("id", "")

    return {
        **tweet,
        "source": "twitter",
        "outlier_score": round(outlier_score, 2),
        "engagement": {
            "likes": likes,
            "retweets": retweets,
            "quotes": quotes,
            "replies": replies,
            "total": engagement,
        },
        "url": f"https://twitter.com/{username}/status/{tweet_id}",
    }


def fetch_dtc_tweets(
    search_terms: list[str] | None = None,
    max_per_term: int = 50,
) -> list[dict]:
    """
    Fetch tweets matching DTC search terms via Apify.

    Args:
        search_terms: List of search queries (defaults to DTC_SEARCH_TERMS)
        max_per_term: Max tweets per search term

    Returns:
        List of scored tweet dicts
    """
    terms = search_terms or DTC_SEARCH_TERMS

    all_tweets = []
    seen_ids = set()

    for term in terms:
        logger.info(f"Searching Twitter for: {term}")

        run_input = {
            "searchTerms": [term],
            "sort": "Latest",
            "maxItems": max_per_term,
        }

        try:
            items = fetch_from_apify(TWITTER_ACTOR, run_input)

            for tweet in items:
                tweet_id = tweet.get("id")
                if tweet_id and tweet_id not in seen_ids:
                    seen_ids.add(tweet_id)
                    scored = score_twitter_post(tweet)
                    all_tweets.append(scored)

        except Exception as e:
            logger.warning(f"Failed to fetch tweets for '{term}': {e}")
            continue

    # Sort by outlier score descending
    all_tweets.sort(key=lambda x: x.get("outlier_score", 0), reverse=True)

    return all_tweets


def run_twitter_aggregation(
    min_score: float = 2.0,
    max_per_term: int = 50,
) -> dict:
    """
    Run full Twitter aggregation with graceful degradation.

    Args:
        min_score: Minimum outlier score to include in results
        max_per_term: Max tweets per search term

    Returns:
        Dict with success status, tweets, and metadata
    """
    start_time = datetime.now(timezone.utc)

    print("\n=== Twitter/X Aggregation ===")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Search terms: {len(DTC_SEARCH_TERMS)}")
    print(f"Minimum outlier score: {min_score}x")
    print("-" * 40)

    result = fetch_with_retry(
        source_name="twitter",
        fetch_fn=lambda: fetch_dtc_tweets(max_per_term=max_per_term),
        cache_key="twitter_dtc_tweets",
    )

    if not result["success"]:
        print(f"\nTwitter fetch failed: {result['error']}")
        print("Pipeline will continue without Twitter data.")
        return result

    tweets = result["items"]

    # Filter by minimum score
    high_score_tweets = [t for t in tweets if t.get("outlier_score", 0) >= min_score]

    print(f"\nFetched: {len(tweets)} tweets")
    print(f"Above {min_score}x threshold: {len(high_score_tweets)}")

    if high_score_tweets:
        print(f"\nTop 5 tweets:")
        for i, tweet in enumerate(high_score_tweets[:5], 1):
            score = tweet.get("outlier_score", 0)
            text = (
                tweet.get("text", "")[:80] + "..."
                if len(tweet.get("text", "")) > 80
                else tweet.get("text", "")
            )
            author = tweet.get("author", {})
            if isinstance(author, dict):
                username = author.get("userName", "unknown")
            else:
                username = "unknown"
            print(f"  {i}. [{score:.1f}x] @{username}: {text}")

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    print(f"\nCompleted in {duration:.1f}s")
    print("-" * 40)

    return {
        **result,
        "items": high_score_tweets,
        "total_fetched": len(tweets),
        "duration_seconds": duration,
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Aggregate trending tweets from DTC accounts and topics"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=2.0,
        help="Minimum outlier score (default: 2.0)",
    )
    parser.add_argument(
        "--max-per-term",
        type=int,
        default=50,
        help="Max tweets per search term (default: 50)",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    result = run_twitter_aggregation(
        min_score=args.min_score,
        max_per_term=args.max_per_term,
    )
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
