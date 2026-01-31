"""
PDF generator for the Product Factory.

Creates professional PDF frameworks and guides using fpdf2 library.
Supports chapters, sections, bullet lists, numbered lists, and callout boxes.
"""

import json
from typing import Optional

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from execution.generators.base_generator import (
    BaseGenerator,
    GeneratedProduct,
    ProductSpec,
)


# Prompt for Claude to generate PDF content structure
PDF_CONTENT_PROMPT = """You are creating content for a professional PDF guide/framework.

Problem being solved: {problem}
Product name: {solution_name}
Target audience: {target_audience}
Key benefits: {key_benefits}

Generate a structured PDF content outline in JSON format with the following structure:

{{
    "title": "Framework/Guide title",
    "subtitle": "Short description (1-2 sentences)",
    "sections": [
        {{
            "title": "Section Title",
            "type": "text",
            "content": "Paragraph text content..."
        }},
        {{
            "title": "Key Steps",
            "type": "bullets",
            "content": ["Bullet point 1", "Bullet point 2", "Bullet point 3"]
        }},
        {{
            "title": "Implementation Order",
            "type": "numbered",
            "content": ["Step 1", "Step 2", "Step 3"]
        }},
        {{
            "title": "Pro Tip",
            "type": "callout",
            "callout_type": "tip",
            "content": "Important tip text..."
        }}
    ]
}}

Rules:
- Include 4-8 sections
- Mix section types (text, bullets, numbered, callout)
- Callout types can be: tip, warning, note
- Keep content actionable and practical for the target audience
- Focus on the key benefits

Return ONLY valid JSON, no explanation or markdown."""


class FrameworkPDF(FPDF):
    """
    Custom PDF class for creating professional framework documents.

    Extends FPDF with methods for chapters, bullet lists, and callout boxes.
    """

    def __init__(self, title: str = "Framework"):
        super().__init__()
        self._title = title
        self._page_width = 210  # A4 width in mm
        self._margin = 10

    def header(self):
        """Add header with title on each page."""
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(51, 51, 51)  # Dark gray
        title_width = self.get_string_width(self._title) + 6
        self.set_x((self._page_width - title_width) / 2)
        self.cell(title_width, 10, self._title, border=0, align="C")
        # Add line below header
        self.set_draw_color(200, 200, 200)  # Light gray
        self.line(self._margin, 20, self._page_width - self._margin, 20)
        self.ln(15)

    def footer(self):
        """Add page number at bottom of each page."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)  # Gray
        # Page X of Y format
        page_text = f"Page {self.page_no()} of {{nb}}"
        self.cell(0, 10, page_text, align="C")

    def chapter_title(self, title: str):
        """
        Add a chapter title with light blue background.

        Args:
            title: Chapter title text
        """
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(230, 242, 255)  # Light blue
        self.set_text_color(0, 51, 102)  # Dark blue
        self.cell(
            0,
            10,
            title,
            border=0,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="L",
            fill=True,
        )
        self.ln(4)

    def chapter_body(self, body: str):
        """
        Add body text in Times font.

        Args:
            body: Paragraph text content
        """
        self.set_font("Times", "", 12)
        self.set_text_color(51, 51, 51)  # Dark gray
        self.multi_cell(0, 6, body)
        self.ln(4)

    def bullet_list(self, items: list[str]):
        """
        Add a formatted bullet point list.

        Args:
            items: List of bullet point strings
        """
        self.set_font("Times", "", 12)
        self.set_text_color(51, 51, 51)
        for item in items:
            # Bullet character and indent
            self.set_x(self._margin + 5)
            self.cell(
                5, 6, chr(149), new_x=XPos.RIGHT, new_y=YPos.TOP
            )  # Bullet character
            # Use multi_cell for text that might wrap
            x_pos = self.get_x()
            self.multi_cell(0, 6, item)
            self.ln(1)
        self.ln(3)

    def numbered_list(self, items: list[str]):
        """
        Add a numbered list.

        Args:
            items: List of items to number
        """
        self.set_font("Times", "", 12)
        self.set_text_color(51, 51, 51)
        for i, item in enumerate(items, 1):
            self.set_x(self._margin + 5)
            self.cell(10, 6, f"{i}.", new_x=XPos.RIGHT, new_y=YPos.TOP)
            x_pos = self.get_x()
            self.multi_cell(0, 6, item)
            self.ln(1)
        self.ln(3)

    def callout_box(self, text: str, callout_type: str = "tip"):
        """
        Add a styled callout box for tips, warnings, or notes.

        Args:
            text: Content of the callout
            callout_type: One of 'tip', 'warning', 'note'
        """
        # Color schemes for different callout types
        colors = {
            "tip": {"fill": (232, 245, 233), "text": (46, 125, 50), "label": "TIP"},
            "warning": {
                "fill": (255, 243, 224),
                "text": (230, 81, 0),
                "label": "WARNING",
            },
            "note": {"fill": (227, 242, 253), "text": (25, 118, 210), "label": "NOTE"},
        }

        scheme = colors.get(callout_type, colors["note"])

        # Draw box background
        self.set_fill_color(*scheme["fill"])
        self.set_draw_color(200, 200, 200)

        # Calculate height needed
        self.set_font("Helvetica", "B", 10)
        label_text = f"{scheme['label']}: "

        # Draw the callout
        x = self._margin + 5
        y = self.get_y()
        width = self._page_width - 2 * self._margin - 10

        # Box with rounded corners effect (just use rect for simplicity)
        self.rect(x, y, width, 20, style="F")

        self.set_xy(x + 3, y + 3)
        self.set_text_color(*scheme["text"])
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, label_text, new_x=XPos.RIGHT, new_y=YPos.TOP)

        self.set_font("Times", "", 10)
        self.multi_cell(width - 10, 5, text)

        self.ln(8)


class PdfGenerator(BaseGenerator):
    """
    Generator for professional PDF frameworks and guides.

    Uses fpdf2 library to create styled PDF documents with chapters,
    bullet lists, numbered lists, and callout boxes.
    """

    def __init__(self, claude_client=None):
        """
        Initialize the PDF generator.

        Args:
            claude_client: Optional Claude API client for content generation
        """
        super().__init__(claude_client)

    def get_product_type(self) -> str:
        """Return the product type this generator handles."""
        return "pdf"

    def generate(self, spec: ProductSpec) -> GeneratedProduct:
        """
        Generate a PDF framework from the specification.

        Args:
            spec: ProductSpec defining what to generate

        Returns:
            GeneratedProduct containing the PDF and documentation
        """
        # Generate content structure using Claude (or use default if no client)
        content = self._generate_content_structure(spec)

        # Render the PDF
        pdf_bytes = self._render_pdf(content)

        # Create README
        readme = self._generate_readme(spec, content)

        # Build file dictionary
        filename = self._sanitize_filename(spec.solution_name) + ".pdf"
        files = {
            filename: pdf_bytes,
            "README.md": readme.encode("utf-8"),
        }

        # Create manifest
        manifest = self._create_manifest(spec, list(files.keys()))

        return GeneratedProduct(
            files=files,
            manifest=manifest,
            sales_copy=None,  # Could be added later
        )

    def validate(self, product: GeneratedProduct) -> bool:
        """
        Validate a generated PDF product.

        Checks:
        - PDF file exists
        - PDF is valid (starts with %PDF)
        - PDF is not empty (> 1KB)

        Args:
            product: GeneratedProduct to validate

        Returns:
            True if valid, False otherwise
        """
        # Find PDF file
        pdf_file = None
        for filename, content in product.files.items():
            if filename.endswith(".pdf"):
                pdf_file = content
                break

        if pdf_file is None:
            return False

        # Check PDF magic bytes (%PDF)
        if not pdf_file.startswith(b"%PDF"):
            return False

        # Check minimum size (1KB)
        if len(pdf_file) < 1024:
            return False

        return True

    def _generate_content_structure(self, spec: ProductSpec) -> dict:
        """
        Generate PDF content structure using Claude or default template.

        Args:
            spec: ProductSpec to generate content for

        Returns:
            Content structure dictionary
        """
        if self.claude_client:
            try:
                prompt = PDF_CONTENT_PROMPT.format(
                    problem=spec.problem,
                    solution_name=spec.solution_name,
                    target_audience=spec.target_audience,
                    key_benefits=", ".join(spec.key_benefits),
                )
                response = self.claude_client.generate(prompt)
                # Parse JSON from response
                content = json.loads(response)
                return content
            except Exception:
                # Fall back to default structure
                pass

        # Default structure if no Claude client or generation fails
        return self._default_content_structure(spec)

    def _default_content_structure(self, spec: ProductSpec) -> dict:
        """
        Create a default content structure when Claude is not available.

        Args:
            spec: ProductSpec to create content for

        Returns:
            Default content structure
        """
        return {
            "title": spec.solution_name,
            "subtitle": f"A framework to solve: {spec.problem}",
            "sections": [
                {
                    "title": "Introduction",
                    "type": "text",
                    "content": f"This framework helps {spec.target_audience} solve the problem of {spec.problem}.",
                },
                {
                    "title": "Key Benefits",
                    "type": "bullets",
                    "content": spec.key_benefits,
                },
                {
                    "title": "Getting Started",
                    "type": "numbered",
                    "content": [
                        "Read through this entire framework first",
                        "Identify which sections apply to your situation",
                        "Implement the strategies step by step",
                        "Track your results and iterate",
                    ],
                },
                {
                    "title": "Pro Tip",
                    "type": "callout",
                    "callout_type": "tip",
                    "content": "Start with one strategy and master it before moving to the next.",
                },
            ],
        }

    def _render_pdf(self, content: dict) -> bytes:
        """
        Render content structure to PDF bytes.

        Args:
            content: Content structure dictionary

        Returns:
            PDF file as bytes
        """
        title = content.get("title", "Framework")
        subtitle = content.get("subtitle", "")
        sections = content.get("sections", [])

        # Create PDF
        pdf = FrameworkPDF(title=title)
        pdf.alias_nb_pages()  # Enable page count
        pdf.add_page()

        # Add subtitle if present
        if subtitle:
            pdf.set_font("Helvetica", "I", 11)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 6, subtitle)
            pdf.ln(8)

        # Add sections
        for section in sections:
            section_type = section.get("type", "text")
            section_title = section.get("title", "")
            section_content = section.get("content", "")

            # Add section title
            if section_title:
                pdf.chapter_title(section_title)

            # Add content based on type
            if section_type == "text":
                pdf.chapter_body(section_content)
            elif section_type == "bullets":
                if isinstance(section_content, list):
                    pdf.bullet_list(section_content)
                else:
                    pdf.chapter_body(str(section_content))
            elif section_type == "numbered":
                if isinstance(section_content, list):
                    pdf.numbered_list(section_content)
                else:
                    pdf.chapter_body(str(section_content))
            elif section_type == "callout":
                callout_type = section.get("callout_type", "note")
                pdf.callout_box(section_content, callout_type)

        # Return PDF bytes
        return bytes(pdf.output())

    def _generate_readme(self, spec: ProductSpec, content: dict) -> str:
        """
        Generate README documentation for the PDF.

        Args:
            spec: ProductSpec used for generation
            content: Generated content structure

        Returns:
            README content as string
        """
        title = content.get("title", spec.solution_name)
        sections = content.get("sections", [])
        section_list = "\n".join(f"- {s.get('title', 'Section')}" for s in sections)

        return f"""# {title}

## About This PDF

This PDF framework was generated to help {spec.target_audience} solve the problem of:

> {spec.problem}

## Contents

{section_list}

## Key Benefits

{chr(10).join(f"- {b}" for b in spec.key_benefits)}

## How to Use

1. Open the PDF in your preferred reader
2. Read through each section in order
3. Take notes on strategies that apply to your situation
4. Implement the actionable steps
5. Refer back to the framework as needed

## License

This framework is for your personal use. Please do not redistribute without permission.
"""

    def _sanitize_filename(self, name: str) -> str:
        """
        Convert a product name to a safe filename.

        Args:
            name: Product name

        Returns:
            Safe filename string
        """
        # Remove or replace unsafe characters
        safe = name.lower()
        safe = safe.replace(" ", "_")
        safe = "".join(c for c in safe if c.isalnum() or c in "_-")
        return safe or "framework"
