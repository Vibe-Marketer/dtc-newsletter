"""
Outlier scoring for Reddit content.

Formula: Outlier Score = (Post Upvotes / Subreddit Average) * Recency Boost * Engagement Modifiers

A score of 6.81 means that post performed almost 7x better than the subreddit's average.
"""

from datetime import datetime, timezone
from typing import Optional
import re


def calculate_recency_boost(
    post_timestamp: float, max_boost: float = 1.3, decay_days: int = 7
) -> float:
    """
    Calculate recency boost for a post.

    - Posts from today get max boost (1.3x)
    - Boost decays linearly over decay_days
    - Posts older than decay_days get 1.0x (no boost)

    Args:
        post_timestamp: Unix timestamp of post creation
        max_boost: Maximum boost for newest posts (default 1.3)
        decay_days: Days until boost reaches 1.0 (default 7)

    Returns:
        Float multiplier between 1.0 and max_boost
    """
    now = datetime.now(timezone.utc)
    post_time = datetime.fromtimestamp(post_timestamp, tz=timezone.utc)

    age_seconds = (now - post_time).total_seconds()
    age_days = age_seconds / (24 * 60 * 60)

    if age_days >= decay_days:
        return 1.0

    if age_days <= 0:
        return max_boost

    # Linear decay from max_boost to 1.0 over decay_days
    boost_range = max_boost - 1.0
    decay_fraction = age_days / decay_days
    boost = max_boost - (boost_range * decay_fraction)

    return boost


# Engagement modifier keywords
MONEY_KEYWORDS = [
    r"\$\d",  # Dollar amounts
    r"revenue",
    r"profit",
    r"sales",
    r"income",
    r"earning",
    r"made \d",
    r"million",
    r"k/month",
    r"k per month",
]

TIME_KEYWORDS = [
    r"\d+ minutes?",
    r"\d+ hours?",
    r"fast",
    r"quick",
    r"instant",
    r"immediately",
    r"overnight",
    r"in \d+ days?",
]

SECRET_KEYWORDS = [
    r"secret",
    r"hidden",
    r"nobody knows",
    r"little-known",
    r"unknown",
    r"untapped",
    r"underrated",
]

CONTROVERSY_KEYWORDS = [
    r"unpopular opinion",
    r"controversial",
    r"nobody talks about",
    r"hot take",
    r"disagree",
    r"wrong about",
]


def _check_keywords(text: str, keywords: list[str]) -> bool:
    """Check if any keyword pattern matches in text (case-insensitive)."""
    text_lower = text.lower()
    for pattern in keywords:
        if re.search(pattern.lower(), text_lower):
            return True
    return False


def calculate_engagement_modifiers(title: str, selftext: str = "") -> float:
    """
    Apply engagement modifiers based on hook content.

    Modifiers (additive, then converted to multiplier):
    - +30% if hook involves money ($, revenue, profit, sales, income)
    - +20% if hook involves time (minutes, hours, fast, quick, instantly)
    - +20% if hook involves secrets (secret, hidden, nobody knows, little-known)
    - +15% if hook involves controversy (unpopular opinion, controversial, nobody talks about)

    Args:
        title: Post title
        selftext: Post body text (optional)

    Returns:
        Float multiplier >= 1.0
    """
    combined_text = f"{title} {selftext}"

    modifier = 0.0

    if _check_keywords(combined_text, MONEY_KEYWORDS):
        modifier += 0.30

    if _check_keywords(combined_text, TIME_KEYWORDS):
        modifier += 0.20

    if _check_keywords(combined_text, SECRET_KEYWORDS):
        modifier += 0.20

    if _check_keywords(combined_text, CONTROVERSY_KEYWORDS):
        modifier += 0.15

    return 1.0 + modifier


def calculate_outlier_score(
    upvotes: int,
    subreddit_avg_upvotes: float,
    post_timestamp: float,
    title: str,
    selftext: str = "",
) -> float:
    """
    Calculate complete outlier score.

    Formula: (upvotes / subreddit_avg) * recency_boost * engagement_modifiers

    Args:
        upvotes: Post upvote count
        subreddit_avg_upvotes: Average upvotes for this subreddit
        post_timestamp: Unix timestamp of post creation
        title: Post title
        selftext: Post body text

    Returns:
        Outlier score (e.g., 6.81 = ~7x better than average)

    Raises:
        ValueError: If subreddit_avg_upvotes is zero or negative
    """
    if subreddit_avg_upvotes <= 0:
        raise ValueError("subreddit_avg_upvotes must be positive")

    # Base score: how many times better than average
    base_score = upvotes / subreddit_avg_upvotes

    # Apply recency boost
    recency = calculate_recency_boost(post_timestamp)

    # Apply engagement modifiers
    engagement = calculate_engagement_modifiers(title, selftext)

    return base_score * recency * engagement
