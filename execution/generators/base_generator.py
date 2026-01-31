"""
Base generator class for the Product Factory.

Defines the contract for all product generators through abstract base class
and dataclasses for input (ProductSpec) and output (GeneratedProduct).
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ProductSpec:
    """
    Specification for a product to be generated.

    This is the input contract for all generators.
    """

    # Required fields
    problem: str  # The pain point being solved
    solution_name: str  # Product name
    target_audience: str  # Who it's for
    key_benefits: list[str]  # 3-5 benefits
    product_type: (
        str  # One of: html_tool, automation, gpt_config, sheets, pdf, prompt_pack
    )

    # Optional fields
    price_cents: Optional[int] = None  # Price in cents (e.g., 2900 = $29)
    perceived_value: Optional[str] = None  # E.g., "$500+" or "10 hours saved"


@dataclass
class GeneratedProduct:
    """
    Output from a product generator.

    Contains the generated files, manifest, and optional sales copy.
    """

    files: dict[str, bytes]  # filename -> content mapping
    manifest: dict  # Product metadata (name, type, version, etc.)
    sales_copy: Optional[str] = None  # Generated sales copy


class BaseGenerator(ABC):
    """
    Abstract base class for all product generators.

    All generators (HTML tool, automation, GPT config, etc.) inherit from this
    and implement the generate() and validate() methods.
    """

    def __init__(self, claude_client=None):
        """
        Initialize the generator.

        Args:
            claude_client: Optional Claude API client for AI-assisted generation.
                          Can be injected for testing or reused across generators.
        """
        self.claude_client = claude_client

    @abstractmethod
    def generate(self, spec: ProductSpec) -> GeneratedProduct:
        """
        Generate a product from the specification.

        Args:
            spec: ProductSpec defining what to generate

        Returns:
            GeneratedProduct containing files, manifest, and optional sales copy

        Raises:
            ValueError: If spec is invalid for this generator
            RuntimeError: If generation fails
        """
        pass

    @abstractmethod
    def validate(self, product: GeneratedProduct) -> bool:
        """
        Validate a generated product.

        Checks that the product meets quality standards:
        - All required files present
        - Files are non-empty and well-formed
        - Manifest is complete

        Args:
            product: GeneratedProduct to validate

        Returns:
            True if product is valid, False otherwise
        """
        pass

    def get_product_type(self) -> str:
        """
        Get the product type this generator handles.

        Returns:
            Product type string (e.g., "html_tool", "automation")
        """
        # Default implementation - subclasses can override
        return "unknown"

    def _create_manifest(self, spec: ProductSpec, files: list[str]) -> dict:
        """
        Create a product manifest from spec and generated files.

        Args:
            spec: ProductSpec used for generation
            files: List of filenames in the product

        Returns:
            Manifest dict with standardized structure
        """
        # Build deliverables list with file info
        deliverables = [
            {"filename": filename, "type": self._get_file_type(filename)}
            for filename in files
        ]

        return {
            "id": str(uuid.uuid4()),
            "name": spec.solution_name,
            "type": spec.product_type,
            "version": "1.0.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "problem": spec.problem,
            "audience": spec.target_audience,
            "benefits": spec.key_benefits,
            "deliverables": deliverables,
            "price_cents": spec.price_cents,
            "perceived_value": spec.perceived_value,
        }

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
