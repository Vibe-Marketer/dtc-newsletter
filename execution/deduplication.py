"""
Content deduplication for DTC Newsletter.
DOE-VERSION: 2026.01.31

Hash-based deduplication prevents repeating content from last 4 weeks.
Works across all content sources (Reddit, YouTube, Perplexity).
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


def generate_content_hash(content: dict) -> str:
    """
    Generate hash from content identifiers.

    Uses source + id for uniqueness:
    - Reddit: "reddit:{post_id}"
    - YouTube: "youtube:{video_id}"
    - Perplexity: "perplexity:{topic_slug}:{date}"

    Args:
        content: Dictionary with 'source' and identifier fields

    Returns:
        MD5 hex digest (32 characters)
    """
    source = content.get("source", "unknown")

    # Get the appropriate ID field based on source
    content_id = content.get("id", "")
    if not content_id:
        content_id = content.get("video_id", "")
    if not content_id:
        content_id = content.get("post_id", "")
    if not content_id:
        # For Perplexity, use topic_slug + date
        topic_slug = content.get("topic_slug", content.get("topic", ""))
        date = content.get("fetched_at", "")[:10] if content.get("fetched_at") else ""
        if topic_slug:
            content_id = f"{topic_slug}:{date}"

    key = f"{source}:{content_id}"
    return hashlib.md5(key.encode()).hexdigest()


def load_seen_hashes(
    cache_dirs: Optional[list[Path]] = None,
    weeks_back: int = 4,
) -> set[str]:
    """
    Load content hashes from last N weeks across all cache directories.

    Scans all JSON files in cache directories, extracts IDs, generates hashes.

    Args:
        cache_dirs: List of cache directories to scan (default: all sources)
        weeks_back: Number of weeks to look back (default: 4)

    Returns:
        Set of content hashes seen in the time window
    """
    if cache_dirs is None:
        cache_dirs = [
            Path("data/content_cache/reddit"),
            Path("data/content_cache/youtube"),
            Path("data/content_cache/perplexity"),
        ]

    cutoff = datetime.now(timezone.utc) - timedelta(weeks=weeks_back)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    seen = set()

    for cache_dir in cache_dirs:
        if not cache_dir.exists():
            continue

        for filepath in cache_dir.glob("*.json"):
            # Check file date from filename or modification time
            file_date = _extract_file_date(filepath)

            if file_date and file_date < cutoff_str:
                continue

            try:
                contents = _extract_contents_from_cache(filepath)
                for content in contents:
                    content_hash = generate_content_hash(content)
                    seen.add(content_hash)
            except (json.JSONDecodeError, IOError):
                continue

    return seen


def _extract_file_date(filepath: Path) -> Optional[str]:
    """
    Extract date from cache filename.

    Expected patterns:
    - reddit_YYYY-MM-DD.json
    - YYYY-MM-DD_query_type_topic.json

    Returns:
        Date string (YYYY-MM-DD) or None if not parseable
    """
    name = filepath.stem

    # Try pattern: source_YYYY-MM-DD
    if "_" in name:
        parts = name.split("_")
        for part in parts:
            if len(part) == 10 and part[4] == "-" and part[7] == "-":
                try:
                    datetime.strptime(part, "%Y-%m-%d")
                    return part
                except ValueError:
                    continue

    # Try pattern: YYYY-MM-DD_...
    if len(name) >= 10 and name[4] == "-" and name[7] == "-":
        date_part = name[:10]
        try:
            datetime.strptime(date_part, "%Y-%m-%d")
            return date_part
        except ValueError:
            pass

    return None


def _extract_contents_from_cache(filepath: Path) -> list[dict]:
    """
    Extract content items from a cache file.

    Handles different cache file structures:
    - Reddit: {"posts": [...], "metadata": {...}}
    - Perplexity: {"research": {...}, "metadata": {...}}

    Returns:
        List of content dictionaries with source added
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    contents = []

    # Determine source from file path
    source = "unknown"
    if "reddit" in str(filepath):
        source = "reddit"
    elif "youtube" in str(filepath):
        source = "youtube"
    elif "perplexity" in str(filepath):
        source = "perplexity"

    # Extract based on structure
    if "posts" in data:
        # Reddit format
        for post in data["posts"]:
            post["source"] = source
            contents.append(post)
    elif "research" in data:
        # Perplexity format
        research = data["research"]
        research["source"] = source
        # Add topic_slug from metadata if available
        if "metadata" in data and "topic_slug" in data["metadata"]:
            research["topic_slug"] = data["metadata"]["topic_slug"]
        contents.append(research)
    elif "videos" in data:
        # YouTube format (future)
        for video in data["videos"]:
            video["source"] = source
            contents.append(video)
    elif isinstance(data, list):
        # Direct list of items
        for item in data:
            item["source"] = source
            contents.append(item)

    return contents


def is_duplicate(content: dict, seen_hashes: set[str]) -> bool:
    """
    Check if content was seen before.

    Args:
        content: Content dictionary to check
        seen_hashes: Set of previously seen content hashes

    Returns:
        True if content hash is in seen_hashes
    """
    return generate_content_hash(content) in seen_hashes


def filter_duplicates(
    contents: list[dict],
    weeks_back: int = 4,
    cache_dirs: Optional[list[Path]] = None,
) -> tuple[list[dict], int]:
    """
    Filter out duplicate content.

    Loads seen hashes from cache directories, then filters the provided
    content list to remove duplicates.

    Args:
        contents: List of content dictionaries to filter
        weeks_back: Weeks to look back for duplicates (default: 4)
        cache_dirs: Cache directories to scan (default: all sources)

    Returns:
        Tuple of (filtered_list, duplicate_count)
    """
    seen = load_seen_hashes(cache_dirs=cache_dirs, weeks_back=weeks_back)

    filtered = []
    duplicates = 0

    for content in contents:
        if is_duplicate(content, seen):
            duplicates += 1
        else:
            filtered.append(content)

    return filtered, duplicates


def add_to_seen(
    contents: list[dict],
    seen_hashes: set[str],
) -> set[str]:
    """
    Add content hashes to the seen set.

    Useful for tracking content within a single run to prevent
    duplicates within the same batch.

    Args:
        contents: List of content to add
        seen_hashes: Existing set of seen hashes (modified in place)

    Returns:
        Updated set of seen hashes
    """
    for content in contents:
        seen_hashes.add(generate_content_hash(content))
    return seen_hashes


def get_dedup_stats(
    cache_dirs: Optional[list[Path]] = None,
    weeks_back: int = 4,
) -> dict:
    """
    Get statistics about content seen for deduplication.

    Args:
        cache_dirs: Cache directories to scan
        weeks_back: Weeks to look back

    Returns:
        Dictionary with counts per source
    """
    if cache_dirs is None:
        cache_dirs = [
            Path("data/content_cache/reddit"),
            Path("data/content_cache/youtube"),
            Path("data/content_cache/perplexity"),
        ]

    stats = {
        "total_hashes": 0,
        "by_source": {},
        "weeks_back": weeks_back,
    }

    cutoff = datetime.now(timezone.utc) - timedelta(weeks=weeks_back)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    for cache_dir in cache_dirs:
        if not cache_dir.exists():
            continue

        source_name = cache_dir.name
        source_count = 0

        for filepath in cache_dir.glob("*.json"):
            file_date = _extract_file_date(filepath)

            if file_date and file_date < cutoff_str:
                continue

            try:
                contents = _extract_contents_from_cache(filepath)
                source_count += len(contents)
            except (json.JSONDecodeError, IOError):
                continue

        stats["by_source"][source_name] = source_count
        stats["total_hashes"] += source_count

    return stats
