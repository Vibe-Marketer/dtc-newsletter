# Phase 2: Core Sources (YouTube + Perplexity) - Research

**Researched:** 2026-01-31
**Domain:** YouTube content aggregation with outlier detection, Perplexity research integration, transcript fetching
**Confidence:** MEDIUM (HIGH for youtube-transcript-api, Perplexity; LOW for TubeLab API specifics)

## Summary

This phase adds two content sources: YouTube with outlier detection and Perplexity for research/trends. The youtube-transcript-api library (v1.2.4) is well-documented, actively maintained, and provides robust transcript fetching without requiring YouTube API keys. Perplexity's API offers three distinct services: Chat Completions (Sonar models), Agentic Research (pro-search preset), and Search (raw results).

TubeLab is a YouTube analytics tool that provides outlier detection, but its website requires JavaScript and API documentation could not be fetched directly. Per user decisions, we'll research TubeLab first, then checkpoint for account creation. The fallback approach using YouTube Data API with manual outlier scoring is well-established.

**Primary recommendation:** Use youtube-transcript-api for transcripts, Perplexity's pro-search preset for research, and implement TubeLab integration with YouTube Data API fallback.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| youtube-transcript-api | 1.2.4 | Fetch YouTube transcripts | No API key required, supports auto-generated subtitles, 6.8k GitHub stars |
| perplexityai | latest | Perplexity API client | Official SDK, supports all three API types |
| requests | >=2.31.0 | HTTP client for TubeLab/YouTube Data API | Already in project, standard for Python HTTP |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| google-api-python-client | >=2.0 | YouTube Data API (fallback) | If TubeLab unavailable/too expensive |
| python-dotenv | >=1.0.0 | Environment variables | Already in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| youtube-transcript-api | YouTube Data API | Data API requires OAuth, more complex, quota limits |
| Perplexity | OpenAI + web scraping | Perplexity has native search grounding, better for trend research |
| TubeLab | Manual outlier scoring | TubeLab has pre-built outlier detection; manual requires more API calls |

**Installation:**
```bash
pip install youtube-transcript-api perplexityai
# Fallback if TubeLab unavailable:
pip install google-api-python-client
```

## Architecture Patterns

### Recommended Project Structure
```
execution/
├── youtube_fetcher.py      # TubeLab or YouTube Data API + outlier scoring
├── transcript_fetcher.py   # youtube-transcript-api wrapper
├── perplexity_client.py    # Perplexity API integration
├── deduplication.py        # Hash-based dedup across sources
├── storage.py              # Extend existing for YouTube/Perplexity
└── content_aggregate.py    # Extend to orchestrate all sources
data/
└── content_cache/
    ├── reddit/             # (existing)
    ├── youtube/            # YouTube videos + metadata
    ├── perplexity/         # Research summaries
    └── transcripts/        # Fetched transcripts
```

### Pattern 1: Content Source Abstraction
**What:** Each content source follows same interface pattern
**When to use:** Adding new content sources
**Example:**
```python
# Source: existing reddit_fetcher.py pattern
class YouTubeFetcher:
    def fetch_all(self, channels: list[str], limit: int, min_outlier_score: float) -> list[dict]:
        """Fetch videos from channels, calculate outlier scores."""
        pass
    
    def _process_video(self, video: dict, channel_avg: float) -> dict:
        """Standardize video data with outlier score."""
        return {
            "id": video["id"],
            "title": video["title"],
            "url": f"https://youtube.com/watch?v={video['id']}",
            "thumbnail_url": video["thumbnail"],
            "views": video["views"],
            "channel_avg_views": channel_avg,
            "outlier_score": round(video["views"] / channel_avg, 2),
            "source": "youtube",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
```

### Pattern 2: Perplexity Two-Stage Research
**What:** First query for trending topics, second for deep dive
**When to use:** Getting fresh research data
**Example:**
```python
# Source: Perplexity official docs
from perplexity import Perplexity

def research_trends(client: Perplexity, topic: str) -> dict:
    """Stage 1: Get trending topics in e-commerce."""
    response = client.responses.create(
        preset="pro-search",
        input=f"What are the top trending topics in {topic} this week?",
        response_format={
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "trends": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "topic": {"type": "string"},
                                    "summary": {"type": "string"},
                                    "why_trending": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    return response

def deep_dive(client: Perplexity, topic: str) -> dict:
    """Stage 2: Deep dive on specific topic."""
    response = client.responses.create(
        preset="pro-search",
        input=f"Provide a detailed analysis of {topic} for e-commerce businesses",
        web_search_options={
            "search_recency_filter": "week"
        }
    )
    return response
```

### Pattern 3: Hash-Based Deduplication
**What:** Content hashing to prevent repeating content from last 4 weeks
**When to use:** Before storing any new content
**Example:**
```python
import hashlib
from pathlib import Path

def generate_content_hash(content: dict) -> str:
    """Generate hash from content identifiers."""
    # Use source + id for uniqueness
    key = f"{content['source']}:{content['id']}"
    return hashlib.md5(key.encode()).hexdigest()

def load_seen_hashes(weeks_back: int = 4) -> set[str]:
    """Load content hashes from last N weeks."""
    # Load from all cache files in date range
    pass

def is_duplicate(content: dict, seen_hashes: set[str]) -> bool:
    """Check if content was seen before."""
    return generate_content_hash(content) in seen_hashes
```

### Anti-Patterns to Avoid
- **Fetching all transcripts eagerly:** Only fetch for top 10 high-scoring videos per run
- **Ignoring rate limits:** youtube-transcript-api can hit IP bans; implement backoff
- **Storing raw API responses:** Always normalize to standard schema
- **Hardcoding channel lists:** Store channels in config for easy updates

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YouTube transcript fetching | Scraping YouTube pages | youtube-transcript-api | Handles auto-generated subs, translations, edge cases |
| Web-grounded research | LLM + manual web scraping | Perplexity API | Native web search with citations |
| YouTube video metadata | Manual page scraping | YouTube Data API or TubeLab | Proper API with consistent data format |
| Content hashing | Custom hash algorithm | hashlib.md5 | Standard, fast, sufficient for dedup |

**Key insight:** YouTube and Perplexity both have proper APIs. Don't scrape web pages - use the official tools.

## Common Pitfalls

### Pitfall 1: YouTube IP Bans
**What goes wrong:** youtube-transcript-api uses undocumented YouTube API, can get blocked
**Why it happens:** Too many requests, especially from cloud IPs (AWS, GCP, Azure)
**How to avoid:** 
- Run locally first (residential IP)
- Implement request delays (1-2 seconds between requests)
- Consider proxy configuration if needed
**Warning signs:** `RequestBlocked` or `IpBlocked` exceptions

### Pitfall 2: Perplexity Rate Limits
**What goes wrong:** API calls fail with rate limit errors
**Why it happens:** Too many requests per minute/day
**How to avoid:**
- Implement exponential backoff
- Cache research results (they're slow-changing)
- Use batch queries where possible
**Warning signs:** 429 HTTP status codes

### Pitfall 3: Missing Transcripts
**What goes wrong:** High-scoring videos have no transcript available
**Why it happens:** Video is new, no captions uploaded, language not supported
**How to avoid:**
- Handle `TranscriptsDisabled`, `NoTranscriptFound` exceptions gracefully
- Try auto-generated transcripts first, fall back to manual
- Log which videos lack transcripts for manual review
**Warning signs:** Multiple `NoTranscriptFound` errors in logs

### Pitfall 4: Outdated Outlier Averages
**What goes wrong:** Outlier scores become meaningless over time
**Why it happens:** Channel averages calculated once and never updated
**How to avoid:**
- Recalculate channel averages each run
- Store sample of recent videos for average calculation
- Use 100+ video sample for stable average (per existing Reddit pattern)
**Warning signs:** Outlier scores consistently >10x or <1x

### Pitfall 5: TubeLab API Key Not Set
**What goes wrong:** Code attempts TubeLab calls without valid credentials
**Why it happens:** User skipped account creation step
**How to avoid:**
- Checkpoint in plan: "Get TubeLab API key" with verification
- Graceful fallback to YouTube Data API
- Clear error messages when key missing
**Warning signs:** API auth failures on first run

## Code Examples

Verified patterns from official sources:

### YouTube Transcript Fetching
```python
# Source: https://github.com/jdepoix/youtube-transcript-api (v1.2.4)
from youtube_transcript_api import YouTubeTranscriptApi

def fetch_transcript(video_id: str) -> list[dict]:
    """Fetch transcript for a YouTube video."""
    ytt_api = YouTubeTranscriptApi()
    
    try:
        # Fetch transcript, prefer English
        transcript = ytt_api.fetch(video_id, languages=['en'])
        return transcript.to_raw_data()
    except Exception as e:
        # Handle TranscriptsDisabled, NoTranscriptFound, etc.
        print(f"Warning: Could not fetch transcript for {video_id}: {e}")
        return []

def list_available_transcripts(video_id: str) -> list[dict]:
    """List all available transcript languages for a video."""
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)
    
    return [
        {
            "language": t.language,
            "language_code": t.language_code,
            "is_generated": t.is_generated,
            "is_translatable": t.is_translatable,
        }
        for t in transcript_list
    ]
```

### Perplexity Chat Completions
```python
# Source: https://docs.perplexity.ai/docs/getting-started/quickstart
from perplexity import Perplexity
import os

def get_perplexity_client() -> Perplexity:
    """Initialize Perplexity client."""
    # Uses PERPLEXITY_API_KEY env var automatically
    return Perplexity()

def search_trends(topic: str) -> dict:
    """Get trending e-commerce topics with citations."""
    client = get_perplexity_client()
    
    completion = client.chat.completions.create(
        model="sonar-pro",  # Advanced search with citations
        messages=[
            {
                "role": "user",
                "content": f"What are the most viral e-commerce and DTC topics this week? Focus on {topic}."
            }
        ],
        web_search_options={
            "search_recency_filter": "week"
        }
    )
    
    return {
        "content": completion.choices[0].message.content,
        "citations": completion.citations or [],
        "model": completion.model,
        "usage": {
            "prompt_tokens": completion.usage.prompt_tokens,
            "completion_tokens": completion.usage.completion_tokens,
        }
    }
```

### Outlier Scoring (Extend Existing Pattern)
```python
# Source: existing execution/scoring.py pattern
def calculate_youtube_outlier_score(
    views: int,
    channel_avg_views: float,
    post_timestamp: float,
    title: str,
    description: str = "",
) -> float:
    """
    Calculate outlier score for YouTube video.
    
    Formula: (views / channel_avg) * recency_boost * engagement_modifiers
    """
    if channel_avg_views <= 0:
        raise ValueError("channel_avg_views must be positive")
    
    # Base score: how many times better than average
    base_score = views / channel_avg_views
    
    # Apply recency boost (reuse from scoring.py)
    recency = calculate_recency_boost(post_timestamp)
    
    # Apply engagement modifiers (reuse from scoring.py)
    engagement = calculate_engagement_modifiers(title, description)
    
    return base_score * recency * engagement
```

### Virality Analysis Structure
```python
# Source: 02-CONTEXT.md decisions - structured for AI consumption
VIRALITY_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "hook_analysis": {
            "type": "object",
            "properties": {
                "hook_type": {"type": "string"},  # question, statement, number, controversy
                "hook_text": {"type": "string"},
                "attention_grabbing_elements": {"type": "array", "items": {"type": "string"}},
            }
        },
        "emotional_triggers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "trigger": {"type": "string"},  # fear, greed, curiosity, urgency
                    "evidence": {"type": "string"},
                    "intensity": {"type": "string"}  # low, medium, high
                }
            }
        },
        "timing_factors": {
            "type": "object",
            "properties": {
                "day_of_week": {"type": "string"},
                "relevant_events": {"type": "array", "items": {"type": "string"}},
                "seasonal_relevance": {"type": "string"}
            }
        },
        "replication_notes": {
            "type": "object",
            "properties": {
                "key_success_factors": {"type": "array", "items": {"type": "string"}},
                "reproducible_elements": {"type": "array", "items": {"type": "string"}},
                "unique_circumstances": {"type": "array", "items": {"type": "string"}}
            }
        },
        "virality_confidence": {
            "type": "string",
            "enum": ["definite", "likely", "possible", "unclear"]
        }
    }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Scraping YouTube pages | youtube-transcript-api library | 2018+ | Reliable transcript access without headless browser |
| Manual web research | Perplexity API with grounding | 2024+ | Citations included, real-time web search |
| Basic view counts | Outlier detection (views ÷ channel avg) | 2023+ | Normalized comparison across different channel sizes |

**Deprecated/outdated:**
- Selenium-based YouTube scraping: Replaced by youtube-transcript-api
- Manual outlier calculation: TubeLab provides pre-computed scores (if available)

## TubeLab Research (INCOMPLETE - Requires User Input)

**Status:** TubeLab website requires JavaScript; API documentation could not be fetched automatically.

**What we know:**
- TubeLab is a YouTube analytics tool for creators
- Provides "outlier detection" feature
- Has a web interface at tubelab.app
- Per user decisions: Research first, then checkpoint for account creation

**What's unclear:**
- API availability (public API vs web-only tool)
- Pricing structure
- API endpoints and authentication
- Rate limits and data format

**Recommended approach:**
1. User manually visits https://www.tubelab.app/pricing and https://www.tubelab.app/api
2. User creates account if API is available and affordable
3. User obtains API key and documents endpoints
4. If no API or too expensive: Implement YouTube Data API fallback

**Fallback implementation (YouTube Data API):**
```python
# Fallback if TubeLab unavailable
from googleapiclient.discovery import build

def get_youtube_client() -> any:
    """Initialize YouTube Data API client."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY environment variable required")
    return build("youtube", "v3", developerKey=api_key)

def fetch_channel_videos(client, channel_id: str, max_results: int = 50) -> list[dict]:
    """Fetch recent videos from a channel."""
    # Note: YouTube Data API has quota limits (10,000 units/day)
    # Each search.list costs 100 units
    request = client.search().list(
        part="snippet",
        channelId=channel_id,
        order="date",
        maxResults=max_results,
        type="video"
    )
    response = request.execute()
    return response.get("items", [])
```

## Recommended DTC/E-commerce YouTube Channels

Based on the phase requirements for broad DTC/e-commerce content:

| Channel | Focus | Why Include |
|---------|-------|-------------|
| Oberlo | Dropshipping | High-quality educational content |
| Wholesale Ted | E-commerce | Actionable Shopify tutorials |
| Gabriel St-Germain | DTC brands | Case studies and strategies |
| Davie Fogarty | E-commerce | Founder of The Oodie, real experience |
| Jon Dykstra | Digital marketing | SEO and content for e-commerce |
| MyWifeQuitHerJob | E-commerce | Steve Chou's practical advice |
| Learn With Shopify | Shopify official | Platform updates and best practices |
| Ecom King | Dropshipping | Cameron Fattahi's tutorials |
| Dan Vas | E-commerce | FBA and general e-com |
| Chase Dimond | Email marketing | DTC email strategy |

**Note:** Claude's discretion per CONTEXT.md - these are suggestions to be validated during implementation.

## Open Questions

Things that couldn't be fully resolved:

1. **TubeLab API Availability**
   - What we know: Tool exists, website at tubelab.app
   - What's unclear: Whether API exists, pricing, authentication
   - Recommendation: User checkpoint to research manually, implement YouTube Data API fallback

2. **Perplexity Model Pricing**
   - What we know: sonar, sonar-pro, sonar-reasoning-pro, sonar-deep-research models exist
   - What's unclear: Exact per-request pricing for each model
   - Recommendation: Use sonar-pro for quality (per user decision "best quality available")

3. **YouTube Data API Quota Management**
   - What we know: 10,000 units/day free tier, search costs 100 units
   - What's unclear: Exact usage patterns needed for daily runs
   - Recommendation: Cache aggressively, fetch only what's needed

## Sources

### Primary (HIGH confidence)
- https://github.com/jdepoix/youtube-transcript-api - v1.2.4 documentation
- https://pypi.org/project/youtube-transcript-api/ - Package info and version
- https://docs.perplexity.ai/docs/getting-started/quickstart - API quickstart
- https://docs.perplexity.ai/api-reference/chat-completions-post - API reference

### Secondary (MEDIUM confidence)
- Existing codebase: execution/scoring.py, execution/storage.py, execution/reddit_fetcher.py
- 02-CONTEXT.md: User decisions from discussion phase

### Tertiary (LOW confidence)
- TubeLab capabilities: Based on general knowledge, website not accessible
- Channel recommendations: Based on training data, not verified as current

## Metadata

**Confidence breakdown:**
- youtube-transcript-api: HIGH - Official docs fetched and verified
- Perplexity API: HIGH - Official docs fetched and verified
- TubeLab API: LOW - Website requires JavaScript, no direct verification
- Outlier scoring pattern: HIGH - Based on existing codebase
- Channel list: LOW - Training data only, needs validation

**Research date:** 2026-01-31
**Valid until:** 2026-02-28 (30 days - APIs are generally stable)
