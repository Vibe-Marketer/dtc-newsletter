# Requirements: DTC Newsletter Automation System

**Defined:** 2026-01-29
**Core Value:** Every week, a complete newsletter draft appears with real trending data, proven format, and a high-value digital product — requiring zero manual research or writing.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Content Aggregation

- [x] **AGGR-01**: Pull high-performing e-commerce videos from YouTube using TubeLab API with outlier detection (score > 5x channel average)
- [ ] **AGGR-02**: Pull viral discussions from Reddit (r/shopify, r/dropship, r/ecommerce) using outlier scoring (upvotes > 3x subreddit average)
- [x] **AGGR-03**: Pull research summaries and trend data via Perplexity API
- [ ] **AGGR-04**: Calculate outlier scores for all content (engagement ÷ source average × recency boost × engagement modifiers)
- [ ] **AGGR-05**: Apply engagement modifiers (+30% money, +20% time savings, +20% "secrets", +15% controversy)
- [ ] **AGGR-06**: Store aggregated content with metadata and outlier scores
- [x] **AGGR-07**: Deduplicate content (don't repeat stories from last 4 weeks)
- [x] **AGGR-08**: Fetch transcripts for high-scoring YouTube videos
- [x] **AGGR-09**: Research TubeLab API, sign up, and integrate for YouTube outlier detection
- [x] **AGGR-10**: Search Reddit for e-com pain points and complaints (for product ideation)

### Content Aggregation — Stretch Goals

- [ ] **AGGR-S01**: Pull trending products from TikTok Shop (via pyktok or Apify)
- [ ] **AGGR-S02**: Pull tweets from DTC accounts via Apify Actor
- [ ] **AGGR-S03**: Pull Amazon Movers & Shakers data via PA-API

### Newsletter Generation

- [x] **NEWS-01**: Generate Section 1 - Instant Reward (high-engagement quote/tweet from aggregated content)
- [x] **NEWS-02**: Generate Section 2 - What's Working Now (tactical nugget under 200 words, problem → solution → how-to)
- [x] **NEWS-03**: Generate Section 3 - The Breakdown (story-sell bridge with source link to outlier content)
- [x] **NEWS-04**: Generate Section 4 - Tool of the Week (contextual soft sell with affiliate or internal product)
- [x] **NEWS-05**: Generate Section 5 - PS Statement (meme, secondary CTA, or additional resource)
- [x] **NEWS-06**: Apply consistent voice (Hormozi/Suby hybrid per voice profile)
- [x] **NEWS-07**: Generate lowercase curiosity-driven subject lines (no emojis, no caps)
- [x] **NEWS-08**: Generate preview text hooks (not "view in browser")
- [x] **NEWS-09**: Output as plain text markdown (no HTML templates, high deliverability)

### Monetization

- [ ] **MONE-01**: Research and discover affiliate opportunities each week (no starting list)
- [ ] **MONE-02**: Output top 3 most promising affiliate opportunities with commission rates and pitch angles
- [ ] **MONE-03**: Output top 3 product alternatives we could create instead
- [ ] **MONE-04**: Generate contextual pitch angle for selected monetization option

### Product Factory

- [x] **PROD-01**: Research e-com pain points via Reddit (people struggling with Shopify, e-com startup problems)
- [x] **PROD-02**: Identify narrow, specific problems that tools could solve very well
- [x] **PROD-03**: Generate one high-value digital product per week (minimum $1K perceived value)
- [x] **PROD-04**: Support product type: Small HTML tools (single-file calculators, generators, automations)
- [x] **PROD-05**: Support product type: Simple automations/workflows (Python scripts, workflow templates)
- [x] **PROD-06**: Support product type: Custom GPT configurations (instructions + knowledge base)
- [x] **PROD-07**: Support product type: Google Sheets templates (calculators, trackers, dashboards)
- [x] **PROD-08**: Support product type: PDF frameworks/guides (structured docs with actionable content)
- [x] **PROD-09**: Support product type: Prompt Packs (curated prompts for specific outcomes)
- [x] **PROD-10**: Generate sales copy for each product (headline, benefits, CTA)
- [x] **PROD-11**: Recommend pricing based on value ($27-97 range, 3-5x perceived value minimum)
- [x] **PROD-12**: Package complete product (all deliverables + sales copy + pricing ready to sell)

### Output & Delivery

- [x] **OUTP-01**: Save newsletter draft as markdown in `output/newsletters/[date]-[topic].md`
- [ ] **OUTP-02**: Save product package in `output/products/[date]-[product-name]/`
- [ ] **OUTP-03**: Generate content calendar with 8 trending topics for initial manual execution
- [x] **OUTP-04**: Output content sheet with: source link, thumbnail, title, outlier score, summary (TubeLab style)

### Operations

- [x] **OPER-01**: CLI execution via `python execution/pipeline_runner.py`
- [x] **OPER-02**: Cost tracking per run via `CostTracker` and `log_run_cost()`
- [x] **OPER-03**: Error handling with graceful degradation (works with partial sources)
- [x] **OPER-04**: Clear failure messages with recovery instructions
- [ ] **OPER-05**: GitHub Actions workflow for scheduled automation (Tuesday 10am, Thursday 8pm)

### Initial Execution

- [ ] **INIT-01**: Research and identify 8 trending e-commerce topics from last 2-3 weeks
- [ ] **INIT-02**: Generate 8 complete newsletter drafts (one per topic)
- [ ] **INIT-03**: Generate 8 high-value digital products (prioritize HTML tools and automations)
- [ ] **INIT-04**: Create content buffer ready for weekly publishing

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Intelligence Layer

- **INTL-01**: Trend scoring algorithm (identify rising topics before peak)
- **INTL-02**: A/B subject line variants for Beehiiv testing
- **INTL-03**: Self-improving prompts based on approval/rejection feedback
- **INTL-04**: Engagement prediction model

### Advanced Monetization

- **ADMN-01**: Revenue attribution per newsletter section
- **ADMN-02**: Competitor newsletter monitoring
- **ADMN-03**: Automatic affiliate program discovery via web scraping

## Out of Scope

| Feature | Reason |
|---------|--------|
| Beehiiv API publishing | No Enterprise access; markdown copy/paste workflow |
| Subscriber management | Beehiiv handles this |
| Payment processing | Use Gumroad/Stripe/Beehiiv directly |
| Social media posting | Different workflow, out of scope |
| Mobile app | Web/CLI sufficient |
| Real-time/daily newsletters | Weekly cadence defined; daily = 7x complexity |
| Custom email infrastructure | Beehiiv handles delivery, reputation, compliance |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AGGR-01 | Phase 2 | Pending |
| AGGR-02 | Phase 1 | Complete* |
| AGGR-03 | Phase 2 | Pending |
| AGGR-04 | Phase 1 | Complete |
| AGGR-05 | Phase 1 | Complete |
| AGGR-06 | Phase 1 | Complete |
| AGGR-07 | Phase 2 | Pending |
| AGGR-08 | Phase 2 | Pending |
| AGGR-09 | Phase 2 | Pending |
| AGGR-10 | Phase 6 | Complete |
| AGGR-S01 | Phase 3 | Pending |
| AGGR-S02 | Phase 3 | Pending |
| AGGR-S03 | Phase 3 | Pending |
| NEWS-01 | Phase 4 | Complete |
| NEWS-02 | Phase 4 | Complete |
| NEWS-03 | Phase 4 | Complete |
| NEWS-04 | Phase 4 | Complete |
| NEWS-05 | Phase 4 | Complete |
| NEWS-06 | Phase 4 | Complete |
| NEWS-07 | Phase 4 | Complete |
| NEWS-08 | Phase 4 | Complete |
| NEWS-09 | Phase 4 | Complete |
| MONE-01 | Phase 5 | Complete |
| MONE-02 | Phase 5 | Complete |
| MONE-03 | Phase 5 | Complete |
| MONE-04 | Phase 5 | Complete |
| PROD-01 | Phase 6 | Complete |
| PROD-02 | Phase 6 | Complete |
| PROD-03 | Phase 6 | Complete |
| PROD-04 | Phase 6 | Complete |
| PROD-05 | Phase 6 | Complete |
| PROD-06 | Phase 6 | Complete |
| PROD-07 | Phase 6 | Complete |
| PROD-08 | Phase 6 | Complete |
| PROD-09 | Phase 6 | Complete |
| PROD-10 | Phase 6 | Complete |
| PROD-11 | Phase 6 | Complete |
| PROD-12 | Phase 6 | Complete |
| OUTP-01 | Phase 7 | Complete |
| OUTP-02 | Phase 6 | Complete |
| OUTP-03 | Phase 8 | Pending |
| OUTP-04 | Phase 2 | Pending |
| OPER-01 | Phase 7 | Complete |
| OPER-02 | Phase 7 | Complete |
| OPER-03 | Phase 7 | Complete |
| OPER-04 | Phase 7 | Complete |
| OPER-05 | Phase 9 | Pending |
| INIT-01 | Phase 8 | Pending |
| INIT-02 | Phase 8 | Pending |
| INIT-03 | Phase 8 | Pending |
| INIT-04 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 49 total (46 core + 3 stretch)
- Mapped to phases: 49
- Unmapped: 0

**Notes:**
- *Complete** = Code complete, live API testing deferred pending credentials

---
*Requirements defined: 2026-01-29*
*Last updated: 2026-01-31 - Phase 7 requirements complete*
