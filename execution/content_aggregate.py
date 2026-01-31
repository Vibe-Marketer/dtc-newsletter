#!/usr/bin/env python3
"""
Content aggregation pipeline for DTC Newsletter.
DOE-VERSION: 2026.01.31

Orchestrates the full content aggregation workflow:
1. Fetches posts from target subreddits (Reddit)
2. Fetches videos from YouTube (TubeLab + YouTube Data API)
3. Optionally runs Perplexity research for trends
4. Optionally fetches from stretch sources (Twitter, TikTok, Amazon)
5. Applies deduplication across all sources
6. Generates content sheet with virality analysis (CSV + JSON)
7. Saves results to output/ directory
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.reddit_fetcher import fetch_all_subreddits, TARGET_SUBREDDITS
from execution.storage import save_reddit_posts, get_cache_stats
from execution.content_sheet import generate_and_save, get_content_sheet_stats

# Optional module imports with graceful degradation
YOUTUBE_AVAILABLE = False
PERPLEXITY_AVAILABLE = False
DEDUP_AVAILABLE = False
STRETCH_AVAILABLE = False
TRANSCRIPT_AVAILABLE = False

_youtube_fetcher = None
_perplexity_client = None
_deduplication = None
_stretch_aggregate = None
_transcript_fetcher = None

try:
    from execution import youtube_fetcher as _youtube_fetcher

    YOUTUBE_AVAILABLE = True
except ImportError:
    pass

try:
    from execution import perplexity_client as _perplexity_client

    PERPLEXITY_AVAILABLE = True
except ImportError:
    pass

try:
    from execution import deduplication as _deduplication

    DEDUP_AVAILABLE = True
except ImportError:
    pass

try:
    from execution import stretch_aggregate as _stretch_aggregate

    STRETCH_AVAILABLE = True
except ImportError:
    pass

try:
    from execution import transcript_fetcher as _transcript_fetcher

    TRANSCRIPT_AVAILABLE = True
except ImportError:
    pass


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Aggregate trending content from multiple sources for DTC newsletter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic run with all core sources
  python execution/content_aggregate.py

  # Reddit only with higher threshold
  python execution/content_aggregate.py --sources reddit --min-score 3.0

  # All sources including stretch
  python execution/content_aggregate.py --include-stretch

  # Skip deduplication
  python execution/content_aggregate.py --no-dedup

  # JSON output only
  python execution/content_aggregate.py --output-format json
        """,
    )

    # Source selection
    parser.add_argument(
        "--sources",
        type=str,
        default="reddit,youtube",
        help="Comma-separated sources: reddit,youtube,perplexity (default: reddit,youtube)",
    )

    parser.add_argument(
        "--no-youtube",
        action="store_true",
        help="Skip YouTube fetching",
    )

    parser.add_argument(
        "--no-perplexity",
        action="store_true",
        help="Skip Perplexity research",
    )

    # Scoring and filtering
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
        help="Maximum posts to fetch per source/subreddit (default: 50)",
    )

    parser.add_argument(
        "--subreddits",
        type=str,
        default=None,
        help="Comma-separated list of subreddits (default: shopify,dropship,ecommerce)",
    )

    # Deduplication
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Skip deduplication filtering",
    )

    parser.add_argument(
        "--dedup-weeks",
        type=int,
        default=4,
        help="Weeks to look back for deduplication (default: 4)",
    )

    # Output options
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["csv", "json", "both"],
        default="both",
        help="Output format: csv, json, or both (default: both)",
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

    # Stretch sources
    parser.add_argument(
        "--include-stretch",
        action="store_true",
        help="Include stretch sources (Twitter, TikTok, Amazon) - requires APIFY_TOKEN",
    )

    return parser.parse_args()


def format_content_display(content: dict, rank: int) -> str:
    """
    Format content item for console display.

    Args:
        content: Content dictionary with outlier_score, title, source, url
        rank: Display rank (1-based)

    Returns:
        Formatted string for display
    """
    score = content.get("outlier_score", 0)
    title = content.get("title", "No title")
    source = content.get("source", "unknown")
    url = content.get("url", "")

    # Source-specific display
    if source == "reddit":
        subreddit = content.get("subreddit", "unknown")
        source_label = f"r/{subreddit}"
    elif source == "youtube":
        channel = content.get("channel_name", "unknown")
        source_label = f"YT: {channel}"
    else:
        source_label = source

    # Truncate long titles
    if len(title) > 70:
        title = title[:67] + "..."

    lines = [
        f"\n{rank}. [{score:.1f}x] {title} ({source_label})",
        f"   URL: {url}",
    ]

    return "\n".join(lines)


def run_aggregation(
    sources: list[str] | None = None,
    min_score: float = 2.0,
    limit: int = 50,
    subreddits: list[str] | None = None,
    save: bool = True,
    show_all: bool = False,
    include_stretch: bool = False,
    skip_dedup: bool = False,
    dedup_weeks: int = 4,
    output_format: str = "both",
    skip_youtube: bool = False,
    skip_perplexity: bool = False,
) -> dict:
    """
    Run the full content aggregation pipeline.

    Args:
        sources: List of sources to fetch from (reddit, youtube, perplexity)
        min_score: Minimum outlier score to include
        limit: Max posts per source
        subreddits: List of subreddits to fetch from
        save: Whether to save results to cache
        show_all: Whether to show all posts or just top 10
        include_stretch: Whether to include stretch sources
        skip_dedup: Whether to skip deduplication
        dedup_weeks: Weeks to look back for deduplication
        output_format: Output format (csv, json, or both)
        skip_youtube: Skip YouTube fetching
        skip_perplexity: Skip Perplexity research

    Returns:
        Dictionary with aggregation results and stats
    """
    start_time = datetime.now(timezone.utc)

    # Default sources
    if sources is None:
        sources = ["reddit", "youtube"]

    # Apply skip flags
    if skip_youtube and "youtube" in sources:
        sources.remove("youtube")
    if skip_perplexity and "perplexity" in sources:
        sources.remove("perplexity")

    print("\n" + "=" * 60)
    print("=== DTC Newsletter Content Aggregation Pipeline ===")
    print("=" * 60)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Sources: {', '.join(sources)}")
    if "reddit" in sources:
        print(f"  Reddit subreddits: {', '.join(subreddits or TARGET_SUBREDDITS)}")
    print(f"Minimum outlier score: {min_score}x")
    print(f"Limit per source: {limit}")
    print(
        f"Deduplication: {'Disabled' if skip_dedup else f'{dedup_weeks} weeks lookback'}"
    )
    print(f"Output format: {output_format}")
    if include_stretch:
        print("Stretch sources: Enabled")
    print("-" * 60)

    all_content = []
    source_counts = {}

    # === REDDIT ===
    if "reddit" in sources:
        print("\n[1/3] Fetching from Reddit...")
        try:
            posts = fetch_all_subreddits(
                limit_per_sub=limit,
                min_outlier_score=min_score,
                subreddits=subreddits,
            )
            # Add source tag
            for post in posts:
                post["source"] = "reddit"
            all_content.extend(posts)
            source_counts["reddit"] = len(posts)
            print(f"  Found {len(posts)} posts meeting threshold")
        except ValueError as e:
            print(f"  Reddit error: {e}")
            source_counts["reddit"] = 0

    # === YOUTUBE ===
    if "youtube" in sources:
        print("\n[2/3] Fetching from YouTube...")
        if YOUTUBE_AVAILABLE and _youtube_fetcher is not None:
            try:
                fetcher = _youtube_fetcher.YouTubeFetcher()
                videos = fetcher.fetch_outliers(min_outlier_score=min_score)
                all_content.extend(videos)
                source_counts["youtube"] = len(videos)
                print(f"  Found {len(videos)} videos meeting threshold")

                # Fetch transcripts for top 10 if available
                if TRANSCRIPT_AVAILABLE and _transcript_fetcher is not None and videos:
                    print("  Fetching transcripts for top 10 videos...")
                    top_videos = sorted(
                        videos, key=lambda x: x.get("outlier_score", 0), reverse=True
                    )[:10]
                    video_ids = [v.get("id", "") for v in top_videos if v.get("id")]
                    transcripts = _transcript_fetcher.fetch_transcripts_batch(
                        video_ids, limit=10, verbose=False
                    )
                    if save:
                        _transcript_fetcher.save_transcripts(transcripts)
                    successful = sum(1 for t in transcripts if t.get("error") is None)
                    print(f"  Fetched {successful}/{len(video_ids)} transcripts")

            except Exception as e:
                print(f"  YouTube error: {e}")
                source_counts["youtube"] = 0
        else:
            print("  YouTube module not available")
            source_counts["youtube"] = 0

    # === PERPLEXITY ===
    if "perplexity" in sources:
        print("\n[3/3] Running Perplexity research...")
        if PERPLEXITY_AVAILABLE and _perplexity_client is not None:
            try:
                trends = _perplexity_client.search_trends("e-commerce DTC")
                if save:
                    _perplexity_client.save_research(trends, "trends")
                print(
                    f"  Trends research saved ({len(trends.get('citations', []))} citations)"
                )
                # Perplexity doesn't add to content list directly
                source_counts["perplexity"] = 1
            except Exception as e:
                print(f"  Perplexity error: {e}")
                source_counts["perplexity"] = 0
        else:
            print("  Perplexity module not available")
            source_counts["perplexity"] = 0
    else:
        print("\n[3/3] Perplexity: Skipped")

    # === STRETCH SOURCES ===
    if include_stretch:
        print("\n[Stretch] Fetching stretch sources...")
        if STRETCH_AVAILABLE and _stretch_aggregate is not None:
            try:
                stretch_result = _stretch_aggregate.run_all_stretch_sources()
                if stretch_result["success"]:
                    merged = _stretch_aggregate.merge_stretch_results(
                        stretch_result, all_content
                    )
                    stretch_count = len(merged) - len(all_content)
                    all_content = merged
                    source_counts["stretch"] = stretch_count
                    print(f"  Added {stretch_count} items from stretch sources")
                    print(
                        f"    Succeeded: {', '.join(stretch_result['sources_succeeded'])}"
                    )
                    if stretch_result["sources_failed"]:
                        print(
                            f"    Failed: {', '.join(stretch_result['sources_failed'])}"
                        )
                else:
                    print(
                        f"  Stretch sources failed: {stretch_result.get('error', 'unknown')}"
                    )
            except Exception as e:
                print(f"  Stretch error: {e}")
        else:
            print("  Stretch sources not available")

    print(f"\nTotal content before dedup: {len(all_content)}")

    # === DEDUPLICATION ===
    dup_count = 0
    if not skip_dedup and DEDUP_AVAILABLE and _deduplication is not None:
        print("\nApplying deduplication...")
        all_content, dup_count = _deduplication.filter_duplicates(
            all_content, weeks_back=dedup_weeks
        )
        print(f"  Removed {dup_count} duplicates (seen in last {dedup_weeks} weeks)")
        print(f"  Remaining: {len(all_content)}")
    elif skip_dedup:
        print("\nDeduplication: Skipped (--no-dedup)")
    else:
        print("\nDeduplication: Not available (module missing)")

    # Sort by outlier score
    all_content.sort(key=lambda x: x.get("outlier_score", 0), reverse=True)

    # === GENERATE CONTENT SHEET ===
    csv_path = None
    json_path = None
    if save and all_content:
        print("\nGenerating content sheet...")
        output_dir = Path("output")

        if output_format == "both":
            csv_path, json_path = generate_and_save(all_content, output_dir=output_dir)
            print(f"  CSV: {csv_path}")
            print(f"  JSON: {json_path}")
        elif output_format == "csv":
            from execution.content_sheet import generate_content_sheet, save_csv

            enriched = generate_content_sheet(all_content)
            csv_path = save_csv(enriched, output_dir=output_dir)
            print(f"  CSV: {csv_path}")
        elif output_format == "json":
            from execution.content_sheet import generate_content_sheet, save_json

            enriched = generate_content_sheet(all_content)
            json_path = save_json(enriched, output_dir=output_dir)
            print(f"  JSON: {json_path}")

    # Save to cache if requested (legacy format)
    cache_file = None
    if save and all_content:
        print("\nSaving to cache...")
        cache_file = save_reddit_posts(all_content)
        print(f"  Cache: {cache_file}")

    # Filter for 3x+ outliers for highlight display
    high_outliers = [p for p in all_content if p.get("outlier_score", 0) >= 3.0]

    # === DISPLAY RESULTS ===
    print("\n" + "=" * 60)
    print("=== Content Aggregation Results ===")
    print("=" * 60)

    # Source summary
    print("\nBy Source:")
    for source, count in source_counts.items():
        print(f"  {source}: {count}")
    print(f"\nTotal content: {len(all_content)}")
    print(f"Duplicates removed: {dup_count}")
    print(f"Posts with 3x+ outlier score: {len(high_outliers)}")

    if high_outliers:
        print(f"\nTop content (3x+ outliers):")
        display_posts = high_outliers if show_all else high_outliers[:10]
        for rank, post in enumerate(display_posts, 1):
            print(format_content_display(post, rank))

        if not show_all and len(high_outliers) > 10:
            print(
                f"\n... and {len(high_outliers) - 10} more (use --show-all to see all)"
            )
    else:
        print("\nNo content with 3x+ outlier score found.")
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

    # Content sheet stats
    if all_content:
        sheet_stats = get_content_sheet_stats(all_content)
        print("\nContent Sheet Stats:")
        print(f"  Total items: {sheet_stats['total_items']}")
        print(
            f"  Score range: {sheet_stats['score_range']['min']:.1f} - {sheet_stats['score_range']['max']:.1f}"
        )
        print(f"  Average score: {sheet_stats['avg_score']:.2f}")

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    print("\n" + "-" * 40)
    print(f"Completed in {duration:.1f}s")
    print("=" * 60)

    return {
        "success": True,
        "content_fetched": len(all_content),
        "source_counts": source_counts,
        "duplicates_removed": dup_count,
        "high_outliers": len(high_outliers),
        "content_saved": len(all_content) if save else 0,
        "cache_file": str(cache_file) if cache_file else None,
        "csv_path": str(csv_path) if csv_path else None,
        "json_path": str(json_path) if json_path else None,
        "duration_seconds": duration,
    }


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Parse sources from comma-separated string
    sources = [s.strip().lower() for s in args.sources.split(",")]

    # Parse subreddits from comma-separated string
    subreddits = None
    if args.subreddits:
        subreddits = [s.strip() for s in args.subreddits.split(",")]

    result = run_aggregation(
        sources=sources,
        min_score=args.min_score,
        limit=args.limit,
        subreddits=subreddits,
        save=not args.no_save,
        show_all=args.show_all,
        include_stretch=args.include_stretch,
        skip_dedup=args.no_dedup,
        dedup_weeks=args.dedup_weeks,
        output_format=args.output_format,
        skip_youtube=args.no_youtube,
        skip_perplexity=args.no_perplexity,
    )

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
