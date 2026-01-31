"""
Tests for anti_pattern_validator module.
DOE-VERSION: 2026.01.31
"""

import pytest
from execution.anti_pattern_validator import (
    ANTI_PATTERNS,
    validate_voice,
    count_sentence_stats,
    get_voice_analysis,
    format_validation_report,
)


class TestAntiPatternsList:
    """Test ANTI_PATTERNS constant."""

    def test_is_list(self):
        """Should be a list."""
        assert isinstance(ANTI_PATTERNS, list)

    def test_has_twenty_plus_patterns(self):
        """Should have 20+ forbidden phrases."""
        assert len(ANTI_PATTERNS) >= 20, (
            f"Expected 20+ patterns, got {len(ANTI_PATTERNS)}"
        )

    def test_contains_buzzword_garbage(self):
        """Should include buzzword garbage patterns."""
        patterns_lower = [p.lower() for p in ANTI_PATTERNS]
        assert "game-changer" in patterns_lower or "game changer" in patterns_lower
        assert "unlock your potential" in patterns_lower
        assert "synergy" in patterns_lower
        assert "dive deep" in patterns_lower

    def test_contains_throat_clearing(self):
        """Should include throat-clearing patterns."""
        patterns_lower = [p.lower() for p in ANTI_PATTERNS]
        assert "it's worth noting" in patterns_lower
        assert "interestingly enough" in patterns_lower
        assert "without further ado" in patterns_lower

    def test_contains_corporate_cringe(self):
        """Should include corporate cringe patterns."""
        patterns_lower = [p.lower() for p in ANTI_PATTERNS]
        assert "take it to the next level" in patterns_lower
        assert "move the needle" in patterns_lower
        assert "circle back" in patterns_lower

    def test_contains_motivational_mush(self):
        """Should include motivational mush patterns."""
        patterns_lower = [p.lower() for p in ANTI_PATTERNS]
        assert "empower" in patterns_lower
        assert "revolutionize" in patterns_lower
        assert "secret sauce" in patterns_lower

    def test_contains_bro_marketing(self):
        """Should include bro marketing patterns."""
        patterns_lower = [p.lower() for p in ANTI_PATTERNS]
        assert "crushing it" in patterns_lower
        assert "killing it" in patterns_lower

    def test_contains_fake_enthusiasm(self):
        """Should include fake enthusiasm patterns."""
        patterns_lower = [p.lower() for p in ANTI_PATTERNS]
        assert "i'm excited to share" in patterns_lower
        assert "i'm thrilled to announce" in patterns_lower


class TestValidateVoice:
    """Test validate_voice function."""

    def test_clean_text_passes(self):
        """Clean text without anti-patterns should pass."""
        clean_text = (
            "This tactic generated $47K in revenue last month. Here's how it works."
        )
        is_valid, violations = validate_voice(clean_text)
        assert is_valid is True
        assert violations == []

    def test_detects_game_changer(self):
        """Should detect 'game-changer' pattern."""
        text = "This tool is a game-changer for your business."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any(
            "game-changer" in v.lower() or "game changer" in v.lower()
            for v in violations
        )

    def test_detects_unlock_potential(self):
        """Should detect 'unlock your potential' pattern."""
        text = "We help you unlock your potential as an entrepreneur."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("unlock your potential" in v.lower() for v in violations)

    def test_detects_leverage(self):
        """Should detect 'leverage' pattern."""
        text = "You can leverage this strategy to grow your store."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("leverage" in v.lower() for v in violations)

    def test_detects_synergy(self):
        """Should detect 'synergy' pattern."""
        text = "There's great synergy between these tools."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("synergy" in v.lower() for v in violations)

    def test_detects_dive_deep(self):
        """Should detect 'dive deep' pattern."""
        text = "Let's dive deep into this strategy."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("dive deep" in v.lower() for v in violations)

    def test_detects_at_end_of_day(self):
        """Should detect 'at the end of the day' pattern."""
        text = "At the end of the day, revenue matters most."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("at the end of the day" in v.lower() for v in violations)

    def test_detects_worth_noting(self):
        """Should detect 'it's worth noting' pattern."""
        text = "It's worth noting that this works best for DTC brands."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("it's worth noting" in v.lower() for v in violations)

    def test_detects_fast_paced_world(self):
        """Should detect 'in today's fast-paced world' pattern."""
        text = "In today's fast-paced world of e-commerce, speed matters."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("fast-paced world" in v.lower() for v in violations)

    def test_detects_next_level(self):
        """Should detect 'take it to the next level' pattern."""
        text = "Ready to take it to the next level?"
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("next level" in v.lower() for v in violations)

    def test_detects_move_needle(self):
        """Should detect 'move the needle' pattern."""
        text = "This will really move the needle for your business."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("move the needle" in v.lower() for v in violations)

    def test_detects_circle_back(self):
        """Should detect 'circle back' pattern."""
        text = "Let's circle back on this next week."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("circle back" in v.lower() for v in violations)

    def test_detects_empower(self):
        """Should detect 'empower' pattern."""
        text = "Our mission is to empower entrepreneurs."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("empower" in v.lower() for v in violations)

    def test_detects_revolutionize(self):
        """Should detect 'revolutionize' pattern."""
        text = "This will revolutionize how you sell."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("revolutionize" in v.lower() for v in violations)

    def test_detects_secret_sauce(self):
        """Should detect 'secret sauce' pattern."""
        text = "The secret sauce is consistency."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("secret sauce" in v.lower() for v in violations)

    def test_detects_crushing_it(self):
        """Should detect 'crushing it' pattern."""
        text = "These brands are crushing it right now."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("crushing it" in v.lower() for v in violations)

    def test_detects_excited_to_share(self):
        """Should detect 'I'm excited to share' pattern."""
        text = "I'm excited to share this new strategy with you."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("excited to share" in v.lower() for v in violations)

    def test_case_insensitive_detection(self):
        """Detection should be case-insensitive."""
        text = "THIS IS A GAME-CHANGER FOR YOUR BUSINESS."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert len(violations) > 0

    def test_detects_multiple_violations(self):
        """Should detect multiple violations in same text."""
        text = "This game-changer will help you unlock your potential and revolutionize your business."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert len(violations) >= 3

    def test_detects_sentence_start_so(self):
        """Should detect sentences starting with 'So,'."""
        text = "So, here's what you need to know. It works."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("So," in v for v in violations)

    def test_detects_sentence_start_look(self):
        """Should detect sentences starting with 'Look,'."""
        text = "Look, I get it. Starting is hard."
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("Look," in v for v in violations)

    def test_detects_excessive_exclamation_points(self):
        """Should detect excessive exclamation points (more than 1)."""
        text = "This is amazing! You'll love it! Try it now!"
        is_valid, violations = validate_voice(text)
        assert is_valid is False
        assert any("exclamation" in v.lower() for v in violations)

    def test_single_exclamation_allowed(self):
        """Single exclamation point should be allowed."""
        text = "This strategy generated $50K in revenue last month!"
        is_valid, violations = validate_voice(text)
        # Should pass (no anti-patterns, only 1 exclamation)
        assert is_valid is True


class TestCountSentenceStats:
    """Test count_sentence_stats function."""

    def test_empty_content(self):
        """Should handle empty content."""
        stats = count_sentence_stats("")
        assert stats["total_words"] == 0
        assert stats["total_sentences"] == 0
        assert stats["avg_words_per_sentence"] == 0.0

    def test_single_sentence(self):
        """Should count single sentence correctly."""
        text = "This is a short sentence."
        stats = count_sentence_stats(text)
        assert stats["total_sentences"] == 1
        assert stats["total_words"] == 5

    def test_multiple_sentences(self):
        """Should count multiple sentences correctly."""
        text = "First sentence here. Second sentence here. Third one."
        stats = count_sentence_stats(text)
        assert stats["total_sentences"] == 3

    def test_word_count_accuracy(self):
        """Should count words accurately."""
        text = "One two three four five. Six seven eight nine ten."
        stats = count_sentence_stats(text)
        assert stats["total_words"] == 10

    def test_average_calculation(self):
        """Should calculate average words per sentence correctly."""
        text = "One two three. Four five six. Seven eight nine."
        stats = count_sentence_stats(text)
        assert stats["avg_words_per_sentence"] == 3.0

    def test_short_sentence_classification(self):
        """Should classify short sentences (under 10 words)."""
        text = "Short one. Also short. Tiny."
        stats = count_sentence_stats(text)
        assert stats["short_sentences"] == 3
        assert stats["medium_sentences"] == 0
        assert stats["long_sentences"] == 0

    def test_medium_sentence_classification(self):
        """Should classify medium sentences (10-18 words)."""
        text = "This is a medium length sentence that has exactly twelve words in it."
        stats = count_sentence_stats(text)
        assert stats["medium_sentences"] == 1

    def test_long_sentence_classification(self):
        """Should classify long sentences (over 18 words)."""
        text = "This is a very long sentence that goes on and on and on and contains way more than eighteen words total which makes it long."
        stats = count_sentence_stats(text)
        assert stats["long_sentences"] == 1

    def test_percentage_calculations(self):
        """Should calculate percentages correctly."""
        # 3 short sentences = 100% short
        text = "Short. Also short. Tiny."
        stats = count_sentence_stats(text)
        assert stats["short_pct"] == 100.0
        assert stats["medium_pct"] == 0.0
        assert stats["long_pct"] == 0.0

    def test_rhythm_score_exists(self):
        """Should calculate rhythm score."""
        text = "Short. Medium length here. Another short one."
        stats = count_sentence_stats(text)
        assert "rhythm_score" in stats
        assert isinstance(stats["rhythm_score"], int)
        assert 0 <= stats["rhythm_score"] <= 100

    def test_sentence_lengths_list(self):
        """Should return list of sentence lengths."""
        text = "One two. Three four five. Six."
        stats = count_sentence_stats(text)
        assert stats["sentence_lengths"] == [2, 3, 1]


class TestGetVoiceAnalysis:
    """Test get_voice_analysis function."""

    def test_returns_complete_analysis(self):
        """Should return dict with validation and stats."""
        text = "This is clean text. No anti-patterns here."
        analysis = get_voice_analysis(text)

        assert "is_valid" in analysis
        assert "violations" in analysis
        assert "stats" in analysis

    def test_analysis_includes_validation(self):
        """Should include validation results."""
        text = "This is a game-changer for your business."
        analysis = get_voice_analysis(text)

        assert analysis["is_valid"] is False
        assert len(analysis["violations"]) > 0

    def test_analysis_includes_stats(self):
        """Should include sentence statistics."""
        text = "Short sentence. Another short one."
        analysis = get_voice_analysis(text)

        assert "total_words" in analysis["stats"]
        assert "total_sentences" in analysis["stats"]


class TestFormatValidationReport:
    """Test format_validation_report function."""

    def test_returns_string(self):
        """Should return a string."""
        text = "This is clean text."
        report = format_validation_report(text)
        assert isinstance(report, str)

    def test_report_contains_status(self):
        """Should contain status line."""
        text = "This is clean text."
        report = format_validation_report(text)
        assert "Status:" in report

    def test_passed_status_for_clean_text(self):
        """Should show PASSED for clean text."""
        text = "This is clean text with no issues."
        report = format_validation_report(text)
        assert "PASSED" in report

    def test_failed_status_for_violations(self):
        """Should show FAILED for text with violations."""
        text = "This game-changer will revolutionize your business."
        report = format_validation_report(text)
        assert "FAILED" in report

    def test_report_lists_violations(self):
        """Should list violations in report."""
        text = "This game-changer is revolutionary."
        report = format_validation_report(text)
        assert "Violations:" in report

    def test_report_includes_stats(self):
        """Should include sentence statistics."""
        text = "Short. Medium length sentence here."
        report = format_validation_report(text)
        assert "Sentence Statistics:" in report
        assert "Total words:" in report
        assert "Total sentences:" in report
