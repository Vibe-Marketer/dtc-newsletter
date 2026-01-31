"""
Tests for voice_profile module.
DOE-VERSION: 2026.01.31
"""

import pytest
from execution.voice_profile import (
    VOICE_PROFILE_PROMPT,
    SECTION_GUIDELINES,
    get_section_guideline,
    get_all_section_names,
)


class TestVoiceProfilePrompt:
    """Test VOICE_PROFILE_PROMPT constant."""

    def test_prompt_is_string(self):
        """Voice profile prompt should be a non-empty string."""
        assert isinstance(VOICE_PROFILE_PROMPT, str)
        assert len(VOICE_PROFILE_PROMPT) > 0

    def test_prompt_has_sufficient_length(self):
        """Voice profile should be ~2000+ tokens (~300+ words)."""
        word_count = len(VOICE_PROFILE_PROMPT.split())
        # Should be at least 300 words for comprehensive guidelines
        assert word_count >= 300, f"Expected 300+ words, got {word_count}"

    def test_prompt_contains_hormozi_reference(self):
        """Should mention Hormozi voice style."""
        assert "hormozi" in VOICE_PROFILE_PROMPT.lower()

    def test_prompt_contains_suby_reference(self):
        """Should mention Suby voice style."""
        assert "suby" in VOICE_PROFILE_PROMPT.lower()

    def test_prompt_contains_sentence_rhythm(self):
        """Should include sentence rhythm guidelines."""
        prompt_lower = VOICE_PROFILE_PROMPT.lower()
        assert "punch" in prompt_lower or "rhythm" in prompt_lower

    def test_prompt_contains_word_count_targets(self):
        """Should specify word count targets."""
        prompt_lower = VOICE_PROFILE_PROMPT.lower()
        # Should mention target word counts per sentence
        assert "8-12" in VOICE_PROFILE_PROMPT or "word" in prompt_lower

    def test_prompt_contains_anti_patterns_section(self):
        """Should explicitly list anti-patterns."""
        prompt_lower = VOICE_PROFILE_PROMPT.lower()
        assert "never" in prompt_lower or "anti-pattern" in prompt_lower

    def test_prompt_contains_specificity_guidance(self):
        """Should mention using concrete numbers."""
        prompt_lower = VOICE_PROFILE_PROMPT.lower()
        assert "number" in prompt_lower or "specific" in prompt_lower

    def test_prompt_contains_read_aloud_test(self):
        """Should mention read-out-loud test."""
        prompt_lower = VOICE_PROFILE_PROMPT.lower()
        assert "read" in prompt_lower and (
            "aloud" in prompt_lower or "out loud" in prompt_lower
        )


class TestSectionGuidelines:
    """Test SECTION_GUIDELINES constant."""

    def test_guidelines_is_dict(self):
        """Section guidelines should be a dictionary."""
        assert isinstance(SECTION_GUIDELINES, dict)

    def test_has_five_sections(self):
        """Should have exactly 5 sections."""
        assert len(SECTION_GUIDELINES) == 5

    def test_section_names(self):
        """Should have correctly named sections."""
        expected_sections = [
            "section_1",
            "section_2",
            "section_3",
            "section_4",
            "section_5",
        ]
        for section in expected_sections:
            assert section in SECTION_GUIDELINES

    def test_section_1_instant_reward(self):
        """Section 1 should be Instant Reward with correct word count."""
        s1 = SECTION_GUIDELINES["section_1"]
        assert s1["name"] == "Instant Reward"
        assert s1["word_count"] == (30, 60)
        assert "description" in s1

    def test_section_2_whats_working_now(self):
        """Section 2 should be What's Working Now with correct word count."""
        s2 = SECTION_GUIDELINES["section_2"]
        assert s2["name"] == "What's Working Now"
        assert s2["word_count"] == (300, 500)
        assert "description" in s2

    def test_section_3_breakdown(self):
        """Section 3 should be The Breakdown with correct word count."""
        s3 = SECTION_GUIDELINES["section_3"]
        assert s3["name"] == "The Breakdown"
        assert s3["word_count"] == (200, 300)
        assert "description" in s3

    def test_section_4_tool_of_week(self):
        """Section 4 should be Tool of the Week with correct word count."""
        s4 = SECTION_GUIDELINES["section_4"]
        assert s4["name"] == "Tool of the Week"
        assert s4["word_count"] == (100, 200)
        assert "description" in s4

    def test_section_5_ps_statement(self):
        """Section 5 should be PS Statement with correct word count."""
        s5 = SECTION_GUIDELINES["section_5"]
        assert s5["name"] == "PS Statement"
        assert s5["word_count"] == (20, 40)
        assert "description" in s5

    def test_section_descriptions_are_substantial(self):
        """Each section should have a substantial description."""
        for section_name, section in SECTION_GUIDELINES.items():
            desc = section["description"]
            assert len(desc) > 100, f"{section_name} description too short"


class TestGetSectionGuideline:
    """Test get_section_guideline function."""

    def test_returns_valid_section(self):
        """Should return section dict for valid section name."""
        result = get_section_guideline("section_1")
        assert isinstance(result, dict)
        assert "name" in result
        assert "word_count" in result
        assert "description" in result

    def test_raises_for_invalid_section(self):
        """Should raise KeyError for invalid section name."""
        with pytest.raises(KeyError) as exc_info:
            get_section_guideline("section_99")
        assert "Unknown section" in str(exc_info.value)

    def test_returns_all_sections(self):
        """Should return valid dict for all section names."""
        for section_name in [
            "section_1",
            "section_2",
            "section_3",
            "section_4",
            "section_5",
        ]:
            result = get_section_guideline(section_name)
            assert result is not None
            assert result["name"] is not None


class TestGetAllSectionNames:
    """Test get_all_section_names function."""

    def test_returns_list(self):
        """Should return a list."""
        result = get_all_section_names()
        assert isinstance(result, list)

    def test_returns_five_sections(self):
        """Should return exactly 5 section names."""
        result = get_all_section_names()
        assert len(result) == 5

    def test_sections_in_order(self):
        """Should return sections in correct order."""
        result = get_all_section_names()
        expected = ["section_1", "section_2", "section_3", "section_4", "section_5"]
        assert result == expected
