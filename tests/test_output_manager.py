"""
Tests for execution/output_manager.py

Tests cover:
- slugify: basic, special chars, empty
- get_next_issue_number: empty dir, existing files
- get_monthly_folder: creates folder
- save_newsletter: full workflow
- update_index: new and append
- notify: macOS and non-macOS
- notify_pipeline_complete: success and failure
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_newsletters_dir(tmp_path: Path):
    """Create a temporary newsletters directory."""
    newsletters_dir = tmp_path / "output" / "newsletters"
    newsletters_dir.mkdir(parents=True)
    return newsletters_dir


@pytest.fixture
def mock_newsletter_output():
    """Create a mock NewsletterOutput object."""

    @dataclass
    class MockNewsletterOutput:
        issue_number: int = 1
        subject_line: str = "DTC Money Minute #1: test topic"
        preview_text: str = "Test preview text"
        sections: dict = field(default_factory=dict)
        markdown: str = "# Test Newsletter\n\nContent here."
        metadata: dict = field(default_factory=dict)

    return MockNewsletterOutput()


@pytest.fixture
def mock_pipeline_result_success():
    """Create a mock successful PipelineResult."""

    @dataclass
    class MockPipelineResult:
        success: bool = True
        newsletter_path: Optional[Path] = None
        content_count: int = 10
        costs: dict = field(default_factory=dict)
        total_cost: float = 0.05
        warnings: list = field(default_factory=list)
        errors: list = field(default_factory=list)

    result = MockPipelineResult()
    result.newsletter_path = Path("output/newsletters/2026-01/001-test.md")
    return result


@pytest.fixture
def mock_pipeline_result_failure():
    """Create a mock failed PipelineResult."""

    @dataclass
    class MockPipelineResult:
        success: bool = False
        newsletter_path: Optional[Path] = None
        content_count: int = 0
        costs: dict = field(default_factory=dict)
        total_cost: float = 0.0
        warnings: list = field(default_factory=list)
        errors: list = field(default_factory=list)

    result = MockPipelineResult()
    result.errors = ["Content aggregation failed - no content available"]
    return result


# =============================================================================
# SLUGIFY TESTS
# =============================================================================


class TestSlugify:
    """Tests for slugify function."""

    def test_slugify_basic(self):
        """Test basic slugification."""
        from execution.output_manager import slugify

        result = slugify("TikTok Shop Strategies")
        assert result == "tiktok-shop-strategies"

    def test_slugify_special_chars(self):
        """Test slugification with special characters."""
        from execution.output_manager import slugify

        result = slugify("What's Working: 2026!")
        assert result == "what-s-working-2026"

    def test_slugify_empty(self):
        """Test slugification of empty string."""
        from execution.output_manager import slugify

        result = slugify("")
        assert result == "newsletter"

    def test_slugify_whitespace_only(self):
        """Test slugification of whitespace-only string."""
        from execution.output_manager import slugify

        result = slugify("   ")
        assert result == "newsletter"

    def test_slugify_numbers(self):
        """Test slugification with numbers."""
        from execution.output_manager import slugify

        result = slugify("Top 10 Tips for 2026")
        assert result == "top-10-tips-for-2026"

    def test_slugify_leading_trailing_special(self):
        """Test that leading/trailing special chars are stripped."""
        from execution.output_manager import slugify

        result = slugify("---hello world---")
        assert result == "hello-world"


# =============================================================================
# GET_NEXT_ISSUE_NUMBER TESTS
# =============================================================================


class TestGetNextIssueNumber:
    """Tests for get_next_issue_number function."""

    def test_get_next_issue_number_empty(self, tmp_path: Path, monkeypatch):
        """Test with no existing newsletters returns 1."""
        from execution import output_manager

        # Point NEWSLETTERS_DIR to our temp dir
        monkeypatch.setattr(output_manager, "NEWSLETTERS_DIR", tmp_path)

        result = output_manager.get_next_issue_number()
        assert result == 1

    def test_get_next_issue_number_nonexistent_dir(self, tmp_path: Path, monkeypatch):
        """Test with nonexistent directory returns 1."""
        from execution import output_manager

        nonexistent = tmp_path / "nonexistent"
        monkeypatch.setattr(output_manager, "NEWSLETTERS_DIR", nonexistent)

        result = output_manager.get_next_issue_number()
        assert result == 1

    def test_get_next_issue_number_existing(self, tmp_path: Path, monkeypatch):
        """Test with existing newsletters returns max + 1."""
        from execution import output_manager

        monkeypatch.setattr(output_manager, "NEWSLETTERS_DIR", tmp_path)

        # Create some test files
        (tmp_path / "001-test.md").write_text("test")
        (tmp_path / "002-another.md").write_text("test")
        (tmp_path / "005-skipped.md").write_text("test")

        result = output_manager.get_next_issue_number()
        assert result == 6

    def test_get_next_issue_number_subfolders(self, tmp_path: Path, monkeypatch):
        """Test scans subfolders for issues."""
        from execution import output_manager

        monkeypatch.setattr(output_manager, "NEWSLETTERS_DIR", tmp_path)

        # Create files in subfolders
        (tmp_path / "2026-01").mkdir()
        (tmp_path / "2026-01" / "003-jan.md").write_text("test")
        (tmp_path / "2026-02").mkdir()
        (tmp_path / "2026-02" / "010-feb.md").write_text("test")

        result = output_manager.get_next_issue_number()
        assert result == 11


# =============================================================================
# GET_MONTHLY_FOLDER TESTS
# =============================================================================


class TestGetMonthlyFolder:
    """Tests for get_monthly_folder function."""

    def test_get_monthly_folder(self, tmp_path: Path, monkeypatch):
        """Test creates YYYY-MM folder."""
        from execution import output_manager

        monkeypatch.setattr(output_manager, "NEWSLETTERS_DIR", tmp_path)

        folder = output_manager.get_monthly_folder()

        # Should be current month
        expected_name = datetime.now().strftime("%Y-%m")
        assert folder.name == expected_name
        assert folder.exists()

    def test_get_monthly_folder_already_exists(self, tmp_path: Path, monkeypatch):
        """Test doesn't fail if folder already exists."""
        from execution import output_manager

        monkeypatch.setattr(output_manager, "NEWSLETTERS_DIR", tmp_path)

        # Pre-create the folder
        month_str = datetime.now().strftime("%Y-%m")
        (tmp_path / month_str).mkdir()

        folder = output_manager.get_monthly_folder()
        assert folder.exists()


# =============================================================================
# SAVE_NEWSLETTER TESTS
# =============================================================================


class TestSaveNewsletter:
    """Tests for save_newsletter function."""

    def test_save_newsletter(self, tmp_path: Path, mock_newsletter_output, monkeypatch):
        """Test full save workflow."""
        from execution import output_manager

        newsletters_dir = tmp_path / "newsletters"
        monkeypatch.setattr(output_manager, "NEWSLETTERS_DIR", newsletters_dir)
        monkeypatch.setattr(
            output_manager, "INDEX_PATH", newsletters_dir / "index.json"
        )

        path = output_manager.save_newsletter(
            mock_newsletter_output, topic="Test Topic"
        )

        # Verify file created
        assert path.exists()
        assert path.name == "001-test-topic.md"
        assert "Test Newsletter" in path.read_text()

        # Verify index.json updated
        index_path = newsletters_dir / "index.json"
        assert index_path.exists()
        index = json.loads(index_path.read_text())
        assert len(index["newsletters"]) == 1
        assert index["newsletters"][0]["issue"] == 1
        assert index["newsletters"][0]["topic"] == "Test Topic"

    def test_save_newsletter_uses_subject_for_slug(
        self, tmp_path: Path, mock_newsletter_output, monkeypatch
    ):
        """Test uses subject line for slug if no topic provided."""
        from execution import output_manager

        newsletters_dir = tmp_path / "newsletters"
        monkeypatch.setattr(output_manager, "NEWSLETTERS_DIR", newsletters_dir)
        monkeypatch.setattr(
            output_manager, "INDEX_PATH", newsletters_dir / "index.json"
        )

        mock_newsletter_output.subject_line = "DTC Money Minute #1: Email Marketing"

        path = output_manager.save_newsletter(mock_newsletter_output)

        # Should use subject line for slug
        assert "email" in path.name.lower() or "marketing" in path.name.lower()


# =============================================================================
# UPDATE_INDEX TESTS
# =============================================================================


class TestUpdateIndex:
    """Tests for update_index function."""

    def test_update_index_new(self, tmp_path: Path, monkeypatch):
        """Test creates index.json if not exists."""
        from execution import output_manager

        monkeypatch.setattr(output_manager, "NEWSLETTERS_DIR", tmp_path)
        monkeypatch.setattr(output_manager, "INDEX_PATH", tmp_path / "index.json")

        entry = {
            "issue": 1,
            "topic": "Test",
            "date": "2026-01-31",
            "path": "2026-01/001-test.md",
            "subject_line": "Subject",
        }

        output_manager.update_index(entry)

        index_path = tmp_path / "index.json"
        assert index_path.exists()
        index = json.loads(index_path.read_text())
        assert len(index["newsletters"]) == 1

    def test_update_index_append(self, tmp_path: Path, monkeypatch):
        """Test appends to existing index."""
        from execution import output_manager

        monkeypatch.setattr(output_manager, "NEWSLETTERS_DIR", tmp_path)
        index_path = tmp_path / "index.json"
        monkeypatch.setattr(output_manager, "INDEX_PATH", index_path)

        # Create existing index
        existing = {"newsletters": [{"issue": 1, "topic": "First"}]}
        index_path.write_text(json.dumps(existing))

        entry = {
            "issue": 2,
            "topic": "Second",
            "date": "2026-01-31",
            "path": "2026-01/002-second.md",
            "subject_line": "Subject 2",
        }

        output_manager.update_index(entry)

        index = json.loads(index_path.read_text())
        assert len(index["newsletters"]) == 2
        assert index["newsletters"][1]["issue"] == 2


# =============================================================================
# NOTIFY TESTS
# =============================================================================


class TestNotify:
    """Tests for notify function."""

    def test_notify_macos(self, monkeypatch):
        """Test calls osascript on macOS."""
        from execution import output_manager

        # Mock platform as macOS
        monkeypatch.setattr(sys, "platform", "darwin")

        # Mock subprocess.run
        mock_run = MagicMock()
        monkeypatch.setattr(subprocess, "run", mock_run)

        output_manager.notify("Test Title", "Test message")

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "osascript"
        assert "Test Title" in call_args[0][0][2]

    def test_notify_non_macos(self, monkeypatch):
        """Test no-op on non-macOS."""
        from execution import output_manager

        # Mock platform as Linux
        monkeypatch.setattr(sys, "platform", "linux")

        # Mock subprocess.run - should NOT be called
        mock_run = MagicMock()
        monkeypatch.setattr(subprocess, "run", mock_run)

        output_manager.notify("Test Title", "Test message")

        mock_run.assert_not_called()

    def test_notify_handles_failure(self, monkeypatch):
        """Test gracefully handles osascript failure."""
        from execution import output_manager

        monkeypatch.setattr(sys, "platform", "darwin")

        # Mock subprocess.run to raise
        def raise_error(*args, **kwargs):
            raise FileNotFoundError("osascript not found")

        monkeypatch.setattr(subprocess, "run", raise_error)

        # Should not raise
        output_manager.notify("Test", "Test")


# =============================================================================
# NOTIFY_PIPELINE_COMPLETE TESTS
# =============================================================================


class TestNotifyPipelineComplete:
    """Tests for notify_pipeline_complete function."""

    def test_notify_pipeline_complete_success(
        self, mock_pipeline_result_success, monkeypatch
    ):
        """Test success notification has correct message."""
        from execution import output_manager

        monkeypatch.setattr(sys, "platform", "darwin")
        mock_run = MagicMock()
        monkeypatch.setattr(subprocess, "run", mock_run)

        output_manager.notify_pipeline_complete(mock_pipeline_result_success)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0][2]
        assert "Complete" in call_args
        assert "$" in call_args  # Cost should be in message

    def test_notify_pipeline_complete_failure(
        self, mock_pipeline_result_failure, monkeypatch
    ):
        """Test failure notification has error message."""
        from execution import output_manager

        monkeypatch.setattr(sys, "platform", "darwin")
        mock_run = MagicMock()
        monkeypatch.setattr(subprocess, "run", mock_run)

        output_manager.notify_pipeline_complete(mock_pipeline_result_failure)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0][2]
        assert "Failed" in call_args
