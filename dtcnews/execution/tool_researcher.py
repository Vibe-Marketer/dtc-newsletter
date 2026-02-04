#!/usr/bin/env python3
"""
Tool researcher for DTCNews newsletter.
DOE-VERSION: 2026.02.04

Researches tools that help accomplish a specific tactic, finds:
- Free alternatives
- Paid options
- Comparisons and reviews
- Affiliate programs
- Social proof and endorsements

Handles sponsor/affiliate logic with "damaging admission" technique.

Usage:
    python execution/tool_researcher.py --tactic "AI video creation for ads"
    python execution/tool_researcher.py --tactic "email automation" --sponsor "Klaviyo"
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DOE_VERSION = "2026.02.04"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
SEARCH_MODEL = "perplexity/sonar"  # For web-grounded search
WRITING_MODEL = "anthropic/claude-sonnet-4"  # For crafting copy


@dataclass
class SponsorConfig:
    """Configuration for sponsor/affiliate handling."""

    has_sponsor: bool = False
    sponsor_name: Optional[str] = None
    specific_angle: Optional[str] = None
    # If no sponsor, we'll look for affiliate opportunities


@dataclass
class ToolOption:
    """A tool option with details."""

    name: str
    category: str  # "free" or "paid"
    description: str
    key_features: list[str]
    pricing: str
    best_for: str
    social_proof: Optional[str] = None
    website: Optional[str] = None
    affiliate_url: Optional[str] = None


@dataclass
class ToolResearch:
    """Complete tool research output."""

    tactic: str
    tool_category: str  # What kind of tool (e.g., "AI video generation")
    free_options: list[ToolOption]
    paid_options: list[ToolOption]
    recommendation: ToolOption
    recommendation_rationale: str
    damaging_admission: Optional[str] = None
    damaging_admission_counter: Optional[str] = None
    affiliate_opportunity: Optional[dict] = None
    comparisons_found: list[str] = None
    researched_at: str = None


def get_client() -> OpenAI:
    """Get OpenRouter client."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")
    return OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)


def research_tools_for_tactic(tactic: str, client: OpenAI) -> dict:
    """
    Research what tools help accomplish a specific tactic.

    Args:
        tactic: The tactic/strategy being taught
        client: OpenRouter client

    Returns:
        Dict with tool category, free options, paid options
    """
    prompt = f"""Research the best tools for: {tactic}

Find:
1. What CATEGORY of tool is needed (e.g., "AI video generation", "email marketing", etc.)
2. Top 3 FREE tools/options with:
   - Name
   - What it does
   - Key features (3 max)
   - Limitations
   - Best for whom
   
3. Top 3 PAID tools with:
   - Name
   - What it does
   - Key features (3 max)
   - Pricing (be specific)
   - Best for whom
   - Notable users/endorsements if known

4. Any comparison articles or reviews you found

Return as JSON:
{{
  "tool_category": "category name",
  "free_options": [
    {{
      "name": "Tool Name",
      "description": "What it does",
      "key_features": ["feature1", "feature2", "feature3"],
      "limitations": "Main limitation",
      "best_for": "Who should use this",
      "website": "URL"
    }}
  ],
  "paid_options": [
    {{
      "name": "Tool Name", 
      "description": "What it does",
      "key_features": ["feature1", "feature2", "feature3"],
      "pricing": "Specific pricing",
      "best_for": "Who should use this",
      "social_proof": "Used by X, endorsed by Y",
      "website": "URL"
    }}
  ],
  "comparison_sources": ["URL1", "URL2"]
}}

Return ONLY valid JSON."""

    completion = client.chat.completions.create(
        model=SEARCH_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a tool researcher. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    response = completion.choices[0].message.content or "{}"

    # Extract JSON
    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        return json.loads(json_match.group())
    return {}


def research_affiliate_program(tool_name: str, client: OpenAI) -> dict:
    """
    Research if a tool has an affiliate program.

    Args:
        tool_name: Name of the tool
        client: OpenRouter client

    Returns:
        Dict with affiliate info or None
    """
    prompt = f"""Research the affiliate program for: {tool_name}

Find:
1. Does {tool_name} have an affiliate/referral program?
2. If yes:
   - Commission rate/structure
   - Cookie duration
   - How to sign up (URL)
   - Any requirements
3. If no, are there alternative ways to earn (referral bonuses, etc.)?

Return as JSON:
{{
  "has_affiliate": true/false,
  "commission": "X% or $X per signup",
  "cookie_duration": "X days",
  "signup_url": "URL to apply",
  "requirements": "Any requirements",
  "notes": "Other relevant info"
}}

Return ONLY valid JSON."""

    completion = client.chat.completions.create(
        model=SEARCH_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are researching affiliate programs. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    response = completion.choices[0].message.content or "{}"

    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    return {"has_affiliate": False}


def research_tool_reviews(tool_name: str, client: OpenAI) -> dict:
    """
    Research reviews and common criticisms of a tool.

    Args:
        tool_name: Name of the tool
        client: OpenRouter client

    Returns:
        Dict with pros, cons, common complaints
    """
    prompt = f"""Research reviews and opinions about: {tool_name}

Find:
1. What do users LOVE about it? (top 3 positives)
2. What do users COMPLAIN about? (top 3 negatives/criticisms)
3. Overall sentiment (positive/mixed/negative)
4. Any notable endorsements or case studies?

Return as JSON:
{{
  "positives": ["pro1", "pro2", "pro3"],
  "negatives": ["con1", "con2", "con3"],
  "sentiment": "positive/mixed/negative",
  "endorsements": ["Company X uses it", "Endorsed by Y"],
  "notable_reviews": ["Source said X"]
}}

Return ONLY valid JSON."""

    completion = client.chat.completions.create(
        model=SEARCH_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are researching tool reviews. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    response = completion.choices[0].message.content or "{}"

    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    return {"positives": [], "negatives": [], "sentiment": "mixed"}


def craft_damaging_admission(
    tool_name: str, negatives: list[str], client: OpenAI
) -> tuple[str, str]:
    """
    Craft a "damaging admission" and counter for authenticity.

    The damaging admission technique: acknowledge a small flaw to build
    credibility, then pivot to show why benefits outweigh it.

    Args:
        tool_name: Tool being recommended
        negatives: List of negative points found
        client: OpenRouter client

    Returns:
        Tuple of (admission, counter)
    """
    if not negatives:
        return None, None

    prompt = f"""Create a "damaging admission" for recommending {tool_name}.

Known criticisms/negatives:
{json.dumps(negatives, indent=2)}

The "damaging admission" technique: Acknowledge ONE minor flaw honestly to build credibility,
then immediately counter with why the benefits far outweigh it.

Rules:
1. Pick the SMALLEST/most manageable negative
2. Acknowledge it honestly (don't dismiss it)
3. Provide a compelling counter that shows why it doesn't matter much
4. Keep it conversational, not salesy

Examples of good damaging admissions:
- "Look, [Tool] isn't cheap. But when you factor in the time saved..."
- "Some users mention the learning curve is steep at first. That said, once you get it..."
- "We've seen a few complaints about X, but honestly, that's far outweighed by..."

Return as JSON:
{{
  "admission": "The honest acknowledgment of the flaw",
  "counter": "Why it doesn't matter / benefits outweigh it"
}}

Return ONLY valid JSON."""

    completion = client.chat.completions.create(
        model=WRITING_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a conversion copywriter. Create authentic, non-salesy copy.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    response = completion.choices[0].message.content or "{}"

    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return data.get("admission"), data.get("counter")
        except:
            pass
    return None, None


def determine_recommendation(
    tactic: str,
    free_options: list[dict],
    paid_options: list[dict],
    sponsor_config: SponsorConfig,
    client: OpenAI,
) -> tuple[dict, str]:
    """
    Determine which tool to recommend based on sponsor config.

    Args:
        tactic: The tactic being taught
        free_options: List of free tool options
        paid_options: List of paid tool options
        sponsor_config: Sponsor/affiliate configuration
        client: OpenRouter client

    Returns:
        Tuple of (recommended_tool, rationale)
    """
    all_options = free_options + paid_options

    if sponsor_config.has_sponsor and sponsor_config.sponsor_name:
        # Find the sponsor in options or add them
        sponsor_tool = None
        for opt in all_options:
            if sponsor_config.sponsor_name.lower() in opt.get("name", "").lower():
                sponsor_tool = opt
                break

        if not sponsor_tool:
            # Research the sponsor tool specifically
            sponsor_tool = {
                "name": sponsor_config.sponsor_name,
                "category": "paid",
                "description": "Sponsor tool",
            }

        # Craft rationale based on angle
        if sponsor_config.specific_angle:
            angle_prompt = f"""Write a recommendation rationale for {sponsor_config.sponsor_name} 
            with this specific angle: {sponsor_config.specific_angle}
            
            Make it feel authentic, not salesy. Use specific benefits.
            Keep it to 2-3 sentences."""
        else:
            angle_prompt = f"""Write a recommendation rationale for {sponsor_config.sponsor_name}
            based on its advantages for: {tactic}
            
            Make it feel authentic, not salesy. Appear unbiased but lean towards the advantages.
            Keep it to 2-3 sentences."""

        completion = client.chat.completions.create(
            model=WRITING_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful newsletter writer. Be conversational and authentic.",
                },
                {"role": "user", "content": angle_prompt},
            ],
        )

        rationale = completion.choices[0].message.content or ""
        return sponsor_tool, rationale.strip()

    else:
        # No sponsor - genuinely recommend the best option
        prompt = f"""Given these tools for "{tactic}":

FREE OPTIONS:
{json.dumps(free_options, indent=2)}

PAID OPTIONS:
{json.dumps(paid_options, indent=2)}

Which ONE tool would you genuinely recommend for a BEGINNER ecommerce entrepreneur?
Consider: ease of use, value for money, effectiveness for the tactic.

Return as JSON:
{{
  "recommended_tool": "Tool Name",
  "category": "free or paid",
  "rationale": "2-3 sentence explanation of why this is the best choice"
}}"""

        completion = client.chat.completions.create(
            model=WRITING_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an unbiased tool reviewer. Recommend what's genuinely best.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        response = completion.choices[0].message.content or "{}"
        json_match = re.search(r"\{[\s\S]*\}", response)

        if json_match:
            data = json.loads(json_match.group())
            tool_name = data.get("recommended_tool", "")

            # Find the full tool info
            for opt in all_options:
                if tool_name.lower() in opt.get("name", "").lower():
                    return opt, data.get("rationale", "")

            # If not found, return first paid option as fallback
            if paid_options:
                return paid_options[0], data.get("rationale", "")
            return free_options[0], data.get("rationale", "")

        # Fallback
        return (
            paid_options[0] if paid_options else free_options[0]
        ), "This tool offers the best balance of features and value."


def run_tool_research(
    tactic: str, sponsor_config: SponsorConfig, verbose: bool = True
) -> ToolResearch:
    """
    Run complete tool research for a tactic.

    Args:
        tactic: The tactic/strategy being taught
        sponsor_config: Sponsor/affiliate configuration
        verbose: Print progress

    Returns:
        ToolResearch with complete findings
    """
    client = get_client()

    if verbose:
        print(f"Researching tools for: {tactic}")
        if sponsor_config.has_sponsor:
            print(f"  Sponsor: {sponsor_config.sponsor_name}")
            if sponsor_config.specific_angle:
                print(f"  Angle: {sponsor_config.specific_angle}")

    # Step 1: Research tools for the tactic
    if verbose:
        print("\n[1/5] Researching tool options...")
    tools_data = research_tools_for_tactic(tactic, client)

    free_options = tools_data.get("free_options", [])
    paid_options = tools_data.get("paid_options", [])
    tool_category = tools_data.get("tool_category", "tools")
    comparisons = tools_data.get("comparison_sources", [])

    if verbose:
        print(f"  Found {len(free_options)} free, {len(paid_options)} paid options")

    # Step 2: Determine recommendation
    if verbose:
        print("\n[2/5] Determining recommendation...")
    recommended, rationale = determine_recommendation(
        tactic, free_options, paid_options, sponsor_config, client
    )

    if verbose:
        print(f"  Recommending: {recommended.get('name', 'Unknown')}")

    # Step 3: Research reviews of recommended tool
    if verbose:
        print("\n[3/5] Researching reviews...")
    reviews = research_tool_reviews(recommended.get("name", ""), client)

    # Step 4: Craft damaging admission if needed
    damaging_admission = None
    damaging_counter = None
    if sponsor_config.has_sponsor or reviews.get("negatives"):
        if verbose:
            print("\n[4/5] Crafting damaging admission...")
        damaging_admission, damaging_counter = craft_damaging_admission(
            recommended.get("name", ""), reviews.get("negatives", []), client
        )
    else:
        if verbose:
            print("\n[4/5] Skipping damaging admission (no negatives found)")

    # Step 5: Research affiliate opportunity (if no sponsor)
    affiliate_info = None
    if not sponsor_config.has_sponsor:
        if verbose:
            print("\n[5/5] Researching affiliate opportunity...")
        affiliate_info = research_affiliate_program(recommended.get("name", ""), client)
        if verbose and affiliate_info.get("has_affiliate"):
            print(
                f"  Affiliate program found: {affiliate_info.get('commission', 'Unknown commission')}"
            )
    else:
        if verbose:
            print("\n[5/5] Skipping affiliate research (has sponsor)")

    # Build result
    result = ToolResearch(
        tactic=tactic,
        tool_category=tool_category,
        free_options=[
            ToolOption(
                name=opt.get("name", ""),
                category="free",
                description=opt.get("description", ""),
                key_features=opt.get("key_features", []),
                pricing="Free",
                best_for=opt.get("best_for", ""),
                website=opt.get("website"),
            )
            for opt in free_options
        ],
        paid_options=[
            ToolOption(
                name=opt.get("name", ""),
                category="paid",
                description=opt.get("description", ""),
                key_features=opt.get("key_features", []),
                pricing=opt.get("pricing", "Paid"),
                best_for=opt.get("best_for", ""),
                social_proof=opt.get("social_proof"),
                website=opt.get("website"),
            )
            for opt in paid_options
        ],
        recommendation=ToolOption(
            name=recommended.get("name", ""),
            category=recommended.get("category", "paid"),
            description=recommended.get("description", ""),
            key_features=recommended.get("key_features", []),
            pricing=recommended.get("pricing", ""),
            best_for=recommended.get("best_for", ""),
            social_proof=recommended.get("social_proof")
            or (
                ", ".join(reviews.get("endorsements", []))
                if reviews.get("endorsements")
                else None
            ),
            website=recommended.get("website"),
        ),
        recommendation_rationale=rationale,
        damaging_admission=damaging_admission,
        damaging_admission_counter=damaging_counter,
        affiliate_opportunity=affiliate_info
        if not sponsor_config.has_sponsor
        else None,
        comparisons_found=comparisons,
        researched_at=datetime.now(timezone.utc).isoformat(),
    )

    return result


def interactive_sponsor_prompt() -> SponsorConfig:
    """
    Interactive prompt to get sponsor configuration.

    Returns:
        SponsorConfig with user's choices
    """
    print("\n" + "=" * 50)
    print("SPONSOR/AFFILIATE CONFIGURATION")
    print("=" * 50)

    has_sponsor = (
        input("\nDo you have a sponsor/affiliate for this issue? (yes/no): ")
        .strip()
        .lower()
    )

    if has_sponsor in ["yes", "y", "1", "true"]:
        sponsor_name = input("Who is the sponsor? (tool name): ").strip()

        if sponsor_name:
            specific_angle = input(
                "Any specific angle/positioning? (or press Enter for none):\n"
                "  e.g., 'Position as #1 for beginners' or 'Highlight their new AI feature'\n"
                "> "
            ).strip()

            return SponsorConfig(
                has_sponsor=True,
                sponsor_name=sponsor_name,
                specific_angle=specific_angle if specific_angle else None,
            )

    return SponsorConfig(has_sponsor=False)


def main():
    parser = argparse.ArgumentParser(
        description="Research tools for a specific tactic",
    )
    parser.add_argument(
        "--tactic",
        "-t",
        required=True,
        help="The tactic/strategy to find tools for",
    )
    parser.add_argument(
        "--sponsor",
        "-s",
        help="Sponsor tool name (if any)",
    )
    parser.add_argument(
        "--angle",
        "-a",
        help="Specific positioning angle for sponsor",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Use interactive prompts for sponsor config",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file",
    )
    args = parser.parse_args()

    print(f"[tool_researcher] v{DOE_VERSION}")

    # Get sponsor config
    if args.interactive:
        sponsor_config = interactive_sponsor_prompt()
    elif args.sponsor:
        sponsor_config = SponsorConfig(
            has_sponsor=True, sponsor_name=args.sponsor, specific_angle=args.angle
        )
    else:
        sponsor_config = SponsorConfig(has_sponsor=False)

    # Run research
    result = run_tool_research(args.tactic, sponsor_config)

    # Display results
    print("\n" + "=" * 60)
    print("TOOL RESEARCH RESULTS")
    print("=" * 60)

    print(f"\nTactic: {result.tactic}")
    print(f"Tool Category: {result.tool_category}")

    print(f"\nFREE OPTIONS ({len(result.free_options)}):")
    for opt in result.free_options:
        print(f"  - {opt.name}: {opt.description[:60]}...")

    print(f"\nPAID OPTIONS ({len(result.paid_options)}):")
    for opt in result.paid_options:
        print(f"  - {opt.name} ({opt.pricing}): {opt.description[:50]}...")

    print(f"\nOUR RECOMMENDATION: {result.recommendation.name}")
    print(f"  Rationale: {result.recommendation_rationale}")

    if result.damaging_admission:
        print(f"\n  Damaging Admission: {result.damaging_admission}")
        print(f"  Counter: {result.damaging_admission_counter}")

    if result.social_proof:
        print(f"\n  Social Proof: {result.recommendation.social_proof}")

    if result.affiliate_opportunity and result.affiliate_opportunity.get(
        "has_affiliate"
    ):
        print(f"\nAFFILIATE OPPORTUNITY:")
        print(
            f"  Commission: {result.affiliate_opportunity.get('commission', 'Unknown')}"
        )
        print(
            f"  Sign up: {result.affiliate_opportunity.get('signup_url', 'Not found')}"
        )

    # Save output
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_path = Path("output") / f"tool_research_{date_str}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict for JSON serialization
    output_data = {
        "tactic": result.tactic,
        "tool_category": result.tool_category,
        "free_options": [asdict(opt) for opt in result.free_options],
        "paid_options": [asdict(opt) for opt in result.paid_options],
        "recommendation": asdict(result.recommendation),
        "recommendation_rationale": result.recommendation_rationale,
        "damaging_admission": result.damaging_admission,
        "damaging_admission_counter": result.damaging_admission_counter,
        "affiliate_opportunity": result.affiliate_opportunity,
        "comparisons_found": result.comparisons_found,
        "researched_at": result.researched_at,
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nSaved to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
