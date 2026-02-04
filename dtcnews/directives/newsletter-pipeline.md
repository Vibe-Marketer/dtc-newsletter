# Newsletter Pipeline
<!-- DOE-VERSION: 2026.02.04 -->

## Goal
Generate a high-value newsletter by finding what's **crushing it** in ecommerce and translating it into actionable content for beginners.

## Trigger Phrases
- "run the newsletter"
- "generate newsletter"
- "create this week's newsletter"
- "run pipeline"

## Quick Start
```bash
cd dtcnews
python execution/dtcnews_pipeline.py
```

## What It Does

### Phase 1: Find What's Crushing It
1. **Aggregate** - Fetch viral content from Reddit, YouTube
2. **Rank** - Score by outlier performance + virality analysis

### Phase 2: Create Genuine Value
3. **Deep Dive** - Generate WHO/WHAT/WHY/HOW breakdown
4. **Select** - Pick content for other sections
5. **Generate** - Assemble full newsletter

### Phase 3: Polish for Impact
6. **Hormozi** - Strengthen hooks with 100M Hooks framework
7. **Schwartz** - Strengthen claims with Breakthrough Advertising
8. **Products** - Insert 2-3 natural product mentions
9. **Edit** - Reading level, jargon, spam triggers

### Phase 4: Human Approval
10. **Review** - You approve before sending

## Resume Mid-Pipeline

```bash
# Already aggregated? Start from ranking
python execution/dtcnews_pipeline.py --start-from rank

# Already have draft? Start from editing
python execution/dtcnews_pipeline.py --start-from edit

# Just need copy review?
python execution/dtcnews_pipeline.py --steps hormozi,schwartz
```

## Output
- `output/newsletter_final_YYYY-MM-DD.md` - Ready for human review
- `output/deep_dive_YYYY-MM-DD.md` - The deep dive section
- All intermediate files in `output/`

## Key Principles
1. **Outlier-first** - Find what's actually viral, not "beginner keywords"
2. **Genuine value** - Extract the mechanism, not just the tactic
3. **Same principles scale** - Beginners get the same insight at their level
4. **Executable today** - Every issue has 3 specific actions

## Error Recovery
- If aggregation fails: Check API keys in `.env`
- If ranking fails: Check `output/content_*.json` exists
- If deep dive fails: Run manually with `--topic "your topic"`
- If editing fails: Check for voice violations, fix and re-run
