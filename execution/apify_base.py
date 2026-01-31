"""
Shared Apify utilities for stretch source aggregators.
DOE-VERSION: 2026.01.31

Provides:
- Base actor invocation with error handling
- Retry logic with exponential backoff
- TTL caching for results (24 hours)
"""

import os
import logging
from typing import Any, Callable
from datetime import datetime, timezone

from apify_client import ApifyClient
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# 24-hour cache for stretch source results
_cache = TTLCache(maxsize=100, ttl=24 * 60 * 60)


def get_apify_client() -> ApifyClient:
    """
    Get configured Apify client.

    Raises:
        ValueError: If APIFY_TOKEN not configured
    """
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise ValueError(
            "APIFY_TOKEN not configured. "
            "Get your token at https://console.apify.com/account/integrations"
        )
    return ApifyClient(token)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def fetch_from_apify(actor_id: str, run_input: dict) -> list[dict]:
    """
    Invoke an Apify actor and return results.

    Args:
        actor_id: Actor identifier (e.g., "apidojo/tweet-scraper")
        run_input: Input parameters for the actor

    Returns:
        List of result items from the actor run

    Raises:
        Exception: On actor failure after retries
    """
    client = get_apify_client()

    logger.info(f"Starting Apify actor: {actor_id}")
    run = client.actor(actor_id).call(run_input=run_input)

    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    logger.info(f"Actor {actor_id} returned {len(items)} items")

    return items


def fetch_with_retry(
    source_name: str,
    fetch_fn: Callable[[], list[dict]],
    cache_key: str | None = None,
) -> dict:
    """
    Execute a fetch function with retry and graceful degradation.

    Args:
        source_name: Name for logging (e.g., "twitter")
        fetch_fn: Function that returns list of items
        cache_key: Optional key for caching results

    Returns:
        Dict with keys: success, items, error, cached, timestamp
    """
    # Check cache first
    if cache_key and cache_key in _cache:
        logger.info(f"{source_name}: returning cached results")
        return {
            "success": True,
            "items": _cache[cache_key],
            "error": None,
            "cached": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    try:
        items = fetch_fn()

        # Cache results
        if cache_key:
            _cache[cache_key] = items

        return {
            "success": True,
            "items": items,
            "error": None,
            "cached": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.warning(f"{source_name} failed after retries: {e}")
        return {
            "success": False,
            "items": [],
            "error": str(e),
            "cached": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def clear_cache() -> None:
    """Clear the TTL cache (useful for testing)."""
    _cache.clear()
