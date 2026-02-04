#!/usr/bin/env python3
"""
Deep dive generator for DTCNews newsletter.
DOE-VERSION: 2026.02.04

Takes the top viral content and creates genuine, valuable deep dives that:
1. Explain WHO is crushing it and their context
2. Break down WHAT they did step-by-step
3. Explain WHY it worked (the mechanism/psychology)
4. Show HOW a beginner can apply the same principle at their scale
5. Provide specific action steps executable TODAY

This is NOT about dumbing down content. It's about:
- Taking sophisticated strategies that are PROVEN to work
- Making them ACCESSIBLE without losing the insight
- Giving beginners the same competitive edge

Usage:
    python execution/deep_dive_generator.py --input output/content_ranked.json
    python execution/deep_dive_generator.py --topic "Email marketing strategy from $2M store"
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.claude_client import ClaudeClient
from execution.virality_analyzer import analyze_virality

DOE_VERSION = "2026.02.04"

# =============================================================================
# DEEP DIVE SYSTEM PROMPT
# =============================================================================

DEEP_DIVE_SYSTEM_PROMPT = """You are an expert ecommerce educator who creates genuinely valuable deep dives.

Your job is to take viral content/strategies and create a deep dive that:
1. Respects the reader's intelligence (don't dumb it down)
2. Makes sophisticated strategies accessible (explain the WHY)
3. Shows how the SAME PRINCIPLES apply at any scale
4. Gives specific, executable action steps

STRUCTURE YOUR DEEP DIVE:

## THE STORY (2-3 sentences)
Who did this? What was their situation? What result did they get?
Make it real and specific - names, numbers, context.

## WHAT THEY DID (The Strategy)
Break down the actual strategy in 3-5 clear points.
Be specific about tactics, not vague about "providing value."

## WHY IT WORKED (The Mechanism)
Explain the psychology or business principle that made this work.
This is what separates insight from surface-level advice.
Connect to universal principles (scarcity, social proof, reciprocity, etc.)

## THE BEGINNER VERSION (Your Action Plan)
Show how someone with 0-10 sales can apply the SAME PRINCIPLE.
Don't give them a watered-down version - give them the CORE that scales.

Key insight: A $2M store sending 5 emails/week and a new store sending 1 email/week 
are using the SAME PRINCIPLE (consistent value delivery). The principle scales.

## DO THIS TODAY (3 specific steps)
Give exactly 3 action steps they can complete in the next 2 hours.
Be specific: "Open Canva and create..." not "Create content..."

## THE PROMPT (Copy-paste ChatGPT prompt)
A prompt that helps them execute one of the action steps.
Max 100 words, one [VARIABLE] to fill in.

OUTPUT FORMAT (return as JSON):
{
  "headline": "Compelling headline for this deep dive",
  "the_story": {
    "who": "Name/description of who did this",
    "situation": "Their starting point or context",
    "result": "Specific outcome with numbers",
    "source": "Where this came from (Reddit, YouTube, etc.)"
  },
  "what_they_did": [
    {
      "tactic": "Specific tactic name",
      "details": "Exactly what they did",
      "why_important": "Why this specific thing mattered"
    }
  ],
  "why_it_worked": {
    "core_principle": "The underlying principle (e.g., 'reciprocity', 'social proof')",
    "mechanism": "How this principle played out in their specific case",
    "universal_truth": "Why this will ALWAYS work, not just for them"
  },
  "beginner_version": {
    "same_principle": "How the same principle applies at small scale",
    "what_to_focus_on": "The ONE thing that matters most",
    "what_to_ignore": "What to skip for now (advanced stuff)",
    "realistic_expectation": "What result a beginner can expect"
  },
  "action_steps": [
    {
      "step": 1,
      "action": "Specific action in imperative voice",
      "time": "How long this takes",
      "tool": "What tool to use (be specific)"
    }
  ],
  "prompt": {
    "text": "The actual ChatGPT prompt (max 100 words)",
    "what_it_produces": "What they'll get from this prompt",
    "variable": "What to replace [VARIABLE] with"
  },
  "key_insight": "One sentence capturing the most valuable takeaway"
}

IMPORTANT GUIDELINES:
- Be SPECIFIC. "Post on Instagram" is useless. "Post a carousel showing your product being used" is useful.
- Include NUMBERS. "Some people" is weak. "47% of respondents" or "3 out of 4 customers" is strong.
- Show the MECHANISM. Don't just say "it builds trust" - explain HOW and WHY it builds trust.
- The beginner version should feel EMPOWERING, not like a consolation prize.
- Action steps should be completable TODAY with tools they already have access to."""


def generate_deep_dive(
    content: dict | str,
    client: ClaudeClient | None = None,
    include_virality: bool = True,
) -> dict:
    """
    Generate a deep dive from viral content.

    Args:
        content: Content dict or string describing the topic
        client: ClaudeClient instance
        include_virality: Whether to include virality analysis context

    Returns:
        Deep dive dict with all sections
    """
    if client is None:
        client = ClaudeClient()

    # Build context
    if isinstance(content, dict):
        title = content.get("title", "")
        body = content.get(
            "summary", content.get("selftext", content.get("description", ""))
        )
        source = content.get("source", "unknown")
        outlier_score = content.get("outlier_score", 0)

        # Get virality analysis
        virality_context = ""
        if include_virality:
            virality = content.get("virality_analysis") or analyze_virality(content)
            hook_type = virality.get("hook_analysis", {}).get("hook_type", "unknown")
            triggers = [t["trigger"] for t in virality.get("emotional_triggers", [])]
            replication = virality.get("replication_notes", "")

            virality_context = f"""
VIRALITY ANALYSIS:
- Outlier score: {outlier_score:.1f}x (times better than average)
- Hook type: {hook_type}
- Emotional triggers: {", ".join(triggers) if triggers else "None detected"}
- Replication notes: {replication}
"""

        content_str = f"""TITLE: {title}

CONTENT: {body}

SOURCE: {source}
{virality_context}"""
    else:
        content_str = f"TOPIC: {content}"

    user_prompt = f"""Create a deep dive based on this viral content/topic:

{content_str}

Create a genuinely valuable deep dive that:
1. Tells the story of who did this and what they achieved
2. Breaks down exactly what they did (be specific)
3. Explains WHY it worked (the underlying principle)
4. Shows how a beginner (0-10 sales) can apply the SAME principle
5. Gives 3 specific actions they can take TODAY
6. Includes a ChatGPT prompt to help them execute

Remember: Don't dumb it down. Make sophisticated strategies ACCESSIBLE while keeping them VALUABLE.

Return as valid JSON."""

    response = client.generate(
        prompt=user_prompt,
        system_prompt=DEEP_DIVE_SYSTEM_PROMPT,
        max_tokens=3000,
    )

    # Parse JSON
    try:
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "raw_response": response,
            "parse_error": "Could not parse JSON",
        }


def format_deep_dive_markdown(dive: dict) -> str:
    """Format deep dive as newsletter-ready markdown."""
    lines = []

    # Headline
    lines.append(f"## {dive.get('headline', 'Deep Dive')}")
    lines.append("")

    # The Story
    story = dive.get("the_story", {})
    if story:
        lines.append(f"**{story.get('who', 'Someone')}** {story.get('situation', '')}.")
        lines.append(f"**The result?** {story.get('result', '')}")
        lines.append("")

    # What They Did
    tactics = dive.get("what_they_did", [])
    if tactics:
        lines.append("### What They Did")
        lines.append("")
        for t in tactics:
            lines.append(f"**{t.get('tactic', '')}:** {t.get('details', '')}")
            if t.get("why_important"):
                lines.append(f"*Why it matters: {t['why_important']}*")
            lines.append("")

    # Why It Worked
    why = dive.get("why_it_worked", {})
    if why:
        lines.append("### Why It Worked")
        lines.append("")
        lines.append(f"**Core principle:** {why.get('core_principle', '')}")
        lines.append("")
        lines.append(why.get("mechanism", ""))
        lines.append("")
        if why.get("universal_truth"):
            lines.append(f"*{why['universal_truth']}*")
            lines.append("")

    # Beginner Version
    beginner = dive.get("beginner_version", {})
    if beginner:
        lines.append("### How YOU Can Apply This")
        lines.append("")
        lines.append(
            f"**The same principle at your scale:** {beginner.get('same_principle', '')}"
        )
        lines.append("")
        lines.append(f"**Focus on:** {beginner.get('what_to_focus_on', '')}")
        lines.append("")
        if beginner.get("what_to_ignore"):
            lines.append(f"**Skip for now:** {beginner['what_to_ignore']}")
            lines.append("")
        lines.append(f"**What to expect:** {beginner.get('realistic_expectation', '')}")
        lines.append("")

    # Action Steps
    steps = dive.get("action_steps", [])
    if steps:
        lines.append("### Do This Today")
        lines.append("")
        for s in steps:
            time_str = f" ({s.get('time', '')})" if s.get("time") else ""
            tool_str = f" *Use: {s.get('tool')}*" if s.get("tool") else ""
            lines.append(f"**{s.get('step', '')}. {s.get('action', '')}**{time_str}")
            if tool_str:
                lines.append(tool_str)
            lines.append("")

    # The Prompt
    prompt = dive.get("prompt", {})
    if prompt and prompt.get("text"):
        lines.append("### Your ChatGPT Prompt")
        lines.append("")
        lines.append("Copy and paste this:")
        lines.append("")
        lines.append("```")
        lines.append(prompt["text"])
        lines.append("```")
        lines.append("")
        if prompt.get("variable"):
            lines.append(f"*Replace `[VARIABLE]` with: {prompt['variable']}*")
            lines.append("")
        lines.append(f"**What you'll get:** {prompt.get('what_it_produces', '')}")
        lines.append("")

    # Key Insight
    if dive.get("key_insight"):
        lines.append("---")
        lines.append("")
        lines.append(f"**Key insight:** {dive['key_insight']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate deep dives from viral content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Input JSON file with ranked/assessed content",
    )
    parser.add_argument(
        "--topic",
        "-t",
        help="Direct topic to create deep dive for",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Index of item to deep dive from input file (default: 0 = top item)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for deep dive",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)",
    )
    args = parser.parse_args()

    print(f"[deep_dive_generator] v{DOE_VERSION}")
    print()

    # Initialize client
    try:
        client = ClaudeClient()
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Get content to deep dive
    content = None

    if args.topic:
        content = args.topic
        print(f"Topic: {args.topic}")
    elif args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"ERROR: File not found: {args.input}")
            return 1

        with open(input_path) as f:
            data = json.load(f)

        # Find content list
        content_list = (
            data.get("ranked_content")
            or data.get("executable")
            or data.get("content")
            or data
        )
        if isinstance(content_list, dict):
            content_list = [content_list]

        if args.index >= len(content_list):
            print(
                f"ERROR: Index {args.index} out of range (only {len(content_list)} items)"
            )
            return 1

        content = content_list[args.index]
        print(f"Deep diving: {content.get('title', 'Unknown')[:60]}...")
    else:
        # Find most recent ranked file
        output_dir = Path("output")
        ranked_files = list(output_dir.glob("content_ranked_*.json")) + list(
            output_dir.glob("content_assessed_*.json")
        )
        if not ranked_files:
            print(
                "ERROR: No input. Run outlier_ranker.py first, or use --topic or --input"
            )
            return 1

        latest = max(ranked_files, key=lambda f: f.stat().st_mtime)
        with open(latest) as f:
            data = json.load(f)

        content_list = (
            data.get("ranked_content")
            or data.get("executable")
            or data.get("content", [])
        )
        if content_list:
            content = content_list[0]
            print(f"Using top item from {latest.name}")
            print(f"Deep diving: {content.get('title', 'Unknown')[:60]}...")
        else:
            print("ERROR: No content found in file")
            return 1

    print()
    print("Generating deep dive...")
    print()

    # Generate deep dive
    dive = generate_deep_dive(content, client)

    if "parse_error" in dive:
        print("WARNING: Could not parse structured response")
        print()
        print(dive.get("raw_response", "No response"))
        return 1

    # Output
    print("=" * 70)

    if args.format in ["json", "both"]:
        print("JSON OUTPUT:")
        print("-" * 40)
        print(json.dumps(dive, indent=2))
        print()

    if args.format in ["markdown", "both"]:
        print("MARKDOWN OUTPUT:")
        print("-" * 40)
        print(format_deep_dive_markdown(dive))
        print()

    # Save
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_path = Path("output") / f"deep_dive_{date_str}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": content.get("title", args.topic)
            if isinstance(content, dict)
            else args.topic,
        },
        "deep_dive": dive,
        "markdown": format_deep_dive_markdown(dive),
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved to: {output_path}")

    # Also save markdown version
    md_path = output_path.with_suffix(".md")
    with open(md_path, "w") as f:
        f.write(format_deep_dive_markdown(dive))
    print(f"Markdown saved to: {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
