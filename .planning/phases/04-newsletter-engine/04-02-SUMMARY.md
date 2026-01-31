---
phase: 04-newsletter-engine
plan: 02
subsystem: generation
tags: [content-selection, outlier-score, diversity-constraint, section-generators, xml-prompts]

# Dependency graph
requires:
  - phase: 04-newsletter-engine
    provides: Voice profile, anti-pattern validator, Claude client with prompt caching
provides:
  - Content selector with diversity constraint (select_content_for_sections)
  - Section 1 generator for 30-60 word instant reward
  - Section 2 generator for 300-500 word tactical content
  - ContentSelection dataclass for structured selections
affects: [04-03, 04-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [content-selection-by-type, diversity-constraint, lenient-word-validation]

key-files:
  created:
    - execution/content_selector.py
    - tests/test_content_selector.py
  modified:
    - execution/section_generators.py
    - tests/test_section_generators.py

key-decisions:
  - "Diversity constraint: at least 2 different sources when possible"
  - "Section 2 prioritizes tactical content (THE MEAT)"
  - "Word count validation warns but doesn't fail (lenient mode)"
  - "Section 1 can reuse content from other sections (quote/hook is different use)"

patterns-established:
  - "Content type detection via keyword matching (_is_tactical, _is_quotable, _has_narrative_potential)"
  - "Fallback with angle flag when content is sparse"
  - "Prior sections passed for narrative coherence"

# Metrics
duration: 5 min
completed: 2026-01-31
---

# Phase 4 Plan 02: Content Selector and Section 1 & 2 Generators Summary

**Content selector prioritizes by outlier score with 2+ source diversity, section generators create 30-60 word hooks and 300-500 word tactical content with lenient validation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-31T13:35:51Z
- **Completed:** 2026-01-31T13:41:29Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created content selector with outlier score prioritization and diversity constraint
- Content type detection: quotable (short/stats), tactical (how-to), narrative (stories)
- Section 1 generates 30-60 word instant reward hooks
- Section 2 generates 300-500 word tactical content (THE MEAT)
- Lenient word count validation (warns, doesn't fail)
- 73 tests passing (44 content selector + 29 section generators)

## Task Commits

Each task was committed atomically:

1. **Task 1: Content Selector Module** - `bfb97c5` (feat)
2. **Task 2: Section Generators Update** - `d2f3dc0` (feat)

## Files Created/Modified

- `execution/content_selector.py` - ContentSelection dataclass, select_content_for_sections(), type detection helpers
- `tests/test_content_selector.py` - 44 tests for content selection logic
- `execution/section_generators.py` - Updated word count validation to lenient mode
- `tests/test_section_generators.py` - 29 tests for section generators

## Decisions Made

1. **Diversity constraint:** Require at least 2 different sources in selection when possible to avoid same-source newsletters
2. **Tactical prioritization:** Section 2 specifically looks for tactical content first (most important section)
3. **Lenient validation:** Word count violations log warnings but don't fail generation (allows Claude flexibility)
4. **Quotable overlap:** Section 1 can use same content as other sections since it's a different transformation (quote/hook)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tests passed on first implementation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Content selector ready for newsletter orchestration
- Section 1 and 2 generators ready for content transformation
- Ready for 04-03-PLAN.md (Section 3 & 4 generators + Subject line generator)

---
*Phase: 04-newsletter-engine*
*Completed: 2026-01-31*
