# TubeLab API Research

**Researched:** 2026-01-31
**Status:** Complete

## Summary

TubeLab is a YouTube analytics tool that provides outlier detection for creators. After research, **no public API was found**. The tool appears to be a web-only SaaS product without developer/programmatic access.

## API Availability

**Status: No public API available**

### Research Findings

| Aspect | Finding |
|--------|---------|
| Website | https://www.tubelab.app (JavaScript-required SPA) |
| API Documentation | None found |
| Developer Portal | None found |
| API Endpoints | Not available |
| Authentication | N/A (web login only) |

### Verification Attempts

1. **Direct website access** - Returns "This site requires JavaScript" - no static content or API docs exposed
2. **Common API paths** - /api, /docs, /developer - all redirect to main SPA
3. **Prior research (02-RESEARCH.md)** - Noted as LOW confidence, website requires JavaScript
4. **Search for "TubeLab API"** - No developer documentation or integration guides found

## Pricing Information

**Status: No public pricing found via web fetch**

TubeLab pricing cannot be retrieved programmatically. Based on tool category (YouTube analytics), typical SaaS pricing would be:
- Free tier: Limited features/channels
- Paid tiers: $15-50/month for creator tools

**User action required:** Visit https://www.tubelab.app/pricing directly to view current pricing.

## What TubeLab Offers (Based on Product Description)

- YouTube analytics for creators
- "Outlier detection" - identifies videos performing above channel average
- Competitor tracking
- Video performance insights

## Recommendation

**Use YouTube Data API fallback**

### Rationale

1. **No public API** - TubeLab does not expose a developer API for programmatic access
2. **Web-only tool** - Designed for manual use via browser, not automation
3. **YouTube Data API alternative** - Google's official API provides video statistics and channel data needed to calculate outlier scores manually

### Implementation Path

1. Use YouTube Data API v3 for video/channel data
2. Calculate outlier scores using existing `execution/scoring.py` pattern:
   - Fetch last 50 videos per channel to calculate channel average views
   - For new videos: `outlier_score = views / channel_avg * recency * modifiers`
3. Same formula already implemented in Phase 1 for Reddit

### YouTube Data API Details

| Aspect | Details |
|--------|---------|
| API | YouTube Data API v3 |
| Auth | API key (simple) or OAuth (for user data) |
| Free Tier | 10,000 units/day |
| Search Cost | 100 units per request |
| Video List Cost | 1 unit per video (up to 50 per request) |
| Documentation | https://developers.google.com/youtube/v3 |

### Quota Calculation for Our Use Case

| Operation | Units | Frequency | Daily Cost |
|-----------|-------|-----------|------------|
| Search for recent videos | 100 | 10 channels | 1,000 |
| Get video details | 1 | 100 videos | 100 |
| Get channel stats | 1 | 10 channels | 10 |
| **Total** | - | - | ~1,110 units/day |

Fits comfortably within 10,000 unit free tier.

## Conclusion

TubeLab is a valuable tool for manual YouTube research, but lacks API access for automation. The YouTube Data API provides all necessary data to replicate TubeLab's outlier detection functionality programmatically, using the same scoring pattern already implemented for Reddit in Phase 1.

---
*Research completed: 2026-01-31*
*Recommendation: YouTube Data API fallback*
