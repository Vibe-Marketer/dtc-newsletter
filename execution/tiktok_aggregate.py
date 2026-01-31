#!/usr/bin/env python3
"""
TikTok content aggregator for DTC Newsletter.
DOE-VERSION: 2026.01.31

Fetches viral TikTok videos with commerce indicators using Apify.
Surfaces trending products and creator-brand partnerships.
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

# Commerce-focused hashtags
COMMERCE_HASHTAGS = [
    "tiktokmademebuyit",
    "amazonfinds",
    "smallbusiness",
    "viralproducts",
    "tiktokshop",
    "dropshipping",
]

# Commerce indicator keywords
COMMERCE_KEYWORDS = [
    "link in bio",
    "shop now",
    "use code",
    "discount",
    "available at",
    "tiktok shop",
    "where to buy",
    "just restocked",
    "selling fast",
]

TIKTOK_ACTOR = "clockworks/tiktok-scraper"


def is_commerce_video(video: dict) -> bool:
    """
    Detect if a video has commerce indicators.

    Checks for:
    - TikTok Shop seller flag
    - Commerce user info
    - Sponsored content flag
    - Commerce keywords in description

    Args:
        video: Raw video data from Apify

    Returns:
        True if video has commerce indicators
    """
    # Check platform flags
    if video.get("ttSeller"):
        return True
    if video.get("isSponsored"):
        return True

    # Check commerce user info
    commerce_info = video.get("commerceUserInfo", {})
    if commerce_info.get("commerceUser"):
        return True

    # Check description for commerce keywords
    desc = (video.get("desc") or "").lower()
    for keyword in COMMERCE_KEYWORDS:
        if keyword in desc:
            return True

    return False


def score_tiktok_video(video: dict, hashtag_avg_plays: float = 100000.0) -> dict:
    """
    Calculate outlier score for a TikTok video.

    Score combines:
    - Play count ratio vs hashtag average
    - Commerce boost (1.5x for commerce videos)

    Args:
        video: Raw video data from Apify
        hashtag_avg_plays: Average plays for comparison (default 100k)

    Returns:
        Video dict with outlier_score and metadata added
    """
    play_count = video.get("playCount", 0) or 0
    like_count = video.get("diggCount", 0) or 0
    comment_count = video.get("commentCount", 0) or 0
    share_count = video.get("shareCount", 0) or 0

    # Base ratio vs average
    base_ratio = play_count / max(hashtag_avg_plays, 1)

    # Commerce boost
    is_commerce = is_commerce_video(video)
    commerce_boost = 1.5 if is_commerce else 1.0

    # Final score
    outlier_score = base_ratio * commerce_boost

    # Build video URL
    author_id = video.get("authorMeta", {}).get("id", "")
    video_id = video.get("id", "")
    url = (
        f"https://www.tiktok.com/@{author_id}/video/{video_id}"
        if author_id and video_id
        else ""
    )

    return {
        **video,
        "source": "tiktok",
        "outlier_score": round(outlier_score, 2),
        "is_commerce": is_commerce,
        "engagement": {
            "plays": play_count,
            "likes": like_count,
            "comments": comment_count,
            "shares": share_count,
        },
        "url": url,
    }


def fetch_trending_tiktoks(
    hashtags: list[str] | None = None,
    results_per_hashtag: int = 30,
) -> list[dict]:
    """
    Fetch trending TikTok videos via Apify.

    Args:
        hashtags: List of hashtags to search (defaults to COMMERCE_HASHTAGS)
        results_per_hashtag: Max videos per hashtag

    Returns:
        List of scored video dicts
    """
    tags = hashtags or COMMERCE_HASHTAGS

    logger.info(f"Fetching TikToks for hashtags: {tags}")

    run_input = {
        "hashtags": tags,
        "resultsPerPage": results_per_hashtag,
        "scrapeRelatedVideos": False,
        "shouldDownloadVideos": False,
    }

    items = fetch_from_apify(TIKTOK_ACTOR, run_input)

    # Deduplicate and score
    seen_ids = set()
    scored_videos = []

    for video in items:
        video_id = video.get("id")
        if video_id and video_id not in seen_ids:
            seen_ids.add(video_id)
            scored = score_tiktok_video(video)
            scored_videos.append(scored)

    # Sort by outlier score descending
    scored_videos.sort(key=lambda x: x.get("outlier_score", 0), reverse=True)

    return scored_videos


def run_tiktok_aggregation(
    min_score: float = 1.5,
    results_per_hashtag: int = 30,
) -> dict:
    """
    Run full TikTok aggregation with graceful degradation.

    Args:
        min_score: Minimum outlier score to include
        results_per_hashtag: Max videos per hashtag

    Returns:
        Dict with success status, videos, and metadata
    """
    start_time = datetime.now(timezone.utc)

    print("\n=== TikTok Aggregation ===")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Hashtags: {len(COMMERCE_HASHTAGS)}")
    print(f"Minimum outlier score: {min_score}x")
    print("-" * 40)

    result = fetch_with_retry(
        source_name="tiktok",
        fetch_fn=lambda: fetch_trending_tiktoks(
            results_per_hashtag=results_per_hashtag
        ),
        cache_key="tiktok_commerce_videos",
    )

    if not result["success"]:
        print(f"\nTikTok fetch failed: {result['error']}")
        print("Pipeline will continue without TikTok data.")
        return result

    videos = result["items"]

    # Filter by minimum score
    high_score_videos = [v for v in videos if v.get("outlier_score", 0) >= min_score]
    commerce_videos = [v for v in high_score_videos if v.get("is_commerce")]

    print(f"\nFetched: {len(videos)} videos")
    print(f"Above {min_score}x threshold: {len(high_score_videos)}")
    print(f"Commerce videos: {len(commerce_videos)}")

    if high_score_videos:
        print(f"\nTop 5 videos:")
        for i, video in enumerate(high_score_videos[:5], 1):
            score = video.get("outlier_score", 0)
            desc = (
                (video.get("desc") or "")[:60] + "..."
                if len(video.get("desc") or "") > 60
                else video.get("desc", "")
            )
            commerce_tag = " [COMMERCE]" if video.get("is_commerce") else ""
            print(f"  {i}. [{score:.1f}x]{commerce_tag} {desc}")

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    print(f"\nCompleted in {duration:.1f}s")
    print("-" * 40)

    return {
        **result,
        "items": high_score_videos,
        "total_fetched": len(videos),
        "commerce_count": len(commerce_videos),
        "duration_seconds": duration,
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Aggregate trending TikTok videos with commerce focus"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=1.5,
        help="Minimum outlier score (default: 1.5)",
    )
    parser.add_argument(
        "--results-per-hashtag",
        type=int,
        default=30,
        help="Max videos per hashtag (default: 30)",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    result = run_tiktok_aggregation(
        min_score=args.min_score,
        results_per_hashtag=args.results_per_hashtag,
    )
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
