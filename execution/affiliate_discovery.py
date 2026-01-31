"""
Affiliate discovery via Perplexity API.
DOE-VERSION: 2026.01.31

Uses Perplexity's web-grounded research to discover relevant affiliate
programs for a given newsletter topic. Returns structured results with
commission rates, accessibility status, and topic fit.
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from openai import OpenAI
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# API configuration
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
DEFAULT_MODEL = "sonar-pro"

# Default cache directory
DEFAULT_CACHE_DIR = Path("data/affiliate_cache")


class AffiliateProgram(BaseModel):
    """A discovered affiliate program with structured metadata."""

    name: str = Field(description="Program name")
    company: str = Field(description="Company/brand name")
    commission_rate: str = Field(description="Commission rate (e.g., '20%' or '$50')")
    commission_type: Literal["percentage", "flat_fee"] = Field(
        description="Type of commission"
    )
    is_recurring: bool = Field(description="Whether commission is recurring")
    product_description: str = Field(description="What the product/service does")
    topic_fit: str = Field(description="Why this fits the newsletter topic")
    network: Literal["ShareASale", "Awin", "PartnerStack", "Impact", "direct"] = Field(
        description="Affiliate network or 'direct' if direct program"
    )
    signup_accessible: bool = Field(
        description="Whether signup is open (not waitlisted/closed)"
    )


class AffiliateDiscoveryResult(BaseModel):
    """Result of affiliate discovery including programs and citations."""

    affiliates: list[AffiliateProgram] = Field(
        description="List of discovered affiliate programs"
    )
    search_citations: list[str] = Field(
        description="Source URLs from Perplexity research"
    )
    topic: str = Field(description="The topic that was searched")


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


def classify_commission(rate: float, is_recurring: bool) -> str:
    """
    Classify commission rate quality based on industry thresholds.

    Per RESEARCH.md:
    - Recurring: excellent >= 20%, good >= 10%, mediocre < 10%
    - One-time: good >= 30%, mediocre >= 15%, poor < 15%

    Args:
        rate: Commission rate as percentage (e.g., 20.0 for 20%)
        is_recurring: Whether the commission recurs

    Returns:
        One of: "excellent", "good", "mediocre", "poor"
    """
    if is_recurring:
        if rate >= 20:
            return "excellent"
        elif rate >= 10:
            return "good"
        else:
            return "mediocre"
    else:
        if rate >= 30:
            return "good"
        elif rate >= 15:
            return "mediocre"
        else:
            return "poor"


def parse_commission_rate(rate_str: str) -> float:
    """
    Extract numeric commission rate from string.

    Args:
        rate_str: Commission rate like "20%", "$50", "30% - 50%"

    Returns:
        Float percentage (e.g., 20.0 for "20%")
        For flat fees, returns 0.0 (classify as poor/mediocre)
    """
    # Handle percentage
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", rate_str)
    if match:
        return float(match.group(1))

    # Handle flat fee - return 0 as we can't compare to percentage thresholds
    if "$" in rate_str:
        return 0.0

    # Try to extract any number
    match = re.search(r"(\d+(?:\.\d+)?)", rate_str)
    if match:
        return float(match.group(1))

    return 0.0


def discover_affiliates(
    topic: str,
    newsletter_context: str = "",
    model: str = DEFAULT_MODEL,
    retry_on_malformed: bool = True,
) -> AffiliateDiscoveryResult:
    """
    Discover affiliate programs relevant to a newsletter topic.

    Uses Perplexity's sonar-pro model to research current affiliate
    programs, verifying accessibility and collecting commission details.

    Args:
        topic: The newsletter topic to find affiliates for
        newsletter_context: Additional context about the newsletter content
        model: Perplexity model to use (default: sonar-pro)
        retry_on_malformed: Whether to retry once on malformed response

    Returns:
        AffiliateDiscoveryResult with list of programs and citations

    Raises:
        ValueError: If API key not configured
        RuntimeError: If Perplexity API fails
    """
    client = get_client()

    context_clause = ""
    if newsletter_context:
        context_clause = f"\n\nNewsletter context: {newsletter_context}"

    prompt = f"""Find the top 5+ affiliate programs relevant to "{topic}" for DTC e-commerce businesses.{context_clause}

For each program, provide:
1. Program name and company
2. Commission rate (exact percentage or flat fee amount)
3. Commission type (percentage or flat_fee)
4. Whether it's recurring (true/false)
5. Brief product/service description
6. Why it specifically fits the topic "{topic}"
7. Affiliate network (ShareASale, Awin, PartnerStack, Impact, or "direct" if direct program)
8. Whether signup is currently accessible (not closed/waitlisted)

Focus on:
- Tools and SaaS products DTC brands actually use
- Programs with accessible signup (not closed/waitlisted)
- Recurring commission programs preferred over one-time

Return your response as a JSON array with objects containing these fields:
name, company, commission_rate, commission_type, is_recurring, product_description, topic_fit, network, signup_accessible

Example format:
[
  {{
    "name": "Program Name",
    "company": "Company Inc",
    "commission_rate": "20%",
    "commission_type": "percentage",
    "is_recurring": true,
    "product_description": "What it does",
    "topic_fit": "Why it fits this topic",
    "network": "ShareASale",
    "signup_accessible": true
  }}
]

Return ONLY the JSON array, no other text."""

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an affiliate marketing researcher for DTC e-commerce newsletters. Always return valid JSON arrays only, no markdown formatting or extra text.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        message = completion.choices[0].message
        content = message.content or ""

        # Extract citations if available
        citations = getattr(completion, "citations", []) or []

        # Parse JSON response
        try:
            # Clean up content - remove markdown code blocks if present
            content = content.strip()
            if content.startswith("```"):
                # Remove markdown code block
                lines = content.split("\n")
                content = "\n".join(
                    lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                )
                content = content.strip()

            affiliates_data = json.loads(content)

            # Validate each affiliate
            affiliates = []
            for item in affiliates_data:
                try:
                    affiliate = AffiliateProgram(**item)
                    affiliates.append(affiliate)
                except Exception as e:
                    logger.warning(f"Skipping invalid affiliate data: {e}")
                    continue

            return AffiliateDiscoveryResult(
                affiliates=affiliates,
                search_citations=citations,
                topic=topic,
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Malformed JSON response: {e}")
            if retry_on_malformed:
                logger.info("Retrying discovery...")
                return discover_affiliates(
                    topic=topic,
                    newsletter_context=newsletter_context,
                    model=model,
                    retry_on_malformed=False,
                )
            else:
                raise RuntimeError(f"Failed to parse affiliate response: {e}") from e

    except Exception as e:
        if "JSON" not in str(e):
            raise RuntimeError(
                f"Perplexity API error during discover_affiliates: {e}"
            ) from e
        raise


def save_affiliates(
    result: AffiliateDiscoveryResult,
    cache_dir: Optional[Path] = None,
) -> Path:
    """
    Save affiliate discovery results to cache.

    Creates a JSON file with date prefix and topic slug for easy identification.
    Cache has 24-hour TTL (per RESEARCH.md decision).

    Args:
        result: AffiliateDiscoveryResult to save
        cache_dir: Directory to save to (default: data/affiliate_cache)

    Returns:
        Path to saved file
    """
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with date prefix and topic slug
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    topic_slug = re.sub(r"[^a-zA-Z0-9]+", "-", result.topic.lower()).strip("-")
    filename = f"{date_str}-{topic_slug}-affiliates.json"

    filepath = cache_dir / filename

    # Prepare data with metadata
    data = {
        "metadata": {
            "source": "perplexity",
            "topic": result.topic,
            "topic_slug": topic_slug,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "ttl_hours": 24,
        },
        "result": result.model_dump(),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def load_affiliates(filepath: Path) -> AffiliateDiscoveryResult:
    """
    Load affiliate discovery results from cache file.

    Args:
        filepath: Path to cache file

    Returns:
        AffiliateDiscoveryResult

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Affiliate cache file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    result_data = data.get("result", data)
    return AffiliateDiscoveryResult(**result_data)


def get_cached_affiliates(
    topic: str,
    cache_dir: Optional[Path] = None,
    max_age_hours: int = 24,
) -> Optional[AffiliateDiscoveryResult]:
    """
    Get cached affiliate results if available and not expired.

    Args:
        topic: Topic to search for
        cache_dir: Cache directory
        max_age_hours: Maximum age of cache in hours (default: 24)

    Returns:
        AffiliateDiscoveryResult if found and valid, None otherwise
    """
    from datetime import timedelta

    cache_dir = cache_dir or DEFAULT_CACHE_DIR

    if not cache_dir.exists():
        return None

    topic_slug = re.sub(r"[^a-zA-Z0-9]+", "-", topic.lower()).strip("-")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

    # Look for matching files
    for filepath in cache_dir.glob(f"*-{topic_slug}-affiliates.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            saved_at = data.get("metadata", {}).get("saved_at")
            if saved_at:
                saved_time = datetime.fromisoformat(saved_at.replace("Z", "+00:00"))
                if saved_time > cutoff:
                    return AffiliateDiscoveryResult(**data.get("result", data))
        except (json.JSONDecodeError, IOError, ValueError):
            continue

    return None
