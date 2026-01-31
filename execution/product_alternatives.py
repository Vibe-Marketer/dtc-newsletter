"""
Product alternatives generator for monetization decisions.
DOE-VERSION: 2026.01.31

Generates product ideas as alternatives to affiliate recommendations.
Products are ranked by value/complexity ratio to prioritize high-value,
low-effort options for the DTC Newsletter audience.
"""

import logging
import os
import re
from datetime import datetime, timezone
from typing import Literal, Optional

from openai import OpenAI
from pydantic import BaseModel, Field
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# API configuration
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
DEFAULT_PERPLEXITY_MODEL = "sonar-pro"
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Product type options per PROJECT.md
ProductType = Literal[
    "HTML tool",
    "automation",
    "GPT",
    "Google Sheet",
    "PDF",
    "prompt pack",
]

# Build complexity levels
BuildComplexity = Literal["easy", "medium", "hard"]

# Voice guidance for pitch generation (matches pitch_generator.py)
VOICE_GUIDANCE = """
Voice requirements (Hormozi/Suby hybrid):
- Short, punchy sentences (under 15 words typically)
- Direct, confident, slightly irreverent tone
- Specific numbers and math: "$X invested -> $Y returned"
- Zero fluff - delete "basically," "essentially," "just"
- Concrete, specific examples (never hypothetical)
- 80% value / 20% ask ratio
"""


class ProductIdea(BaseModel):
    """A product idea that could be created as an affiliate alternative."""

    concept: str = Field(description="Product concept in 1 sentence")
    product_type: ProductType = Field(description="Type of product")
    estimated_value: str = Field(description="Estimated perceived value like '$47-97'")
    build_complexity: BuildComplexity = Field(description="Build complexity level")
    why_beats_affiliate: str = Field(
        description="Why this might beat affiliate option (1 sentence)"
    )
    pitch_angle: str = Field(description="Ready-to-use pitch angle (2-3 sentences)")


class ProductAlternativesResult(BaseModel):
    """Result of product alternatives generation."""

    products: list[ProductIdea] = Field(description="List of product ideas")
    topic: str = Field(description="The topic these products address")
    generated_at: str = Field(description="ISO timestamp of generation")


def get_perplexity_client() -> OpenAI:
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


def get_claude_client() -> anthropic.Anthropic:
    """
    Initialize Claude client.

    Returns:
        Anthropic client

    Raises:
        ValueError: If ANTHROPIC_API_KEY environment variable is not set
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable required")
    return anthropic.Anthropic(api_key=api_key)


def research_pain_points(
    topic: str,
    newsletter_context: str = "",
    model: str = DEFAULT_PERPLEXITY_MODEL,
) -> str:
    """
    Research pain points around a topic using Perplexity.

    Stage 1 of the two-stage approach per RESEARCH.md.

    Args:
        topic: The newsletter topic to research
        newsletter_context: Additional context about the newsletter
        model: Perplexity model to use

    Returns:
        Pain points research summary
    """
    client = get_perplexity_client()

    context_clause = ""
    if newsletter_context:
        context_clause = f"\n\nNewsletter context: {newsletter_context}"

    prompt = f"""Research the top 5 pain points and problems that DTC e-commerce brand owners face related to "{topic}".{context_clause}

Focus on:
- Specific, narrow problems (not broad issues)
- Problems that could be solved with a simple digital tool
- Issues brand owners complain about in forums, communities, and social media
- Problems where the existing solutions are expensive or complex

For each pain point:
1. Describe the specific problem (1-2 sentences)
2. Why it's frustrating for DTC brand owners
3. What they're currently doing to solve it (if anything)
4. How much they'd pay to solve it ($20-100 range)

Return as a structured list of pain points."""

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a product researcher for DTC e-commerce. Find specific, solvable problems.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        return completion.choices[0].message.content or ""

    except Exception as e:
        logger.warning(f"Perplexity research failed: {e}")
        raise RuntimeError(f"Perplexity API error during research: {e}") from e


def generate_product_ideas(
    topic: str,
    pain_points: str,
    newsletter_context: str = "",
    model: str = DEFAULT_CLAUDE_MODEL,
) -> list[ProductIdea]:
    """
    Generate product ideas based on pain points using Claude.

    Stage 2 of the two-stage approach per RESEARCH.md.

    Args:
        topic: The newsletter topic
        pain_points: Research from Perplexity about pain points
        newsletter_context: Additional context about the newsletter
        model: Claude model to use

    Returns:
        List of 3 ProductIdea objects
    """
    client = get_claude_client()

    context_clause = ""
    if newsletter_context:
        context_clause = f"\n\nNewsletter context: {newsletter_context}"

    prompt = f"""Based on the following pain points research for "{topic}", generate 3 product ideas that could be sold to DTC brand owners.{context_clause}

Pain points research:
{pain_points}

Product constraints (per PROJECT.md):
- Target $27-97 price range
- Must solve a specific, narrow problem
- Prefer HTML tools and automations (they're harder to create, so more valuable)
- Product types allowed: HTML tool, automation, GPT, Google Sheet, PDF, prompt pack

For each product, provide:
1. Concept: A 1-sentence description of the product
2. Product type: One of [HTML tool, automation, GPT, Google Sheet, PDF, prompt pack]
3. Estimated value: Price range like "$47-97" based on perceived value
4. Build complexity: One of [easy, medium, hard]
5. Why beats affiliate: 1 sentence on why creating this is better than recommending an affiliate
6. Pitch angle: 2-3 sentences ready for Section 4 "Tool of the Week"

{VOICE_GUIDANCE}

Return as JSON array with objects containing: concept, product_type, estimated_value, build_complexity, why_beats_affiliate, pitch_angle

Example:
[
  {{
    "concept": "HTML calculator that shows exactly how much inventory to order based on sell-through rate",
    "product_type": "HTML tool",
    "estimated_value": "$47-67",
    "build_complexity": "medium",
    "why_beats_affiliate": "You keep 100% of revenue instead of 15-30% commission on someone else's tool",
    "pitch_angle": "Stop guessing how much inventory to order. This calculator uses your actual sell-through data to tell you exactly what to buy. Plug in 3 numbers, get your order quantity. Takes 30 seconds."
  }}
]

Return ONLY the JSON array, no other text."""

    try:
        message = client.messages.create(
            model=model,
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        content = message.content[0].text.strip()

        # Clean up content - remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(
                lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            )
            content = content.strip()

        # Parse JSON
        import json

        products_data = json.loads(content)

        products = []
        for item in products_data:
            try:
                product = ProductIdea(**item)
                products.append(product)
            except Exception as e:
                logger.warning(f"Skipping invalid product data: {e}")
                continue

        return products

    except Exception as e:
        logger.warning(f"Claude product generation failed: {e}")
        raise RuntimeError(f"Claude API error during product generation: {e}") from e


def rank_products(products: list[ProductIdea]) -> list[ProductIdea]:
    """
    Rank products by value/complexity ratio.

    Higher value + lower complexity = better rank.

    Args:
        products: List of ProductIdea objects to rank

    Returns:
        Sorted list with best products first
    """
    # Complexity weights (lower is better)
    complexity_scores = {
        "easy": 1,
        "medium": 2,
        "hard": 3,
    }

    # Extract numeric value from estimated_value string
    def get_value_score(value_str: str) -> float:
        """Extract mid-point value from price range."""
        # Find all numbers in the string
        numbers = re.findall(r"\d+", value_str)
        if not numbers:
            return 50.0  # Default mid-range value

        # Convert to floats
        values = [float(n) for n in numbers]

        # Return average (mid-point for ranges)
        return sum(values) / len(values)

    def get_sort_key(product: ProductIdea) -> float:
        """Calculate sort key: higher is better (value / complexity)."""
        value = get_value_score(product.estimated_value)
        complexity = complexity_scores.get(product.build_complexity, 2)

        # Return negative because we want descending order
        return -(value / complexity)

    return sorted(products, key=get_sort_key)


def generate_product_alternatives(
    topic: str,
    newsletter_context: str = "",
    perplexity_model: str = DEFAULT_PERPLEXITY_MODEL,
    claude_model: str = DEFAULT_CLAUDE_MODEL,
    retry_on_perplexity_failure: bool = True,
) -> ProductAlternativesResult:
    """
    Generate ranked product alternatives for a newsletter topic.

    Uses two-stage approach:
    1. Perplexity researches pain points around the topic
    2. Claude generates product ideas that solve those pain points

    Args:
        topic: The newsletter topic to generate products for
        newsletter_context: Additional context about the newsletter content
        perplexity_model: Perplexity model for research
        claude_model: Claude model for generation
        retry_on_perplexity_failure: Whether to retry Perplexity once on failure

    Returns:
        ProductAlternativesResult with 3 ranked product ideas

    Raises:
        RuntimeError: If both Perplexity and Claude fail
    """
    # Stage 1: Research pain points with Perplexity
    pain_points = ""
    try:
        pain_points = research_pain_points(
            topic=topic,
            newsletter_context=newsletter_context,
            model=perplexity_model,
        )
    except RuntimeError as e:
        if retry_on_perplexity_failure:
            logger.info("Perplexity failed, retrying once...")
            try:
                pain_points = research_pain_points(
                    topic=topic,
                    newsletter_context=newsletter_context,
                    model=perplexity_model,
                )
            except RuntimeError:
                logger.warning(
                    "Perplexity retry failed. Using generic pain points for topic."
                )
                pain_points = f"Generic pain points for DTC brands around {topic}: pricing decisions, inventory management, customer acquisition costs, fulfillment logistics."
        else:
            raise e

    # Stage 2: Generate product ideas with Claude
    products = generate_product_ideas(
        topic=topic,
        pain_points=pain_points,
        newsletter_context=newsletter_context,
        model=claude_model,
    )

    # Rank products by value/complexity ratio
    ranked_products = rank_products(products)

    # Limit to top 3
    ranked_products = ranked_products[:3]

    return ProductAlternativesResult(
        products=ranked_products,
        topic=topic,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
