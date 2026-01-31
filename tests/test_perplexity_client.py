"""
Tests for Perplexity API client.
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestGetClient:
    """Tests for get_client function."""

    def test_raises_error_when_no_api_key(self):
        """Should raise ValueError when PERPLEXITY_API_KEY is not set."""
        from execution.perplexity_client import get_client

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                get_client()

        assert "PERPLEXITY_API_KEY" in str(exc_info.value)

    def test_returns_client_when_api_key_set(self):
        """Should return OpenAI client when API key is configured."""
        from execution.perplexity_client import get_client

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.perplexity_client.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                client = get_client()

        mock_openai.assert_called_once_with(
            api_key="test-key", base_url="https://api.perplexity.ai"
        )
        assert client is not None


class TestSearchTrends:
    """Tests for search_trends function."""

    def test_returns_structured_response(self):
        """Should return dict with content, citations, model, fetched_at."""
        from execution.perplexity_client import search_trends

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Trending topics summary"
        mock_completion.citations = ["https://example.com/source1"]

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.perplexity_client.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = mock_completion

                result = search_trends("e-commerce DTC")

        assert "content" in result
        assert result["content"] == "Trending topics summary"
        assert "citations" in result
        assert result["citations"] == ["https://example.com/source1"]
        assert "model" in result
        assert result["model"] == "sonar-pro"
        assert "fetched_at" in result
        assert "topic" in result
        assert result["topic"] == "e-commerce DTC"

    def test_uses_specified_model(self):
        """Should use the specified model in API call."""
        from execution.perplexity_client import search_trends

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Response"
        mock_completion.citations = []

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.perplexity_client.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = mock_completion

                search_trends("test", model="sonar")

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "sonar"

    def test_handles_api_error(self):
        """Should raise RuntimeError on API failure."""
        from execution.perplexity_client import search_trends

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.perplexity_client.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.side_effect = Exception("API Error")

                with pytest.raises(RuntimeError) as exc_info:
                    search_trends("test")

        assert "Perplexity API error" in str(exc_info.value)

    def test_handles_missing_citations(self):
        """Should handle response without citations gracefully."""
        from execution.perplexity_client import search_trends

        mock_completion = MagicMock(spec=["choices"])  # No citations attribute
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Response without citations"

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.perplexity_client.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = mock_completion

                result = search_trends("test")

        assert result["citations"] == []


class TestDeepDiveTopic:
    """Tests for deep_dive_topic function."""

    def test_returns_structured_response(self):
        """Should return dict with content, citations, model, fetched_at."""
        from execution.perplexity_client import deep_dive_topic

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Deep dive analysis"
        mock_completion.citations = ["https://example.com/source1"]

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.perplexity_client.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = mock_completion

                result = deep_dive_topic("TikTok Shop trends")

        assert "content" in result
        assert result["content"] == "Deep dive analysis"
        assert "citations" in result
        assert "model" in result
        assert "topic" in result
        assert result["topic"] == "TikTok Shop trends"
        assert result["query_type"] == "deep_dive"

    def test_handles_api_error(self):
        """Should raise RuntimeError on API failure."""
        from execution.perplexity_client import deep_dive_topic

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.perplexity_client.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.side_effect = Exception(
                    "Network Error"
                )

                with pytest.raises(RuntimeError) as exc_info:
                    deep_dive_topic("test topic")

        assert "deep_dive_topic" in str(exc_info.value)


class TestSaveResearch:
    """Tests for save_research function."""

    def test_saves_research_to_file(self, tmp_path):
        """Should save research to JSON file with proper structure."""
        from execution.perplexity_client import save_research

        research = {
            "content": "Test research content",
            "citations": ["https://example.com"],
            "model": "sonar-pro",
            "query_type": "search_trends",
            "fetched_at": "2026-01-31T12:00:00+00:00",
        }

        filepath = save_research(research, "dtc-trends", cache_dir=tmp_path)

        assert filepath.exists()
        assert filepath.suffix == ".json"

        with open(filepath) as f:
            data = json.load(f)

        assert "metadata" in data
        assert data["metadata"]["source"] == "perplexity"
        assert data["metadata"]["topic_slug"] == "dtc-trends"
        assert "research" in data
        assert data["research"]["content"] == "Test research content"

    def test_creates_directory_if_missing(self, tmp_path):
        """Should create cache directory if it doesn't exist."""
        from execution.perplexity_client import save_research

        cache_dir = tmp_path / "nested" / "cache"
        research = {"content": "Test", "query_type": "deep_dive"}

        filepath = save_research(research, "test-topic", cache_dir=cache_dir)

        assert filepath.exists()
        assert cache_dir.exists()

    def test_includes_date_prefix(self, tmp_path):
        """Should include date prefix in filename."""
        from execution.perplexity_client import save_research

        research = {"content": "Test", "query_type": "search_trends"}
        filepath = save_research(research, "test", cache_dir=tmp_path)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert filepath.name.startswith(today)

    def test_includes_query_type_in_filename(self, tmp_path):
        """Should include query type in filename."""
        from execution.perplexity_client import save_research

        research = {"content": "Test", "query_type": "deep_dive"}
        filepath = save_research(research, "topic-slug", cache_dir=tmp_path)

        assert "deep_dive" in filepath.name


class TestLoadResearch:
    """Tests for load_research function."""

    def test_loads_research_from_file(self, tmp_path):
        """Should load research from cache file."""
        from execution.perplexity_client import load_research

        data = {
            "metadata": {"source": "perplexity"},
            "research": {
                "content": "Loaded content",
                "citations": [],
            },
        }

        filepath = tmp_path / "test_research.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        result = load_research(filepath)

        assert result["content"] == "Loaded content"

    def test_raises_on_missing_file(self, tmp_path):
        """Should raise FileNotFoundError if file doesn't exist."""
        from execution.perplexity_client import load_research

        with pytest.raises(FileNotFoundError):
            load_research(tmp_path / "nonexistent.json")


class TestGetRecentResearch:
    """Tests for get_recent_research function."""

    def test_returns_research_within_days(self, tmp_path):
        """Should return research from within specified days."""
        from execution.perplexity_client import get_recent_research, save_research

        # Create recent research
        research = {
            "content": "Recent research",
            "query_type": "search_trends",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        save_research(research, "recent-topic", cache_dir=tmp_path)

        results = get_recent_research(cache_dir=tmp_path, days_back=7)

        assert len(results) == 1
        assert results[0]["content"] == "Recent research"

    def test_returns_empty_for_missing_directory(self, tmp_path):
        """Should return empty list if directory doesn't exist."""
        from execution.perplexity_client import get_recent_research

        nonexistent = tmp_path / "nonexistent"
        results = get_recent_research(cache_dir=nonexistent)

        assert results == []

    def test_sorts_by_date_descending(self, tmp_path):
        """Should sort results by fetched_at descending."""
        from execution.perplexity_client import get_recent_research

        # Create files with different dates
        for i, (date_str, fetch_time) in enumerate(
            [
                ("2026-01-30", "2026-01-30T12:00:00+00:00"),
                ("2026-01-31", "2026-01-31T12:00:00+00:00"),
                ("2026-01-29", "2026-01-29T12:00:00+00:00"),
            ]
        ):
            data = {
                "metadata": {"source": "perplexity"},
                "research": {
                    "content": f"Research {i}",
                    "fetched_at": fetch_time,
                },
            }
            filepath = tmp_path / f"{date_str}_search_trends_topic{i}.json"
            with open(filepath, "w") as f:
                json.dump(data, f)

        results = get_recent_research(cache_dir=tmp_path, days_back=30)

        # Should be sorted newest first
        assert results[0]["fetched_at"] == "2026-01-31T12:00:00+00:00"
        assert results[1]["fetched_at"] == "2026-01-30T12:00:00+00:00"
        assert results[2]["fetched_at"] == "2026-01-29T12:00:00+00:00"
