# Newsletter Generation
<!-- DOE-VERSION: 2026.01.31 -->

## Goal

Generate a complete DTC Money Minute newsletter from aggregated content. Produces Beehiiv-ready markdown with subject line, preview text, and all 5 sections following the Hormozi/Suby voice profile.

---

## Trigger Phrases

**Matches:**
- "generate newsletter"
- "create newsletter"
- "newsletter from content"
- "write newsletter"
- "generate dtc money minute"
- "make newsletter from"
- "newsletter for issue"

---

## Quick Start

```bash
# Generate from content sheet JSON
python execution/newsletter_generator.py --content-file output/content_sheet.json --issue-number 1

# With tool recommendation
python execution/newsletter_generator.py --content-file data.json --issue-number 5 \
  --tool-name "Klaviyo" --tool-description "Email marketing platform" \
  --tool-why "2x email revenue for DTC brands"

# Different PS type
python execution/newsletter_generator.py --content-file data.json --issue-number 3 --ps-type cta

# Dry run (preview without saving)
python execution/newsletter_generator.py --content-file data.json --issue-number 1 --dry-run
```

---

## What It Does

1. **Content Selection** — Selects best content for each section based on outlier score and type fit
2. **Section 1: Instant Reward** — 30-60 word hook (quote, stat, or viral observation)
3. **Section 2: What's Working Now** — 300-500 word tactical content (THE MEAT)
4. **Section 3: The Breakdown** — 200-300 word story-sell bridge
5. **Section 4: Tool of the Week** — 100-200 word insider tool recommendation
6. **Section 5: PS Statement** — 20-40 word closer (foreshadow/cta/meme)
7. **Subject Line** — Under 50 chars with style rotation (70% curiosity, 20% direct, 10% question)
8. **Preview Text** — 40-90 char hook for email preview
9. **Markdown Output** — Beehiiv-ready format with metadata comments

---

## Output

**Newsletter Location:** `output/newsletters/{date}-issue-{number}.md`
**Metadata Location:** `output/newsletters/{date}-issue-{number}-meta.json`

**Markdown format:**
```markdown
<!-- Subject: DTC Money Minute #1: the secret no one talks about -->
<!-- Preview: The $47 tool that 8-figure brands use daily -->
<!-- Issue: 1 -->
<!-- Generated: 2026-01-31T14:00:00Z -->

[Section 1 content - instant reward]

[Section 2 content - tactical meat]

[Section 3 content - story breakdown]

[Section 4 content - tool recommendation]

[Section 5 - PS statement]
```

**Console output:**
```
=== Newsletter Generated ===
Issue: #1
Subject: DTC Money Minute #1: the strategy that works
Preview: The one change that doubled their email revenue

Generation time: 45.2s
Sources used: reddit, youtube

Word counts:
  section_1: 42
  section_2: 387
  section_3: 234
  section_4: 156
  section_5: 28

Saved to: output/newsletters/2026-01-31-issue-1.md
```

---

## Prerequisites

### API Keys

```
ANTHROPIC_API_KEY=your_anthropic_key
```

Get key from: https://console.anthropic.com/settings/keys

### Content File

Requires aggregated content from `content_aggregate.py`:
```bash
python execution/content_aggregate.py
# Creates: output/content_sheet.json
```

---

## CLI Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--content-file` | Yes | - | Path to aggregated content JSON |
| `--issue-number` | Yes | - | Newsletter issue number |
| `--tool-name` | No | - | Tool name for Section 4 |
| `--tool-description` | No | - | Tool description for Section 4 |
| `--tool-why` | No | - | Why tool helps for Section 4 |
| `--tool-link` | No | - | Optional link for Section 4 |
| `--ps-type` | No | `foreshadow` | PS type: foreshadow, cta, or meme |
| `--output-dir` | No | `output/newsletters/` | Output directory |
| `--dry-run` | No | - | Preview without saving |

---

## Content File Format

Accepts JSON in these formats:

**Array format:**
```json
[
  {"title": "...", "summary": "...", "source": "reddit", "outlier_score": 4.5},
  {"title": "...", "summary": "...", "source": "youtube", "outlier_score": 3.2}
]
```

**Object with contents key:**
```json
{
  "metadata": {...},
  "contents": [
    {"title": "...", "summary": "...", "source": "reddit", "outlier_score": 4.5}
  ]
}
```

---

## Tool Info

Section 4 requires tool information. Provide via CLI or it uses placeholder:

```bash
--tool-name "Postscript" \
--tool-description "SMS marketing for e-commerce" \
--tool-why "Most stores ignore SMS. This one gets 25% CTR."
```

---

## PS Types

| Type | Purpose | Example |
|------|---------|---------|
| `foreshadow` | Tease next week | "PS: Next week I'm revealing the $0 ad strategy..." |
| `cta` | Secondary action | "PS: Hit reply and tell me your biggest challenge..." |
| `meme` | Relatable humor | "PS: If you read this far, you're in the top 10%..." |

---

## Voice Profile

Newsletter uses Hormozi/Suby hybrid voice:
- Short, punchy sentences (8-12 words avg)
- No fluff words (basically, essentially, just)
- Concrete numbers when available
- 28 anti-patterns blocked (game-changer, unlock potential, etc.)

---

## Edge Cases

### Missing content
**Behavior:** Uses placeholder text, logs warning

### No tool_info provided
**Behavior:** Generates with placeholder tool, logs warning

### Subject line validation fails
**Behavior:** Retries with stricter prompt, raises error if second attempt fails

### Content file not found
**Behavior:** Exits with error message

---

## Workflow Integration

Typical workflow:
```bash
# 1. Aggregate content
python execution/content_aggregate.py

# 2. Generate newsletter
python execution/newsletter_generator.py \
  --content-file output/content_sheet.json \
  --issue-number 1 \
  --tool-name "Postscript" \
  --tool-description "SMS marketing platform" \
  --tool-why "25% CTR vs 2% email"

# 3. Copy markdown to Beehiiv
# Output at: output/newsletters/2026-01-31-issue-1.md
```

---

## Changelog

### 2026.01.31
- Initial release with full orchestration
- Content selection with diversity constraint
- All 5 section generators integrated
- Subject line with 70/20/10 style rotation
- Preview text generation
- Beehiiv-ready markdown output
- CLI with full argument support
