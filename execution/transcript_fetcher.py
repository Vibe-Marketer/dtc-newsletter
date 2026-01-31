"""
YouTube transcript fetcher.
DOE-VERSION: 2026.01.31

Fetches transcripts for high-scoring YouTube videos.
Per CONTEXT.md: Fetch for top 10 high-scoring videos per run.

Uses youtube-transcript-api library for transcript extraction.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

# Per RESEARCH.md pitfall #1: delay to avoid IP bans
REQUEST_DELAY_SECONDS = 1.5

# Per CONTEXT.md: fetch for top 10 videos
DEFAULT_BATCH_SIZE = 10


def fetch_transcript(video_id: str, languages: list[str] | None = None) -> dict:
    """
    Fetch transcript for a single video.

    Args:
        video_id: YouTube video ID (not full URL)
        languages: Preferred languages (default: ['en'])

    Returns:
        Dict with:
        - video_id: str
        - transcript: list[dict] with {text, start, duration}
        - language: str
        - is_generated: bool
        - fetched_at: ISO timestamp
        - error: str | None
    """
    if languages is None:
        languages = ["en"]

    # Clean video ID (handle URLs)
    video_id = _extract_video_id(video_id)

    try:
        # Create API instance
        ytt_api = YouTubeTranscriptApi()

        # Get list of available transcripts
        transcript_list = ytt_api.list(video_id)

        # Try to find a transcript in preferred languages
        transcript_obj = None
        language_found = None
        is_generated = False

        for lang in languages:
            try:
                # Try manually created first
                transcript_obj = transcript_list.find_manually_created_transcript(
                    [lang]
                )
                language_found = lang
                is_generated = False
                break
            except NoTranscriptFound:
                pass

            try:
                # Fall back to auto-generated
                transcript_obj = transcript_list.find_generated_transcript([lang])
                language_found = lang
                is_generated = True
                break
            except NoTranscriptFound:
                pass

        # If no preferred language found, try any available transcript
        if transcript_obj is None:
            try:
                # Get first available transcript
                for transcript in transcript_list:
                    transcript_obj = transcript
                    language_found = transcript.language_code
                    is_generated = transcript.is_generated
                    break
            except Exception:
                pass

        if transcript_obj is None:
            return {
                "video_id": video_id,
                "transcript": [],
                "language": None,
                "is_generated": None,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "error": "No transcript found in any language",
            }

        # Fetch the actual transcript data
        transcript_data = transcript_obj.fetch()

        return {
            "video_id": video_id,
            "transcript": [
                {
                    "text": segment.text,
                    "start": segment.start,
                    "duration": segment.duration,
                }
                for segment in transcript_data
            ],
            "language": language_found,
            "is_generated": is_generated,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }

    except TranscriptsDisabled:
        return {
            "video_id": video_id,
            "transcript": [],
            "language": None,
            "is_generated": None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": "Transcripts are disabled for this video",
        }
    except NoTranscriptFound:
        return {
            "video_id": video_id,
            "transcript": [],
            "language": None,
            "is_generated": None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": "No transcript available for this video",
        }
    except VideoUnavailable:
        return {
            "video_id": video_id,
            "transcript": [],
            "language": None,
            "is_generated": None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": "Video is unavailable",
        }
    except Exception as e:
        return {
            "video_id": video_id,
            "transcript": [],
            "language": None,
            "is_generated": None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": f"Unexpected error: {type(e).__name__}: {e}",
        }


def fetch_transcripts_batch(
    video_ids: list[str],
    limit: int = DEFAULT_BATCH_SIZE,
    delay: float = REQUEST_DELAY_SECONDS,
    verbose: bool = True,
) -> list[dict]:
    """
    Fetch transcripts for multiple videos with rate limiting.

    Args:
        video_ids: List of video IDs
        limit: Max videos to fetch (default: 10)
        delay: Seconds between requests (default: 1.5)
        verbose: Print progress (default: True)

    Returns:
        List of transcript results (success and failures)
    """
    results = []

    # Clean video IDs
    video_ids = [_extract_video_id(vid) for vid in video_ids]

    for i, video_id in enumerate(video_ids[:limit]):
        if i > 0:
            time.sleep(delay)

        result = fetch_transcript(video_id)
        results.append(result)

        # Log progress
        if verbose:
            status = "OK" if result["error"] is None else f"SKIP: {result['error']}"
            print(f"  [{i + 1}/{min(len(video_ids), limit)}] {video_id}: {status}")

    return results


def save_transcripts(transcripts: list[dict], cache_dir: Path | None = None) -> Path:
    """
    Save transcripts to cache directory.

    Args:
        transcripts: List of transcript results
        cache_dir: Directory to save to (default: data/content_cache/transcripts)

    Returns:
        Path to saved file
    """
    cache_dir = cache_dir or Path("data/content_cache/transcripts")
    cache_dir.mkdir(parents=True, exist_ok=True)

    filename = f"transcripts_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
    filepath = cache_dir / filename

    successful = [t for t in transcripts if t.get("error") is None]
    failed = [t for t in transcripts if t.get("error") is not None]

    cache_data = {
        "metadata": {
            "source": "youtube_transcripts",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "total_videos": len(transcripts),
            "successful": len(successful),
            "failed": len(failed),
            "languages": list(
                set(t["language"] for t in successful if t.get("language"))
            ),
        },
        "transcripts": transcripts,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

    return filepath


def load_transcripts(
    cache_dir: Path | None = None, date: Optional[datetime] = None
) -> list[dict]:
    """
    Load transcripts from cache file.

    Args:
        cache_dir: Cache directory
        date: Date of cache to load (default: today)

    Returns:
        List of transcript dicts

    Raises:
        FileNotFoundError: If cache file doesn't exist
    """
    cache_dir = cache_dir or Path("data/content_cache/transcripts")

    if date is None:
        date = datetime.now(timezone.utc)

    filename = f"transcripts_{date.strftime('%Y-%m-%d')}.json"
    filepath = cache_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Cache file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        cache_data = json.load(f)

    return cache_data.get("transcripts", [])


def get_transcript_text(transcript_data: dict) -> str:
    """
    Extract plain text from transcript data.

    Concatenates all transcript segments into a single string.

    Args:
        transcript_data: Transcript result dict with "transcript" key

    Returns:
        Plain text transcript (empty string if no transcript)
    """
    if not transcript_data.get("transcript"):
        return ""

    return " ".join(
        segment.get("text", "") for segment in transcript_data["transcript"]
    )


def get_transcript_with_timestamps(transcript_data: dict) -> str:
    """
    Format transcript with timestamps.

    Args:
        transcript_data: Transcript result dict

    Returns:
        Formatted transcript with [MM:SS] timestamps
    """
    if not transcript_data.get("transcript"):
        return ""

    lines = []
    for segment in transcript_data["transcript"]:
        start = segment.get("start", 0)
        minutes = int(start // 60)
        seconds = int(start % 60)
        text = segment.get("text", "")
        lines.append(f"[{minutes:02d}:{seconds:02d}] {text}")

    return "\n".join(lines)


def _extract_video_id(video_id_or_url: str) -> str:
    """
    Extract video ID from URL or return as-is.

    Handles various YouTube URL formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - VIDEO_ID (already just the ID)

    Args:
        video_id_or_url: Video ID or YouTube URL

    Returns:
        Extracted video ID
    """
    video_id = video_id_or_url.strip()

    # Handle youtube.com URLs
    if "youtube.com/watch" in video_id:
        # Extract v= parameter
        import re

        match = re.search(r"v=([a-zA-Z0-9_-]{11})", video_id)
        if match:
            return match.group(1)

    # Handle youtu.be URLs
    if "youtu.be/" in video_id:
        # Get ID after the last slash
        video_id = video_id.split("youtu.be/")[-1]
        # Remove any query parameters
        video_id = video_id.split("?")[0].split("&")[0]
        return video_id[:11] if len(video_id) >= 11 else video_id

    # Handle embed URLs
    if "/embed/" in video_id:
        video_id = video_id.split("/embed/")[-1]
        video_id = video_id.split("?")[0].split("&")[0]
        return video_id[:11] if len(video_id) >= 11 else video_id

    # Assume it's already a video ID
    return video_id


def fetch_transcripts_for_videos(
    videos: list[dict], id_key: str = "id", limit: int = DEFAULT_BATCH_SIZE, **kwargs
) -> list[dict]:
    """
    Fetch transcripts for a list of video dicts.

    Convenience function that extracts video IDs from video dicts.

    Args:
        videos: List of video dicts with ID field
        id_key: Key containing video ID (default: "id")
        limit: Max videos to fetch
        **kwargs: Additional args for fetch_transcripts_batch

    Returns:
        List of transcript results
    """
    video_ids = [v[id_key] for v in videos[:limit] if id_key in v]
    return fetch_transcripts_batch(video_ids, limit=limit, **kwargs)
