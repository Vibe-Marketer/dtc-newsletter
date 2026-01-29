# DTC Newsletter Automation System

## What This Is

A fully automated weekly newsletter system for DTC News (100K+ subscribers). The system researches trending e-commerce content using outlier detection, drafts newsletters in a combined Hormozi/Suby voice, discovers affiliate opportunities, and creates one high-value digital product per week — all producing markdown drafts ready for Beehiiv copy/paste.

## Core Value

Every week, a complete newsletter draft appears with real trending data, proven format, and a monetizable product — requiring zero manual research or writing.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Content aggregation with outlier scoring (YouTube via TubeLab, Reddit, Perplexity)
- [ ] Stretch sources: TikTok Shop, Twitter/X via Apify, Amazon (best effort)
- [ ] 5-section "DTC Money Minute" format enforced on every output
- [ ] Combined Hormozi/Suby voice applied automatically
- [ ] Markdown output for Beehiiv copy/paste (no API)
- [ ] Top 3 affiliate opportunities discovered weekly + top 3 product alternatives
- [ ] Product Factory that creates one high-value digital product per week
- [ ] Pain point research via Reddit to identify specific problems to solve
- [ ] Product types: HTML tools, automations, GPTs, sheets, PDFs, prompt packs
- [ ] 8 weeks of newsletters + products drafted before automation
- [ ] Scheduled automation via GitHub Actions

### Out of Scope

- Done-for-you Shopify stores — Morrison's territory
- Shopify affiliate promotions — contractually restricted
- Beehiiv API publishing — no Enterprise access; copy/paste workflow
- Live cohort programs — future phase
- Mobile app — web/CLI only

## Context

**The List:**
- 100,000 subscribers, growing 1,000-3,000/day
- 80%+ are brand-new to e-commerce, stuck at product research
- They want tools, not training — shortcuts over education
- Already in Morrison funnel for first 14 days, then hit DTC News

**Research Done:**
- Alex Hormozi email strategy: reward every action, one concept per email, $45 ROI per dollar
- Sabri Suby email principles: 80% value / 20% ask, plain text, personal not corporate
- Dennis Murphy call: audience pain points, product restrictions, timeline urgency
- TubeLab outlier detection: (views ÷ channel avg) × recency × modifiers

**Existing Assets:**
- `dtc-news-newsletter-strategy.md` — complete format and monetization strategy
- Sample email voice to emulate
- DOE framework for workflow automation

**Voice Profile:**
Combination of sample email + Hormozi + Suby characteristics:
- Short, punchy sentences (under 15 words typically)
- Direct, confident, slightly irreverent tone
- Specific numbers and math: "$X invested → $Y returned"
- Zero fluff — delete "basically," "essentially," "just"
- Concrete, specific examples (never hypothetical)
- Lowercase subject lines, curiosity-driven, no emojis
- 80% value / 20% ask ratio
- Soft sell in Section 4, hard value first

## Constraints

- **Platform**: Beehiiv (markdown copy/paste, no API)
- **Voice**: Hormozi/Suby hybrid (short, concrete, math-driven, zero fluff)
- **Format**: Plain text markdown, no HTML templates, no embedded images
- **Frequency**: 2x/week (Tuesday 10am, Thursday 8pm) target
- **Monetization**: No Shopify affiliates, no done-for-you stores
- **Validation**: 8 manual executions before automation enabled
- **Product focus**: HTML tools and automations first (hard stuff), not easy stuff

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Markdown output (no Beehiiv API) | No Enterprise access; copy/paste is fine | — Pending |
| Hormozi/Suby voice hybrid | Combines best of both: punchy + value-first | — Pending |
| Outlier detection for content | Find actually viral content, not just recent | — Pending |
| Top 3 affiliates + top 3 products weekly | Gives optionality each week | — Pending |
| Product Factory prioritizes hard stuff | HTML tools/automations first; easy stuff can wait | — Pending |
| Pain point research via Reddit | Find narrow, specific problems to solve well | — Pending |
| TubeLab for YouTube | Cheap, has outlier detection built-in | — Pending |
| Stretch goals for TikTok/Twitter/Amazon | Attempt but don't block pipeline | — Pending |

---
*Last updated: 2026-01-29 after questioning and research*
