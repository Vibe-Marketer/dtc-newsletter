# Phase 7: Pipeline Integration - Research

**Researched:** 2026-01-31
**Domain:** Python CLI orchestration, error handling, cost tracking
**Confidence:** HIGH

## Summary

Phase 7 integrates all existing modules (content_aggregate, stretch_aggregate, newsletter_generator, affiliate_finder, product_factory) into a single CLI pipeline with error handling, cost tracking, and graceful degradation.

The existing codebase already demonstrates patterns for parallel execution (ThreadPoolExecutor in stretch_aggregate), graceful degradation (try/except with continue), and progress output (print statements with stage announcements). The key additions are:

1. **Cost tracking from Claude API** - Extract usage from response.usage (input_tokens, output_tokens, cache_read_input_tokens)
2. **Retry with exponential backoff** - tenacity library already in requirements.txt
3. **macOS notifications** - Use osascript via subprocess (no additional dependencies)
4. **Output organization** - Auto-increment issue numbers, monthly subfolders, index.json manifest

**Primary recommendation:** Build on existing patterns in content_aggregate.py and stretch_aggregate.py. Use tenacity for retries, extract usage from Claude API responses for cost tracking, and use native osascript for notifications.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tenacity | 9.1.2 | Retry with backoff | Already in requirements.txt, proven in stretch sources |
| anthropic | 0.75.0 | Claude API client | Already used by claude_client.py, provides usage stats |
| argparse | stdlib | CLI argument parsing | Already used by all existing modules |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| subprocess | stdlib | macOS notifications | osascript for desktop alerts |
| json | stdlib | Cost log, index manifest | Data persistence |
| re | stdlib | Topic slugification | Simple regex replacement |
| pathlib | stdlib | File path handling | Already used throughout codebase |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| osascript | pync, plyer | Adds dependency; osascript is native and sufficient |
| print() progress | rich, tqdm | Adds dependency; CONTEXT.md specifies simple text, not spinners |
| Manual retry | backoff, retry | tenacity already in deps, more flexible |

**Installation:**
```bash
# No new dependencies needed - all already in requirements.txt
pip install -r requirements.txt
```

## Architecture Patterns

### Recommended Project Structure
```
execution/
  newsletter_generate.py     # Main pipeline orchestrator (NEW)
  content_aggregate.py       # Stage 1: Core content
  stretch_aggregate.py       # Stage 2: Stretch sources
  newsletter_generator.py    # Stage 3: Generate newsletter
  affiliate_finder.py        # Stage 4: Find monetization
  product_factory.py         # Stage 5: Generate product (optional)
  doe_utils.py              # Cost tracking (existing, extend)

output/
  newsletters/
    2026-01/                 # Monthly subfolder
      001-tiktok-shop-strategies.md
      002-email-deliverability.md
    2026-02/
      003-q1-dtc-trends.md
    index.json               # Newsletter manifest
  products/
    2026-01-31-topic-name/   # Product package folder

data/
  cost_log.json              # Cumulative cost history (NEW)
```

### Pattern 1: Pipeline Orchestration
**What:** Sequential stage execution with graceful degradation
**When to use:** Full pipeline runs
**Example:**
```python
# Source: Existing pattern from content_aggregate.py:294-396
def run_pipeline(topic=None, quiet=False, verbose=False):
    """Run the full newsletter pipeline."""
    results = {}
    costs = {}
    
    # Stage 1: Content aggregation
    announce("Fetching content...", quiet)
    try:
        results["content"] = content_aggregate.run_aggregation()
        costs["content"] = calculate_api_cost(results["content"])
        announce("Content fetched.", quiet)
    except Exception as e:
        log_warning(f"Content aggregation failed: {e}")
        results["content"] = None
    
    # Stage 2: Stretch sources (optional)
    if results["content"]:
        announce("Fetching stretch sources...", quiet)
        try:
            stretch = stretch_aggregate.run_all_stretch_sources()
            if stretch["success"]:
                results["stretch"] = stretch
        except Exception as e:
            log_warning(f"Stretch sources failed: {e}")
    
    # Continue even if sources fail...
    # Stage 3, 4, 5 follow same pattern
```

### Pattern 2: Retry with Exponential Backoff
**What:** Automatic retry for transient failures
**When to use:** Claude API calls
**Example:**
```python
# Source: tenacity docs - https://tenacity.readthedocs.io
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True
)
def call_claude_with_retry(client, prompt, max_tokens=1024):
    """Call Claude API with 3 retries and exponential backoff."""
    return client.generate_with_voice(prompt, max_tokens=max_tokens)
```

### Pattern 3: Cost Tracking from Claude API
**What:** Extract and accumulate API costs
**When to use:** After every Claude API call
**Example:**
```python
# Source: Anthropic API docs - response.usage object
# Pricing: Claude Sonnet 4.5 = $3/MTok input, $15/MTok output

CLAUDE_SONNET_PRICING = {
    "input": 3.0 / 1_000_000,      # $3 per million tokens
    "output": 15.0 / 1_000_000,    # $15 per million tokens
    "cache_read": 0.30 / 1_000_000, # $0.30 per million (10% of input)
    "cache_write": 3.75 / 1_000_000, # $3.75 per million (1.25x input)
}

def calculate_cost(response):
    """Calculate cost from Claude API response."""
    usage = response.usage
    cost = 0.0
    cost += usage.input_tokens * CLAUDE_SONNET_PRICING["input"]
    cost += usage.output_tokens * CLAUDE_SONNET_PRICING["output"]
    if hasattr(usage, "cache_read_input_tokens"):
        cost += (usage.cache_read_input_tokens or 0) * CLAUDE_SONNET_PRICING["cache_read"]
    if hasattr(usage, "cache_creation_input_tokens"):
        cost += (usage.cache_creation_input_tokens or 0) * CLAUDE_SONNET_PRICING["cache_write"]
    return cost
```

### Pattern 4: macOS Desktop Notifications
**What:** Alert user when pipeline completes
**When to use:** End of pipeline (success or failure)
**Example:**
```python
# Source: macOS native osascript
import subprocess

def notify(title: str, message: str):
    """Send macOS desktop notification."""
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script], capture_output=True)
```

### Pattern 5: Issue Number Auto-Increment
**What:** Scan output folder for highest existing issue number
**When to use:** Before saving new newsletter
**Example:**
```python
# Source: CONTEXT.md specification
import re
from pathlib import Path

def get_next_issue_number(newsletters_dir: Path) -> int:
    """Get next issue number by scanning existing newsletters."""
    max_issue = 0
    for md_file in newsletters_dir.rglob("*.md"):
        match = re.match(r"(\d{3})-", md_file.name)
        if match:
            max_issue = max(max_issue, int(match.group(1)))
    return max_issue + 1
```

### Anti-Patterns to Avoid
- **Don't use progress bars or spinners:** CONTEXT.md specifies simple text announcements
- **Don't block on cost warnings:** Warn but continue (non-blocking automation)
- **Don't fail the whole pipeline if one source fails:** Graceful degradation is required
- **Don't store costs in .tmp/:** Use data/cost_log.json for persistence

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Retry logic | Custom while loops | tenacity decorator | Handles edge cases (jitter, max delay, logging) |
| Exponential backoff | time.sleep(2**n) | wait_exponential() | Built-in min/max limits, jitter option |
| Desktop notifications | Custom AppleScript wrapper | Single subprocess.run() call | One-liner, no abstraction needed |
| Slug generation | Complex unicode handling | Simple regex `re.sub(r'[^a-z0-9]+', '-', text.lower())` | DTC topics are English, no i18n needed |

**Key insight:** The existing codebase already has patterns for everything complex. Pipeline integration is primarily composition, not invention.

## Common Pitfalls

### Pitfall 1: Forgetting to Pass Usage Back from Claude Client
**What goes wrong:** ClaudeClient.generate_with_voice() returns only text, not the response object with usage
**Why it happens:** Cost tracking needs access to response.usage
**How to avoid:** Either modify ClaudeClient to return (text, usage) tuple, or add a method that returns the raw response
**Warning signs:** Costs always show $0.00

### Pitfall 2: Race Condition in Issue Number Assignment
**What goes wrong:** If pipeline runs twice simultaneously, both get same issue number
**Why it happens:** Read-then-write without locking
**How to avoid:** Either use file locking, or accept this as edge case (weekly runs won't overlap)
**Warning signs:** Duplicate issue numbers in index.json

### Pitfall 3: Cost Log File Growing Unboundedly
**What goes wrong:** JSONL file becomes huge over time
**Why it happens:** Appending without rotation
**How to avoid:** Consider monthly log rotation or JSON object with date keys (not JSONL)
**Warning signs:** Slow cost report generation

### Pitfall 4: Notification Fails Silently
**What goes wrong:** osascript fails but pipeline reports success
**Why it happens:** subprocess.run() captures output but doesn't check return code
**How to avoid:** Wrap in try/except, log failure but don't fail pipeline
**Warning signs:** No notification when expected

### Pitfall 5: Topic Detection Returns None
**What goes wrong:** Auto-detected topic is None, filename becomes "001-none.md"
**Why it happens:** Content aggregation returned empty or topic extraction failed
**How to avoid:** Default to date-based slug if topic is None
**Warning signs:** Newsletters named with "none" or empty topic

## Code Examples

Verified patterns from official sources:

### CLI with Verbosity Flags
```python
# Source: Existing pattern from content_aggregate.py:78-186
parser = argparse.ArgumentParser(description="Generate DTC newsletter")
parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")
parser.add_argument("-v", "--verbose", action="store_true", help="Show debug output")
parser.add_argument("--topic", type=str, default=None, help="Override auto-detected topic")

def announce(msg: str, quiet: bool = False):
    """Print stage announcement unless quiet mode."""
    if not quiet:
        print(msg)
```

### Persistent Cost Log
```python
# Source: doe_utils.py pattern adapted for JSON
import json
from pathlib import Path
from datetime import datetime

COST_LOG_PATH = Path("data/cost_log.json")

def log_cost(workflow: str, costs: dict, run_id: str = None):
    """Log costs to persistent JSON file."""
    COST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing or create new
    if COST_LOG_PATH.exists():
        with open(COST_LOG_PATH) as f:
            log = json.load(f)
    else:
        log = {"runs": [], "cumulative": {}}
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "workflow": workflow,
        "run_id": run_id or datetime.now().strftime("%Y%m%d-%H%M%S"),
        "costs": costs,
        "total": sum(costs.values())
    }
    log["runs"].append(entry)
    
    # Update cumulative
    for service, cost in costs.items():
        log["cumulative"][service] = log["cumulative"].get(service, 0) + cost
    
    with open(COST_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)
```

### Index.json Manifest
```python
# Source: CONTEXT.md specification
def update_newsletter_index(newsletters_dir: Path, new_entry: dict):
    """Update newsletter index with new entry."""
    index_path = newsletters_dir / "index.json"
    
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = {"newsletters": []}
    
    index["newsletters"].append({
        "issue": new_entry["issue_number"],
        "topic": new_entry["topic"],
        "date": new_entry["date"],
        "path": new_entry["path"],
        "subject_line": new_entry.get("subject_line"),
        "cost": new_entry.get("cost"),
    })
    
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual retry loops | tenacity decorators | 2020+ | Cleaner code, better backoff |
| Print statements | Still valid for CLI | N/A | CONTEXT.md explicitly chose simple text over rich |
| Third-party notification libs | Native osascript | N/A | Zero dependencies for macOS |

**Deprecated/outdated:**
- pync, py-notifier: Additional dependencies not needed for macOS-only use case
- rich progress bars: Explicitly avoided per CONTEXT.md decisions

## Open Questions

Things that couldn't be fully resolved:

1. **Exact cost estimation timing**
   - What we know: Can calculate cost after each API call
   - What's unclear: Should we display real-time cumulative, or just final total?
   - Recommendation: Display after each stage (e.g., "Content: $0.12, Newsletter: $0.35, Total: $0.47")

2. **Product factory integration**
   - What we know: Phase 6 (product_factory.py) is in progress
   - What's unclear: Exact interface for pipeline integration
   - Recommendation: Design pipeline to call optional product step; validate interface when Phase 6 completes

3. **Topic auto-detection source**
   - What we know: Should auto-detect trending topics
   - What's unclear: Which module provides this? content_selector? perplexity_client?
   - Recommendation: Use highest-scoring content item's topic from content_aggregate results

## Sources

### Primary (HIGH confidence)
- anthropic SDK 0.75.0 - response.usage object confirmed in Anthropic API docs
- tenacity 9.1.2 - ReadTheDocs documentation verified
- Existing codebase - content_aggregate.py, stretch_aggregate.py, doe_utils.py patterns

### Secondary (MEDIUM confidence)
- Anthropic pricing page - $3/MTok input, $15/MTok output for Claude Sonnet 4.5
- macOS osascript - Standard subprocess approach for notifications

### Tertiary (LOW confidence)
- None - all patterns verified against existing code or official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use or in requirements.txt
- Architecture: HIGH - Patterns directly from existing codebase
- Pitfalls: MEDIUM - Based on common patterns, not project-specific incidents

**Research date:** 2026-01-31
**Valid until:** 2026-02-28 (30 days - stable Python patterns)
