# TubeLab API Decision

**Date:** 2026-01-31
**Decision:** TubeLab API (primary) + YouTube Data API (fallback)

## Research Findings

Initial research incorrectly concluded TubeLab had no public API. This was wrong.

**TubeLab DOES have a public API:**
- **Base URL:** `https://public-api.tubelab.net/v1`
- **Auth:** `Authorization: Api-Key <key>` header
- **Rate Limit:** 10 requests/minute
- **Key Endpoint:** `GET /search/outliers?query=<topic>` (5 credits)
- **Documentation:** https://tubelab.net/docs/api

The confusion arose because:
1. TubeLab.app (web app) is a JavaScript SPA without visible API docs
2. API documentation lives on tubelab.net/docs/api (different domain)

## User Action

User configured **both** API keys:

```bash
TUBELAB_API_KEY=configured in .env
YOUTUBE_API_KEY=configured in .env
```

This enables the hybrid approach: TubeLab as primary, YouTube as fallback.

## Implementation Path

**Chosen approach:** TubeLab API (primary) + YouTube Data API (fallback)

### TubeLab (Primary)

| Setting | Value |
|---------|-------|
| API Key | `TUBELAB_API_KEY` in .env |
| Base URL | `https://public-api.tubelab.net/v1` |
| Auth Header | `Authorization: Api-Key {key}` |
| Rate Limit | 10 requests/minute |
| Outlier Endpoint | `/search/outliers?query=<topic>` |
| Cost | 5 credits per search |

**Usage:**
```python
headers = {"Authorization": f"Api-Key {api_key}"}
response = requests.get(
    "https://public-api.tubelab.net/v1/search/outliers",
    headers=headers,
    params={"query": "ecommerce"}
)
```

### YouTube Data API (Fallback)

| Setting | Value |
|---------|-------|
| API Key | `YOUTUBE_API_KEY` in .env |
| Base URL | `https://www.googleapis.com/youtube/v3` |
| Quota | 10,000 units/day (free) |
| Search Cost | 100 units per request |

**Fallback triggers:**
- TubeLab rate limit exceeded (HTTP 429)
- TubeLab credits exhausted
- TubeLab API error (5xx)
- TubeLab API key not configured

**Fallback calculation:**
Use existing `execution/scoring.py` pattern:
- Fetch channel's last 50 videos for baseline
- Calculate outlier score: `views / channel_avg * recency * modifiers`

## Impact on Plan 03 (YouTube Fetcher)

Plan 03 will implement a **hybrid YouTube fetcher**:

1. **tubelab_client.py** - TubeLab API client
   - GET /search/outliers for topic-based outlier search
   - Rate limiting (10 req/min)
   - Error handling with fallback trigger

2. **youtube_fetcher.py** - YouTube Data API fallback
   - Channel video listing
   - Video statistics
   - Manual outlier score calculation

3. **youtube_aggregate.py** - Orchestrator
   - Try TubeLab first
   - Fall back to YouTube Data API if TubeLab fails
   - Unified output format for pipeline

### API Priority Logic

```
1. Check TUBELAB_API_KEY exists
2. Call TubeLab /search/outliers
3. If success: return normalized results
4. If failure: log error, try YouTube Data API fallback
5. If TUBELAB_API_KEY missing: skip to YouTube directly
```

## env Variables Required

| Variable | Status | Purpose |
|----------|--------|---------|
| `TUBELAB_API_KEY` | Configured | Primary API |
| `YOUTUBE_API_KEY` | Configured | Fallback API |

## Summary

The hybrid approach provides:
- **Convenience:** TubeLab's pre-built outlier scores
- **Reliability:** YouTube Data API as fallback
- **Cost optimization:** Only use TubeLab credits when available
- **Graceful degradation:** Pipeline continues even if TubeLab fails

---
*Decision documented: 2026-01-31*
*Implementation: Plan 03 (YouTube Fetcher)*
