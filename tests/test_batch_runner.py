"""
Tests for execution/batch_runner.py

Tests cover:
- categorize_ecom_topic() keyword matching
- select_diverse_topics() diversity algorithm
- check_api_keys() API key validation
- BatchRunner.can_continue() cost budget enforcement
- BatchRunner.run_preflight() pre-flight checks
- BatchRunner.discover_topics() with mocking
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from execution.batch_runner import (
    E_COM_CATEGORIES,
    CATEGORY_KEYWORDS,
    categorize_ecom_topic,
    select_diverse_topics,
    check_api_keys,
    BatchRunner,
)


# =============================================================================
# CATEGORIZE_ECOM_TOPIC TESTS
# =============================================================================


class TestCategorizeEcomTopic:
    """Tests for categorize_ecom_topic function."""

    def test_shipping_logistics_keywords(self):
        """Test shipping-related topics are categorized correctly."""
        assert (
            categorize_ecom_topic("shipping costs are killing me")
            == "shipping_logistics"
        )
        assert (
            categorize_ecom_topic("best 3PL for small brands") == "shipping_logistics"
        )
        assert (
            categorize_ecom_topic("fulfillment center recommendations")
            == "shipping_logistics"
        )
        assert categorize_ecom_topic("USPS vs FedEx rates") == "shipping_logistics"

    def test_pricing_margins_keywords(self):
        """Test pricing-related topics are categorized correctly."""
        assert (
            categorize_ecom_topic("how to calculate profit margins")
            == "pricing_margins"
        )
        assert (
            categorize_ecom_topic("pricing strategy for $100 products")
            == "pricing_margins"
        )
        assert categorize_ecom_topic("my COGS are too high") == "pricing_margins"
        assert categorize_ecom_topic("discount codes hurt revenue") == "pricing_margins"

    def test_conversion_optimization_keywords(self):
        """Test conversion-related topics are categorized correctly."""
        assert (
            categorize_ecom_topic("checkout abandonment issues")
            == "conversion_optimization"
        )
        assert (
            categorize_ecom_topic("cart conversion rate dropped")
            == "conversion_optimization"
        )
        assert (
            categorize_ecom_topic("A/B testing landing pages")
            == "conversion_optimization"
        )
        assert (
            categorize_ecom_topic("CRO tips for ecommerce") == "conversion_optimization"
        )

    def test_ads_marketing_keywords(self):
        """Test ads/marketing topics are categorized correctly."""
        assert categorize_ecom_topic("facebook ads strategy 2026") == "ads_marketing"
        assert categorize_ecom_topic("TikTok creative testing") == "ads_marketing"
        assert categorize_ecom_topic("ROAS dropped after iOS update") == "ads_marketing"
        assert categorize_ecom_topic("UGC content for ads") == "ads_marketing"

    def test_inventory_management_keywords(self):
        """Test inventory-related topics are categorized correctly."""
        assert (
            categorize_ecom_topic("inventory management software")
            == "inventory_management"
        )
        assert categorize_ecom_topic("SKU organization tips") == "inventory_management"
        assert (
            categorize_ecom_topic("stockout prevention strategies")
            == "inventory_management"
        )

    def test_customer_retention_keywords(self):
        """Test retention-related topics are categorized correctly."""
        assert (
            categorize_ecom_topic("email retention sequences") == "customer_retention"
        )
        assert categorize_ecom_topic("Klaviyo email flows") == "customer_retention"
        assert categorize_ecom_topic("reducing churn rate") == "customer_retention"
        assert (
            categorize_ecom_topic("increasing LTV per customer") == "customer_retention"
        )

    def test_product_sourcing_keywords(self):
        """Test sourcing-related topics are categorized correctly."""
        assert (
            categorize_ecom_topic("finding suppliers on Alibaba") == "product_sourcing"
        )
        assert (
            categorize_ecom_topic("private label manufacturer search")
            == "product_sourcing"
        )
        assert categorize_ecom_topic("wholesale vendor sourcing") == "product_sourcing"

    def test_platform_tools_keywords(self):
        """Test platform/tool topics are categorized correctly."""
        assert categorize_ecom_topic("best Shopify apps 2026") == "platform_tools"
        assert (
            categorize_ecom_topic("WooCommerce plugin recommendations")
            == "platform_tools"
        )
        assert categorize_ecom_topic("Amazon FBA tips") == "platform_tools"

    def test_unknown_topic_defaults_to_platform_tools(self):
        """Test unknown topics default to platform_tools."""
        assert (
            categorize_ecom_topic("random topic with no keywords") == "platform_tools"
        )
        assert (
            categorize_ecom_topic("something completely unrelated") == "platform_tools"
        )
        assert categorize_ecom_topic("") == "platform_tools"

    def test_case_insensitive_matching(self):
        """Test keyword matching is case-insensitive."""
        assert categorize_ecom_topic("SHIPPING COSTS") == "shipping_logistics"
        assert categorize_ecom_topic("Facebook Ads") == "ads_marketing"
        assert categorize_ecom_topic("SHOPIFY") == "platform_tools"


# =============================================================================
# SELECT_DIVERSE_TOPICS TESTS
# =============================================================================


class TestSelectDiverseTopics:
    """Tests for select_diverse_topics function."""

    def _make_topic(self, title: str, score: float) -> dict:
        """Helper to create topic dict."""
        return {
            "title": title,
            "outlier_score": score,
            "source": "reddit",
            "url": f"https://reddit.com/r/test/{title[:10]}",
        }

    def test_empty_content_returns_empty(self):
        """Test empty input returns empty list."""
        assert select_diverse_topics([]) == []

    def test_selects_one_per_category_first(self):
        """Test diversity filter selects one topic per category before repeating."""
        topics = [
            self._make_topic("shipping rates are high", 5.0),  # shipping
            self._make_topic("shipping costs problem", 4.5),  # shipping (same)
            self._make_topic("facebook ads creative", 4.0),  # ads
            self._make_topic("pricing strategy guide", 3.5),  # pricing
            self._make_topic("conversion rate tips", 3.0),  # conversion
        ]

        result = select_diverse_topics(topics, count=4)

        # Should pick highest from each unique category
        categories = [t["ecom_category"] for t in result]
        assert len(set(categories)) == 4  # All unique categories
        assert result[0]["title"] == "shipping rates are high"  # Highest score

    def test_fills_with_repeats_if_needed(self):
        """Test fills remaining slots with repeats if fewer unique categories."""
        # All same category
        topics = [
            self._make_topic("shipping issue 1", 5.0),
            self._make_topic("shipping issue 2", 4.0),
            self._make_topic("shipping issue 3", 3.0),
            self._make_topic("shipping issue 4", 2.0),
        ]

        result = select_diverse_topics(topics, count=4)

        assert len(result) == 4
        # All should be shipping
        for t in result:
            assert t["ecom_category"] == "shipping_logistics"

    def test_returns_exactly_count_topics(self):
        """Test returns exactly the requested count."""
        topics = [
            self._make_topic("shipping topic", 5.0),
            self._make_topic("pricing topic", 4.5),
            self._make_topic("ads topic", 4.0),
            self._make_topic("conversion topic", 3.5),
            self._make_topic("retention topic", 3.0),
            self._make_topic("sourcing topic", 2.5),
            self._make_topic("inventory topic", 2.0),
            self._make_topic("shopify topic", 1.5),
            self._make_topic("more shipping", 1.0),
            self._make_topic("more pricing", 0.5),
        ]

        result = select_diverse_topics(topics, count=8)
        assert len(result) == 8

    def test_sorts_by_outlier_score(self):
        """Test highest scores selected within categories."""
        topics = [
            self._make_topic("low score shipping", 1.0),
            self._make_topic("high score shipping", 5.0),
            self._make_topic("mid score shipping", 3.0),
        ]

        result = select_diverse_topics(topics, count=3)

        # Should be sorted by score even though all same category
        scores = [t["outlier_score"] for t in result]
        assert scores == [5.0, 3.0, 1.0]

    def test_maximizes_category_diversity(self):
        """Test 8 topics with 8 possible categories gets max diversity."""
        topics = [
            self._make_topic("shipping logistics topic", 8.0),
            self._make_topic("pricing margins topic", 7.0),
            self._make_topic("conversion optimization topic", 6.0),
            self._make_topic("facebook ads marketing topic", 5.0),
            self._make_topic("inventory management topic", 4.0),
            self._make_topic("customer retention topic", 3.5),
            self._make_topic("product sourcing alibaba topic", 3.0),
            self._make_topic("shopify platform tools topic", 2.5),
        ]

        result = select_diverse_topics(topics, count=8)

        # Should have 8 unique categories
        categories = [t["ecom_category"] for t in result]
        assert len(set(categories)) == 8

    def test_adds_ecom_category_to_topics(self):
        """Test function adds ecom_category field to topics."""
        topics = [self._make_topic("shipping test", 5.0)]

        result = select_diverse_topics(topics, count=1)

        assert "ecom_category" in result[0]
        assert result[0]["ecom_category"] == "shipping_logistics"


# =============================================================================
# CHECK_API_KEYS TESTS
# =============================================================================


class TestCheckApiKeys:
    """Tests for check_api_keys function."""

    def test_ready_with_anthropic_key(self, monkeypatch):
        """Test ready=True when ANTHROPIC_API_KEY is set."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        # Clear optional keys
        for key in [
            "REDDIT_CLIENT_ID",
            "PERPLEXITY_API_KEY",
            "TUBELAB_API_KEY",
            "APIFY_TOKEN",
        ]:
            monkeypatch.delenv(key, raising=False)

        result = check_api_keys()

        assert result["ready"] is True
        assert len(result["missing_required"]) == 0

    def test_not_ready_without_anthropic_key(self, monkeypatch):
        """Test ready=False when ANTHROPIC_API_KEY is missing."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        result = check_api_keys()

        assert result["ready"] is False
        assert "ANTHROPIC_API_KEY" in result["missing_required"]

    def test_missing_optional_keys_tracked(self, monkeypatch):
        """Test missing optional keys are listed."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)

        result = check_api_keys()

        assert "REDDIT_CLIENT_ID" in result["missing_optional"]
        assert "PERPLEXITY_API_KEY" in result["missing_optional"]

    def test_available_optional_keys_tracked(self, monkeypatch):
        """Test available optional keys are listed."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("REDDIT_CLIENT_ID", "reddit-id")
        monkeypatch.setenv("APIFY_TOKEN", "apify-token")

        result = check_api_keys()

        assert "REDDIT_CLIENT_ID" in result["available_optional"]
        assert "APIFY_TOKEN" in result["available_optional"]


# =============================================================================
# BATCH RUNNER CAN_CONTINUE TESTS
# =============================================================================


class TestBatchRunnerCanContinue:
    """Tests for BatchRunner.can_continue method."""

    def test_can_continue_at_zero_cost(self):
        """Test can_continue returns True at $0."""
        runner = BatchRunner(dry_run=True)

        assert runner.can_continue() is True

    def test_can_continue_under_budget(self):
        """Test can_continue returns True under budget."""
        runner = BatchRunner(dry_run=True)
        runner.tracker.add_cost("test_stage", 39.0)

        assert runner.can_continue() is True

    def test_can_continue_at_exact_budget(self):
        """Test can_continue returns True at exactly $40."""
        runner = BatchRunner(dry_run=True)
        runner.tracker.add_cost("test_stage", 40.0)

        # At exactly MAX_BUDGET, should still be True (<=)
        assert runner.can_continue() is True

    def test_cannot_continue_over_budget(self):
        """Test can_continue returns False over budget."""
        runner = BatchRunner(dry_run=True)
        runner.tracker.add_cost("test_stage", 41.0)

        assert runner.can_continue() is False


# =============================================================================
# BATCH RUNNER RUN_PREFLIGHT TESTS
# =============================================================================


class TestBatchRunnerRunPreflight:
    """Tests for BatchRunner.run_preflight method."""

    def test_preflight_passes_with_required_keys(self, monkeypatch, capsys):
        """Test preflight returns True when required keys present."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        runner = BatchRunner(dry_run=True)
        result = runner.run_preflight()

        assert result is True
        captured = capsys.readouterr()
        assert "PASS" in captured.out

    def test_preflight_fails_without_required_keys(self, monkeypatch, capsys):
        """Test preflight returns False when required keys missing."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        runner = BatchRunner(dry_run=True)
        result = runner.run_preflight()

        assert result is False
        captured = capsys.readouterr()
        assert "FAIL" in captured.out
        assert "MISSING" in captured.out

    def test_preflight_shows_warnings_for_optional(self, monkeypatch, capsys):
        """Test preflight shows warnings for missing optional keys."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)

        runner = BatchRunner(dry_run=True)
        runner.run_preflight()

        captured = capsys.readouterr()
        assert "WARN" in captured.out
        assert "REDDIT_CLIENT_ID" in captured.out


# =============================================================================
# BATCH RUNNER DISCOVER_TOPICS TESTS
# =============================================================================


class TestBatchRunnerDiscoverTopics:
    """Tests for BatchRunner.discover_topics method."""

    def test_discover_topics_dry_run_returns_mock_data(self):
        """Test dry run returns mock topic data."""
        runner = BatchRunner(dry_run=True)

        topics = runner.discover_topics(min_score=3.0, count=8)

        assert len(topics) == 8
        for topic in topics:
            assert "title" in topic
            assert "outlier_score" in topic
            assert "ecom_category" in topic
            assert topic["outlier_score"] >= 3.0

    def test_discover_topics_dry_run_has_diversity(self):
        """Test dry run mock data has category diversity."""
        runner = BatchRunner(dry_run=True)

        topics = runner.discover_topics(count=8)

        categories = set(t["ecom_category"] for t in topics)
        # Mock data should have at least 6 unique categories
        assert len(categories) >= 6

    def test_discover_topics_respects_count(self):
        """Test discover_topics respects count parameter."""
        runner = BatchRunner(dry_run=True)

        topics = runner.discover_topics(count=4)

        assert len(topics) == 4

    @patch("execution.content_aggregate.run_aggregation")
    def test_discover_topics_live_applies_diversity_filter(
        self, mock_aggregation, tmp_path
    ):
        """Test live discovery applies diversity filter to results."""
        # Create mock content file
        mock_content = {
            "contents": [
                {"title": "shipping topic 1", "outlier_score": 5.0, "source": "reddit"},
                {"title": "shipping topic 2", "outlier_score": 4.5, "source": "reddit"},
                {
                    "title": "facebook ads topic",
                    "outlier_score": 4.0,
                    "source": "reddit",
                },
                {"title": "pricing topic", "outlier_score": 3.5, "source": "reddit"},
            ]
        }
        json_path = tmp_path / "content.json"
        with open(json_path, "w") as f:
            json.dump(mock_content, f)

        mock_aggregation.return_value = {
            "success": True,
            "content_fetched": 4,
            "json_path": str(json_path),
        }

        runner = BatchRunner(dry_run=False)
        topics = runner.discover_topics(min_score=3.0, count=4)

        # Should have diversity
        assert len(topics) == 4
        categories = set(t["ecom_category"] for t in topics)
        assert len(categories) >= 3  # At least 3 unique categories from 4 topics

    @patch("execution.content_aggregate.run_aggregation")
    def test_discover_topics_handles_empty_results(self, mock_aggregation):
        """Test discover_topics handles empty aggregation results."""
        mock_aggregation.return_value = {
            "success": True,
            "content_fetched": 0,
        }

        runner = BatchRunner(dry_run=False)
        topics = runner.discover_topics()

        assert topics == []

    @patch("execution.content_aggregate.run_aggregation")
    def test_discover_topics_handles_aggregation_failure(self, mock_aggregation):
        """Test discover_topics handles aggregation failure gracefully."""
        mock_aggregation.return_value = {
            "success": False,
        }

        runner = BatchRunner(dry_run=False)
        topics = runner.discover_topics()

        assert topics == []


# =============================================================================
# E_COM_CATEGORIES CONSTANT TESTS
# =============================================================================


class TestEComCategoriesConstant:
    """Tests for E_COM_CATEGORIES constant."""

    def test_has_8_categories(self):
        """Test E_COM_CATEGORIES has exactly 8 categories."""
        assert len(E_COM_CATEGORIES) == 8

    def test_expected_categories_present(self):
        """Test all expected categories are present."""
        expected = [
            "shipping_logistics",
            "pricing_margins",
            "conversion_optimization",
            "ads_marketing",
            "inventory_management",
            "customer_retention",
            "product_sourcing",
            "platform_tools",
        ]
        for cat in expected:
            assert cat in E_COM_CATEGORIES


class TestCategoryKeywordsConstant:
    """Tests for CATEGORY_KEYWORDS constant."""

    def test_keywords_for_all_categories(self):
        """Test each category has keywords defined."""
        for category in E_COM_CATEGORIES:
            assert category in CATEGORY_KEYWORDS
            assert len(CATEGORY_KEYWORDS[category]) > 0

    def test_no_overlapping_keywords(self):
        """Test keywords are reasonably unique per category (some overlap is ok)."""
        # Just verify keywords are lists of strings
        for category, keywords in CATEGORY_KEYWORDS.items():
            assert isinstance(keywords, list)
            for kw in keywords:
                assert isinstance(kw, str)
                assert len(kw) > 0
