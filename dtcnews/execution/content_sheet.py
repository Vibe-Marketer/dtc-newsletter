"""
Content sheet generator.
DOE-VERSION: 2026.01.31

Generates CSV and JSON content sheets with full metadata and virality analysis.
Per CONTEXT.md: Both formats generated each run.
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from execution.virality_analyzer import analyze_virality

OUTPUT_DIR = Path("output")

# CSV columns per OUTP-04
CSV_COLUMNS = [
    "source",
    "id",
    "title",
    "url",
    "thumbnail_url",
    "author",
    "published_at",
    "views",
    "engagement_score",  # upvotes for Reddit, views for YouTube
    "outlier_score",
    "hook_type",
    "emotional_triggers",
    "virality_confidence",
    "replication_notes",
]


def generate_content_sheet(
    contents: list[dict], include_virality: bool = True
) -> list[dict]:
    """
    Generate content sheet with virality analysis.

    Args:
        contents: List of content dicts from all sources
        include_virality: Whether to add virality analysis (default True)

    Returns:
        Enriched content list ready for output
    """
    enriched = []

    for content in contents:
        item = content.copy()

        if include_virality:
            virality = analyze_virality(content)
            item["virality_analysis"] = virality

            # Flatten key fields for CSV
            item["hook_type"] = virality.get("hook_analysis", {}).get("hook_type", "")
            triggers = virality.get("emotional_triggers", [])
            item["emotional_triggers"] = ", ".join(t["trigger"] for t in triggers)
            item["virality_confidence"] = virality.get("virality_confidence", "")
            item["replication_notes"] = virality.get("replication_notes", "")

        enriched.append(item)

    return enriched


def save_csv(
    contents: list[dict],
    filename: str = "content_sheet.csv",
    output_dir: Optional[Path] = None,
) -> Path:
    """Save content sheet as CSV."""
    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / filename

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()

        for content in contents:
            # Map fields to CSV columns
            row = {
                "source": content.get("source", ""),
                "id": content.get(
                    "id", content.get("video_id", content.get("post_id", ""))
                ),
                "title": content.get("title", ""),
                "url": content.get("url", ""),
                "thumbnail_url": content.get(
                    "thumbnail_url", content.get("thumbnail", "")
                ),
                "author": content.get("author", content.get("channel_name", "")),
                "published_at": content.get(
                    "published_at", content.get("created_utc", "")
                ),
                "views": content.get("views", content.get("upvotes", 0)),
                "engagement_score": content.get("upvotes", content.get("views", 0)),
                "outlier_score": f"{content.get('outlier_score', 0):.2f}",
                "hook_type": content.get("hook_type", ""),
                "emotional_triggers": content.get("emotional_triggers", ""),
                "virality_confidence": content.get("virality_confidence", ""),
                "replication_notes": content.get("replication_notes", ""),
            }
            writer.writerow(row)

    return filepath


def save_json(
    contents: list[dict],
    filename: str = "content_sheet.json",
    output_dir: Optional[Path] = None,
) -> Path:
    """Save content sheet as JSON with full metadata."""
    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / filename

    output_data = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_items": len(contents),
            "sources": list(set(c.get("source", "unknown") for c in contents)),
        },
        "contents": contents,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return filepath


def generate_and_save(
    contents: list[dict],
    csv_filename: str = "content_sheet.csv",
    json_filename: str = "content_sheet.json",
    output_dir: Optional[Path] = None,
) -> tuple[Path, Path]:
    """Generate content sheet and save both CSV and JSON."""
    enriched = generate_content_sheet(contents)

    csv_path = save_csv(enriched, csv_filename, output_dir)
    json_path = save_json(enriched, json_filename, output_dir)

    return csv_path, json_path


def load_content_sheet(
    filepath: Path,
) -> list[dict]:
    """
    Load content sheet from JSON file.

    Args:
        filepath: Path to JSON content sheet

    Returns:
        List of content dicts

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Content sheet not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("contents", data)


def get_content_sheet_stats(contents: list[dict]) -> dict:
    """
    Get statistics about content sheet.

    Args:
        contents: List of content dicts

    Returns:
        Statistics dict with source counts, score ranges, etc.
    """
    if not contents:
        return {
            "total_items": 0,
            "by_source": {},
            "score_range": {"min": 0, "max": 0},
            "avg_score": 0,
        }

    # Count by source
    by_source = {}
    for c in contents:
        source = c.get("source", "unknown")
        by_source[source] = by_source.get(source, 0) + 1

    # Score statistics
    scores = [c.get("outlier_score", 0) for c in contents]

    return {
        "total_items": len(contents),
        "by_source": by_source,
        "score_range": {
            "min": min(scores),
            "max": max(scores),
        },
        "avg_score": sum(scores) / len(scores) if scores else 0,
    }
