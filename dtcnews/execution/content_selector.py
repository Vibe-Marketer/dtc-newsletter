"""
Content selector for DTC Money Minute newsletter.
DOE-VERSION: 2026.01.31

Selects best content for each newsletter section based on outlier score,
content type matching, and source diversity.

Provides:
- ContentSelection dataclass for structured selection results
- select_content_for_sections() to pick best content for each section
- Helper functions for content type detection
"""

from dataclasses import dataclass, field


@dataclass
class ContentSelection:
    """
    Content selections for each newsletter section.

    Attributes:
        section_1: Best quotable content for Instant Reward
        section_2: Best tactical content for What's Working Now
        section_3: Best narrative content for The Breakdown
        section_4_tool: Tool recommendation (manual input for now)
        sources_used: List of unique sources used
    """

    section_1: dict | None = None
    section_2: dict | None = None
    section_3: dict | None = None
    section_4_tool: str | None = None
    sources_used: list[str] = field(default_factory=list)


def _is_quotable(item: dict) -> bool:
    """
    Check if content is quote-worthy for Section 1.

    Quotable content:
    - Short title (under 100 chars) that's punchy
    - Contains stats/numbers ($, %, or digits)
    - Has viral quote potential

    Args:
        item: Content dict with title, summary, etc.

    Returns:
        True if content is quotable
    """
    title = item.get("title", "")
    summary = item.get("summary", "")

    # Short, punchy titles are quotable
    if len(title) < 100:
        # Check for numbers/stats (strong quote material)
        combined = f"{title} {summary}".lower()
        has_numbers = any(
            char.isdigit() or char == "$" or char == "%" for char in combined
        )
        if has_numbers:
            return True

        # Check for quote indicators
        quote_indicators = ['"', "'", "said", "quote", "viral", "trending"]
        if any(indicator in combined for indicator in quote_indicators):
            return True

    # Very short titles are often punchy observations
    if len(title) < 50:
        return True

    return False


def _is_tactical(item: dict) -> bool:
    """
    Check if content is tactical/actionable for Section 2.

    Tactical content contains how-to, strategy, or step-by-step guidance.

    Args:
        item: Content dict with title, summary, etc.

    Returns:
        True if content is tactical
    """
    title = item.get("title", "").lower()
    summary = item.get("summary", "").lower()
    combined = f"{title} {summary}"

    # Keywords that indicate tactical content
    tactical_keywords = [
        "how to",
        "how i",
        "step",
        "strategy",
        "strategies",
        "tactic",
        "tactics",
        "tip",
        "tips",
        "hack",
        "hacks",
        "guide",
        "tutorial",
        "method",
        "framework",
        "system",
        "process",
        "template",
        "checklist",
        "workflow",
        "technique",
        "approach",
        "formula",
        "blueprint",
        "playbook",
        "secret",
        "trick",
        "way to",
        "ways to",
        "what worked",
        "what works",
        "increased",
        "boosted",
        "doubled",
        "tripled",
    ]

    return any(keyword in combined for keyword in tactical_keywords)


def _has_narrative_potential(item: dict) -> bool:
    """
    Check if content has story/narrative potential for Section 3.

    Narrative content can be turned into a compelling story or case study.

    Args:
        item: Content dict with title, summary, etc.

    Returns:
        True if content has narrative potential
    """
    title = item.get("title", "").lower()
    summary = item.get("summary", "").lower()
    combined = f"{title} {summary}"

    # Keywords that indicate narrative potential
    narrative_keywords = [
        "case study",
        "story",
        "journey",
        "learned",
        "lessons",
        "mistake",
        "mistakes",
        "failed",
        "failure",
        "success",
        "went from",
        "before and after",
        "transformation",
        "turned around",
        "comeback",
        "pivot",
        "pivoted",
        "started",
        "built",
        "grew",
        "scaled",
        "year later",
        "months later",
        "my experience",
        "what happened",
        "behind the scenes",
        "inside",
        "revealed",
        "breakdown",
        "analysis",
        "deep dive",
        "examined",
        "why",
        "surprising",
    ]

    return any(keyword in combined for keyword in narrative_keywords)


def _get_unique_sources(selection: ContentSelection) -> int:
    """
    Count distinct sources in the selection.

    Args:
        selection: ContentSelection with section content

    Returns:
        Number of unique sources used
    """
    sources = set()

    if selection.section_1 and selection.section_1.get("source"):
        sources.add(selection.section_1["source"])
    if selection.section_2 and selection.section_2.get("source"):
        sources.add(selection.section_2["source"])
    if selection.section_3 and selection.section_3.get("source"):
        sources.add(selection.section_3["source"])

    return len(sources)


def select_content_for_sections(aggregated: list[dict]) -> ContentSelection:
    """
    Select best content for each newsletter section.

    Selection priority:
    1. Sort by outlier_score descending (best content first)
    2. Apply diversity constraint: require at least 2 different sources
    3. Match content type to section requirements

    Args:
        aggregated: List of content dicts with outlier_score, title, source, etc.

    Returns:
        ContentSelection with best content for each section
    """
    # Handle empty input
    if not aggregated:
        return ContentSelection(
            section_1=None,
            section_2=None,
            section_3=None,
            section_4_tool=None,
            sources_used=[],
        )

    # Sort by outlier score descending
    sorted_content = sorted(
        aggregated, key=lambda x: x.get("outlier_score", 0), reverse=True
    )

    selection = ContentSelection()
    used_ids = set()  # Track used content to avoid exact duplicates

    # Section 2: Tactical content (THE MEAT - most important)
    # Find first tactical content that's not already used
    for item in sorted_content:
        item_id = item.get("id") or item.get("url") or item.get("title")
        if item_id in used_ids:
            continue
        if _is_tactical(item):
            selection.section_2 = item
            used_ids.add(item_id)
            break

    # If no tactical content found, use highest outlier score item
    if selection.section_2 is None and sorted_content:
        for item in sorted_content:
            item_id = item.get("id") or item.get("url") or item.get("title")
            if item_id not in used_ids:
                selection.section_2 = item
                used_ids.add(item_id)
                break

    # Section 3: Narrative content
    # Try to use different source than section 2 (diversity)
    section_2_source = (
        selection.section_2.get("source") if selection.section_2 else None
    )

    # First pass: narrative content from different source
    for item in sorted_content:
        item_id = item.get("id") or item.get("url") or item.get("title")
        if item_id in used_ids:
            continue
        if _has_narrative_potential(item):
            # Prefer different source for diversity
            if item.get("source") != section_2_source:
                selection.section_3 = item
                used_ids.add(item_id)
                break

    # Second pass: narrative content from any source (if no diverse option)
    if selection.section_3 is None:
        for item in sorted_content:
            item_id = item.get("id") or item.get("url") or item.get("title")
            if item_id in used_ids:
                continue
            if _has_narrative_potential(item):
                selection.section_3 = item
                used_ids.add(item_id)
                break

    # Third pass: if no narrative content, reuse tactical with different angle flag
    if selection.section_3 is None and sorted_content:
        for item in sorted_content:
            item_id = item.get("id") or item.get("url") or item.get("title")
            if item_id not in used_ids:
                # Add flag to indicate this needs different angle treatment
                item_copy = item.copy()
                item_copy["_different_angle_needed"] = True
                selection.section_3 = item_copy
                used_ids.add(item_id)
                break

    # Section 1: Quotable content (can be from any source)
    for item in sorted_content:
        item_id = item.get("id") or item.get("url") or item.get("title")
        # Section 1 can reuse content from other sections if transformed
        if _is_quotable(item):
            selection.section_1 = item
            # Don't add to used_ids - section 1 is just a quote/hook
            break

    # If no quotable content, use highest outlier score
    if selection.section_1 is None and sorted_content:
        selection.section_1 = sorted_content[0]

    # Build sources_used list
    sources = set()
    if selection.section_1 and selection.section_1.get("source"):
        sources.add(selection.section_1["source"])
    if selection.section_2 and selection.section_2.get("source"):
        sources.add(selection.section_2["source"])
    if selection.section_3 and selection.section_3.get("source"):
        sources.add(selection.section_3["source"])
    selection.sources_used = list(sources)

    # Verify diversity constraint (at least 2 sources when possible)
    unique_sources = _get_unique_sources(selection)
    if unique_sources < 2 and len(sorted_content) > 1:
        # Try to swap section_3 for better diversity
        section_2_source = (
            selection.section_2.get("source") if selection.section_2 else None
        )
        for item in sorted_content:
            item_id = item.get("id") or item.get("url") or item.get("title")
            item_source = item.get("source")
            # Find content from different source
            if item_source and item_source != section_2_source:
                # Check if we can use this for section 3
                current_s3_id = None
                if selection.section_3:
                    current_s3_id = (
                        selection.section_3.get("id")
                        or selection.section_3.get("url")
                        or selection.section_3.get("title")
                    )
                if item_id != current_s3_id and item_id not in used_ids:
                    selection.section_3 = item
                    # Rebuild sources_used
                    sources = set()
                    if selection.section_1 and selection.section_1.get("source"):
                        sources.add(selection.section_1["source"])
                    if selection.section_2 and selection.section_2.get("source"):
                        sources.add(selection.section_2["source"])
                    if selection.section_3 and selection.section_3.get("source"):
                        sources.add(selection.section_3["source"])
                    selection.sources_used = list(sources)
                    break

    return selection


def get_selection_summary(selection: ContentSelection) -> str:
    """
    Get a human-readable summary of the content selection.

    Args:
        selection: ContentSelection to summarize

    Returns:
        Formatted string summary
    """
    lines = ["Content Selection Summary", "=" * 30]

    if selection.section_1:
        score = selection.section_1.get("outlier_score", 0)
        title = selection.section_1.get("title", "N/A")[:50]
        source = selection.section_1.get("source", "unknown")
        lines.append(f"\nSection 1 (Instant Reward): {score:.1f}x - {source}")
        lines.append(f"  {title}...")

    if selection.section_2:
        score = selection.section_2.get("outlier_score", 0)
        title = selection.section_2.get("title", "N/A")[:50]
        source = selection.section_2.get("source", "unknown")
        lines.append(f"\nSection 2 (What's Working): {score:.1f}x - {source}")
        lines.append(f"  {title}...")

    if selection.section_3:
        score = selection.section_3.get("outlier_score", 0)
        title = selection.section_3.get("title", "N/A")[:50]
        source = selection.section_3.get("source", "unknown")
        angle_flag = (
            " [DIFFERENT ANGLE NEEDED]"
            if selection.section_3.get("_different_angle_needed")
            else ""
        )
        lines.append(
            f"\nSection 3 (The Breakdown): {score:.1f}x - {source}{angle_flag}"
        )
        lines.append(f"  {title}...")

    lines.append(f"\nSources used: {', '.join(selection.sources_used)}")
    lines.append(f"Diversity: {len(selection.sources_used)} unique sources")

    return "\n".join(lines)


# =============================================================================
# CLI INTERFACE
# =============================================================================


def main():
    """CLI entry point for content selection."""
    import argparse
    import json
    import sys
    from datetime import datetime, timezone
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="Select content for newsletter sections",
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Input JSON file with ranked content",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file for selected content",
    )
    args = parser.parse_args()

    # Find input file
    if args.input:
        input_path = Path(args.input)
    else:
        # Find most recent ranked file
        output_dir = Path("output")
        ranked_files = list(output_dir.glob("content_ranked_*.json"))
        if not ranked_files:
            print("ERROR: No ranked content files found. Run outlier_ranker.py first.")
            return 1
        input_path = max(ranked_files, key=lambda f: f.stat().st_mtime)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        return 1

    print(f"[content_selector]")
    print(f"Input: {input_path}")

    # Load content
    with open(input_path) as f:
        data = json.load(f)

    content = data.get("ranked_content", data.get("content", []))
    if not content:
        print("ERROR: No content found in file")
        return 1

    print(f"Loaded {len(content)} items")

    # Select content
    selection = select_content_for_sections(content)

    # Print summary
    print()
    print(get_selection_summary(selection))

    # Prepare output
    output_data = {
        "metadata": {
            "selected_at": datetime.now(timezone.utc).isoformat(),
            "source_file": str(input_path),
            "total_input": len(content),
        },
        "selection": {
            "section_1": selection.section_1,
            "section_2": selection.section_2,
            "section_3": selection.section_3,
            "section_4_tool": selection.section_4_tool,
            "sources_used": selection.sources_used,
        },
        # Also include content list for newsletter generator
        "contents": content,
    }

    # Save output
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_path = Path("output") / f"content_selected_{date_str}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nSaved to: {output_path}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
