"""
Claude API client with prompt caching for DTC Money Minute newsletter.
DOE-VERSION: 2026.01.31

Provides Anthropic API wrapper with:
- Prompt caching for voice profile (reduces token usage)
- generate_with_voice() for general voice-consistent generation
- generate_section() for section-specific generation with validation

Uses native Anthropic SDK for best prompt caching support.
"""

import os
import logging
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Import voice profile and anti-pattern validator
from execution.voice_profile import VOICE_PROFILE_PROMPT, SECTION_GUIDELINES
from execution.anti_pattern_validator import validate_voice

# Default model - claude-sonnet-4-5 for best cost/quality balance
DEFAULT_MODEL = "claude-sonnet-4-5"


class ClaudeClient:
    """
    Anthropic Claude API client with prompt caching for voice profile.

    The voice profile is cached using ephemeral cache_control to reduce
    token usage across multiple section generations.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.

        Raises:
            ValueError: If no API key provided or found in environment.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable required. "
                "Set it in .env or pass api_key parameter."
            )

        # Import anthropic here to allow mocking in tests
        import anthropic

        self._client = anthropic.Anthropic(api_key=self.api_key)
        self._model = DEFAULT_MODEL

        # Track cache stats
        self._cache_stats = {
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "total_calls": 0,
        }

    def generate_with_voice(
        self,
        prompt: str,
        max_tokens: int = 1024,
    ) -> str:
        """
        Generate text using the voice profile with prompt caching.

        Args:
            prompt: User prompt to generate content for
            max_tokens: Maximum tokens in response (default: 1024)

        Returns:
            Generated text content
        """
        # Build system prompt with cache control
        system = [
            {
                "type": "text",
                "text": VOICE_PROFILE_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        # Make API call
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        # Update cache stats
        self._cache_stats["total_calls"] += 1
        if hasattr(response, "usage"):
            usage = response.usage
            if hasattr(usage, "cache_read_input_tokens"):
                self._cache_stats["cache_read_tokens"] += (
                    usage.cache_read_input_tokens or 0
                )
            if hasattr(usage, "cache_creation_input_tokens"):
                self._cache_stats["cache_write_tokens"] += (
                    usage.cache_creation_input_tokens or 0
                )

        # Log cache stats
        if self._cache_stats["cache_read_tokens"] > 0:
            logger.info(
                f"Cache hit: {self._cache_stats['cache_read_tokens']} tokens read from cache"
            )

        # Extract text content
        content = response.content[0].text
        return content

    def generate_section(
        self,
        section_name: str,
        content: dict,
        prior_sections: Optional[dict] = None,
        validate: bool = True,
    ) -> str:
        """
        Generate a specific newsletter section.

        Args:
            section_name: Name of section (section_1, section_2, etc.)
            content: Source content dict with keys like 'title', 'summary', 'source'
            prior_sections: Optional dict of prior section outputs for narrative coherence
            validate: Whether to validate output against anti-patterns (default: True)

        Returns:
            Generated section text

        Raises:
            KeyError: If section_name is not valid
            ValueError: If anti-patterns detected in output (when validate=True)
        """
        # Get section guidelines
        if section_name not in SECTION_GUIDELINES:
            valid_sections = ", ".join(SECTION_GUIDELINES.keys())
            raise KeyError(
                f"Unknown section: {section_name}. Valid sections: {valid_sections}"
            )

        section_info = SECTION_GUIDELINES[section_name]
        min_words, max_words = section_info["word_count"]

        # Build prompt with section guidelines
        prompt_parts = [
            f"Generate {section_info['name']} for the DTC Money Minute newsletter.",
            "",
            "## Section Guidelines",
            section_info["description"],
            "",
            f"## Word Count",
            f"Target: {min_words}-{max_words} words",
            "",
            "## Source Content",
            f"Title: {content.get('title', 'N/A')}",
            f"Summary: {content.get('summary', 'N/A')}",
            f"Source: {content.get('source', 'N/A')}",
        ]

        # Add additional content fields if present
        if content.get("url"):
            prompt_parts.append(f"URL: {content['url']}")
        if content.get("transcript"):
            prompt_parts.append(f"Transcript excerpt: {content['transcript'][:500]}...")

        # Add prior sections context for narrative coherence
        if prior_sections:
            prompt_parts.extend(
                [
                    "",
                    "## Prior Sections (for narrative coherence)",
                ]
            )
            for sect_name, sect_content in prior_sections.items():
                # Include brief summary of each prior section
                preview = (
                    sect_content[:200] + "..."
                    if len(sect_content) > 200
                    else sect_content
                )
                prompt_parts.append(f"### {sect_name}")
                prompt_parts.append(preview)

        prompt_parts.extend(
            [
                "",
                "## Output",
                "Write the section directly. No headers or labels. Just the content.",
            ]
        )

        prompt = "\n".join(prompt_parts)

        # Generate with voice
        result = self.generate_with_voice(prompt, max_tokens=max_words * 2)

        # Validate if requested
        if validate:
            is_valid, violations = validate_voice(result)
            if not is_valid:
                raise ValueError(
                    f"Anti-patterns detected in generated content: {violations}"
                )

        return result

    def get_cache_stats(self) -> dict:
        """
        Get cache usage statistics.

        Returns:
            Dict with cache_read_tokens, cache_write_tokens, total_calls
        """
        return self._cache_stats.copy()

    def reset_cache_stats(self) -> None:
        """Reset cache statistics to zero."""
        self._cache_stats = {
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "total_calls": 0,
        }


def get_client(api_key: Optional[str] = None) -> ClaudeClient:
    """
    Get a configured ClaudeClient instance.

    Args:
        api_key: Optional API key. Uses ANTHROPIC_API_KEY env var if not provided.

    Returns:
        Configured ClaudeClient instance

    Raises:
        ValueError: If no API key available
    """
    return ClaudeClient(api_key=api_key)
