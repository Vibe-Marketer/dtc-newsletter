"""
Tests for content deduplication module.
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path


class TestGenerateContentHash:
    """Tests for generate_content_hash function."""

    def test_produces_consistent_hashes(self):
        """Should produce the same hash for the same content."""
        from execution.deduplication import generate_content_hash

        content = {"source": "reddit", "id": "abc123"}

        hash1 = generate_content_hash(content)
        hash2 = generate_content_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hex digest

    def test_different_sources_different_hashes(self):
        """Should produce different hashes for different sources with same ID."""
        from execution.deduplication import generate_content_hash

        reddit_content = {"source": "reddit", "id": "xyz789"}
        youtube_content = {"source": "youtube", "id": "xyz789"}

        reddit_hash = generate_content_hash(reddit_content)
        youtube_hash = generate_content_hash(youtube_content)

        assert reddit_hash != youtube_hash

    def test_uses_video_id_field(self):
        """Should use video_id field if id not present."""
        from execution.deduplication import generate_content_hash

        content = {"source": "youtube", "video_id": "dQw4w9WgXcQ"}

        hash_result = generate_content_hash(content)

        expected_content = {"source": "youtube", "id": "dQw4w9WgXcQ"}
        expected_hash = generate_content_hash(expected_content)

        assert hash_result == expected_hash

    def test_uses_post_id_field(self):
        """Should use post_id field if id not present."""
        from execution.deduplication import generate_content_hash

        content = {"source": "reddit", "post_id": "r3dd1t"}

        hash_result = generate_content_hash(content)

        # Should be equivalent to using id
        expected_content = {"source": "reddit", "id": "r3dd1t"}
        expected_hash = generate_content_hash(expected_content)

        assert hash_result == expected_hash

    def test_perplexity_uses_topic_and_date(self):
        """Should use topic_slug + date for Perplexity content."""
        from execution.deduplication import generate_content_hash

        content = {
            "source": "perplexity",
            "topic_slug": "dtc-trends",
            "fetched_at": "2026-01-31T12:00:00+00:00",
        }

        hash_result = generate_content_hash(content)

        # Same topic on same date should have same hash
        content2 = {
            "source": "perplexity",
            "topic_slug": "dtc-trends",
            "fetched_at": "2026-01-31T18:00:00+00:00",  # Different time, same date
        }
        hash2 = generate_content_hash(content2)

        assert hash_result == hash2

    def test_handles_missing_source(self):
        """Should use 'unknown' for missing source."""
        from execution.deduplication import generate_content_hash

        content = {"id": "test123"}

        hash_result = generate_content_hash(content)

        expected = {"source": "unknown", "id": "test123"}
        expected_hash = generate_content_hash(expected)

        assert hash_result == expected_hash


class TestIsDuplicate:
    """Tests for is_duplicate function."""

    def test_identifies_duplicate(self):
        """Should return True for content in seen_hashes."""
        from execution.deduplication import is_duplicate, generate_content_hash

        content = {"source": "reddit", "id": "abc123"}
        seen_hashes = {generate_content_hash(content)}

        assert is_duplicate(content, seen_hashes) is True

    def test_identifies_new_content(self):
        """Should return False for content not in seen_hashes."""
        from execution.deduplication import is_duplicate, generate_content_hash

        content = {"source": "reddit", "id": "abc123"}
        other_content = {"source": "reddit", "id": "xyz789"}
        seen_hashes = {generate_content_hash(other_content)}

        assert is_duplicate(content, seen_hashes) is False

    def test_empty_seen_hashes(self):
        """Should return False when seen_hashes is empty."""
        from execution.deduplication import is_duplicate

        content = {"source": "reddit", "id": "abc123"}

        assert is_duplicate(content, set()) is False


class TestLoadSeenHashes:
    """Tests for load_seen_hashes function."""

    def test_loads_hashes_from_reddit_cache(self, tmp_path):
        """Should load hashes from Reddit cache files."""
        from execution.deduplication import load_seen_hashes

        # Create Reddit cache directory and file
        reddit_dir = tmp_path / "reddit"
        reddit_dir.mkdir()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cache_file = reddit_dir / f"reddit_{today}.json"

        cache_data = {
            "metadata": {"source": "reddit"},
            "posts": [
                {"id": "post1", "title": "Test 1"},
                {"id": "post2", "title": "Test 2"},
            ],
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        seen = load_seen_hashes(cache_dirs=[reddit_dir], weeks_back=4)

        assert len(seen) == 2

    def test_loads_hashes_from_perplexity_cache(self, tmp_path):
        """Should load hashes from Perplexity cache files."""
        from execution.deduplication import load_seen_hashes

        perplexity_dir = tmp_path / "perplexity"
        perplexity_dir.mkdir()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cache_file = perplexity_dir / f"{today}_search_trends_dtc.json"

        cache_data = {
            "metadata": {"source": "perplexity", "topic_slug": "dtc"},
            "research": {
                "content": "Research content",
                "fetched_at": f"{today}T12:00:00+00:00",
            },
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        seen = load_seen_hashes(cache_dirs=[perplexity_dir], weeks_back=4)

        assert len(seen) == 1

    def test_excludes_old_files(self, tmp_path):
        """Should exclude files older than weeks_back."""
        from execution.deduplication import load_seen_hashes

        reddit_dir = tmp_path / "reddit"
        reddit_dir.mkdir()

        # Create old file (5 weeks ago)
        old_date = (datetime.now(timezone.utc) - timedelta(weeks=5)).strftime(
            "%Y-%m-%d"
        )
        old_file = reddit_dir / f"reddit_{old_date}.json"

        with open(old_file, "w") as f:
            json.dump({"posts": [{"id": "old_post"}]}, f)

        # Create recent file
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        recent_file = reddit_dir / f"reddit_{today}.json"

        with open(recent_file, "w") as f:
            json.dump({"posts": [{"id": "recent_post"}]}, f)

        seen = load_seen_hashes(cache_dirs=[reddit_dir], weeks_back=4)

        # Should only have the recent post
        assert len(seen) == 1

    def test_handles_missing_directory(self, tmp_path):
        """Should handle missing cache directory gracefully."""
        from execution.deduplication import load_seen_hashes

        nonexistent = tmp_path / "nonexistent"

        seen = load_seen_hashes(cache_dirs=[nonexistent], weeks_back=4)

        assert seen == set()

    def test_handles_invalid_json(self, tmp_path):
        """Should skip files with invalid JSON."""
        from execution.deduplication import load_seen_hashes

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Invalid JSON file
        invalid_file = cache_dir / f"reddit_{today}_invalid.json"
        invalid_file.write_text("not valid json {")

        seen = load_seen_hashes(cache_dirs=[cache_dir], weeks_back=4)

        assert seen == set()


class TestFilterDuplicates:
    """Tests for filter_duplicates function."""

    def test_filters_known_content(self, tmp_path):
        """Should remove content that exists in cache."""
        from execution.deduplication import filter_duplicates

        # Create cache with known content
        cache_dir = tmp_path / "reddit"
        cache_dir.mkdir()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cache_file = cache_dir / f"reddit_{today}.json"

        with open(cache_file, "w") as f:
            json.dump({"posts": [{"id": "known_post"}]}, f)

        # Content to filter
        contents = [
            {"source": "reddit", "id": "known_post"},  # Should be filtered
            {"source": "reddit", "id": "new_post"},  # Should remain
        ]

        filtered, duplicate_count = filter_duplicates(
            contents, weeks_back=4, cache_dirs=[cache_dir]
        )

        assert len(filtered) == 1
        assert filtered[0]["id"] == "new_post"
        assert duplicate_count == 1

    def test_returns_all_when_no_duplicates(self, tmp_path):
        """Should return all content when no duplicates exist."""
        from execution.deduplication import filter_duplicates

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        contents = [
            {"source": "reddit", "id": "post1"},
            {"source": "reddit", "id": "post2"},
        ]

        filtered, duplicate_count = filter_duplicates(contents, cache_dirs=[empty_dir])

        assert len(filtered) == 2
        assert duplicate_count == 0

    def test_handles_empty_input(self, tmp_path):
        """Should handle empty content list."""
        from execution.deduplication import filter_duplicates

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        filtered, duplicate_count = filter_duplicates([], cache_dirs=[empty_dir])

        assert filtered == []
        assert duplicate_count == 0


class TestAddToSeen:
    """Tests for add_to_seen function."""

    def test_adds_content_hashes(self):
        """Should add content hashes to the seen set."""
        from execution.deduplication import add_to_seen, generate_content_hash

        seen = set()
        contents = [
            {"source": "reddit", "id": "post1"},
            {"source": "reddit", "id": "post2"},
        ]

        result = add_to_seen(contents, seen)

        assert len(result) == 2
        assert generate_content_hash(contents[0]) in result
        assert generate_content_hash(contents[1]) in result

    def test_modifies_set_in_place(self):
        """Should modify the original set."""
        from execution.deduplication import add_to_seen

        seen = set()
        contents = [{"source": "reddit", "id": "post1"}]

        add_to_seen(contents, seen)

        assert len(seen) == 1


class TestGetDedupStats:
    """Tests for get_dedup_stats function."""

    def test_returns_stats_by_source(self, tmp_path):
        """Should return counts per source."""
        from execution.deduplication import get_dedup_stats

        # Create Reddit cache
        reddit_dir = tmp_path / "reddit"
        reddit_dir.mkdir()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cache_file = reddit_dir / f"reddit_{today}.json"

        with open(cache_file, "w") as f:
            json.dump({"posts": [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}]}, f)

        stats = get_dedup_stats(cache_dirs=[reddit_dir], weeks_back=4)

        assert stats["total_hashes"] == 3
        assert stats["by_source"]["reddit"] == 3
        assert stats["weeks_back"] == 4

    def test_handles_empty_cache(self, tmp_path):
        """Should handle empty or missing cache directories."""
        from execution.deduplication import get_dedup_stats

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        stats = get_dedup_stats(cache_dirs=[empty_dir], weeks_back=4)

        assert stats["total_hashes"] == 0


class TestExtractFileDate:
    """Tests for _extract_file_date helper function."""

    def test_extracts_date_from_reddit_format(self, tmp_path):
        """Should extract date from reddit_YYYY-MM-DD.json format."""
        from execution.deduplication import _extract_file_date

        filepath = tmp_path / "reddit_2026-01-31.json"

        result = _extract_file_date(filepath)

        assert result == "2026-01-31"

    def test_extracts_date_from_perplexity_format(self, tmp_path):
        """Should extract date from YYYY-MM-DD_... format."""
        from execution.deduplication import _extract_file_date

        filepath = tmp_path / "2026-01-31_search_trends_topic.json"

        result = _extract_file_date(filepath)

        assert result == "2026-01-31"

    def test_returns_none_for_invalid_format(self, tmp_path):
        """Should return None for files without parseable date."""
        from execution.deduplication import _extract_file_date

        filepath = tmp_path / "some_random_file.json"

        result = _extract_file_date(filepath)

        assert result is None
