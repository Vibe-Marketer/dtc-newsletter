# Phase 3: Stretch Sources - Implementation Plan

**Created:** 2026-01-31
**Time Budget:** 2 days
**Status:** Ready for execution

## Goal

Implement Twitter/X, TikTok, and Amazon Movers & Shakers as "best effort" data sources that add unique signals beyond core sources. Each source should gracefully degrade on failure without blocking the pipeline.

## Success Criteria

1. Three working aggregation scripts (`twitter_aggregate.py`, `tiktok_aggregate.py`, `amazon_aggregate.py`)
2. Each source surfaces content that other sources miss (unique leverage)
3. Failures retry 3x then continue pipeline without that source
4. DOE directives created for each source
5. Integration with existing `content_aggregate.py` pattern

---

## Task Breakdown

### Task 1: Foundation Setup
**Time:** 30 minutes
**Dependencies:** None

1.1 Add new dependencies to `requirements.txt`:
```
apify-client>=1.6.0
tenacity>=8.2.0
cachetools>=5.3.0
```

1.2 Add `APIFY_TOKEN` placeholder to `.env.example`

1.3 Create `execution/apify_base.py` with shared utilities:
- `fetch_from_apify(actor_id, run_input)` - base actor invocation
- `fetch_with_fallback(source_name, fetch_fn)` - graceful degradation wrapper
- TTL cache setup (24-hour)

**Verification:**
- [ ] `pip install -r requirements.txt` succeeds
- [ ] Import `from execution.apify_base import fetch_from_apify` works

---

### Task 2: Twitter/X Aggregator
**Time:** 3 hours
**Dependencies:** Task 1

2.1 Create `execution/twitter_aggregate.py`:
- Use `apidojo/tweet-scraper` Apify actor
- Search queries for DTC founders/brands (curated list of 20-30 accounts)
- Hashtag searches: `#dtcbrand`, `#shopify`, `#ecommerce viral`

2.2 Implement Twitter-specific scoring in script:
```python
def score_twitter_post(tweet, account_avg):
    engagement = likes + retweets + quotes
    ratio = engagement / account_avg
    quote_boost = 1.2 if quotes > retweets * 0.3 else 1.0
    return ratio * quote_boost
```

2.3 Output format matching existing pattern:
```json
{
  "source": "twitter",
  "id": "tweet_id",
  "text": "...",
  "author": "...",
  "engagement": {...},
  "outlier_score": 4.2,
  "url": "https://twitter.com/..."
}
```

2.4 Create `directives/twitter_aggregate.md`

**Verification:**
- [ ] `python execution/twitter_aggregate.py` returns tweets or graceful failure
- [ ] Output includes outlier scores
- [ ] Surfaces founder takes/controversy not found on Reddit

---

### Task 3: TikTok Aggregator
**Time:** 3 hours
**Dependencies:** Task 1

3.1 Create `execution/tiktok_aggregate.py`:
- Use `clockworks/tiktok-scraper` Apify actor
- Hashtags: `tiktokmademebuyit`, `amazonfinds`, `smallbusiness`, `viralproducts`, `tiktokshop`
- Filter for commerce indicators: `ttSeller=true`, `commerceUserInfo.commerceUser=true`

3.2 Implement TikTok-specific scoring:
```python
def score_tiktok_video(video, hashtag_avg):
    base_score = play_count / hashtag_avg
    commerce_boost = 1.5 if is_commerce_video(video) else 1.0
    return base_score * commerce_boost
```

3.3 Commerce detection:
- Check `isSponsored`, `ttSeller` fields
- Check for commerce hashtags in text
- Check `commerceUserInfo` object

3.4 Create `directives/tiktok_aggregate.md`

**Verification:**
- [ ] `python execution/tiktok_aggregate.py` returns videos or graceful failure
- [ ] Commerce videos weighted higher in output
- [ ] Surfaces viral products not found on Reddit/Twitter

---

### Task 4: Amazon Movers & Shakers Aggregator
**Time:** 3 hours
**Dependencies:** Task 1

4.1 Create `execution/amazon_aggregate.py`:
- Use `junglee/amazon-bestsellers` Apify actor
- Start URLs: root Movers & Shakers + Beauty + Health
- Category-agnostic: track which categories have most velocity

4.2 Implement Amazon-specific scoring:
```python
def score_amazon_product(product, category_avg_rank):
    # Lower rank = better, so invert
    position_score = (100 - product["position"]) / 100
    # Boost products that jumped many positions
    velocity_score = estimate_velocity(product)
    return position_score * velocity_score
```

4.3 Track velocity over time:
- Store previous day's positions in cache
- Calculate rank change between runs
- Highlight biggest movers

4.4 Create `directives/amazon_aggregate.md`

**Verification:**
- [ ] `python execution/amazon_aggregate.py` returns products or graceful failure
- [ ] Output shows rank position and estimated velocity
- [ ] Surfaces trending products before they hit social media

---

### Task 5: Integration & Testing
**Time:** 2 hours
**Dependencies:** Tasks 2, 3, 4

5.1 Create `execution/stretch_aggregate.py` orchestrator:
- Runs all three sources in parallel (where possible)
- Collects results with success/failure flags
- Outputs combined JSON with source metadata

5.2 Add stretch sources to main pipeline:
- Modify `content_aggregate.py` to optionally include stretch sources
- Add `--include-stretch` flag
- Merge results by outlier score, preserve source attribution

5.3 Test graceful degradation:
- Temporarily break each source (bad API key)
- Verify pipeline continues with remaining sources
- Check logging shows which sources succeeded/failed

5.4 Create `directives/stretch_aggregate.md` for orchestrator

**Verification:**
- [ ] `python execution/stretch_aggregate.py` runs all sources
- [ ] Pipeline continues when 1-2 sources fail
- [ ] Output metadata shows `sources_succeeded` and `sources_failed`

---

## File Manifest

### New Files
| File | Purpose |
|------|---------|
| `execution/apify_base.py` | Shared Apify client utilities |
| `execution/twitter_aggregate.py` | Twitter/X data fetcher |
| `execution/tiktok_aggregate.py` | TikTok data fetcher |
| `execution/amazon_aggregate.py` | Amazon Movers & Shakers fetcher |
| `execution/stretch_aggregate.py` | Orchestrator for all stretch sources |
| `directives/twitter_aggregate.md` | DOE directive |
| `directives/tiktok_aggregate.md` | DOE directive |
| `directives/amazon_aggregate.md` | DOE directive |
| `directives/stretch_aggregate.md` | DOE directive |

### Modified Files
| File | Changes |
|------|---------|
| `requirements.txt` | Add apify-client, tenacity, cachetools |
| `.env.example` | Add APIFY_TOKEN placeholder |
| `execution/content_aggregate.py` | Add --include-stretch flag (optional) |

---

## Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Apify actor rate limiting | Medium | Use delays between calls, respect quotas |
| TikTok scraper breaks | Medium | Graceful degradation, log warning, continue |
| Costs exceed estimate | Low | Monitor Apify dashboard, set budget alerts |
| API token missing | Low | Clear error message pointing to setup |

---

## Execution Order

```
Day 1 (harder source + foundation):
  Task 1: Foundation Setup (30 min)
  Task 3: TikTok Aggregator (3 hrs) -- hardest, most API complexity
  Task 2: Twitter Aggregator (3 hrs)

Day 2 (easier source + integration):
  Task 4: Amazon Aggregator (3 hrs) -- most straightforward
  Task 5: Integration & Testing (2 hrs)
```

Total estimated: ~11.5 hours across 2 days

---

## Notes

- All scripts follow existing `content_aggregate.py` patterns
- Each source must provide UNIQUE value (not just more data)
- Failure is acceptable; blocking the pipeline is not
- Cache files go to `data/content_cache/{source}/`
