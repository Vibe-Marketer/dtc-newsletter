"""
Product generators for the Product Factory.

This package contains the base generator class and specific generators
for different product types (HTML tools, automations, GPT configs, etc.).
"""

from execution.generators.base_generator import (
    BaseGenerator,
    GeneratedProduct,
    ProductSpec,
)
from execution.generators.html_tool import HtmlToolGenerator

__all__ = [
    "BaseGenerator",
    "GeneratedProduct",
    "ProductSpec",
    "HtmlToolGenerator",
]
