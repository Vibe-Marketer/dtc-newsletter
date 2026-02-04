#!/usr/bin/env python3
"""
Topic tracker for DTCNews newsletter.
DOE-VERSION: 2026.02.04

Prevents covering the same topics repeatedly by:
1. Recording topics used in past newsletters
2. Checking new content against past topics
3. Using keyword extraction + similarity to detect duplicates

This is TOPIC-level deduplication, not content-level.
"Instagram DMs for first sales" from Reddit and the same topic from YouTube
should both be blocked if we covered it recently.

Usage:
    # Check if a topic was recently covered
    python execution/topic_tracker.py --check "email marketing automation"

    # Record a topic as used
    python execution/topic_tracker.py --record "Instagram DM strategy" --issue 5

    # List recent topics
    python execution/topic_tracker.py --list
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DOE_VERSION = "2026.02.04"

# Where we store the topic history
TOPIC_HISTORY_FILE = Path("data/topic_history.json")

# How many weeks back to check for duplicate topics
DEFAULT_WEEKS_BACK = 6

# Keywords that are too generic to match on
STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "your",
    "you",
    "how",
    "what",
    "why",
    "when",
    "where",
    "who",
    "which",
    "can",
    "will",
    "just",
    "get",
    "got",
    "make",
    "made",
    "use",
    "used",
    "using",
    "new",
    "first",
    "best",
    "top",
    "way",
    "ways",
    "thing",
    "things",
    "people",
    "one",
    "two",
}

# Topic categories for broader matching
TOPIC_SYNONYMS = {
    "email": [
        "email",
        "newsletter",
        "klaviyo",
        "mailchimp",
        "abandoned cart",
        "welcome sequence",
    ],
    "ads": [
        "ads",
        "meta ads",
        "facebook ads",
        "instagram ads",
        "tiktok ads",
        "paid traffic",
        "roas",
        "cpm",
        "cpc",
    ],
    "ugc": ["ugc", "user generated", "creator", "influencer", "content creator"],
    "organic": ["organic", "tiktok organic", "reels", "shorts", "viral video"],
    "product": ["product", "winning product", "product research", "trending product"],
    "conversion": ["conversion", "checkout", "cart", "aov", "upsell", "cross-sell"],
    "retention": ["retention", "repeat customer", "loyalty", "subscription", "ltv"],
    "launch": ["launch", "first sale", "getting started", "new store", "beginner"],
}


def extract_keywords(text: str) -> set[str]:
    """
    Extract meaningful keywords from text.

    Args:
        text: Text to extract keywords from

    Returns:
        Set of lowercase keywords
    """
    # Lowercase and split on non-alphanumeric
    words = re.findall(r"[a-z0-9]+", text.lower())

    # Remove stop words and short words
    keywords = {w for w in words if w not in STOP_WORDS and len(w) > 2}

    return keywords


def get_topic_category(text: str) -> Optional[str]:
    """
    Get the broad category of a topic.

    Args:
        text: Topic text

    Returns:
        Category name or None
    """
    text_lower = text.lower()

    for category, terms in TOPIC_SYNONYMS.items():
        for term in terms:
            if term in text_lower:
                return category

    return None


def calculate_similarity(topic1: str, topic2: str) -> float:
    """
    Calculate similarity between two topics.

    Uses keyword overlap + category matching.

    Args:
        topic1: First topic
        topic2: Second topic

    Returns:
        Similarity score 0.0 - 1.0
    """
    # Extract keywords
    kw1 = extract_keywords(topic1)
    kw2 = extract_keywords(topic2)

    if not kw1 or not kw2:
        return 0.0

    # Keyword overlap (Jaccard similarity)
    intersection = len(kw1 & kw2)
    union = len(kw1 | kw2)
    keyword_sim = intersection / union if union > 0 else 0.0

    # Category match bonus
    cat1 = get_topic_category(topic1)
    cat2 = get_topic_category(topic2)
    category_bonus = 0.2 if (cat1 and cat2 and cat1 == cat2) else 0.0

    # Combined score
    return min(keyword_sim + category_bonus, 1.0)


def load_topic_history() -> dict:
    """
    Load topic history from file.

    Returns:
        Dict with "topics" list
    """
    if not TOPIC_HISTORY_FILE.exists():
        return {"topics": []}

    with open(TOPIC_HISTORY_FILE) as f:
        return json.load(f)


def save_topic_history(history: dict) -> None:
    """Save topic history to file."""
    TOPIC_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(TOPIC_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def record_topic(
    topic: str,
    issue_number: int,
    headline: Optional[str] = None,
    source_content: Optional[str] = None,
) -> None:
    """
    Record a topic as used in a newsletter.

    Args:
        topic: Main topic/theme
        issue_number: Newsletter issue number
        headline: Deep dive headline if available
        source_content: Original content title if available
    """
    history = load_topic_history()

    entry = {
        "topic": topic,
        "issue_number": issue_number,
        "headline": headline,
        "source_content": source_content,
        "keywords": list(extract_keywords(topic)),
        "category": get_topic_category(topic),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    history["topics"].append(entry)
    save_topic_history(history)


def check_topic_covered(
    topic: str,
    weeks_back: int = DEFAULT_WEEKS_BACK,
    similarity_threshold: float = 0.4,
) -> tuple[bool, Optional[dict]]:
    """
    Check if a topic was recently covered.

    Args:
        topic: Topic to check
        weeks_back: How many weeks to look back
        similarity_threshold: Min similarity to consider a match (0.0-1.0)

    Returns:
        Tuple of (is_covered, matching_entry or None)
    """
    history = load_topic_history()

    cutoff = datetime.now(timezone.utc) - timedelta(weeks=weeks_back)
    cutoff_str = cutoff.isoformat()

    for entry in history.get("topics", []):
        # Check if within time window
        recorded_at = entry.get("recorded_at", "")
        if recorded_at < cutoff_str:
            continue

        # Check similarity
        past_topic = entry.get("topic", "")
        sim = calculate_similarity(topic, past_topic)

        if sim >= similarity_threshold:
            return True, entry

    return False, None


def filter_covered_topics(
    content_items: list[dict],
    weeks_back: int = DEFAULT_WEEKS_BACK,
    similarity_threshold: float = 0.4,
) -> tuple[list[dict], list[dict]]:
    """
    Filter out content items whose topics were recently covered.

    Args:
        content_items: List of content dicts with "title" key
        weeks_back: Weeks to look back
        similarity_threshold: Min similarity to filter

    Returns:
        Tuple of (filtered_items, removed_items)
    """
    filtered = []
    removed = []

    for item in content_items:
        title = item.get("title", "") or item.get("headline", "")
        summary = item.get("summary", "")

        # Check title and summary
        topic_text = f"{title} {summary}"
        is_covered, match = check_topic_covered(
            topic_text, weeks_back, similarity_threshold
        )

        if is_covered:
            item["_filtered_reason"] = (
                f"Similar to issue #{match.get('issue_number')}: {match.get('topic', '')[:50]}"
            )
            removed.append(item)
        else:
            filtered.append(item)

    return filtered, removed


def list_recent_topics(weeks_back: int = DEFAULT_WEEKS_BACK) -> list[dict]:
    """
    List topics from recent weeks.

    Args:
        weeks_back: Weeks to look back

    Returns:
        List of topic entries
    """
    history = load_topic_history()

    cutoff = datetime.now(timezone.utc) - timedelta(weeks=weeks_back)
    cutoff_str = cutoff.isoformat()

    recent = [
        entry
        for entry in history.get("topics", [])
        if entry.get("recorded_at", "") >= cutoff_str
    ]

    # Sort by date descending
    recent.sort(key=lambda x: x.get("recorded_at", ""), reverse=True)

    return recent


def main():
    parser = argparse.ArgumentParser(
        description="Track newsletter topics to prevent repetition",
    )
    parser.add_argument(
        "--check",
        "-c",
        help="Check if a topic was recently covered",
    )
    parser.add_argument(
        "--record",
        "-r",
        help="Record a topic as used",
    )
    parser.add_argument(
        "--issue",
        "-i",
        type=int,
        help="Issue number (required with --record)",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List recent topics",
    )
    parser.add_argument(
        "--weeks",
        "-w",
        type=int,
        default=DEFAULT_WEEKS_BACK,
        help=f"Weeks to look back (default: {DEFAULT_WEEKS_BACK})",
    )
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=0.4,
        help="Similarity threshold for matching (default: 0.4)",
    )
    args = parser.parse_args()

    print(f"[topic_tracker] v{DOE_VERSION}")
    print()

    if args.list:
        topics = list_recent_topics(args.weeks)
        print(f"Topics from last {args.weeks} weeks:")
        print("=" * 60)

        if not topics:
            print("No topics recorded yet.")
        else:
            for entry in topics:
                issue = entry.get("issue_number", "?")
                topic = entry.get("topic", "Unknown")
                date = entry.get("recorded_at", "")[:10]
                category = entry.get("category", "")
                cat_str = f" [{category}]" if category else ""
                print(f"Issue #{issue} ({date}){cat_str}: {topic}")

        return 0

    if args.check:
        is_covered, match = check_topic_covered(args.check, args.weeks, args.threshold)

        if is_covered:
            print(f"COVERED: This topic was recently used")
            print(f"  Similar to: {match.get('topic', '')}")
            print(f"  Issue: #{match.get('issue_number', '?')}")
            print(f"  Date: {match.get('recorded_at', '')[:10]}")
            return 1
        else:
            print(f"NOT COVERED: This topic is fresh")
            return 0

    if args.record:
        if not args.issue:
            print("ERROR: --issue required with --record")
            return 1

        record_topic(args.record, args.issue)
        print(f"Recorded topic for issue #{args.issue}")
        print(f"  Topic: {args.record}")
        print(f"  Keywords: {', '.join(extract_keywords(args.record))}")
        print(f"  Category: {get_topic_category(args.record) or 'none'}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
