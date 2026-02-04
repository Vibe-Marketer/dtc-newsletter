# DTCNews AI Newsletter System v2
## Integrated Skills, Agents & SOP Leveraging Existing Infrastructure

---

## EXECUTIVE SUMMARY

This system builds on the **existing robust infrastructure** to produce two high-quality newsletter issues per week targeting **beginner ecommerce entrepreneurs** with 90-99% AI execution.

### What Already Exists (Leverage These)
| Component | Script | Status |
|-----------|--------|--------|
| Content Aggregation | `execution/content_aggregate.py` | Ready |
| Newsletter Generation | `execution/newsletter_generator.py` | Ready |
| Subject Line Generator | `execution/subject_line_generator.py` | Ready |
| Voice Profile (Hormozi/Suby) | `execution/voice_profile.py` | Ready |
| Content Selector | `execution/content_selector.py` | Ready |
| Anti-pattern Validator | `execution/anti_pattern_validator.py` | Ready |
| Virality Analyzer | `execution/virality_analyzer.py` | Ready |
| Outlier Scoring | `execution/scoring.py` | Ready |
| Pain Point Miner | `execution/pain_point_miner.py` | Ready |
| Product Factory | `execution/product_factory.py` | Ready |
| Pipeline Runner | `execution/pipeline_runner.py` | Ready |

### What Needs to Be Built (New for DTCNews)
| Component | Purpose | Priority |
|-----------|---------|----------|
| Beginner Filter Skill | Filter content for 0-10 sales audience | Critical |
| AI Prompt Extractor | Extract/create AI prompts from tactics | Critical |
| Copy Review Agent (100M Hooks) | Apply Hormozi hook framework | High |
| Copy Review Agent (Schwartz) | Apply Breakthrough Advertising principles | High |
| Editor Agent | Final polish and deliverability check | High |
| Product Integration Agent | Natural product mention insertion | Medium |

---

## PART 1: EXISTING INFRASTRUCTURE GUIDE

### 1.1 Pipeline Runner - The Master Orchestrator

**What it does:** Runs the complete newsletter pipeline in one command.

```bash
# Full pipeline with auto-detected topic
python execution/pipeline_runner.py

# Specify topic for this issue
python execution/pipeline_runner.py --topic "product research with AI"

# Skip affiliate discovery (use internal products only)
python execution/pipeline_runner.py --skip-affiliates
```

**Output:**
- Newsletter: `output/newsletters/YYYY-MM/{issue}-{topic}.md`
- Index: `output/newsletters/index.json`
- Cost log: `data/cost_log.json`

---

### 1.2 Content Aggregation - Source of Raw Material

**What it does:** Fetches content from Reddit, YouTube, Twitter, TikTok, Amazon.

```bash
# Core sources (Reddit + YouTube)
python execution/content_aggregate.py

# Include stretch sources (Twitter, TikTok, Amazon)
python execution/content_aggregate.py --include-stretch

# Higher quality threshold
python execution/content_aggregate.py --min-score 3.0
```

**Key Parameters:**
- `--sources reddit,youtube` - Core sources
- `--include-stretch` - Add Twitter, TikTok, Amazon via Apify
- `--min-score 2.0` - Minimum outlier score (default)
- `--subreddits shopify,dropship,ecommerce` - Target subreddits

**Output:** `output/content_sheet.csv` and `output/content_sheet.json`

---

### 1.3 Virality Analyzer - Why Content Goes Viral

**What it does:** Analyzes hooks, emotional triggers, and success factors.

**Schema Output:**
```python
{
    "hook_analysis": {
        "hook_type": "question|statement|number|controversy|story",
        "hook_text": "The actual hook",
        "attention_elements": ["money", "exclusivity", "speed", "specificity"]
    },
    "emotional_triggers": [
        {"trigger": "fear|greed|curiosity|urgency|fomo|hope", "evidence": "...", "intensity": "high|medium|low"}
    ],
    "virality_confidence": "definite|likely|possible|unclear",
    "replication_notes": "How to replicate this success"
}
```

**Usage:** Already integrated into content_aggregate.py - automatically analyzes all content.

---

### 1.4 Content Selector - Matching Content to Sections

**What it does:** Automatically selects best content for each newsletter section.

**Selection Logic:**
- **Section 2 (The Meat):** Tactical content with how-to, strategy, step-by-step keywords
- **Section 3 (Breakdown):** Narrative content with story, journey, lessons keywords
- **Section 1 (Hook):** Quotable content with stats, numbers, punchy titles

**Diversity Constraint:** Requires at least 2 different sources across sections.

**Usage:** Already integrated into newsletter_generator.py.

---

### 1.5 Voice Profile - Hormozi/Suby Hybrid

**What it does:** Enforces consistent voice across all content.

**Key Rules (from `voice_profile.py`):**
- **Sentence length:** 60% short (<10 words), 30% medium (10-18), 10% long (>18)
- **Average:** 8-12 words per sentence
- **Zero fluff:** No "basically," "essentially," "just," "really"
- **28 anti-patterns blocked:** game-changer, unlock potential, leverage, synergy, etc.

**Section Guidelines:**
| Section | Name | Word Count | Focus |
|---------|------|------------|-------|
| 1 | Instant Reward | 30-60 | Dopamine hit, quote/stat |
| 2 | What's Working Now | 300-500 | THE MEAT - tactical |
| 3 | The Breakdown | 200-300 | Story-sell bridge |
| 4 | Tool of the Week | 100-200 | Insider friend energy |
| 5 | PS Statement | 20-40 | Foreshadow/CTA/meme |

---

### 1.6 Subject Line Generator - 70/20/10 Rotation

**What it does:** Creates validated subject lines under 50 chars.

**Format:** `DTC Money Minute #X: lowercase curiosity hook`

**Style Rotation:**
- 70% curiosity-driven
- 20% direct benefit (when you have hard numbers)
- 10% question format

**Validation Constraints:**
- Under 50 characters total
- Lowercase after colon
- Zero emojis
- No ALL CAPS words
- Never start with "How to"

---

### 1.7 Anti-Pattern Validator - Voice Compliance

**What it does:** Validates content against 28+ forbidden phrases.

**Banned Categories:**
- **Buzzword Garbage:** game-changer, unlock potential, leverage, synergy, dive deep
- **Throat-Clearing:** it's worth noting, interestingly enough, without further ado
- **Corporate Cringe:** take it to the next level, move the needle, low-hanging fruit
- **Motivational Mush:** empower, revolutionize, transform your business, secret sauce
- **Bro Marketing:** crushing it, killing it
- **Fake Enthusiasm:** I'm excited to share, I'm thrilled to announce

**Also Checks:**
- Excessive exclamation points (max 1)
- Sentences starting with "So," or "Look,"

---

### 1.8 Product Factory - Create Products from Pain Points

**What it does:** Generates digital products from Reddit pain points.

```bash
# Discover pain points
python -m execution.product_factory --discover --limit 10

# Create product
python -m execution.product_factory --create \
  --type html_tool \
  --name "AI Product Description Generator" \
  --problem "Beginners struggle to write product descriptions" \
  --audience "New Shopify store owners with 0-10 sales" \
  --benefits "Generate descriptions in 30 seconds,No copywriting skills needed,Works for any product"
```

**Product Types:**
| Type | Creates | Price Range |
|------|---------|-------------|
| html_tool | Single-file calculator/generator | $27-47 |
| automation | Python script + docs | $47-97 |
| gpt_config | GPT instructions + setup guide | $27-47 |
| sheets | Google Sheets template | $27-47 |
| pdf | Styled PDF framework | $17-37 |
| prompt_pack | Curated prompts + examples | $17-27 |

---

### 1.9 Pain Point Miner - Find Real Problems

**What it does:** Searches Reddit for e-commerce complaints.

**Keywords Searched:**
- Frustration signals: "frustrated with shopify", "hate my shopify", "sick of"
- Help-seeking: "struggling with ecommerce", "can't figure out", "how do i fix"
- Specific pains: "conversion rate low", "cart abandonment", "ads not converting"

**Subreddits:**
- shopify, ecommerce, dropship, Entrepreneur, smallbusiness, FulfillmentByAmazon

**Categories:**
- shipping, inventory, conversion, returns, pricing, marketing, other

---

## PART 2: NEW SKILLS TO BUILD FOR DTCNEWS

### Skill 2.1: Beginner Filter (CRITICAL)

**Purpose:** Filter all content for 0-10 sales relevance

**Why Needed:** Existing pipeline targets "100K+ subscribers, 80%+ new to ecommerce" - need to ensure content is truly beginner-accessible.

**Filter Criteria:**
```python
BEGINNER_SIGNALS = {
    "positive": [
        "first sale", "getting started", "beginner", "new to", "how to start",
        "step by step", "simple", "easy", "basic", "without experience",
        "no budget", "free", "cheap", "$0", "zero cost"
    ],
    "negative": [
        "scaling", "7 figures", "million dollar", "advanced", "enterprise",
        "$100k+", "growing from", "optimization", "at scale"
    ]
}

def is_beginner_friendly(content: dict) -> tuple[bool, float]:
    """
    Returns (is_beginner_friendly, beginner_score 0-10)
    Score 7+ = definitely beginner friendly
    Score 4-6 = could work with simplification
    Score <4 = too advanced
    """
```

**Integration Point:** Add to `content_selector.py` as pre-filter.

---

### Skill 2.2: AI Prompt Extractor (CRITICAL)

**Purpose:** Extract or create copy-paste AI prompts from any tactic

**Why Needed:** Every issue needs "The Prompt Drop" section - a ready-to-use prompt.

**Input:** Tactical content from Deep Dive
**Output:** 
```python
{
    "prompt_text": "Copy-paste ready prompt under 150 words",
    "what_it_produces": "One sentence description",
    "how_to_customize": "What to change in [BRACKETS]",
    "advanced_variation": "Power user enhancement"
}
```

**Implementation:**
```python
def extract_or_create_prompt(tactic_content: str, client: ClaudeClient) -> dict:
    """
    1. If tactic mentions a specific prompt, extract and clean it
    2. If no prompt exists, generate one that would execute this tactic
    3. Validate prompt is under 150 words
    4. Add customization brackets and tips
    """
```

**Integration Point:** New module `execution/prompt_extractor.py`

---

### Skill 2.3: Copy Review Agent - 100M Hooks Framework

**Purpose:** Apply Hormozi's 121 hooks database to improve content

**Review Dimensions:**
1. **Hook Strength** (0-10)
   - Does it grab in <3 seconds?
   - Clear call-out (who this is for)?
   - Condition for value (why consume)?

2. **Hook Type Optimization**
   - Labels: "[Beginners], I have a gift for you"
   - Questions: "Would you pay $10 to get your first sale?"
   - Conditionals: "If you're staring at an empty store..."
   - Commands: "Read this before writing another product description"
   - Statements: "The AI prompt that replaced my $500 copywriter"
   - Stories: "I watched a beginner get 3 sales in 24 hours doing this"

3. **Subject Line Rewrite Suggestions**
   - Generate 5 alternatives using top Hormozi patterns
   - Score each against 121 hooks database

**Implementation:**
```python
HORMOZI_HOOKS_DB = [
    # From 100m_hooks.md - all 121 hooks
    {"text": "Real quick question...", "type": "question", "performance": "top_ad"},
    {"text": "The rumors are true...", "type": "statement", "performance": "top_ad"},
    # ... all 121
]

def review_with_hormozi_framework(content: str, section: str) -> dict:
    """
    Returns:
    - hook_score: 0-10
    - hook_type_detected: str
    - improvements: list[dict] with specific rewrites
    - best_match_from_db: closest performing hook
    """
```

---

### Skill 2.4: Copy Review Agent - Schwartz Framework

**Purpose:** Apply Breakthrough Advertising principles

**Review Dimensions:**

1. **Awareness Stage Match**
   - Our audience: Problem Aware to Solution Aware
   - Check: Are we meeting them there (not assuming they know us)?
   - Fix: Adjust copy to match stage

2. **Market Sophistication Check**
   - Our market: Stage 1-2 (AI + Beginner Ecom is relatively new)
   - Implication: Direct claims still work, mechanism not required yet

3. **Verbalization Strength**
   Apply 38 techniques to weak claims:
   - Measure the size: Add specific numbers
   - Measure the speed: Add timeframes
   - Compare: "Instead of X, you get Y"
   - Metaphorize: Make abstract concrete
   - Demonstrate: Show prime example

4. **Three Dimensions Check**
   - DESIRES: Are we intensifying their desire for results?
   - IDENTIFICATIONS: Are we showing who they become?
   - BELIEFS: Are we working within existing beliefs?

**Implementation:**
```python
VERBALIZATION_TECHNIQUES = [
    {"name": "measure_size", "example": "20,000 FILTER TRAPS IN VICEROY!"},
    {"name": "measure_speed", "example": "IN TWO SECONDS, BAYER ASPIRIN BEGINS TO DISSOLVE"},
    # ... all 38
]

def review_with_schwartz_framework(content: str) -> dict:
    """
    Returns:
    - awareness_stage_match: 0-10
    - sophistication_appropriate: bool
    - weak_claims: list[dict] with strengthened versions
    - dimension_coverage: {"desires": bool, "identifications": bool, "beliefs": bool}
    """
```

---

### Skill 2.5: Editor Agent

**Purpose:** Final polish for clarity, tone, and deliverability

**Checks:**

1. **Reading Level**
   - Target: 6th-8th grade (Flesch-Kincaid)
   - Auto-simplify sentences over 20 words

2. **Jargon Detection**
   ```python
   ECOM_JARGON = [
       "ROAS", "AOV", "LTV", "CAC", "CPA", "CTR", "CVR",
       "funnel", "retargeting", "lookalike", "pixel"
   ]
   # Either explain inline or remove
   ```

3. **Spam Word Check**
   ```python
   SPAM_TRIGGERS = [
       "free", "act now", "limited time", "click here",
       "100%", "guarantee", "no obligation"
   ]
   # Flag for human review or auto-replace
   ```

4. **Deliverability Score**
   - Link-to-text ratio
   - Image count
   - Overall email length

5. **Final Formatting**
   - Section headers consistent
   - Bold on key phrases (not overused)
   - Visual breaks every 150-200 words

---

### Skill 2.6: Product Integration Agent

**Purpose:** Naturally weave product mentions into content

**Products to Integrate:**
| Product | Price | Best Sections | Natural Triggers |
|---------|-------|---------------|------------------|
| AI Store Starter Pack | $19 | 1, 4 (Prompt Drop) | "prompt", "AI", "GPT", "template" |
| First 10 Sales Sprint | $49-59 | 2, 5 (Deep Dive, PS) | "traffic", "ads", "sales", "customers" |
| Ecom Prompt & Template Vault | $19/4wk | 3, 4 (Tool) | "tool", "resource", "template" |

**Integration Rules:**
- 2-3 mentions per issue (1 soft, 1-2 medium)
- Never in opening (pure value first)
- Soft after Section 1: "This prompt is from our AI Store Starter Pack"
- Medium after Section 2: "Want the complete system? Grab [Product] ($XX)"
- Always in footer: All 3 products listed

**Implementation:**
```python
def insert_product_mentions(content: str, sections: dict) -> str:
    """
    1. Scan content for natural trigger words
    2. Insert mentions at appropriate places
    3. Ensure 2-3 mentions total
    4. Add footer with all products
    """
```

---

## PART 3: UNIFIED PIPELINE

### 3.1 Enhanced Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MONDAY / THURSDAY (Research Day)                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────┐                                       │
│  │ 1. content_aggregate.py  │  ← Existing                          │
│  │    --include-stretch     │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 2. Beginner Filter       │  ← NEW SKILL                          │
│  │    (filter for 0-10)     │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 3. content_selector.py   │  ← Existing (enhanced)                │
│  │    (match to sections)   │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 4. HUMAN REVIEW (5 min)  │  ← Checkpoint                         │
│  │    Select winner         │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 5. prompt_extractor.py   │  ← NEW SKILL                          │
│  │    (create Prompt Drop)  │                                       │
│  └──────────────────────────┘                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    TUESDAY / FRIDAY (Production Day)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────┐                                       │
│  │ 6. subject_line_gen.py   │  ← Existing                          │
│  │    (70/20/10 rotation)   │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 7. newsletter_gen.py     │  ← Existing                          │
│  │    (5-section assembly)  │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 8. Copy Review: Hormozi  │  ← NEW SKILL                          │
│  │    (121 hooks framework) │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 9. Copy Review: Schwartz │  ← NEW SKILL                          │
│  │    (Breakthrough Adv.)   │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 10. Product Integration  │  ← NEW SKILL                          │
│  │     (natural mentions)   │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 11. anti_pattern_valid.  │  ← Existing                          │
│  │     (voice compliance)   │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 12. Editor Agent         │  ← NEW SKILL                          │
│  │     (final polish)       │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 13. HUMAN REVIEW (10 min)│  ← Checkpoint                         │
│  │     Final approval       │                                       │
│  └───────────┬──────────────┘                                       │
│              │                                                       │
│              ▼                                                       │
│  ┌──────────────────────────┐                                       │
│  │ 14. Schedule in Beehiiv  │  ← Manual (no API)                    │
│  └──────────────────────────┘                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 3.2 Single Command Execution (Future State)

Once new skills are built, create enhanced pipeline:

```bash
# Full DTCNews pipeline
python execution/dtcnews_pipeline.py \
  --issue-number 1 \
  --topic "finding your first winning product" \
  --tool-name "TikTok Creative Center" \
  --tool-description "Free tool to spy on trending products" \
  --tool-why "See exactly what's selling before you source"

# Options
--beginner-threshold 7      # Minimum beginner score (default 7)
--skip-hormozi-review       # Skip 100M Hooks review
--skip-schwartz-review      # Skip Breakthrough Advertising review
--dry-run                   # Preview without saving
--verbose                   # Show all intermediate outputs
```

---

## PART 4: MASTER PROMPTS (UPDATED FOR DTCNEWS)

### Prompt 4.1: Beginner Filter

```xml
<task>Filter content for beginner relevance</task>

<context>
DTCNews targets 80% beginners with 0-10 sales who are:
- Building their first Shopify store
- Have little to no marketing experience
- Working with limited budgets ($100-500)
- Overwhelmed by conflicting information
- Want quick wins and AI shortcuts
</context>

<content_to_evaluate>
{content_json}
</content_to_evaluate>

<scoring_criteria>
BEGINNER-FRIENDLY SIGNALS (+points):
- Mentions "first sale", "getting started", "beginner" (+3)
- Step-by-step instructions (+2)
- No budget or low budget tactics (+2)
- AI/automation shortcuts (+2)
- Simple, actionable advice (+1)

TOO-ADVANCED SIGNALS (-points):
- Mentions "scaling", "7 figures", "$100k+" (-3)
- Requires existing traffic/customers (-2)
- Complex technical setup (-2)
- Advanced optimization tactics (-1)
</scoring_criteria>

<output_format>
{
  "beginner_score": 0-10,
  "is_beginner_friendly": true/false (score >= 7),
  "positive_signals": ["list of signals found"],
  "negative_signals": ["list of signals found"],
  "simplification_needed": true/false,
  "simplification_notes": "how to make this more beginner-friendly"
}
</output_format>
```

---

### Prompt 4.2: Prompt Extractor

```xml
<task>Create a copy-paste ChatGPT prompt from this tactic</task>

<context>
DTCNews readers are beginners who:
- May have never used ChatGPT for business
- Need prompts that work without customization
- Want immediate, tangible output
- Are building their first Shopify store
</context>

<tactic>
{tactic_content}
</tactic>

<requirements>
1. Prompt MUST be under 150 words
2. Include ONE variable in [BRACKETS] for customization
3. Output must be immediately useful (not educational)
4. Include clear output specification
5. Match the tactic's goal exactly
</requirements>

<output_format>
```
[EXACT PROMPT - COPY-PASTE READY]
```

**What it produces:** [One sentence]

**How to customize:** Replace [BRACKET] with [what]

**Advanced variation:** [One enhancement for power users]
</output_format>

<quality_check>
Before outputting, verify:
- [ ] Under 150 words
- [ ] One [BRACKET] variable only
- [ ] A beginner could use this right now
- [ ] Output is actionable (not advice)
</quality_check>
```

---

### Prompt 4.3: Copy Review - Hormozi Framework

```xml
<task>Review content using Alex Hormozi's 100M Hooks framework</task>

<content_to_review>
{content}
</content_to_review>

<hormozi_framework>
HOOK COMPONENTS:
1. CALL OUT - Gets prospect to say "This is for me"
2. CONDITION FOR VALUE - Why they should consume

HOOK TYPES (use variety):
- Labels: "[Audience], I have a gift for you"
- Questions: "Would you [desirable thing]?"
- Conditionals: "If you're [situation]..."
- Commands: "Read this if..."
- Statements: "The [thing] that [result]"
- Stories: "[Person] just [achieved result]"
- Paradox: "How a [unlikely person] [achieved result]"

TOP PERFORMING PATTERNS:
{insert_top_10_hormozi_hooks}
</hormozi_framework>

<review_dimensions>
1. HOOK STRENGTH (0-10)
   - Grabs attention in <3 seconds?
   - Clear who it's for?
   - Clear value promise?

2. TYPE ANALYSIS
   - What type is currently used?
   - What type would work better?

3. IMPROVEMENT SUGGESTIONS
   - Rewrite the hook using 3 different types
   - Show which top-performing pattern it could model
</review_dimensions>

<output_format>
## Hook Analysis
- **Current Score:** X/10
- **Hook Type:** [type]
- **Strengths:** [what works]
- **Weaknesses:** [what doesn't]

## Suggested Rewrites
1. [Label version]: "..."
2. [Question version]: "..."
3. [Statement version]: "..."

## Best Match from Database
"[top performing hook that's similar]" - [why it works]

## Priority Fix
[Single most impactful change to make]
</output_format>
```

---

### Prompt 4.4: Copy Review - Schwartz Framework

```xml
<task>Review content using Eugene Schwartz's Breakthrough Advertising principles</task>

<content_to_review>
{content}
</content_to_review>

<audience_context>
- AWARENESS STAGE: Problem Aware to Solution Aware
  (They know they want to make money online, started looking at Shopify, but overwhelmed)
- MARKET SOPHISTICATION: Stage 1-2
  (AI + Beginner Ecom is relatively new territory)
</audience_context>

<schwartz_framework>
KEY PRINCIPLES:

1. DESIRE CHANNELING
   - Cannot create desire, only channel existing desire
   - Their desires: income, freedom, validation, escape 9-5
   - Our job: Position product as inevitable destination

2. AWARENESS STAGE MATCH
   - Problem Aware: Start with the problem, lead to solution
   - Solution Aware: Start with solution, lead to our product
   - NEVER assume they know our product

3. VERBALIZATION (38 techniques)
   - Measure the size: Add specific numbers
   - Measure the speed: Add timeframes
   - Compare: "Instead of X, you get Y"
   - Metaphorize: Make abstract concrete
   - Demonstrate: Show prime example
   - State as paradox: "How a bald barber saved my hair"

4. THREE DIMENSIONS
   - DESIRES: Are we intensifying the want?
   - IDENTIFICATIONS: Are we showing who they become?
   - BELIEFS: Are we working within what they already believe?
</schwartz_framework>

<review_dimensions>
1. AWARENESS MATCH (0-10)
   - Does copy meet them at their stage?
   - Any assumptions about product knowledge?

2. CLAIM STRENGTH
   - Find weak/vague claims
   - Apply verbalization to strengthen

3. DIMENSION COVERAGE
   - Desire intensification present?
   - Identity transformation shown?
   - Existing beliefs leveraged?
</review_dimensions>

<output_format>
## Awareness Stage Analysis
- **Current Match:** X/10
- **Issues:** [where we assume too much]
- **Fixes:** [specific adjustments]

## Weak Claims Found
| Weak Claim | Verbalization Technique | Strengthened Version |
|------------|------------------------|---------------------|
| "get results" | Measure the size | "get 3 sales in your first week" |

## Dimension Coverage
- **Desires:** [Y/N] - [notes]
- **Identifications:** [Y/N] - [notes]
- **Beliefs:** [Y/N] - [notes]

## Priority Changes
1. [Most important fix]
2. [Second fix]
3. [Third fix]
</output_format>
```

---

### Prompt 4.5: Editor Agent

```xml
<task>Final edit for clarity, tone, and deliverability</task>

<content_to_edit>
{content}
</content_to_edit>

<audience>
Beginner ecommerce entrepreneurs (0-10 sales)
- Reading level: 6th-8th grade
- No assumed jargon knowledge
- Scanning on mobile
</audience>

<editing_checklist>
1. READING LEVEL
   - Target: Flesch-Kincaid 6th-8th grade
   - Max 20 words per sentence
   - Max 4 sentences per paragraph

2. JARGON CHECK
   Explain or remove:
   - ROAS, AOV, LTV, CAC, CPA, CTR, CVR
   - funnel, retargeting, lookalike, pixel
   - Any term a non-marketer wouldn't know

3. SPAM TRIGGERS
   Flag or replace:
   - "free" → "no-cost" or remove
   - "act now" → "try this today"
   - "limited time" → remove
   - "click here" → "check it out" or specific CTA

4. FORMATTING
   - Section headers present and consistent
   - Bold on key phrases (max 3 per section)
   - Visual breaks every 150-200 words
   - Links formatted properly

5. VOICE COMPLIANCE
   - Mentor-to-student tone
   - Encouraging, not condescending
   - No corporate speak
   - No excessive enthusiasm
</editing_checklist>

<output_format>
## Edited Content
[Full edited content with all changes applied]

## Change Log
| Location | Original | Changed To | Reason |
|----------|----------|------------|--------|
| Para 1 | "leverage your..." | "use your..." | Anti-pattern |

## Metrics
- Reading Level: [X grade]
- Word Count: [X] (target: 900-1,100)
- Spam Score: [X]% (target: <10%)

## Human Review Flags
[Any items requiring human decision]

## Confidence Score: X/10
</output_format>
```

---

### Prompt 4.6: Product Integration

```xml
<task>Insert natural product mentions into newsletter content</task>

<content>
{newsletter_content}
</content>

<products>
1. AI Store Starter Pack ($19)
   - What: GPTs and templates to launch first Shopify store in 7 days
   - Triggers: "prompt", "AI", "GPT", "template", "store setup"
   - Best sections: After Section 1, Prompt Drop

2. First 10 Sales Sprint ($49-59)
   - What: Get first 10 orders in 30 days using ads and AI
   - Triggers: "traffic", "ads", "sales", "customers", "orders"
   - Best sections: After Deep Dive, PS statement

3. Ecom Prompt & Template Vault ($19/4 weeks)
   - What: Monthly prompts, templates, teardowns
   - Triggers: "tool", "resource", "template", "weekly"
   - Best sections: Tool of the Week, footer
</products>

<integration_rules>
1. Total mentions: 2-3 per issue (1 soft, 1-2 medium)
2. NEVER in opening paragraph (pure value first)
3. Must feel natural, not forced
4. Don't interrupt flow

MENTION TYPES:
- SOFT: "This prompt is from our AI Store Starter Pack"
- MEDIUM: "Want the complete system? Grab [Product] ($XX)"
- STRONG: "Stop guessing. [Get the full playbook →]"

PLACEMENT:
- After Section 1 (Instant Reward): Soft mention
- After Section 2 (Deep Dive): Medium mention if relevant
- Section 4 (Tool): Vault mention
- Footer: All 3 products listed
</integration_rules>

<output_format>
## Content with Product Mentions
[Full content with naturally inserted mentions]

## Mentions Added
| Location | Product | Type | Text Used |
|----------|---------|------|-----------|
| After S1 | Starter Pack | Soft | "This prompt is from..." |

## Integration Score: X/10
(How natural do the mentions feel?)
</output_format>
```

---

## PART 5: WEEKLY SOP

### Monday (Issue 1 Research)

| Time | Task | Script/Skill | Human? |
|------|------|--------------|--------|
| 9:00 | Aggregate content | `content_aggregate.py --include-stretch` | No |
| 9:30 | Apply beginner filter | Beginner Filter Skill | No |
| 9:45 | Select content for sections | `content_selector.py` (enhanced) | No |
| 10:00 | **Review & select winner** | - | **5 min** |
| 10:15 | Extract/create prompt | Prompt Extractor Skill | No |
| 10:30 | Research phase complete | - | - |

### Tuesday (Issue 1 Production)

| Time | Task | Script/Skill | Human? |
|------|------|--------------|--------|
| 9:00 | Generate subject lines | `subject_line_generator.py` | No |
| 9:15 | **Select subject line** | - | **2 min** |
| 9:20 | Assemble newsletter | `newsletter_generator.py` | No |
| 10:00 | Hormozi hook review | Copy Review - Hormozi | No |
| 10:15 | Schwartz framework review | Copy Review - Schwartz | No |
| 10:30 | Insert product mentions | Product Integration | No |
| 10:45 | Anti-pattern validation | `anti_pattern_validator.py` | No |
| 11:00 | Final edit | Editor Agent | No |
| 11:30 | **Final human review** | - | **10 min** |
| 12:00 | Schedule in Beehiiv | Manual | 5 min |

### Tuesday 2:00 PM - Issue 1 Sends

### Thursday (Issue 2 Research)
*Same as Monday*

### Friday (Issue 2 Production)
*Same as Tuesday*

### Saturday 10:00 AM - Issue 2 Sends

---

## PART 6: IMPLEMENTATION ROADMAP

### Week 1: Foundation
- [ ] Test existing pipeline end-to-end
- [ ] Document any gaps in existing scripts
- [ ] Set up Beehiiv with tracking
- [ ] Create first issue manually using existing tools

### Week 2: Build New Skills
- [ ] Implement Beginner Filter Skill
- [ ] Implement Prompt Extractor Skill
- [ ] Implement Product Integration Skill
- [ ] Test new skills in isolation

### Week 3: Build Review Agents
- [ ] Implement Hormozi Copy Review
- [ ] Implement Schwartz Copy Review
- [ ] Implement Editor Agent
- [ ] Test full pipeline with new components

### Week 4: Integration & Launch
- [ ] Create unified `dtcnews_pipeline.py`
- [ ] Run 2 complete issues through system
- [ ] Measure human review time (target: <60 min/week)
- [ ] Go live with Issue #1

---

## PART 7: FILE STRUCTURE

```
/execution
  # EXISTING (leverage these)
  ├── content_aggregate.py
  ├── newsletter_generator.py
  ├── subject_line_generator.py
  ├── voice_profile.py
  ├── content_selector.py
  ├── anti_pattern_validator.py
  ├── virality_analyzer.py
  ├── scoring.py
  ├── pain_point_miner.py
  ├── product_factory.py
  ├── pipeline_runner.py
  
  # NEW (build these)
  ├── beginner_filter.py          ← NEW
  ├── prompt_extractor.py         ← NEW
  ├── copy_review_hormozi.py      ← NEW
  ├── copy_review_schwartz.py     ← NEW
  ├── product_integrator.py       ← NEW
  ├── editor_agent.py             ← NEW
  ├── dtcnews_pipeline.py         ← NEW (unified)

/directives
  # EXISTING
  ├── content_aggregate.md
  ├── newsletter_generate.md
  ├── pipeline_runner.md
  ├── product_factory.md
  
  # NEW
  ├── dtcnews_system.md           ← This document (directive version)
  ├── beginner_filter.md          ← NEW
  ├── copy_review.md              ← NEW

/data
  ├── hormozi_hooks_db.json       ← NEW (121 hooks)
  ├── schwartz_techniques.json    ← NEW (38 verbalization)
  ├── beginner_keywords.json      ← NEW
  ├── spam_triggers.json          ← NEW

/output
  ├── newsletters/
  │   └── YYYY-MM/
  │       └── {issue}-{topic}.md
  ├── content_sheet.json
  └── content_sheet.csv
```

---

## APPENDIX A: Quick Reference Commands

```bash
# === EXISTING COMMANDS ===

# Full existing pipeline
python execution/pipeline_runner.py

# Content aggregation only
python execution/content_aggregate.py --include-stretch

# Newsletter from content
python execution/newsletter_generator.py --content-file output/content_sheet.json --issue-number 1

# Pain point discovery
python -m execution.product_factory --discover

# === NEW COMMANDS (after building) ===

# Full DTCNews pipeline
python execution/dtcnews_pipeline.py --issue-number 1 --topic "product research"

# Beginner filter only
python execution/beginner_filter.py --input output/content_sheet.json --threshold 7

# Copy review only
python execution/copy_review_hormozi.py --input draft.md
python execution/copy_review_schwartz.py --input draft.md

# Editor only
python execution/editor_agent.py --input draft.md
```

---

## APPENDIX B: Hormozi Hooks Database (Top 20)

From 100m_hooks.md - use these for subject line generation and hook review:

```json
{
  "hooks": [
    {"text": "Real quick question...", "type": "question", "source": "ads"},
    {"text": "The rumors are true...", "type": "statement", "source": "ads"},
    {"text": "Would you pay $1,000 to have the business of your dreams in 30 days?", "type": "question", "source": "ads"},
    {"text": "Which would you rather be?", "type": "question", "source": "ads"},
    {"text": "Local business owners, I have a gift for you", "type": "label", "source": "ads"},
    {"text": "Read this if you're tired of being broke", "type": "command", "source": "ads"},
    {"text": "How to get ahead of 99% of people", "type": "statement", "source": "ads"},
    {"text": "The smartest thing you can do today", "type": "statement", "source": "ads"},
    {"text": "If you're working all the time and your business isn't growing, you're working on the wrong sh*t", "type": "conditional", "source": "IG"},
    {"text": "Poor people stay poor because they're afraid of other poor people judging them for trying to get rich", "type": "statement", "source": "IG"},
    {"text": "3 hacks to make life suck less", "type": "list", "source": "IG"},
    {"text": "The most miserable place in business is $1-3 million", "type": "statement", "source": "IG"},
    {"text": "Entrepreneurship f*cking sucks most of the time", "type": "statement", "source": "IG"},
    {"text": "Everyone wants the view from the top, but no one wants the climb", "type": "paradox", "source": "X"},
    {"text": "You just have to be willing to look like an idiot while you figure it out", "type": "statement", "source": "X"},
    {"text": "Anything worth doing takes a lot longer than you think", "type": "statement", "source": "X"},
    {"text": "Btw... (I have a favor to ask)", "type": "curiosity", "source": "email"},
    {"text": "I've got a new book", "type": "announcement", "source": "email"},
    {"text": "Only open this if you have a business and want to scale", "type": "conditional", "source": "email"},
    {"text": "We made a boo boo", "type": "curiosity", "source": "email"}
  ]
}
```

---

*Document Version: 2.0*
*Integrates existing infrastructure with new DTCNews-specific skills*
*Next: Build beginner_filter.py and prompt_extractor.py*
