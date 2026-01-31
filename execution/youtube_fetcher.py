"""
YouTube video fetcher with outlier detection.
DOE-VERSION: 2026.01.31

Fetches videos from DTC/e-commerce channels and calculates outlier scores.
Uses TubeLab API (primary) with YouTube Data API fallback.

Per 02-TUBELAB-DECISION.md:
- TubeLab API: https://public-api.tubelab.net/v1
- Auth: Authorization: Api-Key {key}
- Rate Limit: 10 requests/minute
- Key Endpoint: GET /search/outliers?query=<topic> (5 credits)
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

# Check if YouTube Data API client is available
try:
    import googleapiclient.discovery  # noqa: F401

    YOUTUBE_DATA_API_AVAILABLE = True
except ImportError:
    YOUTUBE_DATA_API_AVAILABLE = False

from execution.scoring import calculate_recency_boost, calculate_engagement_modifiers

# Load environment variables
load_dotenv()

# TubeLab API configuration
TUBELAB_BASE_URL = "https://public-api.tubelab.net/v1"
TUBELAB_RATE_LIMIT_PER_MIN = 10
TUBELAB_REQUEST_DELAY = 60.0 / TUBELAB_RATE_LIMIT_PER_MIN  # 6 seconds between requests

# Default DTC/e-commerce search topics (for TubeLab outlier search)
DEFAULT_SEARCH_TOPICS = [
    "ecommerce tips",
    "dropshipping strategy",
    "shopify store",
    "dtc brand",
    "amazon fba",
]

# Outlier threshold per CONTEXT.md: 5x channel average
MIN_OUTLIER_SCORE = 5.0

# Time window per CONTEXT.md: last 14 days
DAYS_LOOKBACK = 14


class TubeLabClient:
    """Client for TubeLab API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TubeLab client.

        Args:
            api_key: TubeLab API key (or from TUBELAB_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("TUBELAB_API_KEY")
        self.base_url = TUBELAB_BASE_URL
        self._last_request_time = 0.0

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def _rate_limit(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < TUBELAB_REQUEST_DELAY:
            time.sleep(TUBELAB_REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def search_outliers(self, query: str, limit: int = 50) -> dict:
        """
        Search for outlier videos on a topic.

        Args:
            query: Search topic (e.g., "ecommerce tips")
            limit: Maximum results to return

        Returns:
            API response dict with outlier videos

        Raises:
            ValueError: If API key not configured
            requests.HTTPError: If API request fails
        """
        if not self.is_configured:
            raise ValueError("TUBELAB_API_KEY environment variable required")

        self._rate_limit()

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        params = {
            "query": query,
            "limit": limit,
        }

        response = requests.get(
            f"{self.base_url}/search/outliers",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        return response.json()

    def get_video_details(self, video_id: str) -> dict:
        """
        Get details for a specific video.

        Args:
            video_id: YouTube video ID

        Returns:
            Video details dict
        """
        if not self.is_configured:
            raise ValueError("TUBELAB_API_KEY environment variable required")

        self._rate_limit()

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
        }

        response = requests.get(
            f"{self.base_url}/videos/{video_id}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        return response.json()


class YouTubeDataAPIClient:
    """Fallback client using YouTube Data API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube Data API client.

        Args:
            api_key: YouTube API key (or from YOUTUBE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self._client = None

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def _get_client(self):
        """Get or create YouTube API client."""
        if self._client is None:
            if not self.is_configured:
                raise ValueError("YOUTUBE_API_KEY environment variable required")
            if not YOUTUBE_DATA_API_AVAILABLE:
                raise ImportError(
                    "google-api-python-client required. "
                    "Run: pip install google-api-python-client"
                )
            # Import build function at use time since it may not be available
            from googleapiclient.discovery import build as yt_build

            self._client = yt_build("youtube", "v3", developerKey=self.api_key)
        return self._client

    def search_videos(
        self,
        query: str,
        max_results: int = 50,
        published_after: Optional[datetime] = None,
    ) -> list[dict]:
        """
        Search for videos on a topic.

        Args:
            query: Search query
            max_results: Maximum results to return (max 50 per request)
            published_after: Only include videos published after this date

        Returns:
            List of video search results
        """
        client = self._get_client()

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50),
            "order": "relevance",
        }

        if published_after:
            params["publishedAfter"] = published_after.isoformat() + "Z"

        response = client.search().list(**params).execute()
        return response.get("items", [])

    def get_video_statistics(self, video_ids: list[str]) -> dict[str, dict]:
        """
        Get statistics for multiple videos.

        Args:
            video_ids: List of video IDs (max 50)

        Returns:
            Dict mapping video_id to statistics
        """
        if not video_ids:
            return {}

        client = self._get_client()

        # API accepts up to 50 IDs
        video_ids = video_ids[:50]

        response = (
            client.videos()
            .list(part="statistics,snippet", id=",".join(video_ids))
            .execute()
        )

        result = {}
        for item in response.get("items", []):
            video_id = item["id"]
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            result[video_id] = {
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "published_at": snippet.get("publishedAt", ""),
            }

        return result

    def get_channel_videos(self, channel_id: str, max_results: int = 50) -> list[dict]:
        """
        Get recent videos from a channel.

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum results to return

        Returns:
            List of video details with statistics
        """
        client = self._get_client()

        # First get the uploads playlist ID
        channel_response = (
            client.channels().list(part="contentDetails", id=channel_id).execute()
        )

        if not channel_response.get("items"):
            return []

        uploads_playlist_id = (
            channel_response["items"][0]
            .get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )

        if not uploads_playlist_id:
            return []

        # Get videos from uploads playlist
        playlist_response = (
            client.playlistItems()
            .list(
                part="contentDetails,snippet",
                playlistId=uploads_playlist_id,
                maxResults=min(max_results, 50),
            )
            .execute()
        )

        video_ids = [
            item["contentDetails"]["videoId"]
            for item in playlist_response.get("items", [])
        ]

        # Get statistics for these videos
        return list(self.get_video_statistics(video_ids).values())


class YouTubeFetcher:
    """YouTube video fetcher with outlier detection using TubeLab + YouTube fallback."""

    def __init__(
        self,
        tubelab_api_key: Optional[str] = None,
        youtube_api_key: Optional[str] = None,
        prefer_tubelab: bool = True,
    ):
        """
        Initialize fetcher.

        Args:
            tubelab_api_key: TubeLab API key (or from env)
            youtube_api_key: YouTube API key (or from env)
            prefer_tubelab: If True, try TubeLab first (default True)
        """
        self.tubelab = TubeLabClient(tubelab_api_key)
        self.youtube = YouTubeDataAPIClient(youtube_api_key)
        self.prefer_tubelab = prefer_tubelab
        self._channel_avg_cache: dict[str, float] = {}

    @property
    def tubelab_available(self) -> bool:
        """Check if TubeLab API is available."""
        return self.tubelab.is_configured

    @property
    def youtube_available(self) -> bool:
        """Check if YouTube Data API is available."""
        return self.youtube.is_configured and YOUTUBE_DATA_API_AVAILABLE

    def fetch_outliers_tubelab(
        self,
        topics: list[str] | None = None,
        min_outlier_score: float = MIN_OUTLIER_SCORE,
    ) -> list[dict]:
        """
        Fetch outlier videos using TubeLab API.

        Args:
            topics: Search topics (default: DEFAULT_SEARCH_TOPICS)
            min_outlier_score: Minimum outlier score to include

        Returns:
            List of standardized video dicts
        """
        if not self.tubelab_available:
            raise ValueError("TubeLab API not configured")

        topics = topics or DEFAULT_SEARCH_TOPICS
        all_videos = []
        seen_ids = set()

        for topic in topics:
            try:
                response = self.tubelab.search_outliers(topic)
                videos = response.get("videos", response.get("data", []))

                for video in videos:
                    video_id = video.get("id") or video.get("video_id")
                    if video_id and video_id not in seen_ids:
                        seen_ids.add(video_id)

                        # Normalize TubeLab response to standard format
                        outlier_score = video.get("outlier_score", 0)
                        if outlier_score >= min_outlier_score:
                            normalized = self._normalize_tubelab_video(video)
                            all_videos.append(normalized)

            except requests.HTTPError as e:
                print(f"TubeLab API error for topic '{topic}': {e}")
                continue
            except Exception as e:
                print(f"Error fetching topic '{topic}': {e}")
                continue

        # Sort by outlier score descending
        all_videos.sort(key=lambda x: x.get("outlier_score", 0), reverse=True)

        return all_videos

    def _normalize_tubelab_video(self, video: dict) -> dict:
        """
        Normalize TubeLab video response to standard format.

        Args:
            video: TubeLab API video dict

        Returns:
            Standardized video dict
        """
        video_id = video.get("id") or video.get("video_id", "")
        title = video.get("title", "")
        description = video.get("description", "")

        # TubeLab may provide these directly
        outlier_score = video.get("outlier_score", 0)
        views = video.get("views") or video.get("view_count", 0)
        channel_avg = video.get("channel_average") or video.get("channel_avg_views", 0)

        # Calculate recency and engagement modifiers for consistency
        published_at = video.get("published_at") or video.get("publishedAt", "")
        recency_boost = 1.0
        if published_at:
            try:
                pub_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                recency_boost = calculate_recency_boost(pub_dt.timestamp())
            except (ValueError, TypeError):
                pass

        engagement_mod = calculate_engagement_modifiers(title, description)

        return {
            "id": video_id,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail_url": video.get("thumbnail_url") or video.get("thumbnail", ""),
            "views": views,
            "channel_name": video.get("channel_name") or video.get("channel_title", ""),
            "channel_id": video.get("channel_id", ""),
            "channel_avg_views": channel_avg,
            "outlier_score": round(outlier_score, 2),
            "recency_boost": round(recency_boost, 2),
            "engagement_modifiers": round(engagement_mod, 2),
            "published_at": published_at,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source": "youtube",
            "api_source": "tubelab",
        }

    def fetch_outliers_youtube(
        self,
        topics: list[str] | None = None,
        min_outlier_score: float = MIN_OUTLIER_SCORE,
        days_back: int = DAYS_LOOKBACK,
    ) -> list[dict]:
        """
        Fetch and calculate outlier videos using YouTube Data API.

        Args:
            topics: Search topics (default: DEFAULT_SEARCH_TOPICS)
            min_outlier_score: Minimum outlier score to include
            days_back: Only include videos from last N days

        Returns:
            List of standardized video dicts
        """
        if not self.youtube_available:
            raise ValueError("YouTube Data API not configured or not installed")

        topics = topics or DEFAULT_SEARCH_TOPICS
        published_after = datetime.now(timezone.utc) - timedelta(days=days_back)

        all_videos = []
        seen_ids = set()

        for topic in topics:
            try:
                # Search for videos
                search_results = self.youtube.search_videos(
                    query=topic, max_results=25, published_after=published_after
                )

                # Get video IDs from search results
                video_ids = [
                    item["id"]["videoId"]
                    for item in search_results
                    if "videoId" in item.get("id", {})
                ]

                # Get detailed statistics
                stats = self.youtube.get_video_statistics(video_ids)

                for video_id, video_stats in stats.items():
                    if video_id in seen_ids:
                        continue
                    seen_ids.add(video_id)

                    # Calculate channel average (cached)
                    channel_id = video_stats.get("channel_id", "")
                    if channel_id:
                        channel_avg = self._get_channel_average(channel_id)
                    else:
                        channel_avg = 1000  # Default fallback

                    # Calculate outlier score
                    outlier_score = self.calculate_outlier_score(
                        views=video_stats.get("view_count", 0),
                        channel_avg=channel_avg,
                        published_at=video_stats.get("published_at", ""),
                        title=video_stats.get("title", ""),
                        description=video_stats.get("description", ""),
                    )

                    if outlier_score >= min_outlier_score:
                        normalized = self._normalize_youtube_video(
                            video_id, video_stats, channel_avg, outlier_score
                        )
                        all_videos.append(normalized)

            except Exception as e:
                print(f"YouTube API error for topic '{topic}': {e}")
                continue

        # Sort by outlier score descending
        all_videos.sort(key=lambda x: x.get("outlier_score", 0), reverse=True)

        return all_videos

    def _get_channel_average(self, channel_id: str) -> float:
        """
        Get average views for a channel (cached).

        Args:
            channel_id: YouTube channel ID

        Returns:
            Average view count for channel's recent videos
        """
        if channel_id in self._channel_avg_cache:
            return self._channel_avg_cache[channel_id]

        try:
            videos = self.youtube.get_channel_videos(channel_id, max_results=50)
            if videos:
                total_views = sum(v.get("view_count", 0) for v in videos)
                avg = total_views / len(videos)
                self._channel_avg_cache[channel_id] = avg
                return avg
        except Exception as e:
            print(f"Error getting channel average for {channel_id}: {e}")

        # Default fallback
        return 1000.0

    def calculate_outlier_score(
        self,
        views: int,
        channel_avg: float,
        published_at: str,
        title: str,
        description: str = "",
    ) -> float:
        """
        Calculate outlier score for a video.

        Uses same formula as Reddit scoring:
        score = (views / channel_avg) * recency_boost * engagement_modifiers

        Args:
            views: Video view count
            channel_avg: Channel's average view count
            published_at: ISO timestamp when video was published
            title: Video title
            description: Video description

        Returns:
            Outlier score (e.g., 6.81 = ~7x better than channel average)
        """
        if channel_avg <= 0:
            channel_avg = 1.0  # Prevent division by zero

        # Base score: how many times better than channel average
        base_score = views / channel_avg

        # Calculate recency boost
        recency_boost = 1.0
        if published_at:
            try:
                pub_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                recency_boost = calculate_recency_boost(pub_dt.timestamp())
            except (ValueError, TypeError):
                pass

        # Calculate engagement modifiers
        engagement = calculate_engagement_modifiers(title, description)

        return base_score * recency_boost * engagement

    def _normalize_youtube_video(
        self, video_id: str, stats: dict, channel_avg: float, outlier_score: float
    ) -> dict:
        """
        Normalize YouTube video data to standard format.

        Args:
            video_id: YouTube video ID
            stats: Video statistics dict
            channel_avg: Channel's average views
            outlier_score: Calculated outlier score

        Returns:
            Standardized video dict
        """
        title = stats.get("title", "")
        description = stats.get("description", "")
        published_at = stats.get("published_at", "")

        # Calculate modifiers for metadata
        recency_boost = 1.0
        if published_at:
            try:
                pub_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                recency_boost = calculate_recency_boost(pub_dt.timestamp())
            except (ValueError, TypeError):
                pass

        engagement_mod = calculate_engagement_modifiers(title, description)

        return {
            "id": video_id,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "views": stats.get("view_count", 0),
            "like_count": stats.get("like_count", 0),
            "comment_count": stats.get("comment_count", 0),
            "channel_name": stats.get("channel_title", ""),
            "channel_id": stats.get("channel_id", ""),
            "channel_avg_views": round(channel_avg, 2),
            "outlier_score": round(outlier_score, 2),
            "recency_boost": round(recency_boost, 2),
            "engagement_modifiers": round(engagement_mod, 2),
            "published_at": published_at,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source": "youtube",
            "api_source": "youtube_data_api",
        }

    def fetch_outliers(
        self,
        topics: list[str] | None = None,
        min_outlier_score: float = MIN_OUTLIER_SCORE,
    ) -> list[dict]:
        """
        Fetch outlier videos using best available API.

        Tries TubeLab first (if configured and prefer_tubelab=True),
        falls back to YouTube Data API if TubeLab fails.

        Args:
            topics: Search topics
            min_outlier_score: Minimum outlier score to include

        Returns:
            List of standardized video dicts sorted by outlier score

        Raises:
            ValueError: If no API is configured
        """
        # Try TubeLab first if preferred and available
        if self.prefer_tubelab and self.tubelab_available:
            try:
                videos = self.fetch_outliers_tubelab(topics, min_outlier_score)
                if videos:
                    return videos
                print("TubeLab returned no results, falling back to YouTube Data API")
            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    print(
                        "TubeLab rate limit exceeded, falling back to YouTube Data API"
                    )
                else:
                    print(f"TubeLab API error: {e}, falling back to YouTube Data API")
            except Exception as e:
                print(f"TubeLab error: {e}, falling back to YouTube Data API")

        # Fallback to YouTube Data API
        if self.youtube_available:
            return self.fetch_outliers_youtube(topics, min_outlier_score)

        # Neither API available
        if self.tubelab_available:
            # TubeLab configured but failed, try again without fallback
            return self.fetch_outliers_tubelab(topics, min_outlier_score)

        raise ValueError(
            "No YouTube API configured. "
            "Set TUBELAB_API_KEY or YOUTUBE_API_KEY in environment."
        )


def fetch_channel_videos(channel_id: str, **kwargs) -> list[dict]:
    """
    Convenience function to fetch videos from a specific channel.

    Uses YouTube Data API directly (TubeLab is topic-based).

    Args:
        channel_id: YouTube channel ID
        **kwargs: Additional arguments for YouTubeDataAPIClient.get_channel_videos

    Returns:
        List of video dicts
    """
    client = YouTubeDataAPIClient()
    return client.get_channel_videos(channel_id, **kwargs)


def calculate_channel_average(channel_id: str) -> float:
    """
    Calculate average views for a channel.

    Args:
        channel_id: YouTube channel ID

    Returns:
        Average view count
    """
    fetcher = YouTubeFetcher()
    return fetcher._get_channel_average(channel_id)


def save_youtube_videos(videos: list[dict], cache_dir: Path | None = None) -> Path:
    """
    Save videos to cache (same pattern as Reddit storage).

    Args:
        videos: List of video dicts
        cache_dir: Directory to save to (default: data/content_cache/youtube)

    Returns:
        Path to saved file
    """
    cache_dir = cache_dir or Path("data/content_cache/youtube")
    cache_dir.mkdir(parents=True, exist_ok=True)

    filename = f"youtube_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
    filepath = cache_dir / filename

    cache_data = {
        "metadata": {
            "source": "youtube",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "video_count": len(videos),
            "api_sources": list(set(v.get("api_source", "unknown") for v in videos)),
        },
        "videos": videos,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

    return filepath
