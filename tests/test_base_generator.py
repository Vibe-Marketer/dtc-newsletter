"""
Tests for base generator class and dataclasses.
"""

import pytest
from unittest.mock import Mock
from uuid import UUID
from datetime import datetime

from execution.generators import BaseGenerator, ProductSpec, GeneratedProduct
from execution.generators.base_generator import BaseGenerator as BaseGeneratorDirect


class TestProductSpec:
    """Test ProductSpec dataclass."""

    def test_creation_with_all_fields(self):
        """ProductSpec should accept all required fields."""
        spec = ProductSpec(
            problem="Shopify checkout is confusing",
            solution_name="Checkout Clarity Tool",
            target_audience="Shopify store owners",
            key_benefits=["Reduce abandonment", "Increase conversions", "Easy setup"],
            product_type="html_tool",
            price_cents=2900,
            perceived_value="$500+ in saved revenue",
        )

        assert spec.problem == "Shopify checkout is confusing"
        assert spec.solution_name == "Checkout Clarity Tool"
        assert spec.target_audience == "Shopify store owners"
        assert len(spec.key_benefits) == 3
        assert spec.product_type == "html_tool"
        assert spec.price_cents == 2900
        assert spec.perceived_value == "$500+ in saved revenue"

    def test_creation_with_optional_fields_defaulted(self):
        """ProductSpec should default optional fields to None."""
        spec = ProductSpec(
            problem="Shipping costs too high",
            solution_name="Shipping Calculator",
            target_audience="E-commerce sellers",
            key_benefits=["Save on shipping", "Compare carriers"],
            product_type="sheets",
        )

        assert spec.problem == "Shipping costs too high"
        assert spec.solution_name == "Shipping Calculator"
        assert spec.price_cents is None
        assert spec.perceived_value is None

    def test_product_types(self):
        """ProductSpec should accept all valid product types."""
        valid_types = [
            "html_tool",
            "automation",
            "gpt_config",
            "sheets",
            "pdf",
            "prompt_pack",
        ]

        for product_type in valid_types:
            spec = ProductSpec(
                problem="Test problem",
                solution_name="Test Product",
                target_audience="Test audience",
                key_benefits=["Benefit 1"],
                product_type=product_type,
            )
            assert spec.product_type == product_type

    def test_key_benefits_list(self):
        """ProductSpec should accept a list of benefits."""
        benefits = ["Benefit 1", "Benefit 2", "Benefit 3", "Benefit 4", "Benefit 5"]
        spec = ProductSpec(
            problem="Problem",
            solution_name="Solution",
            target_audience="Audience",
            key_benefits=benefits,
            product_type="automation",
        )

        assert len(spec.key_benefits) == 5
        assert spec.key_benefits[0] == "Benefit 1"
        assert spec.key_benefits[-1] == "Benefit 5"


class TestGeneratedProduct:
    """Test GeneratedProduct dataclass."""

    def test_creation_with_files_and_manifest(self):
        """GeneratedProduct should accept files dict and manifest dict."""
        files = {
            "index.html": b"<html>content</html>",
            "styles.css": b".class { color: red; }",
        }
        manifest = {
            "id": "test-id",
            "name": "Test Product",
            "type": "html_tool",
        }

        product = GeneratedProduct(
            files=files,
            manifest=manifest,
        )

        assert len(product.files) == 2
        assert product.files["index.html"] == b"<html>content</html>"
        assert product.manifest["name"] == "Test Product"
        assert product.sales_copy is None

    def test_creation_with_sales_copy(self):
        """GeneratedProduct should optionally accept sales copy."""
        product = GeneratedProduct(
            files={"readme.md": b"# Product"},
            manifest={"id": "123", "name": "Product"},
            sales_copy="This product solves X by doing Y.",
        )

        assert product.sales_copy == "This product solves X by doing Y."

    def test_files_are_bytes(self):
        """GeneratedProduct files should be bytes."""
        product = GeneratedProduct(
            files={"test.txt": b"Hello world"},
            manifest={},
        )

        assert isinstance(product.files["test.txt"], bytes)


class ConcreteGenerator(BaseGenerator):
    """Concrete implementation of BaseGenerator for testing."""

    def generate(self, spec: ProductSpec) -> GeneratedProduct:
        files = {
            "main.html": b"<html><body>Generated</body></html>",
        }
        manifest = self._create_manifest(spec, list(files.keys()))
        return GeneratedProduct(files=files, manifest=manifest)

    def validate(self, product: GeneratedProduct) -> bool:
        return len(product.files) > 0 and bool(product.manifest)

    def get_product_type(self) -> str:
        return "test_type"


class TestBaseGenerator:
    """Test BaseGenerator abstract class."""

    def test_cannot_instantiate_directly(self):
        """BaseGenerator should not be directly instantiable."""
        with pytest.raises(TypeError) as exc_info:
            BaseGenerator()

        assert (
            "abstract" in str(exc_info.value).lower()
            or "instantiate" in str(exc_info.value).lower()
        )

    def test_can_instantiate_concrete_subclass(self):
        """Concrete subclasses should be instantiable."""
        generator = ConcreteGenerator()
        assert generator is not None

    def test_accepts_claude_client(self):
        """BaseGenerator should accept optional claude_client."""
        mock_client = Mock()
        generator = ConcreteGenerator(claude_client=mock_client)

        assert generator.claude_client is mock_client

    def test_default_claude_client_is_none(self):
        """Claude client should default to None."""
        generator = ConcreteGenerator()
        assert generator.claude_client is None

    def test_get_product_type_default(self):
        """get_product_type should return subclass override."""
        generator = ConcreteGenerator()
        assert generator.get_product_type() == "test_type"


class TestCreateManifest:
    """Test _create_manifest helper method."""

    def test_manifest_has_uuid(self):
        """Manifest should include a valid UUID."""
        generator = ConcreteGenerator()
        spec = ProductSpec(
            problem="Test problem",
            solution_name="Test Product",
            target_audience="Testers",
            key_benefits=["Benefit"],
            product_type="html_tool",
        )

        manifest = generator._create_manifest(spec, ["file.html"])

        # Should be a valid UUID string
        uuid_obj = UUID(manifest["id"])
        assert uuid_obj is not None

    def test_manifest_has_timestamp(self):
        """Manifest should include ISO timestamp."""
        generator = ConcreteGenerator()
        spec = ProductSpec(
            problem="Test",
            solution_name="Product",
            target_audience="Users",
            key_benefits=["Fast"],
            product_type="automation",
        )

        manifest = generator._create_manifest(spec, ["script.py"])

        # Should be parseable as datetime
        timestamp = manifest["created_at"]
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None

    def test_manifest_has_deliverables_list(self):
        """Manifest should include deliverables list with file info."""
        generator = ConcreteGenerator()
        spec = ProductSpec(
            problem="Test",
            solution_name="Multi-File Product",
            target_audience="Users",
            key_benefits=["Comprehensive"],
            product_type="html_tool",
        )

        manifest = generator._create_manifest(
            spec, ["index.html", "styles.css", "script.js"]
        )

        assert "deliverables" in manifest
        assert len(manifest["deliverables"]) == 3

        # Check deliverable structure
        html_file = next(
            d for d in manifest["deliverables"] if d["filename"] == "index.html"
        )
        assert html_file["type"] == "html"

        css_file = next(
            d for d in manifest["deliverables"] if d["filename"] == "styles.css"
        )
        assert css_file["type"] == "stylesheet"

        js_file = next(
            d for d in manifest["deliverables"] if d["filename"] == "script.js"
        )
        assert js_file["type"] == "javascript"

    def test_manifest_includes_spec_fields(self):
        """Manifest should include all spec fields."""
        generator = ConcreteGenerator()
        spec = ProductSpec(
            problem="Shipping is expensive",
            solution_name="Shipping Saver",
            target_audience="E-commerce sellers",
            key_benefits=["Save money", "Compare carriers", "Easy to use"],
            product_type="sheets",
            price_cents=1999,
            perceived_value="$100+ savings monthly",
        )

        manifest = generator._create_manifest(spec, ["calculator.xlsx"])

        assert manifest["name"] == "Shipping Saver"
        assert manifest["type"] == "sheets"
        assert manifest["version"] == "1.0.0"
        assert manifest["problem"] == "Shipping is expensive"
        assert manifest["audience"] == "E-commerce sellers"
        assert manifest["benefits"] == ["Save money", "Compare carriers", "Easy to use"]
        assert manifest["price_cents"] == 1999
        assert manifest["perceived_value"] == "$100+ savings monthly"

    def test_manifest_handles_various_file_types(self):
        """Manifest should correctly identify various file types."""
        generator = ConcreteGenerator()
        spec = ProductSpec(
            problem="Test",
            solution_name="Test",
            target_audience="Test",
            key_benefits=["Test"],
            product_type="automation",
        )

        files = [
            "doc.md",
            "data.json",
            "config.txt",
            "report.pdf",
            "data.csv",
            "spreadsheet.xlsx",
            "script.py",
            "run.sh",
        ]

        manifest = generator._create_manifest(spec, files)

        expected_types = {
            "doc.md": "markdown",
            "data.json": "json",
            "config.txt": "text",
            "report.pdf": "pdf",
            "data.csv": "csv",
            "spreadsheet.xlsx": "excel",
            "script.py": "python",
            "run.sh": "shell",
        }

        for deliverable in manifest["deliverables"]:
            expected = expected_types[deliverable["filename"]]
            assert deliverable["type"] == expected, (
                f"Expected {expected} for {deliverable['filename']}"
            )

    def test_manifest_handles_unknown_file_type(self):
        """Manifest should return 'unknown' for unrecognized extensions."""
        generator = ConcreteGenerator()
        spec = ProductSpec(
            problem="Test",
            solution_name="Test",
            target_audience="Test",
            key_benefits=["Test"],
            product_type="automation",
        )

        manifest = generator._create_manifest(spec, ["weird.xyz", "noextension"])

        for deliverable in manifest["deliverables"]:
            assert deliverable["type"] == "unknown"


class TestGeneratorIntegration:
    """Integration tests for the full generator flow."""

    def test_generate_and_validate_flow(self):
        """Full generate -> validate flow should work."""
        generator = ConcreteGenerator()
        spec = ProductSpec(
            problem="Cart abandonment is high",
            solution_name="Cart Recovery Tool",
            target_audience="Shopify merchants",
            key_benefits=[
                "Recover lost sales",
                "Automated follow-up",
                "Easy integration",
            ],
            product_type="html_tool",
            price_cents=4900,
        )

        product = generator.generate(spec)
        is_valid = generator.validate(product)

        assert is_valid
        assert len(product.files) > 0
        assert product.manifest["name"] == "Cart Recovery Tool"
        assert product.manifest["type"] == "html_tool"
