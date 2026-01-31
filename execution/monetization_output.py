"""
Monetization output formatter.
DOE-VERSION: 2026.01.31

Combines affiliate programs and product alternatives into a unified
markdown output for decision-making. Creates side-by-side comparison
with tables and expanded details for each option.
"""

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Import models from other modules
from execution.affiliate_discovery import (
    AffiliateProgram,
    classify_commission,
    parse_commission_rate,
)
from execution.product_alternatives import ProductIdea

# Default output directory
DEFAULT_OUTPUT_DIR = Path("output/monetization")

# Claude model for rationale generation
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-20250514"


@dataclass
class MonetizationOption:
    """Unified model for affiliate or product monetization option."""

    type: Literal["affiliate", "product"]
    name: str
    description: str
    pitch_angle: str

    # For affiliates
    commission_rate: Optional[str] = None
    commission_quality: Optional[str] = None  # excellent/good/mediocre/poor
    network: Optional[str] = None

    # For products
    product_type: Optional[str] = None
    build_complexity: Optional[str] = None
    estimated_value: Optional[str] = None


def affiliate_to_option(
    affiliate: AffiliateProgram, pitch: str = ""
) -> MonetizationOption:
    """
    Convert AffiliateProgram to MonetizationOption.

    Args:
        affiliate: AffiliateProgram to convert
        pitch: Optional pitch angle for the affiliate

    Returns:
        MonetizationOption representing the affiliate
    """
    rate = parse_commission_rate(affiliate.commission_rate)
    quality = classify_commission(rate, affiliate.is_recurring)

    return MonetizationOption(
        type="affiliate",
        name=affiliate.name,
        description=affiliate.product_description,
        pitch_angle=pitch,
        commission_rate=affiliate.commission_rate,
        commission_quality=quality,
        network=affiliate.network,
    )


def product_to_option(product: ProductIdea) -> MonetizationOption:
    """
    Convert ProductIdea to MonetizationOption.

    Args:
        product: ProductIdea to convert

    Returns:
        MonetizationOption representing the product
    """
    return MonetizationOption(
        type="product",
        name=product.concept,
        description=product.why_beats_affiliate,
        pitch_angle=product.pitch_angle,
        product_type=product.product_type,
        build_complexity=product.build_complexity,
        estimated_value=product.estimated_value,
    )


def generate_ranking_rationale(
    affiliates: list[MonetizationOption],
    products: list[MonetizationOption],
    model: str = DEFAULT_CLAUDE_MODEL,
) -> dict[str, list[str]]:
    """
    Generate ranking rationale using Claude.

    Explains why #1 beats #2, #2 beats #3, etc. for each track.

    Args:
        affiliates: List of affiliate options (already ranked)
        products: List of product options (already ranked)
        model: Claude model to use

    Returns:
        Dict with 'affiliates' and 'products' keys, each containing
        list of rationale strings
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        # Return empty rationales if no API key
        return {"affiliates": [], "products": []}

    client = anthropic.Anthropic(api_key=api_key)

    # Build context for affiliates
    affiliate_context = ""
    for i, aff in enumerate(affiliates[:3], 1):
        affiliate_context += f"{i}. {aff.name}: {aff.commission_rate} ({aff.commission_quality}), {aff.network}\n"

    # Build context for products
    product_context = ""
    for i, prod in enumerate(products[:3], 1):
        product_context += f"{i}. {prod.name}: {prod.estimated_value}, {prod.build_complexity} complexity\n"

    prompt = f"""Given these ranked monetization options, briefly explain why each rank beats the next.

AFFILIATES (ranked):
{affiliate_context}

PRODUCTS (ranked):
{product_context}

For each track, provide 1-sentence rationales for why #1 beats #2, and why #2 beats #3.

Return as JSON:
{{
  "affiliates": [
    "#1 beats #2 because: [reason]",
    "#2 beats #3 because: [reason]"
  ],
  "products": [
    "#1 beats #2 because: [reason]",
    "#2 beats #3 because: [reason]"
  ]
}}

Keep rationales brief (1 sentence each). Return ONLY the JSON."""

    try:
        message = client.messages.create(
            model=model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        content = message.content[0].text.strip()

        # Clean up markdown if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(
                lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            )
            content = content.strip()

        import json

        result = json.loads(content)
        return result

    except Exception as e:
        logger.warning(f"Failed to generate ranking rationale: {e}")
        return {"affiliates": [], "products": []}


def format_monetization_output(
    affiliates: list[AffiliateProgram],
    products: list[ProductIdea],
    topic: str,
    pitches: dict[str, str],
    include_rationale: bool = True,
) -> str:
    """
    Format affiliates and products into unified markdown output.

    Creates side-by-side comparison with tables and expanded details.

    Args:
        affiliates: List of AffiliateProgram objects (already ranked)
        products: List of ProductIdea objects (already ranked)
        topic: The newsletter topic
        pitches: Dict mapping affiliate name to pitch text
        include_rationale: Whether to generate and include ranking rationale

    Returns:
        Formatted markdown string
    """
    # Convert to unified options
    affiliate_options = [
        affiliate_to_option(aff, pitches.get(aff.name, "")) for aff in affiliates[:3]
    ]
    product_options = [product_to_option(prod) for prod in products[:3]]

    # Generate rationale if requested
    rationale = {"affiliates": [], "products": []}
    if include_rationale and (affiliate_options or product_options):
        rationale = generate_ranking_rationale(affiliate_options, product_options)

    # Build output
    output = f"# Monetization Options: {topic}\n\n"

    # Add note if few affiliates
    if len(affiliates) < 2:
        output += "> **Note:** Limited affiliate options found for this topic. Consider the product alternatives below.\n\n"

    # Affiliate table
    output += "## Top 3 Affiliate Opportunities\n\n"
    if affiliate_options:
        output += "| # | Program | Commission | Quality | Network |\n"
        output += "|---|---------|------------|---------|--------|\n"
        for i, aff in enumerate(affiliate_options, 1):
            output += f"| {i} | {aff.name} | {aff.commission_rate or 'N/A'} | {aff.commission_quality or 'N/A'} | {aff.network or 'N/A'} |\n"
    else:
        output += "*No affiliate programs found for this topic.*\n"
    output += "\n"

    # Product table
    output += "## Top 3 Product Alternatives\n\n"
    if product_options:
        output += "| # | Concept | Type | Complexity | Value |\n"
        output += "|---|---------|------|------------|-------|\n"
        for i, prod in enumerate(product_options, 1):
            # Truncate long concepts
            concept = prod.name[:50] + "..." if len(prod.name) > 50 else prod.name
            output += f"| {i} | {concept} | {prod.product_type or 'N/A'} | {prod.build_complexity or 'N/A'} | {prod.estimated_value or 'N/A'} |\n"
    else:
        output += "*No product alternatives generated.*\n"
    output += "\n"

    # Ranking rationale
    if include_rationale and (rationale.get("affiliates") or rationale.get("products")):
        output += "## Ranking Rationale\n\n"

        if rationale.get("affiliates"):
            output += "**Affiliates:**\n"
            for reason in rationale["affiliates"]:
                output += f"- {reason}\n"
            output += "\n"

        if rationale.get("products"):
            output += "**Products:**\n"
            for reason in rationale["products"]:
                output += f"- {reason}\n"
            output += "\n"

    # Full details
    output += "## Full Details\n\n"

    # Affiliate details
    for i, (aff, aff_opt) in enumerate(zip(affiliates[:3], affiliate_options), 1):
        output += f"### Affiliate #{i}: {aff.name}\n\n"
        output += (
            f"**Commission:** {aff.commission_rate} ({aff_opt.commission_quality})\n"
        )
        output += f"**Network:** {aff.network}\n"
        output += f"**Topic Fit:** {aff.topic_fit}\n"
        if aff_opt.pitch_angle:
            output += f"**Pitch Angle:**\n> {aff_opt.pitch_angle}\n"
        output += "\n"

    # Product details
    for i, prod in enumerate(products[:3], 1):
        output += f"### Product #{i}: {prod.concept}\n\n"
        output += f"**Type:** {prod.product_type}\n"
        output += f"**Complexity:** {prod.build_complexity}\n"
        output += f"**Value:** {prod.estimated_value}\n"
        output += f"**Why It Beats Affiliate:** {prod.why_beats_affiliate}\n"
        output += f"**Pitch Angle:**\n> {prod.pitch_angle}\n"
        output += "\n"

    # Footer
    output += "---\n"
    output += (
        f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*\n"
    )

    return output


def save_output(
    content: str,
    topic_slug: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Path:
    """
    Save monetization output to file.

    Args:
        content: Markdown content to save
        topic_slug: Slug for the topic (used in filename)
        output_dir: Directory to save to (default: output/monetization)

    Returns:
        Path to saved file
    """
    # Create directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with date
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Clean up slug
    clean_slug = re.sub(r"[^a-zA-Z0-9]+", "-", topic_slug.lower()).strip("-")
    filename = f"{date_str}-{clean_slug}.md"

    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def load_output(filepath: Path) -> str:
    """
    Load monetization output from file.

    Args:
        filepath: Path to file to load

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Monetization output not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
