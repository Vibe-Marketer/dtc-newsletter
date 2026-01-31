# Phase 4: Newsletter Engine - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate a complete 5-section newsletter from aggregated content, applying the Hormozi/Suby voice consistently, with subject line and preview text ready for Beehiiv copy/paste. Output is markdown, zero edits needed.

</domain>

<decisions>
## Implementation Decisions

### Section Content Structure

**Section 1 - Instant Reward (30-60 words)**
- Mix of content types based on what's available: quote, viral tweet, or striking stat
- Whatever delivers immediate value in the opening

**Section 2 - What's Working Now (300-500 words)**
- THE MEAT of the newsletter
- Single actionable tactic that solves a narrow, specific problem
- Must be easy and simple to implement with direct, immediate impact
- Case study ONLY when it delivers an incredibly valuable lesson
- Never diluted bullet-point lists

**Section 3 - The Breakdown (200-300 words)**
- Story-sell bridge
- Ratio of story vs lesson depends on source material
- Match narrative weight to what the content supports

**Section 4 - Tool of the Week (100-200 words)**
- Insider friend energy, NEVER a pitch
- Like sharing a secret with a close personal friend
- Should feel "almost illegal" — insider trading vibes
- Never gimmicky, salesy, or cliche

**Section 5 - PS Statement (20-40 words)**
- Second most-read part after subject line (per Hormozi)
- Purpose: reward the reader, train clicking behavior
- Can be: foreshadowing future content, CTA, or funny meme
- Gets people clicking, which trains engagement

### Subject Lines

**Format:** `DTC Money Minute #X: lowercase curiosity hook`

**Style rotation:**
- 70% curiosity-driven (default) — "the product research hack that changed everything"
- 20% direct benefit (when hard numbers) — "2.3x ROAS from one settings change"
- 10% question format (pattern break) — "what's actually stopping your first sale?"

**Hard rules:**
- Always lowercase after the colon
- Zero emojis
- No ALL CAPS words
- Under 50 characters total
- Never start with "How to"

### Voice Application

**Approach:** Guiding principles, not strict template

**Sentence rhythm (Hormozi pattern):**
- Punch (3-6 words) → Setup (12-18 words) → Land it (3-6 words)
- Average: 8-12 words per sentence
- Never 25+ words unless story with payoff
- 60% short punches (under 10 words)
- 30% medium setups (10-18 words)
- 10% longer only when necessary

**Test:** Read out loud. Out of breath = too long. Robotic = add flow.

**Specificity:** Use concrete numbers when available, don't force them

**Anti-patterns (NEVER use):**
- "game-changer", "unlock your potential", "leverage", "synergy"
- "dive deep", "unpack", "at the end of the day"
- "It's worth noting", "Interestingly enough"
- "In today's fast-paced world", "In the ever-evolving landscape"
- "Take it to the next level", "Move the needle"
- "Circle back", "Touch base", "Low-hanging fruit"
- "Empower", "Revolutionize", "Transform your business"
- "Secret sauce", "Silver bullet", "Holy grail"
- "Crushing it", "Killing it" (unless quoting someone)
- "I'm excited to share", "I'm thrilled to announce"
- Excessive exclamation points
- Starting sentences with "So," or "Look,"
- "Without further ado"

### Content Selection Logic

**Source priority:** Best available by outlier score, regardless of source

**Section 2:** Prioritize by outlier score — YouTube, Reddit, or Perplexity

**Section 3:** Whatever has the best narrative potential

**Sparse content fallback:** Perplexity fills gaps when aggregated content is weak

**Reuse policy:** Same source can feed multiple sections if angles are transformed

### Output Formatting

**Section headers:** None — sections flow naturally

**Visual breaks:** None — natural paragraph flow handles transitions

**Link formatting:** Claude's discretion based on context

**Beehiiv readiness:** Copy-paste ready, zero edits needed

### Claude's Discretion
- Exact link formatting per context
- Section ratio adjustments when content quality varies
- Story vs lesson balance in Section 3
- Loading skeleton and error state handling (technical)

</decisions>

<specifics>
## Specific Ideas

- Subject line fatigue is real — same pattern every time = declining open rates over 30-60 days. The numbered format gives consistency, the hook style rotation keeps it fresh.
- 80%+ of the list is stuck at product research — lean into that psychology with curiosity gaps
- Hormozi: "beyond the headline [the PS is] the most read part of the email so not having a PS statement is PS stupid"
- Tool recommendation should feel like insider trading without sounding gimmicky

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-newsletter-engine*
*Context gathered: 2026-01-31*
