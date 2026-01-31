"""
Product packager for the Product Factory.
DOE-VERSION: 2026.01.31

Assembles complete product packages:
- Selects correct generator based on product type
- Generates product using selected generator
- Generates sales copy with voice profile
- Recommends optimal pricing
- Creates manifest with all metadata
- Saves to output directory as package
- Creates downloadable zip file

Output structure:
output/products/{product_id}/
├── manifest.json
├── SALES_COPY.md
├── [product files from generator]
└── {product_id}.zip
"""

import json
import logging
import os
import zipfile
from datetime import datetime, timezone
from typing import Optional
import uuid

from execution.generators.base_generator import ProductSpec, GeneratedProduct
from execution.generators.html_tool import HtmlToolGenerator
from execution.generators.automation import AutomationGenerator
from execution.generators.gpt_config import GptConfigGenerator
from execution.generators.prompt_pack import PromptPackGenerator
from execution.generators.pdf import PdfGenerator
from execution.generators.sheets import SheetsGenerator
from execution.sales_copy_generator import SalesCopyGenerator
from execution.pricing_recommender import PricingRecommender

logger = logging.getLogger(__name__)

# Map product types to generator classes
GENERATOR_MAP = {
    "html_tool": HtmlToolGenerator,
    "automation": AutomationGenerator,
    "gpt_config": GptConfigGenerator,
    "sheets": SheetsGenerator,
    "pdf": PdfGenerator,
    "prompt_pack": PromptPackGenerator,
}


class ProductPackager:
    """
    Assembles complete product packages ready for sale.

    Combines:
    - Product generation (via type-specific generator)
    - Sales copy generation (via SalesCopyGenerator)
    - Pricing recommendation (via PricingRecommender)
    - Package assembly (files + manifest + zip)
    """

    def __init__(
        self,
        claude_client=None,
        output_dir: str = "output/products",
    ):
        """
        Initialize the product packager.

        Args:
            claude_client: Optional Claude API client for AI-assisted generation.
                          Shared across all generators.
            output_dir: Directory for product output (default: output/products)
        """
        self.claude_client = claude_client
        self.output_dir = output_dir

        # Initialize generators with shared claude client
        self._generators = {}
        for product_type, generator_class in GENERATOR_MAP.items():
            self._generators[product_type] = generator_class(claude_client)

        # Initialize sales copy generator and pricing recommender
        self._sales_copy_generator = SalesCopyGenerator(claude_client)
        self._pricing_recommender = PricingRecommender()

    def package(
        self,
        spec: ProductSpec,
        value_signals: Optional[dict] = None,
    ) -> dict:
        """
        Create a complete product package.

        Args:
            spec: ProductSpec defining what to generate
            value_signals: Optional value signals for pricing

        Returns:
            Dict with:
                - product_id: Unique identifier
                - path: Path to output directory
                - manifest: Complete manifest dict
                - url: URL if product is hosted (None for files-only)
                - zip_path: Path to downloadable zip

        Raises:
            ValueError: If product_type is not supported
            RuntimeError: If generation fails
        """
        # Validate product type
        if spec.product_type not in GENERATOR_MAP:
            valid_types = ", ".join(GENERATOR_MAP.keys())
            raise ValueError(
                f"Unknown product type: {spec.product_type}. Valid types: {valid_types}"
            )

        # Generate unique product ID
        product_id = str(uuid.uuid4())[:8]
        logger.info(f"Creating product package: {product_id} ({spec.product_type})")

        # 1. Generate product using appropriate generator
        generator = self._generators[spec.product_type]
        product = generator.generate(spec)
        logger.info(f"Generated {len(product.files)} files")

        # 2. Get pricing recommendation
        pricing = self._pricing_recommender.recommend(spec.product_type, value_signals)
        logger.info(f"Recommended price: {pricing['price_display']}")

        # 3. Generate sales copy
        copy_dict = self._sales_copy_generator.generate(
            spec,
            pricing["price_display"],
            pricing["perceived_value"],
        )
        sales_copy_md = self._sales_copy_generator.format_markdown(copy_dict)
        logger.info("Generated sales copy")

        # 4. Create complete manifest
        manifest = self._create_manifest(product_id, spec, product, pricing, copy_dict)

        # 5. Save product to output directory
        product_path = self._save_product(product_id, product, sales_copy_md, manifest)
        logger.info(f"Saved product to: {product_path}")

        # 6. Create zip file
        zip_path = self._create_zip(product_id, product_path)
        logger.info(f"Created zip: {zip_path}")

        # Determine URL (only for sheets in online mode)
        url = None
        if spec.product_type == "sheets" and "sheet_url" in manifest.get("extras", {}):
            url = manifest["extras"]["sheet_url"]

        return {
            "product_id": product_id,
            "path": product_path,
            "manifest": manifest,
            "url": url,
            "zip_path": zip_path,
        }

    def _create_manifest(
        self,
        product_id: str,
        spec: ProductSpec,
        product: GeneratedProduct,
        pricing: dict,
        copy_dict: dict,
    ) -> dict:
        """
        Create a complete product manifest.

        Args:
            product_id: Unique product identifier
            spec: Original ProductSpec
            product: Generated product
            pricing: Pricing recommendation
            copy_dict: Sales copy sections

        Returns:
            Complete manifest dict
        """
        # Get file list and types
        deliverables = []
        for filename, content in product.files.items():
            file_info = {
                "filename": filename,
                "size_bytes": len(content),
                "type": self._get_file_type(filename),
            }
            deliverables.append(file_info)

        # Build manifest
        manifest = {
            "id": product_id,
            "name": spec.solution_name,
            "type": spec.product_type,
            "version": "1.0.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "problem": spec.problem,
            "audience": spec.target_audience,
            "benefits": spec.key_benefits,
            "deliverables": deliverables,
            "pricing": {
                "price_cents": pricing["price_cents"],
                "price_display": pricing["price_display"],
                "perceived_value": pricing["perceived_value"],
                "justification": pricing["justification"],
            },
            "sales_copy": {
                "headline": copy_dict.get("headline", ""),
                "subheadline": copy_dict.get("subheadline", ""),
                "cta": copy_dict.get("cta", ""),
            },
            "extras": {},
        }

        # Add generator-specific extras from product manifest
        if product.manifest:
            for key in [
                "gpt_name",
                "capabilities",
                "total_prompts",
                "categories",
                "sheet_url",
            ]:
                if key in product.manifest:
                    manifest["extras"][key] = product.manifest[key]

        return manifest

    def _save_product(
        self,
        product_id: str,
        product: GeneratedProduct,
        sales_copy: str,
        manifest: dict,
    ) -> str:
        """
        Save product files to output directory.

        Args:
            product_id: Unique product identifier
            product: Generated product
            sales_copy: Formatted sales copy markdown
            manifest: Complete manifest

        Returns:
            Path to product directory
        """
        # Create output directory
        product_path = os.path.join(self.output_dir, product_id)
        os.makedirs(product_path, exist_ok=True)

        # Save product files
        for filename, content in product.files.items():
            file_path = os.path.join(product_path, filename)

            # Create subdirectories if needed
            file_dir = os.path.dirname(file_path)
            if file_dir:
                os.makedirs(file_dir, exist_ok=True)

            # Write file
            if isinstance(content, bytes):
                with open(file_path, "wb") as f:
                    f.write(content)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

        # Save sales copy
        sales_copy_path = os.path.join(product_path, "SALES_COPY.md")
        with open(sales_copy_path, "w", encoding="utf-8") as f:
            f.write(sales_copy)

        # Save manifest
        manifest_path = os.path.join(product_path, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return product_path

    def _create_zip(self, product_id: str, product_path: str) -> str:
        """
        Create a downloadable zip file.

        Args:
            product_id: Unique product identifier
            product_path: Path to product directory

        Returns:
            Path to zip file
        """
        zip_filename = f"{product_id}.zip"
        zip_path = os.path.join(product_path, zip_filename)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Walk the product directory and add all files except the zip itself
            for root, dirs, files in os.walk(product_path):
                for file in files:
                    if file == zip_filename:
                        continue  # Don't include the zip in itself

                    file_path = os.path.join(root, file)
                    # Use relative path for archive
                    arcname = os.path.relpath(file_path, product_path)
                    zf.write(file_path, arcname)

        return zip_path

    def _get_file_type(self, filename: str) -> str:
        """
        Determine file type from filename extension.

        Args:
            filename: Name of the file

        Returns:
            File type string
        """
        extension_map = {
            ".html": "html",
            ".htm": "html",
            ".css": "stylesheet",
            ".js": "javascript",
            ".json": "json",
            ".md": "markdown",
            ".txt": "text",
            ".pdf": "pdf",
            ".csv": "csv",
            ".xlsx": "excel",
            ".py": "python",
            ".sh": "shell",
        }

        for ext, file_type in extension_map.items():
            if filename.lower().endswith(ext):
                return file_type

        return "unknown"

    def get_supported_types(self) -> list[str]:
        """
        Get list of supported product types.

        Returns:
            List of product type strings
        """
        return list(GENERATOR_MAP.keys())


def package_product(
    spec: ProductSpec,
    output_dir: Optional[str] = None,
    claude_client=None,
    value_signals: Optional[dict] = None,
) -> dict:
    """
    Convenience function to create a product package.

    Args:
        spec: ProductSpec defining what to generate
        output_dir: Optional output directory (default: output/products)
        claude_client: Optional Claude API client
        value_signals: Optional value signals for pricing

    Returns:
        Dict with product_id, path, manifest, url, zip_path

    Raises:
        ValueError: If product_type is not supported
    """
    if output_dir is None:
        output_dir = "output/products"

    packager = ProductPackager(claude_client=claude_client, output_dir=output_dir)
    return packager.package(spec, value_signals)
