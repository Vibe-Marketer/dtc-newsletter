"""
Reddit content fetcher using PRAW.

Fetches posts from target subreddits (r/shopify, r/dropship, r/ecommerce),
calculates outlier scores, and prepares content for storage.
"""

import os
from datetime import datetime, timezone
from typing import Optional

import praw
from dotenv import load_dotenv

from execution.scoring import calculate_outlier_score

# Load environment variables
load_dotenv()

# Target subreddits for DTC/ecommerce content
TARGET_SUBREDDITS = ["shopify", "dropship", "ecommerce"]

# Default number of posts to fetch for average calculation
DEFAULT_SAMPLE_SIZE = 100


def get_reddit_client() -> praw.Reddit:
    """
    Create and return an authenticated Reddit client.

    Requires environment variables:
    - REDDIT_CLIENT_ID
    - REDDIT_CLIENT_SECRET
    - REDDIT_USER_AGENT

    Returns:
        praw.Reddit: Authenticated Reddit instance

    Raises:
        ValueError: If required environment variables are missing
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not client_id:
        raise ValueError("REDDIT_CLIENT_ID environment variable is required")
    if not client_secret:
        raise ValueError("REDDIT_CLIENT_SECRET environment variable is required")
    if not user_agent:
        raise ValueError("REDDIT_USER_AGENT environment variable is required")

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def get_subreddit_average(
    reddit: praw.Reddit,
    subreddit_name: str,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
) -> float:
    """
    Calculate average upvotes for a subreddit based on recent posts.

    Args:
        reddit: Authenticated Reddit client
        subreddit_name: Name of subreddit (without r/ prefix)
        sample_size: Number of posts to sample for average

    Returns:
        Average upvotes for the subreddit

    Raises:
        ValueError: If no posts found in subreddit
    """
    subreddit = reddit.subreddit(subreddit_name)

    total_upvotes = 0
    post_count = 0

    # Fetch hot posts to get a representative sample
    for post in subreddit.hot(limit=sample_size):
        total_upvotes += post.score
        post_count += 1

    if post_count == 0:
        raise ValueError(f"No posts found in r/{subreddit_name}")

    return total_upvotes / post_count


def fetch_subreddit_posts(
    reddit: praw.Reddit,
    subreddit_name: str,
    limit: int = 50,
    min_outlier_score: float = 2.0,
    subreddit_avg: Optional[float] = None,
) -> list[dict]:
    """
    Fetch posts from a subreddit and calculate outlier scores.

    Args:
        reddit: Authenticated Reddit client
        subreddit_name: Name of subreddit (without r/ prefix)
        limit: Maximum posts to fetch
        min_outlier_score: Minimum outlier score to include (default 2.0x)
        subreddit_avg: Pre-calculated average (if None, will calculate)

    Returns:
        List of post dictionaries with outlier scores
    """
    subreddit = reddit.subreddit(subreddit_name)

    # Get average if not provided
    if subreddit_avg is None:
        subreddit_avg = get_subreddit_average(reddit, subreddit_name)

    posts = []

    # Fetch posts from both hot and top (week) for variety
    seen_ids = set()

    for post in subreddit.hot(limit=limit):
        if post.id not in seen_ids:
            seen_ids.add(post.id)
            processed = _process_post(post, subreddit_name, subreddit_avg)
            if processed["outlier_score"] >= min_outlier_score:
                posts.append(processed)

    for post in subreddit.top(time_filter="week", limit=limit):
        if post.id not in seen_ids:
            seen_ids.add(post.id)
            processed = _process_post(post, subreddit_name, subreddit_avg)
            if processed["outlier_score"] >= min_outlier_score:
                posts.append(processed)

    # Sort by outlier score descending
    posts.sort(key=lambda x: x["outlier_score"], reverse=True)

    return posts


def _process_post(post, subreddit_name: str, subreddit_avg: float) -> dict:
    """
    Process a Reddit submission into a standardized dictionary.

    Args:
        post: PRAW Submission object
        subreddit_name: Name of subreddit
        subreddit_avg: Average upvotes for the subreddit

    Returns:
        Processed post dictionary
    """
    # Calculate outlier score
    outlier_score = calculate_outlier_score(
        upvotes=post.score,
        subreddit_avg_upvotes=subreddit_avg,
        post_timestamp=post.created_utc,
        title=post.title,
        selftext=post.selftext or "",
    )

    return {
        "id": post.id,
        "title": post.title,
        "selftext": post.selftext or "",
        "url": f"https://reddit.com{post.permalink}",
        "upvotes": post.score,
        "num_comments": post.num_comments,
        "created_utc": post.created_utc,
        "subreddit": subreddit_name,
        "subreddit_avg_upvotes": subreddit_avg,
        "outlier_score": round(outlier_score, 2),
        "source": "reddit",
        "engagement_modifiers": _get_engagement_modifier_labels(
            post.title, post.selftext or ""
        ),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def _get_engagement_modifier_labels(title: str, selftext: str) -> list[str]:
    """
    Get list of engagement modifier labels that apply to this content.

    Args:
        title: Post title
        selftext: Post body text

    Returns:
        List of modifier labels (e.g., ["money", "time"])
    """
    from execution.scoring import (
        MONEY_KEYWORDS,
        TIME_KEYWORDS,
        SECRET_KEYWORDS,
        CONTROVERSY_KEYWORDS,
        _check_keywords,
    )

    combined_text = f"{title} {selftext}"
    labels = []

    if _check_keywords(combined_text, MONEY_KEYWORDS):
        labels.append("money")
    if _check_keywords(combined_text, TIME_KEYWORDS):
        labels.append("time")
    if _check_keywords(combined_text, SECRET_KEYWORDS):
        labels.append("secret")
    if _check_keywords(combined_text, CONTROVERSY_KEYWORDS):
        labels.append("controversy")

    return labels


def fetch_all_subreddits(
    limit_per_sub: int = 50,
    min_outlier_score: float = 2.0,
    subreddits: Optional[list[str]] = None,
) -> list[dict]:
    """
    Fetch posts from all target subreddits.

    Args:
        limit_per_sub: Maximum posts per subreddit
        min_outlier_score: Minimum outlier score to include
        subreddits: List of subreddits (default: TARGET_SUBREDDITS)

    Returns:
        Combined list of posts from all subreddits, sorted by outlier score
    """
    reddit = get_reddit_client()
    subreddits = subreddits or TARGET_SUBREDDITS

    all_posts = []

    for subreddit_name in subreddits:
        try:
            posts = fetch_subreddit_posts(
                reddit=reddit,
                subreddit_name=subreddit_name,
                limit=limit_per_sub,
                min_outlier_score=min_outlier_score,
            )
            all_posts.extend(posts)
        except Exception as e:
            print(f"Warning: Failed to fetch from r/{subreddit_name}: {e}")

    # Sort combined results by outlier score
    all_posts.sort(key=lambda x: x["outlier_score"], reverse=True)

    return all_posts
