"""
Tests for affiliate discovery module.
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestClassifyCommission:
    """Tests for classify_commission function."""

    def test_recurring_excellent_at_20_percent(self):
        """20% recurring should be excellent."""
        from execution.affiliate_discovery import classify_commission

        assert classify_commission(20.0, is_recurring=True) == "excellent"

    def test_recurring_excellent_above_20_percent(self):
        """Above 20% recurring should be excellent."""
        from execution.affiliate_discovery import classify_commission

        assert classify_commission(30.0, is_recurring=True) == "excellent"
        assert classify_commission(50.0, is_recurring=True) == "excellent"

    def test_recurring_good_at_10_percent(self):
        """10% recurring should be good."""
        from execution.affiliate_discovery import classify_commission

        assert classify_commission(10.0, is_recurring=True) == "good"

    def test_recurring_good_between_10_and_20(self):
        """Between 10-20% recurring should be good."""
        from execution.affiliate_discovery import classify_commission

        assert classify_commission(15.0, is_recurring=True) == "good"
        assert classify_commission(19.9, is_recurring=True) == "good"

    def test_recurring_mediocre_below_10(self):
        """Below 10% recurring should be mediocre."""
        from execution.affiliate_discovery import classify_commission

        assert classify_commission(9.9, is_recurring=True) == "mediocre"
        assert classify_commission(5.0, is_recurring=True) == "mediocre"
        assert classify_commission(0.0, is_recurring=True) == "mediocre"

    def test_onetime_good_at_30_percent(self):
        """30% one-time should be good."""
        from execution.affiliate_discovery import classify_commission

        assert classify_commission(30.0, is_recurring=False) == "good"

    def test_onetime_good_above_30_percent(self):
        """Above 30% one-time should be good."""
        from execution.affiliate_discovery import classify_commission

        assert classify_commission(40.0, is_recurring=False) == "good"
        assert classify_commission(50.0, is_recurring=False) == "good"

    def test_onetime_mediocre_at_15_percent(self):
        """15% one-time should be mediocre."""
        from execution.affiliate_discovery import classify_commission

        assert classify_commission(15.0, is_recurring=False) == "mediocre"

    def test_onetime_mediocre_between_15_and_30(self):
        """Between 15-30% one-time should be mediocre."""
        from execution.affiliate_discovery import classify_commission

        assert classify_commission(20.0, is_recurring=False) == "mediocre"
        assert classify_commission(29.9, is_recurring=False) == "mediocre"

    def test_onetime_poor_below_15(self):
        """Below 15% one-time should be poor."""
        from execution.affiliate_discovery import classify_commission

        assert classify_commission(14.9, is_recurring=False) == "poor"
        assert classify_commission(10.0, is_recurring=False) == "poor"
        assert classify_commission(0.0, is_recurring=False) == "poor"


class TestParseCommissionRate:
    """Tests for parse_commission_rate function."""

    def test_parses_percentage(self):
        """Should extract percentage values."""
        from execution.affiliate_discovery import parse_commission_rate

        assert parse_commission_rate("20%") == 20.0
        assert parse_commission_rate("20 %") == 20.0
        assert parse_commission_rate("15.5%") == 15.5

    def test_parses_percentage_range(self):
        """Should extract first number from range."""
        from execution.affiliate_discovery import parse_commission_rate

        assert parse_commission_rate("30% - 50%") == 30.0

    def test_flat_fee_returns_zero(self):
        """Flat fees should return 0 (can't compare to percentage thresholds)."""
        from execution.affiliate_discovery import parse_commission_rate

        assert parse_commission_rate("$50") == 0.0
        assert parse_commission_rate("$100 per sale") == 0.0

    def test_extracts_number_from_text(self):
        """Should extract number from descriptive text."""
        from execution.affiliate_discovery import parse_commission_rate

        assert parse_commission_rate("up to 25% commission") == 25.0

    def test_returns_zero_for_no_number(self):
        """Should return 0 if no number found."""
        from execution.affiliate_discovery import parse_commission_rate

        assert parse_commission_rate("varies") == 0.0
        assert parse_commission_rate("") == 0.0


class TestAffiliateProgramModel:
    """Tests for AffiliateProgram Pydantic model."""

    def test_valid_affiliate_program(self):
        """Should validate correct affiliate data."""
        from execution.affiliate_discovery import AffiliateProgram

        program = AffiliateProgram(
            name="Test Program",
            company="Test Company",
            commission_rate="20%",
            commission_type="percentage",
            is_recurring=True,
            product_description="A test product",
            topic_fit="Fits the topic well",
            network="ShareASale",
            signup_accessible=True,
        )

        assert program.name == "Test Program"
        assert program.commission_type == "percentage"
        assert program.network == "ShareASale"

    def test_rejects_invalid_commission_type(self):
        """Should reject invalid commission_type."""
        from execution.affiliate_discovery import AffiliateProgram
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AffiliateProgram(
                name="Test",
                company="Test",
                commission_rate="20%",
                commission_type="invalid",  # Must be percentage or flat_fee
                is_recurring=True,
                product_description="Test",
                topic_fit="Test",
                network="direct",
                signup_accessible=True,
            )

    def test_rejects_invalid_network(self):
        """Should reject invalid network."""
        from execution.affiliate_discovery import AffiliateProgram
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AffiliateProgram(
                name="Test",
                company="Test",
                commission_rate="20%",
                commission_type="percentage",
                is_recurring=True,
                product_description="Test",
                topic_fit="Test",
                network="InvalidNetwork",  # Must be valid network
                signup_accessible=True,
            )


class TestDiscoverAffiliates:
    """Tests for discover_affiliates function."""

    def test_returns_structured_result(self):
        """Should return AffiliateDiscoveryResult with affiliates."""
        from execution.affiliate_discovery import discover_affiliates

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(
            [
                {
                    "name": "Klaviyo Partner",
                    "company": "Klaviyo",
                    "commission_rate": "20%",
                    "commission_type": "percentage",
                    "is_recurring": True,
                    "product_description": "Email marketing for e-commerce",
                    "topic_fit": "Perfect for email marketing newsletters",
                    "network": "PartnerStack",
                    "signup_accessible": True,
                }
            ]
        )
        mock_completion.citations = ["https://example.com/source1"]

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.affiliate_discovery.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = mock_completion

                result = discover_affiliates("email marketing")

        assert result.topic == "email marketing"
        assert len(result.affiliates) == 1
        assert result.affiliates[0].name == "Klaviyo Partner"
        assert result.affiliates[0].commission_rate == "20%"
        assert result.search_citations == ["https://example.com/source1"]

    def test_includes_newsletter_context_in_prompt(self):
        """Should include newsletter context in API call."""
        from execution.affiliate_discovery import discover_affiliates

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "[]"
        mock_completion.citations = []

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.affiliate_discovery.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = mock_completion

                discover_affiliates(
                    "shipping optimization",
                    newsletter_context="This week's newsletter focuses on reducing shipping costs",
                )

        call_args = mock_client.chat.completions.create.call_args
        prompt = call_args.kwargs["messages"][1]["content"]
        assert "This week's newsletter focuses on reducing shipping costs" in prompt

    def test_handles_markdown_code_block_response(self):
        """Should handle response wrapped in markdown code block."""
        from execution.affiliate_discovery import discover_affiliates

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = """```json
[
    {
        "name": "Test Program",
        "company": "Test Co",
        "commission_rate": "15%",
        "commission_type": "percentage",
        "is_recurring": false,
        "product_description": "Test product",
        "topic_fit": "Test fit",
        "network": "direct",
        "signup_accessible": true
    }
]
```"""
        mock_completion.citations = []

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.affiliate_discovery.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = mock_completion

                result = discover_affiliates("test topic")

        assert len(result.affiliates) == 1
        assert result.affiliates[0].name == "Test Program"

    def test_retries_on_malformed_json(self):
        """Should retry once on malformed JSON response."""
        from execution.affiliate_discovery import discover_affiliates

        # First response is malformed, second is valid
        malformed_response = MagicMock()
        malformed_response.choices = [MagicMock()]
        malformed_response.choices[0].message.content = "Not valid JSON"
        malformed_response.citations = []

        valid_response = MagicMock()
        valid_response.choices = [MagicMock()]
        valid_response.choices[0].message.content = "[]"
        valid_response.citations = []

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.affiliate_discovery.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.side_effect = [
                    malformed_response,
                    valid_response,
                ]

                result = discover_affiliates("test topic")

        assert result.affiliates == []
        assert mock_client.chat.completions.create.call_count == 2

    def test_raises_on_repeated_malformed_json(self):
        """Should raise RuntimeError after retry fails."""
        from execution.affiliate_discovery import discover_affiliates

        malformed_response = MagicMock()
        malformed_response.choices = [MagicMock()]
        malformed_response.choices[0].message.content = "Not valid JSON"
        malformed_response.citations = []

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.affiliate_discovery.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = malformed_response

                with pytest.raises(RuntimeError) as exc_info:
                    discover_affiliates("test topic")

        assert "Failed to parse affiliate response" in str(exc_info.value)

    def test_skips_invalid_affiliates_in_response(self):
        """Should skip invalid affiliates and keep valid ones."""
        from execution.affiliate_discovery import discover_affiliates

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(
            [
                {
                    "name": "Valid Program",
                    "company": "Valid Co",
                    "commission_rate": "20%",
                    "commission_type": "percentage",
                    "is_recurring": True,
                    "product_description": "Valid product",
                    "topic_fit": "Valid fit",
                    "network": "Awin",
                    "signup_accessible": True,
                },
                {
                    "name": "Invalid",
                    # Missing required fields
                },
            ]
        )
        mock_completion.citations = []

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.affiliate_discovery.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.return_value = mock_completion

                result = discover_affiliates("test topic")

        assert len(result.affiliates) == 1
        assert result.affiliates[0].name == "Valid Program"

    def test_raises_on_api_error(self):
        """Should raise RuntimeError on API failure."""
        from execution.affiliate_discovery import discover_affiliates

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("execution.affiliate_discovery.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.side_effect = Exception("API Error")

                with pytest.raises(RuntimeError) as exc_info:
                    discover_affiliates("test topic")

        assert "Perplexity API error" in str(exc_info.value)

    def test_raises_on_missing_api_key(self):
        """Should raise ValueError if API key not set."""
        from execution.affiliate_discovery import discover_affiliates

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                discover_affiliates("test topic")

        assert "PERPLEXITY_API_KEY" in str(exc_info.value)


class TestSaveAffiliates:
    """Tests for save_affiliates function."""

    def test_saves_to_file(self, tmp_path):
        """Should save affiliate results to JSON file."""
        from execution.affiliate_discovery import (
            AffiliateDiscoveryResult,
            AffiliateProgram,
            save_affiliates,
        )

        program = AffiliateProgram(
            name="Test Program",
            company="Test Co",
            commission_rate="20%",
            commission_type="percentage",
            is_recurring=True,
            product_description="Test",
            topic_fit="Test fit",
            network="direct",
            signup_accessible=True,
        )
        result = AffiliateDiscoveryResult(
            affiliates=[program],
            search_citations=["https://example.com"],
            topic="email marketing",
        )

        filepath = save_affiliates(result, cache_dir=tmp_path)

        assert filepath.exists()
        assert filepath.suffix == ".json"
        assert "email-marketing" in filepath.name
        assert "-affiliates" in filepath.name

    def test_creates_directory_if_missing(self, tmp_path):
        """Should create cache directory if it doesn't exist."""
        from execution.affiliate_discovery import (
            AffiliateDiscoveryResult,
            save_affiliates,
        )

        cache_dir = tmp_path / "nested" / "cache"
        result = AffiliateDiscoveryResult(
            affiliates=[],
            search_citations=[],
            topic="test topic",
        )

        filepath = save_affiliates(result, cache_dir=cache_dir)

        assert filepath.exists()
        assert cache_dir.exists()

    def test_includes_metadata(self, tmp_path):
        """Should include metadata in saved file."""
        from execution.affiliate_discovery import (
            AffiliateDiscoveryResult,
            save_affiliates,
        )

        result = AffiliateDiscoveryResult(
            affiliates=[],
            search_citations=[],
            topic="shipping optimization",
        )

        filepath = save_affiliates(result, cache_dir=tmp_path)

        with open(filepath) as f:
            data = json.load(f)

        assert "metadata" in data
        assert data["metadata"]["source"] == "perplexity"
        assert data["metadata"]["topic"] == "shipping optimization"
        assert data["metadata"]["ttl_hours"] == 24
        assert "saved_at" in data["metadata"]

    def test_includes_date_prefix(self, tmp_path):
        """Should include date prefix in filename."""
        from execution.affiliate_discovery import (
            AffiliateDiscoveryResult,
            save_affiliates,
        )

        result = AffiliateDiscoveryResult(
            affiliates=[],
            search_citations=[],
            topic="test",
        )

        filepath = save_affiliates(result, cache_dir=tmp_path)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert filepath.name.startswith(today)


class TestLoadAffiliates:
    """Tests for load_affiliates function."""

    def test_loads_from_file(self, tmp_path):
        """Should load affiliate results from cache file."""
        from execution.affiliate_discovery import (
            AffiliateDiscoveryResult,
            AffiliateProgram,
            save_affiliates,
            load_affiliates,
        )

        program = AffiliateProgram(
            name="Loaded Program",
            company="Loaded Co",
            commission_rate="25%",
            commission_type="percentage",
            is_recurring=False,
            product_description="Loaded product",
            topic_fit="Loaded fit",
            network="Impact",
            signup_accessible=True,
        )
        original = AffiliateDiscoveryResult(
            affiliates=[program],
            search_citations=["https://example.com"],
            topic="loaded topic",
        )

        filepath = save_affiliates(original, cache_dir=tmp_path)
        loaded = load_affiliates(filepath)

        assert loaded.topic == "loaded topic"
        assert len(loaded.affiliates) == 1
        assert loaded.affiliates[0].name == "Loaded Program"

    def test_raises_on_missing_file(self, tmp_path):
        """Should raise FileNotFoundError if file doesn't exist."""
        from execution.affiliate_discovery import load_affiliates

        with pytest.raises(FileNotFoundError):
            load_affiliates(tmp_path / "nonexistent.json")


class TestGetCachedAffiliates:
    """Tests for get_cached_affiliates function."""

    def test_returns_cached_result(self, tmp_path):
        """Should return cached result if available and not expired."""
        from execution.affiliate_discovery import (
            AffiliateDiscoveryResult,
            save_affiliates,
            get_cached_affiliates,
        )

        result = AffiliateDiscoveryResult(
            affiliates=[],
            search_citations=[],
            topic="email marketing",
        )
        save_affiliates(result, cache_dir=tmp_path)

        cached = get_cached_affiliates("email marketing", cache_dir=tmp_path)

        assert cached is not None
        assert cached.topic == "email marketing"

    def test_returns_none_for_missing_cache(self, tmp_path):
        """Should return None if no cached result found."""
        from execution.affiliate_discovery import get_cached_affiliates

        cached = get_cached_affiliates("nonexistent topic", cache_dir=tmp_path)

        assert cached is None

    def test_returns_none_for_missing_directory(self, tmp_path):
        """Should return None if cache directory doesn't exist."""
        from execution.affiliate_discovery import get_cached_affiliates

        nonexistent = tmp_path / "nonexistent"
        cached = get_cached_affiliates("test", cache_dir=nonexistent)

        assert cached is None

    def test_respects_max_age(self, tmp_path):
        """Should return None if cache is expired."""
        from execution.affiliate_discovery import get_cached_affiliates

        # Create an old cache file manually
        old_date = (datetime.now(timezone.utc) - timedelta(hours=25)).strftime(
            "%Y-%m-%d"
        )
        old_saved_at = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()

        data = {
            "metadata": {
                "source": "perplexity",
                "topic": "old topic",
                "saved_at": old_saved_at,
                "ttl_hours": 24,
            },
            "result": {
                "affiliates": [],
                "search_citations": [],
                "topic": "old topic",
            },
        }

        filepath = tmp_path / f"{old_date}-old-topic-affiliates.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        cached = get_cached_affiliates(
            "old topic", cache_dir=tmp_path, max_age_hours=24
        )

        assert cached is None
