# Amazon Movers & Shakers Aggregation
<!-- DOE-VERSION: 2026.01.31 -->

## Goal
Fetch trending products from Amazon's Movers & Shakers to surface products before they go viral on social media.

## Trigger Phrases
- "get amazon trends"
- "fetch amazon movers"
- "amazon aggregation"
- "run amazon aggregate"

## Quick Start
```bash
python execution/amazon_aggregate.py
python execution/amazon_aggregate.py --min-score 2.0
```

## What It Does
1. Scrapes Amazon Movers & Shakers pages via Apify
2. Extracts position and sales rank change percentage
3. Calculates velocity-weighted outlier score
4. Returns products sorted by momentum

## CLI Options
| Flag | Default | Description |
|------|---------|-------------|
| --min-score | 1.0 | Minimum outlier score threshold |

## Output
- Console display of top movers with position and velocity
- Returns dict with: success, items, categories, duration_seconds
- Graceful degradation on failure

## Scoring
- Position score (30%): Top 10 rank = higher score
- Velocity score (70%): Percentage gain in sales rank
- Products with +1000% gains rank highest

## Unique Value
Amazon surfaces:
- Products trending before social media catches on
- Category-agnostic velocity tracking
- Price point and review data for product ideas
- Real purchase intent signals (not just views)
