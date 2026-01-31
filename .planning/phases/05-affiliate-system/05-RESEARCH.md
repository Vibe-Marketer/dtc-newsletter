# Phase 5: Affiliate System - Research

**Researched:** 2026-01-31
**Domain:** Affiliate Discovery + Product Alternative Generation
**Confidence:** MEDIUM

## Summary

This phase implements a weekly affiliate discovery system that researches monetization opportunities based on each newsletter's specific topic. Unlike traditional affiliate systems with static partner lists, this system dynamically discovers relevant programs using Perplexity's web-grounded research API, then generates contextual pitch angles ready for Section 4 ("Tool of the Week").

The system outputs two parallel tracks: (1) Top 3 affiliate opportunities with commission rates and pitch angles, and (2) Top 3 product alternatives the user could create instead. This dual-track approach gives maximum optionality for monetization each week.

The standard approach is to use Perplexity's existing API (already integrated in the project) with structured JSON output to ensure consistent, parseable results. Pitch angle generation leverages Claude to match the Hormozi/Suby voice profile already defined in the project.

**Primary recommendation:** Use Perplexity for affiliate discovery research with JSON schema for structured output, Claude for pitch angle generation, and a simple commission rate threshold system (good/mediocre/poor) to help with decision-making.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openai (for Perplexity) | 1.x | Perplexity API client | Already in project, OpenAI-compatible API |
| anthropic | 0.x | Claude for pitch generation | Project standard for AI generation |
| pydantic | 2.x | Data validation/models | Already in project for type safety |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json | stdlib | Structured output parsing | Always - for Perplexity responses |
| pathlib | stdlib | File operations | Always - for caching |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Perplexity research | Direct web scraping | Scraping is fragile, violates TOS, less intelligent |
| Claude for pitches | Perplexity for pitches | Claude has better voice matching; Perplexity is for research |
| Manual affiliate networks | PartnerStack/Awin APIs | No public APIs for discovery; manual curation would defeat automation |

**Installation:**
```bash
# Already installed in project
pip install openai anthropic pydantic
```

## Architecture Patterns

### Recommended Module Structure
```
execution/
├── affiliate_discovery.py      # Core discovery logic
├── pitch_generator.py          # Pitch angle generation with Claude
├── product_alternatives.py     # Product idea generation
└── monetization_output.py      # Combined output formatter

data/
└── affiliate_cache/
    └── [date]-[topic]-affiliates.json  # Cached discoveries
```

### Pattern 1: Two-Stage Research with Structured Output
**What:** Use Perplexity for discovery research, then Claude for pitch refinement
**When to use:** Every affiliate discovery run
**Example:**
```python
# Stage 1: Perplexity discovers affiliate programs
def discover_affiliates(topic: str, newsletter_context: str) -> list[AffiliateResult]:
    """
    Use Perplexity with structured output to find relevant affiliate programs.
    """
    prompt = f"""Find the top affiliate programs relevant to "{topic}" for DTC e-commerce businesses.

For each program found, provide:
1. Program name and company
2. Commission rate (percentage or flat fee)
3. Product/service description
4. Why it fits this topic
5. Signup URL or affiliate network (ShareASale, Awin, PartnerStack, Impact, direct)

Focus on:
- Tools and SaaS products DTC brands actually use
- Programs with accessible signup (not closed/waitlisted)
- Recurring commission programs preferred over one-time
"""
    
    response = perplexity_client.chat.completions.create(
        model="sonar-pro",
        messages=[
            {"role": "system", "content": "You are an affiliate marketing researcher..."},
            {"role": "user", "content": prompt}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"schema": AFFILIATE_SCHEMA}
        }
    )
    return parse_affiliate_response(response)

# Stage 2: Claude generates pitch angles
def generate_pitch(affiliate: AffiliateResult, newsletter_context: str) -> str:
    """
    Generate a contextual pitch angle that fits Section 4 voice.
    """
    prompt = f"""Write a pitch for {affiliate.name} in the context of a newsletter about "{newsletter_context}".

Requirements:
- 2-3 sentences max
- Hormozi/Suby voice: concrete benefit, no fluff, math if applicable
- Reference the specific topic/problem from the newsletter
- Soft sell - feels like a recommendation, not an ad
- Ready to copy/paste into Section 4 "Tool of the Week"
"""
    return claude_generate(prompt)
```

### Pattern 2: Parallel Product Alternative Generation
**What:** While finding affiliates, also brainstorm products user could create
**When to use:** Every discovery run
**Example:**
```python
def generate_product_alternatives(topic: str, newsletter_context: str) -> list[ProductIdea]:
    """
    Generate product ideas that could replace affiliate recommendations.
    """
    prompt = f"""Based on the topic "{topic}" and DTC audience pain points, suggest 3 product ideas we could create instead of recommending an affiliate.

For each product:
1. Product concept (1 sentence)
2. Product type: HTML tool, automation, GPT, Google Sheet, PDF, or prompt pack
3. Estimated perceived value ($)
4. Build complexity: easy/medium/hard
5. Why it might beat affiliate option

Constraints:
- Target $27-97 price range
- Must solve a specific, narrow problem
- Prefer HTML tools and automations (per PROJECT.md)
"""
    # Use Perplexity for research + Claude for refinement
```

### Pattern 3: Commission Rate Thresholds
**What:** Classify commission rates as good/mediocre/poor for quick decision-making
**When to use:** Output formatting
**Example:**
```python
def classify_commission(rate: float, is_recurring: bool) -> str:
    """
    Classify commission rate quality.
    
    Thresholds based on industry standards:
    - One-time: good >= 20%, mediocre 10-20%, poor < 10%
    - Recurring: good >= 20%, mediocre 10-20%, poor < 10% (but recurring is inherently better)
    """
    if is_recurring:
        # Recurring commissions are more valuable
        if rate >= 20:
            return "excellent"  # 20%+ recurring is rare and valuable
        elif rate >= 10:
            return "good"
        else:
            return "mediocre"
    else:
        if rate >= 30:
            return "good"
        elif rate >= 15:
            return "mediocre"
        else:
            return "poor"
```

### Anti-Patterns to Avoid
- **Static affiliate lists:** Defeats the purpose of topic-relevant discovery
- **Scraping affiliate networks directly:** Violates TOS, breaks frequently
- **Auto-selecting monetization:** User must choose (per CONTEXT.md)
- **Generic pitches:** Each pitch must reference the specific newsletter topic

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Web research | Custom web scraper | Perplexity API | Grounded, cites sources, handles complexity |
| Affiliate database | Manual CSV/JSON | Perplexity discovery | Stale data problem, maintenance burden |
| Commission lookups | Network API wrappers | Perplexity research | No reliable public APIs exist |
| Voice matching | Rule-based templates | Claude generation | Voice is nuanced, needs AI |
| JSON parsing | Manual string parsing | Pydantic models | Type safety, validation |

**Key insight:** Affiliate program details (commission rates, accessibility) change frequently. Discovery-based approach stays current without maintenance. The research cost per run (~$0.02-0.05) is negligible compared to the value of accurate, timely information.

## Common Pitfalls

### Pitfall 1: Closed/Waitlisted Programs
**What goes wrong:** Perplexity returns programs that aren't actually accessible
**Why it happens:** Public info doesn't reflect current signup status
**How to avoid:** Add explicit instruction to verify accessibility in prompt; include fallback suggestions
**Warning signs:** "Apply to join," "waitlist," "invite only" in program descriptions

### Pitfall 2: Commission Rate Confusion
**What goes wrong:** Mixing percentage vs flat fee, one-time vs recurring
**Why it happens:** Different programs report differently
**How to avoid:** Require structured output with explicit fields for rate type and duration
**Warning signs:** "Up to X%" claims, missing duration info

### Pitfall 3: Generic vs Topic-Relevant Programs
**What goes wrong:** Perplexity returns general e-commerce affiliates instead of topic-specific ones
**Why it happens:** Prompt not specific enough about topic relevance
**How to avoid:** Include newsletter context in prompt; ask "why this fits THIS topic"
**Warning signs:** Same programs appearing regardless of topic

### Pitfall 4: Low/No Affiliate Availability
**What goes wrong:** Some topics have few relevant affiliate programs
**Why it happens:** Niche topics, non-tool-focused content
**How to avoid:** Design fallback strategy - lean toward product alternatives when affiliates scarce
**Warning signs:** Perplexity returns generic programs or few results

### Pitfall 5: Pitch Voice Drift
**What goes wrong:** Generated pitches don't match Hormozi/Suby voice
**Why it happens:** Claude defaults to generic marketing copy
**How to avoid:** Include specific voice examples in prompt; validation pass
**Warning signs:** Fluff words, passive voice, vague benefits

## Code Examples

Verified patterns from official sources and project conventions:

### Perplexity with Structured Output
```python
# Source: Perplexity docs + existing perplexity_client.py pattern
from openai import OpenAI
from pydantic import BaseModel
from typing import Literal

PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

class AffiliateProgram(BaseModel):
    name: str
    company: str
    commission_rate: str  # "20%" or "$50 per sale"
    commission_type: Literal["percentage", "flat_fee"]
    is_recurring: bool
    product_description: str
    topic_fit: str  # Why it fits this newsletter topic
    network: str  # ShareASale, Awin, PartnerStack, Impact, direct
    signup_accessible: bool

class AffiliateDiscoveryResult(BaseModel):
    affiliates: list[AffiliateProgram]
    search_citations: list[str]

def discover_affiliates(topic: str) -> AffiliateDiscoveryResult:
    client = OpenAI(
        api_key=os.getenv("PERPLEXITY_API_KEY"),
        base_url=PERPLEXITY_BASE_URL
    )
    
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=[
            {
                "role": "system",
                "content": "You are an affiliate marketing researcher for DTC e-commerce newsletters."
            },
            {
                "role": "user",
                "content": f"Find 5+ affiliate programs relevant to '{topic}' for DTC brands..."
            }
        ],
        # Note: response_format for Perplexity structured output
        # Uses same pattern as OpenAI but with Perplexity models
    )
    
    # Perplexity returns citations in completion object
    citations = getattr(response, "citations", []) or []
    content = response.choices[0].message.content
    
    # Parse JSON response
    return AffiliateDiscoveryResult.model_validate_json(content)
```

### Pitch Generation with Claude
```python
# Source: Existing pattern + PROJECT.md voice profile
import anthropic

def generate_pitch_angle(
    affiliate: AffiliateProgram,
    newsletter_topic: str,
    problem_context: str
) -> str:
    """
    Generate contextual pitch angle matching Hormozi/Suby voice.
    """
    client = anthropic.Anthropic()
    
    voice_guidance = """
    Voice requirements (Hormozi/Suby hybrid):
    - Short, punchy sentences (under 15 words typically)
    - Direct, confident, slightly irreverent tone
    - Specific numbers and math: "$X invested -> $Y returned"
    - Zero fluff - delete "basically," "essentially," "just"
    - Concrete, specific examples (never hypothetical)
    - 80% value / 20% ask ratio
    """
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": f"""Write a 2-3 sentence pitch for {affiliate.name} to include in a newsletter about "{newsletter_topic}".

Context: {problem_context}
Commission: {affiliate.commission_rate} ({affiliate.commission_type})

{voice_guidance}

Requirements:
- Reference the specific topic/problem
- Feel like a recommendation, not an ad
- Ready to copy/paste into "Tool of the Week" section
"""
            }
        ]
    )
    
    return message.content[0].text
```

### Output Formatting
```python
# Source: Project conventions from existing scripts
from dataclasses import dataclass
from typing import Literal

@dataclass
class MonetizationOption:
    """Single monetization option (affiliate or product)."""
    type: Literal["affiliate", "product"]
    name: str
    description: str
    pitch_angle: str
    
    # For affiliates
    commission_rate: str | None = None
    commission_quality: str | None = None  # good/mediocre/poor
    network: str | None = None
    
    # For products
    product_type: str | None = None  # HTML tool, automation, etc.
    build_complexity: str | None = None  # easy/medium/hard
    estimated_value: str | None = None

def format_output(
    affiliates: list[MonetizationOption],
    products: list[MonetizationOption],
    topic: str
) -> str:
    """Format as markdown for user review."""
    output = f"# Monetization Options: {topic}\n\n"
    
    output += "## Top 3 Affiliate Opportunities\n\n"
    output += "| # | Program | Commission | Quality | Pitch Preview |\n"
    output += "|---|---------|------------|---------|---------------|\n"
    for i, aff in enumerate(affiliates[:3], 1):
        pitch_preview = aff.pitch_angle[:50] + "..."
        output += f"| {i} | {aff.name} | {aff.commission_rate} | {aff.commission_quality} | {pitch_preview} |\n"
    
    output += "\n## Top 3 Product Alternatives\n\n"
    output += "| # | Concept | Type | Complexity | Value |\n"
    output += "|---|---------|------|------------|-------|\n"
    for i, prod in enumerate(products[:3], 1):
        output += f"| {i} | {prod.name} | {prod.product_type} | {prod.build_complexity} | {prod.estimated_value} |\n"
    
    output += "\n## Full Details\n\n"
    # Expanded details below...
    
    return output
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static affiliate lists | Dynamic discovery | Industry trend | More relevant recommendations |
| Manual research | AI-powered research | 2023-2024 | 10x faster, always current |
| Generic pitches | Contextual AI pitches | 2024 | Better conversion |
| Single monetization track | Dual track (affiliate + product) | Novel | More optionality |

**Deprecated/outdated:**
- ShareASale (merged into Awin October 2025) - use Awin instead
- Manual affiliate network lookups - too slow, stale data

## Open Questions

Things that couldn't be fully resolved:

1. **Perplexity Structured Output Reliability**
   - What we know: Perplexity supports JSON schema in response_format
   - What's unclear: Exact schema validation behavior vs OpenAI
   - Recommendation: Test with simple schema first, add retry logic for malformed responses

2. **Commission Rate Verification**
   - What we know: Perplexity can research current rates
   - What's unclear: How often rates change, accuracy of research
   - Recommendation: Include "verify before use" warning in output; consider caching with short TTL

3. **Low-Affiliate Topics Handling**
   - What we know: Some topics will have few relevant programs
   - What's unclear: Threshold for "few" - when to pivot to products
   - Recommendation: If <2 good affiliates found, emphasize product alternatives in output

## Sources

### Primary (HIGH confidence)
- Perplexity docs (https://docs.perplexity.ai) - Structured output, API patterns
- Project's existing perplexity_client.py - Established patterns
- Project's CONTEXT.md, PROJECT.md - Decisions, voice profile

### Secondary (MEDIUM confidence)
- Awin/PartnerStack websites - Affiliate network landscape, commission structures
- PartnerStack marketplace - Commission rate examples (10-50% range typical)

### Tertiary (LOW confidence)
- General knowledge of affiliate marketing - Industry patterns
- Training data on commission rate thresholds - Need validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Uses existing project libraries
- Architecture: HIGH - Follows existing patterns (Perplexity client, Claude generation)
- Pitfalls: MEDIUM - Based on domain knowledge, needs validation
- Commission thresholds: LOW - Needs user feedback to calibrate

**Research date:** 2026-01-31
**Valid until:** 2026-02-28 (30 days - stable domain, structured approach)

---

## Recommendations Summary

### For Planning

1. **Discovery Module** - Single function that takes topic + newsletter context, returns structured affiliate results using Perplexity
2. **Product Alternatives Module** - Parallel function that generates product ideas for same topic
3. **Pitch Generator** - Claude-based generator with voice profile baked in
4. **Output Formatter** - Markdown output with tables + expanded details per CONTEXT.md spec
5. **Caching** - Simple JSON file cache per topic/date to avoid redundant API calls

### Discretion Items (per CONTEXT.md)

- **Perplexity prompts:** Recommend multi-part prompt: (1) discover programs, (2) verify accessibility, (3) explain topic fit
- **Low affiliate handling:** If <2 good affiliates, output message recommending product path; don't force bad affiliates
- **Commission thresholds:** 
  - Recurring: excellent >=20%, good >=10%, mediocre <10%
  - One-time: good >=30%, mediocre >=15%, poor <15%
- **Caching:** 24-hour TTL per topic (affiliates don't change daily; saves API costs)
