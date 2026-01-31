---
phase: 03-stretch-sources
plan: 02
subsystem: aggregation
tags: [tiktok, amazon, apify, scraping, commerce-detection, velocity-scoring]

# Dependency graph
requires:
  - phase: 03-stretch-sources/01
    provides: apify_base.py with fetch_from_apify, fetch_with_retry
provides:
  - TikTok aggregator with commerce indicator detection
  - Amazon Movers & Shakers aggregator with velocity scoring
  - DOE directives for both sources
affects: [phase-4-newsletter-engine, phase-7-pipeline-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Commerce detection via platform flags and keyword matching
    - Velocity-weighted scoring (70% velocity, 30% position)
    - 1.5x commerce boost for TikTok product videos

key-files:
  created:
    - execution/tiktok_aggregate.py
    - execution/amazon_aggregate.py
    - directives/tiktok_aggregate.md
    - directives/amazon_aggregate.md
    - tests/test_tiktok_aggregate.py
    - tests/test_amazon_aggregate.py
  modified: []

key-decisions:
  - "TikTok commerce boost: 1.5x for videos with commerce indicators"
  - "Amazon scoring: 30% position + 70% velocity weighting"

patterns-established:
  - "is_commerce_video() checks ttSeller, isSponsored, commerceUserInfo, keywords"
  - "Percentage parsing handles +1,234% format with commas and plus signs"

# Metrics
duration: 3 min
completed: 2026-01-31
---

# Phase 3 Plan 2: TikTok + Amazon Aggregators Summary

**TikTok commerce-weighted aggregator and Amazon Movers & Shakers velocity scorer implemented with 34 passing tests**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-31T12:43:15Z
- **Completed:** 2026-01-31T12:46:15Z
- **Tasks:** 2
- **Files created:** 6

## Accomplishments
- TikTok aggregator with commerce indicator detection (ttSeller, isSponsored, keywords)
- Commerce videos receive 1.5x score boost for outlier ranking
- Amazon Movers & Shakers aggregator with velocity-weighted scoring
- Position (30%) + velocity (70%) hybrid scoring for Amazon products
- Percentage parsing handles all formats (+1,234% with commas)
- DOE directives matching script versions (2026.01.31)

## Task Commits

Each task was committed atomically:

1. **Task 1: TikTok Aggregator** - `a46f5f4` (feat)
2. **Task 2: Amazon Aggregator** - `f195166` (feat)

## Files Created
- `execution/tiktok_aggregate.py` - TikTok video aggregator with commerce detection
- `execution/amazon_aggregate.py` - Amazon Movers & Shakers aggregator
- `directives/tiktok_aggregate.md` - DOE directive for TikTok
- `directives/amazon_aggregate.md` - DOE directive for Amazon
- `tests/test_tiktok_aggregate.py` - 18 tests for TikTok scoring
- `tests/test_amazon_aggregate.py` - 16 tests for Amazon scoring

## Decisions Made
- **TikTok commerce boost:** 1.5x multiplier for videos with commerce indicators (ttSeller, isSponsored, commerceUserInfo, or commerce keywords in description)
- **Amazon scoring weights:** Position contributes 30%, velocity contributes 70% - prioritizes momentum over current rank

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness
- TikTok and Amazon aggregators ready for integration
- Both export standardized functions for pipeline orchestration
- Graceful degradation built in via fetch_with_retry
- 34 tests confirm scoring logic correctness
- Ready for Phase 3 Plan 03 (Twitter integration) or Phase 7 pipeline integration

---
*Phase: 03-stretch-sources*
*Completed: 2026-01-31*
