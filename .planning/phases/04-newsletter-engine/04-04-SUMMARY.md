---
phase: 04-newsletter-engine
plan: 04
subsystem: generation
tags: [subject-line, preview-text, orchestrator, doe-directive, newsletter]

# Dependency graph
requires:
  - phase: 04-01
    provides: ClaudeClient with prompt caching, voice profile
  - phase: 04-02
    provides: ContentSelection, generate_section_1, generate_section_2
  - phase: 04-03
    provides: generate_section_3, generate_section_4, generate_section_5
provides:
  - Subject line generator with 70/20/10 style rotation
  - Preview text generator (hooks, not generic)
  - Full newsletter orchestrator (content to Beehiiv-ready markdown)
  - DOE directive for "generate newsletter" trigger
affects: [05-affiliate-system]

# Tech tracking
tech-stack:
  added: []
  patterns: [style-rotation, validation-with-retry, orchestration-pipeline, doe-crystallization]

key-files:
  created:
    - execution/subject_line_generator.py
    - execution/newsletter_generator.py
    - directives/newsletter_generate.md
    - tests/test_subject_line_generator.py
    - tests/test_newsletter_generator.py
  modified: []

key-decisions:
  - "Subject line style rotation: curiosity 70%, direct_benefit 20%, question 10%"
  - "Subject line format: 'DTC Money Minute #X: lowercase hook' under 50 chars"
  - "Preview text must be a hook (40-90 chars), never 'View in browser'"
  - "Newsletter output includes metadata comments (<!-- Subject: ... -->)"
  - "DOE directive version: 2026.01.31 (matches script)"

patterns-established:
  - "Validation with retry on failure (stricter prompt on second attempt)"
  - "Full orchestration pipeline: select -> generate -> validate -> format"
  - "Beehiiv-ready markdown with metadata comments"
  - "CLI with --dry-run for safe testing"

# Metrics
duration: ~20 min
completed: 2026-01-31
---

# Phase 4 Plan 04: Subject Lines, Preview Text, and Newsletter Orchestrator Summary

**Subject lines with validation, preview text hooks, full newsletter orchestrator, and DOE crystallization**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-01-31T13:44:08Z
- **Completed:** 2026-01-31T14:05:00Z
- **Tasks:** 2
- **Files created:** 5

## Accomplishments

- Created subject line generator with 70/20/10 style rotation (curiosity/direct_benefit/question)
- Validation ensures <50 chars, lowercase after colon, no emojis, no ALL CAPS in hook
- Created preview text generator for email preheaders (40-90 char hooks)
- Built full newsletter orchestrator that chains: content selection -> 5 sections -> subject -> preview -> markdown
- DOE directive crystallized with matching version 2026.01.31
- CLI interface with all required options (--content-file, --issue-number, --tool-*, --ps-type, --dry-run)
- 64 tests (35 subject line + 29 orchestrator)

## Task Commits

Each task was committed atomically:

1. **Task 1: Subject Line and Preview Text Generators** - `0e01deb` (feat)
2. **Task 2: Newsletter Orchestrator and DOE Directive** - `ca880a3` (feat)

## Files Created/Modified

- `execution/subject_line_generator.py` - Subject line + preview text generation with validation
- `execution/newsletter_generator.py` - Full orchestrator with CLI interface
- `directives/newsletter_generate.md` - DOE directive with trigger phrases
- `tests/test_subject_line_generator.py` - 35 tests for subject line/preview
- `tests/test_newsletter_generator.py` - 29 tests for orchestrator

## Decisions Made

1. **Style rotation weights:** 70% curiosity (engagement driver), 20% direct benefit (concrete value), 10% question (assumption challenger). Weights based on email marketing best practices.

2. **Subject line format:** "DTC Money Minute #X: hook" ensures brand consistency while keeping total under 50 chars. Hook must be lowercase (all lowercase after colon).

3. **Validation with retry:** If Claude returns an invalid subject line, we retry once with a stricter prompt. This handles occasional AI deviation without failing.

4. **Preview text as hook:** Preview text must complement (not repeat) subject line and create curiosity. Generic "View in browser" is explicitly prohibited.

5. **Metadata comments:** Output includes `<!-- Subject: ... -->` and `<!-- Preview: ... -->` at top for easy Beehiiv copy/paste.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test fixture to mock content selector**
- **Found during:** Task 2 test validation
- **Issue:** Integration tests passed only 1 content item, but `select_content_for_sections` requires enough content to populate all sections. Section 3 was not being called because no content was selected for it.
- **Fix:** Updated `mock_all_generators` fixture to also mock `select_content_for_sections` returning a `ContentSelection` with all sections populated.
- **Files modified:** tests/test_newsletter_generator.py
- **Commit:** Included in ca880a3

---

**Total deviations:** 1 bug fix
**Impact on plan:** Minimal - tests now correctly verify orchestrator behavior

## Issues Encountered

None - bug was caught and fixed during test validation phase.

## User Setup Required

None - all required API keys were already configured in previous plans.

## Verification Results

- `python -m pytest tests/test_subject_line_generator.py tests/test_newsletter_generator.py -v` - 64 tests passing
- `python execution/newsletter_generator.py --help` - Shows all CLI options
- `grep "DOE-VERSION: 2026.01.31" directives/newsletter_generate.md execution/newsletter_generator.py` - Versions match
- Total project tests: 562

## Next Phase Readiness

- Phase 4 Newsletter Engine COMPLETE
- Ready for Phase 5 Affiliate System
- Newsletter generation can now produce Beehiiv-ready markdown from aggregated content

---
*Phase: 04-newsletter-engine*
*Completed: 2026-01-31*
