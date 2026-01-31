# Affiliate Finder
<!-- DOE-VERSION: 2026.01.31 -->

## Goal
Discover monetization opportunities for weekly newsletter topics.

## Trigger Phrases
- "find affiliates for [topic]"
- "monetization options for [topic]"
- "what can I sell for [topic]"
- "affiliate finder [topic]"

## Quick Start
```bash
python execution/affiliate_finder.py "[topic]" --context "[newsletter summary]"
```

## What It Does
1. Discovers 5+ relevant affiliate programs via Perplexity
2. Generates 3 product alternatives you could create
3. Creates pitch angles for each option (Hormozi/Suby voice)
4. Outputs markdown with:
   - Top 3 affiliates (commission, quality, network)
   - Top 3 products (type, complexity, value)
   - Ranking rationale
   - Ready-to-use pitch angles

## Options

| Flag | Description |
|------|-------------|
| `--context TEXT` | Newsletter context for better relevance |
| `--no-save` | Don't save output to file (print only) |
| `--output-dir PATH` | Custom output directory |
| `--no-rationale` | Skip ranking rationale generation |
| `-q, --quiet` | Suppress progress output |
| `--verify-version` | Verify DOE version match and exit |

## Output
Markdown file saved to `output/monetization/[date]-[topic].md`

Contains:
- Tables for quick comparison
- Full details with pitch angles
- Decision workflow (pick affiliate OR product)

## Example Output
```markdown
# Monetization Options: email deliverability

## Top 3 Affiliate Opportunities

| # | Program | Commission | Quality | Network |
|---|---------|------------|---------|---------|
| 1 | Klaviyo Partner | 20% | excellent | PartnerStack |
| 2 | Sendgrid Affiliate | 15% | good | Impact |
| 3 | Mailgun Program | $50 | mediocre | direct |

## Top 3 Product Alternatives

| # | Concept | Type | Complexity | Value |
|---|---------|------|------------|-------|
| 1 | Email checker tool | HTML tool | medium | $47-67 |
| 2 | Subject line calculator | Google Sheet | easy | $27-37 |
| 3 | Automation templates | PDF | easy | $37-47 |

## Ranking Rationale
...

## Full Details
...
```

## Notes
- Affiliates verified for accessibility (not closed/waitlisted)
- Products prioritize HTML tools and automations
- If <2 good affiliates found, output recommends product path
- Graceful degradation: continues if one API fails

## Required Environment Variables
- `PERPLEXITY_API_KEY` - For affiliate discovery research
- `ANTHROPIC_API_KEY` - For pitch and rationale generation

## Version
Script: `execution/affiliate_finder.py`
DOE-VERSION: 2026.01.31
