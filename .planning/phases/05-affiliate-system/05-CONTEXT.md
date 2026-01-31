# Phase 5: Affiliate System - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Discover monetization opportunities weekly — outputting top 3 affiliate opportunities and top 3 product alternatives with contextual pitch angles. No starting affiliate list; discovery happens fresh each week based on newsletter topic.

</domain>

<decisions>
## Implementation Decisions

### Discovery criteria
- **Primary filter:** Relevance to THIS week's newsletter topic (not generic e-com affiliates)
- **Ranking factors:** Commission rate + product fit + audience match (weighted equally)
- **Minimum bar:** Must have affiliate program accessible (not waitlisted/closed)
- **Sources for discovery:** Perplexity research on "[topic] affiliate programs" + known aggregators (ShareASale, Impact, PartnerStack)

### Output format
- **Top 3 affiliates:** Program name, commission rate (%), product fit explanation (1 sentence), pitch angle (ready to use in Section 4)
- **Top 3 products:** Product concept, estimated perceived value, build complexity (easy/medium/hard), why it beats affiliate option
- **Ranking rationale:** Brief note on why #1 beats #2, etc. — helps you choose quickly
- **Format:** Markdown table + expanded details below

### Pitch angle generation
- **Contextual to newsletter:** Each pitch references the specific topic/problem from that week's content
- **Voice-matched:** Follows Hormozi/Suby hybrid — concrete benefit, no fluff, math if applicable
- **Ready to use:** Can be copy/pasted directly into Section 4 with minimal editing
- **Length:** 2-3 sentences max

### Decision workflow
- Output presents BOTH affiliate and product options side-by-side
- Each option shows: effort required, potential upside, timeline
- User makes final call (system doesn't auto-choose)
- If user picks affiliate: pitch angle is ready
- If user picks product: feeds into Phase 6 Product Factory

### Claude's Discretion
- Exact Perplexity prompts for affiliate discovery
- How to handle topics with few/no affiliate options (suggest adjacent programs or lean toward products)
- Commission rate thresholds (suggesting good/mediocre/poor)
- Caching strategy for discovered programs

</decisions>

<specifics>
## Specific Ideas

- "Tool of the Week" in Section 4 is the natural placement — pitch should feel like a recommendation, not an ad
- Affiliates should be tools/services DTC operators actually use (Shopify apps, shipping solutions, email tools, etc.)
- Product alternatives should be things that could sell for $27-97 (from PROJECT.md pricing guidance)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-affiliate-system*
*Context gathered: 2026-01-31*
