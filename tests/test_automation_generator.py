"""
Tests for the Automation Generator.
"""

import json
from unittest.mock import MagicMock

import pytest

from execution.generators import BaseGenerator, GeneratedProduct, ProductSpec
from execution.generators.automation import AutomationGenerator, AUTOMATION_PROMPT


class TestAutomationGeneratorBasics:
    """Test basic generator setup and inheritance."""

    def test_inherits_from_base_generator(self):
        """Automation generator should inherit from BaseGenerator."""
        generator = AutomationGenerator()
        assert isinstance(generator, BaseGenerator)

    def test_get_product_type_returns_automation(self):
        """get_product_type should return 'automation'."""
        generator = AutomationGenerator()
        assert generator.get_product_type() == "automation"

    def test_init_with_claude_client(self):
        """Should accept optional claude_client."""
        mock_client = MagicMock()
        generator = AutomationGenerator(claude_client=mock_client)
        assert generator.claude_client is mock_client


class TestAutomationGeneratorGeneration:
    """Test the generate method."""

    @pytest.fixture
    def valid_spec(self):
        """Create a valid ProductSpec for testing."""
        return ProductSpec(
            problem="E-commerce owners waste hours manually updating inventory across channels",
            solution_name="Inventory Sync Tool",
            target_audience="Shopify store owners selling on multiple platforms",
            key_benefits=[
                "Sync inventory in seconds",
                "Prevent overselling",
                "Works with Shopify, Amazon, eBay",
            ],
            product_type="automation",
        )

    @pytest.fixture
    def mock_claude_response(self):
        """Valid Claude response for automation generation."""
        script_code = '''"""
Inventory Sync Tool - Synchronize inventory across multiple e-commerce platforms.

This script helps e-commerce store owners keep their inventory synchronized
across Shopify, Amazon, and eBay to prevent overselling.
"""

import argparse
import sys


def sync_inventory(platform: str, dry_run: bool = False) -> bool:
    """
    Synchronize inventory for the specified platform.
    
    Args:
        platform: The platform to sync (shopify, amazon, ebay)
        dry_run: If True, only simulate the sync
        
    Returns:
        True if sync was successful, False otherwise
    """
    try:
        print(f"Syncing inventory for {platform}...")
        if dry_run:
            print("(Dry run mode - no changes made)")
        return True
    except Exception as e:
        print(f"Error syncing {platform}: {e}")
        return False


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Sync inventory across platforms")
    parser.add_argument("--platform", choices=["shopify", "amazon", "ebay", "all"],
                        default="all", help="Platform to sync")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate sync without making changes")
    
    args = parser.parse_args()
    
    success = sync_inventory(args.platform, args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
'''
        return json.dumps(
            {
                "script_code": script_code,
                "requirements": ["requests", "python-dotenv"],
                "usage_instructions": "Run `python inventory_sync_tool.py --platform shopify` to sync Shopify inventory.",
            }
        )

    def test_generate_produces_py_file(self, valid_spec, mock_claude_response):
        """generate should produce a .py file in the output."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = AutomationGenerator(claude_client=mock_client)
        product = generator.generate(valid_spec)

        py_files = [f for f in product.files.keys() if f.endswith(".py")]
        assert len(py_files) == 1

    def test_generate_produces_requirements_txt(self, valid_spec, mock_claude_response):
        """generate should produce requirements.txt."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = AutomationGenerator(claude_client=mock_client)
        product = generator.generate(valid_spec)

        assert "requirements.txt" in product.files

    def test_generate_produces_readme(self, valid_spec, mock_claude_response):
        """generate should produce README.md."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = AutomationGenerator(claude_client=mock_client)
        product = generator.generate(valid_spec)

        assert "README.md" in product.files

    def test_generate_returns_generated_product(self, valid_spec, mock_claude_response):
        """generate should return a GeneratedProduct instance."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = AutomationGenerator(claude_client=mock_client)
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

        generator = AutomationGenerator(claude_client=mock_client)
        product = generator.generate(valid_spec)

        assert "id" in product.manifest
        assert "name" in product.manifest
        assert "type" in product.manifest
        assert product.manifest["type"] == "automation"

    def test_generate_raises_without_claude_client(self, valid_spec):
        """generate should raise RuntimeError without claude_client."""
        generator = AutomationGenerator()

        with pytest.raises(RuntimeError, match="Claude client is required"):
            generator.generate(valid_spec)

    def test_generate_raises_for_wrong_product_type(self, mock_claude_response):
        """generate should raise ValueError for non-automation specs."""
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_claude_response

        generator = AutomationGenerator(claude_client=mock_client)

        wrong_spec = ProductSpec(
            problem="Some problem",
            solution_name="Some Solution",
            target_audience="Someone",
            key_benefits=["Benefit"],
            product_type="html_tool",  # Wrong type!
        )

        with pytest.raises(ValueError, match="Invalid product type"):
            generator.generate(wrong_spec)


class TestAutomationGeneratorValidation:
    """Test the validate method."""

    @pytest.fixture
    def valid_script(self):
        """A valid Python script with all required elements."""
        return b'''"""
A valid automation script.
"""

import argparse


def main():
    """Main function."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    print("Hello!")


if __name__ == "__main__":
    main()
'''

    def test_validate_catches_missing_py_file(self):
        """validate should return False if no .py file exists."""
        generator = AutomationGenerator()

        product = GeneratedProduct(
            files={"requirements.txt": b"requests\n", "README.md": b"# Documentation"},
            manifest={},
        )

        assert generator.validate(product) is False

    def test_validate_catches_missing_requirements_txt(self, valid_script):
        """validate should return False if requirements.txt is missing."""
        generator = AutomationGenerator()

        product = GeneratedProduct(
            files={"script.py": valid_script, "README.md": b"# Documentation"},
            manifest={},
        )

        assert generator.validate(product) is False

    def test_validate_catches_missing_docstring(self):
        """validate should return False if script has no docstring."""
        generator = AutomationGenerator()

        no_docstring_script = b"""import argparse

def main():
    pass

if __name__ == "__main__":
    main()
"""

        product = GeneratedProduct(
            files={"script.py": no_docstring_script, "requirements.txt": b"requests\n"},
            manifest={},
        )

        assert generator.validate(product) is False

    def test_validate_catches_missing_main_block(self):
        """validate should return False if __main__ block is missing."""
        generator = AutomationGenerator()

        no_main_script = b'''"""
A script without main block.
"""

def main():
    pass
'''

        product = GeneratedProduct(
            files={"script.py": no_main_script, "requirements.txt": b"requests\n"},
            manifest={},
        )

        assert generator.validate(product) is False

    def test_validate_catches_syntax_errors(self):
        """validate should return False for syntax errors."""
        generator = AutomationGenerator()

        syntax_error_script = b'''"""
A script with syntax errors.
"""

def main():
    print("missing closing paren"


if __name__ == "__main__":
    main()
'''

        product = GeneratedProduct(
            files={"script.py": syntax_error_script, "requirements.txt": b"requests\n"},
            manifest={},
        )

        assert generator.validate(product) is False

    def test_validate_accepts_valid_script(self, valid_script):
        """validate should return True for valid scripts."""
        generator = AutomationGenerator()

        product = GeneratedProduct(
            files={"script.py": valid_script, "requirements.txt": b"requests\n"},
            manifest={},
        )

        assert generator.validate(product) is True

    def test_validate_accepts_empty_requirements(self, valid_script):
        """validate should accept scripts with no external dependencies."""
        generator = AutomationGenerator()

        product = GeneratedProduct(
            files={
                "script.py": valid_script,
                "requirements.txt": b"# No external dependencies required\n",
            },
            manifest={},
        )

        assert generator.validate(product) is True

    def test_validate_accepts_single_quote_main_block(self):
        """validate should accept __main__ with single quotes."""
        generator = AutomationGenerator()

        single_quote_script = b"""'''
A valid script with single quotes.
'''

def main():
    pass

if __name__ == '__main__':
    main()
"""

        product = GeneratedProduct(
            files={"script.py": single_quote_script, "requirements.txt": b"requests\n"},
            manifest={},
        )

        assert generator.validate(product) is True


class TestAutomationGeneratorHelpers:
    """Test helper methods."""

    def test_sanitize_filename_basic(self):
        """_sanitize_filename should convert names to safe Python filenames."""
        generator = AutomationGenerator()

        assert (
            generator._sanitize_filename("Inventory Sync Tool") == "inventory_sync_tool"
        )
        assert generator._sanitize_filename("My Tool 2.0") == "my_tool_20"
        assert generator._sanitize_filename("  Spaced  Name  ") == "spaced_name"

    def test_sanitize_filename_special_chars(self):
        """_sanitize_filename should remove special characters."""
        generator = AutomationGenerator()

        assert generator._sanitize_filename("Tool@#$%Name") == "toolname"
        assert generator._sanitize_filename("A/B/C Tool") == "abc_tool"

    def test_sanitize_filename_starts_with_number(self):
        """_sanitize_filename should handle names starting with numbers."""
        generator = AutomationGenerator()

        assert (
            generator._sanitize_filename("3D Printer Tool") == "script_3d_printer_tool"
        )
        assert generator._sanitize_filename("123 Tool") == "script_123_tool"

    def test_sanitize_filename_empty(self):
        """_sanitize_filename should return 'automation' for empty names."""
        generator = AutomationGenerator()

        assert generator._sanitize_filename("") == "automation"
        assert generator._sanitize_filename("@#$%") == "automation"

    def test_generate_requirements_txt_with_deps(self):
        """_generate_requirements_txt should format dependencies correctly."""
        generator = AutomationGenerator()

        result = generator._generate_requirements_txt(
            ["requests", "python-dotenv", "pandas"]
        )

        assert "pandas" in result
        assert "python-dotenv" in result
        assert "requests" in result
        # Should be sorted
        assert result.index("pandas") < result.index("python-dotenv")

    def test_generate_requirements_txt_empty(self):
        """_generate_requirements_txt should handle empty list."""
        generator = AutomationGenerator()

        result = generator._generate_requirements_txt([])

        assert "No external dependencies" in result

    def test_generate_requirements_txt_deduplicates(self):
        """_generate_requirements_txt should remove duplicates."""
        generator = AutomationGenerator()

        result = generator._generate_requirements_txt(
            ["requests", "requests", "pandas"]
        )

        # Count occurrences
        assert result.count("requests") == 1

    def test_parse_response_valid_json(self):
        """_parse_response should parse valid JSON."""
        generator = AutomationGenerator()

        response = json.dumps(
            {
                "script_code": "print('hello')",
                "requirements": ["requests"],
                "usage_instructions": "Run the script",
            }
        )

        result = generator._parse_response(response)
        assert result["script_code"] == "print('hello')"
        assert result["requirements"] == ["requests"]

    def test_parse_response_handles_missing_optional_fields(self):
        """_parse_response should handle missing optional fields."""
        generator = AutomationGenerator()

        response = json.dumps(
            {
                "script_code": "print('hello')"
                # requirements and usage_instructions missing
            }
        )

        result = generator._parse_response(response)
        assert result["script_code"] == "print('hello')"
        assert result["requirements"] == []
        assert result["usage_instructions"] == ""

    def test_parse_response_strips_markdown(self):
        """_parse_response should handle markdown code blocks."""
        generator = AutomationGenerator()

        response = """```json
{
    "script_code": "print('hello')",
    "requirements": [],
    "usage_instructions": "Run it"
}
```"""

        result = generator._parse_response(response)
        assert result["script_code"] == "print('hello')"

    def test_has_docstring_detects_docstring(self):
        """_has_docstring should detect module docstrings."""
        generator = AutomationGenerator()

        with_docstring = '"""This is a docstring."""\nimport sys'
        without_docstring = 'import sys\nprint("hello")'

        assert generator._has_docstring(with_docstring) is True
        assert generator._has_docstring(without_docstring) is False

    def test_has_docstring_handles_single_quotes(self):
        """_has_docstring should detect single-quote docstrings."""
        generator = AutomationGenerator()

        single_quote_docstring = "'''Single quote docstring.'''\nimport sys"

        assert generator._has_docstring(single_quote_docstring) is True

    def test_generate_readme_includes_spec_info(self):
        """_generate_readme should include information from spec."""
        generator = AutomationGenerator()

        spec = ProductSpec(
            problem="Manual inventory updates",
            solution_name="Inventory Sync",
            target_audience="Store owners",
            key_benefits=["Fast", "Easy"],
            product_type="automation",
        )

        readme = generator._generate_readme(spec, "inventory_sync.py", "Run the script")

        assert "Inventory Sync" in readme
        assert "Manual inventory updates" in readme
        assert "Store owners" in readme
        assert "Fast" in readme
        assert "Easy" in readme
        assert "inventory_sync.py" in readme
        assert "requirements.txt" in readme


class TestAutomationPrompt:
    """Test the automation generation prompt."""

    def test_prompt_contains_required_sections(self):
        """AUTOMATION_PROMPT should have all required sections."""
        assert "PROBLEM TO SOLVE" in AUTOMATION_PROMPT
        assert "SCRIPT NAME" in AUTOMATION_PROMPT
        assert "KEY BENEFITS" in AUTOMATION_PROMPT
        assert "TARGET AUDIENCE" in AUTOMATION_PROMPT

    def test_prompt_requests_json_output(self):
        """AUTOMATION_PROMPT should request JSON output."""
        assert "JSON" in AUTOMATION_PROMPT
        assert "script_code" in AUTOMATION_PROMPT
        assert "requirements" in AUTOMATION_PROMPT
        assert "usage_instructions" in AUTOMATION_PROMPT

    def test_prompt_specifies_argparse(self):
        """AUTOMATION_PROMPT should require argparse CLI."""
        assert "argparse" in AUTOMATION_PROMPT

    def test_prompt_specifies_error_handling(self):
        """AUTOMATION_PROMPT should require error handling."""
        assert (
            "try" in AUTOMATION_PROMPT.lower()
            or "error handling" in AUTOMATION_PROMPT.lower()
        )

    def test_prompt_specifies_docstrings(self):
        """AUTOMATION_PROMPT should require docstrings."""
        assert "docstring" in AUTOMATION_PROMPT.lower()
