# TubeLab API Research

**Researched:** 2026-01-31
**Updated:** 2026-01-31 (API discovered)
**Status:** Complete

## Summary

TubeLab is a YouTube analytics tool that provides outlier detection for creators. **A public API IS available** at `https://public-api.tubelab.net/v1`.

## API Availability

**Status: Public API available**

### API Details

| Aspect | Details |
|--------|---------|
| Base URL | `https://public-api.tubelab.net/v1` |
| Documentation | https://tubelab.net/docs/api |
| Authentication | `Authorization: Api-Key <key>` header |
| Rate Limit | 10 requests/minute |
| Billing | Credits-based (subscription required) |

### Key Endpoints

| Endpoint | Cost | Description |
|----------|------|-------------|
| `GET /search/outliers?query=ecommerce` | 5 credits | Search for outlier videos by topic |
| `GET /search/outliers/related` | 5 credits | Find related outlier content |
| `GET /video/transcript/{id}` | TBD | Get video transcript |
| `GET /channel/videos/{id}` | TBD | Get channel videos |

### Authentication

```bash
curl -H "Authorization: Api-Key YOUR_KEY" \
  "https://public-api.tubelab.net/v1/search/outliers?query=ecommerce"
```

## Pricing Information

**Status: Credits-based subscription**

- Requires TubeLab subscription with API credits
- Each outlier search costs 5 credits
- Exact pricing tiers available at https://tubelab.net/pricing

## Correction from Initial Research

Initial research (web fetch) incorrectly concluded no API existed because:
1. TubeLab.app (the web app) is a JavaScript SPA that doesn't expose API docs
2. The API lives on a different domain (`tubelab.net` vs `tubelab.app`)
3. API documentation is at `tubelab.net/docs/api`, not on the main app

## Recommendation

**Use TubeLab API as primary source with YouTube Data API as fallback**

### Rationale

1. **TubeLab provides pre-built outlier detection** - No need to calculate scores manually
2. **Rate limit manageable** - 10 requests/minute is sufficient for weekly newsletter
3. **YouTube Data API as fallback** - If TubeLab credits exhausted or API unavailable, fall back to manual scoring
4. **Hybrid approach** - Best of both worlds: convenience of TubeLab + reliability of YouTube fallback

### Implementation Path

**Primary: TubeLab API**
1. Use `/search/outliers?query=<topic>` to find trending videos
2. Outlier scores provided directly by API
3. 10 requests/minute rate limit - add delays between calls

**Fallback: YouTube Data API**
1. If TubeLab fails (rate limit, credits exhausted, API error)
2. Use YouTube Data API v3 for video/channel data
3. Calculate outlier scores using existing `execution/scoring.py` pattern

### YouTube Data API Details (Fallback)

| Aspect | Details |
|--------|---------|
| API | YouTube Data API v3 |
| Auth | API key |
| Free Tier | 10,000 units/day |
| Search Cost | 100 units per request |
| Documentation | https://developers.google.com/youtube/v3 |

## Conclusion

TubeLab's public API provides exactly what we need: outlier detection for YouTube videos. Using it as the primary source with YouTube Data API as fallback provides both convenience (pre-built scores) and reliability (Google's infrastructure as backup).

---
*Research completed: 2026-01-31*
*Research corrected: 2026-01-31*
*Recommendation: TubeLab primary, YouTube Data API fallback*
