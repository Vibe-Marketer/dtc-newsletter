"""
Tests for Twitter/X aggregation module.
"""

import pytest
from unittest.mock import patch, MagicMock

from execution.twitter_aggregate import (
    score_twitter_post,
    fetch_dtc_tweets,
    run_twitter_aggregation,
    DTC_SEARCH_TERMS,
)


class TestScoreTwitterPost:
    """Tests for score_twitter_post function."""

    def test_basic_scoring(self):
        """Test basic outlier score calculation."""
        tweet = {
            "id": "123",
            "text": "Test tweet",
            "likeCount": 1000,
            "retweetCount": 100,
            "quoteCount": 10,
            "replyCount": 50,
            "author": {"userName": "testuser"},
        }

        result = score_twitter_post(tweet, account_avg_engagement=1000.0)

        # Total engagement = 1000 + 100 + 10 + 50 = 1160
        # Base ratio = 1160 / 1000 = 1.16
        # Quote boost: 10 quotes vs 100 retweets = 10%, < 30%, so no boost
        # Final: 1.16 * 1.0 = 1.16
        assert result["outlier_score"] == 1.16
        assert result["engagement"]["total"] == 1160
        assert result["source"] == "twitter"

    def test_quote_boost_applied(self):
        """Test that quote boost is applied when quotes > 30% of retweets."""
        tweet = {
            "id": "124",
            "text": "Controversial take",
            "likeCount": 1000,
            "retweetCount": 100,
            "quoteCount": 50,  # 50% of retweets - triggers boost
            "replyCount": 0,
            "author": {"userName": "hothead"},
        }

        result = score_twitter_post(tweet, account_avg_engagement=1000.0)

        # Total engagement = 1000 + 100 + 50 + 0 = 1150
        # Base ratio = 1150 / 1000 = 1.15
        # Quote boost: 50/100 = 50% > 30%, so 1.3x
        # Final: 1.15 * 1.3 = 1.495 -> rounded to 1.49
        assert result["outlier_score"] == 1.49

    def test_no_quote_boost_when_zero_retweets(self):
        """Test no boost when retweets are zero."""
        tweet = {
            "id": "125",
            "text": "Tweet with no retweets",
            "likeCount": 500,
            "retweetCount": 0,
            "quoteCount": 10,
            "replyCount": 10,
            "author": {"userName": "lowprofile"},
        }

        result = score_twitter_post(tweet, account_avg_engagement=500.0)

        # Total = 520, ratio = 1.04, no quote boost (retweets=0)
        assert result["outlier_score"] == 1.04

    def test_handles_missing_fields(self):
        """Test handling of tweets with missing engagement fields."""
        tweet = {
            "id": "126",
            "text": "Minimal tweet",
            # All engagement fields missing
        }

        result = score_twitter_post(tweet, account_avg_engagement=1000.0)

        # All zeros = 0 engagement, ratio = 0
        assert result["outlier_score"] == 0.0
        assert result["engagement"]["total"] == 0

    def test_handles_none_values(self):
        """Test handling of None values in engagement fields."""
        tweet = {
            "id": "127",
            "text": "Tweet with None values",
            "likeCount": None,
            "retweetCount": 100,
            "quoteCount": None,
            "replyCount": 10,
            "author": {"userName": "buggy"},
        }

        result = score_twitter_post(tweet, account_avg_engagement=1000.0)

        # None treated as 0: 0 + 100 + 0 + 10 = 110
        assert result["engagement"]["total"] == 110

    def test_url_generation(self):
        """Test tweet URL generation."""
        tweet = {
            "id": "12345",
            "text": "Test",
            "likeCount": 100,
            "author": {"userName": "testaccount"},
        }

        result = score_twitter_post(tweet)

        assert result["url"] == "https://twitter.com/testaccount/status/12345"

    def test_url_with_missing_author(self):
        """Test URL generation when author is missing."""
        tweet = {
            "id": "12345",
            "text": "Test",
            "likeCount": 100,
        }

        result = score_twitter_post(tweet)

        assert result["url"] == "https://twitter.com/unknown/status/12345"

    def test_high_engagement_viral_post(self):
        """Test scoring for truly viral posts."""
        tweet = {
            "id": "viral",
            "text": "This went viral",
            "likeCount": 50000,
            "retweetCount": 10000,
            "quoteCount": 5000,  # 50% of retweets - gets boost
            "replyCount": 5000,
            "author": {"userName": "celebrity"},
        }

        result = score_twitter_post(tweet, account_avg_engagement=1000.0)

        # Total = 70000, ratio = 70, quote boost = 1.3
        # Final = 70 * 1.3 = 91
        assert result["outlier_score"] == 91.0

    def test_preserves_original_tweet_data(self):
        """Test that original tweet data is preserved."""
        tweet = {
            "id": "128",
            "text": "Original text",
            "likeCount": 100,
            "customField": "custom value",
            "author": {"userName": "user", "followers": 5000},
        }

        result = score_twitter_post(tweet)

        assert result["text"] == "Original text"
        assert result["customField"] == "custom value"
        assert result["author"]["followers"] == 5000


class TestFetchDtcTweets:
    """Tests for fetch_dtc_tweets function."""

    @patch("execution.twitter_aggregate.fetch_from_apify")
    def test_fetches_and_deduplicates(self, mock_fetch):
        """Test that tweets are fetched and deduplicated."""
        mock_fetch.return_value = [
            {
                "id": "1",
                "text": "Tweet 1",
                "likeCount": 100,
                "author": {"userName": "u1"},
            },
            {
                "id": "2",
                "text": "Tweet 2",
                "likeCount": 200,
                "author": {"userName": "u2"},
            },
            {
                "id": "1",
                "text": "Tweet 1 duplicate",
                "likeCount": 100,
                "author": {"userName": "u1"},
            },
        ]

        result = fetch_dtc_tweets(search_terms=["test"], max_per_term=10)

        # Should have 2 unique tweets (duplicate ID removed)
        assert len(result) == 2
        assert all(t.get("outlier_score") is not None for t in result)

    @patch("execution.twitter_aggregate.fetch_from_apify")
    def test_sorts_by_outlier_score(self, mock_fetch):
        """Test that results are sorted by outlier score descending."""
        mock_fetch.return_value = [
            {
                "id": "1",
                "text": "Low engagement",
                "likeCount": 100,
                "author": {"userName": "u1"},
            },
            {
                "id": "2",
                "text": "High engagement",
                "likeCount": 10000,
                "author": {"userName": "u2"},
            },
            {
                "id": "3",
                "text": "Medium engagement",
                "likeCount": 1000,
                "author": {"userName": "u3"},
            },
        ]

        result = fetch_dtc_tweets(search_terms=["test"], max_per_term=10)

        scores = [t["outlier_score"] for t in result]
        assert scores == sorted(scores, reverse=True)

    @patch("execution.twitter_aggregate.fetch_from_apify")
    def test_handles_api_failure_gracefully(self, mock_fetch):
        """Test graceful handling of API failures."""
        mock_fetch.side_effect = Exception("API error")

        # Should not raise, returns empty list
        result = fetch_dtc_tweets(search_terms=["test"], max_per_term=10)

        assert result == []

    @patch("execution.twitter_aggregate.fetch_from_apify")
    def test_uses_default_search_terms(self, mock_fetch):
        """Test that default search terms are used when none provided."""
        mock_fetch.return_value = []

        fetch_dtc_tweets(max_per_term=10)

        # Should be called once per default search term
        assert mock_fetch.call_count == len(DTC_SEARCH_TERMS)


class TestRunTwitterAggregation:
    """Tests for run_twitter_aggregation function."""

    @patch("execution.twitter_aggregate.fetch_with_retry")
    def test_filters_by_min_score(self, mock_fetch):
        """Test filtering by minimum outlier score."""
        mock_fetch.return_value = {
            "success": True,
            "items": [
                {"id": "1", "outlier_score": 1.5, "text": "Low score"},
                {"id": "2", "outlier_score": 3.0, "text": "High score"},
                {"id": "3", "outlier_score": 5.0, "text": "Very high score"},
            ],
            "error": None,
            "cached": False,
            "timestamp": "2026-01-31T00:00:00Z",
        }

        result = run_twitter_aggregation(min_score=2.0)

        assert result["success"] is True
        assert len(result["items"]) == 2  # Only scores >= 2.0
        assert all(t["outlier_score"] >= 2.0 for t in result["items"])

    @patch("execution.twitter_aggregate.fetch_with_retry")
    def test_handles_failure(self, mock_fetch):
        """Test handling of fetch failure."""
        mock_fetch.return_value = {
            "success": False,
            "items": [],
            "error": "Connection failed",
            "cached": False,
            "timestamp": "2026-01-31T00:00:00Z",
        }

        result = run_twitter_aggregation()

        assert result["success"] is False
        assert result["error"] == "Connection failed"

    @patch("execution.twitter_aggregate.fetch_with_retry")
    def test_includes_metadata(self, mock_fetch):
        """Test that result includes metadata."""
        mock_fetch.return_value = {
            "success": True,
            "items": [{"id": "1", "outlier_score": 5.0}],
            "error": None,
            "cached": False,
            "timestamp": "2026-01-31T00:00:00Z",
        }

        result = run_twitter_aggregation()

        assert "total_fetched" in result
        assert "duration_seconds" in result
        assert result["total_fetched"] == 1


class TestDTCSearchTerms:
    """Tests for DTC search term configuration."""

    def test_search_terms_not_empty(self):
        """Ensure default search terms are configured."""
        assert len(DTC_SEARCH_TERMS) > 0

    def test_search_terms_are_strings(self):
        """Ensure all search terms are strings."""
        assert all(isinstance(term, str) for term in DTC_SEARCH_TERMS)
