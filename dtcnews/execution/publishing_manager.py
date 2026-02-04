#!/usr/bin/env python3
"""
Publishing manager for DTCNews newsletters.
DOE-VERSION: 2026.02.04

Handles the draft → review → publish workflow:
- Saves generated newsletters to /publishing/drafts/
- Tracks status, dates, and sources
- Moves to /publishing/published/ on approval

Usage:
    # Save a new draft
    from execution.publishing_manager import save_draft, PublishingMetadata

    meta = PublishingMetadata(
        issue_number=5,
        status="draft",
        sources=[{"url": "...", "title": "..."}]
    )
    save_draft(newsletter_md, meta)

    # List drafts
    python execution/publishing_manager.py --list-drafts

    # Approve and publish
    python execution/publishing_manager.py --approve issue-5

    # View status
    python execution/publishing_manager.py --status issue-5
"""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

DOE_VERSION = "2026.02.04"

# Paths
PUBLISHING_DIR = Path(__file__).parent.parent / "publishing"
DRAFTS_DIR = PUBLISHING_DIR / "drafts"
PUBLISHED_DIR = PUBLISHING_DIR / "published"


class Status(str, Enum):
    """Newsletter status."""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


@dataclass
class Source:
    """A source used in the newsletter for fact-checking."""

    url: str
    title: str
    accessed_at: str  # ISO timestamp
    content_type: str = "article"  # article, reddit, youtube, twitter
    quote: Optional[str] = None  # Specific claim from this source


@dataclass
class PublishingMetadata:
    """Metadata for a newsletter in the publishing workflow."""

    issue_number: int
    status: str = Status.DRAFT.value

    # Dates
    draft_created: Optional[str] = None
    last_modified: Optional[str] = None
    tentative_publish_date: Optional[str] = None
    published_date: Optional[str] = None

    # Content info
    subject_line: Optional[str] = None
    preview_text: Optional[str] = None
    viral_edge_title: Optional[str] = None
    tactic: Optional[str] = None

    # Sources for fact-checking
    sources: list[dict] = field(default_factory=list)

    # Review notes
    review_notes: list[str] = field(default_factory=list)
    reviewer: Optional[str] = None

    # Sponsor info
    sponsor_name: Optional[str] = None
    sponsor_angle: Optional[str] = None

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.draft_created:
            self.draft_created = now
        if not self.last_modified:
            self.last_modified = now


def get_draft_filename(issue_number: int) -> str:
    """Get filename for a draft."""
    return f"issue-{issue_number}"


def save_draft(
    newsletter_md: str,
    metadata: PublishingMetadata,
    sources: Optional[list[Source]] = None,
) -> Path:
    """
    Save a newsletter as a draft.

    Args:
        newsletter_md: The full newsletter markdown content
        metadata: Publishing metadata
        sources: List of sources used (for fact-checking)

    Returns:
        Path to saved draft
    """
    # Ensure directories exist
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    # Update sources in metadata
    if sources:
        metadata.sources = [asdict(s) if isinstance(s, Source) else s for s in sources]

    # Update timestamp
    metadata.last_modified = datetime.now(timezone.utc).isoformat()

    # Generate filename
    filename = get_draft_filename(metadata.issue_number)

    # Add sources section to newsletter
    newsletter_with_sources = add_sources_section(newsletter_md, metadata.sources)

    # Save markdown
    md_path = DRAFTS_DIR / f"{filename}.md"
    md_path.write_text(newsletter_with_sources)

    # Save metadata
    meta_path = DRAFTS_DIR / f"{filename}.meta.json"
    meta_path.write_text(json.dumps(asdict(metadata), indent=2))

    return md_path


def add_sources_section(newsletter_md: str, sources: list[dict]) -> str:
    """
    Add a sources section to the bottom of the newsletter for fact-checking.

    Args:
        newsletter_md: The newsletter content
        sources: List of source dicts

    Returns:
        Newsletter with sources section appended
    """
    if not sources:
        return newsletter_md

    lines = [
        "\n---\n",
        "## Sources (For Fact-Checking)\n",
        "*This section is removed before publishing.*\n",
    ]

    for i, source in enumerate(sources, 1):
        url = source.get("url", "")
        title = source.get("title", "Unknown")
        content_type = source.get("content_type", "article")
        accessed = source.get("accessed_at", "")
        quote = source.get("quote", "")

        lines.append(f"\n**[{i}] {title}**")
        lines.append(f"- URL: {url}")
        lines.append(f"- Type: {content_type}")
        if accessed:
            lines.append(f"- Accessed: {accessed}")
        if quote:
            lines.append(f'- Key claim: "{quote}"')

    return newsletter_md + "\n".join(lines)


def remove_sources_section(newsletter_md: str) -> str:
    """Remove the sources section before publishing."""
    marker = "## Sources (For Fact-Checking)"
    if marker in newsletter_md:
        return newsletter_md.split(marker)[0].rstrip() + "\n"
    return newsletter_md


def load_draft(issue_number: int) -> tuple[str, PublishingMetadata]:
    """
    Load a draft by issue number.

    Returns:
        Tuple of (newsletter_md, metadata)
    """
    filename = get_draft_filename(issue_number)

    md_path = DRAFTS_DIR / f"{filename}.md"
    meta_path = DRAFTS_DIR / f"{filename}.meta.json"

    if not md_path.exists():
        raise FileNotFoundError(f"Draft not found: {md_path}")

    newsletter_md = md_path.read_text()

    if meta_path.exists():
        meta_dict = json.loads(meta_path.read_text())
        metadata = PublishingMetadata(**meta_dict)
    else:
        metadata = PublishingMetadata(issue_number=issue_number)

    return newsletter_md, metadata


def update_status(
    issue_number: int, new_status: Status, note: Optional[str] = None
) -> PublishingMetadata:
    """
    Update the status of a draft.

    Args:
        issue_number: Issue number
        new_status: New status
        note: Optional review note

    Returns:
        Updated metadata
    """
    _, metadata = load_draft(issue_number)

    metadata.status = new_status.value
    metadata.last_modified = datetime.now(timezone.utc).isoformat()

    if note:
        metadata.review_notes.append(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}"
        )

    # Save updated metadata
    filename = get_draft_filename(issue_number)
    meta_path = DRAFTS_DIR / f"{filename}.meta.json"
    meta_path.write_text(json.dumps(asdict(metadata), indent=2))

    return metadata


def approve_and_publish(issue_number: int, publish_date: Optional[str] = None) -> Path:
    """
    Approve a draft and move to published.

    Args:
        issue_number: Issue number
        publish_date: Optional publish date (defaults to now)

    Returns:
        Path to published file
    """
    newsletter_md, metadata = load_draft(issue_number)

    # Update metadata
    metadata.status = Status.PUBLISHED.value
    metadata.published_date = publish_date or datetime.now(timezone.utc).isoformat()
    metadata.last_modified = datetime.now(timezone.utc).isoformat()

    # Remove sources section for final version
    clean_newsletter = remove_sources_section(newsletter_md)

    # Ensure published directory exists
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)

    # Generate published filename with date
    pub_date = metadata.published_date[:10]  # YYYY-MM-DD
    pub_filename = f"{pub_date}-issue-{issue_number}"

    # Save to published
    pub_md_path = PUBLISHED_DIR / f"{pub_filename}.md"
    pub_md_path.write_text(clean_newsletter)

    pub_meta_path = PUBLISHED_DIR / f"{pub_filename}.meta.json"
    pub_meta_path.write_text(json.dumps(asdict(metadata), indent=2))

    # Optionally move draft to archive (or delete)
    # For now, we leave drafts in place for reference

    return pub_md_path


def list_drafts() -> list[dict]:
    """List all drafts with their status."""
    drafts = []

    if not DRAFTS_DIR.exists():
        return drafts

    for meta_file in DRAFTS_DIR.glob("*.meta.json"):
        meta = json.loads(meta_file.read_text())
        drafts.append(
            {
                "issue": meta.get("issue_number"),
                "status": meta.get("status"),
                "subject": meta.get("subject_line", "")[:50],
                "created": meta.get("draft_created", "")[:10],
                "modified": meta.get("last_modified", "")[:10],
                "tentative": meta.get("tentative_publish_date", ""),
            }
        )

    return sorted(drafts, key=lambda x: x.get("issue", 0))


def list_published() -> list[dict]:
    """List all published newsletters."""
    published = []

    if not PUBLISHED_DIR.exists():
        return published

    for meta_file in PUBLISHED_DIR.glob("*.meta.json"):
        meta = json.loads(meta_file.read_text())
        published.append(
            {
                "issue": meta.get("issue_number"),
                "subject": meta.get("subject_line", "")[:50],
                "published": meta.get("published_date", "")[:10],
            }
        )

    return sorted(published, key=lambda x: x.get("issue", 0))


def main():
    parser = argparse.ArgumentParser(
        description="Manage newsletter publishing workflow"
    )
    parser.add_argument("--list-drafts", action="store_true", help="List all drafts")
    parser.add_argument(
        "--list-published", action="store_true", help="List published newsletters"
    )
    parser.add_argument("--status", type=int, help="Show status of issue N")
    parser.add_argument("--approve", type=int, help="Approve and publish issue N")
    parser.add_argument("--set-status", type=int, help="Set status of issue N")
    parser.add_argument(
        "--new-status",
        choices=["draft", "review", "approved", "rejected"],
        help="New status",
    )
    parser.add_argument("--note", help="Add a review note")
    parser.add_argument(
        "--set-tentative", help="Set tentative publish date (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    print(f"[publishing_manager] v{DOE_VERSION}")

    if args.list_drafts:
        drafts = list_drafts()
        if not drafts:
            print("\nNo drafts found.")
            return

        print("\n## Drafts\n")
        print(
            f"{'Issue':<8} {'Status':<10} {'Created':<12} {'Modified':<12} {'Subject'}"
        )
        print("-" * 80)
        for d in drafts:
            print(
                f"{d['issue']:<8} {d['status']:<10} {d['created']:<12} {d['modified']:<12} {d['subject']}"
            )

    elif args.list_published:
        published = list_published()
        if not published:
            print("\nNo published newsletters found.")
            return

        print("\n## Published\n")
        print(f"{'Issue':<8} {'Published':<12} {'Subject'}")
        print("-" * 60)
        for p in published:
            print(f"{p['issue']:<8} {p['published']:<12} {p['subject']}")

    elif args.status:
        try:
            _, meta = load_draft(args.status)
            print(f"\n## Issue #{args.status}\n")
            print(f"Status: {meta.status}")
            print(f"Subject: {meta.subject_line or 'Not set'}")
            print(f"Draft created: {meta.draft_created}")
            print(f"Last modified: {meta.last_modified}")
            print(f"Tentative publish: {meta.tentative_publish_date or 'Not set'}")
            print(f"Sources: {len(meta.sources)}")
            if meta.review_notes:
                print(f"\nReview Notes:")
                for note in meta.review_notes:
                    print(f"  - {note}")
        except FileNotFoundError:
            print(f"Draft for issue #{args.status} not found.")

    elif args.approve:
        try:
            path = approve_and_publish(args.approve)
            print(f"\nIssue #{args.approve} approved and published!")
            print(f"Saved to: {path}")
        except FileNotFoundError:
            print(f"Draft for issue #{args.approve} not found.")

    elif args.set_status and args.new_status:
        try:
            status_map = {
                "draft": Status.DRAFT,
                "review": Status.REVIEW,
                "approved": Status.APPROVED,
                "rejected": Status.REJECTED,
            }
            meta = update_status(
                args.set_status, status_map[args.new_status], args.note
            )
            print(f"\nIssue #{args.set_status} status updated to: {meta.status}")
        except FileNotFoundError:
            print(f"Draft for issue #{args.set_status} not found.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
