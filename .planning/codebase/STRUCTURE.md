# Codebase Structure

**Analysis Date:** 2025-01-29

## Directory Layout

```
dtc-newsletter/
├── AGENTS.md              # AI instructions (mirror)
├── CLAUDE.md              # AI instructions (mirror)
├── GEMINI.md              # AI instructions (mirror)
├── README.md              # Project overview and setup
├── REFERENCE.md           # Deep framework documentation
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore             # Git ignore rules
├── directives/            # Workflow definitions (markdown)
├── execution/             # Python scripts
├── pipelines/             # Multi-workflow documentation
├── learnings/             # Failed approaches archive
├── data/                  # Sample data files
└── .tmp/                  # Temporary files (gitignored)
```

## Directory Purposes

**directives/:**
- Purpose: Store workflow instructions in human-readable markdown
- Contains: One `.md` file per workflow, plus `_TEMPLATE.md`
- Key files:
  - `_TEMPLATE.md`: Starter template for new directives
  - `csv_to_json.md`: Example workflow (no API)
  - `weather_lookup.md`: Example workflow (with API)
  - `agent_instructions_maintenance.md`: Framework self-management

**execution/:**
- Purpose: Store Python scripts that implement workflow logic
- Contains: One `.py` file per workflow, plus templates and utilities
- Key files:
  - `_TEMPLATE.py`: Starter template for new scripts
  - `csv_to_json.py`: Example script (no API)
  - `weather_lookup.py`: Example script (with API)
  - `sync_agent_files.py`: Synchronize AGENTS.md/CLAUDE.md/GEMINI.md
  - `doe_utils.py`: Cost tracking, directive listing, version checking

**pipelines/:**
- Purpose: Document multi-step workflows where outputs chain to inputs
- Contains: `PIPELINES.md` with flow diagrams and step tables
- Key files: `PIPELINES.md`

**learnings/:**
- Purpose: Archive failed approaches to prevent re-discovering dead ends
- Contains: One `.md` file per workflow that had alternatives tested
- Key files: `_TEMPLATE.md`

**data/:**
- Purpose: Sample data for testing workflows
- Contains: Example files for workflow input
- Key files: `sample.csv`

**.tmp/:**
- Purpose: Temporary processing files, never committed
- Contains: Intermediate outputs, cost logs, backups
- Generated: `cost_log.jsonl`, `agent_backups/`

## Key File Locations

**Entry Points:**
- `CLAUDE.md`: AI reads this for operating instructions (source of truth)
- `AGENTS.md`: Same content, for tools expecting this filename
- `GEMINI.md`: Same content, for Gemini
- `execution/*.py`: Each script is a CLI entry point

**Configuration:**
- `.env`: API keys and secrets (gitignored, create from `.env.example`)
- `.env.example`: Template showing required environment variables
- `.gitignore`: Defines what files to exclude from git

**Core Logic:**
- `execution/sync_agent_files.py`: Framework file synchronization
- `execution/doe_utils.py`: Framework utilities (costs, versions, listing)

**Documentation:**
- `README.md`: Quick start guide
- `REFERENCE.md`: Complete framework documentation (611 lines)
- `pipelines/PIPELINES.md`: Multi-workflow chain documentation

**Templates:**
- `directives/_TEMPLATE.md`: New directive starter
- `execution/_TEMPLATE.py`: New script starter
- `learnings/_TEMPLATE.md`: New learnings file starter

**Testing:**
- No dedicated test directory (scripts are tested manually via CLI)

## Naming Conventions

**Files:**
- Directives: `snake_case.md` (e.g., `csv_to_json.md`, `weather_lookup.md`)
- Scripts: `snake_case.py` matching directive name (e.g., `csv_to_json.py`)
- Templates: `_TEMPLATE.md` or `_TEMPLATE.py` (underscore prefix)
- Agent files: `UPPERCASE.md` (e.g., `AGENTS.md`, `CLAUDE.md`)

**Directories:**
- Lowercase, singular or simple plural (e.g., `directives`, `execution`, `data`)

**Version Tags:**
- Format: `YYYY.MM.DD` or `YYYY.MM.DD-suffix`
- In directives: `<!-- DOE-VERSION: 2026.01.23 -->`
- In scripts: `DOE_VERSION = "2026.01.23"`

**Environment Variables:**
- UPPERCASE with underscores (e.g., `WEATHER_API_KEY`, `DOE_COST_TRACKING`)

## Where to Add New Code

**New Workflow:**
- Primary directive: `directives/[workflow_name].md` (copy from `_TEMPLATE.md`)
- Primary script: `execution/[workflow_name].py` (copy from `_TEMPLATE.py`)
- Match the names: directive name = script name
- Both must have matching `DOE-VERSION` tags

**New Utility Function:**
- Add to `execution/doe_utils.py` if framework-wide utility
- Or create dedicated `execution/[utility].py` if workflow-specific

**New Pipeline:**
- Document in `pipelines/PIPELINES.md`
- Reference existing directives, don't create new workflow files

**Failed Approaches:**
- Create `learnings/[workflow_name].md` (copy from `_TEMPLATE.md`)
- Document what was tried, why it failed, when to reconsider

**Sample Data:**
- Add to `data/` directory
- Reference in directive's Quick Start section

## Special Directories

**.tmp/:**
- Purpose: All temporary and generated files during execution
- Generated: Yes (created by scripts as needed)
- Committed: No (gitignored)
- Subdirectories: `agent_backups/` for pre-sync backups, workflow-specific dirs as needed

**node_modules/:**
- Purpose: Node.js dependencies (if using Remotion or similar)
- Generated: Yes (via npm install)
- Committed: No (gitignored)

**.git/:**
- Purpose: Git version control data
- Generated: Yes (on git init)
- Committed: N/A (is the repository itself)

**.venv/:**
- Purpose: Python virtual environment (if used)
- Generated: Yes (via python -m venv)
- Committed: No (gitignored)

## Import Patterns

**Python Scripts:**
```python
# Standard library first
import os
import sys
import argparse
from pathlib import Path

# Third-party after blank line
from dotenv import load_dotenv
import requests  # Only when needed

# Local imports (if any)
# from doe_utils import log_cost  # For cost tracking
```

**Environment Loading:**
```python
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("SERVICE_API_KEY")
```

---

*Structure analysis: 2025-01-29*
