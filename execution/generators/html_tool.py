"""
HTML Tool Generator for the Product Factory.

Generates single-file standalone HTML applications with embedded CSS and JavaScript.
These tools work offline in any browser with no external dependencies.
"""

import json
import re
from pathlib import Path
from typing import Optional

from jinja2 import Template

from .base_generator import BaseGenerator, GeneratedProduct, ProductSpec


# Default path to the HTML template
DEFAULT_TEMPLATE_PATH = (
    Path(__file__).parent.parent.parent
    / "data"
    / "product_templates"
    / "html"
    / "base.html"
)


HTML_TOOL_PROMPT = """You are creating a single-file HTML tool that solves a specific problem.

PROBLEM TO SOLVE:
{problem}

TOOL NAME: {solution_name}

KEY BENEFITS:
{benefits}

TARGET AUDIENCE: {target_audience}

Generate a complete, working HTML tool with the following structure:
1. Modern, clean, responsive CSS (mobile-first approach)
2. Semantic HTML structure with appropriate inputs, buttons, and output areas
3. Vanilla JavaScript (no frameworks) with proper error handling

REQUIREMENTS:
- CSS must be self-contained (no external fonts or CDN links)
- JavaScript must be vanilla JS only (no jQuery, React, etc.)
- Must work offline in any modern browser
- Must be accessible (proper labels, ARIA attributes where needed)
- Mobile-responsive design

Return a JSON object with exactly these keys:
{{
    "title": "Tool Title",
    "css": "/* All CSS styles */",
    "body_html": "<main>...</main>",
    "javascript": "// All JavaScript code"
}}

Return ONLY the JSON object, no markdown code blocks or additional text."""


class HtmlToolGenerator(BaseGenerator):
    """
    Generator for single-file HTML tools.

    Creates standalone HTML applications with embedded CSS and JavaScript
    that work offline in any browser.
    """

    def __init__(self, claude_client=None, template_path: Optional[Path] = None):
        """
        Initialize the HTML tool generator.

        Args:
            claude_client: Claude API client for AI-assisted generation
            template_path: Path to the Jinja2 HTML template (uses default if None)
        """
        super().__init__(claude_client)
        self.template_path = template_path or DEFAULT_TEMPLATE_PATH
        self._template: Optional[Template] = None

    def get_product_type(self) -> str:
        """Return the product type this generator handles."""
        return "html_tool"

    @property
    def template(self) -> Template:
        """Lazy-load the Jinja2 template."""
        if self._template is None:
            with open(self.template_path, "r", encoding="utf-8") as f:
                self._template = Template(f.read())
        return self._template

    def generate(self, spec: ProductSpec) -> GeneratedProduct:
        """
        Generate a single-file HTML tool from the specification.

        Args:
            spec: ProductSpec defining what to generate

        Returns:
            GeneratedProduct containing the HTML file and README

        Raises:
            ValueError: If spec is invalid for HTML tools
            RuntimeError: If generation fails
        """
        if spec.product_type != "html_tool":
            raise ValueError(
                f"Invalid product type '{spec.product_type}' for HtmlToolGenerator"
            )

        if self.claude_client is None:
            raise RuntimeError("Claude client is required for generation")

        # Format the prompt with spec details
        prompt = HTML_TOOL_PROMPT.format(
            problem=spec.problem,
            solution_name=spec.solution_name,
            benefits="\n".join(f"- {b}" for b in spec.key_benefits),
            target_audience=spec.target_audience,
        )

        # Call Claude to generate the tool content
        response = self.claude_client.generate(prompt)

        # Parse the JSON response
        try:
            tool_content = self._parse_response(response)
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Failed to parse Claude response: {e}")

        # Render the HTML template
        html_content = self.template.render(
            title=tool_content["title"],
            css=tool_content["css"],
            body=tool_content["body_html"],
            javascript=tool_content["javascript"],
        )

        # Generate filename from solution name
        filename = self._sanitize_filename(spec.solution_name) + ".html"

        # Generate README
        readme_content = self._generate_readme(spec, filename)

        # Create manifest
        files_list = [filename, "README.md"]
        manifest = self._create_manifest(spec, files_list)

        return GeneratedProduct(
            files={
                filename: html_content.encode("utf-8"),
                "README.md": readme_content.encode("utf-8"),
            },
            manifest=manifest,
        )

    def validate(self, product: GeneratedProduct) -> bool:
        """
        Validate a generated HTML tool product.

        Checks:
        - HTML file exists
        - HTML has DOCTYPE, html, head, body tags
        - JavaScript doesn't have obvious syntax errors

        Args:
            product: GeneratedProduct to validate

        Returns:
            True if product is valid, False otherwise
        """
        # Find the HTML file
        html_file = None
        for filename, content in product.files.items():
            if filename.endswith(".html"):
                html_file = content.decode("utf-8")
                break

        if html_file is None:
            return False

        # Check for DOCTYPE
        if (
            "<!DOCTYPE html>" not in html_file
            and "<!doctype html>" not in html_file.lower()
        ):
            return False

        # Check for required HTML structure
        html_lower = html_file.lower()
        if "<html" not in html_lower:
            return False
        if "<head" not in html_lower:
            return False
        if "<body" not in html_lower:
            return False

        # Basic JavaScript syntax check - look for obviously broken code
        # Extract JavaScript content
        js_match = re.search(
            r"<script[^>]*>(.*?)</script>", html_file, re.DOTALL | re.IGNORECASE
        )
        if js_match:
            js_content = js_match.group(1).strip()
            if js_content:
                # Check for obviously unbalanced braces (basic check)
                if js_content.count("{") != js_content.count("}"):
                    return False
                if js_content.count("(") != js_content.count(")"):
                    return False

        return True

    def _parse_response(self, response: str) -> dict:
        """
        Parse the Claude response to extract tool content.

        Args:
            response: Raw response from Claude

        Returns:
            Dict with title, css, body_html, javascript
        """
        # Strip markdown code blocks if present
        response = response.strip()
        if response.startswith("```"):
            # Remove first line (```json or ```)
            lines = response.split("\n")
            response = "\n".join(lines[1:])
        if response.endswith("```"):
            response = response[:-3]

        # Parse JSON
        data = json.loads(response.strip())

        # Validate required keys
        required_keys = ["title", "css", "body_html", "javascript"]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"Missing required key: {key}")

        return data

    def _sanitize_filename(self, name: str) -> str:
        """
        Convert a solution name to a safe filename.

        Args:
            name: Solution name

        Returns:
            Safe filename (without extension)
        """
        # Convert to lowercase, replace spaces with hyphens
        filename = name.lower().strip()
        filename = re.sub(r"\s+", "-", filename)
        # Remove non-alphanumeric characters except hyphens
        filename = re.sub(r"[^a-z0-9\-]", "", filename)
        # Remove multiple consecutive hyphens
        filename = re.sub(r"-+", "-", filename)
        # Remove leading/trailing hyphens
        filename = filename.strip("-")

        return filename or "tool"

    def _generate_readme(self, spec: ProductSpec, filename: str) -> str:
        """
        Generate a README file for the HTML tool.

        Args:
            spec: ProductSpec used for generation
            filename: Name of the generated HTML file

        Returns:
            README content as string
        """
        benefits_list = "\n".join(f"- {b}" for b in spec.key_benefits)

        return f"""# {spec.solution_name}

## Problem Solved

{spec.problem}

## Target Audience

{spec.target_audience}

## Key Benefits

{benefits_list}

## How to Use

1. Download `{filename}`
2. Open it in any modern web browser (Chrome, Firefox, Safari, Edge)
3. The tool works completely offline - no internet connection required

## Files Included

- `{filename}` - The complete tool (single-file HTML with embedded CSS/JS)
- `README.md` - This documentation file

## Technical Details

- **No Dependencies:** Works standalone, no frameworks or libraries required
- **Offline Ready:** All code is embedded, no external resources needed
- **Mobile Responsive:** Works on desktop, tablet, and mobile devices
- **Browser Support:** Any modern browser (Chrome, Firefox, Safari, Edge)

---

*Generated by DTC Newsletter Product Factory*
"""
