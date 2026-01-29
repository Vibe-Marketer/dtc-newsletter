"""
Content storage layer for Reddit posts.

Handles saving fetched content to JSON files and loading cached data.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Default cache directory
DEFAULT_CACHE_DIR = Path("data/content_cache/reddit")


def get_cache_dir() -> Path:
    """
    Get the Reddit content cache directory.

    Creates the directory if it doesn't exist.

    Returns:
        Path to cache directory
    """
    cache_dir = DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cache_filename(date: Optional[datetime] = None) -> str:
    """
    Generate cache filename for a given date.

    Format: reddit_YYYY-MM-DD.json

    Args:
        date: Date for cache file (default: today)

    Returns:
        Cache filename string
    """
    if date is None:
        date = datetime.now(timezone.utc)

    return f"reddit_{date.strftime('%Y-%m-%d')}.json"


def save_reddit_posts(
    posts: list[dict],
    cache_dir: Optional[Path] = None,
    filename: Optional[str] = None,
) -> Path:
    """
    Save Reddit posts to JSON cache file.

    Args:
        posts: List of post dictionaries
        cache_dir: Directory to save to (default: DEFAULT_CACHE_DIR)
        filename: Custom filename (default: auto-generated from date)

    Returns:
        Path to saved file
    """
    cache_dir = cache_dir or get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = get_cache_filename()

    filepath = cache_dir / filename

    # Build cache metadata
    cache_data = {
        "metadata": {
            "source": "reddit",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "post_count": len(posts),
            "subreddits": list(set(p.get("subreddit", "") for p in posts)),
        },
        "posts": posts,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

    return filepath


def load_cached_posts(
    cache_dir: Optional[Path] = None,
    filename: Optional[str] = None,
    date: Optional[datetime] = None,
) -> list[dict]:
    """
    Load Reddit posts from cache file.

    Args:
        cache_dir: Directory to load from (default: DEFAULT_CACHE_DIR)
        filename: Specific filename to load (default: auto from date)
        date: Date of cache to load (default: today)

    Returns:
        List of post dictionaries

    Raises:
        FileNotFoundError: If cache file doesn't exist
    """
    cache_dir = cache_dir or get_cache_dir()

    if filename is None:
        filename = get_cache_filename(date)

    filepath = cache_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Cache file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        cache_data = json.load(f)

    return cache_data.get("posts", [])


def load_all_cached_posts(
    cache_dir: Optional[Path] = None,
    days_back: int = 7,
) -> list[dict]:
    """
    Load all cached posts from the last N days.

    Args:
        cache_dir: Directory to load from (default: DEFAULT_CACHE_DIR)
        days_back: Number of days to look back (default: 7)

    Returns:
        Combined list of posts from all cache files
    """
    from datetime import timedelta

    cache_dir = cache_dir or get_cache_dir()
    all_posts = []
    seen_ids = set()

    now = datetime.now(timezone.utc)

    for i in range(days_back):
        date = now - timedelta(days=i)
        try:
            posts = load_cached_posts(cache_dir=cache_dir, date=date)
            for post in posts:
                # Deduplicate by post ID
                post_id = post.get("id")
                if post_id and post_id not in seen_ids:
                    seen_ids.add(post_id)
                    all_posts.append(post)
        except FileNotFoundError:
            # Skip days without cache files
            continue

    return all_posts


def get_high_outlier_posts(
    min_score: float = 3.0,
    cache_dir: Optional[Path] = None,
    days_back: int = 7,
) -> list[dict]:
    """
    Get posts with outlier score above threshold.

    Args:
        min_score: Minimum outlier score (default: 3.0x)
        cache_dir: Cache directory
        days_back: Days to look back

    Returns:
        List of high-scoring posts, sorted by outlier_score descending
    """
    all_posts = load_all_cached_posts(cache_dir=cache_dir, days_back=days_back)

    high_scorers = [
        post for post in all_posts if post.get("outlier_score", 0) >= min_score
    ]

    # Sort by outlier score descending
    high_scorers.sort(key=lambda x: x.get("outlier_score", 0), reverse=True)

    return high_scorers


def get_cache_stats(cache_dir: Optional[Path] = None) -> dict:
    """
    Get statistics about the cache.

    Args:
        cache_dir: Cache directory

    Returns:
        Dictionary with cache statistics
    """
    cache_dir = cache_dir or get_cache_dir()

    if not cache_dir.exists():
        return {
            "total_files": 0,
            "total_posts": 0,
            "date_range": None,
            "files": [],
        }

    files = sorted(cache_dir.glob("reddit_*.json"))

    total_posts = 0
    dates = []
    file_info = []

    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                post_count = data.get("metadata", {}).get("post_count", 0)
                total_posts += post_count

                # Extract date from filename
                date_str = f.stem.replace("reddit_", "")
                dates.append(date_str)

                file_info.append(
                    {
                        "filename": f.name,
                        "date": date_str,
                        "post_count": post_count,
                    }
                )
        except (json.JSONDecodeError, IOError):
            continue

    return {
        "total_files": len(files),
        "total_posts": total_posts,
        "date_range": f"{min(dates)} to {max(dates)}" if dates else None,
        "files": file_info,
    }


def cleanup_old_cache(
    cache_dir: Optional[Path] = None,
    keep_days: int = 30,
) -> list[str]:
    """
    Remove cache files older than specified days.

    Args:
        cache_dir: Cache directory
        keep_days: Number of days to keep (default: 30)

    Returns:
        List of deleted filenames
    """
    from datetime import timedelta

    cache_dir = cache_dir or get_cache_dir()

    if not cache_dir.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    deleted = []

    for f in cache_dir.glob("reddit_*.json"):
        # Extract date from filename
        date_str = f.stem.replace("reddit_", "")

        if date_str < cutoff_str:
            f.unlink()
            deleted.append(f.name)

    return deleted
