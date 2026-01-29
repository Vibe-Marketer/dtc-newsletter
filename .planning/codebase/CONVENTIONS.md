# Coding Conventions

**Analysis Date:** 2026-01-29

## Naming Patterns

**Files:**
- Scripts: `snake_case.py` (e.g., `sync_agent_files.py`, `weather_lookup.py`)
- Templates: `_TEMPLATE.py` and `_TEMPLATE.md` (underscore prefix)
- Directives: `snake_case.md` matching script name (e.g., `weather_lookup.md`)

**Functions:**
- Use `snake_case` for all functions
- Use verbs for action functions: `sync_files()`, `check_sync()`, `add_learning()`
- Use `get_` prefix for getters: `get_file_content()`, `get_most_recent_modified()`

**Variables:**
- Use `snake_case` for all variables
- Use SCREAMING_SNAKE_CASE for module-level constants: `DOE_VERSION`, `API_KEY`, `AGENT_FILES`
- Use descriptive names: `source_content`, `filtered_entries`, `backup_path`

**Types:**
- Type hints used for function signatures: `def get_file_content(filepath: Path) -> str | None:`
- Python 3.10+ union syntax: `str | None` (not `Optional[str]`)

## Code Style

**Formatting:**
- No explicit formatter configured (Prettier/Black not detected)
- Indentation: 4 spaces (Python standard)
- Line length: ~100 characters observed

**Linting:**
- No linter configuration detected (.eslintrc, .flake8, ruff.toml, etc.)
- Code follows PEP 8 conventions informally

## Import Organization

**Order:**
1. Standard library imports (os, sys, argparse, json, re, etc.)
2. Third-party imports (requests, dotenv)
3. Local imports (none observed - flat module structure)

**Pattern from `execution/sync_agent_files.py`:**
```python
import os
import sys
import argparse
import difflib
import shutil
import re
from datetime import datetime
from pathlib import Path
```

**Path Aliases:**
- None configured
- Use `pathlib.Path` for all file operations

## Error Handling

**Patterns:**
- Early validation with clear error messages and exit codes
- Try/except blocks for external operations (file I/O, API calls)
- Specific exception types caught before general Exception

**Example from `execution/weather_lookup.py`:**
```python
# Early validation pattern
if not API_KEY:
    print("ERROR: WEATHER_API_KEY not set in .env")
    print()
    print("To fix:")
    print("1. Get a free API key at: https://openweathermap.org/api")
    print("2. Add to your .env file:")
    print("   WEATHER_API_KEY=your_key_here")
    return 1

# Specific exception handling
try:
    response = requests.get(API_URL, params=params, timeout=10)
    # HTTP error handling by status code
    if response.status_code == 401:
        print("ERROR: Invalid API key")
        return 1
    if response.status_code == 404:
        print(f"ERROR: City not found: {args.city}")
        return 1
    response.raise_for_status()
except requests.exceptions.Timeout:
    print("ERROR: Request timed out")
    return 1
except requests.exceptions.RequestException as e:
    print(f"ERROR: Request failed: {e}")
    return 1
except KeyError as e:
    print(f"ERROR: Unexpected API response (missing {e})")
    return 1
```

**Return Codes:**
- `return 0` for success
- `return 1` for errors
- `return 130` for keyboard interrupt (Ctrl+C)

## Logging

**Framework:** Console output (no logging framework)

**Patterns:**
- Use `print()` for all output
- Prefix with status indicators: `✅`, `❌`, `⚠️`, `📄`, `📜`, `📦`, `📍`, `✨`
- Section headers with separators: `print("=" * 60)`
- Error messages prefixed with "ERROR:" or "❌"

**Example:**
```python
print(f"✅ Synced: {', '.join(result['synced'])}")
print(f"❌ Error: {error}")
print("=" * 60)
print(f"DOE Cost Report | {filter_type.upper()}")
print("=" * 60)
```

## Comments

**When to Comment:**
- Section headers use comment blocks with `=` separators
- Docstrings at module and function level

**Docstring Pattern:**
```python
"""
Script: sync_agent_files.py
Directive: directives/agent_instructions_maintenance.md
DOE Framework: v2.0.0

Purpose:
    Keep AGENTS.md, CLAUDE.md, and GEMINI.md synchronized.

Cost:
    No API costs - local file operations only

Usage:
    python execution/sync_agent_files.py --check
"""

def get_file_content(filepath: Path) -> str | None:
    """Read file content, return None if file doesn't exist."""
```

**Section Comments:**
```python
# =============================================================================
# VERSION - Must match directive version
# =============================================================================
DOE_VERSION = "2025.12.19"

# =============================================================================
# CONFIGURATION
# =============================================================================
```

## Function Design

**Size:** Functions kept focused, typically 10-50 lines

**Parameters:**
- Use type hints for all parameters
- Optional parameters have defaults: `create_backups: bool = False`
- Required parameters first, optional last

**Return Values:**
- Functions return typed values with type hints
- Complex operations return dicts with status and details:
```python
def sync_files(create_backups: bool = False, source_file: str | None = None) -> dict:
    result = {
        "success": True,
        "source": None,
        "source_reason": None,
        "synced": [],
        "created": [],
        "backups": [],
        "errors": []
    }
    # ... operation ...
    return result
```

## Module Design

**Script Structure:**
Every script follows this pattern:
1. Shebang: `#!/usr/bin/env python3`
2. Module docstring with Purpose, Directive reference, Cost, Usage
3. Imports
4. VERSION constant (must match directive)
5. CONFIGURATION section
6. CORE FUNCTIONS section
7. MAIN section with `main()` function
8. Entry point: `if __name__ == "__main__": sys.exit(main())`

**Exports:**
- Scripts are standalone CLI tools, not importable modules
- No `__all__` exports defined

**Barrel Files:**
- Not used (flat execution directory structure)

## CLI Design

**Pattern:**
- Use `argparse` for all CLI scripts
- Subparsers for complex commands (see `doe_utils.py`)
- Include `--help` description and epilog with examples

**Example from `execution/sync_agent_files.py`:**
```python
parser = argparse.ArgumentParser(
    description="Sync and maintain agent instruction files.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=f"""
Examples:
    %(prog)s --check
    %(prog)s --sync
    %(prog)s --sync --source CLAUDE.md
"""
)
parser.add_argument("--check", "-c", action="store_true", help="Check if files are in sync")
parser.add_argument("--sync", "-s", action="store_true", help="Sync files")
```

## DOE Framework Patterns

**Version Matching:**
- Every directive has `<!-- DOE-VERSION: YYYY.MM.DD -->` in header
- Every script has `DOE_VERSION = "YYYY.MM.DD"` constant
- Versions MUST match between paired directive and script

**Directive-Script Pairing:**
- `directives/weather_lookup.md` ↔ `execution/weather_lookup.py`
- Script docstring references directive: `Directive: directives/weather_lookup.md`

**Environment Variables:**
- Load with `python-dotenv`: `load_dotenv()`
- Access with `os.getenv()`: `API_KEY = os.getenv("WEATHER_API_KEY")`
- Validate before use, provide helpful setup instructions on missing

**Cost Tracking:**
- Optional pattern in template:
```python
def log_cost(workflow: str, costs: dict):
    """Log API costs to .tmp/cost_log.jsonl"""
    log_path = Path(".tmp/cost_log.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "workflow": workflow,
        "costs": costs,
        "total": sum(costs.values())
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

---

*Convention analysis: 2026-01-29*
