# Technology Stack

**Analysis Date:** 2026-01-29

## Languages

**Primary:**
- Python 3.12 - All execution scripts, utilities, and automation

**Secondary:**
- Markdown - Directives, documentation, agent instructions

## Runtime

**Environment:**
- Python 3.12.11
- macOS darwin platform

**Package Manager:**
- pip
- Lockfile: Not present (only requirements.txt)

## Frameworks

**Core:**
- python-dotenv >= 1.0.0 - Environment variable management from `.env` files
- requests >= 2.31.0 - HTTP client for external API calls

**Testing:**
- Not detected - No test framework configured

**Build/Dev:**
- No build tools - Pure Python scripts with direct execution

## Key Dependencies

**Critical:**
- `python-dotenv` - Loads API keys and configuration from `.env` file
- `requests` - Required for any HTTP-based API integrations

**Standard Library Usage:**
- `argparse` - CLI argument parsing in all scripts
- `pathlib` - File path operations
- `json` - Data serialization (cost logging, CSV conversion)
- `csv` - CSV file parsing
- `re` - Regex for version extraction and pattern matching
- `datetime` - Timestamps and date handling
- `shutil` - File operations (backups)
- `difflib` - File comparison in sync utility
- `hashlib` - MD5 hashing for sync detection
- `collections.defaultdict` - Cost aggregation

## Configuration

**Environment:**
- Configuration via `.env` file (copy from `.env.example`)
- Key patterns:
  - `ANTHROPIC_API_KEY` - Primary AI/LLM API
  - `OPENAI_API_KEY` - Alternative AI/LLM API
  - `WEATHER_API_KEY` - OpenWeatherMap integration
  - `DOE_COST_TRACKING` - Enable cost logging
  - `DOE_COST_ALERT_THRESHOLD` - Cost warning threshold

**Build:**
- No build configuration - Scripts run directly with Python interpreter
- `requirements.txt` - Dependency specification

## Platform Requirements

**Development:**
- Python 3.12+ recommended
- pip for dependency installation
- `.env` file with required API keys

**Production:**
- Same as development (CLI-based tool)
- No deployment target - Local execution only

## Version Management

**DOE Framework Versioning:**
- Directives: `<!-- DOE-VERSION: YYYY.MM.DD -->` in markdown header
- Scripts: `DOE_VERSION = "YYYY.MM.DD"` constant
- Version alignment enforced between paired directive/script files

**Current Versions:**
- `agent_instructions_maintenance`: 2025.12.19
- `weather_lookup`: 2026.01.23
- `csv_to_json`: 2026.01.23

---

*Stack analysis: 2026-01-29*
