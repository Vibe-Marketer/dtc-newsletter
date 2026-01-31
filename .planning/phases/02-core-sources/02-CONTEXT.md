# Phase 2: Core Sources - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

YouTube with TubeLab outlier detection + Perplexity research. Add two content sources with outlier scoring, transcript fetching, deduplication, and structured output. Newsletter generation and monetization are separate phases.

</domain>

<decisions>
## Implementation Decisions

### TubeLab integration approach
- Research TubeLab first, then checkpoint for user to create account and get API key
- Fallback if TubeLab unavailable or too expensive: YouTube Data API + manual outlier scoring (same pattern as Reddit)
- Fetch transcripts for top 10 high-scoring videos per run

### YouTube content selection
- Channel discovery: Research-based — Claude identifies top DTC/e-com creators during planning
- Niche focus: Broad DTC/e-commerce (Shopify, dropshipping, Amazon FBA, general e-com)
- Outlier threshold: 5x channel average (match TubeLab's approach)
- Time window: Last 14 days (balance of fresh content + time to accumulate views)

### Perplexity usage
- Two-stage use: (1) Trending topics summary, then (2) deep dive on chosen topic
- Storage: Same pattern as Reddit/YouTube — JSON in data/content_cache/perplexity/ with metadata
- Model selection: Best quality available (not optimizing for cost)

### Content sheet output
- Format: Both CSV and JSON generated each run
- Columns: Full metadata (link, thumbnail, title, score, author, date, engagement stats, virality analysis)
- NO simple summaries — instead, structured virality analysis

### Virality analysis (key decision)
- Primary consumer is AI (newsletter engine), not humans
- Format: Structured/parseable data with categorized virality factors
- Content: Hook analysis, emotional triggers, timing factors, replication notes — as discrete tagged values
- Purpose: Enable AI to extract patterns and reverse-engineer viral content mechanics

### Claude's Discretion
- Specific TubeLab API endpoints and data mapping
- YouTube Data API quota management
- Perplexity prompt engineering for trend/research queries
- Deduplication algorithm (hash-based per roadmap)

</decisions>

<specifics>
## Specific Ideas

- Virality analysis should attempt to "prove and define virality with a high degree of certainty" — not vague observations but specific, extractable factors
- Analysis should uncover "the ultimate legend or key to breaking norms" — what made this content bust through
- Think of it as scientific breakdown: given circumstances + variables → why was virality almost inevitable?
- The 90/10 AI/human usage split means structure and parseability trump readability

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-core-sources*
*Context gathered: 2026-01-31*
