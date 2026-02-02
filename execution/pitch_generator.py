"""
Pitch generator for affiliate recommendations.
DOE-VERSION: 2026.02.02

Generates contextual pitch angles for affiliate products using Claude API via OpenRouter.
Pitches match the Hormozi/Suby voice profile and are ready for Section 4
("Tool of the Week").
"""

import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Import affiliate model and Claude client
from execution.affiliate_discovery import AffiliateProgram
from execution.claude_client import ClaudeClient

# Voice guidance constant per RESEARCH.md and PROJECT.md
VOICE_GUIDANCE = """
Voice requirements (Hormozi/Suby hybrid):
- Short, punchy sentences (under 15 words typically)
- Direct, confident, slightly irreverent tone
- Specific numbers and math: "$X invested -> $Y returned"
- Zero fluff - delete "basically," "essentially," "just"
- Concrete, specific examples (never hypothetical)
- 80% value / 20% ask ratio
"""

# Fluff words to reject in pitches
FLUFF_WORDS = [
    "basically",
    "essentially",
    "just",
    "simply",
    "actually",
    "really",
    "very",
    "quite",
    "somewhat",
    "rather",
]

# Passive voice indicators
PASSIVE_PATTERNS = [
    r"\bis\s+(?:being\s+)?(?:used|done|made|built|created|handled)",
    r"\bwas\s+(?:being\s+)?(?:used|done|made|built|created|handled)",
    r"\bare\s+(?:being\s+)?(?:used|done|made|built|created|handled)",
    r"\bwere\s+(?:being\s+)?(?:used|done|made|built|created|handled)",
    r"\bhas\s+been\s+(?:used|done|made|built|created|handled)",
    r"\bhave\s+been\s+(?:used|done|made|built|created|handled)",
]


class PitchGenerator:
    """
    Generates voice-matched pitches for affiliate products.

    Uses Claude API via OpenRouter to create 2-3 sentence recommendations
    that feel like insider tips rather than advertisements.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize pitch generator.

        Args:
            api_key: OpenRouter API key. If not provided, uses OPENROUTER_API_KEY env var.

        Raises:
            ValueError: If no API key provided or found in environment.
        """
        self._client = ClaudeClient(api_key=api_key)

    def generate_pitch(
        self,
        affiliate: AffiliateProgram,
        newsletter_topic: str,
        problem_context: str = "",
    ) -> str:
        """
        Generate a contextual pitch for an affiliate product.

        Creates a 2-3 sentence recommendation that:
        - References the specific newsletter topic/problem
        - Feels like a recommendation, not an ad
        - Ready to copy/paste into Section 4 "Tool of the Week"
        - Matches the Hormozi/Suby voice profile

        Args:
            affiliate: AffiliateProgram to pitch
            newsletter_topic: The topic of this week's newsletter
            problem_context: Additional context about the problem being solved

        Returns:
            Voice-matched pitch text (2-3 sentences)
        """
        context_clause = ""
        if problem_context:
            context_clause = f"\n\nProblem context: {problem_context}"

        prompt = f"""Write a 2-3 sentence pitch for {affiliate.name} to include in a newsletter about "{newsletter_topic}".

Product: {affiliate.product_description}
Commission: {affiliate.commission_rate} ({affiliate.commission_type})
Why it fits: {affiliate.topic_fit}{context_clause}

{VOICE_GUIDANCE}

Requirements:
- Reference the specific topic/problem from the newsletter
- Feel like a recommendation from a friend, not an advertisement
- Ready to copy/paste into "Tool of the Week" section
- 2-3 sentences MAXIMUM
- No intro phrases like "This tool" or "Check out"
- Start with a benefit or hook

Write only the pitch, nothing else."""

        content = self._client.generate(prompt=prompt, max_tokens=300)
        return content.strip()

    def generate_pitches_batch(
        self,
        affiliates: list[AffiliateProgram],
        newsletter_topic: str,
        problem_context: str = "",
    ) -> dict[str, str]:
        """
        Generate pitches for multiple affiliates.

        Handles individual failures gracefully - logs warning and skips
        that affiliate rather than failing the entire batch.

        Args:
            affiliates: List of AffiliateProgram objects to generate pitches for
            newsletter_topic: The topic of this week's newsletter
            problem_context: Additional context about the problem being solved

        Returns:
            Dict mapping affiliate name to pitch text
        """
        pitches = {}

        for affiliate in affiliates:
            try:
                pitch = self.generate_pitch(
                    affiliate=affiliate,
                    newsletter_topic=newsletter_topic,
                    problem_context=problem_context,
                )
                pitches[affiliate.name] = pitch
            except Exception as e:
                logger.warning(f"Failed to generate pitch for {affiliate.name}: {e}")
                continue

        return pitches


def validate_pitch(pitch: str) -> bool:
    """
    Validate pitch against anti-patterns.

    Checks for:
    - Fluff words: "basically", "essentially", "just", "simply"
    - Passive voice patterns
    - Excessive length (> 4 sentences)

    Args:
        pitch: The pitch text to validate

    Returns:
        True if valid, False if needs regeneration
    """
    # Check for fluff words (case-insensitive)
    pitch_lower = pitch.lower()
    for word in FLUFF_WORDS:
        # Check for word boundaries to avoid false positives
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, pitch_lower):
            logger.debug(f"Fluff word detected: '{word}'")
            return False

    # Check for passive voice patterns
    for pattern in PASSIVE_PATTERNS:
        if re.search(pattern, pitch_lower):
            logger.debug(f"Passive voice detected: pattern '{pattern}'")
            return False

    # Check sentence count (> 4 is too long)
    # Split on sentence-ending punctuation
    sentences = re.split(r"[.!?]+", pitch)
    # Filter out empty strings from split
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) > 4:
        logger.debug(f"Too many sentences: {len(sentences)} > 4")
        return False

    return True


def generate_pitch(
    affiliate: AffiliateProgram,
    newsletter_topic: str,
    problem_context: str = "",
) -> str:
    """
    Convenience function to generate a single pitch.

    Creates a PitchGenerator instance and generates a pitch.
    Use PitchGenerator class directly for batch operations.

    Args:
        affiliate: AffiliateProgram to pitch
        newsletter_topic: The topic of this week's newsletter
        problem_context: Additional context about the problem being solved

    Returns:
        Voice-matched pitch text (2-3 sentences)
    """
    generator = PitchGenerator()
    return generator.generate_pitch(
        affiliate=affiliate,
        newsletter_topic=newsletter_topic,
        problem_context=problem_context,
    )


def generate_pitches_batch(
    affiliates: list[AffiliateProgram],
    newsletter_topic: str,
    problem_context: str = "",
) -> dict[str, str]:
    """
    Convenience function to generate pitches for multiple affiliates.

    Creates a PitchGenerator instance and generates pitches.
    Use PitchGenerator class directly for more control.

    Args:
        affiliates: List of AffiliateProgram objects
        newsletter_topic: The topic of this week's newsletter
        problem_context: Additional context about the problem being solved

    Returns:
        Dict mapping affiliate name to pitch text
    """
    generator = PitchGenerator()
    return generator.generate_pitches_batch(
        affiliates=affiliates,
        newsletter_topic=newsletter_topic,
        problem_context=problem_context,
    )
