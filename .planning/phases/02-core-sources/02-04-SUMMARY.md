---
phase: 02-core-sources
plan: 04
subsystem: integration
tags: [virality-analysis, content-sheet, csv, json, aggregation, deduplication]

# Dependency graph
requires:
  - phase: 02-core-sources
    provides: TubeLab decision (02-01), Perplexity + dedup (02-02), YouTube + transcripts (02-03)
  - phase: 01-foundation
    provides: Outlier scoring (scoring.py), Reddit fetcher, storage patterns
provides:
  - Content sheet generation (CSV + JSON with virality analysis)
  - Virality analyzer with structured AI-parseable output
  - Full source integration (Reddit + YouTube + Perplexity + stretch)
  - Updated DOE directive for content aggregation
affects: [04-newsletter-engine, 06-product-factory]

# Tech tracking
tech-stack:
  added: []
  patterns: [structured-virality-analysis, multi-format-output, graceful-source-degradation]

key-files:
  created:
    - execution/virality_analyzer.py
    - execution/content_sheet.py
    - tests/test_virality_analyzer.py
    - tests/test_content_sheet.py
  modified:
    - execution/content_aggregate.py
    - directives/content_aggregate.md

key-decisions:
  - "Virality analysis produces structured dict, not prose (AI-parseable for Phase 4)"
  - "Content sheet outputs both CSV and JSON by default"
  - "Hook types: question, number, controversy, story, statement (priority order)"
  - "Confidence levels: definite (10x+), likely (5x+), possible (3x+), unclear (<3x)"

patterns-established:
  - "VIRALITY_SCHEMA as contract between virality analyzer and consumers"
  - "CSV columns flattened from nested virality analysis for human readability"
  - "Graceful source degradation: pipeline continues if some sources fail"

# Metrics
duration: 6min
completed: 2026-01-31
---

# Phase 02 Plan 04: Core Sources Integration Summary

**Virality analyzer with structured AI-parseable output, content sheet generation (CSV + JSON), and full source integration (Reddit + YouTube + Perplexity + dedup)**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-31T13:19:22Z
- **Completed:** 2026-01-31T13:25:22Z
- **Tasks:** 3
- **Files created:** 4
- **Files modified:** 2

## Accomplishments

- Created virality_analyzer.py with structured, AI-parseable analysis output
- Created content_sheet.py for CSV and JSON content sheet generation
- Updated content_aggregate.py to integrate all sources (Reddit, YouTube, Perplexity)
- Added deduplication to main pipeline with configurable lookback
- Updated DOE directive to version 2026.01.31 with new CLI options
- 70 new tests (40 virality + 30 content sheet), 308 total tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Create virality analyzer module** - `e54d1eb` (feat)
2. **Task 2: Create content sheet module** - `23b1dc2` (feat)
3. **Task 3: Update content_aggregate.py and DOE directive** - `aa836b6` (feat)

## Files Created/Modified

- `execution/virality_analyzer.py` (188 lines) - Structured virality analysis with VIRALITY_SCHEMA
- `execution/content_sheet.py` (166 lines) - CSV and JSON content sheet generation
- `tests/test_virality_analyzer.py` (264 lines) - 40 tests for virality analyzer
- `tests/test_content_sheet.py` (285 lines) - 30 tests for content sheet
- `execution/content_aggregate.py` (updated) - Integrated all sources, new CLI options
- `directives/content_aggregate.md` (updated) - DOE-VERSION: 2026.01.31

## Virality Analysis Schema

The virality analyzer produces structured output for AI consumption:

```python
VIRALITY_SCHEMA = {
    "hook_analysis": {
        "hook_type": str,  # question, number, controversy, story, statement
        "hook_text": str,  # First 100 chars
        "attention_elements": list,  # money, exclusivity, speed, specificity
    },
    "emotional_triggers": [
        {"trigger": str, "evidence": str, "intensity": str}
    ],
    "timing_factors": {...},
    "success_factors": {
        "key_drivers": list,
        "reproducible_elements": list,
        "unique_circumstances": list,
    },
    "virality_confidence": str,  # definite, likely, possible, unclear
    "replication_notes": str,
}
```

## New CLI Options

| Option | Description |
|--------|-------------|
| `--sources` | Comma-separated: reddit,youtube,perplexity |
| `--no-youtube` | Skip YouTube fetching |
| `--no-perplexity` | Skip Perplexity research |
| `--no-dedup` | Skip deduplication |
| `--dedup-weeks` | Lookback weeks (default: 4) |
| `--output-format` | csv, json, or both (default: both) |

## Decisions Made

1. **Structured virality output** - Dict schema instead of prose summaries for AI parsing in Phase 4
2. **Dual output formats** - Both CSV (human-readable) and JSON (full data) generated each run
3. **Hook type priority** - question > number > controversy > story > statement (first match wins)
4. **Confidence mapping** - Based on outlier score: 10x+ = definite, 5x+ = likely, 3x+ = possible

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all modules implemented successfully with all tests passing.

## User Setup Required

None - no new external service configuration required for this plan.

## Phase 2 Completion

**Phase 2 is now complete.** All 4 plans executed:

| Plan | Description | Commit(s) |
|------|-------------|-----------|
| 02-01 | TubeLab research + decision | c78126c, dfe996c |
| 02-02 | Perplexity + deduplication | 89df773, d47edae |
| 02-03 | YouTube + transcript fetchers | aedc587, 09ebb24 |
| 02-04 | Integration + content sheet | e54d1eb, 23b1dc2, aa836b6 |

**Requirements completed in Phase 2:**
- AGGR-01: Reddit content aggregation (enhanced)
- AGGR-03: YouTube outliers via TubeLab + YouTube Data API
- AGGR-07: Perplexity web research
- AGGR-08: Transcript extraction
- AGGR-09: Deduplication (enhanced with multi-source)
- OUTP-04: Content sheet output (CSV + JSON)

## Next Phase Readiness

- Phase 2 Core Sources complete
- Content pipeline delivers structured output for newsletter generation
- Ready for Phase 4 (Newsletter Engine) - virality analysis feeds into generation
- All API keys already configured (TubeLab, YouTube, Perplexity pending)

---
*Phase: 02-core-sources*
*Completed: 2026-01-31*
