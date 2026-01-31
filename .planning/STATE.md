# Project State: DTC Newsletter Automation System

**Last Updated:** 2026-01-31
**Current Phase:** 5 of 9 (Affiliate System)
**Status:** Phase 5 Complete

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-01-29)

**Core value:** Every week, a complete newsletter draft appears with real trending data, proven format, and a high-value digital product — requiring zero manual research or writing.

**Current focus:** Phase 5 complete - Affiliate discovery, pitch generation, product alternatives, and DOE crystallization done. Ready for Phase 6 Product Factory.

---

## Phase Status

| Phase | Name | Status | Progress | Notes |
|-------|------|--------|----------|-------|
| 1 | Foundation | Complete | 100% | DOE pipeline crystallized (live API deferred) |
| 2 | Core Sources | Complete | 100% | All 4 plans complete (TubeLab + Perplexity + YouTube + Integration) |
| 3 | Stretch Sources | Complete | 100% | Orchestrator + integration complete |
| 4 | Newsletter Engine | Complete | 100% | All 4 plans complete (orchestrator + DOE) |
| 5 | Affiliate System | Complete | 100% | Discovery + pitches + products + DOE |
| 6 | Product Factory | Pending | 0% | Pain points → products |
| 7 | Pipeline Integration | Pending | 0% | Orchestration + ops |
| 8 | Manual Execution | Pending | 0% | 8 newsletters + 8 products |
| 9 | Automation | Pending | 0% | GitHub Actions |

**Overall Progress:** 5/9 phases complete (Foundation + Core Sources + Stretch Sources + Newsletter Engine + Affiliate System)

---

## Requirements Progress

### Content Aggregation (13 total)
- Completed: 10 (AGGR-01 Reddit, AGGR-03 YouTube, AGGR-04 outlier score, AGGR-05 engagement modifiers, AGGR-07 Perplexity, AGGR-08 transcripts, AGGR-09 deduplication, AGGR-S01 TikTok, AGGR-S02 Twitter, AGGR-S03 Amazon)
- In Progress: 0
- Pending: 3

### Newsletter Generation (9 total)
- Completed: 6 (NEWS-01 5-section format, NEWS-02 subject lines, NEWS-03 preview text, NEWS-04 content selection, NEWS-05 orchestrator, NEWS-06 voice profile)
- In Progress: 0
- Pending: 3

### Monetization (4 total)
- Completed: 4 (MON-01 affiliate discovery, MON-02 pitch generation, MON-03 product alternatives, MON-04 output formatter)
- In Progress: 0
- Pending: 0

### Product Factory (12 total)
- Completed: 0
- In Progress: 0
- Pending: 12

### Output & Delivery (4 total)
- Completed: 1 (OUTP-04 content sheet)
- In Progress: 0
- Pending: 3

### Operations (5 total)
- Completed: 0
- In Progress: 0
- Pending: 5

### Initial Execution (4 total)
- Completed: 0
- In Progress: 0
- Pending: 4

**Total:** 21/49 requirements complete

---

## Active Decisions

| Decision | Options | Chosen | Date |
|----------|---------|--------|------|
| Beehiiv integration | API vs Copy/paste | Copy/paste | 2026-01-29 |
| Voice profile | Hormozi vs Suby vs Hybrid | Hybrid | 2026-01-29 |
| Twitter/X approach | Paid API vs Apify | Apify (stretch) | 2026-01-29 |
| Product focus | Easy first vs Hard first | Hard first | 2026-01-29 |
| Affiliate list | Provided vs Discovered | Discovered | 2026-01-29 |
| Recency boost | Exponential vs Linear decay | Linear (7 days) | 2026-01-29 |
| Engagement modifiers | Multiplicative vs Additive | Additive then multiply | 2026-01-29 |
| Reddit live testing | Now vs Deferred | Deferred (code ready) | 2026-01-29 |
| Perplexity SDK | Native vs OpenAI-compat | OpenAI-compatible | 2026-01-31 |
| Dedup hash algorithm | SHA vs MD5 | MD5 (fast, sufficient) | 2026-01-31 |
| Twitter scoring boost | Static vs Quote-based | Quote boost 1.3x | 2026-01-31 |
| Stretch source caching | No cache vs TTL cache | 24-hour TTL cache | 2026-01-31 |
| TikTok commerce boost | Static vs Commerce-weighted | 1.5x for commerce videos | 2026-01-31 |
| Amazon scoring weights | Equal vs Velocity-weighted | 30% position + 70% velocity | 2026-01-31 |
| Stretch execution | Sequential vs Parallel | Parallel (ThreadPoolExecutor) | 2026-01-31 |
| Stretch success criteria | All sources vs Any source | Any source (graceful degradation) | 2026-01-31 |
| Stretch weight in merge | 1.0x vs Reduced | 0.8x (stretch less reliable) | 2026-01-31 |
| TubeLab vs YouTube API | TubeLab only vs YouTube only vs Hybrid | Hybrid (TubeLab primary, YouTube fallback) | 2026-01-31 |
| Virality output format | Prose vs Structured | Structured dict (AI-parseable) | 2026-01-31 |
| Content sheet format | CSV vs JSON vs Both | Both (CSV + JSON default) | 2026-01-31 |
| Hook type detection | Keyword-based priority | question > number > controversy > story > statement | 2026-01-31 |
| Claude model | GPT-4 vs Claude Sonnet | claude-sonnet-4-5 (cost/quality) | 2026-01-31 |
| Voice profile caching | No cache vs Ephemeral | Ephemeral cache_control | 2026-01-31 |
| Subject line style | Single vs Rotation | 70/20/10 rotation (curiosity/benefit/question) | 2026-01-31 |
| Subject line format | Flexible vs Strict | "DTC Money Minute #X: hook" <50 chars, lowercase | 2026-01-31 |
| Preview text | Generic vs Hook | Must be hook (40-90 chars), never "View in browser" | 2026-01-31 |
| Product ranking | Equal vs Weighted | Value/complexity ratio (high value + low complexity = best) | 2026-01-31 |
| Perplexity fallback | Fail vs Retry | Retry once, then generic pain points | 2026-01-31 |
| DOE version matching | Optional vs Required | Required with --verify-version flag | 2026-01-31 |

---

## Blockers

| Blocker | Impact | Resolution |
|---------|--------|------------|
| Reddit API credentials | Live testing deferred | Code ready, integrate when credentials available |

---

## API Keys Required

| Service | Status | Required For |
|---------|--------|--------------|
| Reddit (PRAW) | Not configured | Phase 1 |
| TubeLab | Configured | Phase 2 |
| YouTube Data API | Configured | Phase 2 (fallback) |
| Perplexity | Not configured | Phase 2 |
| Anthropic (Claude) | Configured | Phase 4 |
| Google Sheets | Not configured | Phase 6 |
| Apify | Not configured | Phase 3 (stretch) |

---

## Content Buffer

| Week | Topic | Newsletter | Product | Status |
|------|-------|------------|---------|--------|
| 1 | TBD | - | - | Not started |
| 2 | TBD | - | - | Not started |
| 3 | TBD | - | - | Not started |
| 4 | TBD | - | - | Not started |
| 5 | TBD | - | - | Not started |
| 6 | TBD | - | - | Not started |
| 7 | TBD | - | - | Not started |
| 8 | TBD | - | - | Not started |

---

## Cost Tracking

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| 1 | $0 | - | Reddit API is free |
| 2 | $5-10 | - | TubeLab + Perplexity |
| 3 | $0-5 | - | Apify if used |
| 4 | $5-10 | - | Claude for generation |
| 5 | $2-5 | - | Research calls |
| 6 | $10-20 | - | Product generation |
| 7 | $0 | - | Integration only |
| 8 | $20-40 | - | 8x full pipeline runs |
| 9 | $0 | - | GitHub Actions free tier |

**Total Estimated:** $42-90 for initial build + 8 executions

---

## Session Log

### 2026-01-29: Project Initialization
- Completed deep questioning phase
- Defined voice profile (Hormozi/Suby hybrid)
- Confirmed no Beehiiv API (copy/paste workflow)
- Set stretch goals for TikTok/Twitter/Amazon
- Product Factory to prioritize hard stuff (HTML tools, automations)
- Affiliate discovery weekly (no starting list)
- Created PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md
- Research completed: STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md
- Ready for Phase 1 execution

### 2026-01-29: Phase 1 Plan 01 Complete
- Completed 01-01-PLAN.md (Project setup + outlier scoring)
- Created scoring algorithm with recency boost and engagement modifiers
- 29 tests passing
- Commits: c4dd42b (setup), b66c205 (scoring)

### 2026-01-29: Phase 1 Plan 02 Complete
- Completed 01-02-PLAN.md (Reddit fetcher + storage)
- Created reddit_fetcher.py with PRAW integration and scoring
- Created storage.py for JSON caching with metadata
- All tests passing with mocks (80+ total)
- Live API verification deferred pending credentials
- Commits: ab9b65a (fetcher), 02f9adf (storage)

### 2026-01-29: Phase 1 Plan 03 Complete
- Completed 01-03-PLAN.md (DOE content aggregation)
- Created directives/content_aggregate.md with DOE-VERSION: 2026.01.29
- Created execution/content_aggregate.py with matching version
- CLI supports --min-score, --limit, --subreddits, --no-save, --show-all
- Phase 1 Foundation complete
- Commits: e26d273 (DOE directive+script), 31afc01 (import fix)

### 2026-01-31: Phase 2 Plan 02 Complete
- Completed 02-02-PLAN.md (Perplexity + Deduplication)
- Created perplexity_client.py using OpenAI-compatible API with sonar-pro model
- Created deduplication.py with MD5 hash-based content tracking
- 41 tests passing (17 perplexity + 24 deduplication)
- Commits: 89df773 (perplexity client), d47edae (deduplication)

### 2026-01-31: Phase 3 Plan 01 Complete
- Completed 03-01-PLAN.md (Apify Foundation + Twitter)
- Created apify_base.py with retry, caching, graceful degradation
- Created twitter_aggregate.py with composite scoring (engagement + quote boost)
- Created DOE directive directives/twitter_aggregate.md
- 18 tests passing for Twitter module
- Commits: ae9c76f (apify foundation), 30a9729 (twitter aggregator)

### 2026-01-31: Phase 3 Plan 02 Complete
- Completed 03-02-PLAN.md (TikTok + Amazon aggregators)
- Created tiktok_aggregate.py with commerce detection and 1.5x boost
- Created amazon_aggregate.py with velocity-weighted scoring (30%/70%)
- DOE directives for both with matching version 2026.01.31
- 34 tests passing (18 TikTok + 16 Amazon)
- Commits: a46f5f4 (TikTok), f195166 (Amazon)

### 2026-01-31: Phase 3 Plan 03 Complete - PHASE 3 COMPLETE
- Completed 03-03-PLAN.md (Stretch sources orchestrator + integration)
- Created stretch_aggregate.py with parallel execution (ThreadPoolExecutor)
- Added --include-stretch flag to content_aggregate.py
- Graceful degradation: pipeline continues if 1-2 sources fail
- 18 tests passing for orchestration, 191 total tests
- Commits: cf69ae7 (orchestrator), 795ffc5 (integration)
- Phase 3 Stretch Sources complete

### 2026-01-31: Phase 2 Plan 01 Complete
- Completed 02-01-PLAN.md (TubeLab research + API decision)
- Corrected initial research: TubeLab DOES have public API at public-api.tubelab.net/v1
- User configured BOTH TUBELAB_API_KEY and YOUTUBE_API_KEY
- Decision: TubeLab primary, YouTube Data API fallback (hybrid approach)
- Commits: c78126c (initial research), dfe996c (corrected research + decision)

### 2026-01-31: Phase 2 Plan 03 Complete
- Completed 02-03-PLAN.md (YouTube + Transcript fetchers)
- Created youtube_fetcher.py with TubeLab API primary + YouTube Data API fallback
- Created transcript_fetcher.py with rate limiting (1.5s delay) and error handling
- Outlier scoring uses same formula as Reddit scoring
- 47 new tests (21 YouTube + 26 transcript), 238 total tests passing
- Commits: aedc587 (YouTube fetcher), 09ebb24 (transcript fetcher)

### 2026-01-31: Phase 2 Plan 04 Complete - PHASE 2 COMPLETE
- Completed 02-04-PLAN.md (Core sources integration)
- Created virality_analyzer.py with VIRALITY_SCHEMA for AI-parseable output
- Created content_sheet.py for CSV + JSON content sheet generation
- Updated content_aggregate.py to integrate all sources (Reddit, YouTube, Perplexity)
- Added deduplication to main pipeline, new CLI options (--sources, --output-format, etc.)
- Updated DOE directive to version 2026.01.31
- 70 new tests (40 virality + 30 content sheet), 308 total tests passing
- Commits: e54d1eb (virality), 23b1dc2 (content sheet), aa836b6 (integration)
- Phase 2 Core Sources complete

### 2026-01-31: Phase 4 Plan 01 Complete
- Completed 04-01-PLAN.md (Voice profile + Claude client)
- Created voice_profile.py with VOICE_PROFILE_PROMPT (704 words) and SECTION_GUIDELINES
- Created anti_pattern_validator.py with 28 forbidden phrases
- Created claude_client.py with prompt caching (cache_control: ephemeral)
- 96 new tests (24 voice + 51 anti-pattern + 21 claude client)
- Commits: 169d959 (voice + anti-pattern), df2cd22 (claude client)

### 2026-01-31: Phase 4 Plan 02 Complete
- Completed 04-02-PLAN.md (Content selector + Section 1 & 2 generators)
- Created content_selector.py with outlier score prioritization
- Diversity constraint: at least 2 different sources when possible
- Content type detection: quotable, tactical, narrative
- Updated section_generators.py with lenient word count validation
- Section 1: 30-60 word instant reward hooks
- Section 2: 300-500 word tactical content (THE MEAT)
- 73 tests (44 content selector + 29 section generators)
- Commits: bfb97c5 (content selector), d2f3dc0 (section generators update)

### 2026-01-31: Phase 4 Plan 03 Complete (parallel with Plan 02)
- Completed 04-03-PLAN.md (Section generators 3, 4, 5)
- Created section_generators.py with all 5 section generators
- Section 3: The Breakdown (200-300 words, story-sell bridge)
- Section 4: Tool of the Week (100-200 words, insider friend energy)
- Section 5: PS Statement (20-40 words, foreshadow/cta/meme types)
- XML-structured prompts for consistent Claude parsing
- Non-strict word count validation (logs warnings)
- 29 tests covering all sections + integration
- Commits: fc85c59 (section generators + tests)

### 2026-01-31: Phase 4 Plan 04 Complete - PHASE 4 COMPLETE
- Completed 04-04-PLAN.md (Subject lines, preview text, orchestrator)
- Created subject_line_generator.py with 70/20/10 style rotation
- Validation: <50 chars, lowercase after colon, no emojis, no ALL CAPS
- Created newsletter_generator.py full orchestrator with CLI
- Beehiiv-ready markdown output with metadata comments
- DOE directive directives/newsletter_generate.md with version 2026.01.31
- 64 tests (35 subject + 29 orchestrator), 562 total tests passing
- Commits: 0e01deb (subject line), ca880a3 (orchestrator + DOE)
- Phase 4 Newsletter Engine complete

### 2026-01-31: Phase 5 Plan 01 Complete
- Completed 05-01-PLAN.md (Affiliate discovery + Pitch generation)
- Created affiliate_discovery.py with Perplexity-based program discovery
- AffiliateProgram and AffiliateDiscoveryResult Pydantic models
- Commission classifier with RESEARCH.md thresholds (excellent/good/mediocre/poor)
- Created pitch_generator.py with Claude API (claude-sonnet-4-20250514)
- Voice-matched pitches for Section 4 "Tool of the Week"
- validate_pitch() checks fluff words, passive voice, sentence length
- 61 new tests (36 affiliate + 25 pitch), 623 total tests passing
- Commits: dfc6edd (affiliate discovery), 34ae781 (pitch generator)

### 2026-01-31: Phase 5 Plan 02 Complete - PHASE 5 COMPLETE
- Completed 05-02-PLAN.md (Product alternatives + Output formatter + DOE)
- Created product_alternatives.py with two-stage generation (Perplexity + Claude)
- ProductIdea model with value/complexity ranking
- Created monetization_output.py with unified affiliate/product formatting
- Tables + expanded details matching CONTEXT.md spec
- Created affiliate_finder.py CLI orchestrator
- DOE directive directives/affiliate_finder.md with version 2026.01.31
- 53 new tests (28 product + 25 output), 676 total tests passing
- Commits: 740b587 (product alternatives), 56c16bb (output formatter), 0aa4944 (CLI + DOE)
- Phase 5 Affiliate System complete

---

## Next Actions

1. Start Phase 6 - Execute 06-01-PLAN.md (Product Factory)
2. Configure PERPLEXITY_API_KEY in `.env` for live Perplexity testing
3. Configure APIFY_TOKEN in `.env` for stretch source live testing
4. Configure REDDIT credentials for live Reddit testing

---
*State initialized: 2026-01-29*
*Last updated: 2026-01-31T15:07:01Z*
