"""
Claude API client with prompt caching for DTC Money Minute newsletter.
DOE-VERSION: 2026.02.02

Provides Claude API wrapper via OpenRouter with:
- Prompt caching for voice profile (reduces token usage)
- generate_with_voice() for general voice-consistent generation
- generate_section() for section-specific generation with validation

Uses OpenRouter API (OpenAI-compatible) for access to Anthropic models.
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

# Default model - claude-sonnet-4-5 via OpenRouter
DEFAULT_MODEL = "anthropic/claude-sonnet-4"

# OpenRouter API endpoint
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class ClaudeClient:
    """
    Claude API client via OpenRouter with prompt caching for voice profile.

    Uses OpenRouter's OpenAI-compatible API to access Anthropic models.
    The voice profile is included in system prompt for consistent generation.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client via OpenRouter.

        Args:
            api_key: OpenRouter API key. If not provided, uses OPENROUTER_API_KEY env var.

        Raises:
            ValueError: If no API key provided or found in environment.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable required. "
                "Set it in .env or pass api_key parameter."
            )

        # Import openai here to allow mocking in tests
        from openai import OpenAI

        self._client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=self.api_key,
        )
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
        Generate text using the voice profile.

        Args:
            prompt: User prompt to generate content for
            max_tokens: Maximum tokens in response (default: 1024)

        Returns:
            Generated text content
        """
        # Build messages with voice profile as system prompt
        messages = [
            {"role": "system", "content": VOICE_PROFILE_PROMPT},
            {"role": "user", "content": prompt},
        ]

        # Make API call via OpenRouter
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=messages,
            extra_headers={
                "HTTP-Referer": "https://dtc-newsletter.local",
                "X-Title": "DTC Newsletter Generator",
            },
        )

        # Update stats
        self._cache_stats["total_calls"] += 1
        if hasattr(response, "usage") and response.usage:
            usage = response.usage
            # OpenRouter may provide cache stats in some cases
            if hasattr(usage, "prompt_tokens_details"):
                details = usage.prompt_tokens_details
                if details and hasattr(details, "cached_tokens"):
                    self._cache_stats["cache_read_tokens"] += details.cached_tokens or 0

        # Extract text content
        content = response.choices[0].message.content
        return content or ""

    def generate(
        self,
        prompt: str,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate text using plain prompt (no voice profile).

        Use this for product generation where the voice profile isn't needed
        (e.g., generating HTML tools, automation scripts, GPT configs).

        Args:
            prompt: User prompt to generate content for
            max_tokens: Maximum tokens in response (default: 4096)
            system_prompt: Optional system prompt (default: general assistant)

        Returns:
            Generated text content
        """
        # Build system if provided, otherwise use simple default
        if system_prompt:
            system = system_prompt
        else:
            system = "You are a helpful assistant that generates high-quality content. Follow instructions precisely and return exactly what is requested."

        # Build messages
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

        # Make API call via OpenRouter
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=messages,
            extra_headers={
                "HTTP-Referer": "https://dtc-newsletter.local",
                "X-Title": "DTC Newsletter Generator",
            },
        )

        # Update stats
        self._cache_stats["total_calls"] += 1

        # Extract text content
        content = response.choices[0].message.content
        return content or ""

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
        api_key: Optional API key. Uses OPENROUTER_API_KEY env var if not provided.

    Returns:
        Configured ClaudeClient instance

    Raises:
        ValueError: If no API key available
    """
    return ClaudeClient(api_key=api_key)
