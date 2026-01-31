"""
Tests for the Prompt Pack Generator.

Tests cover:
- Generator inheritance from BaseGenerator
- Product type identification
- File generation (all 4 required files)
- Validation (categories, prompts count, prompt length)
- Markdown formatting
- Claude client mocking
"""

import json
from unittest.mock import MagicMock

import pytest

from execution.generators.base_generator import BaseGenerator, ProductSpec
from execution.generators.prompt_pack import (
    PROMPT_PACK_PROMPT,
    PromptPackGenerator,
)


@pytest.fixture
def sample_spec():
    """Create a sample ProductSpec for testing."""
    return ProductSpec(
        problem="Creating effective marketing copy",
        solution_name="Marketing Copy Master",
        target_audience="Small business owners",
        key_benefits=[
            "Write compelling headlines",
            "Create persuasive product descriptions",
            "Develop email sequences that convert",
        ],
        product_type="prompt_pack",
    )


@pytest.fixture
def mock_claude_response():
    """Create a mock Claude response with valid prompt pack."""
    return json.dumps(
        {
            "title": "Marketing Copy Master Pack",
            "description": "Prompts to help small business owners create compelling marketing copy.",
            "categories": [
                {
                    "name": "Headlines & Hooks",
                    "description": "Prompts for attention-grabbing headlines",
                    "prompts": [
                        {
                            "title": "Headline Generator",
                            "prompt_text": "Create 10 headlines for [YOUR PRODUCT] targeting [YOUR AUDIENCE]. Focus on benefits.",
                            "expected_output_description": "10 headline variations",
                            "example_output": "1. Transform Your [Problem] in Just [Time]",
                        },
                        {
                            "title": "Hook Creator",
                            "prompt_text": "Write 5 opening hooks for [YOUR TOPIC] that create curiosity.",
                            "expected_output_description": "5 attention-grabbing hooks",
                            "example_output": "What if everything you knew about X was wrong?",
                        },
                        {
                            "title": "Subject Line Writer",
                            "prompt_text": "Generate 7 email subject lines for [YOUR CAMPAIGN] with open rate optimization.",
                            "expected_output_description": "7 subject line variations",
                            "example_output": "[First name], don't miss this...",
                        },
                        {
                            "title": "Tagline Developer",
                            "prompt_text": "Create 5 memorable taglines for [YOUR BRAND] that emphasize [KEY BENEFIT].",
                            "expected_output_description": "5 brand taglines",
                            "example_output": "Where quality meets affordability.",
                        },
                        {
                            "title": "CTA Optimizer",
                            "prompt_text": "Improve this call-to-action: [YOUR CTA]. Make it more compelling and urgent.",
                            "expected_output_description": "3 improved CTA variations",
                            "example_output": "Get instant access now (limited spots)",
                        },
                    ],
                },
                {
                    "name": "Product Descriptions",
                    "description": "Prompts for compelling product copy",
                    "prompts": [
                        {
                            "title": "Feature-Benefit Converter",
                            "prompt_text": "Convert these features into benefits: [YOUR FEATURES]. Focus on customer outcomes.",
                            "expected_output_description": "Feature-benefit mapping",
                            "example_output": "Feature: Fast shipping → Benefit: Get your order when you need it",
                        },
                        {
                            "title": "Product Story Writer",
                            "prompt_text": "Write a compelling origin story for [YOUR PRODUCT] that connects with [YOUR AUDIENCE].",
                            "expected_output_description": "Brand/product story",
                            "example_output": "It started when we noticed...",
                        },
                        {
                            "title": "Comparison Maker",
                            "prompt_text": "Create a comparison between [YOUR PRODUCT] and alternatives without naming competitors.",
                            "expected_output_description": "Subtle comparison copy",
                            "example_output": "Unlike typical solutions, we...",
                        },
                        {
                            "title": "Social Proof Writer",
                            "prompt_text": "Turn this customer review into marketing copy: [REVIEW]. Maintain authenticity.",
                            "expected_output_description": "Testimonial-based copy",
                            "example_output": "Real customers are saying...",
                        },
                        {
                            "title": "Urgency Creator",
                            "prompt_text": "Add urgency to this offer: [YOUR OFFER]. Use ethical urgency tactics.",
                            "expected_output_description": "Urgency-enhanced copy",
                            "example_output": "This week only: Get X before...",
                        },
                    ],
                },
                {
                    "name": "Email Sequences",
                    "description": "Prompts for email marketing",
                    "prompts": [
                        {
                            "title": "Welcome Series Outline",
                            "prompt_text": "Create a 5-email welcome sequence outline for [YOUR PRODUCT/SERVICE] subscribers.",
                            "expected_output_description": "5-email sequence structure",
                            "example_output": "Email 1: Welcome & quick win. Email 2: Your story...",
                        },
                        {
                            "title": "Follow-up Email",
                            "prompt_text": "Write a follow-up email for someone who [ACTION]. Goal: [YOUR GOAL].",
                            "expected_output_description": "Follow-up email draft",
                            "example_output": "Hi [Name], Just checking in after...",
                        },
                        {
                            "title": "Re-engagement Email",
                            "prompt_text": "Create an email to re-engage subscribers who haven't opened in 30 days. Offer: [YOUR OFFER].",
                            "expected_output_description": "Win-back email",
                            "example_output": "We miss you! Here's something special...",
                        },
                        {
                            "title": "Launch Announcement",
                            "prompt_text": "Write a launch announcement email for [YOUR NEW PRODUCT]. Build excitement.",
                            "expected_output_description": "Launch email",
                            "example_output": "The wait is over...",
                        },
                        {
                            "title": "Cart Recovery",
                            "prompt_text": "Create a cart abandonment email sequence (3 emails) for [YOUR STORE].",
                            "expected_output_description": "3-email cart recovery series",
                            "example_output": "Email 1 (1hr): Did you forget something?...",
                        },
                    ],
                },
            ],
        }
    )


class TestPromptPackGeneratorInheritance:
    """Test that PromptPackGenerator properly inherits from BaseGenerator."""

    def test_inherits_from_base_generator(self):
        """PromptPackGenerator should inherit from BaseGenerator."""
        generator = PromptPackGenerator()
        assert isinstance(generator, BaseGenerator)

    def test_has_generate_method(self):
        """Generator should have generate method from base class."""
        generator = PromptPackGenerator()
        assert hasattr(generator, "generate")
        assert callable(generator.generate)

    def test_has_validate_method(self):
        """Generator should have validate method from base class."""
        generator = PromptPackGenerator()
        assert hasattr(generator, "validate")
        assert callable(generator.validate)

    def test_accepts_claude_client(self):
        """Generator should accept optional claude_client."""
        mock_client = MagicMock()
        generator = PromptPackGenerator(claude_client=mock_client)
        assert generator.claude_client == mock_client


class TestPromptPackGeneratorProductType:
    """Test product type identification."""

    def test_get_product_type_returns_prompt_pack(self):
        """get_product_type should return 'prompt_pack'."""
        generator = PromptPackGenerator()
        assert generator.get_product_type() == "prompt_pack"


class TestPromptPackGeneratorGenerate:
    """Test the generate method."""

    def test_generate_produces_four_files(self, sample_spec):
        """Generate should produce exactly 4 required files."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        assert "prompts.json" in product.files
        assert "prompts.md" in product.files
        assert "README.md" in product.files
        assert "QUICK_START.md" in product.files
        assert len(product.files) == 4

    def test_generate_creates_valid_json(self, sample_spec):
        """prompts.json should be valid JSON with expected structure."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        prompts_bytes = product.files["prompts.json"]
        prompts_data = json.loads(prompts_bytes.decode("utf-8"))

        assert "title" in prompts_data
        assert "categories" in prompts_data
        assert len(prompts_data["categories"]) >= 3

    def test_generate_with_claude_client(self, sample_spec, mock_claude_response):
        """Generate should use Claude client when provided."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = PromptPackGenerator(claude_client=mock_client)
        product = generator.generate(sample_spec)

        mock_client.generate.assert_called_once()
        prompts_data = json.loads(product.files["prompts.json"].decode("utf-8"))
        assert prompts_data["title"] == "Marketing Copy Master Pack"

    def test_generate_creates_manifest(self, sample_spec):
        """Generate should create a valid manifest."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        assert "id" in product.manifest
        assert product.manifest["type"] == "prompt_pack"
        assert "total_prompts" in product.manifest
        assert "categories" in product.manifest


class TestPromptPackGeneratorValidate:
    """Test the validate method."""

    def test_validate_catches_less_than_3_categories(self, sample_spec):
        """Validate should return False if less than 3 categories."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        # Modify to have only 2 categories
        prompts_data = json.loads(product.files["prompts.json"].decode("utf-8"))
        prompts_data["categories"] = prompts_data["categories"][:2]
        product.files["prompts.json"] = json.dumps(prompts_data).encode("utf-8")

        assert generator.validate(product) is False

    def test_validate_catches_less_than_15_prompts(self, sample_spec):
        """Validate should return False if less than 15 total prompts."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        # Modify to have only 12 prompts (4 per category)
        prompts_data = json.loads(product.files["prompts.json"].decode("utf-8"))
        for category in prompts_data["categories"]:
            category["prompts"] = category["prompts"][:4]
        product.files["prompts.json"] = json.dumps(prompts_data).encode("utf-8")

        assert generator.validate(product) is False

    def test_validate_catches_short_prompts(self, sample_spec):
        """Validate should return False if any prompt is under 20 chars."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        # Modify one prompt to be too short
        prompts_data = json.loads(product.files["prompts.json"].decode("utf-8"))
        prompts_data["categories"][0]["prompts"][0]["prompt_text"] = (
            "Too short"  # 9 chars
        )
        product.files["prompts.json"] = json.dumps(prompts_data).encode("utf-8")

        assert generator.validate(product) is False

    def test_validate_catches_missing_prompt_fields(self, sample_spec):
        """Validate should return False if prompt missing required fields."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        # Remove title from one prompt
        prompts_data = json.loads(product.files["prompts.json"].decode("utf-8"))
        del prompts_data["categories"][0]["prompts"][0]["title"]
        product.files["prompts.json"] = json.dumps(prompts_data).encode("utf-8")

        assert generator.validate(product) is False

    def test_validate_catches_missing_files(self, sample_spec):
        """Validate should return False if required files are missing."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        # Remove a required file
        del product.files["QUICK_START.md"]

        assert generator.validate(product) is False

    def test_validate_catches_invalid_json(self, sample_spec):
        """Validate should return False for invalid JSON."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        # Corrupt the JSON
        product.files["prompts.json"] = b"not valid json"

        assert generator.validate(product) is False

    def test_validate_passes_valid_product(self, sample_spec, mock_claude_response):
        """Validate should return True for valid products."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = PromptPackGenerator(claude_client=mock_client)
        product = generator.generate(sample_spec)

        assert generator.validate(product) is True

    def test_validate_passes_fallback_product(self, sample_spec):
        """Validate should return True for fallback-generated products."""
        generator = PromptPackGenerator()  # No Claude client
        product = generator.generate(sample_spec)

        assert generator.validate(product) is True


class TestPromptPackMarkdownFormatting:
    """Test markdown formatting functionality."""

    def test_prompts_md_includes_code_blocks(self, sample_spec):
        """prompts.md should include code blocks for prompts."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        markdown_content = product.files["prompts.md"].decode("utf-8")

        # Should have code blocks (```)
        assert "```" in markdown_content

    def test_prompts_md_includes_all_categories(self, sample_spec):
        """prompts.md should include all categories."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        markdown_content = product.files["prompts.md"].decode("utf-8")
        prompts_data = json.loads(product.files["prompts.json"].decode("utf-8"))

        for category in prompts_data["categories"]:
            assert category["name"] in markdown_content

    def test_quick_start_has_5_prompts(self, sample_spec):
        """QUICK_START.md should have 5 prompts."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        quick_start = product.files["QUICK_START.md"].decode("utf-8")

        # Count numbered prompts (## 1., ## 2., etc.)
        prompt_count = sum(
            1
            for line in quick_start.split("\n")
            if line.startswith("## ") and line[3].isdigit()
        )
        assert prompt_count == 5

    def test_readme_includes_usage_instructions(self, sample_spec):
        """README.md should include how to use the pack."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        readme = product.files["README.md"].decode("utf-8")

        assert "How to Use" in readme
        assert "Copy" in readme or "Paste" in readme


class TestPromptPackPrompt:
    """Test the prompt pack prompt template."""

    def test_prompt_contains_placeholders(self):
        """PROMPT_PACK_PROMPT should contain all required placeholders."""
        assert "{problem}" in PROMPT_PACK_PROMPT
        assert "{solution_name}" in PROMPT_PACK_PROMPT
        assert "{target_audience}" in PROMPT_PACK_PROMPT

    def test_prompt_specifies_output_format(self):
        """Prompt should specify JSON output format."""
        assert "JSON" in PROMPT_PACK_PROMPT
        assert "categories" in PROMPT_PACK_PROMPT
        assert "prompts" in PROMPT_PACK_PROMPT

    def test_prompt_specifies_requirements(self):
        """Prompt should specify category and prompt requirements."""
        assert "3-5 categories" in PROMPT_PACK_PROMPT
        assert "15" in PROMPT_PACK_PROMPT  # at least 15 prompts


class TestParsePromptsData:
    """Test the _parse_prompts_data helper method."""

    def test_parse_valid_json(self):
        """Should parse valid JSON response."""
        generator = PromptPackGenerator()
        response = '{"title": "Test Pack", "categories": []}'

        result = generator._parse_prompts_data(response)

        assert result["title"] == "Test Pack"

    def test_parse_json_in_code_block(self):
        """Should parse JSON wrapped in markdown code blocks."""
        generator = PromptPackGenerator()
        response = '```json\n{"title": "Test Pack", "categories": []}\n```'

        result = generator._parse_prompts_data(response)

        assert result["title"] == "Test Pack"

    def test_parse_invalid_json_returns_empty_structure(self):
        """Should return empty structure for invalid JSON."""
        generator = PromptPackGenerator()
        response = "This is not JSON"

        result = generator._parse_prompts_data(response)

        assert "title" in result
        assert result["categories"] == []


class TestCountPrompts:
    """Test the _count_prompts helper method."""

    def test_count_prompts_correctly(self, sample_spec):
        """Should count total prompts across all categories."""
        generator = PromptPackGenerator()
        product = generator.generate(sample_spec)

        prompts_data = json.loads(product.files["prompts.json"].decode("utf-8"))
        count = generator._count_prompts(prompts_data)

        # Fallback pack has 5 prompts per category, 3 categories = 15 prompts
        assert count >= 15

    def test_count_empty_categories(self):
        """Should handle empty categories."""
        generator = PromptPackGenerator()
        prompts_data = {"categories": [{"prompts": []}, {"prompts": []}]}

        count = generator._count_prompts(prompts_data)

        assert count == 0
