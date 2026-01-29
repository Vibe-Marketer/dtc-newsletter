# Content Aggregation
<!-- DOE-VERSION: 2026.01.29 -->

## Goal

Run the full Reddit content aggregation pipeline in a single command. Fetches posts from target subreddits (r/shopify, r/dropship, r/ecommerce), calculates outlier scores, and saves results for newsletter generation.

---

## Trigger Phrases

**Matches:**
- "aggregate content"
- "fetch reddit posts"
- "run content pipeline"
- "get trending reddit content"
- "aggregate reddit"

---

## Quick Start

```bash
python execution/content_aggregate.py
```

Show only 3x+ outliers:
```bash
python execution/content_aggregate.py --min-score 3.0
```

Custom subreddits:
```bash
python execution/content_aggregate.py --subreddits shopify,dropship
```

---

## What It Does

1. **Fetch** — Connects to Reddit API via PRAW and fetches hot/top posts from target subreddits
2. **Score** — Calculates outlier scores with recency boost and engagement modifiers
3. **Filter** — Keeps only posts meeting minimum outlier threshold (default 2.0x)
4. **Save** — Caches results to `data/content_cache/reddit/reddit_YYYY-MM-DD.json`
5. **Display** — Shows top posts sorted by outlier score with AI summary placeholders

---

## Output

**Deliverable:** JSON cache file with scored Reddit posts + console summary
**Location:** `data/content_cache/reddit/reddit_YYYY-MM-DD.json`

**Console output example:**
```
=== Content Aggregation Results ===
Posts fetched: 42
Posts meeting threshold: 15
Top posts (3x+ outliers):

1. [5.2x] How I grew from $0 to $50k/mo (r/shopify)
   AI Summary: [placeholder - will be generated in Phase 4]
   URL: https://reddit.com/...

2. [4.8x] The shipping trick that saved my business (r/dropship)
   AI Summary: [placeholder - will be generated in Phase 4]
   URL: https://reddit.com/...
```

---

## Prerequisites

### API Keys

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_app_name/1.0
```

Get credentials at: https://www.reddit.com/prefs/apps

### Dependencies

```bash
pip install praw python-dotenv
```

---

## CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--min-score` | `2.0` | Minimum outlier score to include |
| `--limit` | `50` | Max posts to fetch per subreddit |
| `--subreddits` | `shopify,dropship,ecommerce` | Comma-separated subreddit list |
| `--no-save` | `false` | Show results without saving to cache |
| `--show-all` | `false` | Show all posts, not just top 10 |

---

## Edge Cases

### No Reddit credentials
**Fix:** Script exits with clear error message pointing to .env setup

### Rate limiting
**Fix:** PRAW handles rate limiting automatically; script continues after delay

### Empty results
**Fix:** Script reports "No posts found meeting criteria" and exits gracefully

---

## Changelog

### 2026.01.29
- Created directive and script for Reddit content aggregation
- Integrates reddit_fetcher.py and storage.py modules
- AI summary placeholders for Phase 4 integration
