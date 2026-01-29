# Codebase Concerns

**Analysis Date:** 2026-01-29

## Tech Debt

**Incomplete Template Script:**
- Issue: `execution/_TEMPLATE.py` contains `# TODO: Implement` stub and non-functional placeholder code
- Files: `execution/_TEMPLATE.py`
- Impact: Template is not a working example; developers copying it get broken code
- Fix approach: Either remove the template (since it's documentation-only) or provide a minimal working implementation

**Version Date Format Inconsistency:**
- Issue: AGENTS.md references version date `2025.12.17` in documentation examples, but actual versions use `2025.12.19` and `2026.01.23`
- Files: `AGENTS.md` (line 31), `directives/*.md`, `execution/*.py`
- Impact: Copy-paste from docs creates outdated version tags
- Fix approach: Update AGENTS.md example to use `YYYY.MM.DD` placeholder or current date

**Cost Tracking Not Wired Up:**
- Issue: `doe_utils.py` provides `log_cost()` function, but no scripts actually call it
- Files: `execution/doe_utils.py`, `execution/_TEMPLATE.py` (commented out example)
- Impact: Cost tracking feature exists but produces no data; `python execution/doe_utils.py costs` returns "No cost data found"
- Fix approach: Either integrate `log_cost()` into scripts that make API calls, or remove the feature

**Empty Return Pattern:**
- Issue: `read_cost_log()` returns empty list `[]` without any error handling distinction
- Files: `execution/doe_utils.py` (line 69)
- Impact: Cannot distinguish between "no cost log file" and "cost log file is empty"
- Fix approach: Add explicit check for file existence vs empty file

## Known Bugs

**None Identified**
- No obvious bugs found in the codebase
- All scripts have proper error handling patterns

## Security Considerations

**API Key Handling:**
- Risk: API keys loaded via `dotenv` - standard practice but requires secure `.env` management
- Files: `execution/weather_lookup.py`, `execution/_TEMPLATE.py`, `.env.example`
- Current mitigation: `.gitignore` properly excludes `.env`, `credentials.json`, `token.json`, `*.pem`, `*.key`
- Recommendations: Add pre-commit hook to prevent accidental secret commits

**No Input Sanitization for File Paths:**
- Risk: Scripts accept file paths as arguments without path traversal protection
- Files: `execution/csv_to_json.py` (line 36)
- Current mitigation: None - relies on filesystem permissions
- Recommendations: For user-facing tools, validate paths are within expected directories

## Performance Bottlenecks

**No Async Patterns:**
- Problem: All scripts are synchronous; no async/await usage detected
- Files: All `execution/*.py` files
- Cause: Current workflows are simple single-operation scripts
- Improvement path: As pipelines grow, consider async for parallel API calls

**Large File Handling:**
- Problem: `csv_to_json.py` loads entire file into memory with `list(reader)`
- Files: `execution/csv_to_json.py` (line 48)
- Cause: Simple implementation for small files
- Improvement path: Add streaming JSON output for large CSV files (>10MB)

## Fragile Areas

**Agent File Sync Regex:**
- Files: `execution/sync_agent_files.py` (lines 376-428)
- Why fragile: Complex regex patterns for finding/inserting into "Remember" section; depends on exact markdown structure
- Safe modification: Add comprehensive tests before changing; use explicit markers instead of pattern matching
- Test coverage: No automated tests

**Version Extraction Regex:**
- Files: `execution/doe_utils.py` (lines 168-185)
- Why fragile: Assumes specific format `DOE-VERSION:` in directives and `DOE_VERSION = "..."` in scripts
- Safe modification: Document the exact format requirements; add validation on write
- Test coverage: No automated tests

## Scaling Limits

**Cost Log File:**
- Current capacity: Unbounded JSONL file
- Limit: Eventually becomes slow to parse for reporting; no log rotation
- Scaling path: Implement log rotation or periodic archival to `.tmp/cost_archive/`

**Agent File Size:**
- Current capacity: ~141 lines in AGENTS.md
- Limit: As learnings accumulate in "Remember" section, file grows unbounded
- Scaling path: Periodically consolidate learnings; move detailed docs to separate files

## Dependencies at Risk

**Minimal External Dependencies:**
- The project uses only `dotenv` and `requests` (optional for weather)
- Risk: Low - both are well-maintained packages
- No outdated or deprecated packages detected

## Missing Critical Features

**No Testing Infrastructure:**
- Problem: Zero test files (*.test.*, *.spec.*) found in codebase
- Blocks: Confidence in refactoring; CI/CD pipeline validation
- Priority: Medium - framework is simple enough to manually test, but should add tests before significant growth

**No CI/CD Configuration:**
- Problem: No GitHub Actions, CircleCI, or similar configuration files detected
- Blocks: Automated testing, deployment validation
- Priority: Low - local-first development model may not require it

**No Logging Framework:**
- Problem: Scripts use `print()` for all output; no structured logging
- Blocks: Production debugging, log aggregation
- Priority: Low - appropriate for current local-first scope

## Test Coverage Gaps

**No Automated Tests:**
- What's not tested: All functionality
- Files: All `execution/*.py` files
- Risk: Regressions go unnoticed; refactoring is risky
- Priority: Medium

**Specific Critical Paths Untested:**
1. `sync_agent_files.py` - file sync logic, learning insertion
2. `doe_utils.py` - version extraction, cost aggregation
3. Error handling paths in all scripts

---

*Concerns audit: 2026-01-29*
