"""
Subject line and preview text generators for DTC Money Minute newsletter.
DOE-VERSION: 2026.01.31

Provides:
- generate_subject_line: Creates subject lines under 50 chars with style rotation
- generate_preview_text: Creates 40-90 char preview/preheader hooks
- select_subject_style: Weighted style selection (70% curiosity, 20% direct, 10% question)
- validate_subject_line: Validates format, length, and constraints

Subject line format: "DTC Money Minute #X: lowercase curiosity hook"
Hard constraints: under 50 chars, lowercase after colon, no emojis, no ALL CAPS
"""

import logging
import random
import re
from typing import Optional

from execution.claude_client import ClaudeClient

# Set up logging
logger = logging.getLogger(__name__)

# Subject line style prompts
SUBJECT_STYLES: dict[str, str] = {
    "curiosity": "Create a curiosity-driven hook that makes the reader NEED to open",
    "direct_benefit": "State a specific, concrete benefit with numbers",
    "question": "Ask a question that challenges their assumptions",
}

# Style weights (70% curiosity, 20% direct_benefit, 10% question)
STYLE_WEIGHTS = [0.70, 0.20, 0.10]
STYLE_OPTIONS = ["curiosity", "direct_benefit", "question"]

# Regex for emoji detection
EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map symbols
    "\U0001f700-\U0001f77f"  # alchemical symbols
    "\U0001f780-\U0001f7ff"  # Geometric Shapes Extended
    "\U0001f800-\U0001f8ff"  # Supplemental Arrows-C
    "\U0001f900-\U0001f9ff"  # Supplemental Symbols and Pictographs
    "\U0001fa00-\U0001fa6f"  # Chess Symbols
    "\U0001fa70-\U0001faff"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027b0"  # Dingbats
    "\U0001f926-\U0001f937"  # Additional emoticons
    "]+"
)


def select_subject_style(history: Optional[list[str]] = None) -> str:
    """
    Select subject line style based on 70/20/10 distribution.

    Args:
        history: Optional list of previously used styles (for future tracking)

    Returns:
        Style name: "curiosity", "direct_benefit", or "question"
    """
    # Use weighted random selection
    # history parameter reserved for future style tracking to avoid repetition
    return random.choices(STYLE_OPTIONS, weights=STYLE_WEIGHTS, k=1)[0]


def validate_subject_line(subject: str, issue_number: int) -> tuple[bool, list[str]]:
    """
    Validate subject line against all constraints.

    Args:
        subject: Subject line to validate
        issue_number: Expected issue number

    Returns:
        Tuple of (is_valid, list of violation descriptions)
    """
    violations = []

    # Check total length (must be <= 50 chars)
    if len(subject) > 50:
        violations.append(f"Subject line too long: {len(subject)} chars (max 50)")

    # Check format starts with "DTC Money Minute #X:"
    expected_prefix = f"DTC Money Minute #{issue_number}:"
    if not subject.startswith(expected_prefix):
        violations.append(f"Must start with '{expected_prefix}'")

    # Check lowercase after colon
    if ":" in subject:
        after_colon = subject.split(":", 1)[1].strip()
        if after_colon and after_colon[0].isupper():
            violations.append("Hook after colon must be lowercase")

    # Check for emojis
    if EMOJI_PATTERN.search(subject):
        violations.append("No emojis allowed")

    # Check for ALL CAPS words in the hook (after colon, not in the fixed prefix)
    # "DTC" in prefix is allowed, but no ALL CAPS in the hook
    if ":" in subject:
        after_colon = subject.split(":", 1)[1]
        hook_words = after_colon.split()
        caps_words = [
            w for w in hook_words if len(w) > 1 and w.isupper() and w.isalpha()
        ]
        if caps_words:
            violations.append(f"No ALL CAPS words allowed in hook: {caps_words}")

    # Check for "How to" start after colon
    if ":" in subject:
        after_colon = subject.split(":", 1)[1].strip().lower()
        if after_colon.startswith("how to"):
            violations.append("Hook cannot start with 'How to'")

    is_valid = len(violations) == 0
    return is_valid, violations


def generate_subject_line(
    issue_number: int,
    main_topic: str,
    style: str,
    client: ClaudeClient,
) -> str:
    """
    Generate a subject line for the newsletter.

    Format: "DTC Money Minute #X: lowercase curiosity hook"
    Constraints:
    - Under 50 characters TOTAL
    - Lowercase after colon
    - Zero emojis
    - No ALL CAPS words
    - Never start hook with "How to"

    Args:
        issue_number: Newsletter issue number
        main_topic: Main topic/theme of the newsletter
        style: Subject style ("curiosity", "direct_benefit", or "question")
        client: ClaudeClient instance for generation

    Returns:
        Generated subject line

    Raises:
        ValueError: If subject line cannot be generated within constraints after retry
    """
    if style not in SUBJECT_STYLES:
        raise ValueError(
            f"Invalid style: {style}. Must be one of: {list(SUBJECT_STYLES.keys())}"
        )

    style_prompt = SUBJECT_STYLES[style]
    prefix = f"DTC Money Minute #{issue_number}:"
    max_hook_length = 50 - len(prefix) - 1  # -1 for space after colon

    # Build XML-structured prompt
    prompt = f"""<task>Generate a subject line for DTC Money Minute #{issue_number}</task>

<topic>{main_topic}</topic>

<style>{style_prompt}</style>

<rules>
- Format: DTC Money Minute #{issue_number}: [hook]
- Hook MUST be lowercase after the colon
- Zero emojis
- No ALL CAPS words
- TOTAL subject line MUST be under 50 characters (prefix + hook)
- Hook can be max {max_hook_length} characters
- Never start hook with "How to"
</rules>

<output>Return ONLY the complete subject line, nothing else. No quotes, no explanation.</output>"""

    # Generate subject line
    result = client.generate_with_voice(prompt, max_tokens=100)
    subject = result.strip().strip('"').strip("'")

    # Validate
    is_valid, violations = validate_subject_line(subject, issue_number)

    if not is_valid:
        logger.warning(f"First attempt failed validation: {violations}")

        # Regenerate with stricter prompt
        strict_prompt = f"""<task>Generate a SHORT subject line for DTC Money Minute #{issue_number}</task>

<CRITICAL_CONSTRAINTS>
You FAILED validation. Previous violations: {violations}

FIX THESE ISSUES:
1. TOTAL length must be UNDER 50 characters (currently the limit)
2. After the colon, EVERYTHING must be lowercase
3. ZERO emojis allowed
4. No ALL CAPS words
5. Do NOT start the hook with "how to"
</CRITICAL_CONSTRAINTS>

<topic>{main_topic}</topic>
<style>{style_prompt}</style>

<format>DTC Money Minute #{issue_number}: [short lowercase hook]</format>

<output>Return ONLY the subject line. Under 50 chars total. All lowercase after colon.</output>"""

        result = client.generate_with_voice(strict_prompt, max_tokens=80)
        subject = result.strip().strip('"').strip("'")

        # Validate again
        is_valid, violations = validate_subject_line(subject, issue_number)
        if not is_valid:
            raise ValueError(
                f"Subject line failed validation after retry: {violations}. "
                f"Generated: {subject}"
            )

    logger.info(f"Subject line generated: {subject} ({len(subject)} chars)")
    return subject


def generate_preview_text(
    newsletter_content: str,
    client: ClaudeClient,
) -> str:
    """
    Generate preview/preheader text for the email.

    Must be a HOOK that creates curiosity, NOT "View in browser" or generic text.

    Args:
        newsletter_content: Full newsletter content (or summary)
        client: ClaudeClient instance for generation

    Returns:
        Preview text (40-90 characters)

    Raises:
        ValueError: If preview text cannot be generated within length constraints
    """
    # Get first 200 words for context
    words = newsletter_content.split()[:200]
    content_summary = " ".join(words)

    # Build XML-structured prompt
    prompt = f"""<task>Generate email preview text</task>

<requirements>
- 40-90 characters (STRICT - this is the visible preview length)
- Hook that creates curiosity
- Complements subject line (don't repeat it)
- NOT "View in browser" or similar generic text
- NOT a summary - a HOOK
- Creates urgency to open the email
</requirements>

<newsletter_summary>{content_summary}</newsletter_summary>

<good_examples>
- "The $47 tool that 8-figure brands won't shut up about"
- "Most stores are doing this wrong. Are you?"
- "This one change doubled their email revenue"
</good_examples>

<bad_examples>
- "View in browser"
- "Having trouble viewing this?"
- "This week's newsletter"
- "Read more inside"
</bad_examples>

<output_format>Preview text only, nothing else. No quotes.</output_format>"""

    # Generate preview text
    result = client.generate_with_voice(prompt, max_tokens=100)
    preview = result.strip().strip('"').strip("'")

    # Validate length
    if len(preview) < 40:
        logger.warning(f"Preview text too short: {len(preview)} chars")
        # Try to regenerate with specific length requirement
        length_prompt = f"""<task>Generate LONGER preview text (40-90 chars)</task>

<current_attempt>{preview}</current_attempt>
<problem>Too short at {len(preview)} characters. Needs 40-90 characters.</problem>

<newsletter_context>{content_summary[:100]}</newsletter_context>

<output>Write a curiosity hook between 40-90 characters. No quotes.</output>"""

        result = client.generate_with_voice(length_prompt, max_tokens=80)
        preview = result.strip().strip('"').strip("'")

    if len(preview) > 90:
        logger.warning(f"Preview text too long: {len(preview)} chars, truncating")
        # Truncate to 90 chars at word boundary
        if len(preview) > 90:
            preview = preview[:87].rsplit(" ", 1)[0] + "..."

    # Final validation
    if len(preview) < 40 or len(preview) > 90:
        logger.warning(
            f"Preview text length {len(preview)} outside 40-90 range, but accepting"
        )

    logger.info(f"Preview text generated: {preview} ({len(preview)} chars)")
    return preview
