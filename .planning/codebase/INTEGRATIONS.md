# External Integrations

**Analysis Date:** 2026-01-29

## APIs & External Services

**Weather Data:**
- OpenWeatherMap API - Current weather lookup by city
  - SDK/Client: `requests` library (direct HTTP)
  - Auth: `WEATHER_API_KEY` environment variable
  - Endpoint: `https://api.openweathermap.org/data/2.5/weather`
  - Implementation: `execution/weather_lookup.py`
  - Rate limit: 1,000 calls/day (free tier)

**AI/LLM Services (Configured but not directly used in scripts):**
- Anthropic Claude
  - Auth: `ANTHROPIC_API_KEY`
  - Purpose: AI agent orchestration (used by Claude Code, not scripts)
- OpenAI
  - Auth: `OPENAI_API_KEY`
  - Purpose: Alternative AI provider

**Potential Integrations (Documented in `.env.example`):**
- Apify - Web scraping (`APIFY_API_TOKEN`)
- Replicate - AI image/video generation (`REPLICATE_API_TOKEN`)
- SendGrid - Email (`SENDGRID_API_KEY`)
- Stripe - Payments (`STRIPE_API_KEY`)
- Google Services - OAuth or service account credentials

## Data Storage

**Databases:**
- None - No database integration detected

**File Storage:**
- Local filesystem only
- Paths:
  - `data/` - Sample data files (e.g., `sample.csv`)
  - `.tmp/` - Temporary files and logs (gitignored)
  - `.tmp/cost_log.jsonl` - API cost tracking log
  - `.tmp/agent_backups/` - Agent file backup storage

**Caching:**
- None - No caching mechanism detected

## Authentication & Identity

**Auth Provider:**
- None - No user authentication system

**API Authentication Pattern:**
- Environment variables via `python-dotenv`
- Pattern in scripts:
  ```python
  from dotenv import load_dotenv
  load_dotenv()
  API_KEY = os.getenv("SERVICE_API_KEY")
  ```
- Validation before API calls (fail fast on missing keys)

## Monitoring & Observability

**Error Tracking:**
- None - No external error tracking service

**Logging:**
- Console output (`print()` statements)
- Cost logging to `.tmp/cost_log.jsonl`:
  ```python
  from execution.doe_utils import log_cost
  log_cost("workflow_name", {"anthropic": 0.15})
  ```

**Cost Tracking:**
- Built-in cost tracking via `execution/doe_utils.py`
- Commands:
  ```bash
  python execution/doe_utils.py costs --today
  python execution/doe_utils.py costs --month 2025-12
  python execution/doe_utils.py costs --all
  ```
- Alert threshold configurable via `DOE_COST_ALERT_THRESHOLD`

## CI/CD & Deployment

**Hosting:**
- Local development only
- No deployment pipeline

**CI Pipeline:**
- None detected
- No GitHub Actions, CircleCI, or other CI configuration

## Environment Configuration

**Required env vars:**
- None strictly required for base functionality
- `WEATHER_API_KEY` - Required for weather lookup workflow
- `ANTHROPIC_API_KEY` - Recommended for Claude Code usage

**Optional env vars:**
- `OPENAI_API_KEY` - Alternative AI provider
- `DOE_COST_TRACKING` - Enable/disable cost logging
- `DOE_COST_ALERT_THRESHOLD` - Cost alert threshold (default: $1.00)

**Secrets location:**
- `.env` file in project root (gitignored)
- `.env.example` - Template with placeholder values (committed)

## Webhooks & Callbacks

**Incoming:**
- None - No webhook endpoints

**Outgoing:**
- None - No outgoing webhook calls

## Integration Patterns

**HTTP Request Pattern:**
```python
import requests

response = requests.get(
    API_URL,
    params={"key": "value"},
    timeout=10
)

if response.status_code == 401:
    print("ERROR: Invalid API key")
    return 1

response.raise_for_status()
data = response.json()
```

**Error Handling:**
- Check for missing API key before making request
- Handle specific HTTP status codes (401, 404)
- Timeout handling with `requests.exceptions.Timeout`
- Generic exception catching as fallback

## Google Services (Optional)

**Configuration Options:**
1. OAuth credentials: `credentials.json` in project root
   - `token.json` generated on first auth
2. Service account: `GOOGLE_APPLICATION_CREDENTIALS` env var

**Status:** Not currently used, but documented in `.env.example`

---

*Integration audit: 2026-01-29*
