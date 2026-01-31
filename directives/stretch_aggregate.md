# Stretch Sources Orchestration
<!-- DOE-VERSION: 2026.01.31 -->

## Goal
Run all stretch sources (Twitter, TikTok, Amazon) in parallel with graceful degradation.

## Trigger Phrases
- "run stretch sources"
- "get all stretch data"
- "stretch aggregation"
- "fetch twitter tiktok amazon"

## Quick Start
```bash
python execution/stretch_aggregate.py
python execution/stretch_aggregate.py --sequential
```

## What It Does
1. Runs Twitter, TikTok, and Amazon aggregators (parallel by default)
2. Isolates failures - one source failing doesn't block others
3. Merges results sorted by outlier score
4. Reports which sources succeeded/failed

## CLI Options
| Flag | Default | Description |
|------|---------|-------------|
| --sequential | false | Run sources one at a time |

## Output
- Console summary showing success/failure per source
- Top 10 items across all sources
- Returns dict with: sources_succeeded, sources_failed, items, total_items

## Integration
Use with content_aggregate.py:
```python
from execution.stretch_aggregate import run_all_stretch_sources, merge_stretch_results

# Get stretch results
stretch = run_all_stretch_sources()

# Merge with core (Reddit/YouTube) results
combined = merge_stretch_results(stretch, core_items)
```

## Graceful Degradation
- If APIFY_TOKEN missing: all sources fail gracefully
- If one actor fails: other sources continue
- Success = at least one source returned data
