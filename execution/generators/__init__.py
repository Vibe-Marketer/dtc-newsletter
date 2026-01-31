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
from execution.generators.automation import AutomationGenerator
from execution.generators.html_tool import HtmlToolGenerator
from execution.generators.pdf import PdfGenerator
from execution.generators.sheets import SheetsGenerator

__all__ = [
    "AutomationGenerator",
    "BaseGenerator",
    "GeneratedProduct",
    "HtmlToolGenerator",
    "PdfGenerator",
    "ProductSpec",
    "SheetsGenerator",
]
