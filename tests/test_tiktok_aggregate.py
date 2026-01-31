"""
Tests for TikTok aggregator scoring and commerce detection.
"""

import pytest
from execution.tiktok_aggregate import (
    is_commerce_video,
    score_tiktok_video,
    COMMERCE_KEYWORDS,
)


class TestIsCommerceVideo:
    """Test commerce indicator detection."""

    def test_tt_seller_flag(self):
        """Videos with ttSeller flag are commerce."""
        video = {"ttSeller": True, "desc": "Check this out"}
        assert is_commerce_video(video) is True

    def test_is_sponsored_flag(self):
        """Sponsored videos are commerce."""
        video = {"isSponsored": True, "desc": "Cool product"}
        assert is_commerce_video(video) is True

    def test_commerce_user_info(self):
        """Videos from commerce users are commerce."""
        video = {
            "commerceUserInfo": {"commerceUser": True},
            "desc": "My new product",
        }
        assert is_commerce_video(video) is True

    def test_link_in_bio_keyword(self):
        """Descriptions with 'link in bio' are commerce."""
        video = {"desc": "Get this product! Link in bio for discount"}
        assert is_commerce_video(video) is True

    def test_shop_now_keyword(self):
        """Descriptions with 'shop now' are commerce."""
        video = {"desc": "Amazing deal - shop now before it's gone"}
        assert is_commerce_video(video) is True

    def test_use_code_keyword(self):
        """Descriptions with 'use code' are commerce."""
        video = {"desc": "Use code SAVE20 for 20% off"}
        assert is_commerce_video(video) is True

    def test_tiktok_shop_keyword(self):
        """Descriptions mentioning TikTok Shop are commerce."""
        video = {"desc": "Available on tiktok shop"}
        assert is_commerce_video(video) is True

    def test_non_commerce_video(self):
        """Regular videos without commerce indicators."""
        video = {"desc": "Just a funny video", "ttSeller": False}
        assert is_commerce_video(video) is False

    def test_empty_description(self):
        """Videos with no description."""
        video = {"desc": None}
        assert is_commerce_video(video) is False

    def test_case_insensitive_keywords(self):
        """Commerce keywords are case-insensitive."""
        video = {"desc": "LINK IN BIO for more"}
        assert is_commerce_video(video) is True


class TestScoreTikTokVideo:
    """Test outlier score calculation."""

    def test_basic_scoring(self):
        """Score is play count divided by average."""
        video = {
            "id": "123",
            "playCount": 500000,
            "diggCount": 10000,
            "commentCount": 500,
            "shareCount": 200,
            "authorMeta": {"id": "user1"},
        }
        result = score_tiktok_video(video, hashtag_avg_plays=100000)

        assert result["outlier_score"] == 5.0  # 500k / 100k = 5x
        assert result["source"] == "tiktok"
        assert result["is_commerce"] is False

    def test_commerce_boost(self):
        """Commerce videos get 1.5x boost."""
        video = {
            "id": "456",
            "playCount": 200000,
            "diggCount": 5000,
            "commentCount": 100,
            "shareCount": 50,
            "ttSeller": True,
            "authorMeta": {"id": "seller1"},
        }
        result = score_tiktok_video(video, hashtag_avg_plays=100000)

        # 200k / 100k = 2x, then 2x * 1.5 = 3x
        assert result["outlier_score"] == 3.0
        assert result["is_commerce"] is True

    def test_engagement_metadata(self):
        """Engagement data is extracted correctly."""
        video = {
            "id": "789",
            "playCount": 1000000,
            "diggCount": 50000,
            "commentCount": 2000,
            "shareCount": 1000,
            "authorMeta": {"id": "viral_user"},
        }
        result = score_tiktok_video(video)

        assert result["engagement"]["plays"] == 1000000
        assert result["engagement"]["likes"] == 50000
        assert result["engagement"]["comments"] == 2000
        assert result["engagement"]["shares"] == 1000

    def test_url_construction(self):
        """Video URL is constructed correctly."""
        video = {
            "id": "abc123",
            "playCount": 100000,
            "authorMeta": {"id": "creator_name"},
        }
        result = score_tiktok_video(video)

        assert result["url"] == "https://www.tiktok.com/@creator_name/video/abc123"

    def test_missing_play_count(self):
        """Handle missing or None play count."""
        video = {"id": "999", "playCount": None, "authorMeta": {"id": "user"}}
        result = score_tiktok_video(video)

        assert result["outlier_score"] == 0.0

    def test_zero_average_handling(self):
        """Handle zero average plays (division by zero)."""
        video = {"id": "111", "playCount": 50000, "authorMeta": {"id": "user"}}
        result = score_tiktok_video(video, hashtag_avg_plays=0)

        # Should use max(0, 1) = 1 as divisor
        assert result["outlier_score"] == 50000.0

    def test_missing_author_meta(self):
        """Handle missing author metadata."""
        video = {"id": "222", "playCount": 100000}
        result = score_tiktok_video(video)

        # URL should be empty or have empty author
        assert result["url"] == ""


class TestCommerceKeywords:
    """Test commerce keyword coverage."""

    def test_all_keywords_detected(self):
        """All defined commerce keywords should be detected."""
        for keyword in COMMERCE_KEYWORDS:
            video = {"desc": f"Check out this {keyword} now!"}
            assert is_commerce_video(video) is True, f"Keyword '{keyword}' not detected"
