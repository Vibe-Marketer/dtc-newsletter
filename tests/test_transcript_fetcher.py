"""
Tests for YouTube transcript fetcher.
DOE-VERSION: 2026.01.31

Tests transcript fetching, error handling, rate limiting, and caching.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from execution.transcript_fetcher import (
    fetch_transcript,
    fetch_transcripts_batch,
    save_transcripts,
    load_transcripts,
    get_transcript_text,
    get_transcript_with_timestamps,
    fetch_transcripts_for_videos,
    _extract_video_id,
    REQUEST_DELAY_SECONDS,
    DEFAULT_BATCH_SIZE,
)


# === Test Fixtures ===


@pytest.fixture
def mock_transcript_segment():
    """Mock transcript segment."""
    segment = MagicMock()
    segment.text = "Hello world"
    segment.start = 0.0
    segment.duration = 2.5
    return segment


@pytest.fixture
def mock_transcript_data():
    """Sample transcript data structure."""
    return [
        {"text": "Hello everyone", "start": 0.0, "duration": 2.0},
        {"text": "Welcome to my channel", "start": 2.0, "duration": 3.0},
        {"text": "Today we'll discuss ecommerce", "start": 5.0, "duration": 4.0},
    ]


@pytest.fixture
def sample_transcript_result(mock_transcript_data):
    """Sample successful transcript result."""
    return {
        "video_id": "abc123xyz",
        "transcript": mock_transcript_data,
        "language": "en",
        "is_generated": False,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }


@pytest.fixture
def sample_failed_result():
    """Sample failed transcript result."""
    return {
        "video_id": "fail456",
        "transcript": [],
        "language": None,
        "is_generated": None,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "error": "Transcripts are disabled for this video",
    }


# === Video ID Extraction Tests ===


class TestVideoIdExtraction:
    """Tests for _extract_video_id function."""

    def test_plain_video_id(self):
        """Test plain video ID passthrough."""
        assert _extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_youtube_watch_url(self):
        """Test youtube.com/watch URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert _extract_video_id(url) == "dQw4w9WgXcQ"

    def test_youtube_watch_url_with_params(self):
        """Test youtube.com/watch URL with extra parameters."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s&list=PLxyz"
        assert _extract_video_id(url) == "dQw4w9WgXcQ"

    def test_youtu_be_short_url(self):
        """Test youtu.be short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert _extract_video_id(url) == "dQw4w9WgXcQ"

    def test_youtu_be_with_params(self):
        """Test youtu.be short URL with parameters."""
        url = "https://youtu.be/dQw4w9WgXcQ?t=45"
        assert _extract_video_id(url) == "dQw4w9WgXcQ"

    def test_embed_url(self):
        """Test /embed/ URL format."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert _extract_video_id(url) == "dQw4w9WgXcQ"

    def test_whitespace_handling(self):
        """Test whitespace is stripped."""
        assert _extract_video_id("  dQw4w9WgXcQ  ") == "dQw4w9WgXcQ"


# === Fetch Transcript Tests ===


class TestFetchTranscript:
    """Tests for fetch_transcript function."""

    def test_fetch_transcript_success(self, mock_transcript_segment):
        """Test successful transcript fetch."""
        mock_transcript_list = MagicMock()
        mock_transcript = MagicMock()
        mock_transcript.language_code = "en"
        mock_transcript.is_generated = False
        mock_transcript.fetch.return_value = [mock_transcript_segment]

        mock_transcript_list.find_manually_created_transcript.return_value = (
            mock_transcript
        )

        mock_api_instance = MagicMock()
        mock_api_instance.list.return_value = mock_transcript_list

        with patch(
            "execution.transcript_fetcher.YouTubeTranscriptApi",
            return_value=mock_api_instance,
        ):
            result = fetch_transcript("test_video_id")

            assert result["video_id"] == "test_video_id"
            assert result["error"] is None
            assert len(result["transcript"]) == 1
            assert result["transcript"][0]["text"] == "Hello world"
            assert result["language"] == "en"
            assert result["is_generated"] is False

    def test_fetch_transcript_disabled(self):
        """Test handling TranscriptsDisabled error."""
        from youtube_transcript_api._errors import TranscriptsDisabled

        mock_api_instance = MagicMock()
        mock_api_instance.list.side_effect = TranscriptsDisabled("test_id")

        with patch(
            "execution.transcript_fetcher.YouTubeTranscriptApi",
            return_value=mock_api_instance,
        ):
            result = fetch_transcript("test_video_id")

            assert result["video_id"] == "test_video_id"
            assert result["transcript"] == []
            assert "disabled" in result["error"].lower()

    def test_fetch_transcript_not_found(self):
        """Test handling NoTranscriptFound error."""
        from youtube_transcript_api._errors import NoTranscriptFound

        mock_api_instance = MagicMock()
        mock_api_instance.list.side_effect = NoTranscriptFound("test_id", ["en"], [])

        with patch(
            "execution.transcript_fetcher.YouTubeTranscriptApi",
            return_value=mock_api_instance,
        ):
            result = fetch_transcript("test_video_id")

            assert result["error"] is not None
            assert result["transcript"] == []

    def test_fetch_transcript_video_unavailable(self):
        """Test handling VideoUnavailable error."""
        from youtube_transcript_api._errors import VideoUnavailable

        mock_api_instance = MagicMock()
        mock_api_instance.list.side_effect = VideoUnavailable("test_id")

        with patch(
            "execution.transcript_fetcher.YouTubeTranscriptApi",
            return_value=mock_api_instance,
        ):
            result = fetch_transcript("test_video_id")

            assert "unavailable" in result["error"].lower()

    def test_fetch_transcript_unexpected_error(self):
        """Test handling unexpected errors."""
        mock_api_instance = MagicMock()
        mock_api_instance.list.side_effect = RuntimeError("Unexpected error")

        with patch(
            "execution.transcript_fetcher.YouTubeTranscriptApi",
            return_value=mock_api_instance,
        ):
            result = fetch_transcript("test_video_id")

            assert "RuntimeError" in result["error"]
            assert result["transcript"] == []


# === Batch Fetch Tests ===


class TestFetchTranscriptsBatch:
    """Tests for fetch_transcripts_batch function."""

    def test_batch_respects_limit(self, sample_transcript_result):
        """Test that batch respects limit parameter."""
        with patch(
            "execution.transcript_fetcher.fetch_transcript",
            return_value=sample_transcript_result,
        ):
            video_ids = ["vid1", "vid2", "vid3", "vid4", "vid5"]

            results = fetch_transcripts_batch(
                video_ids, limit=3, delay=0, verbose=False
            )

            assert len(results) == 3

    def test_batch_applies_delay(self, sample_transcript_result):
        """Test that delay is applied between requests."""
        with (
            patch(
                "execution.transcript_fetcher.fetch_transcript",
                return_value=sample_transcript_result,
            ),
            patch("time.sleep") as mock_sleep,
        ):
            video_ids = ["vid1", "vid2", "vid3"]

            fetch_transcripts_batch(video_ids, limit=3, delay=0.5, verbose=False)

            # Sleep called for all but first request
            assert mock_sleep.call_count == 2

    def test_batch_handles_mixed_results(
        self, sample_transcript_result, sample_failed_result
    ):
        """Test batch handles mix of success and failure."""
        with patch(
            "execution.transcript_fetcher.fetch_transcript",
            side_effect=[sample_transcript_result, sample_failed_result],
        ):
            video_ids = ["vid1", "vid2"]

            results = fetch_transcripts_batch(
                video_ids, limit=2, delay=0, verbose=False
            )

            assert len(results) == 2
            assert results[0]["error"] is None
            assert results[1]["error"] is not None

    def test_batch_default_limit(self):
        """Test default batch size is applied."""
        assert DEFAULT_BATCH_SIZE == 10


# === Save/Load Tests ===


class TestSaveLoadTranscripts:
    """Tests for transcript caching."""

    def test_save_transcripts(
        self, tmp_path, sample_transcript_result, sample_failed_result
    ):
        """Test saving transcripts to cache."""
        transcripts = [sample_transcript_result, sample_failed_result]

        filepath = save_transcripts(transcripts, cache_dir=tmp_path)

        assert filepath.exists()
        assert filepath.suffix == ".json"

        with open(filepath) as f:
            data = json.load(f)

        assert data["metadata"]["source"] == "youtube_transcripts"
        assert data["metadata"]["total_videos"] == 2
        assert data["metadata"]["successful"] == 1
        assert data["metadata"]["failed"] == 1
        assert len(data["transcripts"]) == 2

    def test_save_creates_directory(self, tmp_path):
        """Test save creates cache directory if needed."""
        cache_dir = tmp_path / "new_dir"
        assert not cache_dir.exists()

        save_transcripts([{"video_id": "test", "error": None}], cache_dir=cache_dir)

        assert cache_dir.exists()

    def test_load_transcripts(self, tmp_path, sample_transcript_result):
        """Test loading transcripts from cache."""
        # Save first
        save_transcripts([sample_transcript_result], cache_dir=tmp_path)

        # Load
        loaded = load_transcripts(cache_dir=tmp_path)

        assert len(loaded) == 1
        assert loaded[0]["video_id"] == sample_transcript_result["video_id"]

    def test_load_transcripts_not_found(self, tmp_path):
        """Test FileNotFoundError when cache doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_transcripts(cache_dir=tmp_path)


# === Text Extraction Tests ===


class TestTextExtraction:
    """Tests for transcript text extraction."""

    def test_get_transcript_text(self, sample_transcript_result):
        """Test extracting plain text from transcript."""
        text = get_transcript_text(sample_transcript_result)

        assert "Hello everyone" in text
        assert "Welcome to my channel" in text
        assert "Today we'll discuss ecommerce" in text

    def test_get_transcript_text_empty(self, sample_failed_result):
        """Test empty string for failed transcript."""
        text = get_transcript_text(sample_failed_result)
        assert text == ""

    def test_get_transcript_with_timestamps(self, sample_transcript_result):
        """Test formatted transcript with timestamps."""
        formatted = get_transcript_with_timestamps(sample_transcript_result)

        assert "[00:00]" in formatted
        assert "[00:02]" in formatted
        assert "[00:05]" in formatted
        assert "Hello everyone" in formatted

    def test_get_transcript_with_timestamps_empty(self, sample_failed_result):
        """Test empty string for failed transcript."""
        formatted = get_transcript_with_timestamps(sample_failed_result)
        assert formatted == ""


# === Convenience Function Tests ===


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_fetch_transcripts_for_videos(self, sample_transcript_result):
        """Test fetching transcripts from video dicts."""
        videos = [
            {"id": "vid1", "title": "Video 1"},
            {"id": "vid2", "title": "Video 2"},
            {"id": "vid3", "title": "Video 3"},
        ]

        with patch(
            "execution.transcript_fetcher.fetch_transcripts_batch",
            return_value=[sample_transcript_result, sample_transcript_result],
        ) as mock_batch:
            results = fetch_transcripts_for_videos(videos, limit=2, verbose=False)

            # Should extract IDs and call batch
            mock_batch.assert_called_once()
            call_args = mock_batch.call_args
            assert call_args[0][0] == ["vid1", "vid2"]

    def test_fetch_transcripts_custom_id_key(self, sample_transcript_result):
        """Test custom ID key for video dicts."""
        videos = [
            {"video_id": "vid1", "title": "Video 1"},
            {"video_id": "vid2", "title": "Video 2"},
        ]

        with patch(
            "execution.transcript_fetcher.fetch_transcripts_batch",
            return_value=[sample_transcript_result],
        ) as mock_batch:
            fetch_transcripts_for_videos(
                videos, id_key="video_id", limit=1, verbose=False
            )

            call_args = mock_batch.call_args
            assert call_args[0][0] == ["vid1"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
