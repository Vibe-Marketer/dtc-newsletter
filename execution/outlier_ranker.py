#!/usr/bin/env python3
"""
Outlier ranker for DTCNews newsletter.
DOE-VERSION: 2026.02.04

Finds the BIGGEST trending topics in ecommerce by combining:
- Outlier score (performance vs average)
- Virality analysis (hook type, emotional triggers)
- Recency boost

This replaces naive "beginner keyword" filtering with outlier-first selection.
We find what's actually resonating, THEN assess if beginners can execute it.

Usage:
    python execution/outlier_ranker.py
    python execution/outlier_ranker.py --input output/content_2026-02-04.json --top 20
    python execution/outlier_ranker.py --min-score 3.0 --show-analysis
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.virality_analyzer import analyze_virality

DOE_VERSION = "2026.02.04"

# =============================================================================
# RANKING WEIGHTS
# =============================================================================

# How much each factor contributes to final rank
WEIGHTS = {
    "outlier_score": 0.50,  # Raw performance vs average
    "virality_confidence": 0.20,  # How certain we are it's genuinely viral
    "trigger_intensity": 0.15,  # Strength of emotional hooks
    "recency": 0.15,  # Favor fresh content
}

# Virality confidence to numeric
CONFIDENCE_SCORES = {
    "definite": 1.0,
    "likely": 0.75,
    "possible": 0.5,
    "unclear": 0.25,
}

# Trigger intensity to numeric
INTENSITY_SCORES = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3,
}


def calculate_composite_rank(item: dict) -> tuple[float, dict]:
    """
    Calculate composite ranking score using outlier + virality analysis.

    Args:
        item: Content item with outlier_score and optional virality_analysis

    Returns:
        Tuple of (composite_score, breakdown_dict)
    """
    # Get or calculate virality analysis
    virality = item.get("virality_analysis")
    if not virality:
        virality = analyze_virality(item)
        item["virality_analysis"] = virality

    # Component 1: Outlier score (normalize to 0-10 scale, cap at 10)
    outlier_raw = item.get("outlier_score", item.get("score", 1.0))
    outlier_normalized = min(outlier_raw, 10.0)

    # Component 2: Virality confidence
    confidence_str = virality.get("virality_confidence", "unclear")
    confidence_score = CONFIDENCE_SCORES.get(confidence_str, 0.25) * 10

    # Component 3: Trigger intensity (average of all triggers)
    triggers = virality.get("emotional_triggers", [])
    if triggers:
        intensities = [
            INTENSITY_SCORES.get(t.get("intensity", "low"), 0.3) for t in triggers
        ]
        trigger_score = (sum(intensities) / len(intensities)) * 10
    else:
        trigger_score = 2.5  # Base score if no triggers detected

    # Component 4: Recency (already factored into outlier_score, but we can boost further)
    # Check if item has timestamp
    recency_score = 5.0  # Default neutral
    if "created_utc" in item or "published_at" in item:
        timestamp = item.get("created_utc") or item.get("published_at")
        if isinstance(timestamp, (int, float)):
            age_days = (datetime.now(timezone.utc).timestamp() - timestamp) / 86400
            if age_days <= 1:
                recency_score = 10.0
            elif age_days <= 3:
                recency_score = 8.0
            elif age_days <= 7:
                recency_score = 6.0
            else:
                recency_score = 4.0

    # Calculate weighted composite
    composite = (
        outlier_normalized * WEIGHTS["outlier_score"]
        + confidence_score * WEIGHTS["virality_confidence"]
        + trigger_score * WEIGHTS["trigger_intensity"]
        + recency_score * WEIGHTS["recency"]
    )

    breakdown = {
        "outlier": round(outlier_normalized, 2),
        "confidence": round(confidence_score, 2),
        "triggers": round(trigger_score, 2),
        "recency": round(recency_score, 2),
        "composite": round(composite, 2),
    }

    return composite, breakdown


def extract_core_insight(item: dict) -> dict:
    """
    Extract the core insight/tactic from content, separate from results.

    This helps us see WHAT they did, not just WHAT they achieved.

    Args:
        item: Content item

    Returns:
        Dict with extracted insight components
    """
    title = item.get("title", "")
    summary = item.get("summary", item.get("selftext", ""))

    virality = item.get("virality_analysis", {})
    hook = virality.get("hook_analysis", {})

    return {
        "hook_type": hook.get("hook_type", "unknown"),
        "hook_text": hook.get("hook_text", title[:100]),
        "attention_elements": hook.get("attention_elements", []),
        "emotional_triggers": [
            t["trigger"] for t in virality.get("emotional_triggers", [])
        ],
        "replication_notes": virality.get("replication_notes", ""),
    }


def rank_content(
    content: list[dict],
    min_score: float = 2.0,
    top_n: int | None = None,
) -> list[dict]:
    """
    Rank content by composite outlier + virality score.

    Args:
        content: List of content items
        min_score: Minimum composite score to include
        top_n: Return only top N items (None = all that pass min_score)

    Returns:
        Ranked list of content with scores and insights
    """
    ranked = []

    for item in content:
        composite, breakdown = calculate_composite_rank(item)

        if composite >= min_score:
            ranked_item = {
                **item,
                "composite_rank": composite,
                "rank_breakdown": breakdown,
                "core_insight": extract_core_insight(item),
            }
            ranked.append(ranked_item)

    # Sort by composite rank descending
    ranked.sort(key=lambda x: x["composite_rank"], reverse=True)

    if top_n:
        ranked = ranked[:top_n]

    return ranked


def find_latest_content_file() -> Path | None:
    """Find the most recent content aggregate file."""
    output_dir = Path("output")
    if not output_dir.exists():
        return None

    content_files = list(output_dir.glob("content_*.json"))
    content_files = [
        f
        for f in content_files
        if "filtered" not in f.name and "selected" not in f.name
    ]

    if not content_files:
        return None

    return max(content_files, key=lambda f: f.stat().st_mtime)


def format_insight_summary(item: dict) -> str:
    """Format a single item's insight for display."""
    insight = item.get("core_insight", {})
    breakdown = item.get("rank_breakdown", {})

    lines = []
    lines.append(f"  Composite: {item.get('composite_rank', 0):.1f}")
    lines.append(
        f"  Breakdown: outlier={breakdown.get('outlier', 0):.1f} conf={breakdown.get('confidence', 0):.1f} triggers={breakdown.get('triggers', 0):.1f}"
    )
    lines.append(f"  Hook Type: {insight.get('hook_type', 'unknown')}")

    if insight.get("attention_elements"):
        lines.append(f"  Attention: {', '.join(insight['attention_elements'])}")

    if insight.get("emotional_triggers"):
        lines.append(f"  Triggers: {', '.join(insight['emotional_triggers'])}")

    if insight.get("replication_notes"):
        lines.append(f"  Replicate: {insight['replication_notes']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Rank content by outlier performance + virality analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Input JSON file (default: most recent content_*.json)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=2.0,
        help="Minimum composite score to include (default: 2.0)",
    )
    parser.add_argument(
        "--top",
        "-n",
        type=int,
        default=20,
        help="Return top N items (default: 20)",
    )
    parser.add_argument(
        "--show-analysis",
        action="store_true",
        help="Show detailed virality analysis for each item",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for ranked JSON",
    )
    args = parser.parse_args()

    print(f"[outlier_ranker] v{DOE_VERSION}")
    print()

    # Find input file
    if args.input:
        input_path = Path(args.input)
    else:
        input_path = find_latest_content_file()

    if not input_path or not input_path.exists():
        print("ERROR: No input file found. Run content_aggregate.py first.")
        return 1

    print(f"Input: {input_path}")
    print(f"Min score: {args.min_score}")
    print(f"Top N: {args.top}")
    print()

    # Load content
    with open(input_path) as f:
        data = json.load(f)

    if isinstance(data, list):
        content = data
    elif isinstance(data, dict):
        content = data.get("content", data.get("items", []))
    else:
        print("ERROR: Unexpected JSON structure")
        return 1

    print(f"Loaded {len(content)} items")
    print("Calculating composite ranks...")
    print()

    # Rank content
    ranked = rank_content(content, min_score=args.min_score, top_n=args.top)

    # Display results
    print("=" * 70)
    print(f"TOP {len(ranked)} OUTLIERS (by composite rank)")
    print("=" * 70)
    print()

    for i, item in enumerate(ranked, 1):
        source = item.get("source", item.get("subreddit", "unknown"))
        title = item.get("title", "No title")[:65]

        print(f"{i:2}. [{item['composite_rank']:.1f}] {title}...")
        print(f"    Source: {source} | Outlier: {item.get('outlier_score', 0):.1f}x")

        if args.show_analysis:
            print(format_insight_summary(item))

        print()

    # Save output
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_path = Path("output") / f"content_ranked_{date_str}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "metadata": {
            "ranked_at": datetime.now(timezone.utc).isoformat(),
            "source_file": str(input_path),
            "total_input": len(content),
            "total_ranked": len(ranked),
            "min_score": args.min_score,
            "weights": WEIGHTS,
        },
        "ranked_content": ranked,
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print("-" * 70)
    print(f"Saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
