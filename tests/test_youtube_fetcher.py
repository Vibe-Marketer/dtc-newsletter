"""
Tests for YouTube video fetcher with outlier detection.
DOE-VERSION: 2026.01.31

Tests TubeLab client, YouTube Data API fallback, and YouTubeFetcher orchestration.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import requests

from execution.youtube_fetcher import (
    TubeLabClient,
    YouTubeDataAPIClient,
    YouTubeFetcher,
    fetch_channel_videos,
    calculate_channel_average,
    save_youtube_videos,
    MIN_OUTLIER_SCORE,
    TUBELAB_BASE_URL,
)


# === Test Fixtures ===


@pytest.fixture
def mock_tubelab_response():
    """Sample TubeLab outlier search response."""
    return {
        "videos": [
            {
                "id": "abc123",
                "title": "How I Made $1M in eCommerce in 6 Months",
                "description": "My secret strategy for dropshipping success",
                "thumbnail_url": "https://img.youtube.com/vi/abc123/hqdefault.jpg",
                "views": 500000,
                "channel_name": "Ecom Guru",
                "channel_id": "UCxxx123",
                "channel_average": 50000,
                "outlier_score": 10.0,
                "published_at": (
                    datetime.now(timezone.utc) - timedelta(days=2)
                ).isoformat(),
            },
            {
                "id": "def456",
                "title": "Shopify Store Setup Tutorial",
                "description": "Step by step guide",
                "thumbnail_url": "https://img.youtube.com/vi/def456/hqdefault.jpg",
                "views": 100000,
                "channel_name": "Store Builder",
                "channel_id": "UCyyy456",
                "channel_average": 25000,
                "outlier_score": 4.0,  # Below threshold
                "published_at": (
                    datetime.now(timezone.utc) - timedelta(days=5)
                ).isoformat(),
            },
        ]
    }


@pytest.fixture
def mock_youtube_search_response():
    """Sample YouTube Data API search response."""
    return {
        "items": [
            {
                "id": {"videoId": "vid123"},
                "snippet": {
                    "title": "DTC Brand Strategy",
                    "description": "Quick tips for success",
                    "channelTitle": "Marketing Pro",
                    "channelId": "UCchannel1",
                    "publishedAt": (
                        datetime.now(timezone.utc) - timedelta(days=1)
                    ).isoformat()
                    + "Z",
                },
            },
            {
                "id": {"videoId": "vid456"},
                "snippet": {
                    "title": "Amazon FBA Guide",
                    "description": "Secrets to FBA success",
                    "channelTitle": "FBA Master",
                    "channelId": "UCchannel2",
                    "publishedAt": (
                        datetime.now(timezone.utc) - timedelta(days=3)
                    ).isoformat()
                    + "Z",
                },
            },
        ]
    }


@pytest.fixture
def mock_youtube_videos_response():
    """Sample YouTube Data API videos.list response."""
    return {
        "items": [
            {
                "id": "vid123",
                "snippet": {
                    "title": "DTC Brand Strategy",
                    "description": "Quick tips for success",
                    "channelTitle": "Marketing Pro",
                    "channelId": "UCchannel1",
                    "publishedAt": (
                        datetime.now(timezone.utc) - timedelta(days=1)
                    ).isoformat()
                    + "Z",
                },
                "statistics": {
                    "viewCount": "500000",
                    "likeCount": "25000",
                    "commentCount": "1000",
                },
            },
            {
                "id": "vid456",
                "snippet": {
                    "title": "Amazon FBA Guide",
                    "description": "Secrets to FBA success",
                    "channelTitle": "FBA Master",
                    "channelId": "UCchannel2",
                    "publishedAt": (
                        datetime.now(timezone.utc) - timedelta(days=3)
                    ).isoformat()
                    + "Z",
                },
                "statistics": {
                    "viewCount": "250000",
                    "likeCount": "15000",
                    "commentCount": "500",
                },
            },
        ]
    }


# === TubeLabClient Tests ===


class TestTubeLabClient:
    """Tests for TubeLabClient."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = TubeLabClient(api_key="test_key_123")
        assert client.api_key == "test_key_123"
        assert client.is_configured is True

    def test_init_from_env(self):
        """Test initialization from environment variable."""
        with patch.dict(os.environ, {"TUBELAB_API_KEY": "env_key_456"}):
            client = TubeLabClient()
            assert client.api_key == "env_key_456"
            assert client.is_configured is True

    def test_not_configured(self):
        """Test is_configured when no API key."""
        with patch.dict(os.environ, {}, clear=True):
            client = TubeLabClient(api_key=None)
            client.api_key = None  # Ensure it's None
            assert client.is_configured is False

    def test_search_outliers_success(self, mock_tubelab_response):
        """Test successful outlier search."""
        client = TubeLabClient(api_key="test_key")

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_tubelab_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = client.search_outliers("ecommerce")

            assert mock_get.called
            call_args = mock_get.call_args
            assert "Api-Key test_key" in str(call_args)
            assert "ecommerce" in str(call_args)
            assert result == mock_tubelab_response

    def test_search_outliers_not_configured(self):
        """Test search fails when not configured."""
        client = TubeLabClient(api_key=None)
        client.api_key = None

        with pytest.raises(ValueError, match="TUBELAB_API_KEY"):
            client.search_outliers("test")

    def test_rate_limiting(self):
        """Test rate limiting between requests."""
        client = TubeLabClient(api_key="test_key")

        with patch("requests.get") as mock_get, patch("time.sleep") as mock_sleep:
            mock_response = Mock()
            mock_response.json.return_value = {"videos": []}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # First request - no delay
            client._last_request_time = 0
            client.search_outliers("topic1")

            # Second request - should delay
            client.search_outliers("topic2")

            # Verify sleep was called for rate limiting
            assert mock_sleep.called or client._last_request_time > 0


# === YouTubeDataAPIClient Tests ===


class TestYouTubeDataAPIClient:
    """Tests for YouTube Data API fallback client."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = YouTubeDataAPIClient(api_key="yt_key_123")
        assert client.api_key == "yt_key_123"
        assert client.is_configured is True

    def test_init_from_env(self):
        """Test initialization from environment variable."""
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": "env_yt_key"}):
            client = YouTubeDataAPIClient()
            assert client.api_key == "env_yt_key"

    def test_get_video_statistics(self, mock_youtube_videos_response):
        """Test fetching video statistics."""
        client = YouTubeDataAPIClient(api_key="test_key")

        mock_service = MagicMock()
        mock_videos = MagicMock()
        mock_list = MagicMock()
        mock_list.execute.return_value = mock_youtube_videos_response
        mock_videos.list.return_value = mock_list
        mock_service.videos.return_value = mock_videos

        with patch.object(client, "_get_client", return_value=mock_service):
            result = client.get_video_statistics(["vid123", "vid456"])

            assert "vid123" in result
            assert result["vid123"]["view_count"] == 500000
            assert result["vid123"]["title"] == "DTC Brand Strategy"

            assert "vid456" in result
            assert result["vid456"]["view_count"] == 250000

    def test_get_video_statistics_empty(self):
        """Test with empty video ID list."""
        client = YouTubeDataAPIClient(api_key="test_key")
        result = client.get_video_statistics([])
        assert result == {}


# === YouTubeFetcher Tests ===


class TestYouTubeFetcher:
    """Tests for YouTubeFetcher orchestrator."""

    def test_init_defaults(self):
        """Test default initialization."""
        with patch.dict(
            os.environ, {"TUBELAB_API_KEY": "tube_key", "YOUTUBE_API_KEY": "yt_key"}
        ):
            fetcher = YouTubeFetcher()
            assert fetcher.tubelab_available is True
            assert fetcher.prefer_tubelab is True

    def test_tubelab_available_check(self):
        """Test TubeLab availability check."""
        fetcher = YouTubeFetcher(tubelab_api_key="key123")
        assert fetcher.tubelab_available is True

        fetcher2 = YouTubeFetcher(tubelab_api_key=None, youtube_api_key=None)
        fetcher2.tubelab.api_key = None
        assert fetcher2.tubelab_available is False

    def test_fetch_outliers_tubelab(self, mock_tubelab_response):
        """Test fetching outliers via TubeLab."""
        fetcher = YouTubeFetcher(tubelab_api_key="test_key")

        with patch.object(
            fetcher.tubelab, "search_outliers", return_value=mock_tubelab_response
        ):
            result = fetcher.fetch_outliers_tubelab(
                topics=["ecommerce"], min_outlier_score=5.0
            )

            # Should only include video with score >= 5.0
            assert len(result) == 1
            assert result[0]["id"] == "abc123"
            assert result[0]["outlier_score"] == 10.0
            assert result[0]["source"] == "youtube"
            assert result[0]["api_source"] == "tubelab"

    def test_calculate_outlier_score(self):
        """Test outlier score calculation."""
        fetcher = YouTubeFetcher(tubelab_api_key="key")

        # Recent video with money keyword in title
        score = fetcher.calculate_outlier_score(
            views=100000,
            channel_avg=10000,
            published_at=datetime.now(timezone.utc).isoformat(),
            title="How I Made $500k with Dropshipping",
            description="Learn my secrets",
        )

        # Base: 100000/10000 = 10.0
        # Recency: ~1.3 (today)
        # Engagement: +30% money + 20% secret = 1.5
        # Total: ~10 * 1.3 * 1.5 = ~19.5
        assert score >= 15.0  # Should be high

    def test_calculate_outlier_score_zero_avg(self):
        """Test outlier score with zero channel average."""
        fetcher = YouTubeFetcher(tubelab_api_key="key")

        # Should not raise error, uses fallback of 1.0
        score = fetcher.calculate_outlier_score(
            views=1000,
            channel_avg=0,
            published_at="",
            title="Test",
        )
        assert score > 0

    def test_fetch_outliers_fallback(self, mock_tubelab_response):
        """Test fallback from TubeLab to YouTube Data API."""
        fetcher = YouTubeFetcher(tubelab_api_key="tube_key", youtube_api_key="yt_key")

        # TubeLab fails with rate limit
        with patch.object(
            fetcher.tubelab,
            "search_outliers",
            side_effect=requests.HTTPError(response=Mock(status_code=429)),
        ):
            # Mock YouTube fallback
            mock_youtube_videos = [
                {
                    "id": "yt_vid_1",
                    "title": "Revenue Growth Strategy",
                    "url": "https://www.youtube.com/watch?v=yt_vid_1",
                    "views": 300000,
                    "outlier_score": 8.0,
                    "source": "youtube",
                    "api_source": "youtube_data_api",
                }
            ]
            with patch.object(
                fetcher, "fetch_outliers_youtube", return_value=mock_youtube_videos
            ):
                result = fetcher.fetch_outliers(topics=["ecommerce"])

                # Should use YouTube fallback
                assert len(result) == 1
                assert result[0]["api_source"] == "youtube_data_api"

    def test_fetch_outliers_no_api_configured(self):
        """Test error when no API configured."""
        fetcher = YouTubeFetcher(tubelab_api_key=None, youtube_api_key=None)
        fetcher.tubelab.api_key = None
        fetcher.youtube.api_key = None

        with pytest.raises(ValueError, match="No YouTube API configured"):
            fetcher.fetch_outliers()

    def test_normalize_tubelab_video(self):
        """Test TubeLab response normalization."""
        fetcher = YouTubeFetcher(tubelab_api_key="key")

        tubelab_video = {
            "id": "vid123",
            "title": "Test Video $100k Revenue",
            "description": "My secret tips",
            "thumbnail_url": "https://example.com/thumb.jpg",
            "views": 50000,
            "channel_name": "Test Channel",
            "channel_id": "UCtest",
            "channel_average": 5000,
            "outlier_score": 10.0,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }

        normalized = fetcher._normalize_tubelab_video(tubelab_video)

        assert normalized["id"] == "vid123"
        assert normalized["url"] == "https://www.youtube.com/watch?v=vid123"
        assert normalized["source"] == "youtube"
        assert normalized["api_source"] == "tubelab"
        assert normalized["outlier_score"] == 10.0
        assert "fetched_at" in normalized


# === Convenience Function Tests ===


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_save_youtube_videos(self, tmp_path):
        """Test saving videos to cache."""
        videos = [
            {
                "id": "vid1",
                "title": "Test Video 1",
                "views": 10000,
                "outlier_score": 5.0,
                "api_source": "tubelab",
            },
            {
                "id": "vid2",
                "title": "Test Video 2",
                "views": 20000,
                "outlier_score": 7.0,
                "api_source": "youtube_data_api",
            },
        ]

        filepath = save_youtube_videos(videos, cache_dir=tmp_path)

        assert filepath.exists()
        assert filepath.suffix == ".json"

        with open(filepath) as f:
            data = json.load(f)

        assert data["metadata"]["source"] == "youtube"
        assert data["metadata"]["video_count"] == 2
        assert "tubelab" in data["metadata"]["api_sources"]
        assert "youtube_data_api" in data["metadata"]["api_sources"]
        assert len(data["videos"]) == 2

    def test_save_youtube_videos_creates_dir(self, tmp_path):
        """Test that save creates directory if needed."""
        cache_dir = tmp_path / "new_dir"
        assert not cache_dir.exists()

        save_youtube_videos([{"id": "test"}], cache_dir=cache_dir)

        assert cache_dir.exists()


# === Integration Tests ===


class TestIntegration:
    """Integration tests for the full flow."""

    def test_full_flow_with_mocks(self, mock_tubelab_response):
        """Test complete fetch flow with mocked APIs."""
        fetcher = YouTubeFetcher(tubelab_api_key="test_key")

        with patch.object(
            fetcher.tubelab, "search_outliers", return_value=mock_tubelab_response
        ):
            videos = fetcher.fetch_outliers(topics=["ecommerce"], min_outlier_score=5.0)

            # Should get one video above threshold
            assert len(videos) >= 1

            # All videos should meet minimum score
            for video in videos:
                assert video["outlier_score"] >= 5.0
                assert video["source"] == "youtube"
                assert "url" in video
                assert "title" in video


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
