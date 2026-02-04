#!/usr/bin/env python3
"""
Schwartz copy review for DTCNews newsletter.
DOE-VERSION: 2026.02.04

Reviews newsletter copy using Eugene Schwartz's Breakthrough Advertising principles.
Analyzes awareness stage match, applies verbalization techniques to strengthen claims,
and checks three-dimension coverage (desires, identifications, beliefs).

Skill: .claude/skills/dtc-schwartz-04/SKILL.md

Usage:
    python execution/copy_review_schwartz.py --file output/newsletter_draft.md
    python execution/copy_review_schwartz.py --content "Your newsletter copy here..."
    python execution/copy_review_schwartz.py --claims "Save time, Make money, Easy to use"
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
# VERBALIZATION TECHNIQUES
# =============================================================================

VERBALIZATION_TECHNIQUES = {
    "MEASURE_SIZE": {
        "description": "Add specific numbers to quantify the claim",
        "weak": "Lots of prompts included",
        "strong": "47 prompts included in the pack",
    },
    "MEASURE_SPEED": {
        "description": "Add timeframes to show how fast results come",
        "weak": "Get product descriptions quickly",
        "strong": "Get your first product description in 30 seconds",
    },
    "COMPARE": {
        "description": "Show contrast with alternatives using 'Instead of X, you get Y'",
        "weak": "Save time on research",
        "strong": "Instead of 3 hours researching, get answers in 3 minutes",
    },
    "METAPHORIZE": {
        "description": "Make abstract concepts concrete with vivid imagery",
        "weak": "AI does the work",
        "strong": "This prompt does the heavy lifting for you",
    },
    "SENSITIZE": {
        "description": "Make the reader feel, smell, touch, see, or hear it",
        "weak": "Make your first sale",
        "strong": "Imagine opening your phone to see your first sale notification",
    },
    "DEMONSTRATE": {
        "description": "Show a prime example that proves the claim",
        "weak": "People get results",
        "strong": "Sarah used this exact prompt and got her first 3 sales in a week",
    },
    "PARADOX": {
        "description": "Something that seems contradictory but is true",
        "weak": "Easy to use even if you're not technical",
        "strong": "How a non-techie built a store in 48 hours",
    },
    "REMOVE_LIMITATIONS": {
        "description": "Show what the reader won't have to do or suffer",
        "weak": "Easy copywriting",
        "strong": "Write product descriptions without any copywriting skills",
    },
    "BEFORE_AFTER": {
        "description": "Contrast the two states explicitly",
        "weak": "Write descriptions faster",
        "strong": "Before: 3 hours writing one description. After: 3 minutes.",
    },
    "CHALLENGE": {
        "description": "Turn it into a test or challenge",
        "weak": "AI writes like a human",
        "strong": "Can you tell which description was written by AI?",
    },
}

# =============================================================================
# THREE DIMENSIONS
# =============================================================================

THREE_DIMENSIONS = {
    "DESIRES": {
        "description": "The Want - Intensify physical, material, sensual wants. Give them a goal.",
        "dtcnews_examples": [
            "income",
            "freedom",
            "validation",
            "escape 9-5",
            "be own boss",
            "work from anywhere",
        ],
        "weak": "Make money online",
        "strong": "Wake up to sales that happened while you slept",
    },
    "IDENTIFICATIONS": {
        "description": "The Becoming - The role they want to play, who they want to be seen as.",
        "dtcnews_examples": [
            "successful entrepreneur",
            "smart investor",
            "ahead of the curve",
            "tech-savvy",
            "financially independent",
        ],
        "weak": "Learn ecommerce",
        "strong": "Join the founders who figured this out early",
    },
    "BELIEFS": {
        "description": "The Framework - Work WITHIN existing beliefs and prejudices - never fight them.",
        "dtcnews_examples": [
            "AI is the future",
            "dropshipping works",
            "passive income is possible",
            "hard work pays off",
            "there must be a faster way",
        ],
        "weak": "Forget everything you know about business",
        "strong": "You already know AI is changing everything. Here's how to use it.",
    },
}

# =============================================================================
# REVIEW SYSTEM PROMPT
# =============================================================================

SCHWARTZ_REVIEW_PROMPT = """You are a direct response copywriting expert trained on Eugene Schwartz's Breakthrough Advertising principles.

Your job is to analyze newsletter copy and provide:
1. Awareness stage analysis (is copy matching audience awareness?)
2. Claim audit with verbalization technique improvements
3. Three dimensions coverage score

AUDIENCE CONTEXT (DTCNews):
- Awareness Stage: Problem Aware to Solution Aware
  - They KNOW they want income, freedom, escape from 9-5
  - They KNOW solutions like Shopify and dropshipping exist
  - They DON'T know our specific products or why they're best
- Market Sophistication: Stage 1-2 (direct claims still work)

AWARENESS STAGES:
- UNAWARE: Don't know they have a problem
- PROBLEM AWARE: Know the problem, don't know solutions exist
- SOLUTION AWARE: Know solutions exist, don't know your product
- PRODUCT AWARE: Know your product, not convinced yet
- MOST AWARE: Know and love you, need a deal

VERBALIZATION TECHNIQUES (use these to strengthen weak claims):
1. MEASURE_SIZE - Add specific numbers
2. MEASURE_SPEED - Add timeframes
3. COMPARE - "Instead of X, you get Y"
4. METAPHORIZE - Make abstract concrete
5. SENSITIZE - Appeal to senses
6. DEMONSTRATE - Show prime example
7. PARADOX - Contradictory but true
8. REMOVE_LIMITATIONS - Show what they won't suffer
9. BEFORE_AFTER - Contrast two states
10. CHALLENGE - Turn into a test

THREE DIMENSIONS (score 0-2 each):
- DESIRES: Does it paint what they GET? (income, freedom, validation)
- IDENTIFICATIONS: Does it show who they BECOME? (successful entrepreneur, ahead of curve)
- BELIEFS: Does it work WITHIN their worldview? (AI is future, passive income possible)

OUTPUT FORMAT (return as JSON):
{
  "awareness_analysis": {
    "assumed_stage": "PROBLEM_AWARE|SOLUTION_AWARE|etc",
    "correct_for_audience": true/false,
    "explanation": "...",
    "recommended_adjustment": "..." or null
  },
  "claim_audit": [
    {
      "original_claim": "...",
      "issue": "vague|no_proof|weak|etc",
      "technique": "MEASURE_SIZE|COMPARE|etc",
      "strengthened": "..."
    }
  ],
  "three_dimensions": {
    "desires": {
      "score": 0-2,
      "explanation": "...",
      "suggestion": "..." or null
    },
    "identifications": {
      "score": 0-2,
      "explanation": "...",
      "suggestion": "..." or null
    },
    "beliefs": {
      "score": 0-2,
      "explanation": "...",
      "suggestion": "..." or null
    },
    "total": 0-6
  },
  "rewritten_sections": [
    {
      "section": "...",
      "original": "...",
      "improved": "...",
      "technique_used": "..."
    }
  ],
  "summary": {
    "strengths": ["..."],
    "priority_fixes": ["..."]
  }
}"""


def review_copy(content: str, client: ClaudeClient | None = None) -> dict:
    """
    Review copy using Schwartz principles.

    Args:
        content: Newsletter copy to review
        client: ClaudeClient instance (created if not provided)

    Returns:
        Dict with analysis, claim audit, dimension scores, and rewrites
    """
    if client is None:
        client = ClaudeClient()

    user_prompt = f"""Analyze this newsletter copy using Breakthrough Advertising principles:

---
{content}
---

Provide:
1. Awareness stage analysis
2. Identify and strengthen weak claims using verbalization techniques
3. Score the three dimensions (desires, identifications, beliefs)
4. Rewrite weak sections

Return your analysis as valid JSON following the format specified."""

    response = client.generate(
        prompt=user_prompt,
        system_prompt=SCHWARTZ_REVIEW_PROMPT,
        max_tokens=3000,
    )

    # Parse JSON from response
    try:
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(response)
    except json.JSONDecodeError:
        result = {
            "raw_analysis": response,
            "parse_error": "Could not parse JSON response",
        }

    return result


def strengthen_claims(
    claims: list[str], client: ClaudeClient | None = None
) -> list[dict]:
    """
    Apply verbalization techniques to strengthen a list of claims.

    Args:
        claims: List of claim strings to strengthen
        client: ClaudeClient instance

    Returns:
        List of dicts with original, technique, strengthened
    """
    if client is None:
        client = ClaudeClient()

    techniques_ref = "\n".join(
        [
            f"- {name}: {info['description']} (e.g., '{info['weak']}' -> '{info['strong']}')"
            for name, info in VERBALIZATION_TECHNIQUES.items()
        ]
    )

    user_prompt = f"""Strengthen these weak claims using verbalization techniques:

CLAIMS:
{chr(10).join(f"- {claim}" for claim in claims)}

TECHNIQUES:
{techniques_ref}

For each claim, pick the best technique and provide a strengthened version.
Return as JSON array:
[{{"original": "...", "technique": "TECHNIQUE_NAME", "strengthened": "..."}}]"""

    response = client.generate(
        prompt=user_prompt,
        system_prompt="You are a direct response copywriting expert. Transform weak claims into compelling copy using verbalization techniques.",
        max_tokens=2000,
    )

    try:
        json_match = re.search(r"\[[\s\S]*\]", response)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except json.JSONDecodeError:
        return [
            {"original": c, "technique": "UNKNOWN", "strengthened": c} for c in claims
        ]


def format_review_report(review: dict) -> str:
    """
    Format review results as markdown report.

    Args:
        review: Dict with analysis results

    Returns:
        Formatted markdown report
    """
    lines = []
    lines.append("# SCHWARTZ COPY REVIEW")
    lines.append("")

    if "parse_error" in review:
        lines.append("## RAW ANALYSIS")
        lines.append(review.get("raw_analysis", "No analysis available"))
        return "\n".join(lines)

    # Awareness Analysis
    awareness = review.get("awareness_analysis", {})
    lines.append("## AWARENESS ANALYSIS")
    lines.append(f"**Assumed Stage:** {awareness.get('assumed_stage', 'Unknown')}")
    lines.append(
        f"**Correct for Audience:** {'Yes' if awareness.get('correct_for_audience') else 'No'}"
    )
    lines.append(f"**Explanation:** {awareness.get('explanation', '')}")
    if awareness.get("recommended_adjustment"):
        lines.append(
            f"**Recommended Adjustment:** {awareness['recommended_adjustment']}"
        )
    lines.append("")

    # Claim Audit
    claims = review.get("claim_audit", [])
    if claims:
        lines.append("## CLAIM AUDIT")
        lines.append("")
        lines.append("| Original Claim | Issue | Technique | Strengthened |")
        lines.append("|----------------|-------|-----------|--------------|")
        for claim in claims:
            lines.append(
                f"| {claim.get('original_claim', '')} | {claim.get('issue', '')} | {claim.get('technique', '')} | {claim.get('strengthened', '')} |"
            )
        lines.append("")

    # Three Dimensions
    dims = review.get("three_dimensions", {})
    if dims:
        lines.append("## THREE DIMENSIONS SCORE")
        lines.append("")
        for dim_name in ["desires", "identifications", "beliefs"]:
            dim = dims.get(dim_name, {})
            lines.append(
                f"**{dim_name.title()}:** {dim.get('score', 0)}/2 - {dim.get('explanation', '')}"
            )
            if dim.get("suggestion"):
                lines.append(f"  - Suggestion: {dim['suggestion']}")
        lines.append("")
        lines.append(f"**Total: {dims.get('total', 0)}/6**")
        lines.append("")

    # Rewritten Sections
    rewrites = review.get("rewritten_sections", [])
    if rewrites:
        lines.append("## REWRITTEN SECTIONS")
        lines.append("")
        for rewrite in rewrites:
            lines.append(f"### {rewrite.get('section', 'Section')}")
            lines.append(f'**Original:** "{rewrite.get("original", "")}"')
            lines.append(f'**Improved:** "{rewrite.get("improved", "")}"')
            lines.append(f"**Technique:** {rewrite.get('technique_used', '')}")
            lines.append("")

    # Summary
    summary = review.get("summary", {})
    if summary:
        lines.append("## SUMMARY")
        lines.append("")
        if summary.get("strengths"):
            lines.append("**Strengths:**")
            for s in summary["strengths"]:
                lines.append(f"- {s}")
            lines.append("")
        if summary.get("priority_fixes"):
            lines.append("**Priority Fixes:**")
            for i, fix in enumerate(summary["priority_fixes"], 1):
                lines.append(f"{i}. {fix}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Review newsletter copy using Schwartz's Breakthrough Advertising principles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        "-f",
        help="Newsletter draft file to review",
    )
    parser.add_argument(
        "--content",
        "-c",
        help="Direct content to review",
    )
    parser.add_argument(
        "--claims",
        help="Comma-separated list of claims to strengthen",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for review JSON",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)",
    )
    args = parser.parse_args()

    print(f"[copy_review_schwartz] v{DOE_VERSION}")
    print()

    # Initialize Claude client
    try:
        client = ClaudeClient()
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Handle claims-only mode
    if args.claims:
        claims = [c.strip() for c in args.claims.split(",")]
        print(f"Strengthening {len(claims)} claims...")
        print()

        results = strengthen_claims(claims, client)

        print("=" * 60)
        print("STRENGTHENED CLAIMS")
        print("=" * 60)
        for r in results:
            print(f"Original: {r['original']}")
            print(f"Technique: {r['technique']}")
            print(f"Strengthened: {r['strengthened']}")
            print()

        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Saved to: {args.output}")

        return 0

    # Get content to review
    content = args.content

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ERROR: File not found: {args.file}")
            return 1
        content = file_path.read_text()

    if not content:
        print("ERROR: Provide --file, --content, or --claims")
        return 1

    print(f"Content length: {len(content)} chars")
    print()

    # Review copy
    print("Analyzing copy...")
    review = review_copy(content, client)

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
            "review": review,
            "report": format_review_report(review),
        }
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"Saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
