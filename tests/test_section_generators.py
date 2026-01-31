"""
Tests for section generators.
DOE-VERSION: 2026.01.31

Tests all 5 section generators:
- Section 1: Instant Reward (30-60 words)
- Section 2: What's Working Now (300-500 words)
- Section 3: The Breakdown (200-300 words)
- Section 4: Tool of the Week (100-200 words)
- Section 5: PS Statement (20-40 words)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


# ============================================================================
# Section 1 Tests
# ============================================================================


class TestGenerateSection1:
    """Tests for generate_section_1."""

    def test_generates_with_valid_content(self):
        """Section 1 generates from content dict."""
        from execution.section_generators import generate_section_1

        # Mock client
        mock_client = Mock()
        # Generate ~45 words (within 30-60 range)
        mock_response = (
            "Someone paid $47K for a domain name last week. The domain? "
            "'dropshipping.com'. The lesson: positioning beats persuasion. "
            "When you own the category name, you don't need to sell. "
            "People find you. That's the power of strategic positioning."
        )
        mock_client.generate_with_voice.return_value = mock_response

        content = {
            "title": "Domain Sales Hit Record",
            "summary": "Premium domains selling for record prices",
            "stat": "$47K domain sale",
            "source": "twitter",
        }

        result = generate_section_1(content, mock_client)

        assert result == mock_response
        mock_client.generate_with_voice.assert_called_once()

    def test_logs_warning_for_short_word_count(self, caplog):
        """Section 1 logs warning for word count outside 30-60 range."""
        from execution.section_generators import generate_section_1
        import logging

        mock_client = Mock()
        # Too short (8 words) - should log warning but not raise
        mock_client.generate_with_voice.return_value = (
            "This is way too short for section one."
        )

        content = {"title": "Test", "summary": "Test summary"}

        with caplog.at_level(logging.WARNING):
            result = generate_section_1(content, mock_client)

        # Should still return the content
        assert result == "This is way too short for section one."
        # Should have logged a warning
        assert "below target" in caplog.text or "Word count" in caplog.text

    def test_handles_missing_content_fields(self):
        """Section 1 handles missing optional fields."""
        from execution.section_generators import generate_section_1

        mock_client = Mock()
        mock_response = " ".join(["word"] * 45)  # 45 words
        mock_client.generate_with_voice.return_value = mock_response

        # Minimal content
        content = {"title": "Test Title"}

        result = generate_section_1(content, mock_client)
        assert result == mock_response


# ============================================================================
# Section 2 Tests
# ============================================================================


class TestGenerateSection2:
    """Tests for generate_section_2."""

    def test_generates_with_valid_content(self):
        """Section 2 generates from content dict."""
        from execution.section_generators import generate_section_2

        mock_client = Mock()
        # Generate ~350 words (within 300-500 range)
        mock_response = " ".join(["word"] * 350)
        mock_client.generate_with_voice.return_value = mock_response

        content = {
            "title": "Product Research Hack",
            "summary": "Use TikTok trending sounds to find product ideas",
            "tactic": "Search TikTok for trending sounds with #ad",
            "source": "youtube",
        }

        result = generate_section_2(content, mock_client)

        assert result == mock_response
        mock_client.generate_with_voice.assert_called_once()

    def test_logs_warning_for_short_word_count(self, caplog):
        """Section 2 logs warning for word count outside 300-500 range."""
        from execution.section_generators import generate_section_2
        import logging

        mock_client = Mock()
        # Too short (100 words) - should log warning but not raise
        short_content = " ".join(["word"] * 100)
        mock_client.generate_with_voice.return_value = short_content

        content = {"title": "Test", "summary": "Test"}

        with caplog.at_level(logging.WARNING):
            result = generate_section_2(content, mock_client)

        # Should still return the content
        assert result == short_content
        # Should have logged a warning
        assert "below target" in caplog.text or "Word count" in caplog.text

    def test_uses_prior_sections_context(self):
        """Section 2 includes prior sections in prompt."""
        from execution.section_generators import generate_section_2

        mock_client = Mock()
        mock_response = " ".join(["word"] * 400)
        mock_client.generate_with_voice.return_value = mock_response

        content = {"title": "Test", "summary": "Test"}
        prior_sections = {"section_1": "This was the opening hook about domain names."}

        generate_section_2(content, mock_client, prior_sections)

        # Check that the prompt includes prior context
        call_args = mock_client.generate_with_voice.call_args
        prompt = call_args[0][0]
        assert "section_1" in prompt.lower() or "hook" in prompt.lower()


# ============================================================================
# Section 3 Tests
# ============================================================================


class TestGenerateSection3:
    """Tests for generate_section_3."""

    def test_generates_with_narrative_context(self):
        """Section 3 generates with narrative context."""
        from execution.section_generators import generate_section_3

        mock_client = Mock()
        # Generate ~250 words (within 200-300 range)
        mock_response = " ".join(["word"] * 250)
        mock_client.generate_with_voice.return_value = mock_response

        content = {
            "title": "Brand Breakdown: How Hexclad Won",
            "summary": "Hexclad's strategy for dominating cookware",
            "story": "Gordon Ramsay partnership changed everything",
            "source": "youtube",
        }

        result = generate_section_3(content, mock_client)

        assert result == mock_response
        mock_client.generate_with_voice.assert_called_once()

    def test_logs_warning_for_short_word_count(self, caplog):
        """Section 3 logs warning for word count outside 200-300 range."""
        from execution.section_generators import generate_section_3
        import logging

        mock_client = Mock()
        # Too short (50 words) - should log warning but not raise
        short_content = " ".join(["word"] * 50)
        mock_client.generate_with_voice.return_value = short_content

        content = {"title": "Test", "summary": "Test"}

        with caplog.at_level(logging.WARNING):
            result = generate_section_3(content, mock_client)

        # Should still return the content
        assert result == short_content
        # Should have logged a warning
        assert "below target" in caplog.text or "Word count" in caplog.text

    def test_includes_prior_sections_in_prompt(self):
        """Section 3 includes sections 1 and 2 in prompt."""
        from execution.section_generators import generate_section_3

        mock_client = Mock()
        mock_response = " ".join(["word"] * 250)
        mock_client.generate_with_voice.return_value = mock_response

        content = {"title": "Test", "summary": "Test"}
        prior_sections = {
            "section_1": "Opening hook about domains",
            "section_2": "Main tactic about product research using TikTok sounds",
        }

        generate_section_3(content, mock_client, prior_sections)

        # Verify prompt includes prior sections
        call_args = mock_client.generate_with_voice.call_args
        prompt = call_args[0][0]
        assert "Section 1" in prompt
        assert "Section 2" in prompt


# ============================================================================
# Section 4 Tests
# ============================================================================


class TestGenerateSection4:
    """Tests for generate_section_4."""

    def test_uses_tool_info_correctly(self):
        """Section 4 uses tool_info dict correctly."""
        from execution.section_generators import generate_section_4

        mock_client = Mock()
        # Generate ~150 words (within 100-200 range)
        mock_response = " ".join(["word"] * 150)
        mock_client.generate_with_voice.return_value = mock_response

        tool_info = {
            "name": "ViralVault",
            "description": "AI-powered winning product research tool",
            "why_it_helps": "Saves 10+ hours per week on product research",
            "link": "https://viralvault.com",
            "is_affiliate": True,
        }

        result = generate_section_4(tool_info, mock_client)

        assert result == mock_response

        # Verify prompt includes tool info
        call_args = mock_client.generate_with_voice.call_args
        prompt = call_args[0][0]
        assert "ViralVault" in prompt
        assert "AI-powered winning product research tool" in prompt

    def test_logs_warning_for_short_word_count(self, caplog):
        """Section 4 logs warning for word count outside 100-200 range."""
        from execution.section_generators import generate_section_4
        import logging

        mock_client = Mock()
        # Too short (30 words) - should log warning but not raise
        short_content = " ".join(["word"] * 30)
        mock_client.generate_with_voice.return_value = short_content

        tool_info = {
            "name": "TestTool",
            "description": "A test tool",
            "why_it_helps": "It helps with testing",
        }

        with caplog.at_level(logging.WARNING):
            result = generate_section_4(tool_info, mock_client)

        # Should still return the content
        assert result == short_content
        # Should have logged a warning
        assert "below target" in caplog.text or "Word count" in caplog.text

    def test_prompt_includes_insider_language(self):
        """Section 4 prompt includes insider energy guidance."""
        from execution.section_generators import generate_section_4

        mock_client = Mock()
        mock_response = " ".join(["word"] * 150)
        mock_client.generate_with_voice.return_value = mock_response

        tool_info = {
            "name": "TestTool",
            "description": "A test tool",
            "why_it_helps": "It helps",
        }

        generate_section_4(tool_info, mock_client)

        # Verify prompt includes insider language guidance
        call_args = mock_client.generate_with_voice.call_args
        prompt = call_args[0][0]
        assert "insider" in prompt.lower()
        assert "secret" in prompt.lower() or "almost illegal" in prompt.lower()

    def test_with_affiliate_link(self):
        """Section 4 handles affiliate links correctly."""
        from execution.section_generators import generate_section_4

        mock_client = Mock()
        mock_response = " ".join(["word"] * 150)
        mock_client.generate_with_voice.return_value = mock_response

        tool_info = {
            "name": "AffiliateTool",
            "description": "Premium tool with affiliate program",
            "why_it_helps": "Makes money while helping",
            "is_affiliate": True,
        }

        generate_section_4(tool_info, mock_client)

        # Verify affiliate flag is in prompt
        call_args = mock_client.generate_with_voice.call_args
        prompt = call_args[0][0]
        assert "affiliate" in prompt.lower()
        assert "True" in prompt

    def test_without_link(self):
        """Section 4 generates correctly without link field."""
        from execution.section_generators import generate_section_4

        mock_client = Mock()
        mock_response = " ".join(["word"] * 150)
        mock_client.generate_with_voice.return_value = mock_response

        # No link field
        tool_info = {
            "name": "FreeTool",
            "description": "A free tool with no affiliate",
            "why_it_helps": "It's free and useful",
        }

        result = generate_section_4(tool_info, mock_client)

        assert result == mock_response


# ============================================================================
# Section 5 Tests
# ============================================================================


class TestGenerateSection5:
    """Tests for generate_section_5."""

    def test_generates_foreshadow_type(self):
        """Section 5 generates foreshadow PS type."""
        from execution.section_generators import generate_section_5

        mock_client = Mock()
        mock_response = "PS: Next week I'm revealing the $0 ad strategy that's crushing it right now. You won't want to miss this one."
        mock_client.generate_with_voice.return_value = mock_response

        result = generate_section_5(mock_client, ps_type="foreshadow")

        assert result == mock_response
        assert result.upper().startswith("PS")

    def test_generates_cta_type(self):
        """Section 5 generates CTA PS type."""
        from execution.section_generators import generate_section_5

        mock_client = Mock()
        mock_response = "P.S. Reply with your biggest product research question. I read every email and might feature your answer next week."
        mock_client.generate_with_voice.return_value = mock_response

        result = generate_section_5(mock_client, ps_type="cta")

        assert result == mock_response

    def test_generates_meme_type(self):
        """Section 5 generates meme PS type."""
        from execution.section_generators import generate_section_5

        mock_client = Mock()
        mock_response = "PS: If you made it this far, you're officially in the top one percent of readers. That's either dedication or procrastination."
        mock_client.generate_with_voice.return_value = mock_response

        result = generate_section_5(mock_client, ps_type="meme")

        assert result == mock_response

    def test_logs_warning_for_short_word_count(self, caplog):
        """Section 5 logs warning for word count outside 20-40 range."""
        from execution.section_generators import generate_section_5
        import logging

        mock_client = Mock()
        # Too short (4 words) - should log warning but not raise
        mock_client.generate_with_voice.return_value = "PS: Way too short."

        with caplog.at_level(logging.WARNING):
            result = generate_section_5(mock_client, ps_type="foreshadow")

        # Should still return the content
        assert result == "PS: Way too short."
        # Should have logged a warning
        assert "below target" in caplog.text or "Word count" in caplog.text

    def test_validates_starts_with_ps(self):
        """Section 5 validates starts with PS: or P.S."""
        from execution.section_generators import generate_section_5

        mock_client = Mock()
        # Doesn't start with PS
        mock_response = "Next week we'll cover the secret ad strategy that's working right now for DTC brands."
        mock_client.generate_with_voice.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            generate_section_5(mock_client, ps_type="foreshadow")

        assert "must start with 'PS:' or 'P.S.'" in str(exc_info.value)

    def test_invalid_ps_type_raises_error(self):
        """Section 5 raises error for invalid ps_type."""
        from execution.section_generators import generate_section_5

        mock_client = Mock()

        with pytest.raises(ValueError) as exc_info:
            generate_section_5(mock_client, ps_type="invalid")

        assert "Invalid ps_type" in str(exc_info.value)

    def test_all_three_ps_types_supported(self):
        """Section 5 supports all three PS types."""
        from execution.section_generators import generate_section_5

        mock_client = Mock()
        mock_response = "PS: This is a valid PS statement that has between twenty and forty words for testing purposes here."
        mock_client.generate_with_voice.return_value = mock_response

        for ps_type in ["foreshadow", "cta", "meme"]:
            result = generate_section_5(mock_client, ps_type=ps_type)
            assert result == mock_response


# ============================================================================
# Integration Tests
# ============================================================================


class TestSectionIntegration:
    """Integration tests for section generators."""

    def test_all_sections_generate_in_sequence(self):
        """All sections 1-5 generate in sequence."""
        from execution.section_generators import (
            generate_section_1,
            generate_section_2,
            generate_section_3,
            generate_section_4,
            generate_section_5,
        )

        mock_client = Mock()

        # Set up responses for each section with valid word counts
        responses = {
            "section_1": " ".join(["word"] * 45),  # 45 words (30-60)
            "section_2": " ".join(["word"] * 400),  # 400 words (300-500)
            "section_3": " ".join(["word"] * 250),  # 250 words (200-300)
            "section_4": " ".join(["word"] * 150),  # 150 words (100-200)
            "section_5": "PS: " + " ".join(["word"] * 28),  # 29 words (20-40)
        }

        # Configure mock to return different responses
        mock_client.generate_with_voice.side_effect = list(responses.values())

        # Generate sections in sequence
        sections = {}

        content = {"title": "Test", "summary": "Test summary"}
        sections["section_1"] = generate_section_1(content, mock_client)

        sections["section_2"] = generate_section_2(
            content, mock_client, prior_sections=sections
        )

        sections["section_3"] = generate_section_3(
            content, mock_client, prior_sections=sections
        )

        tool_info = {
            "name": "TestTool",
            "description": "A test tool",
            "why_it_helps": "Testing",
        }
        sections["section_4"] = generate_section_4(
            tool_info, mock_client, prior_sections=sections
        )

        sections["section_5"] = generate_section_5(
            mock_client, prior_sections=sections, ps_type="foreshadow"
        )

        # Verify all sections generated
        assert len(sections) == 5
        assert mock_client.generate_with_voice.call_count == 5

    def test_section_context_flows_through(self):
        """Context flows through sections correctly."""
        from execution.section_generators import (
            generate_section_1,
            generate_section_2,
            generate_section_3,
        )

        mock_client = Mock()

        # Track prompts
        prompts = []

        def capture_prompt(prompt, max_tokens=None):
            prompts.append(prompt)
            # Return valid word counts for each section
            if len(prompts) == 1:
                return " ".join(["word"] * 45)  # Section 1
            elif len(prompts) == 2:
                return " ".join(["word"] * 400)  # Section 2
            else:
                return " ".join(["word"] * 250)  # Section 3

        mock_client.generate_with_voice.side_effect = capture_prompt

        # Generate sections with context flow
        sections = {}
        content = {"title": "Test Content", "summary": "Test summary"}

        sections["section_1"] = generate_section_1(content, mock_client)
        sections["section_2"] = generate_section_2(content, mock_client, sections)
        sections["section_3"] = generate_section_3(content, mock_client, sections)

        # Section 2 prompt should reference section 1
        assert len(prompts) == 3
        # Section 3 prompt should reference sections 1 and 2
        section_3_prompt = prompts[2]
        assert "Section 1" in section_3_prompt
        assert "Section 2" in section_3_prompt

    def test_handles_empty_content(self):
        """Generators handle empty content gracefully."""
        from execution.section_generators import generate_section_1

        mock_client = Mock()
        mock_response = " ".join(["word"] * 45)
        mock_client.generate_with_voice.return_value = mock_response

        # Empty content dict
        content = {}

        # Should still generate (using N/A for missing fields)
        result = generate_section_1(content, mock_client)
        assert result == mock_response

        # Verify prompt has N/A placeholders
        call_args = mock_client.generate_with_voice.call_args
        prompt = call_args[0][0]
        assert "N/A" in prompt

    def test_prompts_use_xml_tags(self):
        """All prompts use XML tag structure."""
        from execution.section_generators import (
            generate_section_1,
            generate_section_2,
            generate_section_3,
            generate_section_4,
            generate_section_5,
        )

        mock_client = Mock()

        # Capture all prompts
        prompts = []

        def capture_and_respond(prompt, max_tokens=None):
            prompts.append(prompt)
            # Return appropriate responses
            if "Section 1" in prompt:
                return " ".join(["word"] * 45)
            elif "Section 2" in prompt:
                return " ".join(["word"] * 400)
            elif "Section 3" in prompt:
                return " ".join(["word"] * 250)
            elif "Section 4" in prompt or "Tool of the Week" in prompt:
                return " ".join(["word"] * 150)
            elif "Section 5" in prompt or "PS Statement" in prompt:
                return "PS: " + " ".join(["word"] * 28)
            return " ".join(["word"] * 50)

        mock_client.generate_with_voice.side_effect = capture_and_respond

        content = {"title": "Test", "summary": "Test"}
        tool_info = {"name": "Tool", "description": "Desc", "why_it_helps": "Helps"}

        generate_section_1(content, mock_client)
        generate_section_2(content, mock_client)
        generate_section_3(content, mock_client)
        generate_section_4(tool_info, mock_client)
        generate_section_5(mock_client)

        # Verify all prompts have XML tags
        assert len(prompts) == 5

        for prompt in prompts:
            assert "<task>" in prompt
            assert "</task>" in prompt
            assert "<requirements>" in prompt
            assert "</requirements>" in prompt
            assert "<output_format>" in prompt
            assert "</output_format>" in prompt


# ============================================================================
# Helper Function Tests
# ============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_count_words(self):
        """_count_words counts correctly."""
        from execution.section_generators import _count_words

        assert _count_words("") == 0
        assert _count_words("one") == 1
        assert _count_words("one two three") == 3
        assert _count_words("  spaced   words  ") == 2

    def test_validate_word_count(self, caplog):
        """_validate_word_count validates ranges (non-strict by default)."""
        from execution.section_generators import _validate_word_count
        import logging

        # Within range
        is_valid, count = _validate_word_count("one two three four five", 3, 7)
        assert is_valid is True
        assert count == 5

        # Below range (non-strict default - logs warning, returns True)
        with caplog.at_level(logging.WARNING):
            is_valid, count = _validate_word_count("one two", 3, 7)
        assert is_valid is True  # Non-strict returns True with warning
        assert count == 2
        assert "below target" in caplog.text

        caplog.clear()

        # Above range (non-strict default - logs warning, returns True)
        with caplog.at_level(logging.WARNING):
            is_valid, count = _validate_word_count(
                "one two three four five six seven eight", 3, 7
            )
        assert is_valid is True  # Non-strict returns True with warning
        assert count == 8
        assert "above target" in caplog.text

    def test_validate_word_count_strict_mode(self):
        """_validate_word_count strict mode raises for out of range."""
        from execution.section_generators import _validate_word_count

        # Within range - same behavior
        is_valid, count = _validate_word_count(
            "one two three four five", 3, 7, strict=True
        )
        assert is_valid is True
        assert count == 5

        # Below range (strict mode returns False)
        is_valid, count = _validate_word_count("one two", 3, 7, strict=True)
        assert is_valid is False
        assert count == 2

        # Above range (strict mode returns False)
        is_valid, count = _validate_word_count(
            "one two three four five six seven eight", 3, 7, strict=True
        )
        assert is_valid is False
        assert count == 8

    def test_summarize_prior_sections(self):
        """_summarize_prior_sections creates summaries."""
        from execution.section_generators import _summarize_prior_sections

        # Empty dict
        assert _summarize_prior_sections({}) == "No prior sections"
        assert _summarize_prior_sections(None) == "No prior sections"

        # With content
        prior = {
            "section_1": "This is a long section that should be truncated...",
            "section_2": "Another section",
        }
        result = _summarize_prior_sections(prior, max_chars=20)
        assert "section_1" in result
        assert "section_2" in result
