"""
Sales copy generator for the Product Factory.
DOE-VERSION: 2026.01.31

Generates compelling sales copy using the Hormozi/Suby voice profile:
- Headline (curiosity + benefit, under 10 words)
- Subheadline (expands on promise, under 20 words)
- Problem section (2-3 sentences agitating the pain)
- Solution section (how the product solves it)
- Benefit bullets (5 specific outcomes with numbers)
- Value anchor (what this is worth / alternatives cost)
- Price justification (why this price is a steal)
- CTA (action-oriented call to action)
"""

import json
import logging
from typing import Optional

from execution.voice_profile import VOICE_PROFILE_PROMPT
from execution.generators.base_generator import ProductSpec

logger = logging.getLogger(__name__)

# Prompt template for sales copy generation
SALES_COPY_PROMPT = """Generate sales copy for this digital product:

PRODUCT: {product_name}
PROBLEM IT SOLVES: {problem}
TARGET AUDIENCE: {audience}
KEY BENEFITS: {benefits}
PRICE: {price_display}
PERCEIVED VALUE: {perceived_value}

Generate these sections as JSON:

{{
    "headline": "<curiosity + benefit, under 10 words>",
    "subheadline": "<expands on promise, under 20 words>",
    "problem_section": "<2-3 sentences agitating the pain>",
    "solution_section": "<how this product solves it, 2-3 sentences>",
    "benefit_bullets": [
        "<specific outcome 1 with number if possible>",
        "<specific outcome 2 with number if possible>",
        "<specific outcome 3 with number if possible>",
        "<specific outcome 4 with number if possible>",
        "<specific outcome 5 with number if possible>"
    ],
    "value_anchor": "<what this is worth / what alternatives cost>",
    "price_justification": "<why this price is a steal, 1-2 sentences>",
    "cta": "<action-oriented call to action, 5-8 words>"
}}

Use the DTC Money Minute voice: short sentences, specific numbers, zero fluff.
Return ONLY valid JSON, no markdown code blocks."""


class SalesCopyGenerator:
    """
    Generates compelling sales copy using the Hormozi/Suby voice profile.

    Creates 8-section sales copy:
    1. Headline - curiosity + benefit, under 10 words
    2. Subheadline - expands on promise, under 20 words
    3. Problem section - 2-3 sentences agitating the pain
    4. Solution section - how the product solves it
    5. Benefit bullets - 5 specific outcomes with numbers
    6. Value anchor - what this is worth / alternatives cost
    7. Price justification - why this price is a steal
    8. CTA - action-oriented call to action
    """

    REQUIRED_SECTIONS = [
        "headline",
        "subheadline",
        "problem_section",
        "solution_section",
        "benefit_bullets",
        "value_anchor",
        "price_justification",
        "cta",
    ]

    def __init__(self, claude_client=None):
        """
        Initialize the sales copy generator.

        Args:
            claude_client: Optional Claude API client for AI-assisted generation.
                          If not provided, uses fallback generation.
        """
        self.claude_client = claude_client

    def generate(
        self,
        spec: ProductSpec,
        price_display: str,
        perceived_value: str,
    ) -> dict:
        """
        Generate sales copy for a product.

        Args:
            spec: ProductSpec defining the product
            price_display: Formatted price string (e.g., "$47")
            perceived_value: Perceived value statement (e.g., "$500+ worth of tools")

        Returns:
            Dict with all 8 sales copy sections

        Raises:
            RuntimeError: If generation fails
        """
        # Format the prompt
        prompt = SALES_COPY_PROMPT.format(
            product_name=spec.solution_name,
            problem=spec.problem,
            audience=spec.target_audience,
            benefits=", ".join(spec.key_benefits),
            price_display=price_display,
            perceived_value=perceived_value,
        )

        # Generate using Claude if available
        if self.claude_client:
            try:
                # Use voice profile for consistent tone
                response = self.claude_client.generate_with_voice(
                    prompt, max_tokens=1024
                )
                copy_dict = self._parse_response(response)
            except Exception as e:
                logger.error(f"Claude generation failed: {e}")
                copy_dict = self._generate_fallback(
                    spec, price_display, perceived_value
                )
        else:
            copy_dict = self._generate_fallback(spec, price_display, perceived_value)

        return copy_dict

    def format_markdown(self, copy_dict: dict) -> str:
        """
        Format sales copy as clean markdown.

        Args:
            copy_dict: Dict with all 8 sales copy sections

        Returns:
            Formatted markdown string
        """
        lines = []

        # Headline
        lines.append(f"# {copy_dict.get('headline', 'Your Product')}")
        lines.append("")

        # Subheadline
        lines.append(f"## {copy_dict.get('subheadline', 'Get the solution you need')}")
        lines.append("")

        # Problem section
        lines.append("### The Problem")
        lines.append("")
        lines.append(copy_dict.get("problem_section", ""))
        lines.append("")

        # Solution section
        lines.append("### The Solution")
        lines.append("")
        lines.append(copy_dict.get("solution_section", ""))
        lines.append("")

        # Benefit bullets
        lines.append("### What You Get")
        lines.append("")
        benefits = copy_dict.get("benefit_bullets", [])
        for benefit in benefits:
            lines.append(f"- {benefit}")
        lines.append("")

        # Value anchor
        lines.append("### The Value")
        lines.append("")
        lines.append(copy_dict.get("value_anchor", ""))
        lines.append("")

        # Price justification
        lines.append("### Why This Price")
        lines.append("")
        lines.append(copy_dict.get("price_justification", ""))
        lines.append("")

        # CTA
        lines.append("---")
        lines.append("")
        lines.append(f"**{copy_dict.get('cta', 'Get Started Now')}**")
        lines.append("")

        return "\n".join(lines)

    def validate(self, copy_dict: dict) -> tuple[bool, list[str]]:
        """
        Validate sales copy against requirements.

        Checks:
        - All 8 sections present
        - Headline under 10 words
        - At least 5 benefit bullets

        Args:
            copy_dict: Dict with sales copy sections

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        # Check all required sections present
        for section in self.REQUIRED_SECTIONS:
            if section not in copy_dict or not copy_dict[section]:
                issues.append(f"Missing section: {section}")

        # Check headline word count (under 10 words)
        headline = copy_dict.get("headline", "")
        headline_words = len(headline.split())
        if headline_words > 10:
            issues.append(f"Headline too long: {headline_words} words (max 10)")

        # Check benefit bullets count (at least 5)
        benefits = copy_dict.get("benefit_bullets", [])
        if len(benefits) < 5:
            issues.append(f"Not enough benefit bullets: {len(benefits)} (need 5)")

        is_valid = len(issues) == 0
        return is_valid, issues

    def _parse_response(self, response: str) -> dict:
        """
        Parse Claude's JSON response into a copy dict.

        Args:
            response: Raw response from Claude

        Returns:
            Parsed sales copy dict
        """
        try:
            # Handle potential markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith("```") and not in_block:
                        in_block = True
                        continue
                    elif line.startswith("```") and in_block:
                        break
                    elif in_block:
                        json_lines.append(line)
                clean_response = "\n".join(json_lines)

            return json.loads(clean_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {}

    def _generate_fallback(
        self,
        spec: ProductSpec,
        price_display: str,
        perceived_value: str,
    ) -> dict:
        """
        Generate fallback sales copy when Claude is not available.

        Args:
            spec: ProductSpec defining the product
            price_display: Formatted price string
            perceived_value: Perceived value statement

        Returns:
            Dict with all 8 sales copy sections
        """
        # Generate benefit bullets from key_benefits
        benefit_bullets = []
        for benefit in spec.key_benefits[:5]:
            benefit_bullets.append(benefit)

        # Pad to 5 if needed
        while len(benefit_bullets) < 5:
            benefit_bullets.append(f"Solve {spec.problem} faster")

        return {
            "headline": f"Stop Struggling With {spec.problem[:30]}",
            "subheadline": f"The exact system {spec.target_audience} use to get results",
            "problem_section": (
                f"You're spending too much time on {spec.problem}. "
                f"Every day without a solution costs you money. "
                f"It doesn't have to be this way."
            ),
            "solution_section": (
                f"{spec.solution_name} gives you everything you need. "
                f"Built specifically for {spec.target_audience}. "
                f"Works from day one."
            ),
            "benefit_bullets": benefit_bullets,
            "value_anchor": perceived_value,
            "price_justification": (
                f"At {price_display}, this pays for itself in the first week. "
                f"Most tools like this cost 10x more."
            ),
            "cta": f"Get {spec.solution_name} Now",
        }


def generate_sales_copy(
    spec: ProductSpec,
    price_display: str,
    perceived_value: str,
    claude_client=None,
) -> str:
    """
    Convenience function to generate formatted sales copy.

    Args:
        spec: ProductSpec defining the product
        price_display: Formatted price string (e.g., "$47")
        perceived_value: Perceived value statement
        claude_client: Optional Claude API client

    Returns:
        Formatted markdown sales copy string
    """
    generator = SalesCopyGenerator(claude_client)
    copy_dict = generator.generate(spec, price_display, perceived_value)
    return generator.format_markdown(copy_dict)
