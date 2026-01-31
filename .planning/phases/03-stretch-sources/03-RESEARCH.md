# Phase 3: Stretch Sources - Research

**Researched:** 2026-01-31
**Domain:** Social Media & E-commerce API Scraping (Twitter/X, TikTok, Amazon)
**Confidence:** MEDIUM

## Summary

Phase 3 implements "stretch" data sources that add unique signals beyond core sources (Reddit, YouTube, Perplexity). Each platform offers distinct leverage: Twitter/X for founder takes and controversy signals, TikTok for viral product discovery and commerce indicators, and Amazon for velocity/momentum tracking.

Apify emerges as the unified approach for all three sources, offering Python SDK, pay-per-result pricing, and maintained scrapers. This aligns with the "don't hand-roll" principle - existing infrastructure beats custom scrapers for platforms with anti-bot measures.

**Primary recommendation:** Use Apify actors for all three sources via `apify-client` Python SDK. Expect varying reliability - Twitter is most stable, TikTok is moderately stable, Amazon Movers & Shakers via Apify is reliable for the use case.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `apify-client` | Latest | Run Apify actors from Python | Official SDK, handles auth, dataset retrieval |
| `requests` | 2.31+ | HTTP client (already in project) | Fallback/simple API calls |
| `python-dotenv` | 1.0+ | API key management (already in project) | Keep APIFY_TOKEN in .env |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tenacity` | 8.x | Retry with exponential backoff | All Apify calls - graceful degradation |
| `cachetools` | 5.x | In-memory TTL cache | 24-hour cache for stretch sources |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Apify TikTok | pyktok | pyktok has 442 GitHub stars but relies on browser automation, more fragile, TikTok frequently breaks it |
| Apify Amazon | Amazon PA-API | PA-API requires Amazon Associates approval, strict TOS, no Movers & Shakers endpoint |
| Apify Twitter | Twitter Official API | $100-5000/month, severe rate limits |

**Installation:**
```bash
pip install apify-client tenacity cachetools
```

## Architecture Patterns

### Recommended Project Structure
```
execution/
├── twitter_aggregate.py     # Twitter/X scraper
├── tiktok_aggregate.py      # TikTok scraper  
├── amazon_aggregate.py      # Amazon Movers & Shakers scraper
├── apify_client_base.py     # Shared Apify helper (optional)
├── scoring.py               # Existing - extend for platform-specific scoring
└── content_aggregate.py     # Existing - integrate stretch sources

directives/
├── twitter_aggregate.md     # DOE directive per source
├── tiktok_aggregate.md
└── amazon_aggregate.md
```

### Pattern 1: Apify Actor Invocation
**What:** Standard pattern for calling Apify actors from Python
**When to use:** All stretch source implementations
**Example:**
```python
# Source: https://docs.apify.com/sdk/python
from apify_client import ApifyClient

def fetch_from_apify(actor_id: str, run_input: dict, token: str) -> list:
    """Run an Apify actor and retrieve results."""
    client = ApifyClient(token)
    run = client.actor(actor_id).call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return items
```

### Pattern 2: Graceful Degradation
**What:** Try source, log warning on failure, continue pipeline
**When to use:** All stretch sources - they should never block pipeline
**Example:**
```python
# Source: User decision from CONTEXT.md
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def fetch_stretch_source(source_name: str, fetch_fn) -> list:
    """Attempt fetch with 3 retries, return empty list on failure."""
    try:
        return fetch_fn()
    except Exception as e:
        logger.warning(f"{source_name} failed after retries: {e}")
        return []  # Continue pipeline without this source
```

### Pattern 3: Composite Scoring (Platform-Specific)
**What:** Weight signals differently per platform
**When to use:** Calculating outlier scores that match existing scoring.py pattern
**Example:**
```python
# Twitter: engagement ratio + quote tweet ratio
def score_twitter_post(tweet: dict, account_avg: float) -> float:
    engagement = tweet["likeCount"] + tweet["retweetCount"] + tweet["quoteCount"]
    ratio = engagement / account_avg if account_avg > 0 else engagement
    quote_boost = 1.2 if tweet["quoteCount"] > tweet["retweetCount"] * 0.3 else 1.0
    return ratio * quote_boost

# TikTok: commerce indicators weighted higher
def score_tiktok_video(video: dict, hashtag_avg: float) -> float:
    base_score = video["playCount"] / hashtag_avg if hashtag_avg > 0 else video["playCount"]
    commerce_boost = 1.5 if video.get("isSponsored") or "#tiktokmademebuyit" in str(video.get("hashtags", [])).lower() else 1.0
    return base_score * commerce_boost
```

### Anti-Patterns to Avoid
- **Building custom scrapers:** TikTok and Twitter have sophisticated anti-bot measures. Apify actors are maintained by teams with proxy infrastructure.
- **Ignoring rate limits:** Even with Apify, rapid consecutive calls can trigger issues. Use delays.
- **Blocking pipeline on failure:** Stretch sources are best-effort. Never raise exceptions that halt the main aggregation.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Twitter scraping | Custom Playwright scraper | `apidojo/tweet-scraper` Apify actor | Twitter actively blocks scrapers, Apify handles IP rotation |
| TikTok video data | Custom pyktok wrapper | `clockworks/tiktok-scraper` Apify actor | TikTok changes HTML structure frequently, Apify maintains |
| Amazon trending data | PA-API integration | `junglee/amazon-bestsellers` Apify actor | PA-API doesn't expose Movers & Shakers, requires Associate approval |
| Retry logic | Custom retry loops | `tenacity` library | Handles exponential backoff, jitter, logging correctly |
| Caching | Custom file-based cache | `cachetools.TTLCache` | In-memory, thread-safe, TTL expiration |

**Key insight:** All three platforms actively fight scrapers. The cost of Apify ($0.40-$3.70 per 1000 results) is cheaper than engineer time fixing broken scrapers.

## Common Pitfalls

### Pitfall 1: Assuming pyktok works reliably
**What goes wrong:** pyktok relies on browser automation and TikTok's hidden APIs. TikTok changes these frequently, breaking the library.
**Why it happens:** pyktok README has a prominent warning: "This program may stop working suddenly if TikTok changes how it stores its data."
**How to avoid:** Use Apify's maintained TikTok scrapers instead. They have teams maintaining them.
**Warning signs:** pyktok returning empty results or throwing EmptyResponseException.

### Pitfall 2: Not handling shadow banning
**What goes wrong:** Some tweets/videos don't appear in search results due to platform shadow banning.
**Why it happens:** Twitter and TikTok filter content algorithmically.
**How to avoid:** Accept that some content will be missing. Use multiple search queries. Don't retry infinitely.
**Warning signs:** Significantly fewer results than expected.

### Pitfall 3: Amazon PA-API mismatch
**What goes wrong:** Developers assume PA-API has Movers & Shakers data - it doesn't.
**Why it happens:** PA-API is for product lookup/search, not trending lists.
**How to avoid:** Use Apify's Amazon Bestsellers scraper which can scrape Movers & Shakers URLs directly.
**Warning signs:** PA-API returning product data but no rank change/velocity information.

### Pitfall 4: Ignoring Apify pricing tiers
**What goes wrong:** Costs unexpectedly high because of add-on features or base tier pricing.
**Why it happens:** Twitter actor is $40/1000 tweets on free tier, $0.40/1000 on paid tier. TikTok has add-on costs.
**How to avoid:** Check pricing page. Starter tier ($49/mo) unlocks 99% discounts. Budget accordingly.
**Warning signs:** Apify costs exceeding estimates.

## Code Examples

### Twitter/X via Apify (Recommended)
```python
# Source: https://apify.com/apidojo/tweet-scraper
from apify_client import ApifyClient
import os

def fetch_dtc_tweets(search_terms: list[str], max_per_term: int = 100) -> list[dict]:
    """
    Fetch tweets from DTC-related accounts or search terms.
    
    Cost: ~$0.40 per 1000 tweets (Starter tier)
    Rate: 30-80 tweets/second
    """
    client = ApifyClient(os.getenv("APIFY_TOKEN"))
    
    all_tweets = []
    for term in search_terms:
        run_input = {
            "searchTerms": [term],
            "sort": "Latest",
            "maxItems": max_per_term,
        }
        run = client.actor("apidojo/tweet-scraper").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        all_tweets.extend(items)
    
    return all_tweets

# Example usage:
# tweets = fetch_dtc_tweets(["from:dharmesh", "from:aaborondia", "#dtcbrand"])
```

### TikTok via Apify (Recommended)
```python
# Source: https://apify.com/clockworks/tiktok-scraper
from apify_client import ApifyClient
import os

def fetch_trending_tiktoks(hashtags: list[str], results_per_hashtag: int = 30) -> list[dict]:
    """
    Fetch trending TikTok videos by hashtag.
    
    Cost: ~$3.70 per 1000 results (base), add-ons for filters
    """
    client = ApifyClient(os.getenv("APIFY_TOKEN"))
    
    run_input = {
        "hashtags": hashtags,
        "resultsPerPage": results_per_hashtag,
        "scrapeRelatedVideos": False,
        "shouldDownloadVideos": False,
    }
    
    run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    
    return items

# Example usage:
# videos = fetch_trending_tiktoks(["tiktokmademebuyit", "amazonfinds", "smallbusiness"])
```

### Amazon Movers & Shakers via Apify
```python
# Source: https://apify.com/junglee/amazon-bestsellers
from apify_client import ApifyClient
import os

def fetch_amazon_movers(category_urls: list[str] = None) -> list[dict]:
    """
    Fetch Amazon Movers & Shakers data.
    
    Cost: ~$3.20 per 1000 items
    Supports: Best Sellers, Movers & Shakers, New Releases, Most Wished
    """
    client = ApifyClient(os.getenv("APIFY_TOKEN"))
    
    # Default to broad Movers & Shakers categories
    if category_urls is None:
        category_urls = [
            "https://www.amazon.com/gp/movers-and-shakers/",
            "https://www.amazon.com/gp/movers-and-shakers/beauty/",
            "https://www.amazon.com/gp/movers-and-shakers/hpc/",
        ]
    
    run_input = {
        "startUrls": [{"url": url} for url in category_urls],
    }
    
    run = client.actor("junglee/amazon-bestsellers").call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    
    return items

# Example usage:
# movers = fetch_amazon_movers()
```

### Graceful Degradation Pattern
```python
# Source: User decision from CONTEXT.md
import logging
from typing import Callable
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

logger = logging.getLogger(__name__)

def fetch_with_fallback(
    source_name: str,
    fetch_fn: Callable[[], list],
    max_retries: int = 3
) -> tuple[list, bool]:
    """
    Attempt to fetch from a stretch source with retries.
    
    Returns:
        tuple of (items, success_flag)
    """
    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    def _fetch():
        return fetch_fn()
    
    try:
        items = _fetch()
        logger.info(f"{source_name}: fetched {len(items)} items")
        return items, True
    except RetryError as e:
        logger.warning(f"{source_name}: failed after {max_retries} retries - {e}")
        return [], False
    except Exception as e:
        logger.warning(f"{source_name}: unexpected error - {e}")
        return [], False
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Twitter Official API | Apify scrapers | 2023 (Musk API changes) | Official API now $100-5000/mo, scrapers are only affordable option |
| pyktok for TikTok | Apify TikTok scrapers | Ongoing | pyktok frequently breaks, Apify is maintained |
| Amazon PA-API for trending | Apify scrapers | N/A | PA-API never had trending endpoints |

**Deprecated/outdated:**
- **Twitter v1.1 API**: Fully deprecated
- **Twitter v2 Free tier**: No longer useful for research (only 1500 tweets/month)
- **pyktok without browser**: Requires browser cookies, increasingly fragile

## Platform-Specific Details

### Twitter/X via Apify

**Best Actor:** `apidojo/tweet-scraper`
- **Pricing:** $0.40/1000 tweets (Starter+ tier), $40/1000 on free tier
- **Speed:** 30-80 tweets/second
- **Rating:** 4.4/5 (138 reviews)
- **Features:** Advanced search syntax, profile scraping, list scraping
- **Minimum:** 50 tweets per query (use `twitter-scraper-lite` for smaller queries)

**Search Query Examples for DTC:**
```python
search_terms = [
    "from:shopify lang:en",           # Shopify official
    '"DTC brand" min_faves:100',      # High-engagement DTC mentions
    '#ecommerce viral',                # Viral e-commerce content
    'from:dharmesh OR from:aaborondia',  # DTC founders
]
```

**Output Fields (relevant):**
- `text`, `likeCount`, `retweetCount`, `quoteCount`, `replyCount`
- `author.userName`, `author.followers`, `author.isVerified`
- `createdAt`, `url`

### TikTok via Apify

**Best Actor:** `clockworks/tiktok-scraper` (Apify-maintained)
- **Pricing:** Pay-per-event, ~$3.70/1000 results base + add-ons
- **Rating:** 4.6/5 (192 reviews)
- **Users:** 122K total, 5.4K monthly active
- **Features:** Hashtag, profile, search, video URL scraping

**Relevant Hashtags for DTC:**
```python
hashtags = [
    "tiktokmademebuyit",
    "amazonfinds", 
    "smallbusiness",
    "viralproducts",
    "tiktokshop",
]
```

**Output Fields (relevant):**
- `diggCount` (likes), `shareCount`, `playCount`, `commentCount`, `collectCount`
- `isSponsored`, `isPinned`
- `authorMeta.followers`, `authorMeta.verified`
- `hashtags`, `webVideoUrl`
- Commerce indicators: `commerceUserInfo.commerceUser`, `ttSeller`

**TikTok Shop Note:** No dedicated TikTok Shop trending actor found. The main TikTok scraper can identify commerce users via `ttSeller` and `commerceUserInfo` fields.

### Amazon via Apify

**Best Actor:** `junglee/amazon-bestsellers` (Apify-maintained)
- **Pricing:** $3.20/1000 items
- **Rating:** 4.9/5 (8 reviews)
- **Supports:** Best Sellers, Movers & Shakers, New Releases, Most Wished, Gift Ideas

**Movers & Shakers URLs:**
```python
# These URLs work directly with the actor
urls = [
    "https://www.amazon.com/gp/movers-and-shakers/",
    "https://www.amazon.com/gp/movers-and-shakers/beauty/",
    "https://www.amazon.com/gp/movers-and-shakers/hpc/",  # Health
    "https://www.amazon.de/-/en/gp/movers-and-shakers/",  # Germany
]
```

**Output Fields (relevant):**
- `position`, `name`, `price`, `currency`
- `url`, `thumbnail`, `category`, `categoryUrl`
- Note: Movers & Shakers shows rank changes but actual % change not in Apify output

**Category-Agnostic Strategy:** Start with root Movers & Shakers URL, let the scraper get all top-level categories. Track which categories have most velocity.

## Cost Estimates

| Source | Actor | Est. Daily Volume | Cost/Run | Monthly Cost |
|--------|-------|-------------------|----------|--------------|
| Twitter | apidojo/tweet-scraper | 500 tweets | ~$0.20 | ~$6 |
| TikTok | clockworks/tiktok-scraper | 300 videos | ~$1.11 | ~$33 |
| Amazon | junglee/amazon-bestsellers | 300 items | ~$0.96 | ~$29 |
| **Total** | | | | **~$68/mo** |

Note: Requires Starter tier ($49/mo) for discounted pricing. Total: ~$117/mo including platform.

## Open Questions

1. **TikTok Shop Trending Data**
   - What we know: No dedicated TikTok Shop actor exists. Main scraper has commerce fields.
   - What's unclear: How to get "trending on TikTok Shop" specifically vs general TikTok trending
   - Recommendation: Use hashtag scraping with commerce-focused hashtags, filter for `ttSeller=true`

2. **Amazon Rank Change Percentages**
   - What we know: Apify actor returns position but not % change
   - What's unclear: Whether underlying page has this data or needs separate scrape
   - Recommendation: Accept position-only data, compute velocity by tracking over time

3. **DTC Account Curation for Twitter**
   - What we know: Need list of high-value DTC founder/brand accounts
   - What's unclear: Best source for this list
   - Recommendation: Start with manual curation of 20-30 accounts, expand based on engagement

## Sources

### Primary (HIGH confidence)
- Apify Official Documentation: https://docs.apify.com/sdk/python
- apidojo/tweet-scraper actor page and pricing: https://apify.com/apidojo/tweet-scraper
- clockworks/tiktok-scraper actor page and pricing: https://apify.com/clockworks/tiktok-scraper
- junglee/amazon-bestsellers actor page: https://apify.com/junglee/amazon-bestsellers
- Amazon PA-API documentation: https://webservices.amazon.com/paapi5/documentation/

### Secondary (MEDIUM confidence)
- pyktok GitHub repository (assessed reliability): https://github.com/dfreelon/pyktok

### Tertiary (LOW confidence)
- TikTok Shop trending product availability - unverified, needs runtime testing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Apify SDK is well-documented, officially maintained
- Architecture: MEDIUM - Pattern based on existing codebase analysis, needs validation
- Pitfalls: HIGH - Based on official documentation warnings and pricing pages
- Cost estimates: MEDIUM - Based on pricing pages, actual usage may vary

**Research date:** 2026-01-31
**Valid until:** 2026-03-01 (60 days - Apify actors update frequently)
