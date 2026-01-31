#!/usr/bin/env python3
"""
Output manager for DTC Newsletter pipeline.
DOE-VERSION: 2026.01.31

Manages newsletter output organization:
- Auto-incrementing issue numbers
- Monthly subfolder organization
- index.json manifest tracking
- macOS desktop notifications

Functions:
- save_newsletter: Save newsletter with organized naming
- get_next_issue_number: Find highest existing issue + 1
- notify: Send macOS desktop notification
- notify_pipeline_complete: Notify on pipeline completion
"""

import json
import logging
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from execution.newsletter_generator import NewsletterOutput
    from execution.pipeline_runner import PipelineResult

# Set up logging
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

NEWSLETTERS_DIR = Path("output/newsletters")
INDEX_PATH = NEWSLETTERS_DIR / "index.json"


# =============================================================================
# SLUG GENERATION
# =============================================================================


def slugify(text: str) -> str:
    """
    Convert topic text to URL-safe slug.

    Args:
        text: Topic text to slugify

    Returns:
        URL-safe slug string (lowercase, hyphenated)

    Examples:
        >>> slugify("TikTok Shop Strategies")
        'tiktok-shop-strategies'
        >>> slugify("What's Working: 2026!")
        'what-s-working-2026'
        >>> slugify("")
        'newsletter'
    """
    if not text or not text.strip():
        return "newsletter"

    # Convert to lowercase
    slug = text.lower()

    # Replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)

    # Strip leading/trailing hyphens
    slug = slug.strip("-")

    # Return default if empty after processing
    return slug if slug else "newsletter"


# =============================================================================
# ISSUE NUMBER MANAGEMENT
# =============================================================================


def get_next_issue_number() -> int:
    """
    Get next issue number by scanning existing newsletters.

    Scans all .md files in NEWSLETTERS_DIR (including subfolders)
    for pattern NNN- where NNN is a 3-digit issue number.

    Returns:
        Next issue number (max existing + 1, or 1 if no files)
    """
    max_issue = 0

    if not NEWSLETTERS_DIR.exists():
        return 1

    # Scan all markdown files for issue numbers
    for md_file in NEWSLETTERS_DIR.rglob("*.md"):
        # Match pattern: starts with 3 digits followed by hyphen
        match = re.match(r"(\d{3})-", md_file.name)
        if match:
            issue_num = int(match.group(1))
            max_issue = max(max_issue, issue_num)

    return max_issue + 1


# =============================================================================
# MONTHLY FOLDER MANAGEMENT
# =============================================================================


def get_monthly_folder() -> Path:
    """
    Get or create current month's folder.

    Format: YYYY-MM (e.g., "2026-01")

    Returns:
        Path to monthly folder (created if doesn't exist)
    """
    month_str = datetime.now().strftime("%Y-%m")
    folder = NEWSLETTERS_DIR / month_str

    # Create if doesn't exist
    folder.mkdir(parents=True, exist_ok=True)

    return folder


# =============================================================================
# INDEX MANAGEMENT
# =============================================================================


def update_index(entry: dict) -> None:
    """
    Update index.json manifest with new newsletter entry.

    Creates index.json if it doesn't exist.

    Args:
        entry: Newsletter entry dict with fields:
            - issue: int
            - topic: str
            - date: ISO date string
            - path: relative path from newsletters dir
            - subject_line: str
            - cost: float (optional)
    """
    # Ensure parent directory exists
    NEWSLETTERS_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing or create new
    if INDEX_PATH.exists():
        try:
            with open(INDEX_PATH) as f:
                index = json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.warning("Could not read index.json, creating new")
            index = {"newsletters": []}
    else:
        index = {"newsletters": []}

    # Ensure newsletters key exists
    if "newsletters" not in index:
        index["newsletters"] = []

    # Append new entry
    index["newsletters"].append(entry)

    # Write with indent=2 for readability
    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, indent=2)

    logger.info(f"Updated index.json with issue {entry.get('issue')}")


# =============================================================================
# NEWSLETTER SAVING
# =============================================================================


def save_newsletter(
    output: "NewsletterOutput",
    topic: Optional[str] = None,
) -> Path:
    """
    Save newsletter to organized output structure.

    Creates:
    - Monthly subfolder (YYYY-MM)
    - Filename: {issue:03d}-{slug}.md
    - Updates index.json manifest

    Args:
        output: NewsletterOutput from newsletter_generator
        topic: Optional topic override (uses output metadata if not provided)

    Returns:
        Full path to saved newsletter file
    """
    # Get next issue number
    issue_number = get_next_issue_number()

    # Get monthly folder
    folder = get_monthly_folder()

    # Generate slug from topic or extract from output
    if topic:
        slug = slugify(topic)
    elif hasattr(output, "metadata") and output.metadata:
        # Try to extract topic from metadata or subject line
        meta_topic = output.metadata.get("topic") or output.subject_line
        slug = slugify(meta_topic[:50] if meta_topic else "")
    else:
        slug = slugify(output.subject_line[:50] if output.subject_line else "")

    # Generate filename: {issue:03d}-{slug}.md
    filename = f"{issue_number:03d}-{slug}.md"
    filepath = folder / filename

    # Write markdown content
    filepath.write_text(output.markdown)
    logger.info(f"Newsletter saved to {filepath}")

    # Prepare index entry
    entry = {
        "issue": issue_number,
        "topic": topic or slug.replace("-", " ").title(),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "path": str(filepath.relative_to(NEWSLETTERS_DIR)),
        "subject_line": output.subject_line,
    }

    # Add cost if available in metadata
    if hasattr(output, "metadata") and output.metadata:
        if "cost" in output.metadata:
            entry["cost"] = output.metadata["cost"]

    # Update index
    update_index(entry)

    return filepath


# =============================================================================
# NOTIFICATIONS
# =============================================================================


def notify(title: str, message: str) -> None:
    """
    Send macOS desktop notification.

    Uses osascript for native macOS notifications.
    Silent no-op on non-macOS platforms.
    Logs failure but doesn't raise.

    Args:
        title: Notification title
        message: Notification body text
    """
    # Check if macOS
    if sys.platform != "darwin":
        logger.debug("Skipping notification on non-macOS platform")
        return

    try:
        # Escape quotes in message and title
        safe_title = title.replace('"', '\\"')
        safe_message = message.replace('"', '\\"')

        script = f'display notification "{safe_message}" with title "{safe_title}"'
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
        )
        logger.debug(f"Notification sent: {title}")

    except subprocess.TimeoutExpired:
        logger.warning("Notification timed out")
    except FileNotFoundError:
        logger.warning("osascript not found - notifications unavailable")
    except Exception as e:
        logger.warning(f"Notification failed: {e}")


def notify_pipeline_complete(result: "PipelineResult") -> None:
    """
    Send notification for pipeline completion.

    Sends different messages for success vs failure.

    Args:
        result: PipelineResult from pipeline_runner
    """
    if result.success:
        # Success notification
        title = "DTC Newsletter Complete"
        message = f"Issue saved. Cost: ${result.total_cost:.2f}"

        # Add newsletter path if available
        if result.newsletter_path:
            # Get just the filename for brevity
            message = f"{result.newsletter_path.name} - ${result.total_cost:.2f}"

    else:
        # Failure notification
        title = "DTC Newsletter Failed"

        # Build error summary
        if result.errors:
            message = result.errors[0][:100]  # Truncate long errors
        else:
            message = "Pipeline failed - check logs"

    notify(title, message)
