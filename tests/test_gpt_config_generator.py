"""
Tests for the GPT Configuration Generator.

Tests cover:
- Generator inheritance from BaseGenerator
- Product type identification
- File generation (all 4 required files)
- Validation (JSON, name length, description, instructions, starters)
- Claude client mocking
"""

import json
from unittest.mock import MagicMock

import pytest

from execution.generators.base_generator import BaseGenerator, ProductSpec
from execution.generators.gpt_config import (
    GPT_CONFIG_PROMPT,
    SETUP_GUIDE_TEMPLATE,
    GptConfigGenerator,
)


@pytest.fixture
def sample_spec():
    """Create a sample ProductSpec for testing."""
    return ProductSpec(
        problem="Managing customer returns efficiently",
        solution_name="Returns Master",
        target_audience="E-commerce store owners",
        key_benefits=[
            "Reduce return processing time by 50%",
            "Improve customer satisfaction",
            "Automate refund decisions",
        ],
        product_type="gpt_config",
    )


@pytest.fixture
def mock_claude_response():
    """Create a mock Claude response with valid GPT config."""
    return json.dumps(
        {
            "name": "Returns Master GPT",
            "description": "Helps e-commerce store owners manage customer returns efficiently with automated decisions and improved customer satisfaction.",
            "instructions": " ".join(["word"] * 600),  # 600 words
            "conversation_starters": [
                "Help me set up my returns policy",
                "How do I reduce my return rate?",
                "Create a returns workflow for my store",
                "What are common returns mistakes?",
            ],
            "capabilities": {
                "web_browsing": False,
                "dall_e": False,
                "code_interpreter": True,
            },
        }
    )


class TestGptConfigGeneratorInheritance:
    """Test that GptConfigGenerator properly inherits from BaseGenerator."""

    def test_inherits_from_base_generator(self):
        """GptConfigGenerator should inherit from BaseGenerator."""
        generator = GptConfigGenerator()
        assert isinstance(generator, BaseGenerator)

    def test_has_generate_method(self):
        """Generator should have generate method from base class."""
        generator = GptConfigGenerator()
        assert hasattr(generator, "generate")
        assert callable(generator.generate)

    def test_has_validate_method(self):
        """Generator should have validate method from base class."""
        generator = GptConfigGenerator()
        assert hasattr(generator, "validate")
        assert callable(generator.validate)

    def test_accepts_claude_client(self):
        """Generator should accept optional claude_client."""
        mock_client = MagicMock()
        generator = GptConfigGenerator(claude_client=mock_client)
        assert generator.claude_client == mock_client


class TestGptConfigGeneratorProductType:
    """Test product type identification."""

    def test_get_product_type_returns_gpt_config(self):
        """get_product_type should return 'gpt_config'."""
        generator = GptConfigGenerator()
        assert generator.get_product_type() == "gpt_config"


class TestGptConfigGeneratorGenerate:
    """Test the generate method."""

    def test_generate_produces_four_files(self, sample_spec):
        """Generate should produce exactly 4 required files."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        assert "gpt_config.json" in product.files
        assert "INSTRUCTIONS.md" in product.files
        assert "SETUP_GUIDE.md" in product.files
        assert "conversation_starters.txt" in product.files
        assert len(product.files) == 4

    def test_generate_creates_valid_json(self, sample_spec):
        """gpt_config.json should be valid JSON."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        config_bytes = product.files["gpt_config.json"]
        config = json.loads(config_bytes.decode("utf-8"))

        assert "name" in config
        assert "description" in config
        assert "instructions" in config
        assert "conversation_starters" in config
        assert "capabilities" in config

    def test_generate_with_claude_client(self, sample_spec, mock_claude_response):
        """Generate should use Claude client when provided."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = GptConfigGenerator(claude_client=mock_client)
        product = generator.generate(sample_spec)

        mock_client.generate.assert_called_once()
        config = json.loads(product.files["gpt_config.json"].decode("utf-8"))
        assert config["name"] == "Returns Master GPT"

    def test_generate_creates_manifest(self, sample_spec):
        """Generate should create a valid manifest."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        assert "id" in product.manifest
        assert product.manifest["type"] == "gpt_config"
        assert product.manifest["name"] == sample_spec.solution_name

    def test_generate_instructions_md_includes_full_prompt(self, sample_spec):
        """INSTRUCTIONS.md should include the full instructions."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        instructions_content = product.files["INSTRUCTIONS.md"].decode("utf-8")

        # Should include the solution name
        assert sample_spec.solution_name in instructions_content
        # Should have markdown formatting
        assert "#" in instructions_content

    def test_generate_conversation_starters_one_per_line(self, sample_spec):
        """conversation_starters.txt should have one starter per line."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        starters_content = product.files["conversation_starters.txt"].decode("utf-8")
        starters = starters_content.strip().split("\n")

        assert len(starters) == 4
        for starter in starters:
            assert len(starter) > 0

    def test_generate_setup_guide_includes_gpt_name(self, sample_spec):
        """SETUP_GUIDE.md should include the GPT name."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        setup_content = product.files["SETUP_GUIDE.md"].decode("utf-8")
        # Should include some reference to the GPT
        assert "GPT" in setup_content
        assert "ChatGPT" in setup_content


class TestGptConfigGeneratorValidate:
    """Test the validate method."""

    def test_validate_catches_invalid_json(self, sample_spec):
        """Validate should return False for invalid JSON."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        # Corrupt the JSON
        product.files["gpt_config.json"] = b"not valid json"

        assert generator.validate(product) is False

    def test_validate_catches_name_over_25_chars(self, sample_spec):
        """Validate should return False if name exceeds 25 characters."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        # Modify config with too-long name
        config = json.loads(product.files["gpt_config.json"].decode("utf-8"))
        config["name"] = "This Name Is Way Too Long For GPT"  # 34 chars
        product.files["gpt_config.json"] = json.dumps(config).encode("utf-8")

        assert generator.validate(product) is False

    def test_validate_catches_description_over_300_chars(self, sample_spec):
        """Validate should return False if description exceeds 300 characters."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        # Modify config with too-long description
        config = json.loads(product.files["gpt_config.json"].decode("utf-8"))
        config["description"] = "x" * 301  # 301 chars
        product.files["gpt_config.json"] = json.dumps(config).encode("utf-8")

        assert generator.validate(product) is False

    def test_validate_catches_instructions_under_500_words(self, sample_spec):
        """Validate should return False if instructions under 500 words."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        # Modify config with short instructions
        config = json.loads(product.files["gpt_config.json"].decode("utf-8"))
        config["instructions"] = "This is way too short to be useful."  # ~7 words
        product.files["gpt_config.json"] = json.dumps(config).encode("utf-8")

        assert generator.validate(product) is False

    def test_validate_catches_less_than_4_starters(self, sample_spec):
        """Validate should return False if less than 4 conversation starters."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        # Modify config with only 2 starters
        config = json.loads(product.files["gpt_config.json"].decode("utf-8"))
        config["conversation_starters"] = ["Starter 1", "Starter 2"]
        product.files["gpt_config.json"] = json.dumps(config).encode("utf-8")

        assert generator.validate(product) is False

    def test_validate_catches_more_than_4_starters(self, sample_spec):
        """Validate should return False if more than 4 conversation starters."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        # Modify config with 5 starters
        config = json.loads(product.files["gpt_config.json"].decode("utf-8"))
        config["conversation_starters"] = ["S1", "S2", "S3", "S4", "S5"]
        product.files["gpt_config.json"] = json.dumps(config).encode("utf-8")

        assert generator.validate(product) is False

    def test_validate_catches_missing_files(self, sample_spec):
        """Validate should return False if required files are missing."""
        generator = GptConfigGenerator()
        product = generator.generate(sample_spec)

        # Remove a required file
        del product.files["INSTRUCTIONS.md"]

        assert generator.validate(product) is False

    def test_validate_passes_valid_product(self, sample_spec, mock_claude_response):
        """Validate should return True for valid products."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = GptConfigGenerator(claude_client=mock_client)
        product = generator.generate(sample_spec)

        assert generator.validate(product) is True


class TestGptConfigPrompt:
    """Test the GPT config prompt template."""

    def test_prompt_contains_placeholders(self):
        """GPT_CONFIG_PROMPT should contain all required placeholders."""
        assert "{problem}" in GPT_CONFIG_PROMPT
        assert "{solution_name}" in GPT_CONFIG_PROMPT
        assert "{target_audience}" in GPT_CONFIG_PROMPT
        assert "{key_benefits}" in GPT_CONFIG_PROMPT

    def test_prompt_specifies_output_format(self):
        """Prompt should specify JSON output format."""
        assert "JSON" in GPT_CONFIG_PROMPT
        assert "name" in GPT_CONFIG_PROMPT
        assert "description" in GPT_CONFIG_PROMPT
        assert "instructions" in GPT_CONFIG_PROMPT
        assert "conversation_starters" in GPT_CONFIG_PROMPT


class TestSetupGuideTemplate:
    """Test the setup guide template."""

    def test_template_has_placeholder(self):
        """SETUP_GUIDE_TEMPLATE should have gpt_name placeholder."""
        assert "{gpt_name}" in SETUP_GUIDE_TEMPLATE

    def test_template_includes_steps(self):
        """Template should include step-by-step instructions."""
        assert "Step 1" in SETUP_GUIDE_TEMPLATE
        assert "Step 2" in SETUP_GUIDE_TEMPLATE
        assert "ChatGPT" in SETUP_GUIDE_TEMPLATE

    def test_template_mentions_knowledge_files(self):
        """Template should explain how to add knowledge files."""
        assert "Knowledge" in SETUP_GUIDE_TEMPLATE or "files" in SETUP_GUIDE_TEMPLATE

    def test_template_includes_testing_guidance(self):
        """Template should include guidance on testing the GPT."""
        assert "Test" in SETUP_GUIDE_TEMPLATE or "Preview" in SETUP_GUIDE_TEMPLATE


class TestParseGptConfig:
    """Test the _parse_gpt_config helper method."""

    def test_parse_valid_json(self):
        """Should parse valid JSON response."""
        generator = GptConfigGenerator()
        response = '{"name": "Test", "description": "A test"}'

        result = generator._parse_gpt_config(response)

        assert result["name"] == "Test"
        assert result["description"] == "A test"

    def test_parse_json_in_code_block(self):
        """Should parse JSON wrapped in markdown code blocks."""
        generator = GptConfigGenerator()
        response = '```json\n{"name": "Test", "description": "A test"}\n```'

        result = generator._parse_gpt_config(response)

        assert result["name"] == "Test"

    def test_parse_invalid_json_returns_empty_config(self):
        """Should return empty config for invalid JSON."""
        generator = GptConfigGenerator()
        response = "This is not JSON at all"

        result = generator._parse_gpt_config(response)

        assert "name" in result
        assert result["conversation_starters"] == []
