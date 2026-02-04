#!/usr/bin/env python3
"""
Newsletter generator orchestrator for DTC Money Minute.
DOE-VERSION: 2026.02.04

Full newsletter orchestration:
1. Selects content for sections via content_selector
2. Uses pre-generated deep dive for Section 2 (the meat)
3. Generates other sections with narrative coherence
4. Generates subject line and preview text
5. Outputs Beehiiv-ready markdown

CLI interface for newsletter generation from aggregated content.
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add parent directory to path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import newsletter modules
from execution.claude_client import ClaudeClient
from execution.content_selector import select_content_for_sections, ContentSelection
from execution.section_generators import (
    generate_section_1,
    generate_section_2,
    generate_section_2_from_deep_dive,
    generate_section_3,
    generate_section_4,
    generate_section_5,
)
from execution.subject_line_generator import (
    select_subject_style,
    generate_subject_line,
    generate_preview_text,
)


@dataclass
class NewsletterOutput:
    """
    Complete newsletter output.

    Contains all generated content and metadata for the newsletter.
    """

    issue_number: int
    subject_line: str
    preview_text: str
    sections: dict  # section_1, section_2, etc.
    markdown: str  # Complete formatted output
    metadata: dict = field(default_factory=dict)


def format_as_markdown(output: NewsletterOutput) -> str:
    """
    Format newsletter output as Beehiiv-ready markdown.

    Combines all sections into a single markdown document with:
    - Subject line as comment at top
    - Preview text as comment
    - Sections separated by blank lines
    - No section headers (natural flow)

    Args:
        output: NewsletterOutput with all sections

    Returns:
        Complete markdown string
    """
    lines = []

    # Add metadata as HTML comments at top
    lines.append(f"<!-- Subject: {output.subject_line} -->")
    lines.append(f"<!-- Preview: {output.preview_text} -->")
    lines.append(f"<!-- Issue: {output.issue_number} -->")
    lines.append(f"<!-- Generated: {datetime.now(timezone.utc).isoformat()} -->")
    lines.append("")

    # Add sections in order (no headers, natural flow)
    section_order = ["section_1", "section_2", "section_3", "section_4", "section_5"]

    for section_name in section_order:
        content = output.sections.get(section_name)
        if content:
            lines.append(content.strip())
            lines.append("")  # Blank line between sections

    return "\n".join(lines)


def generate_newsletter(
    aggregated_content: list[dict],
    issue_number: int,
    tool_info: Optional[dict] = None,
    ps_type: str = "foreshadow",
    deep_dive: Optional[dict] = None,
) -> NewsletterOutput:
    """
    Generate a complete newsletter from aggregated content.

    Full orchestration:
    1. Initialize ClaudeClient
    2. Select content via select_content_for_sections()
    3. Generate Section 1 (instant reward)
    4. Generate Section 2 (tactical) - uses deep_dive if provided, otherwise generates
    5. Generate Section 3 (breakdown) with prior context
    6. Generate Section 4 (tool) - uses tool_info or placeholder
    7. Generate Section 5 (PS) with full context
    8. Generate subject line (select style, generate, validate)
    9. Generate preview text
    10. Format as markdown
    11. Return NewsletterOutput

    Args:
        aggregated_content: List of content dicts from content aggregation
        issue_number: Newsletter issue number
        tool_info: Optional dict with tool details for Section 4
            - name: Tool name (required)
            - description: What it does (required)
            - why_it_helps: Why it's valuable (required)
            - link: URL (optional)
        ps_type: Type of PS statement (foreshadow, cta, meme)
        deep_dive: Optional pre-generated deep dive dict for Section 2
            If provided, uses generate_section_2_from_deep_dive()
            If not provided, generates Section 2 from content

    Returns:
        NewsletterOutput with all content and metadata
    """
    start_time = datetime.now(timezone.utc)
    logger.info(f"Starting newsletter generation for issue #{issue_number}")

    # Initialize client
    client = ClaudeClient()

    # Step 1: Select content for sections
    logger.info("Selecting content for sections...")
    selection = select_content_for_sections(aggregated_content)

    # Track sections
    sections = {}
    prior_sections = {}

    # Step 2: Generate Section 1 (Instant Reward)
    logger.info("Generating Section 1: Instant Reward...")
    if selection.section_1:
        sections["section_1"] = generate_section_1(
            content=selection.section_1,
            client=client,
        )
        prior_sections["section_1"] = sections["section_1"]
    else:
        logger.warning("No content for Section 1, using placeholder")
        sections["section_1"] = "Quick win: [Content pending]"
        prior_sections["section_1"] = sections["section_1"]

    # Step 3: Generate Section 2 (What's Working Now)
    logger.info("Generating Section 2: What's Working Now...")
    if deep_dive and isinstance(deep_dive, dict) and "the_story" in deep_dive:
        # Use pre-generated deep dive (outlier-first approach)
        logger.info("Using pre-generated deep dive for Section 2")
        sections["section_2"] = generate_section_2_from_deep_dive(
            deep_dive=deep_dive,
            client=client,
            prior_sections=prior_sections,
        )
        prior_sections["section_2"] = sections["section_2"]
    elif selection.section_2:
        # Fall back to generating from selected content
        logger.info("Generating Section 2 from selected content")
        sections["section_2"] = generate_section_2(
            content=selection.section_2,
            client=client,
            prior_sections=prior_sections,
        )
        prior_sections["section_2"] = sections["section_2"]
    else:
        logger.warning("No content for Section 2, using placeholder")
        sections["section_2"] = "Tactical content: [Content pending]"
        prior_sections["section_2"] = sections["section_2"]

    # Step 4: Generate Section 3 (The Breakdown)
    logger.info("Generating Section 3: The Breakdown...")
    if selection.section_3:
        sections["section_3"] = generate_section_3(
            content=selection.section_3,
            client=client,
            prior_sections=prior_sections,
        )
        prior_sections["section_3"] = sections["section_3"]
    else:
        logger.warning("No content for Section 3, using placeholder")
        sections["section_3"] = "Story breakdown: [Content pending]"
        prior_sections["section_3"] = sections["section_3"]

    # Step 5: Generate Section 4 (Tool of the Week)
    logger.info("Generating Section 4: Tool of the Week...")
    if tool_info:
        sections["section_4"] = generate_section_4(
            tool_info=tool_info,
            client=client,
            prior_sections=prior_sections,
        )
    else:
        # Use placeholder tool info if not provided
        placeholder_tool = {
            "name": "Tool Placeholder",
            "description": "A tool that helps DTC brands",
            "why_it_helps": "Saves time and increases conversions",
        }
        logger.warning("No tool_info provided, using placeholder")
        sections["section_4"] = generate_section_4(
            tool_info=placeholder_tool,
            client=client,
            prior_sections=prior_sections,
        )
    prior_sections["section_4"] = sections["section_4"]

    # Step 6: Generate Section 5 (PS Statement)
    logger.info(f"Generating Section 5: PS Statement (type={ps_type})...")
    sections["section_5"] = generate_section_5(
        client=client,
        prior_sections=prior_sections,
        ps_type=ps_type,
    )

    # Step 7: Generate subject line
    logger.info("Generating subject line...")
    style = select_subject_style()
    logger.info(f"Selected subject style: {style}")

    # Get main topic from section 2 content
    main_topic = "DTC marketing tactics"
    if selection.section_2:
        main_topic = selection.section_2.get("title", main_topic)[:50]

    subject_line = generate_subject_line(
        issue_number=issue_number,
        main_topic=main_topic,
        style=style,
        client=client,
    )

    # Step 8: Generate preview text
    logger.info("Generating preview text...")
    newsletter_content = "\n".join(
        [sections.get(f"section_{i}", "") for i in range(1, 6)]
    )
    preview_text = generate_preview_text(
        newsletter_content=newsletter_content,
        client=client,
    )

    # Build output
    output = NewsletterOutput(
        issue_number=issue_number,
        subject_line=subject_line,
        preview_text=preview_text,
        sections=sections,
        markdown="",  # Will be set below
        metadata={
            "sources_used": selection.sources_used,
            "word_counts": {
                name: len(content.split()) for name, content in sections.items()
            },
            "generation_time": (
                datetime.now(timezone.utc) - start_time
            ).total_seconds(),
            "subject_style": style,
            "ps_type": ps_type,
        },
    )

    # Step 9: Format as markdown
    logger.info("Formatting as markdown...")
    output.markdown = format_as_markdown(output)

    logger.info(
        f"Newsletter generation complete in {output.metadata['generation_time']:.1f}s"
    )
    return output


def save_newsletter(output: NewsletterOutput, output_dir: Path) -> Path:
    """
    Save newsletter to file.

    Args:
        output: NewsletterOutput to save
        output_dir: Directory to save to

    Returns:
        Path to saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-issue-{output.issue_number}.md"
    filepath = output_dir / filename

    # Write file
    filepath.write_text(output.markdown)
    logger.info(f"Newsletter saved to {filepath}")

    # Also save JSON metadata
    metadata_file = output_dir / f"{date_str}-issue-{output.issue_number}-meta.json"
    metadata = {
        "issue_number": output.issue_number,
        "subject_line": output.subject_line,
        "preview_text": output.preview_text,
        "metadata": output.metadata,
    }
    metadata_file.write_text(json.dumps(metadata, indent=2))
    logger.info(f"Metadata saved to {metadata_file}")

    return filepath


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate DTC Money Minute newsletter from aggregated content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from content file
  python execution/newsletter_generator.py --content-file output/content_sheet.json --issue-number 1

  # With tool information
  python execution/newsletter_generator.py --content-file data.json --issue-number 5 \\
    --tool-name "Klaviyo" --tool-description "Email marketing platform" \\
    --tool-why "2x email revenue for DTC brands"

  # Different PS type
  python execution/newsletter_generator.py --content-file data.json --issue-number 3 --ps-type cta

  # Dry run (don't save)
  python execution/newsletter_generator.py --content-file data.json --issue-number 1 --dry-run
        """,
    )

    # Required arguments
    parser.add_argument(
        "--content-file",
        type=str,
        required=True,
        help="Path to aggregated content JSON file",
    )

    parser.add_argument(
        "--issue-number",
        type=int,
        required=True,
        help="Newsletter issue number",
    )

    # Tool information (optional)
    parser.add_argument(
        "--tool-name",
        type=str,
        help="Name of tool for Section 4",
    )

    parser.add_argument(
        "--tool-description",
        type=str,
        help="Description of tool for Section 4",
    )

    parser.add_argument(
        "--tool-why",
        type=str,
        help="Why the tool helps (for Section 4)",
    )

    parser.add_argument(
        "--tool-link",
        type=str,
        help="Optional link for Section 4 tool",
    )

    # PS type
    parser.add_argument(
        "--ps-type",
        type=str,
        choices=["foreshadow", "cta", "meme"],
        default="foreshadow",
        help="Type of PS statement (default: foreshadow)",
    )

    # Deep dive
    parser.add_argument(
        "--deep-dive-file",
        type=str,
        help="Path to pre-generated deep dive JSON file for Section 2",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/newsletters/",
        help="Output directory (default: output/newsletters/)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate but don't save to file",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Load content file
    content_path = Path(args.content_file)
    if not content_path.exists():
        logger.error(f"Content file not found: {content_path}")
        return 1

    with open(content_path) as f:
        data = json.load(f)

    # Handle different JSON structures
    if isinstance(data, list):
        aggregated_content = data
    elif isinstance(data, dict):
        # Try common keys
        aggregated_content = data.get("contents") or data.get("items") or []
    else:
        logger.error(f"Unexpected content format: {type(data)}")
        return 1

    if not aggregated_content:
        logger.error("No content found in content file")
        return 1

    logger.info(f"Loaded {len(aggregated_content)} content items")

    # Load deep dive if provided
    deep_dive = None
    if args.deep_dive_file:
        deep_dive_path = Path(args.deep_dive_file)
        if not deep_dive_path.exists():
            logger.error(f"Deep dive file not found: {deep_dive_path}")
            return 1
        with open(deep_dive_path) as f:
            deep_dive_data = json.load(f)
        # Handle both direct deep dive and wrapped format
        deep_dive = deep_dive_data.get("deep_dive", deep_dive_data)
        logger.info(f"Loaded deep dive: {deep_dive.get('headline', 'Unknown')[:50]}...")

    # Build tool_info if provided
    tool_info = None
    if args.tool_name:
        tool_info = {
            "name": args.tool_name,
            "description": args.tool_description or "A useful tool for DTC brands",
            "why_it_helps": args.tool_why or "Helps improve results",
        }
        if args.tool_link:
            tool_info["link"] = args.tool_link

    # Generate newsletter
    try:
        output = generate_newsletter(
            aggregated_content=aggregated_content,
            issue_number=args.issue_number,
            tool_info=tool_info,
            ps_type=args.ps_type,
            deep_dive=deep_dive,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return 1

    # Display results
    print("\n" + "=" * 60)
    print("=== Newsletter Generated ===")
    print("=" * 60)
    print(f"\nIssue: #{output.issue_number}")
    print(f"Subject: {output.subject_line}")
    print(f"Preview: {output.preview_text}")
    print(f"\nGeneration time: {output.metadata['generation_time']:.1f}s")
    print(f"Sources used: {', '.join(output.metadata['sources_used'])}")

    print("\nWord counts:")
    for section, count in output.metadata["word_counts"].items():
        print(f"  {section}: {count}")

    # Save unless dry run
    if not args.dry_run:
        output_dir = Path(args.output_dir)
        filepath = save_newsletter(output, output_dir)
        print(f"\nSaved to: {filepath}")
    else:
        print("\n(Dry run - not saved)")
        print("\n--- Preview ---")
        print(output.markdown[:1000])
        if len(output.markdown) > 1000:
            print(f"\n... ({len(output.markdown)} total chars)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
