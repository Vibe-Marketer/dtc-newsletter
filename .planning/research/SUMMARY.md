# Research Summary: DTC Newsletter Automation System

**Compiled:** 2026-01-29
**Sources:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

---

## Executive Summary

Building an automated weekly newsletter system for DTC News (100K+ subscribers) requires:
1. **Outlier detection** for content curation (TubeLab for YouTube, custom scoring for Reddit)
2. **Modular pipeline** architecture following DOE framework
3. **Voice profile** enforcement to maintain Hormozi/Suby hybrid style
4. **Product factory** that researches pain points and generates high-value tools

**Estimated cost per newsletter:** ~$0.30-0.50 in API costs
**Estimated build time:** 26-35 days across 9 phases

---

## Stack Decisions

### Confirmed

| Component | Choice | Confidence |
|-----------|--------|------------|
| Language | Python 3.12 | HIGH |
| YouTube outlier | TubeLab API | HIGH |
| Reddit | PRAW (official API) | HIGH |
| Research | Perplexity API | HIGH |
| AI/LLM | Claude 3.5 Sonnet | HIGH |
| PDF generation | WeasyPrint | HIGH |
| Scheduling | GitHub Actions | HIGH |

### Stretch (Best Effort)

| Component | Choice | Confidence |
|-----------|--------|------------|
| TikTok Shop | pyktok or Apify | MEDIUM |
| Twitter/X | Apify Actor | MEDIUM |
| Amazon | PA-API | MEDIUM |

### Ruled Out

| Component | Why Not |
|-----------|---------|
| Beehiiv API | No Enterprise access |
| LangChain | Unnecessary abstraction |
| Paid Twitter API | $100/mo not justified |
| Database | File-based sufficient |

---

## Architecture Overview

```
Weekly Trigger (cron/GitHub Actions)
        │
        ▼
┌─────────────────────────────────┐
│  CONTENT AGGREGATION            │
│  - YouTube (TubeLab outliers)   │
│  - Reddit (outlier scoring)     │
│  - Perplexity (research)        │
│  - Stretch: TikTok/Twitter/     │
│    Amazon                       │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  CONTENT STORAGE                │
│  - JSON files in data/cache/    │
│  - Deduplication tracking       │
│  - Outlier scores + metadata    │
└───────────────┬─────────────────┘
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
┌───────────────┐ ┌───────────────┐
│ NEWSLETTER    │ │ AFFILIATE     │
│ ENGINE        │ │ FINDER        │
│ - 5 sections  │ │ - Top 3       │
│ - Voice       │ │   affiliates  │
│   profile     │ │ - Top 3       │
│ - Subject     │ │   products    │
│   lines       │ │ - Pitch       │
└───────┬───────┘ │   angles      │
        │         └───────┬───────┘
        │                 │
        └────────┬────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  PRODUCT FACTORY                │
│  - Pain point research          │
│  - Product generation           │
│    (HTML, automations, GPTs,    │
│     sheets, PDFs, prompts)      │
│  - Sales copy + pricing         │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  OUTPUT                         │
│  - output/newsletters/*.md      │
│  - output/products/*/           │
│  - Copy/paste to Beehiiv        │
└─────────────────────────────────┘
```

---

## Key Features

### Table Stakes (Must Have)
- Multi-source content aggregation with outlier detection
- 5-section "DTC Money Minute" format
- Consistent Hormozi/Suby voice
- Markdown output for Beehiiv copy/paste
- Human approval checkpoint
- Error notifications
- Deduplication

### Differentiators
- TubeLab-style outlier scoring (views ÷ avg × modifiers)
- Top 3 affiliates + top 3 products each week
- Pain point research for product ideation
- High-value product generation (HTML tools, automations)
- DOE framework integration (directive + script pattern)

### Anti-Features (Not Building)
- Beehiiv API publishing
- Real-time/daily newsletters
- Social media posting
- Payment processing
- Mobile app

---

## Critical Pitfalls to Avoid

### 1. Voice Drift
**Risk:** AI loses Hormozi/Suby voice, becomes generic
**Prevention:** 
- Comprehensive voice profile with 50+ examples
- Anti-patterns list (phrases to NEVER use)
- Human review of first 10+ newsletters

### 2. Low-Value Products
**Risk:** Products feel like padded blog posts
**Prevention:**
- Reddit pain point research for real problems
- Prioritize hard stuff (HTML tools, automations)
- Minimum quality bar: $1K perceived value

### 3. Content Staleness
**Risk:** Run out of fresh angles
**Prevention:**
- Outlier detection finds actually viral content
- Multiple sources (YouTube, Reddit, Perplexity)
- 8-week content calendar planned upfront

### 4. Single Point of Failure
**Risk:** One API down = no newsletter
**Prevention:**
- Graceful degradation (continue with partial sources)
- Stretch sources as backups
- Error notifications

---

## Outlier Score Formula

```
Outlier Score = (Engagement ÷ Source Average) × Recency Boost × Modifiers

Engagement Modifiers:
+30% if involves money/revenue
+20% if involves time savings
+20% if involves "secret" or "nobody talks about"
+15% if has controversy/debate

Thresholds:
- YouTube: Score > 5x = worth covering
- Reddit: Score > 3x = worth covering
```

---

## Voice Profile Summary

**Style:** Hormozi/Suby hybrid

| Element | Rule |
|---------|------|
| Sentences | Short. Punchy. Under 15 words. |
| Tone | Direct, confident, slightly irreverent |
| Numbers | Always include: "$X → $Y returned" |
| Fluff | Zero tolerance. Kill "basically," "essentially" |
| Examples | Concrete, specific, real. Never hypothetical. |
| Subject lines | Lowercase, curiosity-driven, no emojis |
| Ratio | 80% value / 20% ask |

**Anti-patterns (NEVER use):**
- "In today's fast-paced world..."
- "Let's dive in..."
- "Without further ado..."
- "I hope this email finds you well"
- Excessive hedging: "may," "might," "could potentially"

---

## Cost Estimates

| Component | Per Newsletter | Notes |
|-----------|---------------|-------|
| TubeLab | ~$0.05 | Cheap API |
| Perplexity | ~$0.10 | Research queries |
| Claude | ~$0.20 | Content generation |
| Reddit | $0 | Free API |
| **Total** | **~$0.35** | |

**8-week manual phase:** ~$3-4 in API costs
**Monthly ongoing:** ~$3-4 for 8 newsletters

---

## Build Order

1. **Foundation** (Phase 1): Storage + Reddit + scoring
2. **Core Sources** (Phase 2): TubeLab + YouTube + Perplexity
3. **Stretch Sources** (Phase 3): TikTok/Twitter/Amazon (time-boxed)
4. **Newsletter Engine** (Phase 4): 5 sections + voice
5. **Affiliate System** (Phase 5): Top 3 + top 3
6. **Product Factory** (Phase 6): Pain points → products
7. **Integration** (Phase 7): Orchestration
8. **Manual Execution** (Phase 8): 8 newsletters + 8 products
9. **Automation** (Phase 9): GitHub Actions

---

## Success Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| Newsletter generation time | < 5 min | Automated |
| Human review time | < 30 min | Per newsletter |
| Voice fidelity | > 8/10 | Subjective scoring |
| Product downloads | > 10% | Of newsletter readers |
| API cost per issue | < $0.50 | Sustainable |
| Pipeline success rate | > 95% | Graceful degradation |

---

## Open Items for Phase 1

1. [ ] Set up Reddit API credentials (PRAW)
2. [ ] Create `data/content_cache/reddit/` directory structure
3. [ ] Implement outlier scoring algorithm
4. [ ] Test with live subreddit data
5. [ ] Validate engagement modifier logic

---
*Summary compiled: 2026-01-29*
*Next review: After Phase 1 completion*
