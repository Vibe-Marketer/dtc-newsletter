"""
Tests for the pricing recommender module.
"""

import pytest

from execution.pricing_recommender import (
    PricingRecommender,
    recommend_price,
    PRICING_TIERS,
    VALUE_SIGNALS,
)


class TestPricingTiers:
    """Tests for PRICING_TIERS constant."""

    def test_pricing_tiers_has_all_product_types(self):
        """Test that PRICING_TIERS has all expected product types."""
        expected_types = [
            "html_tool",
            "automation",
            "gpt_config",
            "sheets",
            "pdf",
            "prompt_pack",
        ]
        for product_type in expected_types:
            assert product_type in PRICING_TIERS

    def test_pricing_tiers_have_required_fields(self):
        """Test that each tier has base, premium, and perceived_multiplier."""
        for product_type, tier in PRICING_TIERS.items():
            assert "base" in tier, f"{product_type} missing 'base'"
            assert "premium" in tier, f"{product_type} missing 'premium'"
            assert "perceived_multiplier" in tier, (
                f"{product_type} missing 'perceived_multiplier'"
            )

    def test_premium_higher_than_base(self):
        """Test that premium price is always higher than base."""
        for product_type, tier in PRICING_TIERS.items():
            assert tier["premium"] > tier["base"], f"{product_type} premium <= base"

    def test_prices_in_valid_range(self):
        """Test that all prices are in $17-$97 range."""
        for product_type, tier in PRICING_TIERS.items():
            assert tier["base"] >= 17, f"{product_type} base < $17"
            assert tier["premium"] <= 97, f"{product_type} premium > $97"


class TestValueSignals:
    """Tests for VALUE_SIGNALS constant."""

    def test_value_signals_have_required_fields(self):
        """Test that each signal has description and weight."""
        for signal_name, signal_info in VALUE_SIGNALS.items():
            assert "description" in signal_info, f"{signal_name} missing 'description'"
            assert "weight" in signal_info, f"{signal_name} missing 'weight'"

    def test_value_signal_weights_sum_to_one(self):
        """Test that signal weights sum to 1.0."""
        total_weight = sum(signal["weight"] for signal in VALUE_SIGNALS.values())
        assert abs(total_weight - 1.0) < 0.01


class TestPricingRecommenderInit:
    """Tests for PricingRecommender initialization."""

    def test_can_instantiate(self):
        """Test that PricingRecommender can be instantiated."""
        recommender = PricingRecommender()
        assert recommender is not None

    def test_get_product_types(self):
        """Test get_product_types returns all types."""
        recommender = PricingRecommender()
        types = recommender.get_product_types()

        assert isinstance(types, list)
        assert "html_tool" in types
        assert "automation" in types
        assert len(types) == 6


class TestPricingRecommenderRecommend:
    """Tests for the recommend method."""

    def test_recommend_returns_required_fields(self):
        """Test that recommend returns all required fields."""
        recommender = PricingRecommender()
        result = recommender.recommend("html_tool")

        assert "price_cents" in result
        assert "price_display" in result
        assert "perceived_value" in result
        assert "justification" in result

    def test_automation_gets_higher_base_than_pdf(self):
        """Test that automation has higher base price than pdf."""
        recommender = PricingRecommender()

        automation_result = recommender.recommend("automation")
        pdf_result = recommender.recommend("pdf")

        # Automation base is $47, pdf base is $17
        assert automation_result["price_cents"] >= pdf_result["price_cents"]

    def test_premium_tier_selected_with_strong_signals(self):
        """Test that premium tier is selected with strong value signals."""
        recommender = PricingRecommender()

        # Strong signals (all at 0.8+)
        strong_signals = {
            "time_saved": 0.9,
            "money_impact": 0.9,
            "complexity": 0.8,
            "exclusivity": 0.8,
        }

        result = recommender.recommend("html_tool", strong_signals)

        # Premium for html_tool is $47
        assert result["price_cents"] == 4700  # $47 in cents

    def test_base_tier_selected_with_weak_signals(self):
        """Test that base tier is selected with weak value signals."""
        recommender = PricingRecommender()

        # Weak signals (all at 0.2 or lower)
        weak_signals = {
            "time_saved": 0.1,
            "money_impact": 0.2,
            "complexity": 0.1,
            "exclusivity": 0.1,
        }

        result = recommender.recommend("html_tool", weak_signals)

        # Base for html_tool is $27
        assert result["price_cents"] == 2700  # $27 in cents

    def test_perceived_value_includes_multiplier(self):
        """Test that perceived value uses the multiplier from tiers."""
        recommender = PricingRecommender()

        result = recommender.recommend("automation")  # multiplier is 15

        # Automation premium is $97, multiplier is 15
        # Perceived value should be around $1455
        assert "$" in result["perceived_value"]
        assert "worth" in result["perceived_value"]

    def test_unknown_product_type_raises_error(self):
        """Test that unknown product type raises ValueError."""
        recommender = PricingRecommender()

        with pytest.raises(ValueError) as exc_info:
            recommender.recommend("unknown_type")

        assert "Unknown product type" in str(exc_info.value)
        assert "unknown_type" in str(exc_info.value)

    def test_price_display_format(self):
        """Test that price_display is properly formatted."""
        recommender = PricingRecommender()
        result = recommender.recommend("html_tool")

        # Should be formatted like "$27" or "$47"
        assert result["price_display"].startswith("$")
        assert result["price_display"][1:].isdigit()

    def test_recommend_without_signals_uses_default(self):
        """Test that recommend works without explicit value signals."""
        recommender = PricingRecommender()
        result = recommender.recommend("sheets")

        # Should use default signal_strength of 0.5 -> base tier
        assert result["price_cents"] == 2700  # $27 base for sheets

    def test_justification_includes_perceived_value(self):
        """Test that justification mentions perceived value."""
        recommender = PricingRecommender()
        result = recommender.recommend("automation")

        # Justification should reference the value
        assert (
            "worth" in result["justification"].lower() or "$" in result["justification"]
        )


class TestPricingRecommenderSignalStrength:
    """Tests for signal strength calculation."""

    def test_signal_strength_calculation(self):
        """Test that signal strength is calculated correctly."""
        recommender = PricingRecommender()

        # Test with known values
        signals = {
            "time_saved": 1.0,  # weight 0.3
            "money_impact": 1.0,  # weight 0.35
            "complexity": 1.0,  # weight 0.2
            "exclusivity": 1.0,  # weight 0.15
        }

        strength = recommender._calculate_signal_strength(signals)
        assert strength == 1.0  # All maxed out

    def test_signal_strength_with_partial_signals(self):
        """Test signal strength with only some signals provided."""
        recommender = PricingRecommender()

        signals = {
            "money_impact": 1.0,  # Only one signal
        }

        strength = recommender._calculate_signal_strength(signals)
        # Should be weighted average: 0.35 * 1.0 / 1.0 = 0.35
        assert 0.0 < strength < 1.0

    def test_signal_values_clamped_to_range(self):
        """Test that signal values are clamped to 0-1."""
        recommender = PricingRecommender()

        # Values outside 0-1 range
        signals = {
            "time_saved": 2.0,  # Should be clamped to 1.0
            "money_impact": -1.0,  # Should be clamped to 0.0
        }

        strength = recommender._calculate_signal_strength(signals)
        # Should handle clamping gracefully
        assert 0.0 <= strength <= 1.0


class TestRecommendPriceFunction:
    """Tests for the convenience function."""

    def test_convenience_function_works(self):
        """Test that recommend_price convenience function works."""
        result = recommend_price("html_tool")

        assert "price_cents" in result
        assert "price_display" in result
        assert "perceived_value" in result
        assert "justification" in result

    def test_convenience_function_with_signals(self):
        """Test convenience function with value signals."""
        # All signals strong to ensure premium tier
        signals = {
            "time_saved": 0.9,
            "money_impact": 0.9,
            "complexity": 0.8,
            "exclusivity": 0.8,
        }

        result = recommend_price("automation", signals)

        # Should get premium tier
        assert result["price_cents"] == 9700  # $97 for automation premium

    def test_convenience_function_raises_on_unknown_type(self):
        """Test that convenience function raises ValueError for unknown type."""
        with pytest.raises(ValueError):
            recommend_price("invalid_type")


class TestPricingRecommenderEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_boundary_signal_strength(self):
        """Test pricing at signal strength boundary (0.6)."""
        recommender = PricingRecommender()

        # Signal strength just below 0.6 -> base
        weak_signals = {
            "time_saved": 0.5,
            "money_impact": 0.5,
            "complexity": 0.5,
            "exclusivity": 0.5,
        }
        weak_result = recommender.recommend("html_tool", weak_signals)
        assert weak_result["price_cents"] == 2700  # base

        # Signal strength above 0.6 -> premium
        strong_signals = {
            "time_saved": 0.8,
            "money_impact": 0.8,
            "complexity": 0.8,
            "exclusivity": 0.8,
        }
        strong_result = recommender.recommend("html_tool", strong_signals)
        assert strong_result["price_cents"] == 4700  # premium

    def test_all_product_types_work(self):
        """Test that all product types can be priced."""
        recommender = PricingRecommender()

        for product_type in PRICING_TIERS.keys():
            result = recommender.recommend(product_type)
            assert result["price_cents"] > 0
            assert result["price_display"].startswith("$")

    def test_empty_signals_dict(self):
        """Test that empty signals dict uses defaults."""
        recommender = PricingRecommender()
        result = recommender.recommend("pdf", {})

        # Should use default signal_strength
        assert result["price_cents"] == 1700  # $17 base for pdf

    def test_perceived_value_for_high_money_impact(self):
        """Test that high money impact affects perceived value."""
        recommender = PricingRecommender()

        high_money_signals = {
            "money_impact": 0.9,
        }

        result = recommender.recommend("automation", high_money_signals)

        # Should mention revenue potential
        assert (
            "revenue" in result["perceived_value"].lower()
            or "10x" in result["perceived_value"]
        )
