# Phase 8: Manual Execution - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate 8 newsletters and 8 products using the completed pipeline to validate the system works end-to-end. Create a content calendar and fix any issues discovered. This is execution and validation, not building new features.

</domain>

<decisions>
## Implementation Decisions

### Topic Selection Criteria
- **Recency:** Last 4 weeks of content (recent but wide selection pool)
- **Diversity:** Force diversity across e-com sub-areas (no repeats — 1 shipping, 1 pricing, 1 ads, etc.)
- **Source hierarchy:**
  1. Outlier detection first (Reddit, YouTube via TubeLab) — real engagement signals
  2. Trending validation (X, Reddit discussions) — confirm what's hot
  3. Perplexity as supplement only — less time-aware, fill gaps
- **Approval:** Trust the system — top 8 by outlier score + diversity filter auto-selected

### Content Calendar Structure
- **Format:** JSON + Markdown (machine-readable JSON + human-readable MD view)
- **Entry metadata:** Minimal — Week #, topic, newsletter path, product path
- **Scheduling:** Week numbers only (Week 1, Week 2...) — you decide actual dates
- **Pairing:** Newsletters and products are separate (8 newsletters + 8 products, not necessarily matched)

### Product Type Distribution
- **Distribution:** Prioritize hard stuff — 4-5 HTML tools/automations, rest mixed
- **Pain point source:** Real pain points from Reddit pain point miner
- **Approval:** Fully autonomous — system picks top 8 pain points and generates
- **Failure handling:** Retry with different type (if HTML tool fails, try automation for same pain point)

### Quality Validation Approach
- **Newsletter validation layers:**
  1. Anti-pattern check (no forbidden phrases)
  2. Structural check (5 sections present, word counts in range)
  3. Quality gate: voice consistency + at least 2 concrete numbers + source attribution
  4. Human review (final check)
- **Product validation:** Generator validation + functional test (actually run/open the product)
- **Failure handling:** Regenerate with tweaks (modify prompts/approach and retry)

### Claude's Discretion
- Exact order of newsletter generation
- How to structure the functional test for each product type
- Retry logic and prompt adjustments

</decisions>

<specifics>
## Specific Ideas

- Topic sourcing follows natural discovery flow: outliers first, then trending validation, Perplexity last
- Products don't need to match newsletters — they're independent content pieces
- Quality gate must include concrete numbers (the Hormozi/Suby voice demands specificity)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-manual-execution*
*Context gathered: 2026-01-31*
