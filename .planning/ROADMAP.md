# Roadmap: DTC Newsletter Automation System

**Created:** 2026-01-29
**Phases:** 9
**Approach:** Modular Pipeline (DOE Framework)
**Estimated Duration:** 26-35 days

## Phase Overview

| # | Phase | Goal | Requirements | Est. Time |
|---|-------|------|--------------|-----------|
| 1 | Foundation | Storage + outlier scoring + Reddit | 5 | 2-3 days |
| 2 | Core Sources | TubeLab signup + YouTube + Perplexity | 6 | 3-4 days |
| 3 | Stretch Sources | TikTok + Twitter + Amazon (best effort) | 3 | 2-3 days |
| 4 | Newsletter Engine | Full 5-section generator with voice | 9 | 4-5 days |
| 5 | Affiliate System | Top 3 affiliates + top 3 products weekly | 4 | 2-3 days |
| 6 | Product Factory | Pain point research + product generation | 12 | 5-7 days |
| 7 | Pipeline Integration | Complete orchestration + ops | 6 | 3-4 days |
| 8 | Manual Execution | Generate 8 newsletters + 8 products | 4 | 3-5 days |
| 9 | Automation | GitHub Actions scheduling | 1 | 1 day |

---

## Phase 1: Foundation

**Goal:** Prove content can flow from source to storage with outlier scoring

**Requirements:**
- AGGR-02: Reddit aggregation with outlier detection
- AGGR-04: Outlier score calculation
- AGGR-05: Engagement modifiers
- AGGR-06: Content storage with metadata

**Success Criteria:**
1. Script pulls top posts from r/shopify, r/dropship, r/ecommerce via PRAW
2. Each post has outlier score calculated: (upvotes ÷ subreddit avg × recency × modifiers)
3. Engagement modifiers applied: +30% money, +20% time, +20% secrets, +15% controversy
4. Posts stored in `data/content_cache/reddit/` with full metadata as JSON
5. Can filter to show only scores > 3x average

**Deliverables:**
- `directives/content_aggregate.md`
- `execution/content_aggregate.py`
- `data/content_cache/reddit/` populated with test data

**DOE Pattern:**
```
directives/content_aggregate.md  ←→  execution/content_aggregate.py
DOE-VERSION: 2026.01.29
```

**Plans:** 3 plans in 3 waves

Plans:
- [x] 01-01-PLAN.md — Project setup + outlier scoring algorithm (Complete 2026-01-29)
- [x] 01-02-PLAN.md — Reddit fetcher + storage modules (Complete 2026-01-29)
- [x] 01-03-PLAN.md — DOE crystallization + integration (Complete 2026-01-29)

**Phase 1 Complete:** 2026-01-29 (live API testing deferred pending credentials)

---

## Phase 2: Core Sources

**Goal:** YouTube with TubeLab outlier detection + Perplexity research

**Requirements:**
- AGGR-01: YouTube via TubeLab API
- AGGR-03: Perplexity API integration
- AGGR-07: Deduplication
- AGGR-08: Transcript fetching
- AGGR-09: TubeLab API research + signup
- OUTP-04: Content sheet output (TubeLab style)

**Success Criteria:**
1. TubeLab API researched, account created, API key obtained
2. TubeLab integration returns e-com videos with outlier scores > 5x channel average
3. Transcripts fetched for top 10 high-scoring videos via youtube-transcript-api
4. Perplexity API returns trend summaries for e-com topics
5. Deduplication prevents repeating content from last 4 weeks (hash-based)
6. Output CSV/JSON with: source link, thumbnail URL, title, outlier score, AI summary

**Deliverables:**
- Updated `execution/content_aggregate.py` (YouTube + Perplexity modules)
- `data/content_cache/youtube/` populated
- `data/content_cache/perplexity/` populated
- `output/content_sheet.csv`

---

## Phase 3: Stretch Sources (Best Effort)

**Goal:** Attempt TikTok, Twitter, Amazon — don't block pipeline if they fail

**Requirements:**
- AGGR-S01: TikTok Shop trending (stretch)
- AGGR-S02: Twitter/X via Apify (stretch)
- AGGR-S03: Amazon Movers & Shakers (stretch)

**Success Criteria:**
1. At least one stretch source working reliably
2. Graceful failure if source unavailable (log warning, continue pipeline)
3. Pipeline continues without stretch sources
4. Working sources integrated into content aggregation

**Deliverables:**
- `execution/tiktok_aggregate.py` (if viable)
- `execution/twitter_aggregate.py` (if viable)
- `execution/amazon_aggregate.py` (if viable)
- Documentation of what worked/didn't work

**Note:** This phase is time-boxed. If sources prove unreliable after 2 days, move on.

---

## Phase 4: Newsletter Engine

**Goal:** Complete 5-section generator with consistent Hormozi/Suby voice

**Requirements:**
- NEWS-01: Section 1 - Instant Reward (quote/tweet)
- NEWS-02: Section 2 - What's Working Now (tactical nugget)
- NEWS-03: Section 3 - The Breakdown (story-sell bridge)
- NEWS-04: Section 4 - Tool of the Week (soft sell)
- NEWS-05: Section 5 - PS Statement
- NEWS-06: Voice profile application
- NEWS-07: Subject line generation
- NEWS-08: Preview text generation
- NEWS-09: Markdown output

**Success Criteria:**
1. All 5 sections generate correctly from aggregated content
2. Voice matches Hormozi/Suby hybrid: short sentences, concrete examples, math, zero fluff
3. Subject lines are lowercase, curiosity-driven, no emojis
4. Preview text is hook (not "view in browser")
5. Output is clean markdown, ready for Beehiiv copy/paste
6. Anti-patterns never appear in output

**Deliverables:**
- `directives/newsletter_generate.md`
- `execution/newsletter_generate.py`
- `data/voice_profile.json` (examples + anti-patterns)
- Sample newsletter in `output/newsletters/`

---

## Phase 5: Affiliate System

**Goal:** Discover monetization opportunities weekly (no starting list)

**Requirements:**
- MONE-01: Discover affiliate opportunities each week
- MONE-02: Output top 3 affiliate opportunities
- MONE-03: Output top 3 product alternatives
- MONE-04: Generate contextual pitch angles

**Success Criteria:**
1. Research identifies relevant affiliate programs for newsletter topic
2. Top 3 affiliate opportunities output with: program name, commission rate, product fit, pitch angle
3. Top 3 product alternatives output with: product concept, estimated value, build complexity
4. Contextual pitch angle generated that fits naturally in Section 4
5. User can choose affiliate OR product for monetization

**Deliverables:**
- `directives/affiliate_finder.md`
- `execution/affiliate_finder.py`
- Sample output showing top 3 + top 3 format

---

## Phase 6: Product Factory

**Goal:** Research pain points, generate high-value products solving specific problems

**Requirements:**
- PROD-01: Reddit pain point research
- PROD-02: Narrow problem identification
- PROD-03: High-value product generation ($1K+ perceived value)
- PROD-04: HTML tools support
- PROD-05: Automations/workflows support
- PROD-06: Custom GPT support
- PROD-07: Google Sheets support
- PROD-08: PDF frameworks support
- PROD-09: Prompt packs support
- PROD-10: Sales copy generation
- PROD-11: Pricing recommendations
- PROD-12: Complete product packaging
- AGGR-10: Reddit pain point search

**Success Criteria:**
1. Reddit scraping identifies specific e-com pain points (not vague problems)
2. Narrow problems identified that tools could solve very well
3. HTML tools generate as single-file, working calculators/generators
4. Automations generate as documented Python scripts or workflow templates
5. GPT configs generate with complete instructions and knowledge base
6. Sheets generate with formulas, formatting, documentation
7. PDFs generate with professional styling, actionable content
8. Sales copy generated: headline, benefits, CTA
9. Pricing recommendation included ($27-97 based on value)
10. Complete package in `output/products/[name]/` ready to sell

**Deliverables:**
- `directives/product_factory.md`
- `execution/product_factory.py`
- `execution/generators/html_tool.py`
- `execution/generators/automation.py`
- `execution/generators/gpt_config.py`
- `execution/generators/sheets.py`
- `execution/generators/pdf.py`
- `execution/generators/prompt_pack.py`
- `data/product_templates/` with base templates
- Sample product in `output/products/`

---

## Phase 7: Pipeline Integration

**Goal:** Complete orchestration with error handling and cost tracking

**Requirements:**
- OUTP-01: Newsletter markdown output
- OUTP-02: Product package output
- OPER-01: CLI execution
- OPER-02: Cost tracking
- OPER-03: Graceful degradation
- OPER-04: Error messages

**Success Criteria:**
1. Single command runs entire pipeline: `python execution/newsletter_generate.py`
2. Graceful degradation if any source fails (continue with available data)
3. Cost tracked per run via `doe_utils.log_cost()`
4. Clear error messages with recovery instructions
5. Newsletter saved to `output/newsletters/[date]-[topic].md`
6. Product saved to `output/products/[date]-[name]/`
7. All DOE patterns followed (version matching, directive linking)

**Deliverables:**
- Updated `execution/newsletter_generate.py` (full orchestrator)
- Cost logging integrated throughout
- Error handling tested for each failure mode
- Documentation of recovery procedures

---

## Phase 8: Manual Execution

**Goal:** Generate 8 newsletters + 8 products, validate system

**Requirements:**
- INIT-01: Research 8 trending topics
- INIT-02: Generate 8 newsletters
- INIT-03: Generate 8 products (prioritize HTML tools/automations)
- INIT-04: Create content buffer
- OUTP-03: Content calendar

**Success Criteria:**
1. 8 trending e-com topics identified from last 2-3 weeks using outlier detection
2. Content calendar created with topic, angle, product idea for each week
3. 8 complete newsletters generated (one per topic), each following 5-section format
4. 8 high-value products generated (prioritize HTML tools and automations)
5. All stored in output directories, ready for weekly publishing
6. Issues discovered and fixed
7. System validated for autonomous operation

**Deliverables:**
- `output/content_calendar.md` (8-week plan)
- 8 newsletters in `output/newsletters/`
- 8 products in `output/products/`
- Bug fixes and refinements documented

---

## Phase 9: Automation

**Goal:** Scheduled execution via GitHub Actions

**Requirements:**
- OPER-05: GitHub Actions workflow

**Success Criteria:**
1. GitHub Actions workflow configured for Tuesday 10am ET and Thursday 8pm ET
2. All API keys stored as GitHub Secrets
3. Output committed to repo or pushed to accessible location
4. Notification on completion (success or failure)
5. Manual trigger available for on-demand runs

**Deliverables:**
- `.github/workflows/newsletter.yml`
- Secrets configured in GitHub repository settings
- Documentation of automation setup

---

## Build Order Rationale

```
Phase 1: Foundation (Storage + Reddit + Scoring)
    ↓
Phase 2: Core Sources (YouTube + Perplexity)
    ↓
Phase 3: Stretch Sources (TikTok/Twitter/Amazon - best effort)
    ↓
Phase 4: Newsletter Engine (5 sections + voice)
    ↓
Phase 5: Affiliate System (top 3 + top 3)
    ↓
Phase 6: Product Factory (pain points → products)
    ↓
Phase 7: Pipeline Integration (orchestration)
    ↓
Phase 8: Manual Execution (8 newsletters + 8 products)
    ↓
Phase 9: Automation (GitHub Actions)
```

**Why this order:**
1. **Storage first**: Everything needs somewhere to write/read content
2. **Reddit first**: Proves the pattern, easiest API, also feeds product ideation
3. **YouTube second**: Highest value source, requires TubeLab signup
4. **Stretch sources**: Time-boxed, don't block pipeline
5. **Newsletter before monetization**: Need content to monetize
6. **Affiliate before products**: Faster to implement, validates monetization flow
7. **Products last**: Most complex, builds on all prior components
8. **Integration**: Only integrate after all pieces work individually
9. **Manual execution**: Validate before automating
10. **Automation last**: Only automate what's proven to work

---

## Risk Mitigation

| Risk | Mitigation | Phase |
|------|------------|-------|
| TubeLab API unavailable | Fall back to YouTube Data API + manual scoring | Phase 2 |
| Stretch sources unreliable | Time-box to 2 days, continue without | Phase 3 |
| Voice drift in generation | Comprehensive voice profile + anti-patterns | Phase 4 |
| Products feel low-value | Reddit pain point validation + quality bar | Phase 6 |
| API costs exceed budget | Cost tracking + alerts | Phase 7 |
| Pipeline fails silently | Graceful degradation + notifications | Phase 7 |

---

## File Structure (Final)

```
dtc-newsletter/
├── .planning/
│   ├── PROJECT.md
│   ├── REQUIREMENTS.md
│   ├── ROADMAP.md
│   ├── STATE.md
│   ├── config.json
│   └── research/
│       ├── STACK.md
│       ├── FEATURES.md
│       ├── ARCHITECTURE.md
│       ├── PITFALLS.md
│       └── SUMMARY.md
├── directives/
│   ├── content_aggregate.md
│   ├── affiliate_finder.md
│   ├── product_factory.md
│   └── newsletter_generate.md
├── execution/
│   ├── content_aggregate.py
│   ├── affiliate_finder.py
│   ├── product_factory.py
│   ├── newsletter_generate.py
│   └── generators/
│       ├── html_tool.py
│       ├── automation.py
│       ├── gpt_config.py
│       ├── sheets.py
│       ├── pdf.py
│       └── prompt_pack.py
├── data/
│   ├── voice_profile.json
│   ├── content_cache/
│   │   ├── reddit/
│   │   ├── youtube/
│   │   └── perplexity/
│   └── product_templates/
├── output/
│   ├── newsletters/
│   ├── products/
│   └── content_calendar.md
└── .github/
    └── workflows/
        └── newsletter.yml
```

---
*Roadmap created: 2026-01-29*
*Last updated: 2026-01-29T23:24:15Z - Phase 1 complete*
