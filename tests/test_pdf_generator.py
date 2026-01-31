"""
Tests for the PDF generator module.

Tests the FrameworkPDF class and PdfGenerator for creating professional
PDF frameworks using fpdf2.
"""

import pytest
from unittest.mock import Mock, MagicMock

from execution.generators.pdf import (
    FrameworkPDF,
    PdfGenerator,
    PDF_CONTENT_PROMPT,
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
        problem="High cart abandonment rate losing sales",
        solution_name="Cart Recovery Framework",
        target_audience="Shopify store owners",
        key_benefits=[
            "Reduce cart abandonment by 30%",
            "Automate follow-up sequences",
            "Increase conversion rates",
        ],
        product_type="pdf",
    )


@pytest.fixture
def pdf_generator():
    """Create a PdfGenerator instance without Claude client."""
    return PdfGenerator()


@pytest.fixture
def mock_claude_client():
    """Create a mock Claude client for testing."""
    client = Mock()
    client.generate.return_value = """
    {
        "title": "Cart Recovery Master Framework",
        "subtitle": "Reduce abandoned carts and boost revenue",
        "sections": [
            {
                "title": "Introduction",
                "type": "text",
                "content": "Learn how to recover abandoned carts effectively."
            },
            {
                "title": "Key Strategies",
                "type": "bullets",
                "content": ["Email sequences", "SMS reminders", "Exit intent popups"]
            }
        ]
    }
    """
    return client


# FrameworkPDF Tests
class TestFrameworkPDF:
    """Tests for the FrameworkPDF class."""

    def test_framework_pdf_can_be_instantiated(self):
        """Test that FrameworkPDF can be created."""
        pdf = FrameworkPDF(title="Test Framework")
        assert pdf is not None
        assert pdf._title == "Test Framework"

    def test_framework_pdf_default_title(self):
        """Test FrameworkPDF has default title."""
        pdf = FrameworkPDF()
        assert pdf._title == "Framework"

    def test_chapter_title_adds_content(self):
        """Test that chapter_title adds content to PDF."""
        pdf = FrameworkPDF(title="Test")
        pdf.add_page()
        initial_y = pdf.get_y()
        pdf.chapter_title("Test Chapter")
        # Y position should change after adding content
        assert pdf.get_y() > initial_y

    def test_chapter_body_adds_text(self):
        """Test that chapter_body adds text content."""
        pdf = FrameworkPDF(title="Test")
        pdf.add_page()
        initial_y = pdf.get_y()
        pdf.chapter_body("This is test content for the chapter body.")
        assert pdf.get_y() > initial_y

    def test_bullet_list_formats_items(self):
        """Test that bullet_list creates formatted list."""
        pdf = FrameworkPDF(title="Test")
        pdf.add_page()
        initial_y = pdf.get_y()
        pdf.bullet_list(["Item 1", "Item 2", "Item 3"])
        assert pdf.get_y() > initial_y

    def test_numbered_list_formats_items(self):
        """Test that numbered_list creates numbered items."""
        pdf = FrameworkPDF(title="Test")
        pdf.add_page()
        initial_y = pdf.get_y()
        pdf.numbered_list(["First step", "Second step", "Third step"])
        assert pdf.get_y() > initial_y

    def test_callout_box_tip_type(self):
        """Test callout_box with tip type."""
        pdf = FrameworkPDF(title="Test")
        pdf.add_page()
        initial_y = pdf.get_y()
        pdf.callout_box("This is a helpful tip!", "tip")
        assert pdf.get_y() > initial_y

    def test_callout_box_warning_type(self):
        """Test callout_box with warning type."""
        pdf = FrameworkPDF(title="Test")
        pdf.add_page()
        pdf.callout_box("This is a warning!", "warning")
        # Should not raise any errors

    def test_callout_box_note_type(self):
        """Test callout_box with note type."""
        pdf = FrameworkPDF(title="Test")
        pdf.add_page()
        pdf.callout_box("This is a note.", "note")
        # Should not raise any errors


# PdfGenerator Tests
class TestPdfGenerator:
    """Tests for the PdfGenerator class."""

    def test_generator_inherits_from_base_generator(self):
        """Test that PdfGenerator inherits from BaseGenerator."""
        generator = PdfGenerator()
        assert isinstance(generator, BaseGenerator)

    def test_get_product_type_returns_pdf(self):
        """Test that get_product_type returns 'pdf'."""
        generator = PdfGenerator()
        assert generator.get_product_type() == "pdf"

    def test_generate_produces_pdf_file(self, sample_spec, pdf_generator):
        """Test that generate creates a PDF file."""
        product = pdf_generator.generate(sample_spec)

        # Should have files
        assert len(product.files) > 0

        # Should have a .pdf file
        pdf_files = [f for f in product.files.keys() if f.endswith(".pdf")]
        assert len(pdf_files) == 1

    def test_generate_includes_readme(self, sample_spec, pdf_generator):
        """Test that generate creates README.md."""
        product = pdf_generator.generate(sample_spec)
        assert "README.md" in product.files

    def test_generate_pdf_starts_with_pdf_magic(self, sample_spec, pdf_generator):
        """Test that generated PDF starts with %PDF magic bytes."""
        product = pdf_generator.generate(sample_spec)

        pdf_content = None
        for filename, content in product.files.items():
            if filename.endswith(".pdf"):
                pdf_content = content
                break

        assert pdf_content is not None
        assert pdf_content.startswith(b"%PDF")

    def test_generate_creates_manifest(self, sample_spec, pdf_generator):
        """Test that generate creates proper manifest."""
        product = pdf_generator.generate(sample_spec)

        assert product.manifest is not None
        assert "id" in product.manifest
        assert "name" in product.manifest
        assert product.manifest["type"] == "pdf"

    def test_generate_with_claude_client(self, sample_spec, mock_claude_client):
        """Test generate with Claude client for content generation."""
        generator = PdfGenerator(claude_client=mock_claude_client)
        product = generator.generate(sample_spec)

        # Should have called Claude
        mock_claude_client.generate.assert_called_once()

        # Should still produce valid PDF
        pdf_files = [f for f in product.files.keys() if f.endswith(".pdf")]
        assert len(pdf_files) == 1


# Validation Tests
class TestPdfValidation:
    """Tests for PDF validation logic."""

    def test_validate_catches_missing_pdf(self, pdf_generator):
        """Test that validate returns False when PDF is missing."""
        product = GeneratedProduct(
            files={"README.md": b"# Test"},
            manifest={"type": "pdf"},
        )
        assert pdf_generator.validate(product) is False

    def test_validate_catches_empty_pdf(self, pdf_generator):
        """Test that validate returns False for empty PDF."""
        product = GeneratedProduct(
            files={"test.pdf": b"%PDF-tiny"},  # Less than 1KB
            manifest={"type": "pdf"},
        )
        assert pdf_generator.validate(product) is False

    def test_validate_catches_non_pdf_content(self, pdf_generator):
        """Test that validate returns False for non-PDF content."""
        product = GeneratedProduct(
            files={"test.pdf": b"This is not a PDF file" * 100},
            manifest={"type": "pdf"},
        )
        assert pdf_generator.validate(product) is False

    def test_validate_accepts_valid_pdf(self, sample_spec, pdf_generator):
        """Test that validate returns True for valid PDF."""
        product = pdf_generator.generate(sample_spec)
        assert pdf_generator.validate(product) is True


# Content Structure Tests
class TestContentStructure:
    """Tests for content structure generation."""

    def test_default_content_structure_has_title(self, sample_spec, pdf_generator):
        """Test default content structure includes title."""
        content = pdf_generator._default_content_structure(sample_spec)
        assert "title" in content
        assert content["title"] == sample_spec.solution_name

    def test_default_content_structure_has_sections(self, sample_spec, pdf_generator):
        """Test default content structure includes sections."""
        content = pdf_generator._default_content_structure(sample_spec)
        assert "sections" in content
        assert len(content["sections"]) > 0

    def test_default_content_includes_benefits(self, sample_spec, pdf_generator):
        """Test default content includes key benefits."""
        content = pdf_generator._default_content_structure(sample_spec)

        # Find bullets section with benefits
        benefits_section = None
        for section in content["sections"]:
            if section.get("type") == "bullets":
                benefits_section = section
                break

        assert benefits_section is not None
        assert benefits_section["content"] == sample_spec.key_benefits


# Filename Sanitization Tests
class TestFilenameSanitization:
    """Tests for filename sanitization."""

    def test_sanitize_filename_lowercase(self, pdf_generator):
        """Test that filename is lowercased."""
        result = pdf_generator._sanitize_filename("My FRAMEWORK")
        assert result == "my_framework"

    def test_sanitize_filename_replaces_spaces(self, pdf_generator):
        """Test that spaces are replaced with underscores."""
        result = pdf_generator._sanitize_filename("cart recovery guide")
        assert result == "cart_recovery_guide"

    def test_sanitize_filename_removes_special_chars(self, pdf_generator):
        """Test that special characters are removed."""
        result = pdf_generator._sanitize_filename("test!@#$%file")
        assert result == "testfile"

    def test_sanitize_filename_handles_empty(self, pdf_generator):
        """Test that empty name returns default."""
        result = pdf_generator._sanitize_filename("")
        assert result == "framework"


# PDF Content Prompt Tests
class TestPdfContentPrompt:
    """Tests for the PDF content prompt template."""

    def test_prompt_contains_placeholders(self):
        """Test that prompt has required placeholders."""
        assert "{problem}" in PDF_CONTENT_PROMPT
        assert "{solution_name}" in PDF_CONTENT_PROMPT
        assert "{target_audience}" in PDF_CONTENT_PROMPT
        assert "{key_benefits}" in PDF_CONTENT_PROMPT

    def test_prompt_describes_json_structure(self):
        """Test that prompt describes expected JSON structure."""
        assert "title" in PDF_CONTENT_PROMPT
        assert "subtitle" in PDF_CONTENT_PROMPT
        assert "sections" in PDF_CONTENT_PROMPT
        assert "type" in PDF_CONTENT_PROMPT
