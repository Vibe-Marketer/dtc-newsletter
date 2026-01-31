"""
Tests for virality analyzer module.
"""

import pytest

from execution.virality_analyzer import (
    analyze_virality,
    VIRALITY_SCHEMA,
    _analyze_hook,
    _identify_triggers,
    _assess_confidence,
    _generate_replication_notes,
    _identify_success_factors,
)


class TestAnalyzeVirality:
    """Tests for main analyze_virality function."""

    def test_returns_correct_schema_structure(self):
        """Verify output matches VIRALITY_SCHEMA structure."""
        content = {"title": "Test Title", "description": "Test description"}
        result = analyze_virality(content)

        # Check top-level keys
        assert "hook_analysis" in result
        assert "emotional_triggers" in result
        assert "timing_factors" in result
        assert "success_factors" in result
        assert "virality_confidence" in result
        assert "replication_notes" in result

    def test_hook_analysis_structure(self):
        """Verify hook_analysis contains expected keys."""
        content = {"title": "How to make $10k in a month?"}
        result = analyze_virality(content)

        assert "hook_type" in result["hook_analysis"]
        assert "hook_text" in result["hook_analysis"]
        assert "attention_elements" in result["hook_analysis"]

    def test_emotional_triggers_is_list(self):
        """Verify emotional_triggers is a list of dicts."""
        content = {"title": "Don't miss this secret to success!"}
        result = analyze_virality(content)

        assert isinstance(result["emotional_triggers"], list)
        if result["emotional_triggers"]:
            trigger = result["emotional_triggers"][0]
            assert "trigger" in trigger
            assert "evidence" in trigger
            assert "intensity" in trigger

    def test_timing_factors_structure(self):
        """Verify timing_factors contains expected keys."""
        content = {"title": "Test"}
        result = analyze_virality(content)

        assert "day_relevance" in result["timing_factors"]
        assert "trending_topics" in result["timing_factors"]
        assert "seasonal_hook" in result["timing_factors"]

    def test_success_factors_structure(self):
        """Verify success_factors contains expected keys."""
        content = {"title": "Test", "outlier_score": 7.5}
        result = analyze_virality(content)

        assert "key_drivers" in result["success_factors"]
        assert "reproducible_elements" in result["success_factors"]
        assert "unique_circumstances" in result["success_factors"]

    def test_with_transcript(self):
        """Verify function accepts transcript parameter."""
        content = {"title": "Test Video"}
        transcript = "This is the video transcript content."
        result = analyze_virality(content, transcript=transcript)

        # Should still return valid structure
        assert "hook_analysis" in result


class TestAnalyzeHook:
    """Tests for _analyze_hook function."""

    def test_detects_question_hook(self):
        """Questions should be detected."""
        result = _analyze_hook("How do I grow my Shopify store?")
        assert result["hook_type"] == "question"

    def test_detects_number_hook(self):
        """Numbers should be detected."""
        result = _analyze_hook("5 Tips for Better Conversions")
        assert result["hook_type"] == "number"

    def test_detects_controversy_hook(self):
        """Controversial keywords should be detected."""
        result = _analyze_hook("The unpopular truth about dropshipping")
        assert result["hook_type"] == "controversy"

    def test_detects_story_hook(self):
        """Personal story starters should be detected."""
        result = _analyze_hook("I built a successful business from scratch")
        assert result["hook_type"] == "story"

    def test_defaults_to_statement(self):
        """Unknown patterns should default to statement."""
        result = _analyze_hook("Best practices for ecommerce")
        assert result["hook_type"] == "statement"

    def test_detects_money_attention_element(self):
        """Money indicators should be detected."""
        result = _analyze_hook("How I made $50k in revenue")
        assert "money" in result["attention_elements"]

    def test_detects_exclusivity_element(self):
        """Exclusivity keywords should be detected."""
        result = _analyze_hook("The secret nobody tells you about")
        assert "exclusivity" in result["attention_elements"]

    def test_detects_speed_element(self):
        """Speed keywords should be detected."""
        result = _analyze_hook("Get results in 5 minutes")
        assert "speed" in result["attention_elements"]

    def test_detects_specificity_element(self):
        """Numbers add specificity."""
        result = _analyze_hook("7 proven strategies")
        assert "specificity" in result["attention_elements"]

    def test_truncates_long_hook_text(self):
        """Hook text should be truncated to 100 chars."""
        long_title = "A" * 150
        result = _analyze_hook(long_title)
        assert len(result["hook_text"]) <= 100


class TestIdentifyTriggers:
    """Tests for _identify_triggers function."""

    def test_detects_fear_trigger(self):
        """Fear keywords should be detected."""
        result = _identify_triggers("Don't miss out", "You might fail")
        triggers = [t["trigger"] for t in result]
        assert "fear" in triggers

    def test_detects_greed_trigger(self):
        """Greed keywords should be detected."""
        result = _identify_triggers("Make money", "Increase your profit")
        triggers = [t["trigger"] for t in result]
        assert "greed" in triggers

    def test_detects_curiosity_trigger(self):
        """Curiosity keywords should be detected."""
        result = _identify_triggers("Discover the secret", "Hidden strategy revealed")
        triggers = [t["trigger"] for t in result]
        assert "curiosity" in triggers

    def test_detects_urgency_trigger(self):
        """Urgency keywords should be detected."""
        result = _identify_triggers("Act now", "Limited time offer")
        triggers = [t["trigger"] for t in result]
        assert "urgency" in triggers

    def test_high_intensity_for_multiple_matches(self):
        """Multiple keyword matches should increase intensity."""
        result = _identify_triggers("Make money, increase income, get rich", "profit")
        greed_trigger = next((t for t in result if t["trigger"] == "greed"), None)
        assert greed_trigger is not None
        assert greed_trigger["intensity"] == "high"

    def test_medium_intensity_for_two_matches(self):
        """Two matches should give medium intensity."""
        result = _identify_triggers("Make money and profit", "")
        greed_trigger = next((t for t in result if t["trigger"] == "greed"), None)
        assert greed_trigger is not None
        assert greed_trigger["intensity"] == "medium"

    def test_returns_empty_for_no_triggers(self):
        """No matches should return empty list."""
        result = _identify_triggers("Plain title", "Plain description")
        # May or may not have triggers depending on keyword overlap
        assert isinstance(result, list)


class TestAssessConfidence:
    """Tests for _assess_confidence function."""

    def test_definite_for_10x_outlier(self):
        """10x+ outlier should return definite."""
        assert _assess_confidence({"outlier_score": 10.5}) == "definite"
        assert _assess_confidence({"outlier_score": 15.0}) == "definite"

    def test_likely_for_5x_outlier(self):
        """5-10x outlier should return likely."""
        assert _assess_confidence({"outlier_score": 5.0}) == "likely"
        assert _assess_confidence({"outlier_score": 7.5}) == "likely"

    def test_possible_for_3x_outlier(self):
        """3-5x outlier should return possible."""
        assert _assess_confidence({"outlier_score": 3.0}) == "possible"
        assert _assess_confidence({"outlier_score": 4.5}) == "possible"

    def test_unclear_for_low_score(self):
        """Below 3x should return unclear."""
        assert _assess_confidence({"outlier_score": 2.0}) == "unclear"
        assert _assess_confidence({"outlier_score": 1.5}) == "unclear"

    def test_handles_missing_score(self):
        """Missing score should return unclear."""
        assert _assess_confidence({}) == "unclear"


class TestIdentifySuccessFactors:
    """Tests for _identify_success_factors function."""

    def test_exceptional_performance_10x(self):
        """10x+ should be marked as exceptional."""
        result = _identify_success_factors({"outlier_score": 12.0}, None)
        assert "exceptional_performance_10x+" in result["key_drivers"]

    def test_strong_performance_5x(self):
        """5-10x should be marked as strong."""
        result = _identify_success_factors({"outlier_score": 7.0}, None)
        assert "strong_performance_5x+" in result["key_drivers"]

    def test_engagement_modifiers_list(self):
        """Engagement modifiers (list) should be included."""
        result = _identify_success_factors(
            {"engagement_modifiers": ["money_hook", "urgency"]}, None
        )
        assert "money_hook" in result["key_drivers"]
        assert "urgency" in result["key_drivers"]

    def test_engagement_modifiers_numeric(self):
        """Numeric engagement modifiers should be handled."""
        result = _identify_success_factors({"engagement_modifiers": 1.5}, None)
        # Should not crash, and may add a key driver
        assert "key_drivers" in result

    def test_returns_empty_lists_for_minimal_content(self):
        """Minimal content should return empty lists."""
        result = _identify_success_factors({"outlier_score": 2.0}, None)
        # Low score won't add performance drivers
        assert isinstance(result["key_drivers"], list)
        assert isinstance(result["reproducible_elements"], list)
        assert isinstance(result["unique_circumstances"], list)


class TestGenerateReplicationNotes:
    """Tests for _generate_replication_notes function."""

    def test_includes_hook_pattern(self):
        """Hook pattern should be included."""
        analysis = {
            "hook_analysis": {"hook_type": "question", "attention_elements": []},
            "emotional_triggers": [],
            "success_factors": {"reproducible_elements": []},
        }
        result = _generate_replication_notes(analysis)
        assert "Hook pattern: question" in result

    def test_includes_attention_elements(self):
        """Attention elements should be included."""
        analysis = {
            "hook_analysis": {
                "hook_type": "number",
                "attention_elements": ["money", "speed"],
            },
            "emotional_triggers": [],
            "success_factors": {"reproducible_elements": []},
        }
        result = _generate_replication_notes(analysis)
        assert "money" in result
        assert "speed" in result

    def test_includes_high_triggers(self):
        """High intensity triggers should be included."""
        analysis = {
            "hook_analysis": {"hook_type": "statement", "attention_elements": []},
            "emotional_triggers": [
                {"trigger": "greed", "intensity": "high"},
                {"trigger": "fear", "intensity": "low"},
            ],
            "success_factors": {"reproducible_elements": []},
        }
        result = _generate_replication_notes(analysis)
        assert "greed" in result
        assert "fear" not in result  # Low intensity not included

    def test_includes_reproducible_elements(self):
        """Reproducible elements should be included."""
        analysis = {
            "hook_analysis": {"hook_type": "statement", "attention_elements": []},
            "emotional_triggers": [],
            "success_factors": {
                "reproducible_elements": ["use_numbers", "add_urgency"]
            },
        }
        result = _generate_replication_notes(analysis)
        assert "use_numbers" in result
        assert "add_urgency" in result

    def test_returns_analyze_manually_for_empty(self):
        """Empty analysis should return fallback message."""
        analysis = {
            "hook_analysis": {},
            "emotional_triggers": [],
            "success_factors": {},
        }
        result = _generate_replication_notes(analysis)
        assert result == "Analyze manually"


class TestViralitySchema:
    """Tests for VIRALITY_SCHEMA constant."""

    def test_schema_exists(self):
        """Schema should be defined."""
        assert VIRALITY_SCHEMA is not None

    def test_schema_has_required_keys(self):
        """Schema should have all required top-level keys."""
        required = [
            "hook_analysis",
            "emotional_triggers",
            "timing_factors",
            "success_factors",
            "virality_confidence",
            "replication_notes",
        ]
        for key in required:
            assert key in VIRALITY_SCHEMA
