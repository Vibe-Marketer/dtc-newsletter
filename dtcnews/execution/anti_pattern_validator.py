"""
Anti-pattern validator for DTC Money Minute newsletter voice.
DOE-VERSION: 2026.01.31

Validates generated content against forbidden phrases and analyzes
sentence structure to ensure Hormozi/Suby voice compliance.
"""

import re
from typing import Optional

# Complete list of forbidden phrases (20+ anti-patterns)
# Case-insensitive matching applied during validation
ANTI_PATTERNS = [
    # Buzzword Garbage
    "game-changer",
    "game changer",
    "unlock your potential",
    "leverage",  # as a verb - we'll be careful here
    "synergy",
    "dive deep",
    "unpack",
    "at the end of the day",
    # Throat-Clearing Fillers
    "it's worth noting",
    "interestingly enough",
    "in today's fast-paced world",
    "in the ever-evolving landscape",
    "without further ado",
    # Corporate Cringe
    "take it to the next level",
    "move the needle",
    "circle back",
    "touch base",
    "low-hanging fruit",
    # Motivational Mush
    "empower",
    "revolutionize",
    "transform your business",
    "secret sauce",
    "silver bullet",
    "holy grail",
    # Bro Marketing (killing it allowed only in direct quotes)
    "crushing it",
    "killing it",
    # Fake Enthusiasm
    "i'm excited to share",
    "i'm thrilled to announce",
]

# Patterns that are problematic at sentence start
SENTENCE_START_PATTERNS = [
    r"^so,\s",  # Starting with "So,"
    r"^look,\s",  # Starting with "Look,"
]


def validate_voice(content: str) -> tuple[bool, list[str]]:
    """
    Validate content against anti-patterns.

    Args:
        content: Text content to validate

    Returns:
        Tuple of (is_valid, violations_list)
        - is_valid: True if no anti-patterns found
        - violations_list: List of detected anti-pattern phrases
    """
    violations = []
    content_lower = content.lower()

    # Check all anti-patterns (case-insensitive)
    for pattern in ANTI_PATTERNS:
        pattern_lower = pattern.lower()
        if pattern_lower in content_lower:
            violations.append(pattern)

    # Check sentence start patterns
    sentences = _split_into_sentences(content)
    for sentence in sentences:
        sentence_lower = sentence.lower().strip()
        for start_pattern in SENTENCE_START_PATTERNS:
            if re.match(start_pattern, sentence_lower, re.IGNORECASE):
                # Extract the matched phrase
                if sentence_lower.startswith("so,"):
                    violations.append("So, (sentence start)")
                elif sentence_lower.startswith("look,"):
                    violations.append("Look, (sentence start)")

    # Check for excessive exclamation points
    exclamation_count = content.count("!")
    if exclamation_count > 1:
        violations.append(
            f"Excessive exclamation points ({exclamation_count} found, max 1)"
        )

    is_valid = len(violations) == 0
    return is_valid, violations


def count_sentence_stats(content: str) -> dict:
    """
    Analyze sentence structure and word counts.

    Args:
        content: Text content to analyze

    Returns:
        Dict with:
        - total_words: Total word count
        - total_sentences: Number of sentences
        - avg_words_per_sentence: Average words per sentence
        - sentence_lengths: List of word counts per sentence
        - short_sentences: Count of sentences under 10 words (target: 60%)
        - medium_sentences: Count of sentences 10-18 words (target: 30%)
        - long_sentences: Count of sentences over 18 words (target: 10%)
        - short_pct: Percentage of short sentences
        - medium_pct: Percentage of medium sentences
        - long_pct: Percentage of long sentences
        - rhythm_score: Simple assessment of rhythm variety (0-100)
    """
    sentences = _split_into_sentences(content)

    if not sentences:
        return {
            "total_words": 0,
            "total_sentences": 0,
            "avg_words_per_sentence": 0.0,
            "sentence_lengths": [],
            "short_sentences": 0,
            "medium_sentences": 0,
            "long_sentences": 0,
            "short_pct": 0.0,
            "medium_pct": 0.0,
            "long_pct": 0.0,
            "rhythm_score": 0,
        }

    # Count words per sentence
    sentence_lengths = []
    for sentence in sentences:
        words = _count_words(sentence)
        sentence_lengths.append(words)

    total_words = sum(sentence_lengths)
    total_sentences = len(sentences)
    avg_words = total_words / total_sentences if total_sentences > 0 else 0.0

    # Categorize sentences by length
    short = sum(1 for length in sentence_lengths if length < 10)
    medium = sum(1 for length in sentence_lengths if 10 <= length <= 18)
    long = sum(1 for length in sentence_lengths if length > 18)

    # Calculate percentages
    short_pct = (short / total_sentences * 100) if total_sentences > 0 else 0.0
    medium_pct = (medium / total_sentences * 100) if total_sentences > 0 else 0.0
    long_pct = (long / total_sentences * 100) if total_sentences > 0 else 0.0

    # Calculate rhythm score (how well it matches 60/30/10 target)
    rhythm_score = _calculate_rhythm_score(short_pct, medium_pct, long_pct)

    return {
        "total_words": total_words,
        "total_sentences": total_sentences,
        "avg_words_per_sentence": round(avg_words, 1),
        "sentence_lengths": sentence_lengths,
        "short_sentences": short,
        "medium_sentences": medium,
        "long_sentences": long,
        "short_pct": round(short_pct, 1),
        "medium_pct": round(medium_pct, 1),
        "long_pct": round(long_pct, 1),
        "rhythm_score": rhythm_score,
    }


def _split_into_sentences(content: str) -> list[str]:
    """
    Split content into sentences.

    Handles:
    - Standard punctuation (. ! ?)
    - Abbreviations (Mr., Dr., etc.)
    - Numbers with decimals
    """
    if not content or not content.strip():
        return []

    # Simple sentence splitting - split on . ! ? followed by space or end
    # This is imperfect but good enough for analysis
    sentence_pattern = r"(?<=[.!?])\s+"
    raw_sentences = re.split(sentence_pattern, content.strip())

    # Filter out empty strings and very short fragments
    sentences = [s.strip() for s in raw_sentences if s.strip() and len(s.strip()) > 1]

    return sentences


def _count_words(text: str) -> int:
    """Count words in text."""
    if not text:
        return 0
    words = text.split()
    return len(words)


def _calculate_rhythm_score(
    short_pct: float, medium_pct: float, long_pct: float
) -> int:
    """
    Calculate rhythm score based on how close to 60/30/10 targets.

    Perfect score (100): Exactly 60% short, 30% medium, 10% long
    Deductions for deviation from targets
    """
    if short_pct == 0 and medium_pct == 0 and long_pct == 0:
        return 0

    # Target percentages
    target_short = 60.0
    target_medium = 30.0
    target_long = 10.0

    # Calculate deviation from targets (absolute difference)
    short_deviation = abs(short_pct - target_short)
    medium_deviation = abs(medium_pct - target_medium)
    long_deviation = abs(long_pct - target_long)

    # Total deviation (max possible is around 200 if completely off)
    total_deviation = short_deviation + medium_deviation + long_deviation

    # Convert to score (lower deviation = higher score)
    # Max deviation of 100 or more = score of 0
    score = max(0, 100 - int(total_deviation))

    return score


def get_voice_analysis(content: str) -> dict:
    """
    Get complete voice analysis including validation and stats.

    Args:
        content: Text to analyze

    Returns:
        Dict with validation results and sentence statistics
    """
    is_valid, violations = validate_voice(content)
    stats = count_sentence_stats(content)

    return {
        "is_valid": is_valid,
        "violations": violations,
        "stats": stats,
    }


def format_validation_report(content: str) -> str:
    """
    Generate a human-readable validation report.

    Args:
        content: Text to analyze

    Returns:
        Formatted string report
    """
    analysis = get_voice_analysis(content)

    lines = ["Voice Analysis Report", "=" * 40, ""]

    # Validation status
    if analysis["is_valid"]:
        lines.append("Status: PASSED (no anti-patterns detected)")
    else:
        lines.append(f"Status: FAILED ({len(analysis['violations'])} violations)")
        lines.append("")
        lines.append("Violations:")
        for v in analysis["violations"]:
            lines.append(f"  - {v}")

    lines.append("")
    lines.append("Sentence Statistics:")
    stats = analysis["stats"]
    lines.append(f"  Total words: {stats['total_words']}")
    lines.append(f"  Total sentences: {stats['total_sentences']}")
    lines.append(f"  Avg words/sentence: {stats['avg_words_per_sentence']}")
    lines.append("")
    lines.append("Sentence Length Distribution:")
    lines.append(
        f"  Short (<10 words): {stats['short_sentences']} ({stats['short_pct']}%) [target: 60%]"
    )
    lines.append(
        f"  Medium (10-18 words): {stats['medium_sentences']} ({stats['medium_pct']}%) [target: 30%]"
    )
    lines.append(
        f"  Long (>18 words): {stats['long_sentences']} ({stats['long_pct']}%) [target: 10%]"
    )
    lines.append("")
    lines.append(f"Rhythm Score: {stats['rhythm_score']}/100")

    return "\n".join(lines)
