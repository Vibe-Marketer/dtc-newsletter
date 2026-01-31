# Phase 3: Stretch Sources - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Attempt TikTok, Twitter/X, and Amazon Movers & Shakers as data sources. Best effort — don't block pipeline if they fail. Time-boxed to 2 days. Each source should add unique signal that core sources (Reddit, YouTube, Perplexity) don't provide.

</domain>

<decisions>
## Implementation Decisions

### Source Priority & Leverage
- **All three sources pursued** — each offers unique leverage
- **Twitter/X:** Viral founder takes, product announcements, controversy signals — all weighted into composite score
- **TikTok:** Viral product videos, TikTok Shop trending, creator-brand partnerships — all signals with commerce weighting higher
- **Amazon:** Track whatever categories are moving fastest (category-agnostic) — chase velocity, not predetermined categories
- **Time allocation:** Spend 1 day on hardest source, 1 day on easier two

### Data Extraction & Scoring
- **Twitter scoring:** Composite score combining engagement ratio, raw engagement, and quote tweet ratio (like Reddit outlier scoring)
- **TikTok scoring:** All signals combined, with commerce indicators weighted higher (product tags, shop links, "where to buy" comments)
- **Amazon scoring:** Hybrid approach — both platform rank (Movers & Shakers position) AND outlier score (over-performing within category)
- **Unique signal requirement:** Source only counts as "working" if it surfaces things other sources miss

### Failure Handling
- **Runtime failures:** Retry 3x, then continue pipeline without that source
- **Logging:** Console output + persistent log file + output metadata showing which sources succeeded/failed
- **Philosophy:** Focus energy on success strategies, not failure scenarios

### Integration Style
- **Script structure:** Separate scripts per source (twitter_aggregate.py, tiktok_aggregate.py, amazon_aggregate.py)
- **Caching:** Short 24-hour cache — stretch sources change fast, refresh often
- **Newsletter integration:** Mixed with core sources — best content rises regardless of source
- **DOE pattern:** One directive per source (twitter_aggregate.md, tiktok_aggregate.md, amazon_aggregate.md)

### Claude's Discretion
- Specific API/scraping approaches for each platform
- Exact weighting formulas for composite scores
- How to determine "fastest moving" Amazon categories
- Technical implementation of graceful degradation

</decisions>

<specifics>
## Specific Ideas

- "How can we best leverage each platform in a way that's truly thinking outside the box?"
- "How do we gain the most leverage legally possible to 'hack' the algo?"
- Each platform should be leveraged in its own unique way — not just generic data extraction
- Focus on maximum leverage and impact, not just "getting some data"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-stretch-sources*
*Context gathered: 2026-01-31*
