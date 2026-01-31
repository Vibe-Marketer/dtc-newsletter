"""
Tests for the HTML Tool Generator.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from execution.generators import BaseGenerator, GeneratedProduct, ProductSpec
from execution.generators.html_tool import HtmlToolGenerator, HTML_TOOL_PROMPT


class TestHtmlToolGeneratorBasics:
    """Test basic generator setup and inheritance."""

    def test_inherits_from_base_generator(self):
        """HTML tool generator should inherit from BaseGenerator."""
        generator = HtmlToolGenerator()
        assert isinstance(generator, BaseGenerator)

    def test_get_product_type_returns_html_tool(self):
        """get_product_type should return 'html_tool'."""
        generator = HtmlToolGenerator()
        assert generator.get_product_type() == "html_tool"

    def test_init_with_claude_client(self):
        """Should accept optional claude_client."""
        mock_client = MagicMock()
        generator = HtmlToolGenerator(claude_client=mock_client)
        assert generator.claude_client is mock_client

    def test_init_with_custom_template_path(self):
        """Should accept optional template_path."""
        custom_path = Path("/custom/template.html")
        generator = HtmlToolGenerator(template_path=custom_path)
        assert generator.template_path == custom_path

    def test_default_template_path(self):
        """Should have sensible default template path."""
        generator = HtmlToolGenerator()
        assert "base.html" in str(generator.template_path)
        assert "html" in str(generator.template_path)


class TestHtmlToolGeneratorGeneration:
    """Test the generate method."""

    @pytest.fixture
    def valid_spec(self):
        """Create a valid ProductSpec for testing."""
        return ProductSpec(
            problem="E-commerce owners struggle to calculate true profit margins",
            solution_name="Profit Calculator",
            target_audience="Shopify store owners",
            key_benefits=[
                "Calculate profit in seconds",
                "Account for all fees",
                "Track margins over time",
            ],
            product_type="html_tool",
        )

    @pytest.fixture
    def mock_claude_response(self):
        """Valid Claude response for HTML tool generation."""
        return json.dumps(
            {
                "title": "Profit Calculator",
                "css": "body { font-family: sans-serif; } .container { max-width: 800px; margin: 0 auto; }",
                "body_html": '<main class="container"><h1>Profit Calculator</h1><input type="number" id="revenue"><button onclick="calculate()">Calculate</button><div id="result"></div></main>',
                "javascript": "function calculate() { const revenue = document.getElementById('revenue').value; document.getElementById('result').textContent = 'Profit: $' + (revenue * 0.3); }",
            }
        )

    def test_generate_produces_html_file(self, valid_spec, mock_claude_response):
        """generate should produce a .html file in the output."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = HtmlToolGenerator(claude_client=mock_client)
        product = generator.generate(valid_spec)

        html_files = [f for f in product.files.keys() if f.endswith(".html")]
        assert len(html_files) == 1

    def test_generate_includes_readme(self, valid_spec, mock_claude_response):
        """generate should produce a README.md file."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = HtmlToolGenerator(claude_client=mock_client)
        product = generator.generate(valid_spec)

        assert "README.md" in product.files

    def test_generate_html_is_valid_structure(self, valid_spec, mock_claude_response):
        """Generated HTML should have proper structure."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = HtmlToolGenerator(claude_client=mock_client)
        product = generator.generate(valid_spec)

        # Find HTML file
        html_content = None
        for filename, content in product.files.items():
            if filename.endswith(".html"):
                html_content = content.decode("utf-8")
                break

        assert html_content is not None
        assert "<!DOCTYPE html>" in html_content
        assert "<html" in html_content
        assert "<head" in html_content
        assert "<body" in html_content
        assert "</html>" in html_content

    def test_generate_returns_generated_product(self, valid_spec, mock_claude_response):
        """generate should return a GeneratedProduct instance."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = HtmlToolGenerator(claude_client=mock_client)
        product = generator.generate(valid_spec)

        assert isinstance(product, GeneratedProduct)
        assert isinstance(product.files, dict)
        assert isinstance(product.manifest, dict)

    def test_generate_manifest_has_required_fields(
        self, valid_spec, mock_claude_response
    ):
        """Manifest should have required metadata fields."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = HtmlToolGenerator(claude_client=mock_client)
        product = generator.generate(valid_spec)

        assert "id" in product.manifest
        assert "name" in product.manifest
        assert "type" in product.manifest
        assert product.manifest["type"] == "html_tool"

    def test_generate_raises_without_claude_client(self, valid_spec):
        """generate should raise RuntimeError without claude_client."""
        generator = HtmlToolGenerator()

        with pytest.raises(RuntimeError, match="Claude client is required"):
            generator.generate(valid_spec)

    def test_generate_raises_for_wrong_product_type(self, mock_claude_response):
        """generate should raise ValueError for non-html_tool specs."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = HtmlToolGenerator(claude_client=mock_client)

        wrong_spec = ProductSpec(
            problem="Some problem",
            solution_name="Some Solution",
            target_audience="Someone",
            key_benefits=["Benefit"],
            product_type="automation",  # Wrong type!
        )

        with pytest.raises(ValueError, match="Invalid product type"):
            generator.generate(wrong_spec)


class TestHtmlToolGeneratorValidation:
    """Test the validate method."""

    def test_validate_catches_missing_html_file(self):
        """validate should return False if no HTML file exists."""
        generator = HtmlToolGenerator()

        product = GeneratedProduct(files={"README.md": b"# Documentation"}, manifest={})

        assert generator.validate(product) is False

    def test_validate_catches_missing_doctype(self):
        """validate should return False if DOCTYPE is missing."""
        generator = HtmlToolGenerator()

        product = GeneratedProduct(
            files={"tool.html": b"<html><head></head><body></body></html>"}, manifest={}
        )

        assert generator.validate(product) is False

    def test_validate_catches_missing_body_tag(self):
        """validate should return False if body tag is missing."""
        generator = HtmlToolGenerator()

        product = GeneratedProduct(
            files={"tool.html": b"<!DOCTYPE html><html><head></head></html>"},
            manifest={},
        )

        assert generator.validate(product) is False

    def test_validate_catches_missing_head_tag(self):
        """validate should return False if head tag is missing."""
        generator = HtmlToolGenerator()

        product = GeneratedProduct(
            files={"tool.html": b"<!DOCTYPE html><html><body></body></html>"},
            manifest={},
        )

        assert generator.validate(product) is False

    def test_validate_catches_missing_html_tag(self):
        """validate should return False if html tag is missing."""
        generator = HtmlToolGenerator()

        product = GeneratedProduct(
            files={"tool.html": b"<!DOCTYPE html><head></head><body></body>"},
            manifest={},
        )

        assert generator.validate(product) is False

    def test_validate_accepts_valid_html(self):
        """validate should return True for valid HTML structure."""
        generator = HtmlToolGenerator()

        valid_html = b"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Tool</title>
    <style>body { margin: 0; }</style>
</head>
<body>
    <h1>Test</h1>
    <script>function test() { return true; }</script>
</body>
</html>"""

        product = GeneratedProduct(files={"tool.html": valid_html}, manifest={})

        assert generator.validate(product) is True

    def test_validate_catches_unbalanced_js_braces(self):
        """validate should return False for obviously broken JavaScript."""
        generator = HtmlToolGenerator()

        broken_js_html = b"""<!DOCTYPE html>
<html>
<head></head>
<body>
    <script>
        function test() {
            if (true) {
                console.log('missing closing brace')
            // Missing }
    </script>
</body>
</html>"""

        product = GeneratedProduct(files={"tool.html": broken_js_html}, manifest={})

        assert generator.validate(product) is False


class TestHtmlToolGeneratorHelpers:
    """Test helper methods."""

    def test_sanitize_filename_basic(self):
        """_sanitize_filename should convert names to safe filenames."""
        generator = HtmlToolGenerator()

        assert generator._sanitize_filename("Profit Calculator") == "profit-calculator"
        assert generator._sanitize_filename("My Tool 2.0") == "my-tool-20"
        assert generator._sanitize_filename("  Spaced  Name  ") == "spaced-name"

    def test_sanitize_filename_special_chars(self):
        """_sanitize_filename should remove special characters."""
        generator = HtmlToolGenerator()

        assert generator._sanitize_filename("Tool@#$%Name") == "toolname"
        assert generator._sanitize_filename("A/B/C Tool") == "abc-tool"

    def test_sanitize_filename_empty(self):
        """_sanitize_filename should return 'tool' for empty names."""
        generator = HtmlToolGenerator()

        assert generator._sanitize_filename("") == "tool"
        assert generator._sanitize_filename("@#$%") == "tool"

    def test_parse_response_valid_json(self):
        """_parse_response should parse valid JSON."""
        generator = HtmlToolGenerator()

        response = json.dumps(
            {
                "title": "Test",
                "css": "body {}",
                "body_html": "<div></div>",
                "javascript": "console.log('hi')",
            }
        )

        result = generator._parse_response(response)
        assert result["title"] == "Test"
        assert result["css"] == "body {}"

    def test_parse_response_strips_markdown(self):
        """_parse_response should handle markdown code blocks."""
        generator = HtmlToolGenerator()

        response = """```json
{
    "title": "Test",
    "css": "body {}",
    "body_html": "<div></div>",
    "javascript": "console.log('hi')"
}
```"""

        result = generator._parse_response(response)
        assert result["title"] == "Test"

    def test_parse_response_missing_key(self):
        """_parse_response should raise KeyError for missing keys."""
        generator = HtmlToolGenerator()

        response = json.dumps(
            {
                "title": "Test",
                "css": "body {}",
                # Missing body_html and javascript
            }
        )

        with pytest.raises(KeyError):
            generator._parse_response(response)

    def test_generate_readme_includes_spec_info(self):
        """_generate_readme should include information from spec."""
        generator = HtmlToolGenerator()

        spec = ProductSpec(
            problem="Can't calculate profit",
            solution_name="Profit Calc",
            target_audience="Store owners",
            key_benefits=["Fast", "Easy"],
            product_type="html_tool",
        )

        readme = generator._generate_readme(spec, "profit-calc.html")

        assert "Profit Calc" in readme
        assert "Can't calculate profit" in readme
        assert "Store owners" in readme
        assert "Fast" in readme
        assert "Easy" in readme
        assert "profit-calc.html" in readme


class TestHtmlToolPrompt:
    """Test the HTML tool generation prompt."""

    def test_prompt_contains_required_sections(self):
        """HTML_TOOL_PROMPT should have all required sections."""
        assert "PROBLEM TO SOLVE" in HTML_TOOL_PROMPT
        assert "TOOL NAME" in HTML_TOOL_PROMPT
        assert "KEY BENEFITS" in HTML_TOOL_PROMPT
        assert "TARGET AUDIENCE" in HTML_TOOL_PROMPT

    def test_prompt_requests_json_output(self):
        """HTML_TOOL_PROMPT should request JSON output."""
        assert "JSON" in HTML_TOOL_PROMPT
        assert "title" in HTML_TOOL_PROMPT
        assert "css" in HTML_TOOL_PROMPT
        assert "body_html" in HTML_TOOL_PROMPT
        assert "javascript" in HTML_TOOL_PROMPT

    def test_prompt_specifies_vanilla_js(self):
        """HTML_TOOL_PROMPT should require vanilla JavaScript."""
        assert (
            "vanilla" in HTML_TOOL_PROMPT.lower()
            or "no frameworks" in HTML_TOOL_PROMPT.lower()
        )

    def test_prompt_specifies_offline_requirement(self):
        """HTML_TOOL_PROMPT should specify offline capability."""
        assert "offline" in HTML_TOOL_PROMPT.lower()
