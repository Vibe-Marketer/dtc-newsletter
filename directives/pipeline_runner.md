# Pipeline Runner
<!-- DOE-VERSION: 2026.01.31 -->

## Goal
Run the complete DTC newsletter pipeline with a single command.

## Trigger Phrases
**Matches:**
- "run the pipeline"
- "generate newsletter"
- "run newsletter pipeline"
- "create this week's newsletter"

## Quick Start
```bash
# Full pipeline (auto-detect topic)
python execution/pipeline_runner.py

# Specify topic
python execution/pipeline_runner.py --topic "tiktok shop strategies"

# Quiet mode (for automation)
python execution/pipeline_runner.py -q

# Skip affiliate discovery
python execution/pipeline_runner.py --skip-affiliates
```

## What It Does
1. Aggregates content from Reddit, YouTube, and stretch sources
2. Generates 5-section newsletter with Hormozi/Suby voice
3. Discovers affiliate opportunities (optional)
4. Saves newsletter to output/newsletters/{month}/{issue}-{topic}.md
5. Updates index.json manifest
6. Logs costs to data/cost_log.json
7. Sends macOS notification on completion

## Output
- Newsletter markdown: `output/newsletters/YYYY-MM/{issue}-{topic}.md`
- Index manifest: `output/newsletters/index.json`
- Cost log: `data/cost_log.json`

## Flags
| Flag | Description |
|------|-------------|
| `-q, --quiet` | Suppress progress output |
| `-v, --verbose` | Show debug output |
| `--topic TEXT` | Override auto-detected topic |
| `--skip-affiliates` | Skip affiliate discovery |
| `--dry-run` | Show what would run |

## Error Handling
- Pipeline continues if individual sources fail
- Claude API retries 3x with exponential backoff
- Warns (doesn't fail) if cost > $1/operation or $10/run
- Notification sent on both success and failure

## Prerequisites

### API Keys
```
ANTHROPIC_API_KEY=your_anthropic_key
PERPLEXITY_API_KEY=your_perplexity_key  # optional, for stretch sources
APIFY_TOKEN=your_apify_token             # optional, for stretch sources
```

### Required Files
- `output/content_sheet.json` (created by content aggregation)

## Workflow Integration

Typical workflow:
```bash
# 1. Run the full pipeline
python execution/pipeline_runner.py --topic "email marketing tips"

# 2. Review the generated newsletter
cat output/newsletters/2026-01/001-email-marketing-tips.md

# 3. Copy to Beehiiv for publishing
# (Manual step - no Beehiiv API)
```

## Changelog

### 2026.01.31
- Initial release with full orchestration
- Content aggregation from Reddit, YouTube
- Optional stretch sources (Twitter, TikTok, Amazon)
- Newsletter generation with 5-section format
- Affiliate discovery integration
- Cost tracking and logging
- macOS desktop notifications
- Graceful degradation on source failures
