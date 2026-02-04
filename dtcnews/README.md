# DTCNews AI Newsletter System
<!-- DOE-VERSION: 2026.02.04 -->

Generate high-value newsletters by finding what's **crushing it** in ecommerce and building the entire issue around that viral edge.

## Quick Start

```bash
cd dtcnews

# 1. Make sure .env is linked (should already be done)
ls -la .env  # Should show symlink to parent .env

# 2. Generate a newsletter (interactive)
python execution/newsletter_orchestrator.py --issue 1
```

That's it! The orchestrator will:
1. Ask if you have a sponsor/affiliate
2. Find the viral edge
3. Generate everything from that one tactic

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  START: Sponsor/Affiliate Question                          │
│  ├── No? → Find best tool + look for affiliate program      │
│  └── Yes? → Who? → Specific positioning angle?              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Find the Viral Edge                                │
│  Search → Rank by outlier score → Filter covered topics     │
└─────────────────────────────────────────────────────────────┘
                            ↓
           The viral edge determines EVERYTHING
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  SECTION 1: This Week's Win (Hook)                          │
│  → Punchy intro to the tactic, proof points                 │
├─────────────────────────────────────────────────────────────┤
│  SECTION 2: The Deep Dive (Meat)                            │
│  → WHO did it, WHAT they did, WHY it worked, HOW to apply   │
├─────────────────────────────────────────────────────────────┤
│  SECTION 3: Tool of the Week (Contextual!)                  │
│  → Free options, Paid options, Our Recommendation           │
│  → Damaging admission for authenticity                      │
│  → Social proof, affiliate link if no sponsor               │
├─────────────────────────────────────────────────────────────┤
│  SECTION 4: The Prompt Drop (AI Accelerator)                │
│  → Detailed prompt to execute the tactic                    │
│  → What it produces, how to customize                       │
├─────────────────────────────────────────────────────────────┤
│  SECTION 5: Your Next 24 Hours (Action)                     │
│  → ONE specific task, time required, success metric         │
└─────────────────────────────────────────────────────────────┘
```

## Commands

### Generate a Newsletter (Recommended)

```bash
# Interactive mode - asks sponsor questions
python execution/newsletter_orchestrator.py --issue 1

# With a sponsor
python execution/newsletter_orchestrator.py --issue 2 \
  --sponsor "Klaviyo" \
  --angle "Position as #1 for abandoned cart recovery"

# Quick test (skip sponsor questions)
python execution/newsletter_orchestrator.py --issue 1 --skip-sponsor
```

### Run Individual Steps

```bash
# Just find viral content
python execution/search_fetcher.py

# Just rank content
python execution/outlier_ranker.py --show-analysis

# Just research tools for a tactic
python execution/tool_researcher.py --tactic "AI video creation for ads"

# Research tools with sponsor
python execution/tool_researcher.py \
  --tactic "email automation" \
  --sponsor "Klaviyo" \
  --angle "Emphasize their free tier"

# Generate deep dive on specific topic
python execution/deep_dive_generator.py --topic "Instagram DM strategy"

# Check what topics were recently covered
python execution/topic_tracker.py --list
```

### Legacy Pipeline (Step-by-Step)

```bash
# Run old-style pipeline
python execution/dtcnews_pipeline.py

# See pipeline status
python execution/dtcnews_pipeline.py --status

# Run specific steps
python execution/dtcnews_pipeline.py --steps aggregate,rank,deep_dive
```

## Sponsor/Affiliate Logic

### No Sponsor
- Finds genuinely best tool for the tactic
- Researches if affiliate program exists
- Provides signup link if available
- Honest recommendation

### With Sponsor (no specific angle)
- Researches competitor tools for context
- Appears unbiased but leans toward sponsor advantages
- Uses "damaging admission" technique for authenticity
- Acknowledges minor flaw, counters with why benefits outweigh

### With Sponsor + Specific Angle
- Positions sponsor exactly as requested
- Examples: "#1 for beginners", "Highlight new AI feature", etc.
- Still includes competitor context for authenticity

## Output Files

```
output/
├── newsletters/
│   ├── 2026-02-04-issue-1.md       # Complete newsletter
│   └── 2026-02-04-issue-1.json     # Structured data
├── content_YYYY-MM-DD.json          # Raw viral content
├── content_ranked_YYYY-MM-DD.json   # Ranked content
├── deep_dive_YYYY-MM-DD.json        # Deep dive data
├── tool_research_YYYY-MM-DD.json    # Tool research
└── ...
```

## Environment Variables

Only ONE required:

```
OPENROUTER_API_KEY=sk-or-v1-xxxxx    # For Claude + Perplexity/Sonar
```

Get it at: https://openrouter.ai/keys

## Folder Structure

```
dtcnews/
├── execution/               # All scripts
│   ├── newsletter_orchestrator.py  # MAIN - generates full newsletter
│   ├── search_fetcher.py           # Finds viral content via Perplexity
│   ├── outlier_ranker.py           # Ranks by composite score
│   ├── deep_dive_generator.py      # Creates WHO/WHAT/WHY/HOW
│   ├── tool_researcher.py          # Researches tools + affiliates
│   ├── topic_tracker.py            # Prevents duplicate topics
│   └── ...
├── directives/              # Workflow documentation
├── learnings/               # What we've learned
├── data/                    # Reference data (hooks, products)
├── output/                  # Generated content
└── .env → ../.env           # Symlink to parent API keys
```

## The Philosophy

1. **Everything flows from the viral edge** - One tactic drives the whole issue
2. **Tools are contextual** - Recommend what helps THIS tactic, not random tools
3. **Authenticity sells** - Damaging admissions build trust
4. **Executable today** - Specific actions with specific tools in specific time
5. **Topic deduplication** - Don't cover "email marketing" every week

## Quick Reference

| Task | Command |
|------|---------|
| Generate newsletter | `python execution/newsletter_orchestrator.py --issue N` |
| Find viral content | `python execution/search_fetcher.py` |
| Research a tool | `python execution/tool_researcher.py -t "tactic"` |
| Check covered topics | `python execution/topic_tracker.py --list` |
| Record a topic | `python execution/topic_tracker.py --record "topic" --issue N` |
