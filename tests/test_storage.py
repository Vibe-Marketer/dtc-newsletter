"""
Tests for content storage layer.
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import shutil


class TestGetCacheDir:
    """Tests for get_cache_dir function."""

    def test_creates_directory_if_missing(self, tmp_path):
        """Should create cache directory if it doesn't exist."""
        from execution.storage import get_cache_dir, DEFAULT_CACHE_DIR
        from unittest.mock import patch

        test_dir = tmp_path / "cache" / "reddit"

        with patch("execution.storage.DEFAULT_CACHE_DIR", test_dir):
            result = get_cache_dir()

        assert result.exists()
        assert result.is_dir()

    def test_returns_existing_directory(self, tmp_path):
        """Should return existing directory without error."""
        from execution.storage import get_cache_dir
        from unittest.mock import patch

        test_dir = tmp_path / "cache" / "reddit"
        test_dir.mkdir(parents=True)

        with patch("execution.storage.DEFAULT_CACHE_DIR", test_dir):
            result = get_cache_dir()

        assert result == test_dir


class TestGetCacheFilename:
    """Tests for get_cache_filename function."""

    def test_generates_filename_for_today(self):
        """Should generate filename with today's date."""
        from execution.storage import get_cache_filename

        filename = get_cache_filename()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        assert filename == f"reddit_{today}.json"

    def test_generates_filename_for_specific_date(self):
        """Should generate filename for specified date."""
        from execution.storage import get_cache_filename

        test_date = datetime(2025, 6, 15, tzinfo=timezone.utc)
        filename = get_cache_filename(test_date)

        assert filename == "reddit_2025-06-15.json"


class TestSaveRedditPosts:
    """Tests for save_reddit_posts function."""

    def test_saves_posts_to_file(self, tmp_path):
        """Should save posts to JSON file."""
        from execution.storage import save_reddit_posts

        posts = [
            {
                "id": "post1",
                "title": "Test Post 1",
                "outlier_score": 5.0,
                "subreddit": "shopify",
            },
            {
                "id": "post2",
                "title": "Test Post 2",
                "outlier_score": 3.0,
                "subreddit": "ecommerce",
            },
        ]

        filepath = save_reddit_posts(posts, cache_dir=tmp_path)

        assert filepath.exists()

        with open(filepath) as f:
            data = json.load(f)

        assert data["posts"] == posts
        assert data["metadata"]["post_count"] == 2

    def test_includes_metadata(self, tmp_path):
        """Should include metadata in saved file."""
        from execution.storage import save_reddit_posts

        posts = [
            {"id": "post1", "subreddit": "shopify"},
            {"id": "post2", "subreddit": "ecommerce"},
        ]

        filepath = save_reddit_posts(posts, cache_dir=tmp_path)

        with open(filepath) as f:
            data = json.load(f)

        assert "metadata" in data
        assert data["metadata"]["source"] == "reddit"
        assert "fetched_at" in data["metadata"]
        assert set(data["metadata"]["subreddits"]) == {"shopify", "ecommerce"}

    def test_uses_custom_filename(self, tmp_path):
        """Should use custom filename when provided."""
        from execution.storage import save_reddit_posts

        posts = [{"id": "post1"}]
        filepath = save_reddit_posts(posts, cache_dir=tmp_path, filename="custom.json")

        assert filepath.name == "custom.json"

    def test_creates_directory_if_missing(self, tmp_path):
        """Should create cache directory if it doesn't exist."""
        from execution.storage import save_reddit_posts

        cache_dir = tmp_path / "nested" / "cache"
        posts = [{"id": "post1"}]

        filepath = save_reddit_posts(posts, cache_dir=cache_dir)

        assert filepath.exists()
        assert cache_dir.exists()


class TestLoadCachedPosts:
    """Tests for load_cached_posts function."""

    def test_loads_posts_from_file(self, tmp_path):
        """Should load posts from cache file."""
        from execution.storage import load_cached_posts

        # Create test cache file
        posts = [{"id": "post1", "title": "Test"}]
        cache_data = {"metadata": {}, "posts": posts}

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filepath = tmp_path / f"reddit_{today}.json"

        with open(filepath, "w") as f:
            json.dump(cache_data, f)

        loaded = load_cached_posts(cache_dir=tmp_path)

        assert loaded == posts

    def test_loads_for_specific_date(self, tmp_path):
        """Should load posts for specific date."""
        from execution.storage import load_cached_posts

        posts = [{"id": "old_post"}]
        cache_data = {"metadata": {}, "posts": posts}

        filepath = tmp_path / "reddit_2025-01-15.json"
        with open(filepath, "w") as f:
            json.dump(cache_data, f)

        test_date = datetime(2025, 1, 15, tzinfo=timezone.utc)
        loaded = load_cached_posts(cache_dir=tmp_path, date=test_date)

        assert loaded == posts

    def test_raises_on_missing_file(self, tmp_path):
        """Should raise FileNotFoundError if cache file doesn't exist."""
        from execution.storage import load_cached_posts

        with pytest.raises(FileNotFoundError):
            load_cached_posts(cache_dir=tmp_path, filename="nonexistent.json")

    def test_loads_custom_filename(self, tmp_path):
        """Should load from custom filename."""
        from execution.storage import load_cached_posts

        posts = [{"id": "custom_post"}]
        cache_data = {"metadata": {}, "posts": posts}

        filepath = tmp_path / "custom_cache.json"
        with open(filepath, "w") as f:
            json.dump(cache_data, f)

        loaded = load_cached_posts(cache_dir=tmp_path, filename="custom_cache.json")

        assert loaded == posts


class TestLoadAllCachedPosts:
    """Tests for load_all_cached_posts function."""

    def test_loads_posts_from_multiple_days(self, tmp_path):
        """Should load and combine posts from multiple cache files."""
        from execution.storage import load_all_cached_posts

        now = datetime.now(timezone.utc)

        # Create cache files for 3 days
        for i in range(3):
            date = now - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            posts = [{"id": f"post_day{i}", "date": date_str}]
            cache_data = {"metadata": {}, "posts": posts}

            filepath = tmp_path / f"reddit_{date_str}.json"
            with open(filepath, "w") as f:
                json.dump(cache_data, f)

        loaded = load_all_cached_posts(cache_dir=tmp_path, days_back=7)

        assert len(loaded) == 3

    def test_deduplicates_posts_by_id(self, tmp_path):
        """Should deduplicate posts with same ID from different days."""
        from execution.storage import load_all_cached_posts

        now = datetime.now(timezone.utc)

        # Same post ID in two different days
        for i in range(2):
            date = now - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            posts = [{"id": "duplicate_post", "day": i}]
            cache_data = {"metadata": {}, "posts": posts}

            filepath = tmp_path / f"reddit_{date_str}.json"
            with open(filepath, "w") as f:
                json.dump(cache_data, f)

        loaded = load_all_cached_posts(cache_dir=tmp_path, days_back=7)

        # Should only have one post (deduplicated)
        assert len(loaded) == 1

    def test_handles_missing_days_gracefully(self, tmp_path):
        """Should skip days without cache files."""
        from execution.storage import load_all_cached_posts

        now = datetime.now(timezone.utc)

        # Only create file for today
        date_str = now.strftime("%Y-%m-%d")
        posts = [{"id": "today_post"}]
        cache_data = {"metadata": {}, "posts": posts}

        filepath = tmp_path / f"reddit_{date_str}.json"
        with open(filepath, "w") as f:
            json.dump(cache_data, f)

        # Should not raise, just return available posts
        loaded = load_all_cached_posts(cache_dir=tmp_path, days_back=7)

        assert len(loaded) == 1


class TestGetHighOutlierPosts:
    """Tests for get_high_outlier_posts function."""

    def test_filters_by_min_score(self, tmp_path):
        """Should only return posts above min_score threshold."""
        from execution.storage import get_high_outlier_posts

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        posts = [
            {"id": "low", "outlier_score": 1.5},
            {"id": "medium", "outlier_score": 2.5},
            {"id": "high", "outlier_score": 5.0},
        ]
        cache_data = {"metadata": {}, "posts": posts}

        filepath = tmp_path / f"reddit_{date_str}.json"
        with open(filepath, "w") as f:
            json.dump(cache_data, f)

        # Get posts with score >= 3.0
        result = get_high_outlier_posts(min_score=3.0, cache_dir=tmp_path)

        assert len(result) == 1
        assert result[0]["id"] == "high"

    def test_sorts_by_outlier_score_descending(self, tmp_path):
        """Should return posts sorted by outlier_score descending."""
        from execution.storage import get_high_outlier_posts

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        posts = [
            {"id": "p1", "outlier_score": 3.5},
            {"id": "p2", "outlier_score": 7.0},
            {"id": "p3", "outlier_score": 5.0},
        ]
        cache_data = {"metadata": {}, "posts": posts}

        filepath = tmp_path / f"reddit_{date_str}.json"
        with open(filepath, "w") as f:
            json.dump(cache_data, f)

        result = get_high_outlier_posts(min_score=3.0, cache_dir=tmp_path)

        scores = [p["outlier_score"] for p in result]
        assert scores == [7.0, 5.0, 3.5]

    def test_returns_empty_list_when_no_high_scorers(self, tmp_path):
        """Should return empty list when no posts meet threshold."""
        from execution.storage import get_high_outlier_posts

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        posts = [
            {"id": "low1", "outlier_score": 1.0},
            {"id": "low2", "outlier_score": 2.0},
        ]
        cache_data = {"metadata": {}, "posts": posts}

        filepath = tmp_path / f"reddit_{date_str}.json"
        with open(filepath, "w") as f:
            json.dump(cache_data, f)

        result = get_high_outlier_posts(min_score=5.0, cache_dir=tmp_path)

        assert result == []


class TestGetCacheStats:
    """Tests for get_cache_stats function."""

    def test_returns_empty_stats_for_missing_dir(self, tmp_path):
        """Should return empty stats if cache dir doesn't exist."""
        from execution.storage import get_cache_stats

        nonexistent = tmp_path / "nonexistent"
        stats = get_cache_stats(cache_dir=nonexistent)

        assert stats["total_files"] == 0
        assert stats["total_posts"] == 0
        assert stats["date_range"] is None

    def test_calculates_stats_correctly(self, tmp_path):
        """Should calculate correct statistics."""
        from execution.storage import get_cache_stats

        # Create some cache files
        for date_str, count in [("2025-01-15", 5), ("2025-01-16", 10)]:
            posts = [{"id": f"post_{i}"} for i in range(count)]
            cache_data = {"metadata": {"post_count": count}, "posts": posts}

            filepath = tmp_path / f"reddit_{date_str}.json"
            with open(filepath, "w") as f:
                json.dump(cache_data, f)

        stats = get_cache_stats(cache_dir=tmp_path)

        assert stats["total_files"] == 2
        assert stats["total_posts"] == 15
        assert stats["date_range"] == "2025-01-15 to 2025-01-16"

    def test_includes_file_details(self, tmp_path):
        """Should include details for each file."""
        from execution.storage import get_cache_stats

        posts = [{"id": "post1"}]
        cache_data = {"metadata": {"post_count": 1}, "posts": posts}

        filepath = tmp_path / "reddit_2025-01-20.json"
        with open(filepath, "w") as f:
            json.dump(cache_data, f)

        stats = get_cache_stats(cache_dir=tmp_path)

        assert len(stats["files"]) == 1
        assert stats["files"][0]["filename"] == "reddit_2025-01-20.json"
        assert stats["files"][0]["date"] == "2025-01-20"
        assert stats["files"][0]["post_count"] == 1


class TestCleanupOldCache:
    """Tests for cleanup_old_cache function."""

    def test_deletes_old_files(self, tmp_path):
        """Should delete cache files older than keep_days."""
        from execution.storage import cleanup_old_cache

        now = datetime.now(timezone.utc)

        # Create old file (40 days ago)
        old_date = now - timedelta(days=40)
        old_filepath = tmp_path / f"reddit_{old_date.strftime('%Y-%m-%d')}.json"
        old_filepath.write_text('{"metadata": {}, "posts": []}')

        # Create recent file (5 days ago)
        recent_date = now - timedelta(days=5)
        recent_filepath = tmp_path / f"reddit_{recent_date.strftime('%Y-%m-%d')}.json"
        recent_filepath.write_text('{"metadata": {}, "posts": []}')

        deleted = cleanup_old_cache(cache_dir=tmp_path, keep_days=30)

        assert len(deleted) == 1
        assert not old_filepath.exists()
        assert recent_filepath.exists()

    def test_keeps_recent_files(self, tmp_path):
        """Should keep files within keep_days."""
        from execution.storage import cleanup_old_cache

        now = datetime.now(timezone.utc)

        # Create recent file
        recent_filepath = tmp_path / f"reddit_{now.strftime('%Y-%m-%d')}.json"
        recent_filepath.write_text('{"metadata": {}, "posts": []}')

        deleted = cleanup_old_cache(cache_dir=tmp_path, keep_days=30)

        assert len(deleted) == 0
        assert recent_filepath.exists()

    def test_returns_list_of_deleted_files(self, tmp_path):
        """Should return list of deleted filenames."""
        from execution.storage import cleanup_old_cache

        now = datetime.now(timezone.utc)

        # Create old files
        for i in [35, 40, 45]:
            old_date = now - timedelta(days=i)
            filepath = tmp_path / f"reddit_{old_date.strftime('%Y-%m-%d')}.json"
            filepath.write_text('{"metadata": {}, "posts": []}')

        deleted = cleanup_old_cache(cache_dir=tmp_path, keep_days=30)

        assert len(deleted) == 3
        for filename in deleted:
            assert filename.startswith("reddit_")
            assert filename.endswith(".json")

    def test_handles_empty_directory(self, tmp_path):
        """Should handle empty directory without error."""
        from execution.storage import cleanup_old_cache

        deleted = cleanup_old_cache(cache_dir=tmp_path, keep_days=30)

        assert deleted == []

    def test_handles_nonexistent_directory(self, tmp_path):
        """Should handle nonexistent directory without error."""
        from execution.storage import cleanup_old_cache

        nonexistent = tmp_path / "nonexistent"
        deleted = cleanup_old_cache(cache_dir=nonexistent, keep_days=30)

        assert deleted == []


class TestIntegration:
    """Integration tests for save and load."""

    def test_save_and_load_roundtrip(self, tmp_path):
        """Should save and load posts correctly."""
        from execution.storage import save_reddit_posts, load_cached_posts

        original_posts = [
            {
                "id": "abc123",
                "title": "Test Post",
                "selftext": "Content here",
                "url": "https://reddit.com/r/test",
                "upvotes": 500,
                "outlier_score": 5.5,
                "subreddit": "test",
                "engagement_modifiers": ["money", "time"],
            }
        ]

        save_reddit_posts(original_posts, cache_dir=tmp_path)
        loaded_posts = load_cached_posts(cache_dir=tmp_path)

        assert loaded_posts == original_posts

    def test_unicode_content_preserved(self, tmp_path):
        """Should preserve unicode characters in content."""
        from execution.storage import save_reddit_posts, load_cached_posts

        posts = [
            {
                "id": "unicode_post",
                "title": "How I made $10,000 with emoji strategy",
                "selftext": "Step 1: Use these emojis correctly...",
            }
        ]

        save_reddit_posts(posts, cache_dir=tmp_path)
        loaded = load_cached_posts(cache_dir=tmp_path)

        assert loaded[0]["title"] == posts[0]["title"]
        assert loaded[0]["selftext"] == posts[0]["selftext"]
