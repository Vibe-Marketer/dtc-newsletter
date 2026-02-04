#!/usr/bin/env python3
"""
Editor agent for DTCNews newsletter final pass.
DOE-VERSION: 2026.02.04

Performs final editing checks including:
- Reading level analysis (6th-8th grade target)
- Jargon removal/explanation
- Spam trigger replacement
- Formatting validation
- Voice compliance verification

Skill: .claude/skills/dtc-editor-06/SKILL.md

Usage:
    python execution/editor_agent.py --file output/newsletter_draft.md
    python execution/editor_agent.py --content "Newsletter content..."
    python execution/editor_agent.py --file draft.md --fix --output polished.md
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

from execution.anti_pattern_validator import validate_voice, count_sentence_stats

DOE_VERSION = "2026.02.04"

# =============================================================================
# JARGON GLOSSARY
# =============================================================================

JARGON_REPLACEMENTS = {
    "roas": ("return on ad spend", "profit per dollar spent on ads"),
    "aov": ("average order value", "typical purchase amount"),
    "ltv": ("customer lifetime value", "total revenue from one customer"),
    "clv": ("customer lifetime value", "total revenue from one customer"),
    "cac": ("customer acquisition cost", "cost to get one new customer"),
    "cpa": ("cost per acquisition", "cost per sale or signup"),
    "ctr": ("click-through rate", "percentage who click"),
    "cvr": ("conversion rate", "percentage who buy"),
    "cro": ("conversion rate optimization", "improving your checkout"),
    "ugc": ("user-generated content", "customer photos/videos"),
    "dtc": ("direct-to-consumer", "selling directly, no middleman"),
    "d2c": ("direct-to-consumer", "selling directly, no middleman"),
    "kpi": ("key performance indicator", "important metric to track"),
    "roi": ("return on investment", "profit compared to what you spent"),
    "sem": ("search engine marketing", "paid ads on Google"),
    "seo": ("search engine optimization", "ranking in Google for free"),
    "b2b": ("business-to-business", "selling to other businesses"),
    "b2c": ("business-to-consumer", "selling to regular people"),
    "skus": ("stock keeping units", "different product variants"),
    "sku": ("stock keeping unit", "a specific product variant"),
}

# =============================================================================
# SPAM TRIGGERS
# =============================================================================

SPAM_TRIGGERS = {
    # High risk - always replace
    "free": ["no-cost", "complimentary", None],
    "act now": ["try this today", "start with", None],
    "limited time": [None, "this week", "for now"],
    "click here": ["read the guide", "see examples", "check it out"],
    "guarantee": ["promise", None],
    "100%": ["fully", "completely"],
    "buy now": ["get started", "try it"],
    # Medium risk
    "urgent": ["important", "time-sensitive"],
    "exclusive": ["early access", "insider"],
    "amazing": [None],  # Replace with specific benefit
    "incredible": [None],  # Replace with specific result
}

# =============================================================================
# EDITING FUNCTIONS
# =============================================================================


def check_reading_level(content: str) -> dict:
    """
    Analyze reading level and sentence structure.

    Args:
        content: Text content to analyze

    Returns:
        Dict with stats and issues
    """
    stats = count_sentence_stats(content)

    issues = []

    # Check average words per sentence
    avg_words = stats.get("avg_words_per_sentence", 0)
    if avg_words > 20:
        issues.append(
            f"Average sentence length too high: {avg_words:.1f} words (target: under 15)"
        )
    elif avg_words > 15:
        issues.append(
            f"Average sentence length slightly high: {avg_words:.1f} words (target: under 15)"
        )

    # Check for very long sentences
    sentence_lengths = stats.get("sentence_lengths", [])
    long_sentences = [i for i, length in enumerate(sentence_lengths) if length > 25]
    if long_sentences:
        issues.append(
            f"Found {len(long_sentences)} sentences over 25 words (split these)"
        )

    # Check rhythm score
    rhythm = stats.get("rhythm_score", 0)
    if rhythm < 70:
        issues.append(f"Rhythm score low: {rhythm}/100 (target: 70+)")

    return {
        "stats": stats,
        "issues": issues,
        "passed": len(issues) == 0,
    }


def find_jargon(content: str) -> list[dict]:
    """
    Find industry jargon that needs explanation or replacement.

    Args:
        content: Text content to scan

    Returns:
        List of dicts with term, context, and suggested replacement
    """
    found = []
    content_lower = content.lower()

    for term, (full_form, plain_english) in JARGON_REPLACEMENTS.items():
        # Check if term exists but isn't already explained
        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, content_lower):
            # Check if already explained in parentheses
            explained_pattern = rf"\b{re.escape(term)}\s*\([^)]+\)"
            if not re.search(explained_pattern, content_lower):
                found.append(
                    {
                        "term": term.upper(),
                        "full_form": full_form,
                        "plain_english": plain_english,
                        "suggestion": f"{term.upper()} ({plain_english})"
                        if plain_english
                        else full_form,
                    }
                )

    return found


def find_spam_triggers(content: str) -> list[dict]:
    """
    Find spam trigger words that should be replaced.

    Args:
        content: Text content to scan

    Returns:
        List of dicts with trigger and replacements
    """
    found = []
    content_lower = content.lower()

    for trigger, replacements in SPAM_TRIGGERS.items():
        pattern = rf"\b{re.escape(trigger)}\b"
        matches = list(re.finditer(pattern, content_lower))
        if matches:
            valid_replacements = [r for r in replacements if r is not None]
            found.append(
                {
                    "trigger": trigger,
                    "count": len(matches),
                    "replacements": valid_replacements,
                    "note": "Replace with specific benefit"
                    if not valid_replacements
                    else None,
                }
            )

    return found


def check_formatting(content: str) -> list[str]:
    """
    Check formatting issues.

    Args:
        content: Text content to check

    Returns:
        List of formatting issues
    """
    issues = []

    # Check for ALL CAPS (except common acronyms)
    allowed_caps = {
        "AI",
        "GPT",
        "CEO",
        "CTO",
        "FAQ",
        "DIY",
        "URL",
        "PDF",
        "PS",
        "TL",
        "DR",
    }
    caps_words = re.findall(r"\b[A-Z]{2,}\b", content)
    suspicious_caps = [w for w in caps_words if w not in allowed_caps]
    if suspicious_caps:
        issues.append(
            f"ALL CAPS words found (may trigger spam filters): {', '.join(set(suspicious_caps)[:5])}"
        )

    # Check exclamation points
    exclamation_count = content.count("!")
    if exclamation_count > 1:
        issues.append(
            f"Too many exclamation points: {exclamation_count} (max 1 per newsletter)"
        )

    # Check for multiple consecutive question marks or exclamation points
    if re.search(r"[!?]{2,}", content):
        issues.append("Multiple consecutive punctuation marks (!!/??) - unprofessional")

    # Check bold usage (rough estimate based on markdown)
    bold_count = len(re.findall(r"\*\*[^*]+\*\*", content))
    # Count sections (rough: each ## header)
    section_count = max(1, len(re.findall(r"^##\s", content, re.MULTILINE)))
    if bold_count > section_count * 3:
        issues.append(
            f"Excessive bold text: ~{bold_count} instances (max 3 per section)"
        )

    return issues


def calculate_confidence_score(
    reading_issues: list,
    jargon: list,
    spam_triggers: list,
    formatting_issues: list,
    voice_violations: list,
) -> int:
    """
    Calculate overall confidence score for the newsletter.

    Args:
        reading_issues: Reading level issues
        jargon: Unexplained jargon found
        spam_triggers: Spam triggers found
        formatting_issues: Formatting problems
        voice_violations: Voice anti-pattern violations

    Returns:
        Score 0-100 (90+ = ready for review, 70-89 = minor concerns, <70 = needs work)
    """
    score = 100

    # Reading level penalties
    score -= len(reading_issues) * 5

    # Jargon penalties (minor)
    score -= len(jargon) * 2

    # Spam trigger penalties
    score -= len(spam_triggers) * 5

    # Formatting penalties
    score -= len(formatting_issues) * 3

    # Voice violations are serious
    score -= len(voice_violations) * 8

    return max(0, min(100, score))


def edit_content(content: str) -> tuple[str, dict]:
    """
    Run full editing pass on content.

    Args:
        content: Content to edit

    Returns:
        Tuple of (content, report) - note: content is unchanged in analyze mode
    """
    # Reading level
    reading_result = check_reading_level(content)

    # Jargon
    jargon_found = find_jargon(content)

    # Spam triggers
    spam_found = find_spam_triggers(content)

    # Formatting
    formatting_issues = check_formatting(content)

    # Voice
    voice_valid, voice_violations = validate_voice(content)

    # Calculate confidence
    confidence = calculate_confidence_score(
        reading_result["issues"],
        jargon_found,
        spam_found,
        formatting_issues,
        voice_violations,
    )

    report = {
        "reading_level": reading_result,
        "jargon": jargon_found,
        "spam_triggers": spam_found,
        "formatting": formatting_issues,
        "voice": {
            "valid": voice_valid,
            "violations": voice_violations,
        },
        "confidence_score": confidence,
        "ready_for_review": confidence >= 70,
    }

    return content, report


def format_report(report: dict) -> str:
    """
    Format editing report as markdown.

    Args:
        report: Editing report dict

    Returns:
        Formatted markdown report
    """
    lines = []
    lines.append("# EDITOR REPORT")
    lines.append("")

    # Confidence score
    score = report["confidence_score"]
    status = (
        "Ready for human review"
        if score >= 90
        else "Minor concerns"
        if score >= 70
        else "Needs additional editing"
    )
    lines.append(f"## Confidence Score: {score}/100")
    lines.append(f"**Status:** {status}")
    lines.append("")

    # Reading Level
    reading = report["reading_level"]
    stats = reading["stats"]
    lines.append("## Reading Level")
    lines.append(
        f"- Average words/sentence: {stats.get('avg_words_per_sentence', 0):.1f}"
    )
    lines.append(f"- Rhythm score: {stats.get('rhythm_score', 0)}/100")
    lines.append(
        f"- Short sentences (under 10 words): {stats.get('short_pct', 0):.0f}%"
    )
    lines.append(f"- Long sentences (over 18 words): {stats.get('long_pct', 0):.0f}%")
    if reading["issues"]:
        lines.append("")
        lines.append("**Issues:**")
        for issue in reading["issues"]:
            lines.append(f"- {issue}")
    lines.append("")

    # Jargon
    jargon = report["jargon"]
    if jargon:
        lines.append("## Jargon Found")
        lines.append("")
        lines.append("| Term | Suggested Replacement |")
        lines.append("|------|----------------------|")
        for j in jargon:
            lines.append(f"| {j['term']} | {j['suggestion']} |")
        lines.append("")

    # Spam Triggers
    spam = report["spam_triggers"]
    if spam:
        lines.append("## Spam Triggers")
        lines.append("")
        for s in spam:
            replacements = (
                ", ".join(s["replacements"])
                if s["replacements"]
                else s.get("note", "Remove or replace")
            )
            lines.append(
                f"- **{s['trigger']}** (found {s['count']}x) - Replace with: {replacements}"
            )
        lines.append("")

    # Formatting
    formatting = report["formatting"]
    if formatting:
        lines.append("## Formatting Issues")
        lines.append("")
        for issue in formatting:
            lines.append(f"- {issue}")
        lines.append("")

    # Voice
    voice = report["voice"]
    if voice["violations"]:
        lines.append("## Voice Violations")
        lines.append("")
        for v in voice["violations"]:
            lines.append(f"- {v}")
        lines.append("")
    elif voice["valid"]:
        lines.append("## Voice Check: PASSED")
        lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    total_issues = (
        len(reading.get("issues", []))
        + len(jargon)
        + len(spam)
        + len(formatting)
        + len(voice.get("violations", []))
    )
    if total_issues == 0:
        lines.append("No issues found. Content is ready for human review.")
    else:
        lines.append(f"**Total issues found:** {total_issues}")
        lines.append("")
        lines.append("**Priority fixes:**")
        # Voice violations first
        if voice["violations"]:
            lines.append(f"1. Fix voice violations ({len(voice['violations'])} found)")
        # Then spam triggers
        if spam:
            lines.append(f"2. Replace spam triggers ({len(spam)} types found)")
        # Then reading level
        if reading["issues"]:
            lines.append(
                f"3. Improve reading level (avg {stats.get('avg_words_per_sentence', 0):.1f} words/sentence)"
            )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Final editing pass for DTCNews newsletter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        "-f",
        help="Newsletter file to edit",
    )
    parser.add_argument(
        "--content",
        "-c",
        help="Direct content to edit",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for edited content",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only generate report, don't output edited content",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="markdown",
        help="Report format (default: markdown)",
    )
    args = parser.parse_args()

    print(f"[editor_agent] v{DOE_VERSION}")
    print()

    # Get content
    content = args.content

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ERROR: File not found: {args.file}")
            return 1
        content = file_path.read_text()

    if not content:
        print("ERROR: Provide --file or --content")
        return 1

    print(f"Content length: {len(content)} chars")
    print()

    # Run editing pass
    print("Running editing checks...")
    edited_content, report = edit_content(content)

    print()
    print("=" * 60)

    # Output report
    if args.format in ["json", "both"]:
        print("JSON REPORT:")
        print("-" * 40)
        print(json.dumps(report, indent=2))
        print()

    if args.format in ["markdown", "both"]:
        print(format_report(report))
        print()

    # Save output
    if args.output and not args.report_only:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            f.write(edited_content)
        print(f"Saved to: {output_path}")

        # Also save report
        report_path = output_path.with_suffix(".report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {report_path}")

    # Return code based on confidence
    if report["confidence_score"] >= 90:
        print("Content is ready for human review.")
        return 0
    elif report["confidence_score"] >= 70:
        print("Content has minor issues but can proceed to review.")
        return 0
    else:
        print("Content needs additional editing before review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
