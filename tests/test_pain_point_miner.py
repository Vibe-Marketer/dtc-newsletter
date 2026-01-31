"""
Tests for pain point miner module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from execution.pain_point_miner import (
    PAIN_KEYWORDS,
    PAIN_SUBREDDITS,
    CATEGORY_KEYWORDS,
    search_pain_points,
    categorize_pain_point,
    get_top_pain_points,
)


class TestPainKeywords:
    """Test PAIN_KEYWORDS contains expected complaint indicators."""

    def test_contains_frustration_signals(self):
        """PAIN_KEYWORDS should contain frustration-indicating phrases."""
        frustration_keywords = [
            "frustrated with shopify",
            "hate my shopify",
            "shopify problem",
        ]
        for kw in frustration_keywords:
            assert kw in PAIN_KEYWORDS, f"Missing frustration keyword: {kw}"

    def test_contains_help_seeking(self):
        """PAIN_KEYWORDS should contain help-seeking phrases."""
        help_keywords = [
            "struggling with ecommerce",
            "need help with store",
            "can't figure out",
        ]
        for kw in help_keywords:
            assert kw in PAIN_KEYWORDS, f"Missing help-seeking keyword: {kw}"

    def test_contains_specific_pains(self):
        """PAIN_KEYWORDS should contain specific e-commerce pain points."""
        specific_pains = [
            "conversion rate low",
            "cart abandonment",
            "shipping nightmare",
            "inventory management hell",
            "returns killing me",
        ]
        for kw in specific_pains:
            assert kw in PAIN_KEYWORDS, f"Missing specific pain keyword: {kw}"

    def test_keywords_not_empty(self):
        """PAIN_KEYWORDS should have substantial entries."""
        assert len(PAIN_KEYWORDS) >= 10, "Should have at least 10 pain keywords"


class TestPainSubreddits:
    """Test PAIN_SUBREDDITS contains target subreddits."""

    def test_contains_shopify(self):
        """PAIN_SUBREDDITS should contain shopify subreddit."""
        assert "shopify" in PAIN_SUBREDDITS

    def test_contains_ecommerce(self):
        """PAIN_SUBREDDITS should contain ecommerce subreddit."""
        assert "ecommerce" in PAIN_SUBREDDITS

    def test_contains_dropship(self):
        """PAIN_SUBREDDITS should contain dropship subreddit."""
        assert "dropship" in PAIN_SUBREDDITS

    def test_contains_entrepreneur(self):
        """PAIN_SUBREDDITS should contain Entrepreneur subreddit."""
        assert "Entrepreneur" in PAIN_SUBREDDITS

    def test_contains_smallbusiness(self):
        """PAIN_SUBREDDITS should contain smallbusiness subreddit."""
        assert "smallbusiness" in PAIN_SUBREDDITS

    def test_contains_fba(self):
        """PAIN_SUBREDDITS should contain FulfillmentByAmazon subreddit."""
        assert "FulfillmentByAmazon" in PAIN_SUBREDDITS


class TestSearchPainPoints:
    """Test search_pain_points function with mocked Reddit."""

    def _create_mock_post(
        self, id, title, selftext, score, num_comments, permalink="/r/test/post"
    ):
        """Helper to create a mock Reddit post."""
        post = Mock()
        post.id = id
        post.title = title
        post.selftext = selftext
        post.score = score
        post.num_comments = num_comments
        post.permalink = permalink
        return post

    @patch("execution.pain_point_miner.get_reddit_client")
    def test_returns_list_of_dicts(self, mock_get_client):
        """search_pain_points should return a list of dictionaries."""
        # Setup mock
        mock_reddit = Mock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit

        # Mock search returning one post
        mock_post = self._create_mock_post("post1", "Test title", "Test body", 100, 50)
        mock_subreddit.search.return_value = [mock_post]

        result = search_pain_points(
            subreddits=["shopify"], keywords=["frustrated"], limit=10
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], dict)

    @patch("execution.pain_point_miner.get_reddit_client")
    def test_dict_contains_required_fields(self, mock_get_client):
        """Pain point dicts should contain required fields."""
        mock_reddit = Mock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit

        mock_post = self._create_mock_post("post1", "Test title", "Test body", 100, 50)
        mock_subreddit.search.return_value = [mock_post]

        result = search_pain_points(
            subreddits=["shopify"], keywords=["frustrated"], limit=10
        )

        required_fields = [
            "title",
            "body",
            "score",
            "comments",
            "url",
            "keyword",
            "subreddit",
        ]
        for field in required_fields:
            assert field in result[0], f"Missing field: {field}"

    @patch("execution.pain_point_miner.get_reddit_client")
    def test_sorts_by_engagement_score(self, mock_get_client):
        """Results should be sorted by engagement score descending."""
        mock_reddit = Mock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit

        # Create posts with different engagement
        posts = [
            self._create_mock_post(
                "post1", "Low engagement", "", 10, 5
            ),  # engagement: 15
            self._create_mock_post(
                "post2", "High engagement", "", 200, 100
            ),  # engagement: 300
            self._create_mock_post(
                "post3", "Medium engagement", "", 50, 25
            ),  # engagement: 75
        ]
        mock_subreddit.search.return_value = posts

        result = search_pain_points(subreddits=["shopify"], keywords=["test"], limit=10)

        # Verify sorted by engagement (score + comments) descending
        assert result[0]["engagement_score"] >= result[-1]["engagement_score"]
        assert result[0]["title"] == "High engagement"

    @patch("execution.pain_point_miner.get_reddit_client")
    def test_deduplicates_by_post_id(self, mock_get_client):
        """Duplicate posts should be removed."""
        mock_reddit = Mock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit

        # Same post returned for different keywords
        duplicate_post = self._create_mock_post("same_id", "Same post", "", 100, 50)
        mock_subreddit.search.return_value = [duplicate_post]

        result = search_pain_points(
            subreddits=["shopify"],
            keywords=["keyword1", "keyword2", "keyword3"],
            limit=10,
        )

        # Should only have one instance of the post
        assert len(result) == 1

    @patch("execution.pain_point_miner.get_reddit_client")
    def test_truncates_body_to_500_chars(self, mock_get_client):
        """Body text should be truncated to 500 characters."""
        mock_reddit = Mock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit

        long_body = "x" * 1000
        mock_post = self._create_mock_post("post1", "Title", long_body, 100, 50)
        mock_subreddit.search.return_value = [mock_post]

        result = search_pain_points(subreddits=["shopify"], keywords=["test"], limit=10)

        assert len(result[0]["body"]) == 500

    @patch("execution.pain_point_miner.get_reddit_client")
    def test_uses_default_subreddits_if_none(self, mock_get_client):
        """Should use PAIN_SUBREDDITS if none provided."""
        mock_reddit = Mock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.search.return_value = []

        search_pain_points(subreddits=None, keywords=["test"])

        # Verify subreddit was called for each default subreddit
        called_subs = [call[0][0] for call in mock_reddit.subreddit.call_args_list]
        for sub in PAIN_SUBREDDITS:
            assert sub in called_subs

    @patch("execution.pain_point_miner.get_reddit_client")
    def test_uses_default_keywords_if_none(self, mock_get_client):
        """Should use PAIN_KEYWORDS if none provided."""
        mock_reddit = Mock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.search.return_value = []

        search_pain_points(subreddits=["shopify"], keywords=None)

        # Verify search was called for multiple keywords
        assert mock_subreddit.search.call_count >= len(PAIN_KEYWORDS)


class TestCategorizePainPoint:
    """Test categorize_pain_point function."""

    def test_categorizes_shipping(self):
        """Should categorize shipping-related pain points."""
        pain_point = {"title": "Shipping nightmare", "body": "My fulfillment is a mess"}
        assert categorize_pain_point(pain_point) == "shipping"

    def test_categorizes_inventory(self):
        """Should categorize inventory-related pain points."""
        pain_point = {
            "title": "Inventory management broken",
            "body": "Stock levels out of sync with warehouse",
        }
        assert categorize_pain_point(pain_point) == "inventory"

    def test_categorizes_conversion(self):
        """Should categorize conversion-related pain points."""
        pain_point = {
            "title": "Low conversion rate",
            "body": "Cart abandonment is killing me",
        }
        assert categorize_pain_point(pain_point) == "conversion"

    def test_categorizes_returns(self):
        """Should categorize returns-related pain points."""
        pain_point = {
            "title": "Return policy issues",
            "body": "Getting too many refund requests",
        }
        assert categorize_pain_point(pain_point) == "returns"

    def test_categorizes_pricing(self):
        """Should categorize pricing-related pain points."""
        pain_point = {
            "title": "Pricing strategy broken",
            "body": "My margins are terrible",
        }
        assert categorize_pain_point(pain_point) == "pricing"

    def test_categorizes_marketing(self):
        """Should categorize marketing-related pain points."""
        pain_point = {
            "title": "Facebook ads spending too much",
            "body": "My advertising budget is wasted on bad SEO",
        }
        assert categorize_pain_point(pain_point) == "marketing"

    def test_categorizes_other_for_unknown(self):
        """Should return 'other' for pain points that don't match categories."""
        pain_point = {
            "title": "Random problem",
            "body": "Something completely unrelated",
        }
        assert categorize_pain_point(pain_point) == "other"

    def test_case_insensitive(self):
        """Category matching should be case-insensitive."""
        pain_point = {"title": "SHIPPING NIGHTMARE", "body": "FULFILLMENT IS BROKEN"}
        assert categorize_pain_point(pain_point) == "shipping"


class TestGetTopPainPoints:
    """Test get_top_pain_points convenience function."""

    @patch("execution.pain_point_miner.search_pain_points")
    def test_returns_limited_results(self, mock_search):
        """Should return at most 'limit' pain points."""
        # Create 30 mock pain points
        mock_results = [
            {"title": f"Pain {i}", "body": "", "engagement_score": 100 - i}
            for i in range(30)
        ]
        mock_search.return_value = mock_results

        result = get_top_pain_points(limit=20)

        assert len(result) == 20

    @patch("execution.pain_point_miner.search_pain_points")
    def test_adds_category_to_results(self, mock_search):
        """Should add 'category' field to each pain point."""
        mock_results = [
            {
                "title": "Shipping issue",
                "body": "Fulfillment problems",
                "engagement_score": 100,
            }
        ]
        mock_search.return_value = mock_results

        result = get_top_pain_points(limit=10)

        assert "category" in result[0]
        assert result[0]["category"] == "shipping"

    @patch("execution.pain_point_miner.search_pain_points")
    def test_handles_empty_results(self, mock_search):
        """Should handle empty search results gracefully."""
        mock_search.return_value = []

        result = get_top_pain_points(limit=20)

        assert result == []
