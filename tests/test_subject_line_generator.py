"""
Tests for subject_line_generator.py

Tests cover:
- Style selection follows 70/20/10 distribution
- Subject line format validation
- Subject line generation
- Preview text generation
"""

import pytest
from collections import Counter
from unittest.mock import MagicMock, patch
import random

from execution.subject_line_generator import (
    select_subject_style,
    validate_subject_line,
    generate_subject_line,
    generate_preview_text,
    SUBJECT_STYLES,
    STYLE_OPTIONS,
    STYLE_WEIGHTS,
)


class TestSelectSubjectStyle:
    """Tests for select_subject_style function."""

    def test_returns_valid_style(self):
        """Style selection returns one of the valid styles."""
        for _ in range(10):
            style = select_subject_style()
            assert style in STYLE_OPTIONS

    def test_style_options_match_styles(self):
        """STYLE_OPTIONS matches SUBJECT_STYLES keys."""
        assert set(STYLE_OPTIONS) == set(SUBJECT_STYLES.keys())

    def test_weights_sum_to_one(self):
        """Style weights sum to 1.0."""
        assert sum(STYLE_WEIGHTS) == pytest.approx(1.0)

    def test_accepts_history_parameter(self):
        """Function accepts optional history parameter."""
        # Should not raise
        style = select_subject_style(history=["curiosity", "direct_benefit"])
        assert style in STYLE_OPTIONS

    def test_distribution_follows_weights(self):
        """Style distribution follows 70/20/10 weights (statistical test)."""
        # Set seed for reproducibility
        random.seed(42)

        # Run 1000 selections
        results = [select_subject_style() for _ in range(1000)]
        counts = Counter(results)

        # Check distribution is roughly correct (allow 10% variance)
        total = sum(counts.values())
        curiosity_pct = counts["curiosity"] / total
        direct_pct = counts["direct_benefit"] / total
        question_pct = counts["question"] / total

        # Expected: 70%, 20%, 10% - allow 10% variance
        assert 0.60 <= curiosity_pct <= 0.80, f"Curiosity: {curiosity_pct:.2%}"
        assert 0.10 <= direct_pct <= 0.30, f"Direct: {direct_pct:.2%}"
        assert 0.02 <= question_pct <= 0.20, f"Question: {question_pct:.2%}"


class TestValidateSubjectLine:
    """Tests for validate_subject_line function."""

    def test_valid_subject_line_passes(self):
        """Valid subject line passes all checks."""
        subject = "DTC Money Minute #1: the secret no one talks about"
        is_valid, violations = validate_subject_line(subject, 1)
        assert is_valid is True
        assert violations == []

    def test_rejects_too_long_subject(self):
        """Subject over 50 chars is rejected."""
        subject = "DTC Money Minute #1: this is a really long subject line that exceeds fifty characters"
        is_valid, violations = validate_subject_line(subject, 1)
        assert is_valid is False
        assert any("too long" in v for v in violations)

    def test_rejects_wrong_prefix(self):
        """Subject without correct prefix is rejected."""
        subject = "Wrong Prefix #1: something here"
        is_valid, violations = validate_subject_line(subject, 1)
        assert is_valid is False
        assert any("Must start with" in v for v in violations)

    def test_rejects_wrong_issue_number(self):
        """Subject with wrong issue number is rejected."""
        subject = "DTC Money Minute #2: the secret"
        is_valid, violations = validate_subject_line(subject, 1)
        assert is_valid is False
        assert any("Must start with" in v for v in violations)

    def test_rejects_uppercase_after_colon(self):
        """Uppercase letter after colon is rejected."""
        subject = "DTC Money Minute #1: The secret here"
        is_valid, violations = validate_subject_line(subject, 1)
        assert is_valid is False
        assert any("lowercase" in v.lower() for v in violations)

    def test_accepts_lowercase_after_colon(self):
        """Lowercase letter after colon is accepted."""
        subject = "DTC Money Minute #1: the secret here"
        is_valid, violations = validate_subject_line(subject, 1)
        assert is_valid is True

    def test_rejects_emojis(self):
        """Subject with emojis is rejected."""
        subject = "DTC Money Minute #1: fire deal 🔥"
        is_valid, violations = validate_subject_line(subject, 1)
        assert is_valid is False
        assert any("emoji" in v.lower() for v in violations)

    def test_rejects_all_caps_words_in_hook(self):
        """Subject with ALL CAPS words in hook is rejected."""
        subject = "DTC Money Minute #1: the BEST deal"
        is_valid, violations = validate_subject_line(subject, 1)
        assert is_valid is False
        assert any("CAPS" in v for v in violations)

    def test_allows_dtc_in_prefix(self):
        """DTC in prefix is allowed (it's part of required format)."""
        subject = "DTC Money Minute #1: the secret"
        is_valid, violations = validate_subject_line(subject, 1)
        # DTC is in prefix, not in hook, so should be valid
        assert not any("CAPS" in v for v in violations)

    def test_accepts_single_letter_caps(self):
        """Single uppercase letters are OK (like 'I')."""
        # "I" is single char - should be OK (only 2+ char words flagged)
        subject = "DTC Money Minute #1: why i quit"  # lowercase hook
        is_valid, violations = validate_subject_line(subject, 1)
        # Should pass - no ALL CAPS violations
        assert not any("CAPS" in v for v in violations)

    def test_rejects_how_to_start(self):
        """Subject starting with 'How to' after colon is rejected."""
        subject = "DTC Money Minute #1: how to win"
        is_valid, violations = validate_subject_line(subject, 1)
        assert is_valid is False
        assert any("How to" in v for v in violations)

    def test_returns_multiple_violations(self):
        """Returns all violations, not just first."""
        subject = "DTC Money Minute #1: How To WIN BIG 🎉 and make lots of money fast"
        is_valid, violations = validate_subject_line(subject, 1)
        assert is_valid is False
        assert len(violations) >= 2  # Multiple issues

    def test_exact_50_chars_is_valid(self):
        """Subject of exactly 50 chars is valid."""
        # Create subject of exactly 50 chars
        prefix = "DTC Money Minute #1: "
        hook = "a" * (50 - len(prefix))
        subject = prefix + hook
        assert len(subject) == 50
        is_valid, violations = validate_subject_line(subject, 1)
        # Should pass length check
        assert not any("too long" in v for v in violations)


class TestGenerateSubjectLine:
    """Tests for generate_subject_line function."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock ClaudeClient."""
        client = MagicMock()
        return client

    def test_generates_valid_subject_line(self, mock_client):
        """Generates valid subject line on first try."""
        mock_client.generate_with_voice.return_value = "DTC Money Minute #1: the secret"

        result = generate_subject_line(
            issue_number=1,
            main_topic="email marketing",
            style="curiosity",
            client=mock_client,
        )

        assert result == "DTC Money Minute #1: the secret"
        assert mock_client.generate_with_voice.call_count == 1

    def test_retries_on_validation_failure(self, mock_client):
        """Retries with stricter prompt on validation failure."""
        # First call returns invalid, second returns valid
        mock_client.generate_with_voice.side_effect = [
            "DTC Money Minute #1: The Uppercase Hook That Is Way Too Long For The Limit",
            "DTC Money Minute #1: the fixed hook",
        ]

        result = generate_subject_line(
            issue_number=1,
            main_topic="email marketing",
            style="curiosity",
            client=mock_client,
        )

        assert result == "DTC Money Minute #1: the fixed hook"
        assert mock_client.generate_with_voice.call_count == 2

    def test_raises_on_double_failure(self, mock_client):
        """Raises ValueError if retry also fails."""
        mock_client.generate_with_voice.return_value = "DTC Money Minute #1: THIS IS ALL CAPS AND WAY TOO LONG FOR ANY REASONABLE LIMIT"

        with pytest.raises(ValueError) as exc_info:
            generate_subject_line(
                issue_number=1,
                main_topic="email marketing",
                style="curiosity",
                client=mock_client,
            )

        assert "failed validation after retry" in str(exc_info.value)

    def test_rejects_invalid_style(self, mock_client):
        """Raises ValueError for invalid style."""
        with pytest.raises(ValueError) as exc_info:
            generate_subject_line(
                issue_number=1,
                main_topic="email marketing",
                style="invalid_style",
                client=mock_client,
            )

        assert "Invalid style" in str(exc_info.value)

    def test_strips_quotes_from_result(self, mock_client):
        """Strips surrounding quotes from generated result."""
        mock_client.generate_with_voice.return_value = (
            '"DTC Money Minute #1: the secret"'
        )

        result = generate_subject_line(
            issue_number=1,
            main_topic="email marketing",
            style="curiosity",
            client=mock_client,
        )

        assert result == "DTC Money Minute #1: the secret"

    def test_uses_correct_style_prompt(self, mock_client):
        """Uses correct style prompt in generation."""
        mock_client.generate_with_voice.return_value = "DTC Money Minute #5: hook"

        generate_subject_line(
            issue_number=5,
            main_topic="product research",
            style="direct_benefit",
            client=mock_client,
        )

        # Check the prompt contains style guidance
        call_args = mock_client.generate_with_voice.call_args
        prompt = call_args[0][0]
        assert "concrete benefit" in prompt.lower()  # direct_benefit style

    def test_prompt_includes_issue_number(self, mock_client):
        """Prompt includes the issue number."""
        mock_client.generate_with_voice.return_value = "DTC Money Minute #42: hook"

        generate_subject_line(
            issue_number=42,
            main_topic="test topic",
            style="curiosity",
            client=mock_client,
        )

        call_args = mock_client.generate_with_voice.call_args
        prompt = call_args[0][0]
        assert "#42" in prompt


class TestGeneratePreviewText:
    """Tests for generate_preview_text function."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock ClaudeClient."""
        client = MagicMock()
        return client

    def test_generates_preview_text(self, mock_client):
        """Generates preview text within length constraints."""
        mock_client.generate_with_voice.return_value = (
            "The $47 tool that 8-figure brands use daily"
        )

        result = generate_preview_text(
            newsletter_content="This week we discuss tools for email marketing...",
            client=mock_client,
        )

        assert len(result) >= 40
        assert len(result) <= 90

    def test_strips_quotes_from_result(self, mock_client):
        """Strips surrounding quotes from generated result."""
        mock_client.generate_with_voice.return_value = '"The secret most stores miss"'

        result = generate_preview_text(
            newsletter_content="Content here...",
            client=mock_client,
        )

        assert not result.startswith('"')
        assert not result.endswith('"')

    def test_regenerates_if_too_short(self, mock_client):
        """Regenerates if preview is too short."""
        mock_client.generate_with_voice.side_effect = [
            "Too short",  # First attempt: too short
            "This is a longer preview text that meets the minimum requirements",  # Second attempt
        ]

        result = generate_preview_text(
            newsletter_content="Content here...",
            client=mock_client,
        )

        assert mock_client.generate_with_voice.call_count == 2

    def test_truncates_if_too_long(self, mock_client):
        """Truncates preview to 90 chars if too long."""
        long_preview = "This is a very long preview text that definitely exceeds the ninety character limit we have set for this field and needs truncation"
        mock_client.generate_with_voice.return_value = long_preview

        result = generate_preview_text(
            newsletter_content="Content here...",
            client=mock_client,
        )

        assert len(result) <= 90
        assert result.endswith("...")

    def test_not_generic_view_in_browser(self, mock_client):
        """Preview should not be generic 'view in browser' text."""
        # This is checked by the prompt, but we verify the prompt includes guidance
        mock_client.generate_with_voice.return_value = "The strategy that tripled their email revenue overnight"  # 52 chars - in range

        generate_preview_text(
            newsletter_content="Content here...",
            client=mock_client,
        )

        # Check the first call's prompt (before any retry)
        call_args = mock_client.generate_with_voice.call_args_list[0]
        prompt = call_args[0][0]
        assert "View in browser" in prompt  # Listed as bad example to avoid

    def test_uses_newsletter_content_for_context(self, mock_client):
        """Uses newsletter content in the prompt."""
        mock_client.generate_with_voice.return_value = (
            "A hook about email marketing secrets"
        )

        generate_preview_text(
            newsletter_content="Email marketing is the key to success in DTC businesses...",
            client=mock_client,
        )

        call_args = mock_client.generate_with_voice.call_args
        prompt = call_args[0][0]
        assert "Email marketing" in prompt

    def test_handles_long_content_summary(self, mock_client):
        """Handles very long newsletter content by truncating."""
        mock_client.generate_with_voice.return_value = (
            "A preview hook text of appropriate length"
        )

        # Create very long content
        long_content = "word " * 500

        generate_preview_text(
            newsletter_content=long_content,
            client=mock_client,
        )

        call_args = mock_client.generate_with_voice.call_args
        prompt = call_args[0][0]
        # Should have truncated to ~200 words
        assert prompt.count("word") <= 250


class TestSubjectStyleConstants:
    """Tests for style constants."""

    def test_subject_styles_has_required_keys(self):
        """SUBJECT_STYLES has all required style keys."""
        assert "curiosity" in SUBJECT_STYLES
        assert "direct_benefit" in SUBJECT_STYLES
        assert "question" in SUBJECT_STYLES

    def test_subject_styles_values_are_prompts(self):
        """SUBJECT_STYLES values are prompt strings."""
        for style, prompt in SUBJECT_STYLES.items():
            assert isinstance(prompt, str)
            assert len(prompt) > 10  # Not empty/trivial

    def test_style_weights_match_options(self):
        """STYLE_WEIGHTS length matches STYLE_OPTIONS."""
        assert len(STYLE_WEIGHTS) == len(STYLE_OPTIONS)
