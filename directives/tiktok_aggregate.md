# TikTok Content Aggregation
<!-- DOE-VERSION: 2026.01.31 -->

## Goal
Fetch viral TikTok videos with commerce indicators to surface trending products before they hit other platforms.

## Trigger Phrases
- "get tiktok trends"
- "fetch tiktok videos"
- "tiktok aggregation"
- "run tiktok aggregate"

## Quick Start
```bash
python execution/tiktok_aggregate.py
python execution/tiktok_aggregate.py --min-score 2.0
```

## What It Does
1. Searches TikTok for commerce-focused hashtags via Apify
2. Detects commerce indicators (TikTok Shop, sponsored, keywords)
3. Applies 1.5x boost for commerce videos
4. Returns scored videos sorted by outlier score

## CLI Options
| Flag | Default | Description |
|------|---------|-------------|
| --min-score | 1.5 | Minimum outlier score threshold |
| --results-per-hashtag | 30 | Max videos per hashtag |

## Output
- Console display of top videos with scores
- Commerce videos tagged with [COMMERCE]
- Returns dict with: success, items, commerce_count, duration_seconds
- Graceful degradation on failure

## Unique Value
TikTok surfaces:
- Products going viral before Amazon/Google trends
- Creator-brand partnerships and collaborations
- TikTok Shop trending items
- "TikTok made me buy it" products
