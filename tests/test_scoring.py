"""
Tests for the outlier scoring algorithm.

Tests cover:
- Recency boost calculation (fresh posts vs old posts)
- Engagement modifiers (money, time, secrets, controversy)
- Complete outlier score calculation
- Edge cases and error handling
"""

import pytest
from datetime import datetime, timezone
import time

from execution.scoring import (
    calculate_recency_boost,
    calculate_engagement_modifiers,
    calculate_outlier_score,
)


class TestRecencyBoost:
    """Tests for calculate_recency_boost function."""

    def test_brand_new_post_gets_max_boost(self):
        """A post created just now should get the maximum 1.3x boost."""
        now_timestamp = time.time()
        boost = calculate_recency_boost(now_timestamp)
        assert boost == pytest.approx(1.3, rel=0.01)

    def test_week_old_post_gets_no_boost(self):
        """A post 7+ days old should get exactly 1.0x (no boost)."""
        seven_days_ago = time.time() - (7 * 24 * 60 * 60)
        boost = calculate_recency_boost(seven_days_ago)
        assert boost == 1.0

    def test_very_old_post_gets_no_boost(self):
        """A post 30 days old should still get exactly 1.0x."""
        thirty_days_ago = time.time() - (30 * 24 * 60 * 60)
        boost = calculate_recency_boost(thirty_days_ago)
        assert boost == 1.0

    def test_half_decay_period_gives_middle_boost(self):
        """A post 3.5 days old should get ~1.15x boost (midpoint)."""
        three_and_half_days_ago = time.time() - (3.5 * 24 * 60 * 60)
        boost = calculate_recency_boost(three_and_half_days_ago)
        # Midpoint between 1.0 and 1.3 is 1.15
        assert boost == pytest.approx(1.15, rel=0.01)

    def test_one_day_old_post(self):
        """A post 1 day old should get approximately 1.257x boost."""
        one_day_ago = time.time() - (1 * 24 * 60 * 60)
        boost = calculate_recency_boost(one_day_ago)
        # After 1/7 of decay period: 1.3 - (0.3 * 1/7) = 1.257
        assert boost == pytest.approx(1.257, rel=0.01)

    def test_custom_max_boost(self):
        """Test with a custom max_boost value."""
        now_timestamp = time.time()
        boost = calculate_recency_boost(now_timestamp, max_boost=1.5)
        assert boost == pytest.approx(1.5, rel=0.01)

    def test_custom_decay_days(self):
        """A post at half of custom decay period should get middle boost."""
        five_days_ago = time.time() - (5 * 24 * 60 * 60)
        boost = calculate_recency_boost(five_days_ago, decay_days=10)
        # Midpoint: 1.0 + (0.3 * 0.5) = 1.15
        assert boost == pytest.approx(1.15, rel=0.01)


class TestEngagementModifiers:
    """Tests for calculate_engagement_modifiers function."""

    def test_no_modifiers_returns_1(self):
        """Plain title with no special keywords returns 1.0."""
        modifier = calculate_engagement_modifiers("Just a regular post")
        assert modifier == 1.0

    def test_money_modifier_dollar_sign(self):
        """Dollar amounts trigger +30% modifier."""
        modifier = calculate_engagement_modifiers("I made $500 today")
        assert modifier == pytest.approx(1.30, rel=0.01)

    def test_money_modifier_revenue(self):
        """'revenue' keyword triggers +30% modifier."""
        modifier = calculate_engagement_modifiers("My store's revenue doubled")
        assert modifier == pytest.approx(1.30, rel=0.01)

    def test_money_modifier_profit(self):
        """'profit' keyword triggers +30% modifier."""
        modifier = calculate_engagement_modifiers("How to increase profit margins")
        assert modifier == pytest.approx(1.30, rel=0.01)

    def test_time_modifier_minutes(self):
        """Time references trigger +20% modifier."""
        modifier = calculate_engagement_modifiers("Do this in 5 minutes")
        assert modifier == pytest.approx(1.20, rel=0.01)

    def test_time_modifier_quick(self):
        """'quick' keyword triggers +20% modifier."""
        modifier = calculate_engagement_modifiers("Quick tip for beginners")
        assert modifier == pytest.approx(1.20, rel=0.01)

    def test_secret_modifier(self):
        """Secret keywords trigger +20% modifier."""
        # Note: avoid words that trigger other modifiers
        modifier = calculate_engagement_modifiers("The hidden truth about marketing")
        assert modifier == pytest.approx(1.20, rel=0.01)

    def test_secret_modifier_hidden(self):
        """'hidden' keyword triggers +20% modifier."""
        modifier = calculate_engagement_modifiers("Hidden features in Shopify")
        assert modifier == pytest.approx(1.20, rel=0.01)

    def test_controversy_modifier(self):
        """Controversy keywords trigger +15% modifier."""
        modifier = calculate_engagement_modifiers(
            "Unpopular opinion: dropshipping is dead"
        )
        assert modifier == pytest.approx(1.15, rel=0.01)

    def test_multiple_modifiers_stack(self):
        """Multiple modifiers should stack additively."""
        # Money (+30%) + Time (+20%) = +50%
        modifier = calculate_engagement_modifiers("Made $1000 in 30 minutes")
        assert modifier == pytest.approx(1.50, rel=0.01)

    def test_all_modifiers_stack(self):
        """All four modifiers stacking: +30% + 20% + 20% + 15% = +85%."""
        title = "Secret: Made $5000 overnight - unpopular opinion"
        modifier = calculate_engagement_modifiers(title)
        # Money (overnight has $ and "made") + time (overnight) + secret + controversy
        assert modifier == pytest.approx(1.85, rel=0.01)

    def test_modifier_in_selftext(self):
        """Modifiers in body text should also be detected."""
        modifier = calculate_engagement_modifiers(
            "Check this out", selftext="The secret nobody knows about"
        )
        assert modifier == pytest.approx(1.20, rel=0.01)

    def test_case_insensitive(self):
        """Keyword matching should be case-insensitive."""
        modifier = calculate_engagement_modifiers("REVENUE is up!")
        assert modifier == pytest.approx(1.30, rel=0.01)


class TestOutlierScore:
    """Tests for calculate_outlier_score function."""

    def test_basic_calculation(self):
        """Test basic outlier score without modifiers."""
        # 500 upvotes vs 100 average = 5x, no modifiers, fresh post
        now = time.time()
        score = calculate_outlier_score(
            upvotes=500,
            subreddit_avg_upvotes=100,
            post_timestamp=now,
            title="Regular post title",
        )
        # 5 * 1.3 * 1.0 = 6.5
        assert score == pytest.approx(6.5, rel=0.01)

    def test_with_engagement_modifier(self):
        """Test outlier score with engagement modifier."""
        now = time.time()
        score = calculate_outlier_score(
            upvotes=500,
            subreddit_avg_upvotes=100,
            post_timestamp=now,
            title="Made $10000 last month",  # +30% money modifier
        )
        # 5 * 1.3 * 1.3 = 8.45
        assert score == pytest.approx(8.45, rel=0.01)

    def test_old_post_no_recency_boost(self):
        """Old post gets no recency boost."""
        week_ago = time.time() - (7 * 24 * 60 * 60)
        score = calculate_outlier_score(
            upvotes=500,
            subreddit_avg_upvotes=100,
            post_timestamp=week_ago,
            title="Regular post",
        )
        # 5 * 1.0 * 1.0 = 5.0
        assert score == pytest.approx(5.0, rel=0.01)

    def test_below_average_post(self):
        """Post performing below average gets score < 1."""
        now = time.time()
        score = calculate_outlier_score(
            upvotes=50,
            subreddit_avg_upvotes=100,
            post_timestamp=now,
            title="Regular post",
        )
        # 0.5 * 1.3 * 1.0 = 0.65
        assert score == pytest.approx(0.65, rel=0.01)

    def test_exactly_average_post(self):
        """Post at exactly average should get score around 1.3 (recency only)."""
        now = time.time()
        score = calculate_outlier_score(
            upvotes=100,
            subreddit_avg_upvotes=100,
            post_timestamp=now,
            title="Regular post",
        )
        # 1 * 1.3 * 1.0 = 1.3
        assert score == pytest.approx(1.3, rel=0.01)

    def test_zero_average_raises_error(self):
        """Zero subreddit average should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_outlier_score(
                upvotes=100,
                subreddit_avg_upvotes=0,
                post_timestamp=time.time(),
                title="Test",
            )

    def test_negative_average_raises_error(self):
        """Negative subreddit average should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_outlier_score(
                upvotes=100,
                subreddit_avg_upvotes=-50,
                post_timestamp=time.time(),
                title="Test",
            )

    def test_real_world_example(self):
        """Test a realistic scenario matching TubeLab-style scoring."""
        # Scenario: Viral post with 2000 upvotes in subreddit averaging 200
        # Post is 2 days old, title mentions money
        two_days_ago = time.time() - (2 * 24 * 60 * 60)
        score = calculate_outlier_score(
            upvotes=2000,
            subreddit_avg_upvotes=200,
            post_timestamp=two_days_ago,
            title="How I grew my Shopify store to $50k/month revenue",
        )
        # Base: 10x
        # Recency: ~1.214 (5/7 of boost remaining)
        # Engagement: 1.3 (money modifier)
        # Expected: 10 * 1.214 * 1.3 ≈ 15.78
        assert score > 15.0
        assert score < 17.0

    def test_selftext_affects_score(self):
        """Body text with modifiers should affect the score."""
        now = time.time()
        score = calculate_outlier_score(
            upvotes=100,
            subreddit_avg_upvotes=100,
            post_timestamp=now,
            title="Check this out",
            selftext="Here's the secret to getting results fast",
        )
        # 1 * 1.3 * (1.0 + 0.2 + 0.2) = 1 * 1.3 * 1.4 = 1.82
        # (time: "fast" + secret: "secret")
        assert score == pytest.approx(1.82, rel=0.01)
