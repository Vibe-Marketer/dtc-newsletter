#!/usr/bin/env python3
"""
Newsletter orchestrator for DTCNews.
DOE-VERSION: 2026.02.04

Master orchestrator that:
1. Asks about sponsor/affiliate FIRST
2. Finds the viral edge/outlier
3. Flows EVERYTHING from that outlier:
   - Deep dive on the tactic
   - Tool research (contextual to tactic)
   - Prompt that helps execute the tactic
   - Next 24 hours action steps

The entire newsletter is driven by ONE viral tactic.

Usage:
    python execution/newsletter_orchestrator.py
    python execution/newsletter_orchestrator.py --issue 2
    python execution/newsletter_orchestrator.py --skip-sponsor  # For testing
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.search_fetcher import fetch_all_content
from execution.outlier_ranker import rank_content
from execution.deep_dive_generator import generate_deep_dive, format_deep_dive_markdown
from execution.tool_researcher import (
    run_tool_research,
    SponsorConfig,
    interactive_sponsor_prompt,
    ToolResearch,
)
from execution.topic_tracker import record_topic, check_topic_covered
from execution.claude_client import ClaudeClient
from execution.publishing_manager import (
    save_draft,
    PublishingMetadata,
    Source,
)

DOE_VERSION = "2026.02.04"


@dataclass
class NewsletterConfig:
    """Configuration for newsletter generation."""

    issue_number: int
    sponsor_config: SponsorConfig
    date: str


@dataclass
class NewsletterContent:
    """Complete newsletter content."""

    config: NewsletterConfig

    # The viral edge that drives everything
    viral_edge: dict
    tactic: str  # Core tactic extracted from viral edge

    # Section content
    section_1_hook: str
    section_2_deep_dive: dict
    section_3_tool: str  # Formatted markdown string
    section_4_prompt: dict
    section_5_action: str

    # Metadata
    subject_line: str
    preview_text: str
    generated_at: str
    next_issue_teaser: str = ""  # PS teaser for next issue


def ask_sponsor_questions() -> SponsorConfig:
    """
    Ask sponsor/affiliate questions at the start.

    Returns:
        SponsorConfig with user's choices
    """
    print("\n" + "=" * 60)
    print("NEWSLETTER CONFIGURATION")
    print("=" * 60)

    print("\nBefore we start, let's configure this issue:\n")

    # Question 1: Sponsor?
    has_sponsor_input = (
        input("Do you have a sponsor/affiliate for this issue? [yes/no]: ")
        .strip()
        .lower()
    )
    has_sponsor = has_sponsor_input in ["yes", "y", "1", "true"]

    if not has_sponsor:
        print(
            "\n  No sponsor - we'll find the best tool and look for affiliate opportunities."
        )
        return SponsorConfig(has_sponsor=False)

    # Question 2: Who?
    sponsor_name = input("\nWho is the sponsor? (tool/company name): ").strip()

    if not sponsor_name:
        print("  No sponsor name provided - treating as no sponsor.")
        return SponsorConfig(has_sponsor=False)

    # Question 3: Specific angle?
    print(f"\nDo you have a specific angle/positioning request for {sponsor_name}?")
    print("  Examples:")
    print("  - 'Position as #1 for beginners'")
    print("  - 'Highlight their new AI feature launched last week'")
    print("  - 'Emphasize their free tier'")
    print("  - Or leave blank for general positive positioning")

    specific_angle = input("\nSpecific angle (or Enter for none): ").strip()

    print(f"\n  Sponsor: {sponsor_name}")
    if specific_angle:
        print(f"  Angle: {specific_angle}")
    else:
        print(
            "  Angle: General positive positioning with damaging admission for authenticity"
        )

    return SponsorConfig(
        has_sponsor=True,
        sponsor_name=sponsor_name,
        specific_angle=specific_angle if specific_angle else None,
    )


def find_viral_edge(verbose: bool = True) -> tuple[dict, Optional[dict]]:
    """
    Find the viral edge/outlier that will drive the newsletter.

    Returns:
        Tuple of (top ranked item, next best item for teaser)
    """
    if verbose:
        print("\n" + "=" * 60)
        print("STEP 1: FINDING THE VIRAL EDGE")
        print("=" * 60)

    # Fetch content
    if verbose:
        print("\nSearching for viral ecommerce content...")

    content = fetch_all_content(verbose=verbose)

    if not content:
        raise ValueError("No content found. Check your API keys.")

    if verbose:
        print(f"\nFound {len(content)} items. Ranking by outlier score...")

    # Rank content
    ranked, filtered = rank_content(content, min_score=2.0, top_n=10)

    if not ranked:
        raise ValueError("No content passed ranking threshold.")

    # Find first and second non-covered items
    top_item = None
    next_item = None

    for item in ranked:
        is_covered, match = check_topic_covered(item.get("title", ""))
        if is_covered:
            if verbose and top_item is None:
                print(
                    f"\n  Skipping '{item.get('title', '')[:40]}...' (covered in Issue #{match.get('issue_number') if match else '?'})"
                )
            continue

        if top_item is None:
            top_item = item
        elif next_item is None:
            next_item = item
            break

    if top_item is None:
        # Fallback to first item if all covered
        top_item = ranked[0]
        next_item = ranked[1] if len(ranked) > 1 else None

    if verbose:
        print(f"\n  VIRAL EDGE SELECTED:")
        print(f"  Title: {top_item.get('title', 'Unknown')[:70]}...")
        print(
            f"  Score: {top_item.get('composite_rank', top_item.get('outlier_score', 0)):.1f}x"
        )
        print(f"  Source: {top_item.get('source', 'unknown')}")
        if next_item:
            print(f"\n  NEXT ISSUE TEASER:")
            print(f"  Title: {next_item.get('title', 'Unknown')[:70]}...")

    return top_item, next_item


def generate_section_1_hook(
    viral_edge: dict, deep_dive: dict, client: ClaudeClient
) -> str:
    """
    Generate Section 1: This Week's Win (The Hook).

    Immediately prove value with a concrete, timely win.
    """
    prompt = f"""Write Section 1: "This Week's Win" for a newsletter.

THE VIRAL EDGE:
Title: {viral_edge.get("title", "")}
Summary: {viral_edge.get("summary", "")}
Results: {viral_edge.get("results", "")}

FROM DEEP DIVE:
Headline: {deep_dive.get("headline", "")}
Key Insight: {deep_dive.get("key_insight", "")}

REQUIREMENTS:
- 150-200 words MAX
- Start with the specific tactic/win that's working RIGHT NOW
- Include a concrete number or proof point
- Make it punchy, not setup-heavy
- End with transition to "Here's what they did..."

TONE: Excited but not hype-y. Like telling a friend about something cool you found.

Write the section (no header/title needed):"""

    return client.generate_with_voice(prompt, max_tokens=400)


def generate_section_4_prompt(
    tactic: str, deep_dive: dict, tool_research: ToolResearch, client: ClaudeClient
) -> dict:
    """
    Generate Section 4: The Prompt Drop.

    A well-crafted, detailed prompt that helps execute the tactic.
    """
    prompt = f"""Create a ChatGPT/AI prompt for Section 4: "The Prompt Drop"

THE TACTIC: {tactic}

FROM DEEP DIVE:
- What they did: {json.dumps(deep_dive.get("what_they_did", [])[:2], indent=2)}
- Beginner version: {deep_dive.get("beginner_version", {}).get("same_principle", "")}

RECOMMENDED TOOL: {tool_research.recommendation.name}

Create a prompt that helps execute this tactic. Requirements:
1. DETAILED and STRUCTURED (not vague)
2. Has clear sections/steps
3. Includes ONE [VARIABLE] for customization
4. Produces something immediately useful
5. 50-150 words for the prompt itself

Return as JSON:
{{
  "prompt_title": "Short title (e.g., 'Product Video Script Generator')",
  "prompt_text": "The full copy-paste prompt",
  "what_it_produces": "What the user will get",
  "how_to_customize": "What to change in the [VARIABLE]",
  "advanced_tip": "One advanced variation"
}}

Return ONLY valid JSON."""

    response = client.generate(prompt, max_tokens=600)

    # Parse JSON
    import re

    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass

    # Fallback
    return {
        "prompt_title": "Tactic Execution Prompt",
        "prompt_text": deep_dive.get("prompt", {}).get("text", ""),
        "what_it_produces": deep_dive.get("prompt", {}).get("what_it_produces", ""),
        "how_to_customize": "Replace the [VARIABLE] with your specific details",
        "advanced_tip": "Add more context for better results",
    }


def generate_section_5_action(
    tactic: str,
    deep_dive: dict,
    tool_research: ToolResearch,
    prompt_drop: dict,
    client: ClaudeClient,
) -> str:
    """
    Generate Section 5: Your Next 24 Hours.

    ONE specific task to complete before next issue.
    """
    prompt = f"""Write Section 5: "Your Next 24 Hours"

THE TACTIC: {tactic}

ACTION STEPS FROM DEEP DIVE:
{json.dumps(deep_dive.get("action_steps", []), indent=2)}

RECOMMENDED TOOL: {tool_research.recommendation.name}

PROMPT THEY HAVE: {prompt_drop.get("prompt_title", "")}

Write a "Your Next 24 Hours" section:
- ONE ultra-specific task (not multiple)
- Time required (be realistic, under 1 hour)
- Success metric (how they know they did it)
- End with engagement prompt ("Reply with..." or "Share...")

Format:
**Your Next 24 Hours**

**The Task:** [Specific action]

**Time Needed:** X minutes

**Success Metric:** [How they'll know it's done]

**Share:** [Engagement prompt]

Keep it to 50-75 words total. Be specific, not vague."""

    return client.generate_with_voice(prompt, max_tokens=200)


def load_hormozi_hooks() -> dict:
    """Load Hormozi hooks database."""
    hooks_path = Path(__file__).parent.parent / "data" / "hormozi_hooks_db.json"
    if hooks_path.exists():
        with open(hooks_path) as f:
            return json.load(f)
    return {}


def generate_subject_and_preview(
    viral_edge: dict, deep_dive: dict, issue_number: int, client: ClaudeClient
) -> tuple[str, str]:
    """Generate subject line and preview text using Hormozi hook patterns."""

    # Load hooks for inspiration
    hooks_data = load_hormozi_hooks()

    # Get subject line formulas
    formulas = hooks_data.get("subject_line_formulas", {})
    formula_examples = []
    for category, patterns in formulas.items():
        for pattern in patterns[:2]:  # Take top 2 from each category
            formula_examples.append(f"- {pattern}")

    # Get beginner-adapted hooks
    adapted = hooks_data.get("beginner_adapted", [])
    adapted_examples = [h.get("adapted", "") for h in adapted[:3]]

    prompt = f"""Create a subject line and preview text for this newsletter:

HEADLINE: {deep_dive.get("headline", "")}
KEY RESULT: {viral_edge.get("results", "")}
KEY INSIGHT: {deep_dive.get("key_insight", "")}
ISSUE NUMBER: {issue_number}

HORMOZI-STYLE SUBJECT LINE FORMULAS (use these as inspiration):
{chr(10).join(formula_examples[:6])}

EXAMPLE ADAPTED HOOKS:
{chr(10).join(["- " + h for h in adapted_examples if h])}

SUBJECT LINE RULES:
- Under 50 characters
- Include the issue number naturally (e.g., "Issue #5:" or "#5:")
- Use curiosity, specific numbers, or direct benefit
- NO clickbait, NO ALL CAPS
- Make it feel like a friend texting you something exciting

PREVIEW TEXT RULES:
- 50-90 characters
- Expands on subject line with a specific detail
- Creates urgency or curiosity to open

Return as JSON:
{{
  "subject": "Your subject line here",
  "preview": "Your preview text here"
}}"""

    response = client.generate(prompt, max_tokens=150)

    import re

    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return data.get("subject", ""), data.get("preview", "")
        except:
            pass

    # Fallback
    return (
        f"Issue #{issue_number}: This week's viral tactic",
        "The exact strategy that's working right now.",
    )


def generate_ps_teaser(next_viral: Optional[dict], client: ClaudeClient) -> str:
    """
    Generate the PS teaser for next issue based on next viral content.

    Args:
        next_viral: The next best viral item (or None)
        client: ClaudeClient for generation

    Returns:
        Teaser string for the PS line
    """
    if not next_viral:
        return "something big we're tracking in the DTC space"

    title = next_viral.get("title", "")
    summary = next_viral.get("summary", "")

    prompt = f"""Create a short, intriguing teaser for next week's newsletter.

NEXT TOPIC:
Title: {title}
Summary: {summary[:200] if summary else ""}

Write a 5-10 word teaser that:
- Creates curiosity without giving away the full tactic
- Uses specific language (numbers, tools, results if available)
- Makes readers want to open next week's email

Examples of good teasers:
- "how one store 5x'd revenue with AI chatbots"
- "the $0 TikTok strategy that's crushing paid ads"
- "why your email subject lines are killing conversions"

Return ONLY the teaser text, nothing else."""

    teaser = client.generate(prompt, max_tokens=50).strip()

    # Clean up any quotes or extra formatting
    teaser = teaser.strip("\"'")

    # Fallback if too long or empty
    if not teaser or len(teaser) > 80:
        # Extract key phrase from title
        teaser = title[:60] if title else "a game-changing tactic we just discovered"

    return teaser


def load_products() -> dict:
    """Load products from data/products.json."""
    products_path = Path(__file__).parent.parent / "data" / "products.json"
    if products_path.exists():
        with open(products_path) as f:
            return json.load(f)
    return {"products": [], "integration_rules": {}}


def find_contextual_product_mention(tactic: str, deep_dive: dict) -> Optional[dict]:
    """
    Find the most relevant product to mention based on tactic context.

    Args:
        tactic: The main tactic being covered
        deep_dive: The deep dive content

    Returns:
        Dict with product info and mention template, or None
    """
    products_data = load_products()
    products = products_data.get("products", [])

    if not products:
        return None

    # Keywords from the tactic and deep dive
    tactic_lower = tactic.lower()
    what_they_did = deep_dive.get("what_they_did", [])
    keywords = [tactic_lower]
    for item in what_they_did:
        keywords.append(item.get("tactic", "").lower())

    # Score each product by context match
    best_match = None
    best_score = 0

    for product in products:
        score = 0
        contexts = product.get("good_contexts", [])
        for context in contexts:
            context_lower = context.lower()
            for keyword in keywords:
                if context_lower in keyword or keyword in context_lower:
                    score += 2
                # Partial match
                for word in context_lower.split():
                    if word in keyword:
                        score += 1

        if score > best_score:
            best_score = score
            best_match = product

    if best_match and best_score >= 2:
        # Pick a random mention template
        templates = best_match.get("mention_templates", [])
        import random

        template = random.choice(templates) if templates else None

        return {"product": best_match, "template": template, "score": best_score}

    return None


def format_tool_section(
    tool_research: ToolResearch, sponsor_config: SponsorConfig
) -> str:
    """
    Format Section 3: Tool of the Week.

    Includes free/paid comparison, recommendation, damaging admission.
    """
    lines = []

    lines.append(f"## Tool of the Week: {tool_research.tool_category}\n")

    # Context
    lines.append(
        f"To execute this tactic, you need the right {tool_research.tool_category.lower()} tool. Here's what we found:\n"
    )

    # Free options
    lines.append("**Free Options:**")
    for opt in tool_research.free_options[:3]:
        lines.append(f"- **{opt.name}** - {opt.description[:80]}...")
        if opt.best_for:
            lines.append(f"  *Best for: {opt.best_for}*")

    lines.append("")

    # Paid options
    lines.append("**Paid Options:**")
    for opt in tool_research.paid_options[:3]:
        pricing = f" ({opt.pricing})" if opt.pricing else ""
        lines.append(f"- **{opt.name}**{pricing} - {opt.description[:80]}...")
        if opt.social_proof:
            lines.append(f"  *{opt.social_proof}*")

    lines.append("")

    # Our recommendation
    lines.append(f"**Our Recommendation: {tool_research.recommendation.name}**\n")
    lines.append(tool_research.recommendation_rationale)

    # Damaging admission (for authenticity)
    if tool_research.damaging_admission:
        lines.append("")
        lines.append(f"*{tool_research.damaging_admission}*")
        lines.append(f"\n{tool_research.damaging_admission_counter}")

    # Social proof
    if tool_research.recommendation.social_proof:
        lines.append(f"\n*{tool_research.recommendation.social_proof}*")

    # Affiliate link (if no sponsor)
    if not sponsor_config.has_sponsor and tool_research.affiliate_opportunity:
        aff = tool_research.affiliate_opportunity
        if aff.get("has_affiliate"):
            lines.append(
                f"\n[Try {tool_research.recommendation.name} →]({tool_research.recommendation.website or '#'})"
            )

    return "\n".join(lines)


def format_full_newsletter(content: NewsletterContent, tactic: str = "") -> str:
    """Format the complete newsletter as markdown."""

    lines = []

    # Metadata
    lines.append(f"<!-- Subject: {content.subject_line} -->")
    lines.append(f"<!-- Preview: {content.preview_text} -->")
    lines.append(f"<!-- Issue: {content.config.issue_number} -->")
    lines.append(f"<!-- Generated: {content.generated_at} -->")
    lines.append("")

    # Section 1: This Week's Win
    lines.append("## This Week's Win\n")
    lines.append(content.section_1_hook)
    lines.append("")

    # Section 2: The Deep Dive
    lines.append("## The Deep Dive\n")
    deep_dive_md = format_deep_dive_markdown(content.section_2_deep_dive)

    # Try to add a contextual product mention after action steps
    product_mention = find_contextual_product_mention(
        tactic, content.section_2_deep_dive
    )
    if product_mention and product_mention.get("template"):
        # Add mention after the deep dive content
        deep_dive_md += f"\n\n{product_mention['template']}"

    lines.append(deep_dive_md)
    lines.append("")

    # Section 3: Tool of the Week
    lines.append(content.section_3_tool)
    lines.append("")

    # Section 4: The Prompt Drop
    prompt = content.section_4_prompt
    lines.append(
        f"## The Prompt Drop: {prompt.get('prompt_title', 'AI Accelerator')}\n"
    )
    lines.append("Copy and paste this into ChatGPT:\n")
    lines.append("```")
    lines.append(prompt.get("prompt_text", ""))
    lines.append("```\n")
    lines.append(f"**What you'll get:** {prompt.get('what_it_produces', '')}\n")
    lines.append(f"**How to customize:** {prompt.get('how_to_customize', '')}\n")
    if prompt.get("advanced_tip"):
        lines.append(f"**Pro tip:** {prompt.get('advanced_tip', '')}")
    lines.append("")

    # CTA for prompt library (links to Starter Pack)
    lines.append(
        "*Want 47 more prompts like this? [Get the AI Store Starter Pack →](https://dtcnews.com/starter-pack)*"
    )
    lines.append("")

    # Section 5: Your Next 24 Hours
    lines.append(content.section_5_action)
    lines.append("")

    # Sign off
    lines.append("---")
    lines.append("")
    lines.append("See you next week,")
    lines.append("The DTC Edge Team")
    lines.append("")

    # PS teaser (generated from next viral content)
    teaser = (
        content.next_issue_teaser or "something big we're tracking in the DTC space"
    )
    lines.append(f"*PS: Next issue we're breaking down {teaser}.*")

    return "\n".join(lines)


def run_newsletter_generation(
    issue_number: int = 1,
    skip_sponsor_prompt: bool = False,
    sponsor_config: Optional[SponsorConfig] = None,
    verbose: bool = True,
) -> NewsletterContent:
    """
    Run the complete newsletter generation pipeline.

    Args:
        issue_number: Newsletter issue number
        skip_sponsor_prompt: Skip interactive sponsor questions
        sponsor_config: Pre-configured sponsor settings
        verbose: Print progress

    Returns:
        NewsletterContent with complete newsletter
    """
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Step 0: Get sponsor configuration
    if sponsor_config:
        config_sponsor = sponsor_config
    elif skip_sponsor_prompt:
        config_sponsor = SponsorConfig(has_sponsor=False)
    else:
        config_sponsor = ask_sponsor_questions()

    config = NewsletterConfig(
        issue_number=issue_number, sponsor_config=config_sponsor, date=date_str
    )

    # Step 1: Find the viral edge (and next issue teaser)
    viral_edge, next_viral = find_viral_edge(verbose=verbose)

    # Step 2: Generate deep dive
    if verbose:
        print("\n" + "=" * 60)
        print("STEP 2: GENERATING DEEP DIVE")
        print("=" * 60)

    deep_dive = generate_deep_dive(viral_edge)

    if verbose:
        print(f"\n  Headline: {deep_dive.get('headline', '')[:60]}...")

    # Extract the tactic for tool research
    tactic = deep_dive.get("headline", "") or viral_edge.get("title", "")
    # Simplify to core tactic
    what_they_did = deep_dive.get("what_they_did", [])
    if what_they_did:
        tactic = what_they_did[0].get("tactic", tactic)

    # Step 3: Research tools for this tactic
    if verbose:
        print("\n" + "=" * 60)
        print("STEP 3: RESEARCHING TOOLS")
        print("=" * 60)
        print(f"\n  Tactic: {tactic}")

    tool_research = run_tool_research(tactic, config_sponsor, verbose=verbose)

    # Step 4: Generate all sections
    if verbose:
        print("\n" + "=" * 60)
        print("STEP 4: GENERATING SECTIONS")
        print("=" * 60)

    client = ClaudeClient()

    # Section 1: Hook
    if verbose:
        print("\n  Generating Section 1: This Week's Win...")
    section_1 = generate_section_1_hook(viral_edge, deep_dive, client)

    # Section 3: Tool (already have tool_research)
    if verbose:
        print("  Formatting Section 3: Tool of the Week...")
    section_3 = format_tool_section(tool_research, config_sponsor)

    # Section 4: Prompt
    if verbose:
        print("  Generating Section 4: The Prompt Drop...")
    section_4 = generate_section_4_prompt(tactic, deep_dive, tool_research, client)

    # Section 5: Action
    if verbose:
        print("  Generating Section 5: Your Next 24 Hours...")
    section_5 = generate_section_5_action(
        tactic, deep_dive, tool_research, section_4, client
    )

    # Subject and preview
    if verbose:
        print("  Generating subject line and preview...")
    subject, preview = generate_subject_and_preview(
        viral_edge, deep_dive, issue_number, client
    )

    # PS teaser for next issue
    if verbose:
        print("  Generating PS teaser...")
    ps_teaser = generate_ps_teaser(next_viral, client)

    # Record topic for deduplication
    record_topic(
        topic=deep_dive.get("headline", "") or tactic,
        issue_number=issue_number,
        headline=deep_dive.get("headline"),
        source_content=viral_edge.get("title"),
    )

    # Assemble content
    content = NewsletterContent(
        config=config,
        viral_edge=viral_edge,
        tactic=tactic,
        section_1_hook=section_1,
        section_2_deep_dive=deep_dive,
        section_3_tool=section_3,
        section_4_prompt=section_4,
        section_5_action=section_5,
        subject_line=subject,
        preview_text=preview,
        generated_at=datetime.now(timezone.utc).isoformat(),
        next_issue_teaser=ps_teaser,
    )

    return content


def main():
    parser = argparse.ArgumentParser(
        description="Generate a complete newsletter from viral edge to final copy",
    )
    parser.add_argument(
        "--issue",
        "-i",
        type=int,
        default=1,
        help="Issue number (default: 1)",
    )
    parser.add_argument(
        "--skip-sponsor",
        action="store_true",
        help="Skip sponsor questions (for testing)",
    )
    parser.add_argument(
        "--sponsor",
        help="Sponsor name (skips interactive prompt)",
    )
    parser.add_argument(
        "--angle",
        help="Sponsor positioning angle",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path",
    )
    args = parser.parse_args()

    print(f"[newsletter_orchestrator] v{DOE_VERSION}")
    print(f"Generating Issue #{args.issue}")

    # Build sponsor config if provided via CLI
    sponsor_config = None
    if args.sponsor:
        sponsor_config = SponsorConfig(
            has_sponsor=True, sponsor_name=args.sponsor, specific_angle=args.angle
        )

    # Run generation
    content = run_newsletter_generation(
        issue_number=args.issue,
        skip_sponsor_prompt=args.skip_sponsor,
        sponsor_config=sponsor_config,
        verbose=True,
    )

    # Format newsletter
    newsletter_md = format_full_newsletter(content, tactic=content.tactic)

    # Save
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_path = Path("output/newsletters") / f"{date_str}-issue-{args.issue}.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write(newsletter_md)

    # Also save JSON data
    json_path = output_path.with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump(
            {
                "config": asdict(content.config),
                "viral_edge": content.viral_edge,
                "deep_dive": content.section_2_deep_dive,
                "tool_research": content.section_3_tool,
                "prompt": content.section_4_prompt,
                "subject_line": content.subject_line,
                "preview_text": content.preview_text,
                "generated_at": content.generated_at,
            },
            f,
            indent=2,
            default=str,
        )

    # Extract sources for fact-checking
    sources = []
    viral_edge = content.viral_edge
    if viral_edge:
        sources.append(
            Source(
                url=viral_edge.get("url", viral_edge.get("link", "")),
                title=viral_edge.get("title", "Primary source"),
                accessed_at=datetime.now(timezone.utc).isoformat(),
                content_type=viral_edge.get("source", "article"),
                quote=viral_edge.get("results", viral_edge.get("summary", "")[:200]),
            )
        )

    # Add tool research sources if available
    tool_info = content.section_3_tool
    if isinstance(tool_info, str) and "**Our Recommendation:" in tool_info:
        # Extract tool name from the formatted string
        pass  # Tool sources handled separately

    # Save to publishing/drafts
    pub_metadata = PublishingMetadata(
        issue_number=args.issue,
        status="draft",
        subject_line=content.subject_line,
        preview_text=content.preview_text,
        viral_edge_title=viral_edge.get("title", "") if viral_edge else "",
        tactic=content.tactic,
        sponsor_name=args.sponsor,
        sponsor_angle=args.angle,
    )

    draft_path = save_draft(newsletter_md, pub_metadata, sources)

    # Display results
    print("\n" + "=" * 60)
    print("NEWSLETTER GENERATED!")
    print("=" * 60)

    print(f"\nSubject: {content.subject_line}")
    print(f"Preview: {content.preview_text}")

    print(f"\nSaved to:")
    print(f"  - Draft: {draft_path}")
    print(f"  - Output: {output_path}")
    print(f"  - JSON: {json_path}")

    print(f"\nSources tracked: {len(sources)}")
    print("\nNext steps:")
    print("  1. Review draft in publishing/drafts/")
    print("  2. Fact-check sources at bottom of file")
    print(
        f"  3. Approve: python execution/publishing_manager.py --approve {args.issue}"
    )

    print("\n" + "-" * 60)
    print("PREVIEW:")
    print("-" * 60)
    print(newsletter_md[:2000] + "..." if len(newsletter_md) > 2000 else newsletter_md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
