"""
Tests for Reddit fetcher module.

Uses mocking to avoid actual API calls during testing.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


class TestGetRedditClient:
    """Tests for get_reddit_client function."""

    def test_missing_client_id(self):
        """Should raise ValueError when REDDIT_CLIENT_ID is missing."""
        from execution.reddit_fetcher import get_reddit_client

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="REDDIT_CLIENT_ID"):
                get_reddit_client()

    def test_missing_client_secret(self):
        """Should raise ValueError when REDDIT_CLIENT_SECRET is missing."""
        from execution.reddit_fetcher import get_reddit_client

        with patch.dict("os.environ", {"REDDIT_CLIENT_ID": "test_id"}, clear=True):
            with pytest.raises(ValueError, match="REDDIT_CLIENT_SECRET"):
                get_reddit_client()

    def test_missing_user_agent(self):
        """Should raise ValueError when REDDIT_USER_AGENT is missing."""
        from execution.reddit_fetcher import get_reddit_client

        with patch.dict(
            "os.environ",
            {
                "REDDIT_CLIENT_ID": "test_id",
                "REDDIT_CLIENT_SECRET": "test_secret",
            },
            clear=True,
        ):
            with pytest.raises(ValueError, match="REDDIT_USER_AGENT"):
                get_reddit_client()

    @patch("execution.reddit_fetcher.praw.Reddit")
    def test_creates_client_with_credentials(self, mock_reddit):
        """Should create Reddit client with correct credentials."""
        from execution.reddit_fetcher import get_reddit_client

        with patch.dict(
            "os.environ",
            {
                "REDDIT_CLIENT_ID": "test_id",
                "REDDIT_CLIENT_SECRET": "test_secret",
                "REDDIT_USER_AGENT": "test_agent",
            },
            clear=True,
        ):
            get_reddit_client()

        mock_reddit.assert_called_once_with(
            client_id="test_id",
            client_secret="test_secret",
            user_agent="test_agent",
        )


class TestGetSubredditAverage:
    """Tests for get_subreddit_average function."""

    def test_calculates_average_correctly(self):
        """Should calculate average upvotes from posts."""
        from execution.reddit_fetcher import get_subreddit_average

        # Create mock posts
        mock_posts = [
            MagicMock(score=100),
            MagicMock(score=200),
            MagicMock(score=300),
        ]

        # Create mock subreddit
        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = iter(mock_posts)

        # Create mock reddit client
        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit

        avg = get_subreddit_average(mock_reddit, "test_subreddit", sample_size=3)

        assert avg == 200.0  # (100 + 200 + 300) / 3

    def test_raises_on_empty_subreddit(self):
        """Should raise ValueError when subreddit has no posts."""
        from execution.reddit_fetcher import get_subreddit_average

        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = iter([])

        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit

        with pytest.raises(ValueError, match="No posts found"):
            get_subreddit_average(mock_reddit, "empty_subreddit")


class TestProcessPost:
    """Tests for _process_post function."""

    def test_processes_post_correctly(self):
        """Should convert PRAW submission to dictionary with all fields."""
        from execution.reddit_fetcher import _process_post

        # Create mock post
        mock_post = MagicMock()
        mock_post.id = "abc123"
        mock_post.title = "How I made $10k in 30 days"
        mock_post.selftext = "Here's my secret strategy..."
        mock_post.permalink = "/r/shopify/comments/abc123/how_i_made"
        mock_post.score = 500
        mock_post.num_comments = 42
        mock_post.created_utc = datetime.now(timezone.utc).timestamp()

        result = _process_post(mock_post, "shopify", 100.0)

        assert result["id"] == "abc123"
        assert result["title"] == "How I made $10k in 30 days"
        assert result["selftext"] == "Here's my secret strategy..."
        assert (
            result["url"] == "https://reddit.com/r/shopify/comments/abc123/how_i_made"
        )
        assert result["upvotes"] == 500
        assert result["num_comments"] == 42
        assert result["subreddit"] == "shopify"
        assert result["subreddit_avg_upvotes"] == 100.0
        assert result["source"] == "reddit"
        assert "outlier_score" in result
        assert "engagement_modifiers" in result
        assert "fetched_at" in result

    def test_outlier_score_calculated(self):
        """Should calculate outlier score using scoring module."""
        from execution.reddit_fetcher import _process_post

        mock_post = MagicMock()
        mock_post.id = "test"
        mock_post.title = "Simple title"
        mock_post.selftext = ""
        mock_post.permalink = "/r/test/comments/test"
        mock_post.score = 500
        mock_post.num_comments = 10
        mock_post.created_utc = datetime.now(timezone.utc).timestamp()

        result = _process_post(mock_post, "test", 100.0)

        # Base score is 5.0 (500/100), with recency boost should be higher
        assert result["outlier_score"] >= 5.0

    def test_engagement_modifiers_detected(self):
        """Should detect engagement modifiers in content."""
        from execution.reddit_fetcher import _process_post

        mock_post = MagicMock()
        mock_post.id = "test"
        mock_post.title = "Unpopular opinion: This secret made me $50k revenue"
        mock_post.selftext = ""
        mock_post.permalink = "/r/test/comments/test"
        mock_post.score = 100
        mock_post.num_comments = 10
        mock_post.created_utc = datetime.now(timezone.utc).timestamp()

        result = _process_post(mock_post, "test", 100.0)

        assert "money" in result["engagement_modifiers"]
        assert "secret" in result["engagement_modifiers"]
        assert "controversy" in result["engagement_modifiers"]


class TestFetchSubredditPosts:
    """Tests for fetch_subreddit_posts function."""

    def test_filters_by_min_outlier_score(self):
        """Should filter posts below min_outlier_score threshold."""
        from execution.reddit_fetcher import fetch_subreddit_posts

        # Create mock posts with different scores
        mock_posts = []
        for score in [10, 50, 100, 500]:  # Will have outlier scores 0.1, 0.5, 1.0, 5.0
            post = MagicMock()
            post.id = f"post_{score}"
            post.title = "Test post"
            post.selftext = ""
            post.permalink = f"/r/test/comments/post_{score}"
            post.score = score
            post.num_comments = 5
            post.created_utc = datetime.now(timezone.utc).timestamp()
            mock_posts.append(post)

        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = iter(mock_posts)
        mock_subreddit.top.return_value = iter([])

        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit

        # With avg of 100, min_outlier_score of 2.0 should only include the 500 score post
        result = fetch_subreddit_posts(
            mock_reddit, "test", limit=10, min_outlier_score=2.0, subreddit_avg=100.0
        )

        # Only the 500-score post should pass (outlier score ~5.0+)
        assert len(result) == 1
        assert result[0]["upvotes"] == 500

    def test_combines_hot_and_top(self):
        """Should fetch from both hot and top (week) listings."""
        from execution.reddit_fetcher import fetch_subreddit_posts

        # Create different mock posts for hot and top
        hot_post = MagicMock()
        hot_post.id = "hot_post"
        hot_post.title = "Hot post"
        hot_post.selftext = ""
        hot_post.permalink = "/r/test/comments/hot_post"
        hot_post.score = 500
        hot_post.num_comments = 10
        hot_post.created_utc = datetime.now(timezone.utc).timestamp()

        top_post = MagicMock()
        top_post.id = "top_post"
        top_post.title = "Top post"
        top_post.selftext = ""
        top_post.permalink = "/r/test/comments/top_post"
        top_post.score = 600
        top_post.num_comments = 20
        top_post.created_utc = datetime.now(timezone.utc).timestamp()

        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = iter([hot_post])
        mock_subreddit.top.return_value = iter([top_post])

        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit

        result = fetch_subreddit_posts(
            mock_reddit, "test", limit=10, min_outlier_score=0, subreddit_avg=100.0
        )

        assert len(result) == 2
        assert any(p["id"] == "hot_post" for p in result)
        assert any(p["id"] == "top_post" for p in result)

    def test_deduplicates_posts(self):
        """Should not include duplicate posts that appear in both hot and top."""
        from execution.reddit_fetcher import fetch_subreddit_posts

        # Same post in both hot and top
        post = MagicMock()
        post.id = "duplicate_post"
        post.title = "Popular post"
        post.selftext = ""
        post.permalink = "/r/test/comments/duplicate_post"
        post.score = 500
        post.num_comments = 10
        post.created_utc = datetime.now(timezone.utc).timestamp()

        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = iter([post])
        mock_subreddit.top.return_value = iter([post])

        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit

        result = fetch_subreddit_posts(
            mock_reddit, "test", limit=10, min_outlier_score=0, subreddit_avg=100.0
        )

        assert len(result) == 1

    def test_sorts_by_outlier_score_descending(self):
        """Should return posts sorted by outlier score, highest first."""
        from execution.reddit_fetcher import fetch_subreddit_posts

        mock_posts = []
        for score in [100, 500, 300]:  # Random order
            post = MagicMock()
            post.id = f"post_{score}"
            post.title = "Test"
            post.selftext = ""
            post.permalink = f"/r/test/comments/post_{score}"
            post.score = score
            post.num_comments = 5
            post.created_utc = datetime.now(timezone.utc).timestamp()
            mock_posts.append(post)

        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = iter(mock_posts)
        mock_subreddit.top.return_value = iter([])

        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit

        result = fetch_subreddit_posts(
            mock_reddit, "test", limit=10, min_outlier_score=0, subreddit_avg=100.0
        )

        # Should be sorted descending by outlier score
        scores = [p["outlier_score"] for p in result]
        assert scores == sorted(scores, reverse=True)


class TestFetchAllSubreddits:
    """Tests for fetch_all_subreddits function."""

    @patch("execution.reddit_fetcher.get_reddit_client")
    @patch("execution.reddit_fetcher.fetch_subreddit_posts")
    def test_fetches_from_all_target_subreddits(self, mock_fetch, mock_client):
        """Should fetch posts from all TARGET_SUBREDDITS."""
        from execution.reddit_fetcher import fetch_all_subreddits, TARGET_SUBREDDITS

        mock_fetch.return_value = []
        mock_client.return_value = MagicMock()

        fetch_all_subreddits()

        # Should call fetch_subreddit_posts for each target subreddit
        assert mock_fetch.call_count == len(TARGET_SUBREDDITS)
        called_subreddits = [
            call[1]["subreddit_name"] for call in mock_fetch.call_args_list
        ]
        for sub in TARGET_SUBREDDITS:
            assert sub in called_subreddits

    @patch("execution.reddit_fetcher.get_reddit_client")
    @patch("execution.reddit_fetcher.fetch_subreddit_posts")
    def test_combines_and_sorts_results(self, mock_fetch, mock_client):
        """Should combine posts from all subreddits and sort by outlier score."""
        from execution.reddit_fetcher import fetch_all_subreddits

        # Return different posts for each subreddit
        def mock_fetch_side_effect(**kwargs):
            subreddit = kwargs["subreddit_name"]
            if subreddit == "shopify":
                return [{"id": "s1", "outlier_score": 5.0, "subreddit": "shopify"}]
            elif subreddit == "dropship":
                return [{"id": "d1", "outlier_score": 10.0, "subreddit": "dropship"}]
            elif subreddit == "ecommerce":
                return [{"id": "e1", "outlier_score": 3.0, "subreddit": "ecommerce"}]
            return []

        mock_fetch.side_effect = mock_fetch_side_effect
        mock_client.return_value = MagicMock()

        result = fetch_all_subreddits()

        # Should have all 3 posts
        assert len(result) == 3

        # Should be sorted by outlier score descending
        assert result[0]["outlier_score"] == 10.0
        assert result[1]["outlier_score"] == 5.0
        assert result[2]["outlier_score"] == 3.0

    @patch("execution.reddit_fetcher.get_reddit_client")
    @patch("execution.reddit_fetcher.fetch_subreddit_posts")
    def test_handles_failed_subreddit_gracefully(self, mock_fetch, mock_client, capsys):
        """Should continue fetching other subreddits if one fails."""
        from execution.reddit_fetcher import fetch_all_subreddits

        def mock_fetch_side_effect(**kwargs):
            subreddit = kwargs["subreddit_name"]
            if subreddit == "dropship":
                raise Exception("API Error")
            return [{"id": subreddit, "outlier_score": 5.0}]

        mock_fetch.side_effect = mock_fetch_side_effect
        mock_client.return_value = MagicMock()

        result = fetch_all_subreddits()

        # Should still have results from other subreddits
        assert len(result) == 2  # shopify and ecommerce

        # Should print warning
        captured = capsys.readouterr()
        assert "dropship" in captured.out
        assert "Warning" in captured.out

    @patch("execution.reddit_fetcher.get_reddit_client")
    @patch("execution.reddit_fetcher.fetch_subreddit_posts")
    def test_accepts_custom_subreddits(self, mock_fetch, mock_client):
        """Should allow specifying custom subreddit list."""
        from execution.reddit_fetcher import fetch_all_subreddits

        mock_fetch.return_value = []
        mock_client.return_value = MagicMock()

        custom_subs = ["entrepreneur", "startups"]
        fetch_all_subreddits(subreddits=custom_subs)

        assert mock_fetch.call_count == 2
        called_subreddits = [
            call[1]["subreddit_name"] for call in mock_fetch.call_args_list
        ]
        assert "entrepreneur" in called_subreddits
        assert "startups" in called_subreddits


class TestEngagementModifierLabels:
    """Tests for _get_engagement_modifier_labels function."""

    def test_money_modifier_detected(self):
        """Should detect money-related keywords."""
        from execution.reddit_fetcher import _get_engagement_modifier_labels

        labels = _get_engagement_modifier_labels("Made $5000 in revenue", "")
        assert "money" in labels

    def test_time_modifier_detected(self):
        """Should detect time-related keywords."""
        from execution.reddit_fetcher import _get_engagement_modifier_labels

        labels = _get_engagement_modifier_labels("Did this in 30 minutes", "")
        assert "time" in labels

    def test_secret_modifier_detected(self):
        """Should detect secret-related keywords."""
        from execution.reddit_fetcher import _get_engagement_modifier_labels

        labels = _get_engagement_modifier_labels(
            "The hidden truth about dropshipping", ""
        )
        assert "secret" in labels

    def test_controversy_modifier_detected(self):
        """Should detect controversy-related keywords."""
        from execution.reddit_fetcher import _get_engagement_modifier_labels

        labels = _get_engagement_modifier_labels(
            "Unpopular opinion: Shopify is overrated", ""
        )
        assert "controversy" in labels

    def test_multiple_modifiers(self):
        """Should detect multiple modifiers in same content."""
        from execution.reddit_fetcher import _get_engagement_modifier_labels

        labels = _get_engagement_modifier_labels(
            "Unpopular opinion: This secret made me $10k fast", ""
        )

        assert "money" in labels
        assert "controversy" in labels
        assert "secret" in labels
        # Note: "fast" is a time keyword
        assert "time" in labels

    def test_no_modifiers_for_plain_content(self):
        """Should return empty list for plain content."""
        from execution.reddit_fetcher import _get_engagement_modifier_labels

        labels = _get_engagement_modifier_labels(
            "Regular post about ecommerce", "Just some text"
        )
        assert labels == []
