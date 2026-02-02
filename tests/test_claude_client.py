"""
Tests for claude_client module.
DOE-VERSION: 2026.02.02

Tests mock the OpenAI SDK (used for OpenRouter) to avoid actual API calls.
"""

import pytest
from unittest.mock import MagicMock, patch
import os


class TestClaudeClientInit:
    """Test ClaudeClient initialization."""

    def test_init_with_api_key(self):
        """Should initialize with provided API key."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("openai.OpenAI") as mock_openai:
                from execution.claude_client import ClaudeClient

                client = ClaudeClient(api_key="test-key-123")

                assert client.api_key == "test-key-123"
                mock_openai.assert_called_once()

    def test_init_from_env(self):
        """Should initialize from OPENROUTER_API_KEY env var."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key-456"}, clear=True):
            with patch("openai.OpenAI") as mock_openai:
                # Need to reimport to pick up env change
                import importlib
                import execution.claude_client as client_module

                importlib.reload(client_module)

                client = client_module.ClaudeClient()

                assert client.api_key == "env-key-456"

    def test_init_raises_without_key(self):
        """Should raise ValueError if no API key available."""
        # This test needs to completely bypass both the env and .env file
        # The cleanest approach is to patch os.getenv in the module
        with patch.dict(os.environ, {}, clear=True):
            # Also need to prevent load_dotenv from adding the key back
            with patch("dotenv.load_dotenv"):  # Prevent .env loading
                # Patch os.getenv to return None for OPENROUTER_API_KEY
                original_getenv = os.getenv

                def mock_getenv(key, default=None):
                    if key == "OPENROUTER_API_KEY":
                        return None
                    return original_getenv(key, default)

                with patch("os.getenv", side_effect=mock_getenv):
                    with patch("openai.OpenAI"):
                        import importlib
                        import execution.claude_client as client_module

                        importlib.reload(client_module)

                        with pytest.raises(ValueError) as exc_info:
                            client_module.ClaudeClient()

                        assert "OPENROUTER_API_KEY" in str(exc_info.value)


class TestGenerateWithVoice:
    """Test generate_with_voice method."""

    @pytest.fixture
    def mock_client(self):
        """Create a ClaudeClient with mocked OpenAI (OpenRouter)."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=True):
            with patch("openai.OpenAI") as mock_openai:
                # Create mock response matching OpenAI format
                mock_response = MagicMock()
                mock_choice = MagicMock()
                mock_choice.message.content = "Generated text response"
                mock_response.choices = [mock_choice]
                mock_response.usage = MagicMock()
                mock_response.usage.prompt_tokens_details = None

                # Configure mock client
                mock_instance = MagicMock()
                mock_instance.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_instance

                import importlib
                import execution.claude_client as client_module

                importlib.reload(client_module)

                client = client_module.ClaudeClient()
                yield client, mock_instance

    def test_returns_text_content(self, mock_client):
        """Should return text content from response."""
        client, mock_instance = mock_client

        result = client.generate_with_voice("Test prompt")

        assert result == "Generated text response"

    def test_uses_voice_profile_prompt(self, mock_client):
        """Should use VOICE_PROFILE_PROMPT in system message."""
        client, mock_instance = mock_client

        client.generate_with_voice("Test prompt")

        # Get the call arguments
        call_args = mock_instance.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages")

        # Verify system message contains voice profile
        system_msg = messages[0]
        assert system_msg["role"] == "system"
        assert (
            "Hormozi" in system_msg["content"]
        )  # Voice profile contains Hormozi reference

    def test_uses_correct_model(self, mock_client):
        """Should use anthropic/claude-sonnet-4 model via OpenRouter."""
        client, mock_instance = mock_client

        client.generate_with_voice("Test prompt")

        call_args = mock_instance.chat.completions.create.call_args
        model = call_args.kwargs.get("model")

        assert model == "anthropic/claude-sonnet-4"

    def test_passes_max_tokens(self, mock_client):
        """Should pass max_tokens parameter."""
        client, mock_instance = mock_client

        client.generate_with_voice("Test prompt", max_tokens=2048)

        call_args = mock_instance.chat.completions.create.call_args
        max_tokens = call_args.kwargs.get("max_tokens")

        assert max_tokens == 2048

    def test_default_max_tokens(self, mock_client):
        """Should use default max_tokens of 1024."""
        client, mock_instance = mock_client

        client.generate_with_voice("Test prompt")

        call_args = mock_instance.chat.completions.create.call_args
        max_tokens = call_args.kwargs.get("max_tokens")

        assert max_tokens == 1024

    def test_tracks_call_count(self, mock_client):
        """Should track total API calls."""
        client, mock_instance = mock_client

        client.generate_with_voice("Test prompt")

        stats = client.get_cache_stats()
        assert stats["total_calls"] == 1


class TestGenerateSection:
    """Test generate_section method."""

    @pytest.fixture
    def mock_client_for_section(self):
        """Create a ClaudeClient with mocked OpenAI for section generation."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=True):
            with patch("openai.OpenAI") as mock_openai:
                # Create mock response with clean text (no anti-patterns)
                mock_response = MagicMock()
                mock_choice = MagicMock()
                mock_choice.message.content = (
                    "Clean generated section content without any violations."
                )
                mock_response.choices = [mock_choice]
                mock_response.usage = MagicMock()
                mock_response.usage.prompt_tokens_details = None

                mock_instance = MagicMock()
                mock_instance.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_instance

                import importlib
                import execution.claude_client as client_module

                importlib.reload(client_module)

                client = client_module.ClaudeClient()
                yield client, mock_instance

    def test_generates_section_1(self, mock_client_for_section):
        """Should generate section_1 (Instant Reward)."""
        client, mock_instance = mock_client_for_section

        content = {"title": "Test Title", "summary": "Test summary"}
        result = client.generate_section("section_1", content)

        assert result == "Clean generated section content without any violations."

    def test_generates_section_2(self, mock_client_for_section):
        """Should generate section_2 (What's Working Now)."""
        client, mock_instance = mock_client_for_section

        content = {"title": "Test Tactic", "summary": "This tactic works"}
        result = client.generate_section("section_2", content)

        assert result is not None

    def test_raises_for_invalid_section(self, mock_client_for_section):
        """Should raise KeyError for invalid section name."""
        client, mock_instance = mock_client_for_section

        with pytest.raises(KeyError) as exc_info:
            client.generate_section("section_99", {"title": "Test"})

        assert "Unknown section" in str(exc_info.value)

    def test_includes_prior_sections(self, mock_client_for_section):
        """Should include prior sections in prompt for coherence."""
        client, mock_instance = mock_client_for_section

        content = {"title": "Test Title", "summary": "Test summary"}
        prior = {
            "section_1": "Prior section 1 content here",
        }

        client.generate_section("section_2", content, prior_sections=prior)

        # Check that prior sections were included in prompt
        call_args = mock_instance.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages")
        user_prompt = messages[1]["content"]  # User message is at index 1

        assert "Prior Sections" in user_prompt or "section_1" in user_prompt

    def test_validates_output_by_default(self, mock_client_for_section):
        """Should validate output against anti-patterns by default."""
        client, mock_instance = mock_client_for_section

        # Change mock to return text with anti-pattern
        mock_instance.chat.completions.create.return_value.choices[
            0
        ].message.content = "This is a game-changer for your business."

        content = {"title": "Test", "summary": "Summary"}

        with pytest.raises(ValueError) as exc_info:
            client.generate_section("section_1", content)

        assert "Anti-patterns detected" in str(exc_info.value)

    def test_can_skip_validation(self, mock_client_for_section):
        """Should skip validation when validate=False."""
        client, mock_instance = mock_client_for_section

        # Change mock to return text with anti-pattern
        mock_instance.chat.completions.create.return_value.choices[
            0
        ].message.content = "This is a game-changer for your business."

        content = {"title": "Test", "summary": "Summary"}

        # Should not raise when validate=False
        result = client.generate_section("section_1", content, validate=False)

        assert "game-changer" in result

    def test_includes_content_fields(self, mock_client_for_section):
        """Should include content fields in prompt."""
        client, mock_instance = mock_client_for_section

        content = {
            "title": "Amazing Tactic",
            "summary": "This tactic generated $50K",
            "source": "reddit",
            "url": "https://example.com",
        }

        client.generate_section("section_1", content)

        call_args = mock_instance.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages")
        user_prompt = messages[1]["content"]  # User message at index 1

        assert "Amazing Tactic" in user_prompt
        assert "$50K" in user_prompt


class TestCacheStats:
    """Test cache statistics methods."""

    @pytest.fixture
    def client(self):
        """Create a ClaudeClient with mocked OpenAI."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=True):
            with patch("openai.OpenAI") as mock_openai:
                mock_response = MagicMock()
                mock_choice = MagicMock()
                mock_choice.message.content = "Response"
                mock_response.choices = [mock_choice]
                mock_response.usage = MagicMock()
                mock_response.usage.prompt_tokens_details = None

                mock_instance = MagicMock()
                mock_instance.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_instance

                import importlib
                import execution.claude_client as client_module

                importlib.reload(client_module)

                yield client_module.ClaudeClient()

    def test_get_cache_stats_initial(self, client):
        """Should return zero stats initially."""
        stats = client.get_cache_stats()

        assert stats["cache_read_tokens"] == 0
        assert stats["cache_write_tokens"] == 0
        assert stats["total_calls"] == 0

    def test_reset_cache_stats(self, client):
        """Should reset cache stats to zero."""
        # Make a call to accumulate stats
        client.generate_with_voice("Test")

        # Reset
        client.reset_cache_stats()

        stats = client.get_cache_stats()
        assert stats["cache_read_tokens"] == 0
        assert stats["cache_write_tokens"] == 0
        assert stats["total_calls"] == 0


class TestGetClient:
    """Test get_client helper function."""

    def test_returns_claude_client(self):
        """Should return a ClaudeClient instance."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=True):
            with patch("openai.OpenAI"):
                import importlib
                import execution.claude_client as client_module

                importlib.reload(client_module)

                client = client_module.get_client()

                assert isinstance(client, client_module.ClaudeClient)

    def test_accepts_api_key(self):
        """Should accept api_key parameter."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("anthropic.Anthropic"):
                import importlib
                import execution.claude_client as client_module

                importlib.reload(client_module)

                client = client_module.get_client(api_key="custom-key")

                assert client.api_key == "custom-key"
