#!/usr/bin/env python3
"""
Content aggregation pipeline for DTC Newsletter.
DOE-VERSION: 2026.01.29

Orchestrates the full Reddit content aggregation workflow:
1. Fetches posts from target subreddits
2. Calculates outlier scores
3. Saves to cache
4. Displays results with AI summary placeholders
"""

import argparse
import sys
from datetime import datetime, timezone

from execution.reddit_fetcher import fetch_all_subreddits, TARGET_SUBREDDITS
from execution.storage import save_reddit_posts, get_cache_stats


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Aggregate trending content from Reddit for DTC newsletter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python execution/content_aggregate.py
  python execution/content_aggregate.py --min-score 3.0
  python execution/content_aggregate.py --subreddits shopify,dropship
  python execution/content_aggregate.py --no-save --show-all
        """,
    )

    parser.add_argument(
        "--min-score",
        type=float,
        default=2.0,
        help="Minimum outlier score to include (default: 2.0)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum posts to fetch per subreddit (default: 50)",
    )

    parser.add_argument(
        "--subreddits",
        type=str,
        default=None,
        help="Comma-separated list of subreddits (default: shopify,dropship,ecommerce)",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Display results without saving to cache",
    )

    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all posts instead of just top 10",
    )

    return parser.parse_args()


def format_post_display(post: dict, rank: int) -> str:
    """
    Format a post for console display.

    Args:
        post: Post dictionary with outlier_score, title, subreddit, url
        rank: Display rank (1-based)

    Returns:
        Formatted string for display
    """
    score = post.get("outlier_score", 0)
    title = post.get("title", "No title")
    subreddit = post.get("subreddit", "unknown")
    url = post.get("url", "")
    modifiers = post.get("engagement_modifiers", [])

    # Truncate long titles
    if len(title) > 80:
        title = title[:77] + "..."

    # Format engagement modifiers if present
    modifier_str = ""
    if modifiers:
        modifier_str = f" [{', '.join(modifiers)}]"

    lines = [
        f"\n{rank}. [{score:.1f}x]{modifier_str} {title} (r/{subreddit})",
        f"   AI Summary: [placeholder - will be generated in Phase 4]",
        f"   URL: {url}",
    ]

    return "\n".join(lines)


def run_aggregation(
    min_score: float = 2.0,
    limit: int = 50,
    subreddits: list[str] | None = None,
    save: bool = True,
    show_all: bool = False,
) -> dict:
    """
    Run the full content aggregation pipeline.

    Args:
        min_score: Minimum outlier score to include
        limit: Max posts per subreddit
        subreddits: List of subreddits to fetch from
        save: Whether to save results to cache
        show_all: Whether to show all posts or just top 10

    Returns:
        Dictionary with aggregation results and stats
    """
    start_time = datetime.now(timezone.utc)

    print("\n=== Content Aggregation Pipeline ===")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Target subreddits: {', '.join(subreddits or TARGET_SUBREDDITS)}")
    print(f"Minimum outlier score: {min_score}x")
    print(f"Posts per subreddit limit: {limit}")
    print("-" * 40)

    # Fetch posts
    print("\nFetching posts from Reddit...")
    try:
        posts = fetch_all_subreddits(
            limit_per_sub=limit,
            min_outlier_score=min_score,
            subreddits=subreddits,
        )
    except ValueError as e:
        print(f"\nError: {e}")
        print("\nPlease configure Reddit API credentials in .env:")
        print("  REDDIT_CLIENT_ID=your_client_id")
        print("  REDDIT_CLIENT_SECRET=your_client_secret")
        print("  REDDIT_USER_AGENT=your_app_name/1.0")
        print("\nGet credentials at: https://www.reddit.com/prefs/apps")
        return {"success": False, "error": str(e)}

    if not posts:
        print("\nNo posts found meeting criteria.")
        return {
            "success": True,
            "posts_fetched": 0,
            "posts_saved": 0,
            "cache_file": None,
        }

    print(f"Found {len(posts)} posts meeting threshold")

    # Filter for 3x+ outliers for highlight display
    high_outliers = [p for p in posts if p.get("outlier_score", 0) >= 3.0]

    # Save to cache if requested
    cache_file = None
    if save:
        print("\nSaving to cache...")
        cache_file = save_reddit_posts(posts)
        print(f"Saved to: {cache_file}")

    # Display results
    print("\n" + "=" * 50)
    print("=== Content Aggregation Results ===")
    print("=" * 50)
    print(f"\nPosts fetched: {len(posts)}")
    print(f"Posts with 3x+ outlier score: {len(high_outliers)}")

    if high_outliers:
        print(f"\nTop posts (3x+ outliers):")
        display_posts = high_outliers if show_all else high_outliers[:10]
        for rank, post in enumerate(display_posts, 1):
            print(format_post_display(post, rank))

        if not show_all and len(high_outliers) > 10:
            print(
                f"\n... and {len(high_outliers) - 10} more (use --show-all to see all)"
            )
    else:
        print("\nNo posts with 3x+ outlier score found.")
        print("Consider lowering --min-score or waiting for trending content.")

    # Show cache stats
    if save:
        print("\n" + "-" * 40)
        print("Cache Statistics:")
        stats = get_cache_stats()
        print(f"  Total cache files: {stats['total_files']}")
        print(f"  Total cached posts: {stats['total_posts']}")
        if stats["date_range"]:
            print(f"  Date range: {stats['date_range']}")

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    print("\n" + "-" * 40)
    print(f"Completed in {duration:.1f}s")
    print("=" * 50)

    return {
        "success": True,
        "posts_fetched": len(posts),
        "high_outliers": len(high_outliers),
        "posts_saved": len(posts) if save else 0,
        "cache_file": str(cache_file) if cache_file else None,
        "duration_seconds": duration,
    }


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Parse subreddits from comma-separated string
    subreddits = None
    if args.subreddits:
        subreddits = [s.strip() for s in args.subreddits.split(",")]

    result = run_aggregation(
        min_score=args.min_score,
        limit=args.limit,
        subreddits=subreddits,
        save=not args.no_save,
        show_all=args.show_all,
    )

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
