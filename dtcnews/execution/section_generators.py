"""
Section generators for DTC Money Minute newsletter.
DOE-VERSION: 2026.02.04

Contains generators for all 5 newsletter sections:
- generate_section_1: Instant Reward (30-60 words)
- generate_section_2: What's Working Now (300-500 words)
- generate_section_2_from_deep_dive: Section 2 from pre-generated deep dive
- generate_section_3: The Breakdown (200-300 words)
- generate_section_4: Tool of the Week (100-200 words)
- generate_section_5: PS Statement (20-40 words)

Each generator uses ClaudeClient with XML-structured prompts and
validates word counts for section compliance.
"""

import logging
from typing import Optional

from execution.claude_client import ClaudeClient
from execution.anti_pattern_validator import validate_voice

# Set up logging
logger = logging.getLogger(__name__)


def _count_words(text: str) -> int:
    """Count words in text."""
    if not text:
        return 0
    return len(text.split())


def _validate_word_count(
    text: str, min_words: int, max_words: int, strict: bool = False
) -> tuple[bool, int]:
    """
    Validate text is within word count range.

    Args:
        text: Text to validate
        min_words: Minimum word count
        max_words: Maximum word count
        strict: If True, returns False when out of range. If False, just logs warning.

    Returns:
        Tuple of (is_valid, actual_count)
    """
    count = _count_words(text)
    is_valid = min_words <= count <= max_words

    if not is_valid and not strict:
        if count < min_words:
            logger.warning(
                f"Word count ({count}) below target ({min_words}-{max_words})"
            )
        else:
            logger.warning(
                f"Word count ({count}) above target ({min_words}-{max_words})"
            )
        # Return True to indicate we accept it (with warning)
        return True, count

    return is_valid, count


def _summarize_prior_sections(prior_sections: dict | None, max_chars: int = 300) -> str:
    """
    Create a brief summary of prior sections for context.

    Args:
        prior_sections: Dict mapping section names to content
        max_chars: Max characters to include per section

    Returns:
        Summarized context string
    """
    if not prior_sections:
        return "No prior sections"

    summaries = []
    for name, content in prior_sections.items():
        if content:
            preview = (
                content[:max_chars] + "..." if len(content) > max_chars else content
            )
            summaries.append(f"{name}: {preview}")

    return "\n".join(summaries) if summaries else "No prior sections"


def generate_section_1(
    content: dict,
    client: ClaudeClient,
    prior_sections: Optional[dict] = None,
) -> str:
    """
    Generate Section 1: Instant Reward (30-60 words).

    Delivers immediate value - a quote, viral tweet, or striking stat.

    Args:
        content: Source content dict with keys like 'title', 'summary', 'quote', 'stat'
        client: ClaudeClient instance for generation
        prior_sections: Not used for Section 1 (it's first), included for API consistency

    Returns:
        Generated section text (30-60 words)

    Raises:
        ValueError: If generated content fails word count validation
    """
    # Build XML-structured prompt
    prompt = f"""<task>Generate Section 1: Instant Reward</task>

<requirements>
- 30-60 words ONLY
- Immediate dopamine hit in first sentence
- Can be: provocative quote, surprising stat, viral observation
- No setup needed. Just the punch.
- Reader should feel rewarded for opening the email
</requirements>

<source_content>
Title: {content.get("title", "N/A")}
Summary: {content.get("summary", "N/A")}
Quote: {content.get("quote", "N/A")}
Stat: {content.get("stat", "N/A")}
Source: {content.get("source", "N/A")}
</source_content>

<output_format>
Write the section directly. No headers, no "Section 1" label.
Just deliver the instant reward.
</output_format>"""

    # Generate with voice profile
    result = client.generate_with_voice(prompt, max_tokens=150)

    # Validate word count (30-60) - warn but don't fail
    is_valid, word_count = _validate_word_count(result, 30, 60, strict=False)
    logger.debug(f"Section 1 generated: {word_count} words (target: 30-60)")

    return result


def generate_section_2(
    content: dict,
    client: ClaudeClient,
    prior_sections: Optional[dict] = None,
) -> str:
    """
    Generate Section 2: What's Working Now (300-500 words).

    THE MEAT of the newsletter. Single actionable tactic.

    Args:
        content: Source content dict with tactical information
        client: ClaudeClient instance for generation
        prior_sections: Dict of prior sections for narrative context

    Returns:
        Generated section text (300-500 words)

    Raises:
        ValueError: If generated content fails word count validation
    """
    # Get prior context
    prior_context = ""
    if prior_sections:
        if prior_sections.get("section_1"):
            prior_context = f"Section 1 hook: {prior_sections['section_1'][:100]}..."

    # Build XML-structured prompt
    prompt = f"""<task>Generate Section 2: What's Working Now</task>

<requirements>
- 300-500 words
- THE MEAT of the newsletter
- Single actionable tactic, NOT a bullet-point list
- Easy and simple to implement with direct, immediate impact
- Structure: Problem -> Solution -> Why It Works -> How To Do It -> Expected Result
</requirements>

<source_content>
Title: {content.get("title", "N/A")}
Summary: {content.get("summary", "N/A")}
Tactic: {content.get("tactic", content.get("summary", "N/A"))}
Source: {content.get("source", "N/A")}
Transcript: {content.get("transcript", "N/A")[:500] if content.get("transcript") else "N/A"}
</source_content>

<prior_context>
{prior_context if prior_context else "This is Section 2, following the opening hook."}
</prior_context>

<output_format>
Write the section directly. No headers.
Natural paragraph flow with the Problem -> Solution -> How-to structure.
</output_format>"""

    # Generate with voice profile
    result = client.generate_with_voice(prompt, max_tokens=1000)

    # Validate word count (300-500) - warn but don't fail
    is_valid, word_count = _validate_word_count(result, 300, 500, strict=False)
    logger.debug(f"Section 2 generated: {word_count} words (target: 300-500)")

    return result


def generate_section_2_from_deep_dive(
    deep_dive: dict,
    client: ClaudeClient,
    prior_sections: Optional[dict] = None,
) -> str:
    """
    Generate Section 2 from a pre-generated deep dive.

    This uses the rich deep dive content (WHO, WHAT, WHY, HOW) to create
    Section 2, ensuring the genuine value is preserved while fitting the
    newsletter format.

    Args:
        deep_dive: Deep dive dict with keys: headline, the_story, what_they_did,
                   why_it_worked, beginner_version, action_steps, prompt, key_insight
        client: ClaudeClient instance for generation
        prior_sections: Dict of prior sections for narrative context

    Returns:
        Generated section text (300-500 words)
    """
    # Get prior context
    prior_context = ""
    if prior_sections and prior_sections.get("section_1"):
        prior_context = f"Section 1 hook: {prior_sections['section_1'][:100]}..."

    # Extract deep dive components
    story = deep_dive.get("the_story", {})
    what_they_did = deep_dive.get("what_they_did", [])
    why_it_worked = deep_dive.get("why_it_worked", {})
    beginner_version = deep_dive.get("beginner_version", {})
    action_steps = deep_dive.get("action_steps", [])
    prompt_info = deep_dive.get("prompt", {})
    key_insight = deep_dive.get("key_insight", "")

    # Format the deep dive components for the prompt
    story_text = f"""
WHO: {story.get("who", "Unknown")}
SITUATION: {story.get("situation", "")}
RESULT: {story.get("result", "")}
SOURCE: {story.get("source", "")}
"""

    tactics_text = (
        "\n".join(
            [
                f"- {t.get('tactic', '')}: {t.get('details', '')} ({t.get('why_important', '')})"
                for t in what_they_did
            ]
        )
        if what_they_did
        else "N/A"
    )

    why_text = f"""
CORE PRINCIPLE: {why_it_worked.get("core_principle", "")}
MECHANISM: {why_it_worked.get("mechanism", "")}
UNIVERSAL TRUTH: {why_it_worked.get("universal_truth", "")}
"""

    beginner_text = f"""
SAME PRINCIPLE AT SMALL SCALE: {beginner_version.get("same_principle", "")}
FOCUS ON: {beginner_version.get("what_to_focus_on", "")}
SKIP FOR NOW: {beginner_version.get("what_to_ignore", "")}
REALISTIC EXPECTATION: {beginner_version.get("realistic_expectation", "")}
"""

    steps_text = (
        "\n".join(
            [
                f"{s.get('step', '')}. {s.get('action', '')} ({s.get('time', '')}) - Tool: {s.get('tool', '')}"
                for s in action_steps
            ]
        )
        if action_steps
        else "N/A"
    )

    prompt_text = f"""
PROMPT: {prompt_info.get("text", "")}
PRODUCES: {prompt_info.get("what_it_produces", "")}
"""

    # Build XML-structured prompt
    prompt = f"""<task>Generate Section 2: What's Working Now from Deep Dive</task>

<requirements>
- 300-500 words
- THE MEAT of the newsletter - genuine value
- DO NOT dumb it down - make sophisticated strategies ACCESSIBLE
- Structure: Story hook -> What they did -> Why it worked -> How YOU apply it -> Action steps
- Include the ChatGPT prompt at the end as "Your Prompt" section
</requirements>

<deep_dive_content>
<headline>{deep_dive.get("headline", "")}</headline>

<the_story>{story_text}</the_story>

<what_they_did>{tactics_text}</what_they_did>

<why_it_worked>{why_text}</why_it_worked>

<beginner_application>{beginner_text}</beginner_application>

<action_steps>{steps_text}</action_steps>

<chatgpt_prompt>{prompt_text}</chatgpt_prompt>

<key_insight>{key_insight}</key_insight>
</deep_dive_content>

<prior_context>
{prior_context if prior_context else "This is Section 2, following the opening hook."}
</prior_context>

<output_format>
Write this as a flowing narrative that:
1. Opens with a compelling hook from the story (1-2 sentences)
2. Shares what they did (2-3 key tactics)
3. Explains WHY it worked (the mechanism - this is the gold)
4. Shows how a beginner applies the SAME PRINCIPLE
5. Ends with "Do This Today:" (3 specific steps)
6. Closes with "Your Prompt:" (the ChatGPT prompt in a code block)

Natural paragraph flow. No "Section 2" label. Bold key phrases.
Make it feel like a smart friend explaining something valuable.
</output_format>"""

    # Generate with voice profile
    result = client.generate_with_voice(prompt, max_tokens=1200)

    # Validate word count (300-500) - warn but don't fail
    is_valid, word_count = _validate_word_count(result, 300, 500, strict=False)
    logger.debug(
        f"Section 2 (from deep dive) generated: {word_count} words (target: 300-500)"
    )

    return result


def generate_section_3(
    content: dict,
    client: ClaudeClient,
    prior_sections: Optional[dict] = None,
) -> str:
    """
    Generate Section 3: The Breakdown (200-300 words).

    Story-sell bridge: narrative that leads to lesson.
    Ratio of story vs lesson depends on source material.

    Args:
        content: Source content dict with narrative potential
        client: ClaudeClient instance for generation
        prior_sections: Dict of prior sections for narrative context

    Returns:
        Generated section text (200-300 words)

    Raises:
        ValueError: If generated content fails word count validation
    """
    # Build prior context
    section_1_preview = ""
    section_2_preview = ""

    if prior_sections:
        if prior_sections.get("section_1"):
            section_1_preview = prior_sections["section_1"][:100]
        if prior_sections.get("section_2"):
            section_2_preview = prior_sections["section_2"][:200]

    # Build XML-structured prompt
    prompt = f"""<task>Generate Section 3: The Breakdown</task>

<requirements>
- 200-300 words
- Story-sell bridge format
- Match narrative weight to what content supports
- If source has strong story, lean into narrative
- If source is more tactical, shorter story + deeper lesson
- Must connect to actionable learning
</requirements>

<source_content>
Title: {content.get("title", "N/A")}
Summary: {content.get("summary", "N/A")}
Story: {content.get("story", content.get("summary", "N/A"))}
Source: {content.get("source", "N/A")}
</source_content>

<prior_context>
Section 1: {section_1_preview if section_1_preview else "N/A"}
Section 2: {section_2_preview if section_2_preview else "N/A"}
</prior_context>

<output_format>Natural paragraph flow, no headers</output_format>"""

    # Generate with voice profile
    result = client.generate_with_voice(prompt, max_tokens=600)

    # Validate word count (200-300) - warn but don't fail
    is_valid, word_count = _validate_word_count(result, 200, 300, strict=False)
    logger.debug(f"Section 3 generated: {word_count} words (target: 200-300)")

    return result


def generate_section_4(
    tool_info: dict,
    client: ClaudeClient,
    prior_sections: Optional[dict] = None,
) -> str:
    """
    Generate Section 4: Tool of the Week (100-200 words).

    CRITICAL: Insider friend energy, NEVER a pitch.
    Like sharing a secret with close friend.
    Should feel "almost illegal" - insider trading vibes.

    Args:
        tool_info: Dict containing:
            - name: Tool name (required)
            - description: What it does (required)
            - why_it_helps: Why it's valuable (required)
            - link: URL (optional)
            - is_affiliate: Whether it's an affiliate link (bool, optional)
        client: ClaudeClient instance for generation
        prior_sections: Dict of prior sections for context

    Returns:
        Generated section text (100-200 words)

    Raises:
        ValueError: If generated content fails word count validation
    """
    # Extract tool info
    tool_name = tool_info.get("name", "Unknown Tool")
    tool_description = tool_info.get("description", "")
    why_it_helps = tool_info.get("why_it_helps", "")
    is_affiliate = tool_info.get("is_affiliate", False)

    # Summarize prior sections
    prior_summary = _summarize_prior_sections(prior_sections, max_chars=150)

    # Build XML-structured prompt
    prompt = f"""<task>Generate Section 4: Tool of the Week</task>

<requirements>
- 100-200 words
- INSIDER FRIEND ENERGY - like sharing a secret
- Never gimmicky, salesy, or cliche
- Should feel "almost illegal" to share
- If affiliate, still feels like genuine recommendation
- Natural mention of tool name and what it does
</requirements>

<tool_info>
Name: {tool_name}
What it does: {tool_description}
Why it helps: {why_it_helps}
Is affiliate: {is_affiliate}
</tool_info>

<prior_context>Newsletter so far covers: {prior_summary}</prior_context>

<tone_guidance>
Good openings:
- "Found this last week and had to share..."
- "Not sure how this isn't more popular..."
- "This is what the 8-figure brands are using..."

Do NOT use:
- "revolutionary", "game-changing", "unlock"
- Marketing speak or corporate buzzwords
- Overselling - let the tool speak for itself
</tone_guidance>

<output_format>Conversational paragraph, no headers</output_format>"""

    # Generate with voice profile
    result = client.generate_with_voice(prompt, max_tokens=400)

    # Validate word count (100-200) - warn but don't fail
    is_valid, word_count = _validate_word_count(result, 100, 200, strict=False)
    logger.debug(f"Section 4 generated: {word_count} words (target: 100-200)")

    return result


def generate_section_5(
    client: ClaudeClient,
    prior_sections: Optional[dict] = None,
    ps_type: str = "foreshadow",
) -> str:
    """
    Generate Section 5: PS Statement (20-40 words).

    Second most-read part after subject line (per Hormozi).
    Purpose: reward reader, train clicking behavior.

    Args:
        client: ClaudeClient instance for generation
        prior_sections: Dict of prior sections for context
        ps_type: Type of PS statement:
            - "foreshadow": tease next week's content
            - "cta": secondary call to action
            - "meme": funny/relatable observation

    Returns:
        Generated PS statement text (20-40 words)

    Raises:
        ValueError: If generated content fails word count validation or doesn't start with PS
    """
    # Validate ps_type
    valid_types = ["foreshadow", "cta", "meme"]
    if ps_type not in valid_types:
        raise ValueError(f"Invalid ps_type: {ps_type}. Must be one of: {valid_types}")

    # Get key points from prior sections
    key_points = []
    if prior_sections:
        for name, content in prior_sections.items():
            if content and len(content) > 20:
                # Extract first sentence as key point
                first_sentence = (
                    content.split(".")[0] if "." in content else content[:50]
                )
                key_points.append(f"{name}: {first_sentence}")

    newsletter_context = (
        "\n".join(key_points[:3]) if key_points else "Newsletter covered DTC tactics"
    )

    # Type-specific guidance
    type_guidance = {
        "foreshadow": "Tease next week's content - create anticipation without giving away the secret",
        "cta": "Secondary call to action - reply to email, share with friend, check resource",
        "meme": "Funny/relatable observation - insider joke that rewards reading to the end",
    }

    # Build XML-structured prompt
    prompt = f"""<task>Generate Section 5: PS Statement</task>

<requirements>
- 20-40 words MAXIMUM
- Start with "PS:" or "P.S."
- Type: {ps_type}
  - {type_guidance[ps_type]}
- Purpose: reward reader, get them clicking
</requirements>

<newsletter_context>{newsletter_context}</newsletter_context>

<output_format>Single PS statement, nothing else</output_format>"""

    # Generate with voice profile (short max_tokens for PS)
    result = client.generate_with_voice(prompt, max_tokens=100)

    # Clean up result - ensure it starts with PS
    result = result.strip()

    # Validate starts with PS: or P.S.
    result_upper = result.upper()
    if not (
        result_upper.startswith("PS:")
        or result_upper.startswith("PS ")
        or result_upper.startswith("P.S.")
        or result_upper.startswith("P.S ")
    ):
        raise ValueError(
            f"Section 5 must start with 'PS:' or 'P.S.' but got: {result[:20]}..."
        )

    # Validate word count (20-40) - warn but don't fail
    is_valid, word_count = _validate_word_count(result, 20, 40, strict=False)
    logger.debug(f"Section 5 generated: {word_count} words (target: 20-40)")

    return result
