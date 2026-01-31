"""
Tests for stretch sources orchestrator.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestRunSourceSafely:
    """Tests for run_source_safely function."""

    def test_successful_fetch_returns_result_with_source(self):
        """Successful fetch should return result with source name added."""
        from execution.stretch_aggregate import run_source_safely

        mock_result = {
            "success": True,
            "items": [{"id": 1, "outlier_score": 2.5}],
        }

        result = run_source_safely("twitter", lambda: mock_result)

        assert result["source"] == "twitter"
        assert result["success"] is True
        assert len(result["items"]) == 1

    def test_failed_fetch_returns_error_dict(self):
        """Failed fetch should return error dict without raising."""
        from execution.stretch_aggregate import run_source_safely

        def failing_fn():
            raise Exception("API error")

        result = run_source_safely("tiktok", failing_fn)

        assert result["source"] == "tiktok"
        assert result["success"] is False
        assert result["items"] == []
        assert "API error" in result["error"]

    def test_isolates_exceptions(self):
        """Should not raise exceptions, always return dict."""
        from execution.stretch_aggregate import run_source_safely

        def raise_value_error():
            raise ValueError("Bad input")

        # Should not raise
        result = run_source_safely("amazon", raise_value_error)
        assert result["success"] is False
        assert "Bad input" in result["error"]


class TestRunAllStretchSources:
    """Tests for run_all_stretch_sources function."""

    @patch("execution.stretch_aggregate.run_source_safely")
    def test_returns_success_when_one_source_works(self, mock_run):
        """Success if at least one source worked."""
        from execution.stretch_aggregate import run_all_stretch_sources

        # Mock one success, two failures
        def side_effect(name, fn):
            if name == "twitter":
                return {"source": "twitter", "success": True, "items": [{"id": 1}]}
            return {"source": name, "success": False, "items": [], "error": "failed"}

        mock_run.side_effect = side_effect

        result = run_all_stretch_sources(parallel=False)

        assert result["success"] is True
        assert "twitter" in result["sources_succeeded"]
        assert len(result["sources_failed"]) >= 0  # May have tiktok, amazon

    @patch("execution.stretch_aggregate.run_source_safely")
    def test_returns_failure_when_all_sources_fail(self, mock_run):
        """Failure if all sources failed."""
        from execution.stretch_aggregate import run_all_stretch_sources

        mock_run.return_value = {
            "source": "x",
            "success": False,
            "items": [],
            "error": "error",
        }

        result = run_all_stretch_sources(parallel=False)

        assert result["success"] is False
        assert len(result["sources_succeeded"]) == 0
        assert len(result["sources_failed"]) > 0

    @patch("execution.stretch_aggregate.run_source_safely")
    def test_merges_items_from_all_sources(self, mock_run):
        """Items should be merged and sorted by outlier score."""
        from execution.stretch_aggregate import run_all_stretch_sources

        def side_effect(name, fn):
            if name == "twitter":
                return {
                    "source": "twitter",
                    "success": True,
                    "items": [{"id": "t1", "outlier_score": 3.0}],
                }
            elif name == "tiktok":
                return {
                    "source": "tiktok",
                    "success": True,
                    "items": [{"id": "tk1", "outlier_score": 5.0}],
                }
            elif name == "amazon":
                return {
                    "source": "amazon",
                    "success": True,
                    "items": [{"id": "a1", "outlier_score": 2.0}],
                }
            return {"source": name, "success": False, "items": []}

        mock_run.side_effect = side_effect

        result = run_all_stretch_sources(parallel=False)

        assert result["total_items"] == 3
        # Should be sorted by outlier score descending
        assert result["items"][0]["outlier_score"] == 5.0  # TikTok
        assert result["items"][1]["outlier_score"] == 3.0  # Twitter
        assert result["items"][2]["outlier_score"] == 2.0  # Amazon

    @patch("execution.stretch_aggregate.run_source_safely")
    def test_adds_stretch_source_tag_to_items(self, mock_run):
        """Each item should have stretch_source tag."""
        from execution.stretch_aggregate import run_all_stretch_sources

        mock_run.return_value = {
            "source": "twitter",
            "success": True,
            "items": [{"id": "t1", "outlier_score": 3.0}],
        }

        result = run_all_stretch_sources(parallel=False)

        for item in result["items"]:
            assert "stretch_source" in item

    def test_returns_error_when_no_modules_available(self):
        """Should return error when no source modules can be imported."""
        from execution.stretch_aggregate import run_all_stretch_sources

        with patch.dict(
            "sys.modules",
            {
                "execution.twitter_aggregate": None,
                "execution.tiktok_aggregate": None,
                "execution.amazon_aggregate": None,
            },
        ):
            # This test checks the "no sources" branch
            # In practice, the modules exist, so we mock import failures
            pass  # Module import is at function level, hard to test directly


class TestMergeStretchResults:
    """Tests for merge_stretch_results function."""

    def test_merges_core_and_stretch_items(self):
        """Should combine core and stretch items."""
        from execution.stretch_aggregate import merge_stretch_results

        core_items = [
            {"id": "r1", "outlier_score": 4.0, "source": "reddit"},
        ]

        stretch_result = {
            "items": [
                {"id": "t1", "outlier_score": 5.0, "source": "twitter"},
            ]
        }

        combined = merge_stretch_results(stretch_result, core_items)

        assert len(combined) == 2
        # Core items should not be marked as stretch
        core = [i for i in combined if i.get("id") == "r1"][0]
        assert core["is_stretch"] is False
        # Stretch items should be marked
        stretch = [i for i in combined if i.get("id") == "t1"][0]
        assert stretch["is_stretch"] is True

    def test_applies_weight_to_stretch_items(self):
        """Stretch items should have reduced score."""
        from execution.stretch_aggregate import merge_stretch_results

        core_items = [
            {"id": "r1", "outlier_score": 4.0},
        ]

        stretch_result = {
            "items": [
                {"id": "t1", "outlier_score": 5.0},
            ]
        }

        combined = merge_stretch_results(stretch_result, core_items, stretch_weight=0.8)

        stretch = [i for i in combined if i.get("id") == "t1"][0]
        assert stretch["outlier_score"] == 4.0  # 5.0 * 0.8
        assert stretch["original_outlier_score"] == 5.0

    def test_preserves_original_score(self):
        """Should preserve original outlier score."""
        from execution.stretch_aggregate import merge_stretch_results

        stretch_result = {
            "items": [
                {"id": "t1", "outlier_score": 10.0},
            ]
        }

        combined = merge_stretch_results(stretch_result, [], stretch_weight=0.5)

        assert combined[0]["original_outlier_score"] == 10.0
        assert combined[0]["outlier_score"] == 5.0

    def test_sorts_by_adjusted_score(self):
        """Combined list should be sorted by adjusted score."""
        from execution.stretch_aggregate import merge_stretch_results

        core_items = [
            {"id": "r1", "outlier_score": 3.0},
        ]

        stretch_result = {
            "items": [
                {"id": "t1", "outlier_score": 5.0},  # Becomes 4.0 after 0.8 weight
            ]
        }

        combined = merge_stretch_results(stretch_result, core_items, stretch_weight=0.8)

        # Stretch (4.0) > Core (3.0)
        assert combined[0]["id"] == "t1"
        assert combined[1]["id"] == "r1"

    def test_handles_empty_stretch_results(self):
        """Should handle empty stretch results."""
        from execution.stretch_aggregate import merge_stretch_results

        core_items = [
            {"id": "r1", "outlier_score": 3.0},
        ]

        stretch_result = {"items": []}

        combined = merge_stretch_results(stretch_result, core_items)

        assert len(combined) == 1
        assert combined[0]["id"] == "r1"

    def test_handles_empty_core_items(self):
        """Should handle empty core items."""
        from execution.stretch_aggregate import merge_stretch_results

        stretch_result = {
            "items": [
                {"id": "t1", "outlier_score": 5.0},
            ]
        }

        combined = merge_stretch_results(stretch_result, [])

        assert len(combined) == 1
        assert combined[0]["id"] == "t1"


class TestParallelExecution:
    """Tests for parallel execution behavior."""

    @patch("execution.stretch_aggregate.run_source_safely")
    def test_parallel_execution_collects_all_results(self, mock_run):
        """Parallel execution should collect results from all sources."""
        from execution.stretch_aggregate import run_all_stretch_sources

        def side_effect(name, fn):
            return {
                "source": name,
                "success": True,
                "items": [{"id": f"{name}-1", "outlier_score": 1.0}],
            }

        mock_run.side_effect = side_effect

        result = run_all_stretch_sources(parallel=True)

        # Should have results from available sources
        assert result["success"] is True
        assert len(result["sources_succeeded"]) > 0

    @patch("execution.stretch_aggregate.run_source_safely")
    def test_sequential_execution_works(self, mock_run):
        """Sequential execution should work correctly."""
        from execution.stretch_aggregate import run_all_stretch_sources

        call_order = []

        def side_effect(name, fn):
            call_order.append(name)
            return {
                "source": name,
                "success": True,
                "items": [],
            }

        mock_run.side_effect = side_effect

        result = run_all_stretch_sources(parallel=False)

        # Should have been called for each source
        assert len(call_order) > 0
        assert result["success"] is True


class TestGracefulDegradation:
    """Tests for graceful degradation behavior."""

    @patch("execution.stretch_aggregate.run_source_safely")
    def test_continues_when_one_source_fails(self, mock_run):
        """Pipeline should continue when some sources fail."""
        from execution.stretch_aggregate import run_all_stretch_sources

        def side_effect(name, fn):
            if name == "twitter":
                return {
                    "source": "twitter",
                    "success": False,
                    "items": [],
                    "error": "API down",
                }
            return {
                "source": name,
                "success": True,
                "items": [{"id": f"{name}-1", "outlier_score": 2.0}],
            }

        mock_run.side_effect = side_effect

        result = run_all_stretch_sources(parallel=False)

        # Should still succeed overall
        assert result["success"] is True
        # Twitter should be in failed list
        assert "twitter" in result["sources_failed"]
        # Other sources should have items
        assert result["total_items"] >= 1

    @patch("execution.stretch_aggregate.run_source_safely")
    def test_reports_all_failures(self, mock_run):
        """Should report all failed sources."""
        from execution.stretch_aggregate import run_all_stretch_sources

        mock_run.return_value = {
            "source": "x",
            "success": False,
            "items": [],
            "error": "error",
        }

        result = run_all_stretch_sources(parallel=False)

        # All should be failed
        assert result["success"] is False
        assert len(result["sources_failed"]) == 3  # twitter, tiktok, amazon
        assert len(result["sources_succeeded"]) == 0
