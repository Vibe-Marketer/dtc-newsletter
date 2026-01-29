# Testing Patterns

**Analysis Date:** 2026-01-29

## Test Framework

**Runner:**
- No test framework detected
- No test configuration files (jest.config.*, vitest.config.*, pytest.ini, conftest.py)

**Assertion Library:**
- Not configured

**Run Commands:**
```bash
# No test commands available - testing not implemented
```

## Test File Organization

**Location:**
- No test files found (`*.test.*`, `*.spec.*`, `test_*.py`, `*_test.py`)

**Naming:**
- Not established

**Structure:**
- Not established

## Current Testing State

**Status:** No automated testing infrastructure exists.

**What's testable:**
- `execution/sync_agent_files.py` - File sync operations, learning additions
- `execution/csv_to_json.py` - CSV parsing and JSON output
- `execution/weather_lookup.py` - API integration (requires mocking)
- `execution/doe_utils.py` - Cost tracking, version checking, directive listing

## Recommended Test Setup

Based on the codebase patterns, pytest would be the natural choice for this Python project.

**Suggested Installation:**
```bash
pip install pytest pytest-cov
```

**Suggested Configuration (`pytest.ini`):**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

**Suggested Structure:**
```
tests/
├── test_sync_agent_files.py
├── test_csv_to_json.py
├── test_weather_lookup.py
├── test_doe_utils.py
└── conftest.py
```

## Test Patterns to Implement

**Unit Test Pattern:**
```python
# tests/test_csv_to_json.py
import pytest
from pathlib import Path
import json
import tempfile

def test_csv_converts_to_json():
    """Test basic CSV to JSON conversion."""
    csv_content = "name,age\nAlice,30\nBob,25"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_path = f.name
    
    # Import the function or run as subprocess
    # Assert output matches expected JSON
```

**Mocking Pattern:**
```python
# tests/test_weather_lookup.py
import pytest
from unittest.mock import patch, Mock

def test_weather_lookup_success():
    """Test successful weather API call."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "San Francisco",
        "sys": {"country": "US"},
        "main": {"temp": 15.5},
        "weather": [{"description": "clear sky"}]
    }
    
    with patch('requests.get', return_value=mock_response):
        # Run weather lookup
        # Assert output contains expected data
        pass

def test_weather_lookup_missing_api_key():
    """Test error when API key is not set."""
    with patch.dict('os.environ', {}, clear=True):
        # Run weather lookup
        # Assert exit code 1 and helpful message
        pass
```

**Fixture Pattern:**
```python
# tests/conftest.py
import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def temp_project():
    """Create a temporary project directory with agent files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)
        
        # Create agent files
        content = "# Test Agent Instructions\n<!-- DOE-VERSION: 2025.12.19 -->\n"
        (project / "AGENTS.md").write_text(content)
        (project / "CLAUDE.md").write_text(content)
        (project / "GEMINI.md").write_text(content)
        
        # Create directories
        (project / "directives").mkdir()
        (project / "execution").mkdir()
        (project / ".tmp").mkdir()
        
        yield project

@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("name,email,age\nAlice,alice@example.com,30\nBob,bob@example.com,25\n")
    return csv_file
```

## What to Mock

**External APIs:**
- OpenWeatherMap API in `weather_lookup.py`
- Any future external service integrations

**File System (when appropriate):**
- When testing error conditions
- When testing path validation

**Environment Variables:**
- API keys for testing missing/invalid key scenarios
- Use `patch.dict('os.environ', {...})`

## What NOT to Mock

**File Operations (usually):**
- Use `tempfile` and real file operations for most tests
- The sync scripts work with actual files, test with real temp files

**Internal Functions:**
- Test the actual implementation, not mocked versions
- Only mock at boundaries (external APIs, environment)

## Test Categories

**Unit Tests (to implement):**
- `sync_agent_files.py`:
  - `test_get_file_content_exists` - File exists returns content
  - `test_get_file_content_missing` - File missing returns None
  - `test_detect_source_file_different_content` - Most recent file detected
  - `test_detect_source_file_identical_content` - Default source used
  - `test_sync_files_creates_missing` - Missing files created
  - `test_add_learning_appends` - Learning added to Remember section
- `csv_to_json.py`:
  - `test_basic_conversion` - Simple CSV converts correctly
  - `test_empty_csv` - Empty CSV returns empty array
  - `test_missing_file` - Nonexistent file returns error
  - `test_output_to_file` - --output flag writes to file
- `doe_utils.py`:
  - `test_cost_report_empty` - No data shows message
  - `test_cost_report_today_filter` - Today filter works
  - `test_version_check_aligned` - Matching versions detected
  - `test_version_check_mismatch` - Mismatched versions flagged

**Integration Tests (to implement):**
- End-to-end workflow execution
- Directive + script version alignment validation

**E2E Tests:**
- Not applicable for CLI tools (manual testing sufficient)

## Coverage

**Requirements:** None enforced

**Recommended Target:** 80% for critical paths

**View Coverage (when implemented):**
```bash
pytest --cov=execution --cov-report=html
```

## CLI Testing Pattern

Scripts are CLI tools, test via subprocess:

```python
import subprocess
import sys

def test_csv_to_json_cli():
    """Test CLI invocation."""
    result = subprocess.run(
        [sys.executable, "execution/csv_to_json.py", "data/sample.csv"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    # Parse stdout as JSON
    import json
    data = json.loads(result.stdout)
    assert isinstance(data, list)

def test_sync_check_cli():
    """Test sync check command."""
    result = subprocess.run(
        [sys.executable, "execution/sync_agent_files.py", "--check"],
        capture_output=True,
        text=True
    )
    # Exit code 0 = in sync, 1 = out of sync
    assert result.returncode in [0, 1]
```

## Priority Testing Needs

**High Priority:**
1. `sync_agent_files.py` - Core framework functionality
2. `csv_to_json.py` - Data transformation correctness

**Medium Priority:**
3. `doe_utils.py` - Cost tracking and version checking

**Low Priority:**
4. `weather_lookup.py` - Example workflow, external API dependent

---

*Testing analysis: 2026-01-29*
