"""
Tests for Amazon Movers & Shakers aggregator scoring.
"""

import pytest
from execution.amazon_aggregate import score_amazon_product, MOVERS_URLS


class TestScoreAmazonProduct:
    """Test outlier score calculation for Amazon products."""

    def test_basic_scoring_high_velocity(self):
        """High velocity products get high scores."""
        product = {
            "asin": "B001TEST",
            "position": 1,
            "rankChange": "+1000%",
            "title": "Viral Product",
            "url": "https://amazon.com/dp/B001TEST",
        }
        result = score_amazon_product(product)

        # Position: (100-1)/100 * 0.3 = 0.297
        # Velocity: 1000/100 * 0.7 = 7.0
        # Total: 0.297 + 7.0 = 7.297
        assert result["outlier_score"] == 7.3  # rounded
        assert result["position"] == 1
        assert result["rank_change_pct"] == 1000
        assert result["source"] == "amazon"

    def test_position_only_scoring(self):
        """Products with no velocity still get position score."""
        product = {
            "asin": "B002TEST",
            "position": 5,
            "rankChange": "0%",
            "title": "Steady Product",
        }
        result = score_amazon_product(product)

        # Position: (100-5)/100 * 0.3 = 0.285
        # Velocity: 0
        # Total: 0.285
        assert result["outlier_score"] == 0.28
        assert result["rank_change_pct"] == 0

    def test_velocity_weighting(self):
        """Velocity is weighted 70%, position 30%."""
        # Two products: one with good position, one with good velocity
        good_position = {
            "asin": "B003A",
            "position": 1,  # Best position
            "rankChange": "+100%",  # Moderate velocity
        }
        good_velocity = {
            "asin": "B003B",
            "position": 50,  # Mid position
            "rankChange": "+500%",  # High velocity
        }

        result_pos = score_amazon_product(good_position)
        result_vel = score_amazon_product(good_velocity)

        # Good velocity should win due to 70% weighting
        assert result_vel["outlier_score"] > result_pos["outlier_score"]

    def test_percentage_parsing_with_plus(self):
        """Parse rank change with leading +."""
        product = {"asin": "B004", "position": 10, "rankChange": "+500%"}
        result = score_amazon_product(product)
        assert result["rank_change_pct"] == 500

    def test_percentage_parsing_with_comma(self):
        """Parse rank change with thousands separator."""
        product = {"asin": "B005", "position": 10, "rankChange": "+1,234%"}
        result = score_amazon_product(product)
        assert result["rank_change_pct"] == 1234

    def test_percentage_parsing_no_plus(self):
        """Parse rank change without leading +."""
        product = {"asin": "B006", "position": 10, "rankChange": "200%"}
        result = score_amazon_product(product)
        assert result["rank_change_pct"] == 200

    def test_position_as_string(self):
        """Handle position as string with # prefix."""
        product = {"asin": "B007", "position": "#3", "rankChange": "+100%"}
        result = score_amazon_product(product)
        assert result["position"] == 3

    def test_missing_rank_change(self):
        """Handle missing rank change."""
        product = {"asin": "B008", "position": 20}
        result = score_amazon_product(product)
        assert result["rank_change_pct"] == 0

    def test_invalid_rank_change(self):
        """Handle invalid rank change format."""
        product = {"asin": "B009", "position": 20, "rankChange": "N/A"}
        result = score_amazon_product(product)
        assert result["rank_change_pct"] == 0

    def test_url_preserved(self):
        """Product URL is preserved in result."""
        product = {
            "asin": "B010",
            "position": 1,
            "rankChange": "100%",
            "url": "https://amazon.com/dp/B010",
        }
        result = score_amazon_product(product)
        assert result["url"] == "https://amazon.com/dp/B010"

    def test_low_position_score(self):
        """Products at bottom of list get low position score."""
        product = {"asin": "B011", "position": 99, "rankChange": "+100%"}
        result = score_amazon_product(product, category_size=100)

        # Position score near 0
        # (100-99)/100 * 0.3 = 0.003
        # Velocity: 100/100 * 0.7 = 0.7
        # Total: 0.703
        assert result["outlier_score"] == 0.7

    def test_extreme_velocity(self):
        """Very high velocity products get very high scores."""
        product = {"asin": "B012", "position": 50, "rankChange": "+5000%"}
        result = score_amazon_product(product)

        # Position: (100-50)/100 * 0.3 = 0.15
        # Velocity: 5000/100 * 0.7 = 35.0
        # Total: 35.15
        assert result["outlier_score"] == 35.15


class TestMoversUrls:
    """Test that URLs cover expected categories."""

    def test_main_movers_url(self):
        """Main Movers & Shakers URL is included."""
        assert "https://www.amazon.com/gp/movers-and-shakers/" in MOVERS_URLS

    def test_beauty_category(self):
        """Beauty category is tracked."""
        assert any("beauty" in url for url in MOVERS_URLS)

    def test_health_category(self):
        """Health & Personal Care is tracked."""
        assert any("hpc" in url for url in MOVERS_URLS)

    def test_multiple_categories(self):
        """At least 3 categories are tracked."""
        assert len(MOVERS_URLS) >= 3
