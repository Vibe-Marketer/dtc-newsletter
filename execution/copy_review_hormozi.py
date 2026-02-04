#!/usr/bin/env python3
"""
Hormozi hooks copy review for DTCNews newsletter.
DOE-VERSION: 2026.02.04

Reviews newsletter copy using Alex Hormozi's 100M Hooks framework.
Analyzes subject lines and opening hooks against proven patterns,
provides scored feedback with concrete rewrites.

Skill: .claude/skills/dtc-hormozi-03/SKILL.md

Usage:
    python execution/copy_review_hormozi.py --subject "Tips for Growing Your Store"
    python execution/copy_review_hormozi.py --file output/newsletter_draft.md
    python execution/copy_review_hormozi.py --subject "..." --opening "In this issue..."
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.claude_client import ClaudeClient

DOE_VERSION = "2026.02.04"

# =============================================================================
# HORMOZI HOOK TYPES
# =============================================================================

HOOK_TYPES = {
    "LABEL": {
        "description": "Calls out specific audience directly",
        "pattern": "[Audience], I have [something] for you",
        "example": "Local business owners, I have a gift for you",
    },
    "QUESTION": {
        "description": "Engages by asking what they want",
        "pattern": "Would you [desirable thing]?",
        "example": "Would you pay $1,000 to have the business of your dreams in 30 days?",
    },
    "CONDITIONAL": {
        "description": "Speaks to specific situations",
        "pattern": "If you're [situation], then [hook]",
        "example": "If you're working all the time and your business isn't growing...",
    },
    "COMMAND": {
        "description": "Direct instruction that implies value",
        "pattern": "Read this if... / Do this... / Stop [bad thing]",
        "example": "Read this if you want to win",
    },
    "STATEMENT": {
        "description": "Bold claim or truth bomb",
        "pattern": "The [thing] that [result]",
        "example": "The smartest thing you can do today",
    },
    "STORY": {
        "description": "Opens with narrative tension",
        "pattern": "[Person] just [achieved result]",
        "example": "My first nine businesses didn't really amount to anything. Nine.",
    },
    "PARADOX": {
        "description": "Unexpected contradiction that demands explanation",
        "pattern": "How a [unlikely person] [achieved result]",
        "example": "How a bald-headed barber saved my hair",
    },
    "LIST": {
        "description": "Promise of multiple value items",
        "pattern": "[Number] ways to [result]",
        "example": "3 hacks to make life suck less",
    },
    "CURIOSITY": {
        "description": "Creates information gap that must be closed",
        "pattern": "Incomplete thought or unexpected statement",
        "example": "The rumors are true...",
    },
}

TOP_PERFORMING_HOOKS = [
    "Real quick question...",
    "You might be wondering why I just caught a banana...",
    "That's weird... I don't see your name on the invite list?",
    "The rumors are true...",
    "Would you pay $1,000 to have the business of your dreams?",
    "$4,664 per month... That's what Kyle... the last person on the leaderboard...",
    "Which would you rather be? The guy pushing the boulder...",
    "Throw out your morning routine and switch to a money routine",
    "Local business owners, I have a gift for you",
    "I have a confession...",
]

# =============================================================================
# REVIEW SYSTEM PROMPT
# =============================================================================

HORMOZI_REVIEW_PROMPT = """You are a hook optimization expert trained on Alex Hormozi's 100M Hooks framework.

Your job is to analyze newsletter hooks (subject lines, preview text, opening lines) and provide:
1. Scored analysis on three dimensions
2. Identification of hook type used
3. Concrete rewrites using different hook types

HOOK COMPONENTS:
Every effective hook has two parts:
- CALL OUT: Gets the prospect to say "This is for me"
- CONDITION FOR VALUE: Why they should consume this content

SCORING DIMENSIONS (0-10 each):
1. ATTENTION: Does it stop the scroll in under 3 seconds?
   - 0-2: Generic, could be any newsletter
   - 7-8: Strong pattern interrupt, curiosity gap
   - 9-10: Irresistible - must click/read

2. TARGETING: Is it clear who this is for?
   - 0-2: No audience signal
   - 7-8: Specific audience, they'd self-identify
   - 9-10: Laser-targeted, readers say "this is for ME"

3. VALUE PROMISE: Is the benefit of reading clear?
   - 0-2: No reason to read
   - 7-8: Clear transformation or insight promised
   - 9-10: Compelling, specific value that demands attention

HOOK TYPES TO USE IN REWRITES:
- LABEL: "[Audience], [value hook]"
- QUESTION: "Would you [desire]?"
- COMMAND: "Read this if [condition]"
- CURIOSITY: "[pattern interrupt]..."
- STATEMENT: "The [thing] that [result]"
- PARADOX: "How a [unlikely person] [achieved result]"
- LIST: "[Number] ways to [result]"

TOP PERFORMERS TO REFERENCE:
1. "Real quick question..."
2. "The rumors are true..."
3. "Would you pay $1,000 to have the business of your dreams?"
4. "Local business owners, I have a gift for you"
5. "I have a confession..."

OUTPUT FORMAT (return as JSON):
{
  "hooks_analyzed": [
    {
      "location": "subject_line",
      "original": "...",
      "type_detected": "STATEMENT|QUESTION|etc",
      "scores": {
        "attention": 5,
        "attention_note": "...",
        "targeting": 3,
        "targeting_note": "...",
        "value": 4,
        "value_note": "...",
        "overall": 4.0
      },
      "has_call_out": true/false,
      "has_condition_for_value": true/false,
      "rewrites": [
        {"type": "LABEL", "text": "..."},
        {"type": "QUESTION", "text": "..."},
        {"type": "COMMAND", "text": "..."},
        {"type": "CURIOSITY", "text": "..."},
        {"type": "STATEMENT", "text": "..."}
      ]
    }
  ],
  "best_rewrite": {
    "location": "...",
    "text": "...",
    "type": "...",
    "rationale": "..."
  },
  "quick_win": "Small tweak to current that would improve score",
  "strategy_note": "Any broader observations about hook strategy"
}"""


def review_hooks(
    subject: str,
    preview: str | None = None,
    opening: str | None = None,
    client: ClaudeClient | None = None,
) -> dict:
    """
    Review hooks using Hormozi framework.

    Args:
        subject: Subject line to review
        preview: Optional preview/preheader text
        opening: Optional opening paragraph
        client: ClaudeClient instance (created if not provided)

    Returns:
        Dict with analysis, scores, and rewrites
    """
    if client is None:
        client = ClaudeClient()

    # Build the review request
    hooks_to_review = [f"Subject Line: {subject}"]
    if preview:
        hooks_to_review.append(f"Preview Text: {preview}")
    if opening:
        hooks_to_review.append(f"Opening Line: {opening}")

    user_prompt = f"""Analyze these newsletter hooks and provide scored feedback with rewrites:

{chr(10).join(hooks_to_review)}

Context: This is for DTCNews, a newsletter targeting beginner ecommerce entrepreneurs (0-10 sales).

Provide your analysis as valid JSON following the format specified."""

    response = client.generate(
        prompt=user_prompt,
        system_prompt=HORMOZI_REVIEW_PROMPT,
        max_tokens=2048,
    )

    # Parse JSON from response
    try:
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(response)
    except json.JSONDecodeError:
        # Return raw response if JSON parsing fails
        result = {
            "raw_analysis": response,
            "parse_error": "Could not parse JSON response",
        }

    return result


def format_review_report(review: dict) -> str:
    """
    Format review results as markdown report.

    Args:
        review: Dict with analysis results

    Returns:
        Formatted markdown report
    """
    lines = []
    lines.append("# HORMOZI HOOK REVIEW")
    lines.append("")

    if "parse_error" in review:
        lines.append("## RAW ANALYSIS")
        lines.append(review.get("raw_analysis", "No analysis available"))
        return "\n".join(lines)

    # Analyzed hooks
    hooks = review.get("hooks_analyzed", [])
    for hook in hooks:
        location = hook.get("location", "unknown").replace("_", " ").title()
        lines.append(f"## {location}")
        lines.append("")
        lines.append(f'**Original:** "{hook.get("original", "")}"')
        lines.append(f"**Type Detected:** {hook.get('type_detected', 'Unknown')}")
        lines.append("")

        scores = hook.get("scores", {})
        lines.append("### Scores")
        lines.append(
            f"- Attention: {scores.get('attention', 0)}/10 - {scores.get('attention_note', '')}"
        )
        lines.append(
            f"- Targeting: {scores.get('targeting', 0)}/10 - {scores.get('targeting_note', '')}"
        )
        lines.append(
            f"- Value: {scores.get('value', 0)}/10 - {scores.get('value_note', '')}"
        )
        lines.append(f"- **Overall: {scores.get('overall', 0)}/10**")
        lines.append("")

        lines.append("### Analysis")
        lines.append(
            f"- Call Out Present: {'Yes' if hook.get('has_call_out') else 'No'}"
        )
        lines.append(
            f"- Condition for Value: {'Yes' if hook.get('has_condition_for_value') else 'No'}"
        )
        lines.append("")

        lines.append("### Rewrites")
        for rewrite in hook.get("rewrites", []):
            lines.append(f'- [{rewrite.get("type", "")}] "{rewrite.get("text", "")}"')
        lines.append("")

    # Best rewrite
    best = review.get("best_rewrite", {})
    if best:
        lines.append("## RECOMMENDATION")
        lines.append(
            f'**Best Option:** [{best.get("type", "")}] "{best.get("text", "")}"'
        )
        lines.append(f"**Rationale:** {best.get('rationale', '')}")
        lines.append("")

    # Quick win
    quick_win = review.get("quick_win")
    if quick_win:
        lines.append(f"**Quick Win:** {quick_win}")
        lines.append("")

    # Strategy note
    strategy = review.get("strategy_note")
    if strategy:
        lines.append(f"**Strategy Note:** {strategy}")

    return "\n".join(lines)


def extract_hooks_from_file(file_path: Path) -> dict:
    """
    Extract hooks from a newsletter draft file.

    Args:
        file_path: Path to markdown or JSON file

    Returns:
        Dict with subject, preview, opening
    """
    content = file_path.read_text()

    result = {
        "subject": None,
        "preview": None,
        "opening": None,
    }

    if file_path.suffix == ".json":
        data = json.loads(content)
        result["subject"] = data.get("subject_line") or data.get("subject")
        result["preview"] = data.get("preview_text") or data.get("preview")
        result["opening"] = data.get("opening") or data.get("intro")
    else:
        # Try to extract from markdown
        # Look for subject line patterns
        subject_match = re.search(r"(?:subject|title):\s*(.+)", content, re.IGNORECASE)
        if subject_match:
            result["subject"] = subject_match.group(1).strip().strip("\"'")

        # Look for preview text
        preview_match = re.search(
            r"(?:preview|preheader):\s*(.+)", content, re.IGNORECASE
        )
        if preview_match:
            result["preview"] = preview_match.group(1).strip().strip("\"'")

        # First paragraph after header as opening
        para_match = re.search(r"^#.+\n\n(.+?)(?:\n\n|$)", content, re.MULTILINE)
        if para_match:
            result["opening"] = para_match.group(1).strip()

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Review newsletter hooks using Hormozi's 100M Hooks framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--subject",
        "-s",
        help="Subject line to review",
    )
    parser.add_argument(
        "--preview",
        "-p",
        help="Preview/preheader text to review",
    )
    parser.add_argument(
        "--opening",
        "-o",
        help="Opening paragraph to review",
    )
    parser.add_argument(
        "--file",
        "-f",
        help="Newsletter draft file (markdown or JSON)",
    )
    parser.add_argument(
        "--output",
        help="Output file for review JSON",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)",
    )
    args = parser.parse_args()

    print(f"[copy_review_hormozi] v{DOE_VERSION}")
    print()

    # Get hooks to review
    subject = args.subject
    preview = args.preview
    opening = args.opening

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ERROR: File not found: {args.file}")
            return 1
        extracted = extract_hooks_from_file(file_path)
        subject = subject or extracted["subject"]
        preview = preview or extracted["preview"]
        opening = opening or extracted["opening"]

    if not subject:
        print("ERROR: Subject line required. Use --subject or --file")
        return 1

    print(f"Subject: {subject}")
    if preview:
        print(f"Preview: {preview}")
    if opening:
        print(f"Opening: {opening[:60]}...")
    print()

    # Initialize Claude client
    try:
        client = ClaudeClient()
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Review hooks
    print("Analyzing hooks...")
    review = review_hooks(subject, preview, opening, client)

    print()
    print("=" * 60)

    # Output based on format
    if args.format in ["json", "both"]:
        print("JSON OUTPUT:")
        print("-" * 40)
        print(json.dumps(review, indent=2))
        print()

    if args.format in ["markdown", "both"]:
        print("MARKDOWN REPORT:")
        print("-" * 40)
        print(format_review_report(review))
        print()

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_data = {
            "input": {"subject": subject, "preview": preview, "opening": opening},
            "review": review,
            "report": format_review_report(review),
        }
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"Saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
