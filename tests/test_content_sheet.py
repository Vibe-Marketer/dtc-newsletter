"""
Tests for content sheet module.
"""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from execution.content_sheet import (
    generate_content_sheet,
    save_csv,
    save_json,
    generate_and_save,
    load_content_sheet,
    get_content_sheet_stats,
    CSV_COLUMNS,
)


# Sample test data
SAMPLE_CONTENT = [
    {
        "source": "reddit",
        "id": "abc123",
        "title": "How I made $50k in 3 months",
        "url": "https://reddit.com/r/shopify/abc123",
        "author": "test_user",
        "upvotes": 500,
        "outlier_score": 7.5,
        "published_at": "2026-01-30T12:00:00Z",
    },
    {
        "source": "youtube",
        "id": "xyz789",
        "title": "5 Secret Tips for E-commerce",
        "url": "https://youtube.com/watch?v=xyz789",
        "channel_name": "TestChannel",
        "views": 100000,
        "outlier_score": 5.2,
        "published_at": "2026-01-28T10:00:00Z",
    },
]


class TestGenerateContentSheet:
    """Tests for generate_content_sheet function."""

    def test_returns_enriched_list(self):
        """Should return enriched list with virality analysis."""
        result = generate_content_sheet(SAMPLE_CONTENT)

        assert len(result) == len(SAMPLE_CONTENT)
        assert all("virality_analysis" in item for item in result)

    def test_adds_virality_analysis(self):
        """Should add virality_analysis dict."""
        result = generate_content_sheet(SAMPLE_CONTENT)

        for item in result:
            virality = item.get("virality_analysis", {})
            assert "hook_analysis" in virality
            assert "emotional_triggers" in virality
            assert "virality_confidence" in virality

    def test_flattens_virality_fields(self):
        """Should flatten key virality fields for CSV."""
        result = generate_content_sheet(SAMPLE_CONTENT)

        for item in result:
            assert "hook_type" in item
            assert "emotional_triggers" in item  # Flattened string
            assert "virality_confidence" in item
            assert "replication_notes" in item

    def test_without_virality(self):
        """Should skip virality when include_virality=False."""
        result = generate_content_sheet(SAMPLE_CONTENT, include_virality=False)

        for item in result:
            assert "virality_analysis" not in item

    def test_preserves_original_fields(self):
        """Should preserve original content fields."""
        result = generate_content_sheet(SAMPLE_CONTENT)

        assert result[0]["title"] == SAMPLE_CONTENT[0]["title"]
        assert result[0]["outlier_score"] == SAMPLE_CONTENT[0]["outlier_score"]

    def test_empty_input(self):
        """Should handle empty input."""
        result = generate_content_sheet([])
        assert result == []


class TestSaveCSV:
    """Tests for save_csv function."""

    def test_creates_csv_file(self):
        """Should create CSV file in output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            enriched = generate_content_sheet(SAMPLE_CONTENT)

            filepath = save_csv(enriched, output_dir=output_dir)

            assert filepath.exists()
            assert filepath.suffix == ".csv"

    def test_csv_has_headers(self):
        """CSV should have correct headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            enriched = generate_content_sheet(SAMPLE_CONTENT)

            filepath = save_csv(enriched, output_dir=output_dir)

            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                assert set(reader.fieldnames) == set(CSV_COLUMNS)

    def test_csv_contains_data(self):
        """CSV should contain content data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            enriched = generate_content_sheet(SAMPLE_CONTENT)

            filepath = save_csv(enriched, output_dir=output_dir)

            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == len(SAMPLE_CONTENT)
                assert rows[0]["title"] == SAMPLE_CONTENT[0]["title"]

    def test_csv_outlier_score_formatted(self):
        """Outlier score should be formatted to 2 decimal places."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            enriched = generate_content_sheet(SAMPLE_CONTENT)

            filepath = save_csv(enriched, output_dir=output_dir)

            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                row = next(reader)
                # Should be "7.50" not "7.5"
                assert row["outlier_score"] == "7.50"

    def test_custom_filename(self):
        """Should support custom filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            enriched = generate_content_sheet(SAMPLE_CONTENT)

            filepath = save_csv(enriched, filename="custom.csv", output_dir=output_dir)

            assert filepath.name == "custom.csv"


class TestSaveJSON:
    """Tests for save_json function."""

    def test_creates_json_file(self):
        """Should create JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            enriched = generate_content_sheet(SAMPLE_CONTENT)

            filepath = save_json(enriched, output_dir=output_dir)

            assert filepath.exists()
            assert filepath.suffix == ".json"

    def test_json_has_metadata(self):
        """JSON should have metadata section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            enriched = generate_content_sheet(SAMPLE_CONTENT)

            filepath = save_json(enriched, output_dir=output_dir)

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

                assert "metadata" in data
                assert "generated_at" in data["metadata"]
                assert "total_items" in data["metadata"]
                assert "sources" in data["metadata"]

    def test_json_contains_contents(self):
        """JSON should contain contents array."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            enriched = generate_content_sheet(SAMPLE_CONTENT)

            filepath = save_json(enriched, output_dir=output_dir)

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

                assert "contents" in data
                assert len(data["contents"]) == len(SAMPLE_CONTENT)

    def test_json_preserves_virality_analysis(self):
        """JSON should preserve full virality analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            enriched = generate_content_sheet(SAMPLE_CONTENT)

            filepath = save_json(enriched, output_dir=output_dir)

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

                for item in data["contents"]:
                    assert "virality_analysis" in item
                    assert "hook_analysis" in item["virality_analysis"]

    def test_sources_list_unique(self):
        """Sources list should contain unique values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            enriched = generate_content_sheet(SAMPLE_CONTENT)

            filepath = save_json(enriched, output_dir=output_dir)

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                sources = data["metadata"]["sources"]

                # Should have reddit and youtube
                assert "reddit" in sources
                assert "youtube" in sources


class TestGenerateAndSave:
    """Tests for generate_and_save function."""

    def test_creates_both_files(self):
        """Should create both CSV and JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            csv_path, json_path = generate_and_save(
                SAMPLE_CONTENT, output_dir=output_dir
            )

            assert csv_path.exists()
            assert json_path.exists()

    def test_default_filenames(self):
        """Should use default filenames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            csv_path, json_path = generate_and_save(
                SAMPLE_CONTENT, output_dir=output_dir
            )

            assert csv_path.name == "content_sheet.csv"
            assert json_path.name == "content_sheet.json"

    def test_custom_filenames(self):
        """Should support custom filenames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            csv_path, json_path = generate_and_save(
                SAMPLE_CONTENT,
                csv_filename="custom.csv",
                json_filename="custom.json",
                output_dir=output_dir,
            )

            assert csv_path.name == "custom.csv"
            assert json_path.name == "custom.json"

    def test_content_matches_between_formats(self):
        """Content should match between CSV and JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            csv_path, json_path = generate_and_save(
                SAMPLE_CONTENT, output_dir=output_dir
            )

            # Check counts match
            with open(csv_path, "r", encoding="utf-8") as f:
                csv_rows = list(csv.DictReader(f))

            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            assert len(csv_rows) == len(json_data["contents"])


class TestLoadContentSheet:
    """Tests for load_content_sheet function."""

    def test_loads_json_file(self):
        """Should load content from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            enriched = generate_content_sheet(SAMPLE_CONTENT)

            json_path = save_json(enriched, output_dir=output_dir)

            loaded = load_content_sheet(json_path)

            assert len(loaded) == len(SAMPLE_CONTENT)
            assert loaded[0]["title"] == SAMPLE_CONTENT[0]["title"]

    def test_raises_for_missing_file(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_content_sheet(Path("/nonexistent/file.json"))


class TestGetContentSheetStats:
    """Tests for get_content_sheet_stats function."""

    def test_returns_total_items(self):
        """Should return total item count."""
        enriched = generate_content_sheet(SAMPLE_CONTENT)
        stats = get_content_sheet_stats(enriched)

        assert stats["total_items"] == len(SAMPLE_CONTENT)

    def test_counts_by_source(self):
        """Should count items by source."""
        enriched = generate_content_sheet(SAMPLE_CONTENT)
        stats = get_content_sheet_stats(enriched)

        assert stats["by_source"]["reddit"] == 1
        assert stats["by_source"]["youtube"] == 1

    def test_score_range(self):
        """Should calculate score range."""
        enriched = generate_content_sheet(SAMPLE_CONTENT)
        stats = get_content_sheet_stats(enriched)

        assert stats["score_range"]["min"] == 5.2
        assert stats["score_range"]["max"] == 7.5

    def test_avg_score(self):
        """Should calculate average score."""
        enriched = generate_content_sheet(SAMPLE_CONTENT)
        stats = get_content_sheet_stats(enriched)

        expected_avg = (7.5 + 5.2) / 2
        assert abs(stats["avg_score"] - expected_avg) < 0.01

    def test_empty_input(self):
        """Should handle empty input."""
        stats = get_content_sheet_stats([])

        assert stats["total_items"] == 0
        assert stats["by_source"] == {}
        assert stats["avg_score"] == 0


class TestCSVColumns:
    """Tests for CSV_COLUMNS constant."""

    def test_columns_defined(self):
        """CSV columns should be defined."""
        assert CSV_COLUMNS is not None
        assert len(CSV_COLUMNS) > 0

    def test_required_columns_present(self):
        """Required columns should be present."""
        required = ["source", "id", "title", "url", "outlier_score"]
        for col in required:
            assert col in CSV_COLUMNS

    def test_virality_columns_present(self):
        """Virality-related columns should be present."""
        virality_cols = ["hook_type", "emotional_triggers", "virality_confidence"]
        for col in virality_cols:
            assert col in CSV_COLUMNS
