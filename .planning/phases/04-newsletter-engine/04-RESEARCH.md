# Phase 4: Newsletter Engine - Research

**Researched:** 2026-01-31
**Domain:** LLM-based content generation, newsletter copywriting, voice style enforcement
**Confidence:** HIGH

## Summary

This phase implements a 5-section newsletter generator that transforms aggregated content into a complete, Beehiiv-ready markdown newsletter. The core challenge is not technical API integration (straightforward with Anthropic SDK) but rather **voice consistency** and **anti-pattern enforcement**.

The existing codebase already uses OpenAI-compatible APIs (Perplexity client), but we'll use the native Anthropic SDK for better prompt caching support and voice consistency. The key architectural insight: **treat the voice profile as cached context** that persists across section generation, reducing costs and ensuring consistency.

**Primary recommendation:** Use Anthropic Python SDK with prompt caching for the voice profile and anti-patterns list. Generate sections sequentially with shared context, not in parallel, to maintain narrative coherence.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | 0.75.0+ | Claude API client | Already installed; native SDK with prompt caching support |
| python-dotenv | 1.0.0+ | Environment config | Already in use for API keys |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| jinja2 | 3.1.0+ | Template rendering | Optional - for newsletter structure templates |
| pydantic | 2.0+ | Data validation | Structured output validation if using tool use |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Anthropic SDK | OpenAI SDK | OpenAI could work but lacks prompt caching; Anthropic SDK is already imported via pip |
| Sequential generation | Parallel sections | Parallel is faster but loses narrative coherence between sections |
| Raw API | LangChain | LangChain adds complexity; raw SDK is sufficient for this use case |

**Installation:**
```bash
pip install anthropic>=0.75.0
# Already have python-dotenv, no additional deps needed
```

## Architecture Patterns

### Recommended Project Structure
```
execution/
├── newsletter_generator.py     # Main orchestrator (NEWS-01 to NEWS-09)
├── voice_profile.py            # Voice profile data + anti-patterns list
├── section_generators.py       # Individual section generation functions
├── content_selector.py         # Logic to pick best content for each section
└── claude_client.py            # Anthropic API wrapper with prompt caching

data/
└── newsletters/
    └── [date]-draft.md         # Output location
```

### Pattern 1: Cached Voice Profile
**What:** Store the complete voice profile (guiding principles, sentence rhythm, anti-patterns) as a system prompt with `cache_control` set to ephemeral. This caches the ~2000+ tokens of voice instructions for reuse across all section generations.

**When to use:** Every newsletter generation run.

**Example:**
```python
# Source: Anthropic docs - prompt caching
import anthropic

client = anthropic.Anthropic()

# Voice profile is long (~2000+ tokens) - cache it
voice_system = [
    {
        "type": "text",
        "text": VOICE_PROFILE_PROMPT,  # Full Hormozi/Suby guidelines
        "cache_control": {"type": "ephemeral"}
    }
]

response = client.messages.create(
    model="claude-sonnet-4-5",  # Sonnet for cost/quality balance
    max_tokens=1024,
    system=voice_system,
    messages=[{"role": "user", "content": section_prompt}]
)
```

### Pattern 2: Sequential Section Generation with Context
**What:** Generate sections in order, passing prior sections as context to maintain narrative flow.

**When to use:** Sections 2-5 (Section 1 can be standalone).

**Example:**
```python
def generate_newsletter(aggregated_content: dict) -> dict:
    sections = {}
    
    # Section 1: Standalone
    sections["instant_reward"] = generate_section_1(aggregated_content)
    
    # Section 2: Uses Section 1 as context
    sections["whats_working"] = generate_section_2(
        aggregated_content, 
        prior_sections=sections
    )
    
    # Continue sequentially...
    return sections
```

### Pattern 3: Anti-Pattern Validation
**What:** Post-process generated content to detect and flag anti-patterns before final output.

**When to use:** Every generated section.

**Example:**
```python
ANTI_PATTERNS = [
    "game-changer", "unlock your potential", "leverage", "synergy",
    "dive deep", "unpack", "at the end of the day",
    # ... full list from CONTEXT.md
]

def validate_voice(content: str) -> tuple[bool, list[str]]:
    """Returns (is_valid, list_of_violations)."""
    violations = []
    content_lower = content.lower()
    for pattern in ANTI_PATTERNS:
        if pattern.lower() in content_lower:
            violations.append(pattern)
    return len(violations) == 0, violations
```

### Pattern 4: Subject Line Style Rotation
**What:** Track subject line style history and rotate per the 70/20/10 distribution.

**When to use:** Subject line generation (NEWS-07).

**Example:**
```python
import random

def select_subject_style(history: list[str] = None) -> str:
    """Returns 'curiosity', 'direct_benefit', or 'question'."""
    # If no history or building initial buffer, use weighted random
    weights = [0.70, 0.20, 0.10]
    styles = ["curiosity", "direct_benefit", "question"]
    return random.choices(styles, weights=weights)[0]
```

### Anti-Patterns to Avoid
- **Parallel section generation:** Loses narrative coherence; sections should reference each other
- **Hardcoded templates:** Use guiding principles, not rigid templates
- **Single-prompt generation:** Too much for one prompt; chain prompts for better quality
- **Ignoring anti-pattern validation:** LLMs occasionally slip; always validate output

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API rate limiting | Custom retry logic | anthropic SDK has built-in retries | SDK handles 429s, backoff automatically |
| Prompt templating | String concatenation | XML tags + f-strings | Claude parses XML reliably; messy concatenation causes errors |
| JSON output parsing | Regex extraction | Claude's tool_use or JSON mode | Structured outputs are reliable; regex is fragile |
| Token counting | Character estimation | anthropic.count_tokens() | Accurate counting prevents context overflow |

**Key insight:** The Anthropic SDK handles the hard parts (retries, streaming, token counting). Focus on prompt engineering and content selection, not infrastructure.

## Common Pitfalls

### Pitfall 1: Voice Drift Across Sections
**What goes wrong:** Section 1 sounds like Hormozi, Section 5 sounds like generic AI.
**Why it happens:** Each API call starts fresh without voice context.
**How to avoid:** Use prompt caching with voice profile in every call; pass prior sections as context.
**Warning signs:** Inconsistent sentence length distribution; anti-patterns appearing in later sections.

### Pitfall 2: Anti-Pattern Leakage
**What goes wrong:** LLM generates "game-changer" or "unlock your potential" despite instructions.
**Why it happens:** LLMs have strong priors from training data; explicit negation isn't always enough.
**How to avoid:** 
1. Include anti-patterns in system prompt with explicit "NEVER use these phrases"
2. Post-process with validation function
3. Regenerate if violations detected
**Warning signs:** Any phrase from the anti-patterns list in output.

### Pitfall 3: Subject Line Too Long
**What goes wrong:** Subject line exceeds 50 characters, gets truncated in inbox.
**Why it happens:** LLM focuses on curiosity hook, ignores length constraint.
**How to avoid:** 
1. Include length constraint prominently in prompt
2. Validate output length
3. Regenerate with stricter guidance if over limit
**Warning signs:** Generated subject line > 50 chars.

### Pitfall 4: Content Selection Favors Same Source
**What goes wrong:** All sections use Reddit content; YouTube/Perplexity ignored.
**Why it happens:** Greedy selection by outlier score without diversity consideration.
**How to avoid:** Implement diversity constraint - require at least 2 different sources in newsletter.
**Warning signs:** Same source URL appearing in multiple sections.

### Pitfall 5: Sparse Content Day
**What goes wrong:** No good content available, newsletter generation fails.
**Why it happens:** Some days have weak aggregated content.
**How to avoid:** Perplexity as fallback source; graceful degradation with quality warning.
**Warning signs:** All content items below 2x outlier score.

## Code Examples

Verified patterns from official sources:

### Basic Anthropic API Call
```python
# Source: docs.anthropic.com/en/api/client-sdks
import anthropic

client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system="You are a DTC newsletter writer with Hormozi's style.",
    messages=[
        {"role": "user", "content": "Write Section 1 based on: [content]"}
    ]
)

content = response.content[0].text
```

### Prompt Caching for Voice Profile
```python
# Source: docs.anthropic.com/en/docs/build-with-claude/prompt-caching
import anthropic

client = anthropic.Anthropic()

# Cache the voice profile (>1024 tokens required for caching)
VOICE_PROFILE = """
You are writing the DTC Money Minute newsletter.

## Voice: Hormozi/Suby Hybrid

### Sentence Rhythm
- Punch (3-6 words) -> Setup (12-18 words) -> Land it (3-6 words)
- Average: 8-12 words per sentence
- Never 25+ words unless story with payoff
- 60% short punches (under 10 words)
- 30% medium setups (10-18 words)
- 10% longer only when necessary

### Anti-Patterns (NEVER use these phrases)
- "game-changer", "unlock your potential", "leverage", "synergy"
- "dive deep", "unpack", "at the end of the day"
- "It's worth noting", "Interestingly enough"
- "In today's fast-paced world", "In the ever-evolving landscape"
- "Take it to the next level", "Move the needle"
- "Circle back", "Touch base", "Low-hanging fruit"
- "Empower", "Revolutionize", "Transform your business"
- "Secret sauce", "Silver bullet", "Holy grail"
- "Crushing it", "Killing it" (unless quoting someone)
- "I'm excited to share", "I'm thrilled to announce"
- Excessive exclamation points
- Starting sentences with "So," or "Look,"
- "Without further ado"

### Specificity
Use concrete numbers when available. Don't force them.

### Test
Read out loud. Out of breath = too long. Robotic = add flow.
"""

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": VOICE_PROFILE,
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[{"role": "user", "content": section_prompt}]
)

# Check cache usage
print(f"Cache read: {response.usage.cache_read_input_tokens}")
print(f"Cache write: {response.usage.cache_creation_input_tokens}")
```

### Structured Section Prompt with XML Tags
```python
# Source: docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags
SECTION_2_PROMPT = """
<task>
Generate Section 2: What's Working Now

This is THE MEAT of the newsletter. A single actionable tactic that solves a narrow, specific problem.
</task>

<requirements>
- 300-500 words
- Single actionable tactic, not bullet-point lists
- Problem -> Solution -> How-to structure
- Easy and simple to implement with direct, immediate impact
- Case study ONLY when it delivers an incredibly valuable lesson
</requirements>

<source_content>
{aggregated_content}
</source_content>

<output_format>
Write the section directly. No headers. Natural paragraph flow.
</output_format>
"""
```

### Content Selection Logic
```python
def select_content_for_sections(aggregated: list[dict]) -> dict:
    """Select best content for each section based on outlier score and fit."""
    
    # Sort by outlier score
    sorted_content = sorted(
        aggregated, 
        key=lambda x: x.get("outlier_score", 0), 
        reverse=True
    )
    
    selections = {}
    used_sources = set()
    
    # Section 2: Best tactical content (prioritize YouTube/Reddit)
    for item in sorted_content:
        if item["source"] in ["youtube", "reddit", "perplexity"]:
            if _is_tactical(item):
                selections["section_2"] = item
                used_sources.add(item["id"])
                break
    
    # Section 3: Best narrative content (different source if possible)
    for item in sorted_content:
        if item["id"] not in used_sources:
            if _has_narrative_potential(item):
                selections["section_3"] = item
                used_sources.add(item["id"])
                break
    
    # Section 1: High-engagement quote/stat
    for item in sorted_content:
        if _is_quotable(item):
            selections["section_1"] = item
            break
    
    return selections

def _is_tactical(item: dict) -> bool:
    """Check if content is tactical (how-to, actionable)."""
    keywords = ["how to", "step", "strategy", "tactic", "tip", "hack"]
    title = item.get("title", "").lower()
    return any(kw in title for kw in keywords)

def _has_narrative_potential(item: dict) -> bool:
    """Check if content can be turned into a story."""
    keywords = ["case study", "story", "journey", "learned", "mistake", "failed"]
    title = item.get("title", "").lower()
    return any(kw in title for kw in keywords)

def _is_quotable(item: dict) -> bool:
    """Check if content has a strong quotable element."""
    # Quote-worthy if short, punchy, or has stats
    return len(item.get("title", "")) < 100 or "$" in item.get("title", "")
```

### Subject Line Generator with Style
```python
def generate_subject_line(
    issue_number: int,
    main_topic: str,
    style: str = "curiosity"
) -> str:
    """Generate subject line with proper format.
    
    Format: DTC Money Minute #X: lowercase curiosity hook
    Constraint: <50 characters total
    """
    
    style_prompts = {
        "curiosity": "Create a curiosity-driven hook that makes the reader NEED to open",
        "direct_benefit": "State a specific, concrete benefit with numbers",
        "question": "Ask a question that challenges their assumptions"
    }
    
    prompt = f"""
    <task>Generate a subject line for DTC Money Minute #{issue_number}</task>
    
    <topic>{main_topic}</topic>
    
    <style>{style_prompts[style]}</style>
    
    <rules>
    - Format: DTC Money Minute #{issue_number}: [hook]
    - Hook must be lowercase after the colon
    - Zero emojis
    - No ALL CAPS words
    - TOTAL subject line under 50 characters
    - Never start hook with "How to"
    </rules>
    
    <output>Return ONLY the subject line, nothing else.</output>
    """
    
    # Generate and validate
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    
    subject = response.content[0].text.strip()
    
    # Validate length
    if len(subject) > 50:
        # Regenerate with stricter constraint
        return _regenerate_shorter(issue_number, main_topic, style)
    
    return subject
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single long prompt | Chained prompts with caching | 2024 | Better quality, lower cost |
| String templates | XML-tagged structured prompts | 2024 | More reliable parsing |
| Raw API calls | SDK with built-in retries | Always | Handles rate limits automatically |
| Hope-based anti-patterns | Explicit + validation | Always | Catches AI slip-ups |

**Deprecated/outdated:**
- Old Claude models (claude-2, claude-instant): Use claude-sonnet-4-5 for best cost/quality
- Manual rate limiting: SDK handles this automatically
- Streaming for single sections: Not needed; sections are short

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal section generation order**
   - What we know: Sequential maintains coherence; Section 1 can be standalone
   - What's unclear: Whether Section 5 (PS) should reference earlier sections or be independent
   - Recommendation: Test both approaches; start with independent PS

2. **Tool of the Week automation**
   - What we know: Section 4 needs "insider friend energy, not a pitch"
   - What's unclear: How to source tool recommendations automatically (Phase 5 concern)
   - Recommendation: For Phase 4, allow manual tool input; automate discovery in Phase 5

3. **Perplexity fallback threshold**
   - What we know: Perplexity fills gaps when content is weak
   - What's unclear: What outlier score threshold triggers fallback?
   - Recommendation: If no content >2x outlier, use Perplexity. Test and adjust.

## Sources

### Primary (HIGH confidence)
- Anthropic SDK docs (docs.anthropic.com) - API usage, prompt caching, prompt engineering
- Existing codebase - perplexity_client.py patterns, test structure, storage patterns
- 04-CONTEXT.md - User decisions on voice, format, section structure

### Secondary (MEDIUM confidence)
- Anthropic prompt engineering guides - XML tags, multishot prompting, chain of thought

### Tertiary (LOW confidence)
- General LLM content generation best practices - derived from experience, not specific sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Anthropic SDK documented, already installed
- Architecture: HIGH - Follows existing codebase patterns + Anthropic best practices
- Pitfalls: HIGH - Derived from documented anti-patterns + common LLM issues
- Voice enforcement: MEDIUM - Requires testing to validate anti-pattern detection works

**Research date:** 2026-01-31
**Valid until:** 2026-02-28 (stable domain, 30-day validity)
