# Agent Instructions
<!-- DOE-VERSION: 2026.02.04 -->

You help run and improve the DTCNews AI newsletter system.

---

## How You Operate

### On Every Request

1. **Check `directives/`** for existing workflow
2. **If found:** Execute it
3. **If not found:** Research, build, then save

### The Newsletter Pipeline

The main workflow is in `directives/newsletter-pipeline.md`. Run it with:

```bash
python execution/dtcnews_pipeline.py
```

### Key Commands

| User Says | You Do |
|-----------|--------|
| "run the newsletter" | `python execution/dtcnews_pipeline.py` |
| "check pipeline status" | `python execution/dtcnews_pipeline.py --status` |
| "pick up from [step]" | `python execution/dtcnews_pipeline.py --start-from [step]` |
| "just run [steps]" | `python execution/dtcnews_pipeline.py --steps [steps]` |
| "dry run" | `python execution/dtcnews_pipeline.py --dry-run` |

### Available Steps

```
aggregate  → rank → deep_dive → select → generate → hormozi → schwartz → products → edit → review
```

---

## Error Handling

| Error | Fix |
|-------|-----|
| "API key not set" | Check `.env` has the required keys |
| "File not found" | Run earlier pipeline step first |
| "JSON parse error" | Check output file, may need manual fix |
| Step failed | Check logs, fix issue, resume with `--start-from` |

---

## Learnings

When you learn something that improves the system:

1. Add it to `learnings/README.md`
2. Update relevant scripts if needed
3. Bump DOE-VERSION in affected files

---

## Core Principles

1. **Outlier-first** - Find what's actually viral, then assess
2. **Genuine value** - Extract the mechanism, not surface tactics
3. **Same principles scale** - Beginners get the same insight
4. **Executable today** - Specific actions, specific tools, specific times

---

## File Locations

| What | Where |
|------|-------|
| Scripts | `execution/` |
| Workflows | `directives/` |
| Learnings | `learnings/` |
| Reference data | `data/` |
| Generated output | `output/` |
| API keys | `.env` |
