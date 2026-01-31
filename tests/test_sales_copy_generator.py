"""
Tests for the sales copy generator module.
"""

import json
import pytest
from unittest.mock import Mock, patch

from execution.sales_copy_generator import (
    SalesCopyGenerator,
    generate_sales_copy,
    SALES_COPY_PROMPT,
)
from execution.generators.base_generator import ProductSpec


@pytest.fixture
def sample_spec():
    """Create a sample ProductSpec for testing."""
    return ProductSpec(
        problem="Finding profitable products takes weeks of manual research",
        solution_name="Product Research Accelerator",
        target_audience="DTC e-commerce founders",
        key_benefits=[
            "Find winning products in under 2 hours",
            "Validate demand before investing inventory",
            "Spy on competitor bestsellers automatically",
            "Get profit margin calculations instantly",
            "Access a database of 10,000+ tested products",
        ],
        product_type="html_tool",
    )


@pytest.fixture
def sample_copy_dict():
    """Create sample sales copy dict for testing."""
    return {
        "headline": "Stop Guessing. Start Selling.",
        "subheadline": "The exact system 7-figure brands use to find winning products",
        "problem_section": (
            "You're spending weeks researching products. "
            "Most will never sell. "
            "That's time and money you can't get back."
        ),
        "solution_section": (
            "Product Research Accelerator cuts your research time from weeks to hours. "
            "It validates demand, analyzes competition, and calculates margins automatically."
        ),
        "benefit_bullets": [
            "Find winning products in under 2 hours",
            "Validate demand before investing inventory",
            "Spy on competitor bestsellers automatically",
            "Get profit margin calculations instantly",
            "Access a database of 10,000+ tested products",
        ],
        "value_anchor": "Competitors charge $97/month for similar tools. This is yours forever for one price.",
        "price_justification": "At $47, this pays for itself with your first winning product. Most users find one within a week.",
        "cta": "Get the Accelerator Now",
    }


class TestSalesCopyGeneratorInit:
    """Tests for SalesCopyGenerator initialization."""

    def test_can_instantiate(self):
        """Test that SalesCopyGenerator can be instantiated."""
        generator = SalesCopyGenerator()
        assert generator is not None

    def test_instantiate_with_claude_client(self):
        """Test instantiation with a Claude client."""
        mock_client = Mock()
        generator = SalesCopyGenerator(claude_client=mock_client)
        assert generator.claude_client == mock_client

    def test_has_required_sections(self):
        """Test that REQUIRED_SECTIONS constant is defined."""
        assert len(SalesCopyGenerator.REQUIRED_SECTIONS) == 8
        assert "headline" in SalesCopyGenerator.REQUIRED_SECTIONS
        assert "benefit_bullets" in SalesCopyGenerator.REQUIRED_SECTIONS


class TestSalesCopyGeneratorGenerate:
    """Tests for the generate method."""

    def test_generate_returns_dict_with_all_sections(self, sample_spec):
        """Test that generate returns dict with all 8 sections."""
        generator = SalesCopyGenerator()
        result = generator.generate(sample_spec, "$47", "$500+ worth of tools")

        assert isinstance(result, dict)
        for section in SalesCopyGenerator.REQUIRED_SECTIONS:
            assert section in result

    def test_generate_with_claude_client(self, sample_spec, sample_copy_dict):
        """Test generation with a mock Claude client."""
        mock_client = Mock()
        mock_client.generate_with_voice.return_value = json.dumps(sample_copy_dict)

        generator = SalesCopyGenerator(claude_client=mock_client)
        result = generator.generate(sample_spec, "$47", "$500+ worth")

        mock_client.generate_with_voice.assert_called_once()
        assert result["headline"] == sample_copy_dict["headline"]

    def test_generate_fallback_without_client(self, sample_spec):
        """Test that fallback generation works without Claude client."""
        generator = SalesCopyGenerator()
        result = generator.generate(sample_spec, "$47", "$500+ worth")

        assert "headline" in result
        assert "benefit_bullets" in result
        assert len(result["benefit_bullets"]) >= 5

    def test_generate_fallback_on_claude_error(self, sample_spec):
        """Test fallback when Claude client raises an exception."""
        mock_client = Mock()
        mock_client.generate_with_voice.side_effect = Exception("API error")

        generator = SalesCopyGenerator(claude_client=mock_client)
        result = generator.generate(sample_spec, "$47", "$500+ worth")

        # Should fall back to fallback generation
        assert "headline" in result
        assert "benefit_bullets" in result

    def test_generate_uses_voice_profile(self, sample_spec, sample_copy_dict):
        """Test that generation uses the voice profile."""
        mock_client = Mock()
        mock_client.generate_with_voice.return_value = json.dumps(sample_copy_dict)

        generator = SalesCopyGenerator(claude_client=mock_client)
        generator.generate(sample_spec, "$47", "$500+ worth")

        # Verify generate_with_voice was called (which uses voice profile)
        mock_client.generate_with_voice.assert_called_once()
        call_args = mock_client.generate_with_voice.call_args
        prompt = call_args[0][0]

        # Prompt should contain product info
        assert "Product Research Accelerator" in prompt
        assert "DTC Money Minute voice" in prompt


class TestSalesCopyGeneratorFormatMarkdown:
    """Tests for the format_markdown method."""

    def test_format_markdown_produces_valid_output(self, sample_copy_dict):
        """Test that format_markdown produces valid markdown."""
        generator = SalesCopyGenerator()
        result = generator.format_markdown(sample_copy_dict)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_markdown_includes_all_sections(self, sample_copy_dict):
        """Test that formatted markdown includes all sections."""
        generator = SalesCopyGenerator()
        result = generator.format_markdown(sample_copy_dict)

        # Check for headers
        assert "# " in result  # Headline
        assert "## " in result  # Subheadline
        assert "### The Problem" in result
        assert "### The Solution" in result
        assert "### What You Get" in result
        assert "### The Value" in result
        assert "### Why This Price" in result

    def test_format_markdown_includes_benefit_bullets(self, sample_copy_dict):
        """Test that benefit bullets are formatted as list."""
        generator = SalesCopyGenerator()
        result = generator.format_markdown(sample_copy_dict)

        # Count bullet points
        bullet_count = result.count("\n- ")
        assert bullet_count >= 5

    def test_format_markdown_includes_cta(self, sample_copy_dict):
        """Test that CTA is included in bold."""
        generator = SalesCopyGenerator()
        result = generator.format_markdown(sample_copy_dict)

        assert "**Get the Accelerator Now**" in result


class TestSalesCopyGeneratorValidate:
    """Tests for the validate method."""

    def test_validate_valid_copy(self, sample_copy_dict):
        """Test that valid copy passes validation."""
        generator = SalesCopyGenerator()
        is_valid, issues = generator.validate(sample_copy_dict)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_catches_missing_sections(self, sample_copy_dict):
        """Test that validation catches missing sections."""
        generator = SalesCopyGenerator()

        # Remove a required section
        incomplete_copy = sample_copy_dict.copy()
        del incomplete_copy["headline"]

        is_valid, issues = generator.validate(incomplete_copy)

        assert is_valid is False
        assert any("Missing section: headline" in issue for issue in issues)

    def test_validate_catches_headline_too_long(self, sample_copy_dict):
        """Test that validation catches headline > 10 words."""
        generator = SalesCopyGenerator()

        # Make headline too long
        long_headline_copy = sample_copy_dict.copy()
        long_headline_copy["headline"] = (
            "This is a very long headline that has way more than ten words in it"
        )

        is_valid, issues = generator.validate(long_headline_copy)

        assert is_valid is False
        assert any("Headline too long" in issue for issue in issues)

    def test_validate_catches_few_benefits(self, sample_copy_dict):
        """Test that validation catches < 5 benefit bullets."""
        generator = SalesCopyGenerator()

        # Reduce benefits to less than 5
        few_benefits_copy = sample_copy_dict.copy()
        few_benefits_copy["benefit_bullets"] = ["Benefit 1", "Benefit 2", "Benefit 3"]

        is_valid, issues = generator.validate(few_benefits_copy)

        assert is_valid is False
        assert any("Not enough benefit bullets" in issue for issue in issues)

    def test_validate_returns_multiple_issues(self):
        """Test that validation returns all issues found."""
        generator = SalesCopyGenerator()

        # Create copy with multiple issues
        bad_copy = {
            "headline": "This headline is definitely way too long to pass the ten word limit",
            "subheadline": "Good subheadline",
            "problem_section": "Good problem",
            "solution_section": "Good solution",
            "benefit_bullets": ["Only one bullet"],
            "value_anchor": "Good anchor",
            "price_justification": "Good justification",
            "cta": "Good CTA",
        }

        is_valid, issues = generator.validate(bad_copy)

        assert is_valid is False
        assert len(issues) >= 2  # At least headline too long + not enough benefits


class TestGenerateSalesCopyFunction:
    """Tests for the convenience function."""

    def test_convenience_function_works(self, sample_spec):
        """Test that generate_sales_copy convenience function works."""
        result = generate_sales_copy(sample_spec, "$47", "$500+ worth of tools")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "# " in result  # Should have markdown headers

    def test_convenience_function_with_client(self, sample_spec, sample_copy_dict):
        """Test convenience function with Claude client."""
        mock_client = Mock()
        mock_client.generate_with_voice.return_value = json.dumps(sample_copy_dict)

        result = generate_sales_copy(
            sample_spec, "$47", "$500+ worth", claude_client=mock_client
        )

        assert "Stop Guessing. Start Selling." in result
        mock_client.generate_with_voice.assert_called_once()


class TestSalesCopyGeneratorEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_response_handles_markdown_blocks(self, sample_copy_dict):
        """Test that JSON wrapped in markdown blocks is parsed correctly."""
        generator = SalesCopyGenerator()

        # Wrap JSON in markdown code block
        wrapped_response = f"```json\n{json.dumps(sample_copy_dict)}\n```"

        result = generator._parse_response(wrapped_response)
        assert result["headline"] == sample_copy_dict["headline"]

    def test_parse_response_handles_invalid_json(self):
        """Test that invalid JSON returns empty dict."""
        generator = SalesCopyGenerator()

        result = generator._parse_response("not valid json at all")
        assert result == {}

    def test_fallback_pads_benefits_to_five(self):
        """Test that fallback pads benefits to 5 if fewer provided."""
        spec = ProductSpec(
            problem="Test problem",
            solution_name="Test Solution",
            target_audience="Test audience",
            key_benefits=["Benefit 1", "Benefit 2"],  # Only 2 benefits
            product_type="html_tool",
        )

        generator = SalesCopyGenerator()
        result = generator._generate_fallback(spec, "$27", "$200+ value")

        assert len(result["benefit_bullets"]) == 5

    def test_validate_empty_section_fails(self, sample_copy_dict):
        """Test that empty sections fail validation."""
        generator = SalesCopyGenerator()

        empty_section_copy = sample_copy_dict.copy()
        empty_section_copy["headline"] = ""

        is_valid, issues = generator.validate(empty_section_copy)

        assert is_valid is False
        assert any("Missing section: headline" in issue for issue in issues)


class TestSalesCopyPromptTemplate:
    """Tests for the prompt template."""

    def test_prompt_template_has_placeholders(self):
        """Test that prompt template has all required placeholders."""
        assert "{product_name}" in SALES_COPY_PROMPT
        assert "{problem}" in SALES_COPY_PROMPT
        assert "{audience}" in SALES_COPY_PROMPT
        assert "{benefits}" in SALES_COPY_PROMPT
        assert "{price_display}" in SALES_COPY_PROMPT
        assert "{perceived_value}" in SALES_COPY_PROMPT

    def test_prompt_mentions_voice_profile(self):
        """Test that prompt mentions DTC Money Minute voice."""
        assert "DTC Money Minute" in SALES_COPY_PROMPT
        assert "short sentences" in SALES_COPY_PROMPT
        assert "zero fluff" in SALES_COPY_PROMPT
