# Phase 9: Automation - Research

**Researched:** 2026-02-02
**Domain:** GitHub Actions scheduled workflows
**Confidence:** HIGH

## Summary

This phase implements scheduled automation of the newsletter pipeline using GitHub Actions. The domain is well-documented with stable APIs. GitHub Actions provides native support for cron-based scheduling, secrets management, and workflow dispatch (manual triggers).

The primary challenge is timezone handling - GitHub Actions cron schedules only support UTC. For consistent Eastern Time execution (Tuesday 10am ET, Thursday 8pm ET), the workflow must either accept ~1 hour variance during DST transitions or implement dynamic scheduling logic.

The existing pipeline (`python execution/pipeline_runner.py`) is designed for CLI execution with exit codes, making it ideal for GitHub Actions integration. All API keys follow standard environment variable patterns compatible with GitHub Secrets.

**Primary recommendation:** Use `ubuntu-latest` runner with `actions/setup-python@v5`, cache pip dependencies, configure 8 repository secrets, use UTC-based cron approximating ET times, implement `workflow_dispatch` for manual runs.

## Standard Stack

The established tools for GitHub Actions Python automation:

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| GitHub Actions | N/A | CI/CD platform | Native to GitHub, free for public repos |
| `ubuntu-latest` | 24.04+ | Runner OS | Best Python support, cheapest |
| `actions/checkout@v5` | v5 | Clone repo | Official GitHub action |
| `actions/setup-python@v5` | v5 | Python setup | Official, supports caching |
| POSIX cron | N/A | Scheduling | Built into GitHub Actions |

### Supporting
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `actions/upload-artifact@v4` | v4 | Save outputs | Preserve newsletter files |
| `pip` caching | Built-in | Speed up runs | Every run (via setup-python) |
| GitHub Secrets | N/A | Store API keys | All sensitive credentials |
| `workflow_dispatch` | N/A | Manual trigger | On-demand runs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `ubuntu-latest` | `macos-latest` | 10x more expensive, no benefit |
| GitHub Secrets | Environment variables | Secrets are encrypted at rest |
| Cron schedule | External scheduler | More complexity, less integrated |

**No additional installation required** - all tools are built into GitHub Actions.

## Architecture Patterns

### Recommended Workflow Structure
```yaml
name: Newsletter Pipeline
on:
  schedule:
    - cron: '0 15 * * 2'  # Tuesday ~10am ET (EST)
    - cron: '0 1 * * 5'   # Thursday ~8pm ET (EST -> Friday UTC)
  workflow_dispatch:       # Manual trigger

jobs:
  generate-newsletter:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup-python with caching
      - install dependencies
      - run pipeline
      - commit output (optional)
      - notify on completion
```

### Pattern 1: Secrets as Environment Variables
**What:** Map GitHub Secrets to env vars for pipeline consumption
**When to use:** Always - existing pipeline reads from environment
**Example:**
```yaml
# Source: https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  TUBELAB_API_KEY: ${{ secrets.TUBELAB_API_KEY }}
  YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
  PERPLEXITY_API_KEY: ${{ secrets.PERPLEXITY_API_KEY }}
  APIFY_TOKEN: ${{ secrets.APIFY_TOKEN }}
  REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
  REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
  REDDIT_USER_AGENT: ${{ secrets.REDDIT_USER_AGENT }}
```

### Pattern 2: Dependency Caching
**What:** Cache pip packages to speed up workflow runs
**When to use:** Always - significantly reduces run time
**Example:**
```yaml
# Source: https://docs.github.com/en/actions/tutorials/build-and-test-code/python
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'
- run: pip install -r requirements.txt
```

### Pattern 3: Commit Output to Repo
**What:** Auto-commit generated newsletters back to repository
**When to use:** When newsletters should be version-controlled
**Example:**
```yaml
- name: Commit newsletter
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add output/newsletters/
    git diff --staged --quiet || git commit -m "feat: generate newsletter $(date +%Y-%m-%d)"
    git push
```

### Pattern 4: Manual Trigger with Inputs
**What:** Allow on-demand runs with optional parameters
**When to use:** Testing, emergency newsletter generation
**Example:**
```yaml
# Source: https://docs.github.com/en/actions/reference/events-that-trigger-workflows#workflow_dispatch
on:
  workflow_dispatch:
    inputs:
      topic:
        description: 'Override topic (optional)'
        required: false
        type: string
      skip_affiliates:
        description: 'Skip affiliate discovery'
        required: false
        type: boolean
        default: false
```

### Anti-Patterns to Avoid
- **Hardcoding secrets in workflow file:** Use GitHub Secrets exclusively
- **Using `continue-on-error: true` on critical steps:** Hides real failures
- **Ignoring exit codes:** Pipeline returns non-zero on failure - don't mask this
- **Running on every push:** Wastes resources; use schedule + manual only
- **Not setting timeout:** Default 6 hours is too long; set `timeout-minutes: 30`

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Python setup | Manual python install | `actions/setup-python@v5` | Handles versions, caching, PATH |
| Dependency caching | Manual cache logic | `setup-python` cache option | Built-in, correct invalidation |
| Secrets management | `.env` file in repo | GitHub Secrets | Encrypted, audit logged |
| Notifications | Custom email code | GitHub Actions notifications | Built-in status emails |
| Manual trigger UI | Custom webhook | `workflow_dispatch` | Native GitHub UI |
| Artifact storage | Custom upload | `actions/upload-artifact@v4` | 90-day retention, downloadable |

**Key insight:** GitHub Actions provides primitives for everything needed. Custom solutions add maintenance burden with no benefit.

## Common Pitfalls

### Pitfall 1: UTC Cron vs Local Time
**What goes wrong:** Schedule runs at wrong time due to UTC-only cron
**Why it happens:** GitHub Actions cron doesn't support timezones
**How to avoid:** 
- Calculate UTC offset manually (ET = UTC-5 or UTC-4)
- Document the intended local time in workflow comments
- Accept ~1 hour variance during DST transitions
**Warning signs:** Newsletter generated at unexpected times

### Pitfall 2: Secrets Not Available
**What goes wrong:** Pipeline fails with "missing API key" errors
**Why it happens:** Secrets not configured in repo, or typos in names
**How to avoid:**
- Use EXACT same names as `.env` file
- Test with `workflow_dispatch` before relying on schedule
- Add step to verify secrets exist (check if non-empty)
**Warning signs:** Works locally but fails in Actions

### Pitfall 3: Scheduled Workflow Never Runs
**What goes wrong:** Cron schedule doesn't trigger workflow
**Why it happens:** Workflow file not on default branch, or repo inactive >60 days
**How to avoid:**
- Ensure workflow is merged to `main`
- Workflows auto-disable after 60 days of inactivity
- Check Actions settings: scheduled workflows can be disabled
**Warning signs:** No workflow runs in Actions tab

### Pitfall 4: Exit Code Masking
**What goes wrong:** Workflow shows success but pipeline actually failed
**Why it happens:** Using `|| true` or `continue-on-error` inappropriately
**How to avoid:**
- Let pipeline exit code propagate naturally
- Only use `continue-on-error` for truly optional steps
- Check `pipeline_runner.py` returns correct exit codes (it does: 0 success, 1 failure)
**Warning signs:** "Successful" runs with empty output

### Pitfall 5: Rate Limits on Scheduled Runs
**What goes wrong:** APIs fail due to rate limiting
**Why it happens:** Multiple scheduled runs queued, or other workflows using same keys
**How to avoid:**
- Use `concurrency` to prevent parallel runs
- Space schedules reasonably (current: 2x/week is fine)
- Monitor API usage in cost tracking
**Warning signs:** Intermittent API errors on scheduled runs

### Pitfall 6: Git Push Permission Denied
**What goes wrong:** Auto-commit step fails with permission error
**Why it happens:** Default `GITHUB_TOKEN` lacks push permission
**How to avoid:**
- Add `permissions: contents: write` to workflow
- Or use `persist-credentials: true` in checkout action
**Warning signs:** "Permission denied" or "403" on git push

## Code Examples

Verified patterns from official sources:

### Complete Workflow Template
```yaml
# Source: GitHub Actions official documentation
name: DTC Newsletter Pipeline

on:
  schedule:
    # Tuesday 10am ET (EST: UTC-5)
    - cron: '0 15 * * 2'
    # Thursday 8pm ET (EST: UTC-5, runs Friday 1am UTC)
    - cron: '0 1 * * 5'
  workflow_dispatch:
    inputs:
      topic:
        description: 'Override topic'
        required: false
        type: string

permissions:
  contents: write

concurrency:
  group: newsletter-pipeline
  cancel-in-progress: false

jobs:
  generate:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      TUBELAB_API_KEY: ${{ secrets.TUBELAB_API_KEY }}
      YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
      PERPLEXITY_API_KEY: ${{ secrets.PERPLEXITY_API_KEY }}
      APIFY_TOKEN: ${{ secrets.APIFY_TOKEN }}
      REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
      REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
      REDDIT_USER_AGENT: ${{ secrets.REDDIT_USER_AGENT }}
    
    steps:
      - uses: actions/checkout@v5
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run newsletter pipeline
        run: |
          if [ -n "${{ github.event.inputs.topic }}" ]; then
            python execution/pipeline_runner.py --topic "${{ github.event.inputs.topic }}"
          else
            python execution/pipeline_runner.py
          fi
      
      - name: Commit newsletter output
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add output/
          git diff --staged --quiet || git commit -m "feat: newsletter $(date +%Y-%m-%d)"
          git push
```

### Verifying Secrets Exist
```yaml
# Verify critical secrets are configured
- name: Verify required secrets
  run: |
    missing=""
    [ -z "$ANTHROPIC_API_KEY" ] && missing="$missing ANTHROPIC_API_KEY"
    [ -z "$REDDIT_CLIENT_ID" ] && missing="$missing REDDIT_CLIENT_ID"
    if [ -n "$missing" ]; then
      echo "::error::Missing required secrets:$missing"
      exit 1
    fi
```

### Notification on Failure
```yaml
# Built-in: GitHub sends email on failure by default
# For custom notification:
- name: Notify on failure
  if: failure()
  run: |
    echo "::error::Newsletter pipeline failed. Check logs."
    # Could add Slack/Discord webhook here
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `actions/checkout@v3` | `actions/checkout@v5` | 2024 | Better Node.js support |
| `actions/setup-python@v4` | `actions/setup-python@v5` | 2024 | Improved caching |
| `actions/upload-artifact@v3` | `actions/upload-artifact@v4` | 2023 | Better compression, dedup |
| Manual pip cache | `setup-python` cache option | 2023 | Simpler, more reliable |

**Deprecated/outdated:**
- `set-output` command: Use `$GITHUB_OUTPUT` environment file instead
- `save-state` command: Use `$GITHUB_STATE` environment file instead
- `actions/checkout@v2`: Missing security fixes, use v5

## Cron Schedule Reference

GitHub Actions uses POSIX cron with 5 fields (no seconds):
```
min hour day month weekday
 *   *    *    *      *
```

**Target schedule in Eastern Time:**
- Tuesday 10:00 AM ET
- Thursday 8:00 PM ET

**UTC equivalents (approximate - varies with DST):**

| ET Time | EST (Nov-Mar) UTC | EDT (Mar-Nov) UTC |
|---------|-------------------|-------------------|
| Tue 10am | `0 15 * * 2` | `0 14 * * 2` |
| Thu 8pm | `0 1 * * 5` | `0 0 * * 5` |

**Recommendation:** Use EST times (UTC-5) for year-round schedule. During EDT, runs will be 1 hour early (9am instead of 10am, 7pm instead of 8pm). This is preferable to missing the target time.

## Secrets Configuration

Required secrets (8 total):

| Secret Name | Description | How to Obtain |
|-------------|-------------|---------------|
| `ANTHROPIC_API_KEY` | Claude API key | console.anthropic.com |
| `TUBELAB_API_KEY` | TubeLab YouTube data | tubelab.net/developers |
| `YOUTUBE_API_KEY` | YouTube Data API v3 | console.cloud.google.com |
| `PERPLEXITY_API_KEY` | Perplexity search | perplexity.ai/settings/api |
| `APIFY_TOKEN` | Apify scraping | console.apify.com |
| `REDDIT_CLIENT_ID` | Reddit OAuth | reddit.com/prefs/apps |
| `REDDIT_CLIENT_SECRET` | Reddit OAuth | reddit.com/prefs/apps |
| `REDDIT_USER_AGENT` | Reddit identification | Format: `app-name/1.0 by /u/username` |

**To add secrets:**
1. Go to repo Settings -> Secrets and variables -> Actions
2. Click "New repository secret"
3. Add name and value
4. Repeat for all 8 secrets

## Open Questions

Things that couldn't be fully resolved:

1. **DST-aware scheduling**
   - What we know: GitHub Actions cron is UTC-only
   - What's unclear: Best approach for exact ET timing
   - Recommendation: Accept 1-hour variance OR implement conditional logic in workflow to check day/time and skip if wrong

2. **Notification preferences**
   - What we know: GitHub sends failure emails by default
   - What's unclear: Whether user wants Slack/Discord notifications
   - Recommendation: Start with email only; add custom notifications if requested

3. **Output persistence strategy**
   - What we know: Can commit to repo, upload as artifact, or both
   - What's unclear: User preference for newsletter storage
   - Recommendation: Commit to repo for persistence; artifact for debugging

## Sources

### Primary (HIGH confidence)
- https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions - Complete workflow syntax reference
- https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows - Schedule and workflow_dispatch triggers
- https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions - Secrets management
- https://docs.github.com/en/actions/tutorials/build-and-test-code/python - Python workflow patterns

### Secondary (MEDIUM confidence)
- Existing `pipeline_runner.py` - Verified CLI interface and exit codes
- Existing `requirements.txt` - Verified dependencies

### Tertiary (LOW confidence)
- None - all findings verified with official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official GitHub documentation
- Architecture: HIGH - Verified patterns from official sources
- Pitfalls: HIGH - Documented GitHub limitations
- Cron scheduling: HIGH - POSIX standard, documented UTC-only behavior

**Research date:** 2026-02-02
**Valid until:** 2026-05-02 (90 days - stable domain, rarely changes)
