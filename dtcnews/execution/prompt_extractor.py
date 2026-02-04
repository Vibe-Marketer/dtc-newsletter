#!/usr/bin/env python3
"""
Prompt extractor for DTCNews newsletter "Prompt Drop" section.
DOE-VERSION: 2026.02.04

Extracts or creates copy-paste ChatGPT prompts from tactical content.
Ensures prompts are under 150 words with exactly one bracketed variable.

Skill: .claude/skills/dtc-prompt-02/SKILL.md

Usage:
    python execution/prompt_extractor.py --content "Deep dive about product research..."
    python execution/prompt_extractor.py --file output/newsletter_draft.json --section deep_dive
    python execution/prompt_extractor.py --tactic "Writing product descriptions with AI"
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
# PROMPT EXTRACTION SYSTEM PROMPT
# =============================================================================

EXTRACTOR_SYSTEM_PROMPT = """You are a prompt engineer specializing in creating copy-paste ready ChatGPT prompts for beginner ecommerce entrepreneurs.

Your task is to analyze tactical content and create a single, high-value ChatGPT prompt that executes the main tactic automatically.

STRICT REQUIREMENTS:
1. Maximum 150 words total (shorter is better, aim for 50-80 words)
2. Exactly ONE bracketed variable: [YOUR PRODUCT], [YOUR NICHE], [YOUR OFFER], or [YOUR BRAND]
3. Specify exact output format (number of items, structure, length)
4. Output must be immediately usable - not a plan, not suggestions, actual copy they can use
5. A complete beginner could paste this and get useful results

OUTPUT FORMAT (return as JSON):
{
  "prompt_text": "The complete, copy-paste ready prompt under 150 words",
  "what_it_produces": "One sentence describing the output",
  "how_to_customize": "Instructions for the bracketed variable",
  "advanced_variation": "Optional enhancement for power users"
}

EXAMPLES OF GOOD PROMPTS:
- "I sell [YOUR PRODUCT]. Write 5 unique product descriptions for my website. Each should be 2-3 sentences, highlight a different benefit, and end with a soft call-to-action."
- "Write 10 Facebook ad headlines for [YOUR PRODUCT]. Use these patterns: questions, 'how I...' statements, counterintuitive claims, and specific numbers. Keep each under 10 words."

COMMON FAILURES TO AVOID:
- Prompts that produce "ideas" instead of finished copy
- Multiple variables that require research to fill
- Missing output specifications (user gets wall of text)
- Prompts about the tactic instead of executing the tactic"""


def extract_prompt(content: str, client: ClaudeClient) -> dict:
    """
    Extract or create a ChatGPT prompt from tactical content.

    Args:
        content: The tactical content (Deep Dive, tutorial, etc.)
        client: ClaudeClient instance

    Returns:
        Dict with prompt_text, what_it_produces, how_to_customize, advanced_variation
    """
    user_prompt = f"""Analyze this tactical content and create a copy-paste ready ChatGPT prompt:

CONTENT:
{content}

Create a prompt that executes the main tactic from this content. Remember:
- Max 150 words
- Exactly ONE [BRACKETED] variable
- Specify exact output format
- Must produce immediately usable output

Return your response as valid JSON."""

    response = client.generate(
        prompt=user_prompt,
        system_prompt=EXTRACTOR_SYSTEM_PROMPT,
        max_tokens=1024,
    )

    # Parse JSON from response
    try:
        # Try to extract JSON from response (may have markdown code blocks)
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(response)
    except json.JSONDecodeError:
        # If JSON parsing fails, create structured response from raw text
        result = {
            "prompt_text": response.strip(),
            "what_it_produces": "See prompt for details",
            "how_to_customize": "Replace the bracketed variable with your specific info",
            "advanced_variation": None,
        }

    return result


def validate_prompt(prompt_data: dict) -> tuple[bool, list[str]]:
    """
    Validate that a prompt meets quality requirements.

    Args:
        prompt_data: Dict with prompt_text and other fields

    Returns:
        Tuple of (is_valid, issues_list)
    """
    issues = []
    prompt_text = prompt_data.get("prompt_text", "")

    # Check word count
    word_count = len(prompt_text.split())
    if word_count > 150:
        issues.append(f"Prompt too long: {word_count} words (max 150)")

    # Check for bracketed variable
    variables = re.findall(r"\[YOUR [A-Z]+\]", prompt_text, re.IGNORECASE)
    if len(variables) == 0:
        issues.append(
            "Missing bracketed variable (need exactly one like [YOUR PRODUCT])"
        )
    elif len(variables) > 1:
        unique_vars = set(variables)
        if len(unique_vars) > 1:
            issues.append(
                f"Multiple variables found: {', '.join(unique_vars)} (need exactly one)"
            )

    # Check for output specification
    output_indicators = [
        r"\d+\s+(?:items?|options?|headlines?|descriptions?|ideas?|versions?)",
        r"list\s+(?:of\s+)?\d+",
        r"table",
        r"paragraph",
        r"sentence",
    ]
    has_output_spec = any(
        re.search(p, prompt_text, re.IGNORECASE) for p in output_indicators
    )
    if not has_output_spec:
        issues.append(
            "Consider adding output specification (e.g., 'Give me 5 options...')"
        )

    is_valid = len(issues) == 0
    return is_valid, issues


def format_prompt_drop(prompt_data: dict) -> str:
    """
    Format prompt data for newsletter Prompt Drop section.

    Args:
        prompt_data: Dict with prompt fields

    Returns:
        Formatted markdown for newsletter
    """
    output = []
    output.append("## PROMPT DROP")
    output.append("")
    output.append("Copy this prompt into ChatGPT:")
    output.append("")
    output.append("```")
    output.append(prompt_data.get("prompt_text", ""))
    output.append("```")
    output.append("")
    output.append(f"**What you'll get:** {prompt_data.get('what_it_produces', '')}")
    output.append("")
    output.append(f"**How to customize:** {prompt_data.get('how_to_customize', '')}")

    if prompt_data.get("advanced_variation"):
        output.append("")
        output.append(f"**Power user tip:** {prompt_data['advanced_variation']}")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Extract or create ChatGPT prompts from tactical content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--content",
        "-c",
        help="Direct content to extract prompt from",
    )
    parser.add_argument(
        "--file",
        "-f",
        help="JSON file containing newsletter draft",
    )
    parser.add_argument(
        "--section",
        "-s",
        default="deep_dive",
        help="Section to extract from in file (default: deep_dive)",
    )
    parser.add_argument(
        "--tactic",
        "-t",
        help="Brief description of tactic to create prompt for",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for prompt JSON (default: stdout)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)",
    )
    args = parser.parse_args()

    print(f"[prompt_extractor] v{DOE_VERSION}")
    print()

    # Determine content source
    content = None

    if args.content:
        content = args.content
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ERROR: File not found: {args.file}")
            return 1
        with open(file_path) as f:
            data = json.load(f)
        # Try to find the section
        content = data.get(args.section) or data.get("content", {}).get(args.section)
        if not content:
            print(f"ERROR: Section '{args.section}' not found in file")
            return 1
    elif args.tactic:
        content = f"Tactic: {args.tactic}\n\nCreate a prompt that helps a beginner ecommerce entrepreneur implement this tactic using AI."
    else:
        print("ERROR: Provide --content, --file, or --tactic")
        return 1

    print(f"Content length: {len(content)} chars")
    print()

    # Initialize Claude client
    try:
        client = ClaudeClient()
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Extract prompt
    print("Extracting prompt...")
    prompt_data = extract_prompt(content, client)

    # Validate
    is_valid, issues = validate_prompt(prompt_data)

    print()
    print("=" * 60)
    print("PROMPT EXTRACTION RESULTS")
    print("=" * 60)

    if not is_valid:
        print("VALIDATION WARNINGS:")
        for issue in issues:
            print(f"  - {issue}")
        print()

    # Output based on format
    if args.format in ["json", "both"]:
        print("JSON OUTPUT:")
        print("-" * 40)
        print(json.dumps(prompt_data, indent=2))
        print()

    if args.format in ["markdown", "both"]:
        print("MARKDOWN OUTPUT:")
        print("-" * 40)
        print(format_prompt_drop(prompt_data))
        print()

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_data = {
            "prompt": prompt_data,
            "validation": {"is_valid": is_valid, "issues": issues},
            "markdown": format_prompt_drop(prompt_data),
        }
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"Saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
