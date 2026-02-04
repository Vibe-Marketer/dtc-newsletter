"""
Perplexity API client for web-grounded research.
DOE-VERSION: 2026.01.31

Two-stage research pattern:
1. search_trends() - Get trending e-commerce topics with citations
2. deep_dive_topic() - Detailed analysis of specific topic

Uses OpenAI-compatible API with Perplexity's sonar-pro model for best quality.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Install: pip install openai (Perplexity uses OpenAI-compatible API)
from openai import OpenAI

PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
DEFAULT_MODEL = "sonar-pro"  # Best quality per user decision

# Default cache directory for Perplexity research
DEFAULT_CACHE_DIR = Path("data/content_cache/perplexity")


def get_client() -> OpenAI:
    """
    Initialize Perplexity client using OpenAI-compatible API.

    Returns:
        OpenAI client configured for Perplexity API

    Raises:
        ValueError: If PERPLEXITY_API_KEY environment variable is not set
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY environment variable required")
    return OpenAI(api_key=api_key, base_url=PERPLEXITY_BASE_URL)


def search_trends(
    topic: str = "e-commerce DTC",
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Stage 1: Get trending topics with citations.

    Searches for viral and trending topics in the specified area,
    focusing on recent content from the last week.

    Args:
        topic: Focus area for trend search (default: "e-commerce DTC")
        model: Perplexity model to use (default: sonar-pro)

    Returns:
        dict with:
        - content: Summary text of trending topics
        - citations: List of source URLs
        - model: Model used
        - fetched_at: ISO timestamp

    Raises:
        ValueError: If API key is not configured
    """
    client = get_client()

    prompt = f"""What are the most viral and trending topics in {topic} this week? 
Focus on:
- Viral content and discussions
- New strategies or tactics gaining traction
- Controversies or hot debates
- Success stories and case studies
- Emerging tools or platforms

Provide specific examples with data points where available."""

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a trend research analyst specializing in e-commerce and DTC brands. Provide factual, data-driven insights with specific examples.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        # Extract response content and citations
        message = completion.choices[0].message
        content = message.content or ""

        # Perplexity returns citations in the completion object
        citations = getattr(completion, "citations", []) or []

        return {
            "content": content,
            "citations": citations,
            "model": model,
            "topic": topic,
            "query_type": "search_trends",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        # Re-raise with context
        raise RuntimeError(f"Perplexity API error during search_trends: {e}") from e


def deep_dive_topic(
    topic: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Stage 2: Deep dive on specific topic.

    Provides detailed analysis of a specific topic for e-commerce businesses,
    with actionable insights and specific recommendations.

    Args:
        topic: Specific topic to analyze in depth
        model: Perplexity model to use (default: sonar-pro)

    Returns:
        dict with:
        - content: Detailed analysis text
        - citations: List of source URLs
        - model: Model used
        - fetched_at: ISO timestamp

    Raises:
        ValueError: If API key is not configured
    """
    client = get_client()

    prompt = f"""Provide a detailed analysis of "{topic}" for e-commerce and DTC businesses.

Include:
1. What is this trend and why is it significant?
2. Who is doing this well? (specific examples with results)
3. Key success factors and common mistakes
4. How can e-commerce brands implement this?
5. Expected ROI or impact based on available data

Be specific with numbers, case studies, and actionable recommendations."""

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an e-commerce strategy consultant. Provide detailed, actionable analysis with specific examples and data.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        message = completion.choices[0].message
        content = message.content or ""
        citations = getattr(completion, "citations", []) or []

        return {
            "content": content,
            "citations": citations,
            "model": model,
            "topic": topic,
            "query_type": "deep_dive",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise RuntimeError(f"Perplexity API error during deep_dive_topic: {e}") from e


def save_research(
    research: dict,
    topic_slug: str,
    cache_dir: Optional[Path] = None,
) -> Path:
    """
    Save research results to cache directory.

    Creates a JSON file with date prefix and topic slug for easy identification.

    Args:
        research: Research result dict from search_trends or deep_dive_topic
        topic_slug: URL-safe slug for the topic (e.g., "dtc-email-marketing")
        cache_dir: Directory to save to (default: data/content_cache/perplexity)

    Returns:
        Path to saved file
    """
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with date prefix
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    query_type = research.get("query_type", "research")
    filename = f"{date_str}_{query_type}_{topic_slug}.json"

    filepath = cache_dir / filename

    # Add metadata
    research_with_meta = {
        "metadata": {
            "source": "perplexity",
            "query_type": query_type,
            "topic_slug": topic_slug,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        },
        "research": research,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(research_with_meta, f, indent=2, ensure_ascii=False)

    return filepath


def load_research(
    filepath: Path,
) -> dict:
    """
    Load research from cache file.

    Args:
        filepath: Path to cache file

    Returns:
        Research dict

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Research file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("research", data)


def get_recent_research(
    cache_dir: Optional[Path] = None,
    days_back: int = 7,
) -> list[dict]:
    """
    Get research from the last N days.

    Args:
        cache_dir: Cache directory to scan
        days_back: Number of days to look back

    Returns:
        List of research dicts, sorted by date descending
    """
    from datetime import timedelta

    cache_dir = cache_dir or DEFAULT_CACHE_DIR

    if not cache_dir.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    results = []

    for filepath in cache_dir.glob("*.json"):
        # Extract date from filename (YYYY-MM-DD prefix)
        date_str = filepath.stem[:10]

        if date_str >= cutoff_str:
            try:
                research = load_research(filepath)
                research["_filepath"] = str(filepath)
                results.append(research)
            except (json.JSONDecodeError, IOError):
                continue

    # Sort by fetched_at descending
    results.sort(key=lambda x: x.get("fetched_at", ""), reverse=True)

    return results
