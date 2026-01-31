"""
Pain point miner for e-commerce problems.

Searches Reddit for complaints and frustrations in e-commerce subreddits,
scores them by engagement, and categorizes them for product development.
"""

from typing import Optional

from execution.reddit_fetcher import get_reddit_client

# Pain-focused keywords targeting e-commerce complaints
PAIN_KEYWORDS = [
    # Frustration signals
    "frustrated with shopify",
    "hate my shopify",
    "shopify problem",
    "sick of",
    "tired of",
    "annoyed with",
    # Help-seeking
    "struggling with ecommerce",
    "need help with store",
    "can't figure out",
    "anyone else having issues",
    "how do i fix",
    # Specific pains
    "conversion rate low",
    "cart abandonment",
    "shipping nightmare",
    "inventory management hell",
    "returns killing me",
    "fulfillment issues",
    "customer service overwhelmed",
    "pricing strategy broken",
    "marketing not working",
    "ads not converting",
    "traffic but no sales",
    "abandoned checkout",
    "refund requests",
    "chargebacks",
]

# Target subreddits for e-commerce pain points
PAIN_SUBREDDITS = [
    "shopify",
    "ecommerce",
    "dropship",
    "Entrepreneur",
    "smallbusiness",
    "FulfillmentByAmazon",
]

# Category keywords for classification
CATEGORY_KEYWORDS = {
    "shipping": [
        "shipping",
        "fulfillment",
        "delivery",
        "courier",
        "usps",
        "fedex",
        "ups",
        "tracking",
    ],
    "inventory": [
        "inventory",
        "stock",
        "out of stock",
        "oversold",
        "warehouse",
        "storage",
    ],
    "conversion": [
        "conversion",
        "convert",
        "sales funnel",
        "checkout",
        "cart abandonment",
        "bounce rate",
    ],
    "returns": ["return", "refund", "chargeback", "dispute", "exchange"],
    "pricing": ["pricing", "price", "margin", "profit", "cost", "expensive", "cheap"],
    "marketing": [
        "marketing",
        "ads",
        "advertising",
        "facebook ads",
        "google ads",
        "traffic",
        "seo",
        "ppc",
    ],
}


def search_pain_points(
    subreddits: Optional[list[str]] = None,
    keywords: Optional[list[str]] = None,
    limit: int = 100,
    time_filter: str = "month",
) -> list[dict]:
    """
    Search Reddit for pain points using complaint-focused keywords.

    Args:
        subreddits: List of subreddits to search (default: PAIN_SUBREDDITS)
        keywords: List of keywords to search for (default: PAIN_KEYWORDS)
        limit: Maximum posts per keyword per subreddit
        time_filter: Time filter for search ("hour", "day", "week", "month", "year", "all")

    Returns:
        List of pain point dicts sorted by engagement score (upvotes + comments) descending.
        Each dict contains: title, body, score, comments, url, keyword, subreddit
    """
    reddit = get_reddit_client()
    subreddits = subreddits or PAIN_SUBREDDITS
    keywords = keywords or PAIN_KEYWORDS

    pain_points = []
    seen_ids = set()  # For deduplication

    for subreddit_name in subreddits:
        try:
            subreddit = reddit.subreddit(subreddit_name)

            for keyword in keywords:
                try:
                    for post in subreddit.search(
                        keyword, limit=limit, time_filter=time_filter
                    ):
                        # Deduplicate by post ID
                        if post.id in seen_ids:
                            continue
                        seen_ids.add(post.id)

                        # Get first 500 chars of body
                        body = post.selftext or ""
                        body = body[:500] if len(body) > 500 else body

                        engagement_score = post.score + post.num_comments

                        pain_points.append(
                            {
                                "id": post.id,
                                "title": post.title,
                                "body": body,
                                "score": post.score,
                                "comments": post.num_comments,
                                "engagement_score": engagement_score,
                                "url": f"https://reddit.com{post.permalink}",
                                "keyword": keyword,
                                "subreddit": subreddit_name,
                            }
                        )
                except Exception as e:
                    # Continue with other keywords if one fails
                    print(
                        f"Warning: Search failed for keyword '{keyword}' in r/{subreddit_name}: {e}"
                    )
                    continue

        except Exception as e:
            # Continue with other subreddits if one fails
            print(f"Warning: Failed to access r/{subreddit_name}: {e}")
            continue

    # Sort by engagement score descending
    pain_points.sort(key=lambda x: x["engagement_score"], reverse=True)

    return pain_points


def categorize_pain_point(pain_point: dict) -> str:
    """
    Categorize a pain point based on keywords in title and body.

    Args:
        pain_point: Pain point dict with 'title' and 'body' keys

    Returns:
        Category string: "shipping", "inventory", "conversion", "returns", "pricing", "marketing", or "other"
    """
    combined_text = (
        f"{pain_point.get('title', '')} {pain_point.get('body', '')}".lower()
    )

    # Check each category
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in combined_text:
                return category

    return "other"


def get_top_pain_points(limit: int = 20) -> list[dict]:
    """
    Convenience function to get top pain points across all subreddits and keywords.

    Args:
        limit: Maximum number of pain points to return

    Returns:
        Top N pain points by engagement, with category added
    """
    pain_points = search_pain_points()

    # Add category to each pain point
    for pp in pain_points:
        pp["category"] = categorize_pain_point(pp)

    return pain_points[:limit]
