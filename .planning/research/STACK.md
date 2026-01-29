# Stack Research: Newsletter Automation System

**Research Date:** 2026-01-29
**Purpose:** Define the 2025 standard stack for automated newsletter systems with content aggregation, API integrations, and digital product generation.

---

## Recommended Stack

### Core Runtime

| Component | Choice | Version | Rationale |
|-----------|--------|---------|-----------|
| Language | Python | 3.12+ | Already established in project; best ecosystem for web scraping, API integrations, and AI/ML |
| Package Manager | pip + requirements.txt | - | Simple, matches existing setup; no need for poetry/pdm complexity |
| Environment | python-dotenv | >=1.0.0 | Already in use; handles API keys cleanly |

**Confidence:** HIGH

Python 3.12 is the correct choice. The alternative (Node.js/TypeScript) has stronger async patterns but weaker AI/ML ecosystem and scraping libraries. Given this project's heavy AI and data extraction needs, Python wins decisively.

---

### Content Aggregation

#### TikTok Shop

| Approach | Library/Tool | Confidence |
|----------|--------------|------------|
| **Primary** | `pyktok` (unofficial scraper) | MEDIUM |
| **Fallback** | Playwright + custom scraping | MEDIUM |
| **Ideal** | TikTok Shop Affiliate API | LOW (requires partnership approval) |

**Reality Check:** TikTok Shop has no official public API for content discovery. All approaches require either:
- Unofficial scrapers (risk of breaking)
- Browser automation (Playwright/Selenium)
- Partnership-level API access (6+ month approval process)

**Recommendation:** Start with `pyktok` for trending content discovery. Build a thin abstraction layer so we can swap implementations.

```bash
pip install pyktok playwright
playwright install chromium
```

#### YouTube

| Approach | Library | Version | Confidence |
|----------|---------|---------|------------|
| **Primary** | `google-api-python-client` | >=2.100.0 | HIGH |
| **For transcripts** | `youtube-transcript-api` | >=0.6.0 | HIGH |

**API Access:** Official YouTube Data API v3 - free tier allows 10,000 quota units/day (sufficient for weekly newsletter).

```bash
pip install google-api-python-client youtube-transcript-api
```

**Confidence:** HIGH

#### Twitter/X

| Approach | Library | Confidence |
|----------|---------|------------|
| **Primary** | Official X API v2 (Basic tier $100/mo) | MEDIUM |
| **Alternative** | `nitter` instances + scraping | LOW |
| **Alternative** | `snscrape` (broken since 2023) | DEPRECATED |

**Reality Check:** X API is expensive ($100/mo minimum for useful access) and rate-limited. For a weekly newsletter, manual curation + AI summarization may be more cost-effective than API access.

**Recommendation:** If budget allows, use official API via `tweepy`:
```bash
pip install tweepy>=4.14.0
```

If not, consider RSS feeds from accounts that cross-post, or manual curation with AI-assisted summarization.

**Confidence:** MEDIUM (depends on budget allocation)

#### Amazon (Product/Affiliate Data)

| Approach | Library | Confidence |
|----------|---------|------------|
| **Primary** | Amazon Product Advertising API (PA-API 5.0) | HIGH |
| **Scraping fallback** | `playwright` + custom | LOW (ToS risk) |

**API Access:** Requires Amazon Associates account (already have for affiliate). PA-API gives product data, pricing, reviews.

```bash
pip install paapi5-python-sdk
# or use raw requests - SDK is thin wrapper
```

**Confidence:** HIGH (official API, affiliate account likely exists)

#### Reddit

| Approach | Library | Version | Confidence |
|----------|---------|---------|------------|
| **Primary** | `praw` | >=7.7.0 | HIGH |

**API Access:** Free tier sufficient for weekly content. 100 requests/minute, 1000/day on basic OAuth.

```bash
pip install praw>=7.7.0
```

**Confidence:** HIGH

#### Perplexity

| Approach | Library | Confidence |
|----------|---------|------------|
| **Primary** | Perplexity API (pplx-api) | HIGH |
| **Alternative** | Use Claude with web search tools | MEDIUM |

**API Access:** Perplexity offers API access at $0.20-1.00 per 1M tokens depending on model. Good for real-time research.

```bash
pip install requests  # Direct API calls, no official SDK needed
```

**Confidence:** HIGH

---

### Email Platform Integration

#### Beehiiv API

| Endpoint | Purpose | Availability |
|----------|---------|--------------|
| `POST /publications/{id}/posts` | Create draft posts | **Enterprise only (beta)** |
| `GET /posts` | List existing posts | All tiers |
| `POST /subscriptions` | Manage subscribers | All tiers |

**Critical Discovery:** The Posts Create endpoint (for creating drafts programmatically) is **Enterprise-only and in beta**. This is a significant constraint.

**Options:**
1. **Upgrade to Enterprise** - Unlocks full automation capability
2. **Hybrid approach** - Generate content as Markdown/HTML files, manually paste into Beehiiv
3. **Alternative platform** - Consider ConvertKit or Buttondown if API access is critical

**Recommended:** Given 100K+ subscriber scale, Enterprise tier is likely justified. Confirm with Beehiiv sales on timeline/pricing.

```python
# Beehiiv API integration (Enterprise)
import requests

BEEHIIV_API = "https://api.beehiiv.com/v2"

def create_draft(publication_id: str, title: str, content: str, api_key: str):
    return requests.post(
        f"{BEEHIIV_API}/publications/{publication_id}/posts",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "title": title,
            "body_content": content,  # Raw HTML
            "status": "draft"
        }
    )
```

**Confidence:** HIGH (API is well-documented, just needs Enterprise tier)

#### Alternatives Considered

| Platform | API Quality | Why Not |
|----------|-------------|---------|
| ConvertKit | Excellent | Would require migration of 100K subscribers |
| Buttondown | Good | Smaller platform, less feature-rich |
| Mailchimp | Mediocre | Expensive at scale, bloated |

**Recommendation:** Stay with Beehiiv, pursue Enterprise tier for API access.

---

### Product Generation

#### Custom GPTs (OpenAI)

| Component | Library | Version | Confidence |
|-----------|---------|---------|------------|
| **GPT creation** | `openai` | >=1.0.0 | HIGH |
| **Assistants API** | `openai` (beta.assistants) | >=1.0.0 | MEDIUM |

**Note:** OpenAI Assistants API is marked deprecated (removal August 2026). Use Responses API for new implementations.

```bash
pip install openai>=1.0.0
```

**Reality:** Custom GPTs cannot be created programmatically via API. They must be configured manually in ChatGPT. What we CAN automate:
- Generate the GPT instructions/system prompt
- Create knowledge base documents
- Package everything for manual GPT creation

**Confidence:** HIGH for content generation, LOW for full automation

#### PDF Generation

| Library | Version | Use Case | Confidence |
|---------|---------|----------|------------|
| **Primary** | `weasyprint` | >=60.0 | Styled PDFs from HTML/CSS | HIGH |
| **Alternative** | `reportlab` | >=4.0.0 | Programmatic PDF creation | HIGH |
| **Simple** | `markdown` + `weasyprint` | - | Markdown to PDF | HIGH |

```bash
pip install weasyprint>=60.0 markdown>=3.5.0
```

**Recommendation:** Use `weasyprint` - it renders HTML/CSS to PDF, allowing template-based generation with consistent branding.

**Confidence:** HIGH

#### Google Sheets Generation

| Library | Version | Confidence |
|---------|---------|------------|
| **Primary** | `gspread` | >=5.10.0 | HIGH |
| **Auth** | `google-auth` | >=2.20.0 | HIGH |

```bash
pip install gspread>=5.10.0 google-auth>=2.20.0
```

**Confidence:** HIGH

#### Small Tools (Calculators, Generators)

| Approach | Technology | Confidence |
|----------|------------|------------|
| **Web-based** | HTML + JavaScript (single file) | HIGH |
| **Hosted** | Streamlit or Gradio | MEDIUM |
| **Notion templates** | Manual creation | HIGH |

**Recommendation:** Generate single-file HTML tools with embedded JavaScript. No hosting required - delivered as downloadable files.

**Confidence:** HIGH

---

### Automation/Scheduling

| Approach | Technology | Confidence |
|----------|------------|------------|
| **Development** | Manual CLI execution | HIGH |
| **Production (simple)** | macOS `launchd` or Linux `cron` | HIGH |
| **Production (robust)** | GitHub Actions scheduled workflows | HIGH |
| **Production (complex)** | Temporal or Prefect | OVERKILL |

**Recommendation:** Start with manual execution during 8-week validation phase. Graduate to GitHub Actions for scheduled runs.

```yaml
# .github/workflows/newsletter.yml
name: Weekly Newsletter
on:
  schedule:
    - cron: '0 14 * * 2'  # Tuesday 10am ET
    - cron: '0 0 * * 5'   # Thursday 8pm ET
  workflow_dispatch:  # Manual trigger

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python execution/generate_newsletter.py
        env:
          BEEHIIV_API_KEY: ${{ secrets.BEEHIIV_API_KEY }}
          # ... other secrets
```

**Confidence:** HIGH

---

### AI/LLM Layer

| Task | Model | Provider | Rationale |
|------|-------|----------|-----------|
| **Content summarization** | Claude 3.5 Sonnet | Anthropic | Best cost/quality for long-form text |
| **Voice/style writing** | Claude 3.5 Sonnet | Anthropic | Excellent at maintaining voice consistency |
| **Research/fact-finding** | Perplexity Sonar | Perplexity | Real-time web access built-in |
| **Product descriptions** | Claude 3.5 Sonnet | Anthropic | Structured output, marketing copy |
| **Code generation (tools)** | Claude 3.5 Sonnet or GPT-4o | Either | Both excellent for JS/HTML |

**Primary SDK:**
```bash
pip install anthropic>=0.25.0
```

**Secondary (for GPT creation):**
```bash
pip install openai>=1.0.0
```

**Cost Estimates (per newsletter):**
| Task | Tokens (est.) | Cost |
|------|---------------|------|
| Content research | 50K input, 5K output | ~$0.20 |
| Draft writing | 10K input, 3K output | ~$0.05 |
| Product generation | 5K input, 2K output | ~$0.02 |
| **Total per issue** | - | **~$0.30** |

**Confidence:** HIGH

---

## What NOT to Use

| Technology | Why Not |
|------------|---------|
| **LangChain** | Unnecessary abstraction layer; direct API calls are simpler for this use case |
| **Scrapy** | Overkill for targeted scraping; Playwright handles dynamic content better |
| **Selenium** | Playwright is faster, more reliable, better API |
| **Node.js/TypeScript** | Weaker AI/ML ecosystem; would require rewriting existing scripts |
| **Docker** | Unnecessary complexity for CLI-based automation |
| **Kubernetes** | Way overkill - this is a weekly batch job |
| **Celery/Redis** | No need for distributed task queue - single sequential workflow |
| **Django/Flask** | No web UI needed - pure CLI automation |
| **SQLite/Postgres** | No database needed - file-based storage sufficient |
| **snscrape** | Broken since X API changes in 2023 |
| **OpenAI Assistants API** | Deprecated, removal August 2026 |

---

## Complete requirements.txt

```txt
# Core
python-dotenv>=1.0.0
requests>=2.31.0

# Content Aggregation
pyktok>=0.1.0
playwright>=1.40.0
google-api-python-client>=2.100.0
youtube-transcript-api>=0.6.0
tweepy>=4.14.0
praw>=7.7.0

# AI/LLM
anthropic>=0.25.0
openai>=1.0.0

# Product Generation
weasyprint>=60.0
markdown>=3.5.0
gspread>=5.10.0
google-auth>=2.20.0

# Utilities
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

---

## Confidence Levels Summary

| Component | Confidence | Notes |
|-----------|------------|-------|
| Core Runtime (Python 3.12) | HIGH | Proven, established |
| YouTube API | HIGH | Official, well-documented |
| Reddit API (PRAW) | HIGH | Official, stable |
| Amazon PA-API | HIGH | Official, affiliate access |
| Beehiiv Integration | HIGH | Requires Enterprise tier |
| PDF Generation | HIGH | Mature libraries |
| Google Sheets | HIGH | Official API |
| AI/LLM Layer | HIGH | Mature SDKs |
| TikTok Shop | MEDIUM | No official API, scraper risk |
| Twitter/X | MEDIUM | Expensive, rate-limited |
| Perplexity | MEDIUM | Newer API, less battle-tested |
| Custom GPT Automation | LOW | No programmatic creation |

---

## Action Items for Roadmap

1. **Confirm Beehiiv Enterprise** - Required for Posts Create API
2. **Validate TikTok scraping** - Test `pyktok` reliability
3. **Budget X API** - Decide if $100/mo is justified vs manual curation
4. **Set up Google Cloud** - For YouTube API and Sheets access
5. **Set up Anthropic account** - Primary LLM provider
6. **Install Playwright browsers** - `playwright install chromium`

---

*Research completed: 2026-01-29*
