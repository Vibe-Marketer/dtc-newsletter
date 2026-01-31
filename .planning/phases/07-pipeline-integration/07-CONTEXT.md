# Phase 7: Pipeline Integration - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete orchestration of all pipeline components (content aggregation, newsletter generation, affiliate discovery) with error handling, cost tracking, and graceful degradation. Single command runs the full pipeline; individual stages remain runnable separately.

</domain>

<decisions>
## Implementation Decisions

### CLI Experience
- Progress shown by default (stage announcements: "Fetching Reddit... Done.")
- `-q` flag for quiet mode, `-v` flag for debug/verbose
- No dry-run mode needed (real runs are cheap enough)
- Both full pipeline command AND modular stage commands
- Auto-detect trending topics by default, `--topic` flag to override

### Failure Handling
- Continue without failed sources (log warning, proceed with available data)
- Retry 3x with exponential backoff (1s, 2s, 4s) for Claude API failures
- Partial success acceptable: save newsletter even if affiliate discovery fails
- Always notify on completion (success or failure) via desktop notification

### Progress & Cost Reporting
- Stage announcements for progress: "Fetching Reddit... Done. Generating newsletter..."
- Real-time cost display after each API call, plus total at end
- Warn (but don't block) if single operation > $1 or run total > $10
- Persistent cost log: both current run AND cumulative history in `data/cost_log.json`

### Output Organization
- Newsletter filenames: `{issue_number:03d}-{topic-slug}.md` (e.g., `001-tiktok-shop-strategies.md`)
- Issue number auto-increments by scanning `output/newsletters/` for highest existing
- Dated subfolders: `output/newsletters/2026-01/001-topic.md` (grouped by month)
- Manifest file: `output/newsletters/index.json` with all newsletters (date, topic, issue, path)

### Claude's Discretion
- Exact notification mechanism (macOS notification, terminal bell, etc.)
- Cost estimation approach for real-time display
- Topic slug generation (how to slugify detected topics)
- Index.json schema (what fields to include beyond the basics)

</decisions>

<specifics>
## Specific Ideas

- Stage announcements should be simple text, not progress bars or spinners
- Cost warnings should be visible but non-blocking (don't interrupt automation)
- The pipeline should "just work" for weekly automated runs while still being debuggable when needed

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 07-pipeline-integration*
*Context gathered: 2026-01-31*
