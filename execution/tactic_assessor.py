#!/usr/bin/env python3
"""
Tactic assessor for DTCNews newsletter.
DOE-VERSION: 2026.02.04

Evaluates whether the UNDERLYING TACTIC in viral content can be executed
by a beginner (0-10 sales), regardless of how the content is written.

Key insight: A post about "$500K revenue" might contain a tactic that requires
only $0 and 30 minutes. We assess the TACTIC, not the LANGUAGE.

Usage:
    python execution/tactic_assessor.py --input output/content_ranked_2026-02-04.json
    python execution/tactic_assessor.py --content "Post title and content here"
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

# Add parent directory to path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.claude_client import ClaudeClient

DOE_VERSION = "2026.02.04"

# =============================================================================
# ASSESSMENT CRITERIA
# =============================================================================

# What makes a tactic beginner-executable?
BEGINNER_REQUIREMENTS = {
    "budget": {
        "max_dollars": 100,
        "description": "Can be done with $100 or less (ideally $0)",
    },
    "traffic": {
        "requires_existing": False,
        "description": "Doesn't require existing website traffic",
    },
    "customers": {
        "requires_existing": False,
        "description": "Doesn't require existing customer base or email list",
    },
    "time": {
        "max_hours_to_start": 4,
        "description": "Can start seeing results within 4 hours of work",
    },
    "technical": {
        "max_skill_level": "basic",  # basic, intermediate, advanced
        "description": "No coding, API work, or technical setup beyond clicking",
    },
    "team": {
        "requires_team": False,
        "description": "Can be done solo, no VAs or employees needed",
    },
}

# =============================================================================
# ASSESSMENT SYSTEM PROMPT
# =============================================================================

ASSESSOR_SYSTEM_PROMPT = """You are an expert at extracting actionable tactics from content and assessing whether beginners can execute them.

Your job is to:
1. Extract the CORE TACTIC from content (what did they actually DO?)
2. Separate the tactic from the results (ignore revenue numbers, focus on actions)
3. Assess if a complete beginner (0-10 sales, $0-100 budget, no existing traffic) can do this

BEGINNER REQUIREMENTS:
- Budget: $100 or less to start (ideally $0)
- Traffic: Doesn't require existing website visitors
- Customers: Doesn't require existing email list or customer base
- Time: Can start within 4 hours of work
- Technical: No coding, APIs, or complex integrations
- Team: Can be done solo

OUTPUT FORMAT (return as JSON):
{
  "extracted_tactic": {
    "what_they_did": "One sentence describing the core action",
    "why_it_worked": "One sentence on the mechanism",
    "time_investment": "Estimated hours to implement",
    "tools_needed": ["list", "of", "tools"],
    "cost_to_start": "$X or free"
  },
  "beginner_assessment": {
    "is_executable": true/false,
    "budget_ok": true/false,
    "budget_note": "...",
    "traffic_ok": true/false,
    "traffic_note": "...",
    "customers_ok": true/false,
    "customers_note": "...",
    "time_ok": true/false,
    "time_note": "...",
    "technical_ok": true/false,
    "technical_note": "...",
    "team_ok": true/false,
    "team_note": "...",
    "overall_score": 0-6,
    "blocking_issues": ["list of things that make this NOT beginner-executable"]
  },
  "beginner_adaptation": {
    "needed": true/false,
    "original_requires": "What the original assumed",
    "adapted_version": "How a beginner could do a simpler version",
    "what_to_skip": "Parts to ignore for now",
    "what_to_focus_on": "The core that still works at small scale"
  },
  "action_steps": [
    "Step 1: Do this specific thing",
    "Step 2: Then do this",
    "Step 3: etc"
  ]
}

IMPORTANT:
- A $1M case study might contain a $0 tactic - extract it
- Focus on the MECHANISM, not the scale
- If adaptation is needed, provide it
- Action steps should be specific enough to execute TODAY"""


def assess_tactic(content: dict | str, client: ClaudeClient | None = None) -> dict:
    """
    Assess whether a tactic is beginner-executable.

    Args:
        content: Content dict with title/summary OR string of content
        client: ClaudeClient instance

    Returns:
        Assessment dict with tactic extraction and beginner evaluation
    """
    if client is None:
        client = ClaudeClient()

    # Build content string
    if isinstance(content, dict):
        title = content.get("title", "")
        summary = content.get(
            "summary", content.get("selftext", content.get("description", ""))
        )
        source = content.get("source", "unknown")
        content_str = f"Title: {title}\n\nContent: {summary}\n\nSource: {source}"
    else:
        content_str = content

    user_prompt = f"""Analyze this content and extract the core tactic. Then assess if a beginner can execute it.

CONTENT:
{content_str}

Remember:
- Extract WHAT THEY DID, not what they achieved
- Assess against beginner requirements (no traffic, no customers, <$100, <4 hours)
- If not beginner-ready, provide an adapted version that IS
- Give specific action steps

Return your analysis as valid JSON."""

    response = client.generate(
        prompt=user_prompt,
        system_prompt=ASSESSOR_SYSTEM_PROMPT,
        max_tokens=2000,
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


def batch_assess(
    content_list: list[dict],
    client: ClaudeClient | None = None,
    min_score: int = 4,
) -> tuple[list[dict], list[dict]]:
    """
    Assess multiple content items and separate into executable/not-executable.

    Args:
        content_list: List of content dicts
        client: ClaudeClient instance
        min_score: Minimum beginner score (0-6) to pass

    Returns:
        Tuple of (executable_list, needs_adaptation_list)
    """
    if client is None:
        client = ClaudeClient()

    executable = []
    needs_adaptation = []

    for item in content_list:
        print(f"  Assessing: {item.get('title', 'Unknown')[:50]}...")

        assessment = assess_tactic(item, client)

        # Add assessment to item
        assessed_item = {
            **item,
            "tactic_assessment": assessment,
        }

        # Check if executable
        beginner = assessment.get("beginner_assessment", {})
        score = beginner.get("overall_score", 0)
        is_exec = beginner.get("is_executable", False)

        if is_exec and score >= min_score:
            executable.append(assessed_item)
        else:
            needs_adaptation.append(assessed_item)

    return executable, needs_adaptation


def format_assessment_report(assessment: dict) -> str:
    """Format assessment as readable report."""
    lines = []

    # Extracted tactic
    tactic = assessment.get("extracted_tactic", {})
    lines.append("## EXTRACTED TACTIC")
    lines.append(f"**What they did:** {tactic.get('what_they_did', 'Unknown')}")
    lines.append(f"**Why it worked:** {tactic.get('why_it_worked', 'Unknown')}")
    lines.append(f"**Time to implement:** {tactic.get('time_investment', 'Unknown')}")
    lines.append(f"**Cost to start:** {tactic.get('cost_to_start', 'Unknown')}")
    if tactic.get("tools_needed"):
        lines.append(f"**Tools:** {', '.join(tactic['tools_needed'])}")
    lines.append("")

    # Beginner assessment
    beginner = assessment.get("beginner_assessment", {})
    lines.append("## BEGINNER ASSESSMENT")
    lines.append(
        f"**Executable by beginner:** {'YES' if beginner.get('is_executable') else 'NO'}"
    )
    lines.append(f"**Overall score:** {beginner.get('overall_score', 0)}/6")
    lines.append("")

    checks = [
        ("Budget", "budget_ok", "budget_note"),
        ("Traffic", "traffic_ok", "traffic_note"),
        ("Customers", "customers_ok", "customers_note"),
        ("Time", "time_ok", "time_note"),
        ("Technical", "technical_ok", "technical_note"),
        ("Team", "team_ok", "team_note"),
    ]

    for label, ok_key, note_key in checks:
        status = "PASS" if beginner.get(ok_key) else "FAIL"
        note = beginner.get(note_key, "")
        lines.append(f"- {label}: {status} - {note}")

    if beginner.get("blocking_issues"):
        lines.append("")
        lines.append("**Blocking issues:**")
        for issue in beginner["blocking_issues"]:
            lines.append(f"  - {issue}")
    lines.append("")

    # Adaptation
    adapt = assessment.get("beginner_adaptation", {})
    if adapt.get("needed"):
        lines.append("## BEGINNER ADAPTATION")
        lines.append(f"**Original requires:** {adapt.get('original_requires', '')}")
        lines.append(f"**Adapted version:** {adapt.get('adapted_version', '')}")
        lines.append(f"**Skip for now:** {adapt.get('what_to_skip', '')}")
        lines.append(f"**Focus on:** {adapt.get('what_to_focus_on', '')}")
        lines.append("")

    # Action steps
    steps = assessment.get("action_steps", [])
    if steps:
        lines.append("## ACTION STEPS")
        for i, step in enumerate(steps, 1):
            lines.append(f"{i}. {step}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Assess whether tactics are beginner-executable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Input JSON file with ranked content",
    )
    parser.add_argument(
        "--content",
        "-c",
        help="Direct content to assess",
    )
    parser.add_argument(
        "--top",
        "-n",
        type=int,
        default=10,
        help="Assess top N items from input (default: 10)",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=4,
        help="Minimum beginner score to pass (default: 4 out of 6)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for assessed content",
    )
    args = parser.parse_args()

    print(f"[tactic_assessor] v{DOE_VERSION}")
    print()

    # Initialize client
    try:
        client = ClaudeClient()
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Single content assessment
    if args.content:
        print("Assessing single content...")
        assessment = assess_tactic(args.content, client)
        print()
        print("=" * 60)
        print(format_assessment_report(assessment))
        return 0

    # Batch assessment from file
    if not args.input:
        # Find most recent ranked file
        output_dir = Path("output")
        ranked_files = list(output_dir.glob("content_ranked_*.json"))
        if not ranked_files:
            print(
                "ERROR: No input file. Run outlier_ranker.py first or specify --input"
            )
            return 1
        args.input = str(max(ranked_files, key=lambda f: f.stat().st_mtime))

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: File not found: {args.input}")
        return 1

    print(f"Input: {input_path}")
    print(f"Assessing top {args.top} items...")
    print()

    # Load content
    with open(input_path) as f:
        data = json.load(f)

    content = data.get("ranked_content", data.get("content", data))
    if isinstance(content, dict):
        content = [content]

    content = content[: args.top]

    # Assess
    executable, needs_adaptation = batch_assess(content, client, args.min_score)

    # Results
    print()
    print("=" * 60)
    print("ASSESSMENT RESULTS")
    print("=" * 60)
    print(f"Total assessed: {len(content)}")
    print(f"Beginner-executable: {len(executable)}")
    print(f"Needs adaptation: {len(needs_adaptation)}")
    print()

    if executable:
        print("EXECUTABLE BY BEGINNERS:")
        for item in executable:
            title = item.get("title", "Unknown")[:50]
            score = (
                item.get("tactic_assessment", {})
                .get("beginner_assessment", {})
                .get("overall_score", 0)
            )
            print(f"  [{score}/6] {title}...")
        print()

    if needs_adaptation:
        print("NEEDS ADAPTATION:")
        for item in needs_adaptation:
            title = item.get("title", "Unknown")[:50]
            blocking = (
                item.get("tactic_assessment", {})
                .get("beginner_assessment", {})
                .get("blocking_issues", [])
            )
            print(f"  - {title}...")
            if blocking:
                print(f"    Issues: {', '.join(blocking[:2])}")
        print()

    # Save output
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_path = Path("output") / f"content_assessed_{date_str}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "metadata": {
            "assessed_at": datetime.now(timezone.utc).isoformat(),
            "source_file": str(input_path),
            "total_assessed": len(content),
            "executable_count": len(executable),
            "adaptation_count": len(needs_adaptation),
            "min_score": args.min_score,
        },
        "executable": executable,
        "needs_adaptation": needs_adaptation,
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
