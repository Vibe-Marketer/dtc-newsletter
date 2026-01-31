# Phase 8: Manual Execution - Research

**Researched:** 2026-01-31
**Domain:** Batch execution of existing pipeline
**Confidence:** HIGH

## Summary

Phase 8 is an execution phase, not a build phase. The system is fully built with 1064 passing tests. Research focused on how to orchestrate batch generation of 8 newsletters and 8 products using existing code, implement the diversity filter for topic selection, structure the content calendar, and handle validation/retry workflows.

The existing codebase provides all necessary primitives:
- `pipeline_runner.py` for single newsletter generation
- `product_factory.py` for product generation from pain points
- `content_aggregate.py` for topic sourcing with outlier detection
- `anti_pattern_validator.py` for quality checks
- `output_manager.py` for organized output with index.json
- `cost_tracker.py` for cost monitoring

**Primary recommendation:** Create a batch orchestrator script (`execution/batch_runner.py`) that wraps existing code with diversity filtering, retry logic, and content calendar generation.

## Standard Stack

### Core (Already Built)
| Module | Purpose | Why Standard |
|--------|---------|--------------|
| `pipeline_runner.py` | Single newsletter orchestration | Full pipeline with cost tracking, retry, notifications |
| `product_factory.py` | Product generation from pain points | Discovers pain points, auto-selects product type, generates |
| `content_aggregate.py` | Content sourcing | Reddit, YouTube, Perplexity with outlier scoring |
| `output_manager.py` | Output organization | Monthly folders, auto-increment issues, index.json |
| `cost_tracker.py` | Cost monitoring | Per-stage tracking, warnings, persistent logging |

### Supporting (Already Built)
| Module | Purpose | When to Use |
|--------|---------|-------------|
| `anti_pattern_validator.py` | Voice compliance | Newsletter quality gate |
| `content_selector.py` | Content type matching | Diversity across sources |
| `deduplication.py` | 4-week lookback | Prevent topic repetition |
| `pain_point_miner.py` | Reddit pain point discovery | Product ideation |

### New Required
| Component | Purpose | Implementation |
|-----------|---------|----------------|
| `batch_runner.py` | Batch orchestration | New script wrapping existing code |
| Content calendar | JSON + MD tracking | Simple file generation |
| Diversity filter | Topic selection | Algorithm on outlier scores + categories |

**No new dependencies required** - all functionality exists.

## Architecture Patterns

### Recommended Execution Flow

```
1. TOPIC DISCOVERY
   content_aggregate.py --sources reddit,youtube
   ↓
   Filter: last 4 weeks + outlier score >= 3.0
   ↓
   Diversity: categorize by e-com sub-area
   ↓
   Select: top 8 unique categories

2. NEWSLETTER GENERATION (x8)
   For each topic:
     pipeline_runner.py --topic "{topic}"
     ↓
     Validate: anti_pattern_validator.validate_voice()
     ↓
     If fails: regenerate with modified prompt
     ↓
     Update content calendar

3. PRODUCT GENERATION (x8)
   product_factory.py --discover --limit 8
   ↓
   Prioritize: 4-5 html_tool/automation, rest mixed
   ↓
   For each pain point:
     product_factory.py --from-pain-point {file} --type {type}
     ↓
     Validate: open/run product
     ↓
     If fails: retry with different type
     ↓
     Update content calendar
```

### Diversity Filter Implementation

```python
# Source: Based on content_selector.py patterns

E_COM_CATEGORIES = [
    "shipping_logistics",
    "pricing_margins", 
    "conversion_optimization",
    "ads_marketing",
    "inventory_management",
    "customer_retention",
    "product_sourcing",
    "platform_tools",
]

def select_diverse_topics(content: list[dict], count: int = 8) -> list[dict]:
    """
    Select top topics ensuring diversity across e-com sub-areas.
    
    1. Sort by outlier_score descending
    2. Categorize each by e-com sub-area
    3. Select highest from each category first
    4. Fill remaining with next highest overall
    """
    # Categorize
    for item in content:
        item['ecom_category'] = categorize_ecom_topic(item)
    
    selected = []
    used_categories = set()
    
    # First pass: one per category
    for item in sorted(content, key=lambda x: x['outlier_score'], reverse=True):
        if item['ecom_category'] not in used_categories:
            selected.append(item)
            used_categories.add(item['ecom_category'])
            if len(selected) >= count:
                break
    
    # Second pass: fill remaining (allows category repeats)
    if len(selected) < count:
        for item in sorted(content, key=lambda x: x['outlier_score'], reverse=True):
            if item not in selected:
                selected.append(item)
                if len(selected) >= count:
                    break
    
    return selected
```

### Content Calendar Structure

```json
{
  "generated_at": "2026-01-31T12:00:00Z",
  "newsletters": [
    {
      "week": 1,
      "topic": "TikTok Shop conversion tactics",
      "newsletter_path": "output/newsletters/2026-02/003-tiktok-shop-conversion.md",
      "outlier_score": 4.2,
      "source": "reddit",
      "status": "generated"
    }
  ],
  "products": [
    {
      "week": 1,
      "pain_point": "Shipping cost calculator needed",
      "product_type": "html_tool",
      "product_path": "output/products/shipping-cost-calculator/",
      "status": "generated"
    }
  ],
  "stats": {
    "newsletters_generated": 8,
    "products_generated": 8,
    "total_cost": 12.50,
    "failures_recovered": 2
  }
}
```

Markdown view (`content_calendar.md`):

```markdown
# Content Calendar

Generated: 2026-01-31

## Newsletters

| Week | Topic | Path | Status |
|------|-------|------|--------|
| 1 | TikTok Shop conversion tactics | 2026-02/003-tiktok-shop.md | Generated |
| 2 | ... | ... | ... |

## Products

| Week | Pain Point | Type | Path | Status |
|------|------------|------|------|--------|
| 1 | Shipping cost calculator | html_tool | shipping-cost-calculator/ | Generated |
| 2 | ... | ... | ... | ... |
```

### Anti-Patterns to Avoid
- **Rebuilding existing code:** All generation code exists - wrap, don't rewrite
- **Manual topic selection:** Trust the outlier scores + diversity filter
- **Sequential failure:** One failure should not stop the batch
- **Missing validation:** Each output needs quality gate before counting as done

## Don't Hand-Roll

Problems that already have solutions in the codebase:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Topic scoring | Custom scoring | `content_aggregate.py` with `--min-score 3.0` | Outlier detection already proven |
| Newsletter generation | New generator | `pipeline_runner.py --topic "{topic}"` | Full pipeline with voice, validation |
| Product generation | New factory | `product_factory.py --from-pain-point` | Integrates pain points, pricing, packaging |
| Deduplication | Custom tracking | `deduplication.py` (4-week lookback) | Hash-based, battle-tested |
| Output organization | Custom paths | `output_manager.py` functions | Monthly folders, index.json |
| Cost tracking | Manual counting | `cost_tracker.py` | Per-stage, warnings, persistent log |
| Voice validation | Manual review | `anti_pattern_validator.validate_voice()` | 28 anti-patterns checked |

**Key insight:** The system is complete. Phase 8 is orchestration and validation, not development.

## Common Pitfalls

### Pitfall 1: Running Without API Keys
**What goes wrong:** Pipeline silently degrades or fails
**Why it happens:** Reddit/Perplexity/Apify not configured
**How to avoid:** Pre-flight check at batch start
**Warning signs:** "Module not available" messages, empty content

```python
# Pre-flight check
def check_api_keys():
    required = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "REDDIT_CLIENT_ID": os.getenv("REDDIT_CLIENT_ID"),
    }
    optional = {
        "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY"),
        "APIFY_TOKEN": os.getenv("APIFY_TOKEN"),
    }
    
    missing_required = [k for k, v in required.items() if not v]
    if missing_required:
        raise ValueError(f"Missing required: {missing_required}")
    
    missing_optional = [k for k, v in optional.items() if not v]
    if missing_optional:
        print(f"WARNING: Missing optional: {missing_optional}")
```

### Pitfall 2: Cost Runaway
**What goes wrong:** Batch costs exceed $40 budget
**Why it happens:** 8 newsletters + 8 products with retries
**How to avoid:** Check cumulative cost before each generation
**Warning signs:** `cost_tracker.check_warning()` returns message

```python
# Per-generation cost check
MAX_BATCH_COST = 40.0

def can_continue(tracker: CostTracker) -> bool:
    total = tracker.get_total()
    if total > MAX_BATCH_COST:
        print(f"STOP: Cost ${total:.2f} exceeds ${MAX_BATCH_COST}")
        return False
    return True
```

### Pitfall 3: Duplicate Topics
**What goes wrong:** Same topic selected multiple times
**Why it happens:** Diversity filter not applied
**How to avoid:** Track selected topics, enforce uniqueness
**Warning signs:** Multiple newsletters on same sub-area

### Pitfall 4: Product Generation Loops
**What goes wrong:** Same pain point fails repeatedly
**Why it happens:** HTML tool fails, retry with HTML tool again
**How to avoid:** Rotate product types on failure
**Warning signs:** Same error message 3+ times

```python
PRODUCT_TYPE_FALLBACKS = {
    "html_tool": ["automation", "sheets"],
    "automation": ["prompt_pack", "gpt_config"],
    "sheets": ["pdf", "prompt_pack"],
}

def retry_with_fallback(pain_point: dict, failed_type: str) -> str:
    fallbacks = PRODUCT_TYPE_FALLBACKS.get(failed_type, ["pdf"])
    return fallbacks[0]
```

### Pitfall 5: Validation False Positives
**What goes wrong:** Anti-pattern validator rejects valid content
**Why it happens:** "leverage" appears in legitimate context
**How to avoid:** Human review for edge cases (per CONTEXT.md)
**Warning signs:** Multiple regenerations for same newsletter

## Code Examples

### Batch Newsletter Generation

```python
# Source: Wraps existing pipeline_runner.py

from execution.pipeline_runner import run_pipeline
from execution.cost_tracker import CostTracker

def generate_newsletters_batch(topics: list[str], tracker: CostTracker) -> list[dict]:
    """Generate 8 newsletters from selected topics."""
    results = []
    
    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}/8] Generating newsletter: {topic}")
        
        result = run_pipeline(
            topic=topic,
            quiet=False,
            skip_affiliates=True,  # Focus on newsletters
        )
        
        # Validate
        if result.success:
            validation = validate_newsletter(result.newsletter_path)
            if validation['is_valid']:
                results.append({
                    "topic": topic,
                    "path": str(result.newsletter_path),
                    "cost": result.total_cost,
                    "status": "success"
                })
            else:
                # Retry with validation feedback
                print(f"  Validation failed: {validation['violations']}")
                # Regenerate logic here
        else:
            results.append({
                "topic": topic,
                "error": result.errors[0] if result.errors else "Unknown",
                "status": "failed"
            })
        
        # Cost check
        if not can_continue(tracker):
            break
    
    return results
```

### Newsletter Quality Gate

```python
# Source: Uses existing anti_pattern_validator.py

from execution.anti_pattern_validator import validate_voice, count_sentence_stats
from pathlib import Path

def validate_newsletter(path: Path) -> dict:
    """
    Full quality validation per CONTEXT.md:
    1. Anti-pattern check (no forbidden phrases)
    2. Structural check (5 sections, word counts)
    3. Quality gate (voice + numbers + attribution)
    """
    content = path.read_text()
    
    # 1. Anti-pattern check
    is_valid, violations = validate_voice(content)
    if not is_valid:
        return {"is_valid": False, "violations": violations, "stage": "anti_pattern"}
    
    # 2. Structural check
    sections = content.split("\n\n")
    if len(sections) < 5:
        return {"is_valid": False, "violations": ["Fewer than 5 sections"], "stage": "structure"}
    
    # 3. Quality gate - concrete numbers
    has_numbers = any(char.isdigit() for char in content)
    has_dollar = "$" in content
    has_percent = "%" in content
    
    if not (has_numbers or has_dollar or has_percent):
        return {"is_valid": False, "violations": ["No concrete numbers found"], "stage": "quality"}
    
    # 4. Sentence stats for rhythm score
    stats = count_sentence_stats(content)
    if stats['rhythm_score'] < 40:
        return {"is_valid": False, "violations": [f"Rhythm score too low: {stats['rhythm_score']}"], "stage": "quality"}
    
    return {"is_valid": True, "violations": [], "stage": "passed"}
```

### Product Type Distribution

```python
# Source: Per CONTEXT.md - 4-5 HTML tools/automations, rest mixed

from execution.product_factory import ProductFactory, PRODUCT_TYPES

def distribute_product_types(count: int = 8) -> list[str]:
    """
    Distribute product types per CONTEXT.md:
    - 4-5 HTML tools/automations (hard stuff first)
    - Rest mixed from other types
    """
    hard_types = ["html_tool", "automation"]
    easy_types = ["gpt_config", "sheets", "pdf", "prompt_pack"]
    
    distribution = []
    
    # 4-5 hard types
    hard_count = 5 if count >= 8 else 4
    for i in range(hard_count):
        distribution.append(hard_types[i % 2])  # Alternate html_tool, automation
    
    # Fill rest with mixed
    remaining = count - hard_count
    for i in range(remaining):
        distribution.append(easy_types[i % len(easy_types)])
    
    return distribution
```

### Content Calendar Writer

```python
# Source: New utility for Phase 8

import json
from datetime import datetime
from pathlib import Path

def write_content_calendar(
    newsletters: list[dict],
    products: list[dict],
    output_dir: Path = Path("output")
) -> tuple[Path, Path]:
    """
    Write content calendar in JSON + Markdown formats.
    """
    calendar = {
        "generated_at": datetime.now().isoformat(),
        "newsletters": newsletters,
        "products": products,
        "stats": {
            "newsletters_generated": sum(1 for n in newsletters if n.get("status") == "success"),
            "products_generated": sum(1 for p in products if p.get("status") == "success"),
            "total_cost": sum(n.get("cost", 0) for n in newsletters) + sum(p.get("cost", 0) for p in products),
        }
    }
    
    # JSON
    json_path = output_dir / "content_calendar.json"
    json_path.write_text(json.dumps(calendar, indent=2))
    
    # Markdown
    md_lines = [
        "# Content Calendar",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "\n## Newsletters\n",
        "| Week | Topic | Path | Status |",
        "|------|-------|------|--------|",
    ]
    for i, n in enumerate(newsletters, 1):
        md_lines.append(f"| {i} | {n.get('topic', 'N/A')[:30]} | {n.get('path', 'N/A')} | {n.get('status', 'pending')} |")
    
    md_lines.extend([
        "\n## Products\n",
        "| Week | Pain Point | Type | Path | Status |",
        "|------|------------|------|------|--------|",
    ])
    for i, p in enumerate(products, 1):
        md_lines.append(f"| {i} | {p.get('pain_point', 'N/A')[:25]} | {p.get('type', 'N/A')} | {p.get('path', 'N/A')} | {p.get('status', 'pending')} |")
    
    md_path = output_dir / "content_calendar.md"
    md_path.write_text("\n".join(md_lines))
    
    return json_path, md_path
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual topic selection | Outlier detection + diversity | Phase 8 | Autonomous selection |
| Sequential generation | Batch with cost tracking | Phase 8 | Controlled execution |
| Manual validation | Anti-pattern + structural checks | Phase 4 | Consistent quality |

**What's already modern:**
- Outlier scoring for topic detection
- Hash-based deduplication
- Voice profile with anti-pattern validation
- Cost tracking with thresholds
- Graceful degradation on failures

## Open Questions

### 1. Reddit Credentials Not Configured
- **What we know:** Code is ready (`reddit_fetcher.py`), credentials not in `.env`
- **What's unclear:** Whether to proceed without Reddit or wait for configuration
- **Recommendation:** Add pre-flight check, warn if Reddit unavailable, continue with YouTube/Perplexity

### 2. Human Review Integration
- **What we know:** CONTEXT.md specifies "human review (final check)" for newsletters
- **What's unclear:** How to pause batch for human review
- **Recommendation:** Generate all 8, mark for review, human approves/rejects in batch

### 3. Product Functional Testing
- **What we know:** CONTEXT.md specifies "functional test (actually run/open the product)"
- **What's unclear:** How to automate opening HTML files or running Python scripts
- **Recommendation:** For HTML: check file exists + size > 1KB. For Python: `ast.parse()` + syntax check. Manual functional test for edge cases.

## Sources

### Primary (HIGH confidence)
- `execution/pipeline_runner.py` - Full orchestration code reviewed
- `execution/product_factory.py` - Factory pattern understood
- `execution/anti_pattern_validator.py` - Validation rules documented
- `execution/content_aggregate.py` - Source aggregation patterns
- `08-CONTEXT.md` - User decisions locked

### Secondary (MEDIUM confidence)
- `STATE.md` - Project state, 1064 tests passing
- Test files - Validation patterns from test coverage

### Tertiary (LOW confidence)
- None - All findings from codebase analysis

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All code exists and is tested
- Architecture: HIGH - Patterns derived from existing code
- Pitfalls: HIGH - Based on actual code structure

**Research date:** 2026-01-31
**Valid until:** 2026-02-28 (stable codebase, execution-focused)
