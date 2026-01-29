# Architecture

**Analysis Date:** 2025-01-29

## Pattern Overview

**Overall:** Directive-Orchestration-Execution (DOE) Framework

**Key Characteristics:**
- Human-readable directives define workflows in plain English
- AI orchestration layer routes requests and makes decisions
- Python scripts handle deterministic execution
- Three-layer separation prevents error compounding
- Self-improving system with user-approved modifications

## Layers

**Directives Layer:**
- Purpose: Store workflow instructions in plain English
- Location: `directives/`
- Contains: Markdown files defining what each workflow does, trigger phrases, steps, outputs
- Depends on: Nothing (top of stack)
- Used by: AI orchestration layer for routing and execution guidance

**Orchestration Layer:**
- Purpose: AI-powered decision making and routing
- Location: External (Claude Code, Cursor, Gemini reading CLAUDE.md/AGENTS.md/GEMINI.md)
- Contains: Instructions for how AI should operate, error handling, escalation rules
- Depends on: `directives/` for workflow definitions, `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` for operating instructions
- Used by: User requests routed through AI interface

**Execution Layer:**
- Purpose: Deterministic Python scripts that do the actual work
- Location: `execution/`
- Contains: Python scripts with CLI interfaces, one per workflow
- Depends on: `.env` for configuration, external APIs as needed
- Used by: Orchestration layer (AI calls these scripts)

## Data Flow

**Request Processing:**

1. User makes request to AI (Claude Code, etc.)
2. AI reads instructions from `CLAUDE.md` (or `AGENTS.md`/`GEMINI.md`)
3. AI searches `directives/` for matching trigger phrases
4. If found: AI follows directive steps, calls `execution/*.py` scripts
5. If not found: AI researches approaches, builds workflow, crystallizes to directive + script

**Workflow Execution:**

1. AI locates directive in `directives/[workflow].md`
2. AI verifies version alignment with `execution/[workflow].py`
3. AI runs Python script with appropriate arguments
4. Script processes data, writes temp files to `.tmp/` if needed
5. Script returns results to stdout or specified output location
6. AI validates results per directive's validation criteria
7. AI reports success/failure to user

**State Management:**
- No persistent state between runs (stateless design)
- Temporary files stored in `.tmp/` (gitignored)
- Cost tracking appends to `.tmp/cost_log.jsonl`
- Configuration stored in `.env` (gitignored)

## Key Abstractions

**Directive:**
- Purpose: Capture a reusable workflow in human-readable form
- Examples: `directives/csv_to_json.md`, `directives/weather_lookup.md`
- Pattern: Markdown with structured sections (Goal, Trigger Phrases, Quick Start, What It Does, Output)
- Version tagged with `<!-- DOE-VERSION: YYYY.MM.DD -->` comment

**Execution Script:**
- Purpose: Implement workflow logic in deterministic Python code
- Examples: `execution/csv_to_json.py`, `execution/weather_lookup.py`
- Pattern: CLI tool with argparse, version constant `DOE_VERSION`, main() entry point
- Must match directive version for execution

**Agent Instructions:**
- Purpose: Define how AI operates across all workflows
- Examples: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` (all identical)
- Pattern: Mirrored files for different AI tool compatibility
- Synced via `execution/sync_agent_files.py`

**Pipeline:**
- Purpose: Chain multiple workflows where output feeds input
- Examples: `pipelines/PIPELINES.md` (documentation only currently)
- Pattern: ASCII flow diagrams + step tables showing data handoffs

## Entry Points

**User → AI:**
- Location: Any AI tool (Claude Code, Cursor, etc.)
- Triggers: Natural language requests matching directive trigger phrases
- Responsibilities: Route request, execute workflow, report results

**AI → Scripts:**
- Location: `execution/*.py` (each script is an entry point)
- Triggers: CLI invocation with arguments
- Responsibilities: Process input, interact with APIs, produce output

**Framework Maintenance:**
- Location: `execution/sync_agent_files.py`
- Triggers: `--check`, `--sync`, `--add-learning`, etc.
- Responsibilities: Keep agent files synchronized, add learnings

**Utilities:**
- Location: `execution/doe_utils.py`
- Triggers: `costs`, `list`, `check-versions` subcommands
- Responsibilities: Cost tracking, directive listing, version alignment

## Error Handling

**Strategy:** Classify errors, act per classification, update directives with learnings

**Patterns:**

**Configuration Errors (fix once, no retry):**
- Missing API key → Add to `.env`
- Wrong file path → Correct in directive
- Action: Fix config, don't update directive

**Transient Errors (retry with backoff):**
- Rate limiting → Wait 1s, 2s, 4s, 8s (max 60s)
- Network timeout → Retry up to 3x
- Action: Retry, update directive only if pattern persists

**Logic Errors (update script + directive):**
- Wrong output format → Fix script, update directive Output section
- Missing edge case → Add handling, bump version
- Action: Fix both files, bump version tag

**External Errors (escalate to human):**
- API deprecated or changed → Notify user, document in learnings
- Cost threshold exceeded → Pause and confirm
- Action: Stop, notify, await human input

## Cross-Cutting Concerns

**Logging:** Console output via print statements, cost tracking to `.tmp/cost_log.jsonl`

**Validation:** Per-directive validation criteria (output exists, exit code 0, no errors)

**Authentication:** API keys stored in `.env`, loaded via `python-dotenv`

**Version Control:** Directive ↔ Script version tags must match (`DOE-VERSION`)

**Self-Improvement:** AI proposes changes to agent instructions, requires user approval, syncs across all three agent files

---

*Architecture analysis: 2025-01-29*
