# Content Aggregation
<!-- DOE-VERSION: 2026.01.31 -->

## Goal

Run the full content aggregation pipeline in a single command. Fetches content from multiple sources (Reddit, YouTube, Perplexity), applies deduplication, performs virality analysis, and outputs structured content sheets (CSV + JSON) for newsletter generation.

---

## Trigger Phrases

**Matches:**
- "aggregate content"
- "fetch reddit posts"
- "fetch youtube videos"
- "run content pipeline"
- "get trending content"
- "aggregate all sources"
- "generate content sheet"

---

## Quick Start

```bash
# All core sources (Reddit + YouTube)
python execution/content_aggregate.py

# Reddit only with higher threshold
python execution/content_aggregate.py --sources reddit --min-score 3.0

# Include stretch sources (Twitter, TikTok, Amazon)
python execution/content_aggregate.py --include-stretch

# All sources including Perplexity research
python execution/content_aggregate.py --sources reddit,youtube,perplexity
```

---

## What It Does

1. **Fetch Reddit** — Hot/top posts from target subreddits (r/shopify, r/dropship, r/ecommerce)
2. **Fetch YouTube** — Outlier videos via TubeLab API (with YouTube Data API fallback)
3. **Perplexity Research** — Optional trend research with citations (--sources perplexity)
4. **Stretch Sources** — Optional Twitter, TikTok, Amazon (--include-stretch)
5. **Deduplicate** — Filters content seen in last 4 weeks across all sources
6. **Virality Analysis** — Analyzes hooks, triggers, confidence for each item
7. **Content Sheet** — Generates CSV and JSON with full metadata
8. **Cache** — Saves raw data to `data/content_cache/` for future runs

---

## Output

**Content Sheet Location:** `output/content_sheet.csv` and `output/content_sheet.json`

**Cache Locations:**
- Reddit: `data/content_cache/reddit/reddit_YYYY-MM-DD.json`
- YouTube: `data/content_cache/youtube/youtube_YYYY-MM-DD.json`
- Transcripts: `data/content_cache/transcripts/transcripts_YYYY-MM-DD.json`
- Perplexity: `data/content_cache/perplexity/YYYY-MM-DD_*.json`

**Console output example:**
```
=== DTC Newsletter Content Aggregation Pipeline ===
Started: 2026-01-31 14:00:00 UTC
Sources: reddit, youtube
Minimum outlier score: 2.0x
...

=== Content Aggregation Results ===

By Source:
  reddit: 42
  youtube: 15

Total content: 57
Duplicates removed: 8
Posts with 3x+ outlier score: 12

Top content (3x+ outliers):
1. [7.5x] How I grew from $0 to $50k/mo (r/shopify)
   URL: https://reddit.com/...

2. [6.2x] 5 Secret Tips for E-commerce (YT: ChannelName)
   URL: https://youtube.com/...

Content Sheet Stats:
  Total items: 49
  Score range: 2.1 - 7.5
  Average score: 3.42
```

---

## Prerequisites

### API Keys

```
# Required for Reddit
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_app_name/1.0

# Required for YouTube (at least one)
TUBELAB_API_KEY=your_tubelab_key
YOUTUBE_API_KEY=your_youtube_key

# Optional for Perplexity
PERPLEXITY_API_KEY=pplx-...

# Optional for stretch sources
APIFY_TOKEN=your_apify_token
```

Get credentials:
- Reddit: https://www.reddit.com/prefs/apps
- TubeLab: https://tubelab.net/dashboard
- YouTube: https://console.cloud.google.com
- Perplexity: https://perplexity.ai/settings/api
- Apify: https://apify.com/account/integrations

### Dependencies

```bash
pip install praw python-dotenv openai google-api-python-client youtube-transcript-api
```

---

## CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--sources` | `reddit,youtube` | Comma-separated source list |
| `--no-youtube` | - | Skip YouTube fetching |
| `--no-perplexity` | - | Skip Perplexity research |
| `--min-score` | `2.0` | Minimum outlier score to include |
| `--limit` | `50` | Max items per source |
| `--subreddits` | `shopify,dropship,ecommerce` | Comma-separated subreddit list |
| `--no-dedup` | - | Skip deduplication |
| `--dedup-weeks` | `4` | Weeks to look back for duplicates |
| `--output-format` | `both` | Output format: csv, json, or both |
| `--no-save` | - | Don't save to cache or output |
| `--show-all` | - | Show all items, not just top 10 |
| `--include-stretch` | - | Include Twitter, TikTok, Amazon |

---

## Sources

| Source | Module | API Required | Notes |
|--------|--------|--------------|-------|
| Reddit | `reddit_fetcher.py` | Reddit API | Core source, always available |
| YouTube | `youtube_fetcher.py` | TubeLab or YouTube | TubeLab primary, YouTube fallback |
| Perplexity | `perplexity_client.py` | Perplexity | Trend research, optional |
| Twitter | `twitter_aggregate.py` | Apify | Stretch source |
| TikTok | `tiktok_aggregate.py` | Apify | Stretch source |
| Amazon | `amazon_aggregate.py` | Apify | Stretch source |

---

## Content Sheet Format

### CSV Columns

| Column | Description |
|--------|-------------|
| source | reddit, youtube, twitter, etc. |
| id | Unique content ID |
| title | Content title |
| url | Direct link |
| thumbnail_url | Thumbnail image |
| author | Author or channel name |
| published_at | Publication timestamp |
| views | View/upvote count |
| engagement_score | Primary engagement metric |
| outlier_score | Calculated outlier score |
| hook_type | question, number, story, etc. |
| emotional_triggers | Detected triggers (greed, fear, etc.) |
| virality_confidence | definite, likely, possible, unclear |
| replication_notes | How to replicate success |

### JSON Structure

```json
{
  "metadata": {
    "generated_at": "2026-01-31T14:00:00Z",
    "total_items": 49,
    "sources": ["reddit", "youtube"]
  },
  "contents": [
    {
      "source": "reddit",
      "id": "abc123",
      "title": "...",
      "outlier_score": 7.5,
      "virality_analysis": {
        "hook_analysis": {...},
        "emotional_triggers": [...],
        "success_factors": {...},
        "virality_confidence": "definite",
        "replication_notes": "..."
      }
    }
  ]
}
```

---

## Edge Cases

### No API credentials
**Fix:** Script continues with available sources, skips others with warning

### Rate limiting
**Fix:** TubeLab (10 req/min) and transcript fetching (1.5s delay) handle rate limits

### Empty results
**Fix:** Script reports "No content found" and exits gracefully

### Deduplication removes all content
**Fix:** Use `--no-dedup` or `--dedup-weeks 1` for shorter lookback

---

## Changelog

### 2026.01.31
- Added YouTube integration (TubeLab + YouTube Data API fallback)
- Added Perplexity research integration
- Added deduplication across all sources
- Added virality analysis with structured output
- Added content sheet generation (CSV + JSON)
- Added transcript fetching for top YouTube videos
- Updated CLI with new source and output options

### 2026.01.29
- Created directive and script for Reddit content aggregation
- Integrates reddit_fetcher.py and storage.py modules
- AI summary placeholders for Phase 4 integration
