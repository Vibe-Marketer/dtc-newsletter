#!/usr/bin/env python3
"""
Search-based content fetcher for DTCNews.
DOE-VERSION: 2026.02.04

Uses Perplexity/Sonar via OpenRouter to find viral ecommerce content.
Searches across Reddit, Twitter, YouTube, and other sources via web search.

This is the PRIMARY content source - no Reddit API needed!

Usage:
    python execution/search_fetcher.py
    python execution/search_fetcher.py --queries "email marketing,ugc ads,meta ads"
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DOE_VERSION = "2026.02.04"

# Use OpenRouter to access Perplexity/Sonar
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "perplexity/sonar"  # Web-grounded search model

# Search queries optimized for finding viral ecommerce content
DEFAULT_QUERIES = [
    "viral ecommerce tips reddit this week",
    "dropshipping success story 2024 2025",
    "shopify store case study revenue",
    "DTC brand marketing strategy working",
    "ecommerce email marketing results",
    "meta ads ecommerce ROAS strategy",
    "first sale shopify how to",
    "ugc ads ecommerce tiktok",
]


def get_openrouter_client() -> OpenAI:
    """Get OpenRouter client for Perplexity/Sonar access."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set in environment")
    return OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)


def search_viral_content(query: str, client: OpenAI) -> dict:
    """
    Search for viral ecommerce content using Perplexity/Sonar via OpenRouter.

    Args:
        query: Search query
        client: OpenRouter client

    Returns:
        Dict with content items found
    """
    prompt = f"""Search for viral and high-engagement content about: {query}

Find specific posts, videos, or discussions that went viral or got high engagement.
For each piece of content found, extract:
1. Title or headline
2. Key insight or tactic mentioned
3. Any numbers/results mentioned (revenue, sales, ROAS, etc.)
4. Source (Reddit, Twitter/X, YouTube, blog, etc.)
5. Approximate engagement (upvotes, likes, views if available)

Focus on content from the last 30 days that contains ACTIONABLE tactics.
Look especially for:
- Reddit posts with 100+ upvotes
- Twitter/X threads with good engagement  
- YouTube videos about ecommerce tactics
- Case studies with real numbers

Return as JSON array with this structure:
[
  {{
    "title": "Post/video title",
    "summary": "Key insight or tactic (2-3 sentences)",
    "results": "Any numbers mentioned (revenue, ROAS, sales, etc.)",
    "source": "reddit/twitter/youtube/blog",
    "source_detail": "r/shopify or @username or channel name",
    "engagement": "upvotes/likes/views estimate",
    "url": "URL if available, otherwise null"
  }}
]

Return ONLY the JSON array, no other text."""

    try:
        completion = client.chat.completions.create(
            model=MODEL,  # perplexity/sonar via OpenRouter
            messages=[
                {
                    "role": "system",
                    "content": "You are a content researcher finding viral ecommerce content. Return only valid JSON arrays.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        response_text = completion.choices[0].message.content or "[]"

        # Extract JSON from response
        json_match = re.search(r"\[[\s\S]*\]", response_text)
        if json_match:
            items = json.loads(json_match.group())
        else:
            items = []

        # Get citations if available
        citations = getattr(completion, "citations", []) or []

        return {
            "query": query,
            "items": items,
            "citations": citations,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    except json.JSONDecodeError:
        return {
            "query": query,
            "items": [],
            "citations": [],
            "error": "Failed to parse JSON response",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "query": query,
            "items": [],
            "citations": [],
            "error": str(e),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }


def estimate_outlier_score(item: dict) -> float:
    """
    Estimate outlier score from engagement data.

    Args:
        item: Content item dict

    Returns:
        Estimated outlier score (1.0 - 10.0)
    """
    engagement = (item.get("engagement") or "").lower()
    results = (item.get("results") or "").lower()

    score = 2.0  # Base score for being found

    # Boost for high engagement
    if any(x in engagement for x in ["1000", "1k", "2k", "5k", "10k", "viral"]):
        score += 2.0
    elif any(x in engagement for x in ["500", "hundreds"]):
        score += 1.0
    elif any(x in engagement for x in ["100", "200", "300"]):
        score += 0.5

    # Boost for concrete results
    if any(x in results for x in ["$", "revenue", "sales", "roas", "roi"]):
        score += 1.5
    if any(x in results for x in ["k", "000", "million"]):
        score += 1.0

    # Boost for specific tactics
    summary = (item.get("summary") or "").lower()
    if any(x in summary for x in ["step", "how to", "exactly", "strategy", "template"]):
        score += 0.5

    return min(score, 10.0)


def fetch_all_content(
    queries: list[str] | None = None, verbose: bool = True
) -> list[dict]:
    """
    Fetch content from all queries.

    Args:
        queries: List of search queries (uses defaults if None)
        verbose: Print progress

    Returns:
        List of content items with outlier scores
    """
    queries = queries or DEFAULT_QUERIES

    try:
        client = get_openrouter_client()
    except ValueError as e:
        print(f"ERROR: {e}")
        return []

    all_items = []
    seen_titles = set()

    for i, query in enumerate(queries, 1):
        if verbose:
            print(f"[{i}/{len(queries)}] Searching: {query[:50]}...")

        result = search_viral_content(query, client)

        if result.get("error"):
            if verbose:
                print(f"  Error: {result['error']}")
            continue

        items = result.get("items", [])
        if verbose:
            print(f"  Found {len(items)} items")

        for item in items:
            # Dedupe by title
            title = item.get("title", "").lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)

                # Add metadata
                item["source"] = item.get("source", "search")
                item["outlier_score"] = estimate_outlier_score(item)
                item["search_query"] = query

                all_items.append(item)

    # Sort by outlier score
    all_items.sort(key=lambda x: x.get("outlier_score", 0), reverse=True)

    return all_items


def main():
    parser = argparse.ArgumentParser(
        description="Fetch viral ecommerce content via search",
    )
    parser.add_argument(
        "--queries",
        "-q",
        help="Comma-separated search queries (uses defaults if not provided)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=50,
        help="Max items to return (default: 50)",
    )
    args = parser.parse_args()

    print(f"[search_fetcher] v{DOE_VERSION}")
    print()

    # Parse queries
    queries = None
    if args.queries:
        queries = [q.strip() for q in args.queries.split(",")]

    # Fetch content
    items = fetch_all_content(queries)

    if not items:
        print("\nNo content found. Check your PERPLEXITY_API_KEY.")
        return 1

    # Limit results
    items = items[: args.limit]

    print()
    print("=" * 60)
    print(f"Found {len(items)} content items")
    print("=" * 60)

    # Show top 10
    print("\nTop 10 by outlier score:")
    for i, item in enumerate(items[:10], 1):
        score = item.get("outlier_score", 0)
        title = item.get("title", "No title")[:60]
        source = item.get("source_detail", item.get("source", "unknown"))
        print(f"{i}. [{score:.1f}x] {title}")
        print(f"   Source: {source}")
        if item.get("results"):
            print(f"   Results: {item['results'][:60]}")
        print()

    # Save output
    output_path = args.output
    if not output_path:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_path = f"output/content_{date_str}.json"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "metadata": {
            "source": "perplexity_search",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "total_items": len(items),
        },
        "content": items,
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
