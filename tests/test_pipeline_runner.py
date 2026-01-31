"""
Tests for pipeline_runner.py orchestrator.
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import argparse

import pytest

# Import the module under test
from execution.pipeline_runner import (
    PipelineResult,
    announce,
    call_with_retry,
    stage_content_aggregation,
    stage_newsletter_generation,
    stage_affiliate_discovery,
    get_next_issue_number,
    run_pipeline,
)
from execution.cost_tracker import CostTracker


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_cost_tracker():
    """Create a mock CostTracker."""
    tracker = CostTracker()
    return tracker


@pytest.fixture
def mock_args():
    """Create mock CLI arguments."""
    args = argparse.Namespace()
    args.topic = None
    args.include_stretch = False
    args.ps_type = "foreshadow"
    return args


@pytest.fixture
def sample_aggregation_result():
    """Create sample content aggregation result."""
    return {
        "success": True,
        "content_fetched": 25,
        "source_counts": {"reddit": 15, "youtube": 10},
        "high_outliers": 8,
        "json_path": "output/content_sheet.json",
    }


@pytest.fixture
def sample_content_data():
    """Create sample content JSON data."""
    return {
        "contents": [
            {
                "title": "TikTok Shop Strategies for Q1",
                "source": "reddit",
                "outlier_score": 5.2,
                "url": "https://reddit.com/r/shopify/example",
            },
            {
                "title": "Email Marketing Tactics",
                "source": "youtube",
                "outlier_score": 4.1,
                "url": "https://youtube.com/watch?v=abc123",
            },
        ]
    }


@pytest.fixture
def mock_newsletter_output():
    """Create mock NewsletterOutput."""
    mock_output = Mock()
    mock_output.issue_number = 5
    mock_output.subject_line = "dtc money minute #5: test subject"
    mock_output.preview_text = "Test preview text"
    mock_output.sections = {
        "section_1": "Section 1 content",
        "section_2": "Section 2 content",
        "section_3": "Section 3 content",
        "section_4": "Section 4 content",
        "section_5": "PS content",
    }
    mock_output.markdown = "# Newsletter\n\nContent here"
    mock_output.metadata = {"generation_time": 5.2}
    return mock_output


# =============================================================================
# TEST PIPELINE RESULT DATACLASS
# =============================================================================


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_pipeline_result_fields(self):
        """Test PipelineResult has all required fields."""
        result = PipelineResult(
            success=True,
            newsletter_path=Path("output/newsletters/001-test.md"),
            content_count=25,
            costs={"stage_1": 0.15, "stage_2": 0.35},
            total_cost=0.50,
            warnings=["warning 1"],
            errors=[],
        )

        assert result.success is True
        assert result.newsletter_path == Path("output/newsletters/001-test.md")
        assert result.content_count == 25
        assert result.costs == {"stage_1": 0.15, "stage_2": 0.35}
        assert result.total_cost == 0.50
        assert result.warnings == ["warning 1"]
        assert result.errors == []

    def test_pipeline_result_defaults(self):
        """Test PipelineResult default values."""
        result = PipelineResult(
            success=False,
            newsletter_path=None,
            content_count=0,
        )

        assert result.costs == {}
        assert result.total_cost == 0.0
        assert result.warnings == []
        assert result.errors == []


# =============================================================================
# TEST ANNOUNCE
# =============================================================================


class TestAnnounce:
    """Tests for announce function."""

    def test_announce_prints(self, capsys):
        """Test announce prints when not quiet."""
        announce("Test message", quiet=False)
        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_announce_quiet(self, capsys):
        """Test announce is silent in quiet mode."""
        announce("Test message", quiet=True)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_announce_default_not_quiet(self, capsys):
        """Test announce defaults to not quiet."""
        announce("Default message")
        captured = capsys.readouterr()
        assert "Default message" in captured.out


# =============================================================================
# TEST CALL WITH RETRY
# =============================================================================


class TestCallWithRetry:
    """Tests for call_with_retry function."""

    def test_call_with_retry_success(self):
        """Test successful call without retry."""
        mock_func = Mock(return_value="success")
        result = call_with_retry(mock_func, "arg1", kwarg1="value")

        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg1="value")

    def test_call_with_retry_passes_args(self):
        """Test call_with_retry passes all arguments."""
        mock_func = Mock(return_value=42)
        result = call_with_retry(mock_func, 1, 2, 3, a="x", b="y")

        assert result == 42
        mock_func.assert_called_once_with(1, 2, 3, a="x", b="y")

    def test_call_with_retry_returns_function_result(self):
        """Test call_with_retry returns function result."""

        def add(a, b):
            return a + b

        result = call_with_retry(add, 5, 3)
        assert result == 8


# =============================================================================
# TEST STAGE CONTENT AGGREGATION
# =============================================================================


class TestStageContentAggregation:
    """Tests for stage_content_aggregation function."""

    def test_stage_content_aggregation_success(
        self, mock_cost_tracker, mock_args, sample_aggregation_result, monkeypatch
    ):
        """Test successful content aggregation."""
        mock_run_agg = Mock(return_value=sample_aggregation_result)
        monkeypatch.setattr("execution.content_aggregate.run_aggregation", mock_run_agg)

        result = stage_content_aggregation(mock_args, mock_cost_tracker, quiet=True)

        assert result is not None
        assert result["content"] == sample_aggregation_result
        assert result["json_path"] == "output/content_sheet.json"
        assert mock_cost_tracker.get_stage_cost("content_aggregation") == 0.0

    def test_stage_content_aggregation_failure(
        self, mock_cost_tracker, mock_args, monkeypatch
    ):
        """Test content aggregation returns None on failure."""
        mock_run_agg = Mock(side_effect=Exception("API error"))
        monkeypatch.setattr("execution.content_aggregate.run_aggregation", mock_run_agg)

        result = stage_content_aggregation(mock_args, mock_cost_tracker, quiet=True)

        assert result is None
        # Cost should still be tracked (as 0)
        assert mock_cost_tracker.get_stage_cost("content_aggregation") == 0.0

    def test_stage_content_aggregation_empty_result(
        self, mock_cost_tracker, mock_args, monkeypatch
    ):
        """Test graceful handling of empty result."""
        mock_run_agg = Mock(return_value={"success": True, "content_fetched": 0})
        monkeypatch.setattr("execution.content_aggregate.run_aggregation", mock_run_agg)

        result = stage_content_aggregation(mock_args, mock_cost_tracker, quiet=True)

        assert result is None


# =============================================================================
# TEST STAGE NEWSLETTER GENERATION
# =============================================================================


class TestStageNewsletterGeneration:
    """Tests for stage_newsletter_generation function."""

    def test_stage_newsletter_generation_success(
        self,
        mock_cost_tracker,
        mock_args,
        sample_content_data,
        mock_newsletter_output,
        tmp_path,
        monkeypatch,
    ):
        """Test successful newsletter generation."""
        # Setup mocks
        mock_generate = Mock(return_value=mock_newsletter_output)
        monkeypatch.setattr(
            "execution.newsletter_generator.generate_newsletter", mock_generate
        )

        # Create temp JSON file
        json_path = tmp_path / "content.json"
        json_path.write_text(json.dumps(sample_content_data))

        content_result = {
            "content": {"content_fetched": 25},
            "topic": "test topic",
            "json_path": str(json_path),
        }

        result = stage_newsletter_generation(
            content_result, mock_args, mock_cost_tracker, quiet=True
        )

        assert result is not None
        assert result.issue_number == 5
        assert mock_cost_tracker.get_stage_cost("newsletter_generation") > 0

    def test_stage_newsletter_generation_no_content(self, mock_cost_tracker, mock_args):
        """Test newsletter generation skipped when no content."""
        result = stage_newsletter_generation(
            None, mock_args, mock_cost_tracker, quiet=True
        )
        assert result is None

    def test_stage_newsletter_generation_missing_json(
        self, mock_cost_tracker, mock_args, tmp_path
    ):
        """Test newsletter generation handles missing JSON file."""
        content_result = {
            "content": {"content_fetched": 10},
            "topic": "test",
            "json_path": str(tmp_path / "nonexistent.json"),
        }

        result = stage_newsletter_generation(
            content_result, mock_args, mock_cost_tracker, quiet=True
        )

        assert result is None

    def test_stage_newsletter_generation_failure(
        self, mock_cost_tracker, mock_args, sample_content_data, tmp_path, monkeypatch
    ):
        """Test newsletter generation returns None after failure."""
        mock_generate = Mock(side_effect=Exception("Generation failed"))
        monkeypatch.setattr(
            "execution.newsletter_generator.generate_newsletter", mock_generate
        )

        json_path = tmp_path / "content.json"
        json_path.write_text(json.dumps(sample_content_data))

        content_result = {
            "content": {"content_fetched": 10},
            "topic": "test",
            "json_path": str(json_path),
        }

        result = stage_newsletter_generation(
            content_result, mock_args, mock_cost_tracker, quiet=True
        )

        # Should return None after failure
        assert result is None


# =============================================================================
# TEST STAGE AFFILIATE DISCOVERY
# =============================================================================


class TestStageAffiliateDiscovery:
    """Tests for stage_affiliate_discovery function."""

    def test_stage_affiliate_discovery_success(self, mock_cost_tracker, monkeypatch):
        """Test successful affiliate discovery."""
        mock_discover = Mock(return_value="# Affiliate Report\n...")
        monkeypatch.setattr(
            "execution.affiliate_finder.run_monetization_discovery", mock_discover
        )

        result = stage_affiliate_discovery("test topic", mock_cost_tracker, quiet=True)

        assert result is not None
        assert "output" in result
        assert mock_cost_tracker.get_stage_cost("affiliate_discovery") > 0

    def test_stage_affiliate_discovery_optional(self, mock_cost_tracker, monkeypatch):
        """Test pipeline continues if affiliate discovery fails."""
        mock_discover = Mock(side_effect=Exception("Discovery failed"))
        monkeypatch.setattr(
            "execution.affiliate_finder.run_monetization_discovery", mock_discover
        )

        result = stage_affiliate_discovery("test topic", mock_cost_tracker, quiet=True)

        # Should return None but not raise
        assert result is None


# =============================================================================
# TEST GET NEXT ISSUE NUMBER
# =============================================================================


class TestGetNextIssueNumber:
    """Tests for get_next_issue_number function."""

    def test_get_next_issue_number_empty_dir(self, tmp_path):
        """Test returns 1 for empty directory."""
        result = get_next_issue_number(tmp_path)
        assert result == 1

    def test_get_next_issue_number_nonexistent_dir(self, tmp_path):
        """Test returns 1 for nonexistent directory."""
        nonexistent = tmp_path / "does_not_exist"
        result = get_next_issue_number(nonexistent)
        assert result == 1

    def test_get_next_issue_number_with_existing(self, tmp_path):
        """Test increments from highest existing issue."""
        # Create some newsletter files
        (tmp_path / "001-topic-one.md").write_text("content")
        (tmp_path / "002-topic-two.md").write_text("content")
        (tmp_path / "005-topic-five.md").write_text("content")

        result = get_next_issue_number(tmp_path)
        assert result == 6

    def test_get_next_issue_number_with_subfolders(self, tmp_path):
        """Test scans subfolders recursively."""
        subfolder = tmp_path / "2026-01"
        subfolder.mkdir()
        (subfolder / "003-january.md").write_text("content")

        result = get_next_issue_number(tmp_path)
        assert result == 4

    def test_get_next_issue_number_issue_pattern(self, tmp_path):
        """Test handles issue-N pattern."""
        (tmp_path / "2026-01-15-issue-7.md").write_text("content")

        result = get_next_issue_number(tmp_path)
        assert result == 8


# =============================================================================
# TEST RUN PIPELINE
# =============================================================================


class TestRunPipeline:
    """Tests for run_pipeline function."""

    def test_run_pipeline_full_success(self, monkeypatch, mock_newsletter_output):
        """Test full pipeline success."""
        # Setup mocks
        mock_content = Mock(
            return_value={
                "content": {"content_fetched": 25},
                "topic": "test topic",
                "json_path": "output/content.json",
            }
        )
        mock_newsletter = Mock(return_value=mock_newsletter_output)
        mock_save = Mock(return_value=Path("output/newsletters/001-test.md"))
        mock_affiliate = Mock(return_value={"output": "affiliates"})
        mock_log_cost = Mock()

        monkeypatch.setattr(
            "execution.pipeline_runner.stage_content_aggregation", mock_content
        )
        monkeypatch.setattr(
            "execution.pipeline_runner.stage_newsletter_generation", mock_newsletter
        )
        monkeypatch.setattr("execution.newsletter_generator.save_newsletter", mock_save)
        monkeypatch.setattr(
            "execution.pipeline_runner.stage_affiliate_discovery", mock_affiliate
        )
        monkeypatch.setattr("execution.pipeline_runner.log_run_cost", mock_log_cost)

        result = run_pipeline(quiet=True)

        assert result.success is True
        assert result.newsletter_path == Path("output/newsletters/001-test.md")
        assert result.content_count == 25
        mock_log_cost.assert_called_once()

    def test_run_pipeline_partial_failure(self, monkeypatch):
        """Test pipeline fails gracefully when content aggregation fails."""
        # Content aggregation fails
        mock_content = Mock(return_value=None)
        mock_log_cost = Mock()

        monkeypatch.setattr(
            "execution.pipeline_runner.stage_content_aggregation", mock_content
        )
        monkeypatch.setattr("execution.pipeline_runner.log_run_cost", mock_log_cost)

        result = run_pipeline(quiet=True)

        # Pipeline should fail if no content
        assert result.success is False
        assert "Content aggregation failed" in result.errors[0]

    def test_run_pipeline_affiliate_failure_continues(
        self, monkeypatch, mock_newsletter_output
    ):
        """Test pipeline continues if affiliate discovery fails."""
        mock_content = Mock(
            return_value={
                "content": {"content_fetched": 10},
                "topic": "test",
                "json_path": "test.json",
            }
        )
        mock_newsletter = Mock(return_value=mock_newsletter_output)
        mock_save = Mock(return_value=Path("output/001-test.md"))
        mock_affiliate = Mock(return_value=None)  # Affiliate fails
        mock_log_cost = Mock()

        monkeypatch.setattr(
            "execution.pipeline_runner.stage_content_aggregation", mock_content
        )
        monkeypatch.setattr(
            "execution.pipeline_runner.stage_newsletter_generation", mock_newsletter
        )
        monkeypatch.setattr("execution.newsletter_generator.save_newsletter", mock_save)
        monkeypatch.setattr(
            "execution.pipeline_runner.stage_affiliate_discovery", mock_affiliate
        )
        monkeypatch.setattr("execution.pipeline_runner.log_run_cost", mock_log_cost)

        result = run_pipeline(quiet=True)

        # Pipeline should still succeed
        assert result.success is True
        assert "Affiliate discovery failed" in result.warnings[0]

    def test_run_pipeline_total_failure(self, monkeypatch):
        """Test pipeline failure when all content sources fail."""
        mock_content = Mock(return_value=None)
        mock_log_cost = Mock()

        monkeypatch.setattr(
            "execution.pipeline_runner.stage_content_aggregation", mock_content
        )
        monkeypatch.setattr("execution.pipeline_runner.log_run_cost", mock_log_cost)

        result = run_pipeline(quiet=True)

        assert result.success is False
        assert len(result.errors) > 0


# =============================================================================
# TEST CLI
# =============================================================================


class TestCLI:
    """Tests for CLI interface."""

    def test_cli_help(self):
        """Test CLI --help exits successfully."""
        result = subprocess.run(
            [sys.executable, "execution/pipeline_runner.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "Run the full DTC newsletter pipeline" in result.stdout
        assert "--quiet" in result.stdout
        assert "--verbose" in result.stdout
        assert "--topic" in result.stdout
        assert "--skip-affiliates" in result.stdout
        assert "--dry-run" in result.stdout

    def test_cli_dry_run(self):
        """Test --dry-run shows stages without executing."""
        result = subprocess.run(
            [sys.executable, "execution/pipeline_runner.py", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "DRY RUN" in result.stdout
        assert "Content Aggregation" in result.stdout
        assert "Newsletter Generation" in result.stdout
        assert "Affiliate Discovery" in result.stdout


# =============================================================================
# TEST INTEGRATION
# =============================================================================


class TestIntegration:
    """Integration tests for pipeline components."""

    def test_pipeline_result_serializable(self):
        """Test PipelineResult can be converted to dict."""
        result = PipelineResult(
            success=True,
            newsletter_path=Path("test.md"),
            content_count=10,
            costs={"stage_1": 0.1},
            total_cost=0.1,
            warnings=[],
            errors=[],
        )

        # Should be able to access all fields
        assert result.success == True
        assert str(result.newsletter_path) == "test.md"

    def test_cost_tracker_integration(self):
        """Test CostTracker integrates properly with stages."""
        tracker = CostTracker()

        # Simulate adding costs from multiple stages
        tracker.add_cost("content_aggregation", 0.0)
        tracker.add_cost("newsletter_generation", 0.15)
        tracker.add_cost("affiliate_discovery", 0.05)

        assert tracker.get_total() == 0.20
        assert tracker.get_stage_cost("newsletter_generation") == 0.15

        # Export to dict
        data = tracker.to_dict()
        assert "run_id" in data
        assert "costs" in data
        assert data["total"] == 0.20
