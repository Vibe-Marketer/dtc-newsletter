"""
Tests for pitch generator module.
"""

import pytest
from unittest.mock import MagicMock, patch


def create_mock_affiliate(
    name="Test Program",
    company="Test Co",
    commission_rate="20%",
    commission_type="percentage",
    is_recurring=True,
    product_description="A test product for testing",
    topic_fit="Fits the topic well",
    network="direct",
    signup_accessible=True,
):
    """Helper to create a mock AffiliateProgram."""
    from execution.affiliate_discovery import AffiliateProgram

    return AffiliateProgram(
        name=name,
        company=company,
        commission_rate=commission_rate,
        commission_type=commission_type,
        is_recurring=is_recurring,
        product_description=product_description,
        topic_fit=topic_fit,
        network=network,
        signup_accessible=signup_accessible,
    )


class TestValidatePitch:
    """Tests for validate_pitch function."""

    def test_valid_pitch_passes(self):
        """A clean pitch should pass validation."""
        from execution.pitch_generator import validate_pitch

        pitch = "Save 3 hours per week on email sequences. Klaviyo handles the heavy lifting."
        assert validate_pitch(pitch) is True

    def test_rejects_basically(self):
        """Should reject pitch with 'basically'."""
        from execution.pitch_generator import validate_pitch

        pitch = "Basically, this tool saves you time."
        assert validate_pitch(pitch) is False

    def test_rejects_essentially(self):
        """Should reject pitch with 'essentially'."""
        from execution.pitch_generator import validate_pitch

        pitch = "It's essentially a game-changer for email."
        assert validate_pitch(pitch) is False

    def test_rejects_just(self):
        """Should reject pitch with 'just'."""
        from execution.pitch_generator import validate_pitch

        pitch = "Just sign up and watch the magic happen."
        assert validate_pitch(pitch) is False

    def test_rejects_simply(self):
        """Should reject pitch with 'simply'."""
        from execution.pitch_generator import validate_pitch

        pitch = "Simply connect your store and you're done."
        assert validate_pitch(pitch) is False

    def test_rejects_actually(self):
        """Should reject pitch with 'actually'."""
        from execution.pitch_generator import validate_pitch

        pitch = "This tool actually works unlike the others."
        assert validate_pitch(pitch) is False

    def test_rejects_really(self):
        """Should reject pitch with 'really'."""
        from execution.pitch_generator import validate_pitch

        pitch = "I really love this email platform."
        assert validate_pitch(pitch) is False

    def test_rejects_passive_voice(self):
        """Should reject pitch with passive voice."""
        from execution.pitch_generator import validate_pitch

        pitch = "Your email sequences are being handled automatically."
        assert validate_pitch(pitch) is False

    def test_rejects_was_used(self):
        """Should reject 'was used' passive pattern."""
        from execution.pitch_generator import validate_pitch

        pitch = "This technique was used by top brands."
        assert validate_pitch(pitch) is False

    def test_rejects_too_many_sentences(self):
        """Should reject pitch with more than 4 sentences."""
        from execution.pitch_generator import validate_pitch

        pitch = "One. Two. Three. Four. Five sentences is too many."
        assert validate_pitch(pitch) is False

    def test_accepts_four_sentences(self):
        """Should accept pitch with exactly 4 sentences."""
        from execution.pitch_generator import validate_pitch

        pitch = "One benefit. Two benefits. Three benefits. Four max."
        assert validate_pitch(pitch) is True

    def test_accepts_exclamation_and_question(self):
        """Should handle different sentence terminators."""
        from execution.pitch_generator import validate_pitch

        pitch = "Want faster shipping? Use ShipBob! Your customers will thank you."
        assert validate_pitch(pitch) is True

    def test_rejects_case_insensitive(self):
        """Should reject fluff words regardless of case."""
        from execution.pitch_generator import validate_pitch

        pitch = "BASICALLY, this is the best tool."
        assert validate_pitch(pitch) is False

        pitch = "Essentially the same thing."
        assert validate_pitch(pitch) is False

    def test_accepts_word_inside_word(self):
        """Should not flag 'just' inside 'adjust' or 'justify'."""
        from execution.pitch_generator import validate_pitch

        # 'just' appears in 'adjustment' but shouldn't trigger
        pitch = "Make quick adjustments to your shipping rates."
        assert validate_pitch(pitch) is True


class TestPitchGenerator:
    """Tests for PitchGenerator class."""

    def test_raises_on_missing_api_key(self):
        """Should raise ValueError if API key not set."""
        from execution.pitch_generator import PitchGenerator

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                PitchGenerator()

        assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    def test_accepts_api_key_parameter(self):
        """Should accept API key as parameter."""
        from execution import pitch_generator as pg

        with patch.object(pg, "anthropic") as mock_anthropic:
            mock_anthropic.Anthropic.return_value = MagicMock()
            generator = pg.PitchGenerator(api_key="test-key")

        mock_anthropic.Anthropic.assert_called_once_with(api_key="test-key")
        assert generator.api_key == "test-key"

    def test_generate_pitch_calls_api(self):
        """Should call Claude API with correct prompt."""
        from execution import pitch_generator as pg

        affiliate = create_mock_affiliate(
            name="Klaviyo",
            product_description="Email marketing for e-commerce",
            topic_fit="Perfect for email automation topic",
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Save hours on email. Klaviyo automates it."

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch.object(pg, "anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.Anthropic.return_value = mock_client
                mock_client.messages.create.return_value = mock_response

                generator = pg.PitchGenerator()
                result = generator.generate_pitch(
                    affiliate=affiliate,
                    newsletter_topic="email automation",
                    problem_context="Brands spending too much time on manual emails",
                )

        assert result == "Save hours on email. Klaviyo automates it."
        mock_client.messages.create.assert_called_once()

        # Verify prompt includes key elements
        call_args = mock_client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
        assert "Klaviyo" in prompt
        assert "email automation" in prompt
        assert "Email marketing for e-commerce" in prompt
        assert "problem_context" in prompt.lower() or "spending too much time" in prompt

    def test_generate_pitch_includes_voice_guidance(self):
        """Should include voice guidance in prompt."""
        from execution import pitch_generator as pg

        affiliate = create_mock_affiliate()

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Test pitch output."

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch.object(pg, "anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.Anthropic.return_value = mock_client
                mock_client.messages.create.return_value = mock_response

                generator = pg.PitchGenerator()
                generator.generate_pitch(
                    affiliate=affiliate,
                    newsletter_topic="test topic",
                )

        call_args = mock_client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]

        # Check that voice guidance is included
        assert "Short, punchy sentences" in prompt
        assert "Zero fluff" in prompt

    def test_generate_pitch_uses_correct_model(self):
        """Should use claude-sonnet-4-20250514 model."""
        from execution import pitch_generator as pg

        affiliate = create_mock_affiliate()

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Test output."

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch.object(pg, "anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.Anthropic.return_value = mock_client
                mock_client.messages.create.return_value = mock_response

                generator = pg.PitchGenerator()
                generator.generate_pitch(
                    affiliate=affiliate,
                    newsletter_topic="test",
                )

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-sonnet-4-20250514"

    def test_generate_pitch_max_tokens(self):
        """Should use max_tokens of 300."""
        from execution import pitch_generator as pg

        affiliate = create_mock_affiliate()

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Test output."

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch.object(pg, "anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.Anthropic.return_value = mock_client
                mock_client.messages.create.return_value = mock_response

                generator = pg.PitchGenerator()
                generator.generate_pitch(
                    affiliate=affiliate,
                    newsletter_topic="test",
                )

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["max_tokens"] == 300


class TestGeneratePitchesBatch:
    """Tests for batch pitch generation."""

    def test_generates_multiple_pitches(self):
        """Should generate pitches for all affiliates."""
        from execution import pitch_generator as pg

        affiliates = [
            create_mock_affiliate(name="Program A"),
            create_mock_affiliate(name="Program B"),
            create_mock_affiliate(name="Program C"),
        ]

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Test pitch."

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch.object(pg, "anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.Anthropic.return_value = mock_client
                mock_client.messages.create.return_value = mock_response

                generator = pg.PitchGenerator()
                results = generator.generate_pitches_batch(
                    affiliates=affiliates,
                    newsletter_topic="test topic",
                )

        assert len(results) == 3
        assert "Program A" in results
        assert "Program B" in results
        assert "Program C" in results
        assert mock_client.messages.create.call_count == 3

    def test_handles_partial_failures(self):
        """Should skip failed affiliates and continue with others."""
        from execution import pitch_generator as pg

        affiliates = [
            create_mock_affiliate(name="Success A"),
            create_mock_affiliate(name="Failure B"),
            create_mock_affiliate(name="Success C"),
        ]

        mock_success = MagicMock()
        mock_success.content = [MagicMock()]
        mock_success.content[0].text = "Success pitch."

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch.object(pg, "anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.Anthropic.return_value = mock_client

                # Second call fails
                mock_client.messages.create.side_effect = [
                    mock_success,
                    Exception("API Error"),
                    mock_success,
                ]

                generator = pg.PitchGenerator()
                results = generator.generate_pitches_batch(
                    affiliates=affiliates,
                    newsletter_topic="test topic",
                )

        assert len(results) == 2
        assert "Success A" in results
        assert "Failure B" not in results
        assert "Success C" in results

    def test_returns_empty_dict_on_all_failures(self):
        """Should return empty dict if all affiliates fail."""
        from execution import pitch_generator as pg

        affiliates = [
            create_mock_affiliate(name="Fail A"),
            create_mock_affiliate(name="Fail B"),
        ]

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch.object(pg, "anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.Anthropic.return_value = mock_client
                mock_client.messages.create.side_effect = Exception("API Error")

                generator = pg.PitchGenerator()
                results = generator.generate_pitches_batch(
                    affiliates=affiliates,
                    newsletter_topic="test topic",
                )

        assert results == {}


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_generate_pitch_function(self):
        """Module-level generate_pitch should work."""
        from execution import pitch_generator as pg

        affiliate = create_mock_affiliate(name="Convenience Test")

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Convenience pitch."

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch.object(pg, "anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.Anthropic.return_value = mock_client
                mock_client.messages.create.return_value = mock_response

                result = pg.generate_pitch(
                    affiliate=affiliate,
                    newsletter_topic="test",
                )

        assert result == "Convenience pitch."

    def test_generate_pitches_batch_function(self):
        """Module-level generate_pitches_batch should work."""
        from execution import pitch_generator as pg

        affiliates = [
            create_mock_affiliate(name="Batch A"),
            create_mock_affiliate(name="Batch B"),
        ]

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Batch pitch."

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch.object(pg, "anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.Anthropic.return_value = mock_client
                mock_client.messages.create.return_value = mock_response

                results = pg.generate_pitches_batch(
                    affiliates=affiliates,
                    newsletter_topic="test",
                )

        assert len(results) == 2
        assert "Batch A" in results
        assert "Batch B" in results
