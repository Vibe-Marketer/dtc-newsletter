#!/usr/bin/env python3
"""
Product integrator for DTCNews newsletter.
DOE-VERSION: 2026.02.04

Inserts natural product mentions into newsletter content.
Ensures 2-3 organic mentions per issue with proper placement and tone.

Skill: .claude/skills/dtc-products-05/SKILL.md

Usage:
    python execution/product_integrator.py --file output/newsletter_draft.md
    python execution/product_integrator.py --content "Newsletter content..." --output integrated.md
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.claude_client import ClaudeClient

DOE_VERSION = "2026.02.04"

# =============================================================================
# PRODUCT CATALOG
# =============================================================================


@dataclass
class Product:
    """Product definition with triggers and mention templates."""

    id: str
    name: str
    price: str
    value_prop: str
    url_slug: str
    triggers: list[str]
    best_sections: list[str]
    soft_templates: list[str]
    medium_templates: list[str]


PRODUCTS = [
    Product(
        id="starter-pack",
        name="AI Store Starter Pack",
        price="$19",
        value_prop="GPTs and templates to launch first Shopify store in 7 days",
        url_slug="starter-pack",
        triggers=[
            "prompt",
            "ai",
            "gpt",
            "template",
            "store setup",
            "product descriptions",
            "getting started",
            "launch",
            "beginner",
            "first store",
        ],
        best_sections=["After Section 1", "Section 4 (Prompt Drop)"],
        soft_templates=[
            "This prompt is from our AI Store Starter Pack.",
            "We pulled this from the Starter Pack vault.",
            "One of 47 prompts in the Starter Pack.",
        ],
        medium_templates=[
            "Get 47 more prompts like this in the Starter Pack ($19).",
            "The AI Store Starter Pack has the full collection of these ($19).",
            "Want more? The Starter Pack includes 47 GPTs and templates for $19.",
        ],
    ),
    Product(
        id="sales-sprint",
        name="First 10 Sales Sprint",
        price="$49-59",
        value_prop="Get first 10 orders in 30 days using ads and AI",
        url_slug="first-10-sales",
        triggers=[
            "traffic",
            "ads",
            "sales",
            "customers",
            "orders",
            "first sale",
            "meta ads",
            "facebook ads",
            "acquisition",
            "conversion",
            "getting customers",
        ],
        best_sections=["After Section 2", "Section 5 (PS)"],
        soft_templates=[
            "This exact strategy is in our First 10 Sales Sprint.",
            "We cover this in depth in the Sales Sprint.",
            "This is step 3 of the First 10 Sales playbook.",
        ],
        medium_templates=[
            "Want the complete playbook? The Sprint walks you through it ($49).",
            "The First 10 Sales Sprint gives you the full system for $49.",
            "Get all 30 days mapped out in the Sales Sprint ($49).",
        ],
    ),
    Product(
        id="vault",
        name="Ecom Prompt and Template Vault",
        price="$19/4 weeks",
        value_prop="Monthly prompts, templates, and teardowns delivered weekly",
        url_slug="vault",
        triggers=[
            "tool",
            "resource",
            "template",
            "weekly",
            "new this week",
            "swipe file",
            "teardown",
            "collection",
        ],
        best_sections=["Section 3 (Tool of Week)", "Section 4 (Prompt Drop)"],
        soft_templates=[
            "Vault members got this template yesterday.",
            "This dropped in the Vault last week.",
            "From this month's Vault collection.",
        ],
        medium_templates=[
            "Join the Vault for weekly resources ($19/month).",
            "The Vault delivers fresh templates like this every week ($19/mo).",
            "Get a new batch every week in the Vault ($19/month).",
        ],
    ),
]

FOOTER_TEMPLATE = """---

**Level up your store:**

- **AI Store Starter Pack** - Launch your first Shopify store in 7 days with 47 GPTs and templates. [$19]
- **First 10 Sales Sprint** - Get your first 10 orders in 30 days with our ads + AI playbook. [$49]
- **Ecom Prompt and Template Vault** - Fresh prompts, templates, and teardowns delivered weekly. [$19/mo]
"""

# =============================================================================
# INTEGRATION SYSTEM PROMPT
# =============================================================================

INTEGRATOR_SYSTEM_PROMPT = """You are an expert at naturally integrating product mentions into newsletter content.

Your goal is to add 2-3 product mentions that feel like helpful recommendations, not ads.

PRODUCTS AVAILABLE:
1. AI Store Starter Pack ($19) - 47 GPTs and templates for launching a Shopify store
   - Triggers: prompts, AI, GPT, templates, getting started, first store
   - Best after: Prompt Drop section, after tactical content
   
2. First 10 Sales Sprint ($49) - 30-day playbook for first 10 orders
   - Triggers: traffic, ads, sales, customers, orders
   - Best after: Deep Dive section, in PS
   
3. Ecom Prompt and Template Vault ($19/mo) - Weekly prompts and templates
   - Triggers: tools, resources, templates, weekly content
   - Best in: Tool of Week section, Prompt Drop

RULES:
1. NEVER mention a product before delivering value in that section
2. Mentions should feel like a friend sharing a helpful resource
3. Maximum 2-3 mentions per newsletter (not counting footer)
4. Use soft mentions (just name) or medium mentions (name + price)
5. Space mentions apart - never two within 3 paragraphs
6. Different products preferred over same product twice

SOFT MENTION EXAMPLES:
- "This prompt is from our AI Store Starter Pack."
- "This exact strategy is in our First 10 Sales Sprint."
- "Vault members got this template yesterday."

MEDIUM MENTION EXAMPLES:
- "Get 47 more prompts like this in the Starter Pack ($19)."
- "Want the complete playbook? The Sprint walks you through it ($49)."
- "Join the Vault for weekly resources ($19/month)."

OUTPUT FORMAT:
Return the integrated content with mentions marked like this:
<!-- PRODUCT MENTION: [product-id] [soft/medium] -->
[mention text]

Also provide a placement report after the content."""


def find_triggers(content: str, products: list[Product]) -> dict[str, list[str]]:
    """
    Find product triggers in content.

    Args:
        content: Newsletter content to scan
        products: List of Product objects

    Returns:
        Dict mapping product_id to list of triggers found
    """
    content_lower = content.lower()
    found = {}

    for product in products:
        matches = []
        for trigger in product.triggers:
            if trigger.lower() in content_lower:
                matches.append(trigger)
        if matches:
            found[product.id] = matches

    return found


def integrate_products(
    content: str,
    client: ClaudeClient | None = None,
    max_mentions: int = 3,
) -> tuple[str, dict]:
    """
    Integrate product mentions into newsletter content.

    Args:
        content: Newsletter content to integrate products into
        client: ClaudeClient instance
        max_mentions: Maximum number of mentions to add (default: 3)

    Returns:
        Tuple of (integrated_content, placement_report)
    """
    if client is None:
        client = ClaudeClient()

    # Find triggers
    triggers_found = find_triggers(content, PRODUCTS)

    trigger_summary = "\n".join(
        [f"- {pid}: {', '.join(triggers)}" for pid, triggers in triggers_found.items()]
    )

    user_prompt = f"""Integrate product mentions into this newsletter content.

TRIGGERS FOUND:
{trigger_summary if trigger_summary else "No specific triggers found - use judgment based on content"}

CONTENT:
---
{content}
---

Add 2-3 natural product mentions following the rules. Mark each mention with HTML comments.
After the content, provide a placement report showing what was added and why.

Remember:
- Never mention before delivering value
- Feel like a friend sharing a resource, not an ad
- Space mentions apart
- Use different products when possible"""

    response = client.generate(
        prompt=user_prompt,
        system_prompt=INTEGRATOR_SYSTEM_PROMPT,
        max_tokens=4000,
    )

    # Parse the response
    # Try to split content from report
    if "## Placement Report" in response or "## PLACEMENT REPORT" in response:
        parts = re.split(
            r"##\s*(?:Placement Report|PLACEMENT REPORT)", response, flags=re.IGNORECASE
        )
        integrated_content = parts[0].strip()
        report_text = parts[1].strip() if len(parts) > 1 else ""
    elif "---" in response and "Product Integration Report" in response:
        parts = response.split("---")
        integrated_content = parts[0].strip()
        report_text = "---".join(parts[1:]).strip()
    else:
        integrated_content = response
        report_text = ""

    # Count mentions
    soft_count = len(
        re.findall(r"<!-- PRODUCT MENTION:.*?soft", integrated_content, re.IGNORECASE)
    )
    medium_count = len(
        re.findall(r"<!-- PRODUCT MENTION:.*?medium", integrated_content, re.IGNORECASE)
    )

    # Build report
    report = {
        "triggers_found": triggers_found,
        "total_mentions": soft_count + medium_count,
        "soft_mentions": soft_count,
        "medium_mentions": medium_count,
        "report_text": report_text,
    }

    return integrated_content, report


def add_footer(content: str) -> str:
    """
    Add product footer to content if not already present.

    Args:
        content: Newsletter content

    Returns:
        Content with footer added
    """
    if "Level up your store" in content:
        return content

    return content.rstrip() + "\n\n" + FOOTER_TEMPLATE


def format_report(report: dict) -> str:
    """
    Format placement report as markdown.

    Args:
        report: Placement report dict

    Returns:
        Formatted markdown
    """
    lines = []
    lines.append("## Product Integration Report")
    lines.append("")
    lines.append(f"**Total Mentions:** {report['total_mentions']} (target: 2-3)")
    lines.append(f"**Soft Mentions:** {report['soft_mentions']}")
    lines.append(f"**Medium Mentions:** {report['medium_mentions']}")
    lines.append("")

    if report.get("triggers_found"):
        lines.append("**Triggers Found:**")
        for pid, triggers in report["triggers_found"].items():
            lines.append(f"- {pid}: {', '.join(triggers)}")
        lines.append("")

    if report.get("report_text"):
        lines.append("**Details:**")
        lines.append(report["report_text"])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Integrate product mentions into DTCNews newsletter content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        "-f",
        help="Newsletter draft file to process",
    )
    parser.add_argument(
        "--content",
        "-c",
        help="Direct content to process",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for integrated content",
    )
    parser.add_argument(
        "--max-mentions",
        type=int,
        default=3,
        help="Maximum number of mentions to add (default: 3)",
    )
    parser.add_argument(
        "--no-footer",
        action="store_true",
        help="Don't add product footer",
    )
    parser.add_argument(
        "--triggers-only",
        action="store_true",
        help="Only show triggers found, don't integrate",
    )
    args = parser.parse_args()

    print(f"[product_integrator] v{DOE_VERSION}")
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

    # Find triggers
    triggers = find_triggers(content, PRODUCTS)

    if args.triggers_only:
        print("=" * 60)
        print("TRIGGERS FOUND")
        print("=" * 60)
        if triggers:
            for pid, found in triggers.items():
                product = next(p for p in PRODUCTS if p.id == pid)
                print(f"{product.name}:")
                for t in found:
                    print(f"  - {t}")
                print()
        else:
            print("No product triggers found in content.")
        return 0

    print("Triggers found:")
    for pid, found in triggers.items():
        print(f"  {pid}: {', '.join(found[:3])}{'...' if len(found) > 3 else ''}")
    print()

    # Initialize Claude client
    try:
        client = ClaudeClient()
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Integrate products
    print("Integrating product mentions...")
    integrated, report = integrate_products(content, client, args.max_mentions)

    # Add footer
    if not args.no_footer:
        integrated = add_footer(integrated)

    print()
    print("=" * 60)
    print("INTEGRATION COMPLETE")
    print("=" * 60)
    print()
    print(format_report(report))
    print()

    # Output
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            f.write(integrated)
        print(f"Saved integrated content to: {output_path}")
    else:
        print("-" * 60)
        print("INTEGRATED CONTENT PREVIEW (first 1000 chars):")
        print("-" * 60)
        print(integrated[:1000])
        if len(integrated) > 1000:
            print(f"... ({len(integrated) - 1000} more chars)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
