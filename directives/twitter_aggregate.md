# Twitter/X Content Aggregation
<!-- DOE-VERSION: 2026.01.31 -->

## Goal
Fetch viral tweets from DTC founders and brands to surface unique signals not found on Reddit.

## Trigger Phrases
- "get twitter trends"
- "fetch dtc tweets"
- "twitter aggregation"
- "run twitter aggregate"

## Quick Start
```bash
python execution/twitter_aggregate.py
python execution/twitter_aggregate.py --min-score 3.0
```

## What It Does
1. Searches Twitter for DTC-relevant terms via Apify
2. Calculates outlier scores (engagement vs account average)
3. Applies quote boost for controversial/viral content
4. Returns scored tweets sorted by outlier score

## CLI Options
| Flag | Default | Description |
|------|---------|-------------|
| --min-score | 2.0 | Minimum outlier score threshold |
| --max-per-term | 50 | Max tweets per search term |

## Output
- Console display of top tweets with scores
- Returns dict with: success, items, total_fetched, duration_seconds
- Graceful degradation on failure (logs warning, returns empty)

## Unique Value
Twitter surfaces:
- Founder hot takes and opinions
- Product launch announcements
- Controversy and drama (high quote ratio)
- Viral threads with tactical advice

## Configuration

### Environment Variables
- `APIFY_TOKEN` - Required for Twitter scraping via Apify

### Search Terms (Default)
- "shopify founder"
- "dtc brand launch"
- "ecommerce revenue"
- "dropshipping 2026"
- "#dtcbrand viral"

## Scoring Algorithm

Outlier score = (total_engagement / account_avg) * quote_boost

Where:
- total_engagement = likes + retweets + quotes + replies
- account_avg = 1000 (default baseline)
- quote_boost = 1.3x if quotes > 30% of retweets, else 1.0x

High quote ratio indicates controversial/discussion-worthy content.

## Dependencies
- execution/apify_base.py - Shared Apify utilities
- apify-client - Apify Python SDK
- tenacity - Retry logic
- cachetools - TTL caching (24 hours)

## Cost
~$0.40 per 1000 tweets (Apify Starter tier)
