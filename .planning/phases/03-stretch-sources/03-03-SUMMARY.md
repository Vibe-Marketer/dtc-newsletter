---
phase: 03-stretch-sources
plan: 03
subsystem: aggregation
tags: [orchestration, parallel-execution, graceful-degradation, threading]

# Dependency graph
requires:
  - phase: 03-01
    provides: Apify foundation + Twitter aggregator
  - phase: 03-02
    provides: TikTok + Amazon aggregators
provides:
  - Stretch sources orchestrator (run_all_stretch_sources)
  - Merge function for core + stretch items
  - Integration flag for content_aggregate.py
affects: [phase-4-newsletter-engine, phase-7-pipeline-integration]

# Tech tracking
tech-stack:
  added: [ThreadPoolExecutor]
  patterns: [parallel-execution-with-failure-isolation, graceful-degradation]

key-files:
  created:
    - execution/stretch_aggregate.py
    - directives/stretch_aggregate.md
    - tests/test_stretch_aggregate.py
  modified:
    - execution/content_aggregate.py

key-decisions:
  - "Parallel by default with ThreadPoolExecutor(max_workers=3)"
  - "Success = at least one source worked"
  - "Stretch items weighted 0.8x when merged with core"
  - "Module import at runtime for graceful degradation"

patterns-established:
  - "Parallel execution pattern: ThreadPoolExecutor with as_completed"
  - "Failure isolation: run_source_safely wraps each source"
  - "Optional module import: _stretch_aggregate pattern"

# Metrics
duration: 3min
completed: 2026-01-31
---

# Phase 3 Plan 3: Stretch Sources Orchestrator Summary

**Unified orchestrator running Twitter, TikTok, and Amazon in parallel with graceful degradation; integrated with content_aggregate.py via --include-stretch flag**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-31T12:49:01Z
- **Completed:** 2026-01-31T12:52:20Z
- **Tasks:** 2/2
- **Files modified:** 4 (3 created, 1 modified)

## Accomplishments

- Created stretch_aggregate.py orchestrator with parallel execution
- Implemented run_source_safely for failure isolation
- Added merge_stretch_results for combining stretch + core items
- Integrated --include-stretch flag into content_aggregate.py
- 18 tests for orchestration logic

## Task Commits

1. **Task 1: Stretch Sources Orchestrator** - `cf69ae7` (feat)
2. **Task 2: Integration with Content Aggregate** - `795ffc5` (feat)

## Files Created/Modified

- `execution/stretch_aggregate.py` - Orchestrator with parallel execution and graceful degradation
- `directives/stretch_aggregate.md` - DOE directive with trigger phrases and usage
- `tests/test_stretch_aggregate.py` - 18 tests for orchestration and merging
- `execution/content_aggregate.py` - Added --include-stretch flag and integration

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Parallel execution by default | ThreadPoolExecutor with max_workers=3 for I/O-bound API calls |
| Success = at least one source | Pipeline continues even if 1-2 sources fail |
| Stretch weight 0.8x | Stretch sources less reliable than core, adjust scores accordingly |
| Runtime import | Module import inside function for graceful degradation if modules missing |

## Deviations from Plan

None - plan executed exactly as written.

## Source Reliability Assessment

Based on implementation and research from 03-RESEARCH.md:

| Source | Expected Reliability | Notes |
|--------|---------------------|-------|
| Twitter | High | Apify actor well-maintained, 4.4/5 rating |
| TikTok | Medium | Platform changes frequently, Apify maintains |
| Amazon | High | Movers & Shakers data stable, 4.9/5 rating |

## Issues Encountered

None - all implementations straightforward.

## Recommendations for Production

1. **Cost Management:** Apify Starter tier ($49/mo) unlocks 99% discounts
2. **Monitoring:** Track sources_succeeded/sources_failed per run
3. **Caching:** 24-hour TTL cache in apify_base.py already handles this
4. **Graceful Degradation:** Pipeline continues without stretch data if APIFY_TOKEN missing

## Next Phase Readiness

- Phase 3 (Stretch Sources) complete
- All three stretch sources implemented with unified orchestrator
- Integration with content_aggregate.py ready
- Ready for Phase 4 (Newsletter Engine) or Phase 2 continuation

---
*Phase: 03-stretch-sources*
*Completed: 2026-01-31*
