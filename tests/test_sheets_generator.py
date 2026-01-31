"""
Tests for the Google Sheets generator module.

Tests the SheetsGenerator for creating Google Sheets templates
with offline fallback support.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch

from execution.generators.sheets import (
    SheetsGenerator,
    SCOPES,
    SHEETS_CONTENT_PROMPT,
)
from execution.generators.base_generator import (
    BaseGenerator,
    ProductSpec,
    GeneratedProduct,
)


# Test fixtures
@pytest.fixture
def sample_spec():
    """Create a sample ProductSpec for testing."""
    return ProductSpec(
        problem="Tracking inventory levels is manual and error-prone",
        solution_name="Inventory Tracker Pro",
        target_audience="Small e-commerce businesses",
        key_benefits=[
            "Real-time stock visibility",
            "Automatic reorder alerts",
            "Cost tracking and analytics",
        ],
        product_type="sheets",
    )


@pytest.fixture
def sheets_generator():
    """Create a SheetsGenerator instance without credentials."""
    return SheetsGenerator()


@pytest.fixture
def mock_claude_client():
    """Create a mock Claude client for testing."""
    client = Mock()
    client.generate.return_value = """
    {
        "title": "Inventory Tracker Pro",
        "worksheets": [
            {
                "name": "Inventory",
                "headers": ["SKU", "Product Name", "Quantity", "Reorder Point"],
                "formulas": {
                    "E2": "=IF(C2<D2, \\"REORDER\\", \\"OK\\")"
                },
                "sample_data": [
                    ["SKU-001", "Widget A", 50, 25],
                    ["SKU-002", "Widget B", 10, 20]
                ],
                "notes": "Track inventory levels"
            }
        ]
    }
    """
    return client


# SheetsGenerator Tests
class TestSheetsGenerator:
    """Tests for the SheetsGenerator class."""

    def test_generator_inherits_from_base_generator(self):
        """Test that SheetsGenerator inherits from BaseGenerator."""
        generator = SheetsGenerator()
        assert isinstance(generator, BaseGenerator)

    def test_get_product_type_returns_sheets(self):
        """Test that get_product_type returns 'sheets'."""
        generator = SheetsGenerator()
        assert generator.get_product_type() == "sheets"

    def test_generate_works_in_offline_mode(self, sample_spec, sheets_generator):
        """Test that generate works without credentials."""
        product = sheets_generator.generate(sample_spec)

        # Should produce files
        assert len(product.files) > 0

        # Should have mode set to offline
        assert product.manifest.get("mode") == "offline"

    def test_generate_produces_sheet_definition_json(
        self, sample_spec, sheets_generator
    ):
        """Test that generate creates sheet_definition.json."""
        product = sheets_generator.generate(sample_spec)
        assert "sheet_definition.json" in product.files

    def test_generate_produces_readme(self, sample_spec, sheets_generator):
        """Test that generate creates README.md."""
        product = sheets_generator.generate(sample_spec)
        assert "README.md" in product.files

    def test_generate_produces_manual_setup(self, sample_spec, sheets_generator):
        """Test that generate creates MANUAL_SETUP.md."""
        product = sheets_generator.generate(sample_spec)
        assert "MANUAL_SETUP.md" in product.files

    def test_sheet_definition_is_valid_json(self, sample_spec, sheets_generator):
        """Test that sheet_definition.json is valid JSON."""
        product = sheets_generator.generate(sample_spec)

        definition_bytes = product.files["sheet_definition.json"]
        definition = json.loads(definition_bytes.decode("utf-8"))

        assert "title" in definition
        assert "worksheets" in definition

    def test_generate_creates_manifest(self, sample_spec, sheets_generator):
        """Test that generate creates proper manifest."""
        product = sheets_generator.generate(sample_spec)

        assert product.manifest is not None
        assert "id" in product.manifest
        assert product.manifest["type"] == "sheets"


# Validation Tests
class TestSheetsValidation:
    """Tests for Sheets validation logic."""

    def test_validate_catches_missing_definition(self, sheets_generator):
        """Test that validate returns False when definition is missing."""
        product = GeneratedProduct(
            files={"README.md": b"# Test"},
            manifest={"type": "sheets"},
        )
        assert sheets_generator.validate(product) is False

    def test_validate_catches_invalid_json(self, sheets_generator):
        """Test that validate returns False for invalid JSON."""
        product = GeneratedProduct(
            files={"sheet_definition.json": b"not valid json"},
            manifest={"type": "sheets"},
        )
        assert sheets_generator.validate(product) is False

    def test_validate_catches_missing_worksheets(self, sheets_generator):
        """Test that validate returns False when no worksheets."""
        definition = {"title": "Test", "worksheets": []}
        product = GeneratedProduct(
            files={"sheet_definition.json": json.dumps(definition).encode()},
            manifest={"type": "sheets"},
        )
        assert sheets_generator.validate(product) is False

    def test_validate_catches_missing_headers(self, sheets_generator):
        """Test that validate returns False when worksheet has no headers."""
        definition = {
            "title": "Test",
            "worksheets": [{"name": "Sheet1", "headers": []}],
        }
        product = GeneratedProduct(
            files={"sheet_definition.json": json.dumps(definition).encode()},
            manifest={"type": "sheets"},
        )
        assert sheets_generator.validate(product) is False

    def test_validate_accepts_valid_definition(self, sample_spec, sheets_generator):
        """Test that validate returns True for valid definition."""
        product = sheets_generator.generate(sample_spec)
        assert sheets_generator.validate(product) is True


# Manual Instructions Tests
class TestManualInstructions:
    """Tests for manual setup instruction generation."""

    def test_manual_instructions_include_title(self, sample_spec, sheets_generator):
        """Test that manual instructions include sheet title."""
        product = sheets_generator.generate(sample_spec)

        instructions = product.files["MANUAL_SETUP.md"].decode("utf-8")
        assert sample_spec.solution_name in instructions

    def test_manual_instructions_include_worksheets(
        self, sample_spec, sheets_generator
    ):
        """Test that manual instructions include worksheet names."""
        product = sheets_generator.generate(sample_spec)

        instructions = product.files["MANUAL_SETUP.md"].decode("utf-8")
        # Default structure has Dashboard and Data Entry
        assert "Dashboard" in instructions

    def test_manual_instructions_include_headers(self, sample_spec, sheets_generator):
        """Test that manual instructions include column headers."""
        product = sheets_generator.generate(sample_spec)

        instructions = product.files["MANUAL_SETUP.md"].decode("utf-8")
        assert "Headers" in instructions


# SCOPES Tests
class TestScopes:
    """Tests for Google API scopes."""

    def test_scopes_include_spreadsheets(self):
        """Test that SCOPES include spreadsheets permission."""
        assert any("spreadsheets" in scope for scope in SCOPES)

    def test_scopes_include_drive(self):
        """Test that SCOPES include drive permission."""
        assert any("drive" in scope for scope in SCOPES)

    def test_scopes_is_list(self):
        """Test that SCOPES is a list."""
        assert isinstance(SCOPES, list)


# Content Prompt Tests
class TestSheetsContentPrompt:
    """Tests for the Sheets content prompt template."""

    def test_prompt_contains_placeholders(self):
        """Test that prompt has required placeholders."""
        assert "{problem}" in SHEETS_CONTENT_PROMPT
        assert "{solution_name}" in SHEETS_CONTENT_PROMPT
        assert "{target_audience}" in SHEETS_CONTENT_PROMPT
        assert "{key_benefits}" in SHEETS_CONTENT_PROMPT

    def test_prompt_describes_json_structure(self):
        """Test that prompt describes expected JSON structure."""
        assert "title" in SHEETS_CONTENT_PROMPT
        assert "worksheets" in SHEETS_CONTENT_PROMPT
        assert "headers" in SHEETS_CONTENT_PROMPT
        assert "formulas" in SHEETS_CONTENT_PROMPT


# Default Structure Tests
class TestDefaultStructure:
    """Tests for default sheet structure."""

    def test_default_structure_has_title(self, sample_spec, sheets_generator):
        """Test default structure has title from spec."""
        structure = sheets_generator._default_sheet_structure(sample_spec)
        assert structure["title"] == sample_spec.solution_name

    def test_default_structure_has_worksheets(self, sample_spec, sheets_generator):
        """Test default structure has worksheets."""
        structure = sheets_generator._default_sheet_structure(sample_spec)
        assert len(structure["worksheets"]) > 0

    def test_default_worksheets_have_headers(self, sample_spec, sheets_generator):
        """Test default worksheets have headers."""
        structure = sheets_generator._default_sheet_structure(sample_spec)
        for ws in structure["worksheets"]:
            assert "headers" in ws
            assert len(ws["headers"]) > 0


# Claude Integration Tests
class TestClaudeIntegration:
    """Tests for Claude client integration."""

    def test_generate_with_claude_client(self, sample_spec, mock_claude_client):
        """Test generate with Claude client for content generation."""
        generator = SheetsGenerator(claude_client=mock_claude_client)
        product = generator.generate(sample_spec)

        # Should have called Claude
        mock_claude_client.generate.assert_called_once()

        # Should still produce valid definition
        assert "sheet_definition.json" in product.files

    def test_falls_back_on_claude_error(self, sample_spec):
        """Test that generation falls back to default on Claude error."""
        # Create a client that raises an error
        client = Mock()
        client.generate.side_effect = Exception("API Error")

        generator = SheetsGenerator(claude_client=client)
        product = generator.generate(sample_spec)

        # Should still produce valid output
        assert "sheet_definition.json" in product.files
        assert generator.validate(product) is True


# Credential Handling Tests
class TestCredentialHandling:
    """Tests for credential handling."""

    def test_get_client_returns_none_without_credentials(self, sheets_generator):
        """Test that _get_client returns None without credentials file."""
        client = sheets_generator._get_client()
        assert client is None

    def test_credentials_path_from_init(self):
        """Test that credentials path can be set via init."""
        generator = SheetsGenerator(credentials_path="/custom/path.json")
        assert generator.credentials_path == "/custom/path.json"

    @patch.dict("os.environ", {"GOOGLE_SERVICE_ACCOUNT_JSON": "/env/path.json"})
    def test_credentials_path_from_env(self):
        """Test that credentials path can come from environment."""
        generator = SheetsGenerator()
        assert generator.credentials_path == "/env/path.json"

    def test_default_credentials_path(self):
        """Test default credentials path."""
        with patch.dict("os.environ", {}, clear=True):
            generator = SheetsGenerator()
            assert generator.credentials_path == "service_account.json"


# Online Mode Tests (with mocked gspread)
class TestOnlineMode:
    """Tests for online mode with gspread mocked."""

    @patch("execution.generators.sheets.GSPREAD_AVAILABLE", True)
    @patch("execution.generators.sheets.gspread")
    @patch("execution.generators.sheets.Credentials")
    @patch("os.path.exists")
    def test_online_mode_creates_sheet(
        self, mock_exists, mock_creds, mock_gspread, sample_spec
    ):
        """Test that online mode creates actual Google Sheet."""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds.from_service_account_file.return_value = Mock()

        mock_spreadsheet = Mock()
        mock_spreadsheet.url = "https://docs.google.com/spreadsheets/d/test123"
        mock_spreadsheet.sheet1 = Mock()

        mock_client = Mock()
        mock_client.create.return_value = mock_spreadsheet
        mock_gspread.authorize.return_value = mock_client

        # Generate
        generator = SheetsGenerator(credentials_path="test_creds.json")
        product = generator.generate(sample_spec)

        # Should have URL in manifest
        assert product.manifest.get("mode") == "online"
        assert product.manifest.get("sheet_url") == mock_spreadsheet.url
