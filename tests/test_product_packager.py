"""
Tests for the product packager module.
"""

import json
import os
import tempfile
import zipfile
import pytest
from unittest.mock import Mock, patch, MagicMock

from execution.product_packager import (
    ProductPackager,
    package_product,
    GENERATOR_MAP,
)
from execution.generators.base_generator import ProductSpec, GeneratedProduct


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
def mock_generated_product():
    """Create a mock GeneratedProduct."""
    return GeneratedProduct(
        files={
            "tool.html": b"<!DOCTYPE html><html><head></head><body></body></html>",
            "README.md": b"# Product README",
        },
        manifest={
            "id": "test-123",
            "name": "Test Product",
            "type": "html_tool",
        },
    )


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestProductPackagerInit:
    """Tests for ProductPackager initialization."""

    def test_can_instantiate(self):
        """Test that ProductPackager can be instantiated."""
        packager = ProductPackager()
        assert packager is not None

    def test_instantiate_with_claude_client(self):
        """Test instantiation with a Claude client."""
        mock_client = Mock()
        packager = ProductPackager(claude_client=mock_client)
        assert packager.claude_client == mock_client

    def test_instantiate_with_custom_output_dir(self, temp_output_dir):
        """Test instantiation with custom output directory."""
        packager = ProductPackager(output_dir=temp_output_dir)
        assert packager.output_dir == temp_output_dir

    def test_generators_initialized(self):
        """Test that all generators are initialized."""
        packager = ProductPackager()
        assert len(packager._generators) == len(GENERATOR_MAP)


class TestGeneratorMap:
    """Tests for GENERATOR_MAP constant."""

    def test_generator_map_has_all_product_types(self):
        """Test that GENERATOR_MAP has all expected product types."""
        expected_types = [
            "html_tool",
            "automation",
            "gpt_config",
            "sheets",
            "pdf",
            "prompt_pack",
        ]
        for product_type in expected_types:
            assert product_type in GENERATOR_MAP

    def test_generator_map_values_are_classes(self):
        """Test that GENERATOR_MAP values are generator classes."""
        for product_type, generator_class in GENERATOR_MAP.items():
            # Should be a class (callable)
            assert callable(generator_class)
            # Should have generate method
            assert hasattr(generator_class, "generate")


class TestProductPackagerPackage:
    """Tests for the package method."""

    def test_package_selects_correct_generator(
        self, sample_spec, mock_generated_product, temp_output_dir
    ):
        """Test that package selects the correct generator."""
        # Mock the html_tool generator
        mock_generator = Mock()
        mock_generator.generate.return_value = mock_generated_product

        packager = ProductPackager(output_dir=temp_output_dir)
        packager._generators["html_tool"] = mock_generator

        result = packager.package(sample_spec)

        # Verify correct generator was called
        mock_generator.generate.assert_called_once_with(sample_spec)

    def test_package_creates_output_directory(
        self, sample_spec, mock_generated_product, temp_output_dir
    ):
        """Test that package creates the output directory."""
        mock_generator = Mock()
        mock_generator.generate.return_value = mock_generated_product

        packager = ProductPackager(output_dir=temp_output_dir)
        packager._generators["html_tool"] = mock_generator

        result = packager.package(sample_spec)

        # Verify directory was created
        assert os.path.exists(result["path"])
        assert os.path.isdir(result["path"])

    def test_manifest_includes_all_required_fields(
        self, sample_spec, mock_generated_product, temp_output_dir
    ):
        """Test that manifest includes all required fields."""
        mock_generator = Mock()
        mock_generator.generate.return_value = mock_generated_product

        packager = ProductPackager(output_dir=temp_output_dir)
        packager._generators["html_tool"] = mock_generator

        result = packager.package(sample_spec)
        manifest = result["manifest"]

        # Check required fields
        assert "id" in manifest
        assert "name" in manifest
        assert "type" in manifest
        assert "created_at" in manifest
        assert "problem" in manifest
        assert "audience" in manifest
        assert "benefits" in manifest
        assert "deliverables" in manifest
        assert "pricing" in manifest
        assert "sales_copy" in manifest

    def test_sales_copy_is_included_in_package(
        self, sample_spec, mock_generated_product, temp_output_dir
    ):
        """Test that sales copy is included in the package."""
        mock_generator = Mock()
        mock_generator.generate.return_value = mock_generated_product

        packager = ProductPackager(output_dir=temp_output_dir)
        packager._generators["html_tool"] = mock_generator

        result = packager.package(sample_spec)

        # Check sales copy file exists
        sales_copy_path = os.path.join(result["path"], "SALES_COPY.md")
        assert os.path.exists(sales_copy_path)

        # Check it has content
        with open(sales_copy_path, "r") as f:
            content = f.read()
        assert len(content) > 0
        assert "# " in content  # Has heading

    def test_pricing_is_included_in_manifest(
        self, sample_spec, mock_generated_product, temp_output_dir
    ):
        """Test that pricing is included in the manifest."""
        mock_generator = Mock()
        mock_generator.generate.return_value = mock_generated_product

        packager = ProductPackager(output_dir=temp_output_dir)
        packager._generators["html_tool"] = mock_generator

        result = packager.package(sample_spec)
        pricing = result["manifest"]["pricing"]

        # Check pricing fields
        assert "price_cents" in pricing
        assert "price_display" in pricing
        assert "perceived_value" in pricing
        assert "justification" in pricing

    def test_zip_file_is_created(
        self, sample_spec, mock_generated_product, temp_output_dir
    ):
        """Test that a zip file is created."""
        mock_generator = Mock()
        mock_generator.generate.return_value = mock_generated_product

        packager = ProductPackager(output_dir=temp_output_dir)
        packager._generators["html_tool"] = mock_generator

        result = packager.package(sample_spec)

        # Check zip file exists
        assert os.path.exists(result["zip_path"])
        assert result["zip_path"].endswith(".zip")

        # Check it's a valid zip
        with zipfile.ZipFile(result["zip_path"], "r") as zf:
            names = zf.namelist()
            assert len(names) > 0

    def test_package_unknown_type_raises_error(self, temp_output_dir):
        """Test that unknown product type raises ValueError."""
        packager = ProductPackager(output_dir=temp_output_dir)

        bad_spec = ProductSpec(
            problem="Test problem",
            solution_name="Test Solution",
            target_audience="Test audience",
            key_benefits=["Benefit 1"],
            product_type="invalid_type",
        )

        with pytest.raises(ValueError) as exc_info:
            packager.package(bad_spec)

        assert "Unknown product type" in str(exc_info.value)


class TestProductPackagerHelpers:
    """Tests for helper methods."""

    def test_get_supported_types(self):
        """Test get_supported_types returns all types."""
        packager = ProductPackager()
        types = packager.get_supported_types()

        assert isinstance(types, list)
        assert "html_tool" in types
        assert "automation" in types
        assert len(types) == 6

    def test_get_file_type_html(self):
        """Test file type detection for HTML files."""
        packager = ProductPackager()
        assert packager._get_file_type("tool.html") == "html"
        assert packager._get_file_type("page.htm") == "html"

    def test_get_file_type_json(self):
        """Test file type detection for JSON files."""
        packager = ProductPackager()
        assert packager._get_file_type("config.json") == "json"

    def test_get_file_type_unknown(self):
        """Test file type detection for unknown extensions."""
        packager = ProductPackager()
        assert packager._get_file_type("file.xyz") == "unknown"


class TestPackageProductFunction:
    """Tests for the convenience function."""

    def test_convenience_function_works(self, sample_spec):
        """Test that package_product convenience function works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the generator
            with patch.object(ProductPackager, "package") as mock_package:
                mock_package.return_value = {
                    "product_id": "test-123",
                    "path": tmpdir,
                    "manifest": {},
                    "url": None,
                    "zip_path": os.path.join(tmpdir, "test.zip"),
                }

                result = package_product(sample_spec, output_dir=tmpdir)

                assert "product_id" in result
                assert "path" in result
                assert "manifest" in result

    def test_convenience_function_uses_default_output_dir(self, sample_spec):
        """Test that convenience function uses default output dir."""
        with patch.object(ProductPackager, "__init__", return_value=None):
            with patch.object(ProductPackager, "package") as mock_package:
                mock_package.return_value = {
                    "product_id": "test",
                    "path": "",
                    "manifest": {},
                    "url": None,
                    "zip_path": "",
                }

                # Don't specify output_dir
                result = package_product(sample_spec)

                # Verify it works
                assert result is not None


class TestProductPackagerIntegration:
    """Integration tests with mock generators."""

    def test_full_package_flow(
        self, sample_spec, mock_generated_product, temp_output_dir
    ):
        """Test the full packaging flow."""
        mock_generator = Mock()
        mock_generator.generate.return_value = mock_generated_product

        packager = ProductPackager(output_dir=temp_output_dir)
        packager._generators["html_tool"] = mock_generator

        result = packager.package(sample_spec)

        # Verify all expected outputs
        assert result["product_id"] is not None
        assert os.path.exists(result["path"])
        assert os.path.exists(result["zip_path"])
        assert len(result["manifest"]["deliverables"]) > 0

        # Verify files in output directory
        files_in_dir = os.listdir(result["path"])
        assert "manifest.json" in files_in_dir
        assert "SALES_COPY.md" in files_in_dir
        assert any(f.endswith(".zip") for f in files_in_dir)

    def test_manifest_saved_as_json(
        self, sample_spec, mock_generated_product, temp_output_dir
    ):
        """Test that manifest is saved as valid JSON."""
        mock_generator = Mock()
        mock_generator.generate.return_value = mock_generated_product

        packager = ProductPackager(output_dir=temp_output_dir)
        packager._generators["html_tool"] = mock_generator

        result = packager.package(sample_spec)

        # Load and verify manifest
        manifest_path = os.path.join(result["path"], "manifest.json")
        with open(manifest_path, "r") as f:
            loaded_manifest = json.load(f)

        assert loaded_manifest["name"] == sample_spec.solution_name
        assert loaded_manifest["type"] == sample_spec.product_type

    def test_zip_contains_all_files(
        self, sample_spec, mock_generated_product, temp_output_dir
    ):
        """Test that zip contains all product files."""
        mock_generator = Mock()
        mock_generator.generate.return_value = mock_generated_product

        packager = ProductPackager(output_dir=temp_output_dir)
        packager._generators["html_tool"] = mock_generator

        result = packager.package(sample_spec)

        # Extract and check zip contents
        with zipfile.ZipFile(result["zip_path"], "r") as zf:
            names = zf.namelist()

        # Should contain manifest, sales copy, and product files
        assert "manifest.json" in names
        assert "SALES_COPY.md" in names
        assert "tool.html" in names
        assert "README.md" in names

    def test_different_product_types(self, temp_output_dir):
        """Test packaging different product types."""
        packager = ProductPackager(output_dir=temp_output_dir)

        # Create specs for different types
        for product_type in ["html_tool", "pdf", "prompt_pack"]:
            spec = ProductSpec(
                problem="Test problem",
                solution_name=f"Test {product_type}",
                target_audience="Test audience",
                key_benefits=[
                    "Benefit 1",
                    "Benefit 2",
                    "Benefit 3",
                    "Benefit 4",
                    "Benefit 5",
                ],
                product_type=product_type,
            )

            # Mock the generator
            mock_product = GeneratedProduct(
                files={f"product.{product_type[:3]}": b"content"},
                manifest={},
            )
            packager._generators[product_type] = Mock()
            packager._generators[product_type].generate.return_value = mock_product

            result = packager.package(spec)

            assert result["product_id"] is not None
            assert result["manifest"]["type"] == product_type
