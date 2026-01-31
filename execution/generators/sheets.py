"""
Google Sheets generator for the Product Factory.

Creates Google Sheets templates with formulas and formatting.
Supports both online mode (with credentials) and offline mode (JSON definition).
"""

import json
import os
from typing import Optional

try:
    import gspread
    from google.oauth2.service_account import Credentials

    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

from execution.generators.base_generator import (
    BaseGenerator,
    GeneratedProduct,
    ProductSpec,
)


# Google API scopes required for Sheets and Drive access
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# Prompt for Claude to generate sheet structure
SHEETS_CONTENT_PROMPT = """You are creating a Google Sheets template for a productivity/business tool.

Problem being solved: {problem}
Product name: {solution_name}
Target audience: {target_audience}
Key benefits: {key_benefits}

Generate a structured Google Sheets template in JSON format with the following structure:

{{
    "title": "Spreadsheet title",
    "worksheets": [
        {{
            "name": "Sheet1",
            "headers": ["Column A Header", "Column B Header", "Column C Header"],
            "formulas": {{
                "D2": "=SUM(B2:C2)",
                "E2": "=IF(D2>100, \\"High\\", \\"Low\\")"
            }},
            "sample_data": [
                ["Row1 Col1", 100, 50],
                ["Row1 Col2", 200, 75]
            ],
            "column_widths": {{"A": 150, "B": 100, "C": 100}},
            "notes": "This sheet tracks..."
        }}
    ]
}}

Rules:
- Include 1-3 worksheets that solve the problem
- Each worksheet should have clear headers
- Include useful formulas where appropriate (SUM, IF, COUNTIF, etc.)
- Add 2-3 rows of sample data to demonstrate usage
- Column widths are in pixels
- Keep it practical and immediately usable for the target audience

Return ONLY valid JSON, no explanation or markdown."""


class SheetsGenerator(BaseGenerator):
    """
    Generator for Google Sheets templates.

    Supports two modes:
    1. Online mode: Creates actual Google Sheet with credentials
    2. Offline mode: Generates JSON definition for manual creation
    """

    def __init__(self, claude_client=None, credentials_path: Optional[str] = None):
        """
        Initialize the Sheets generator.

        Args:
            claude_client: Optional Claude API client for content generation
            credentials_path: Path to service account JSON file.
                            Defaults to GOOGLE_SERVICE_ACCOUNT_JSON env var
                            or "service_account.json"
        """
        super().__init__(claude_client)
        self.credentials_path = credentials_path or os.environ.get(
            "GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json"
        )

    def get_product_type(self) -> str:
        """Return the product type this generator handles."""
        return "sheets"

    def generate(self, spec: ProductSpec) -> GeneratedProduct:
        """
        Generate a Google Sheets template from the specification.

        If credentials are available, creates an actual Google Sheet.
        Otherwise, generates a JSON definition for manual creation.

        Args:
            spec: ProductSpec defining what to generate

        Returns:
            GeneratedProduct containing sheet definition and documentation
        """
        # Generate sheet structure using Claude (or use default)
        structure = self._generate_sheet_structure(spec)

        # Try to create online if credentials available
        client = self._get_client()
        sheet_url = None

        if client:
            try:
                sheet_url = self._create_sheet_online(client, structure)
            except Exception as e:
                # Fall back to offline mode
                pass

        # Build files
        files = {}

        # Always include JSON definition (backup/offline mode)
        files["sheet_definition.json"] = json.dumps(structure, indent=2).encode("utf-8")

        # Generate README
        readme = self._generate_readme(spec, structure, sheet_url)
        files["README.md"] = readme.encode("utf-8")

        # Generate manual setup instructions
        manual_instructions = self._generate_manual_instructions(structure)
        files["MANUAL_SETUP.md"] = manual_instructions.encode("utf-8")

        # Create manifest
        manifest = self._create_manifest(spec, list(files.keys()))

        # Add sheet URL to manifest if available
        if sheet_url:
            manifest["sheet_url"] = sheet_url
            manifest["mode"] = "online"
        else:
            manifest["mode"] = "offline"

        return GeneratedProduct(
            files=files,
            manifest=manifest,
            sales_copy=None,
        )

    def validate(self, product: GeneratedProduct) -> bool:
        """
        Validate a generated Sheets product.

        Checks:
        - sheet_definition.json exists
        - At least one worksheet defined
        - Headers are present for each worksheet

        Args:
            product: GeneratedProduct to validate

        Returns:
            True if valid, False otherwise
        """
        # Check for sheet definition file
        if "sheet_definition.json" not in product.files:
            return False

        try:
            definition = json.loads(
                product.files["sheet_definition.json"].decode("utf-8")
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False

        # Check for worksheets
        worksheets = definition.get("worksheets", [])
        if not worksheets:
            return False

        # Check each worksheet has headers
        for worksheet in worksheets:
            headers = worksheet.get("headers", [])
            if not headers:
                return False

        return True

    def _get_client(self) -> Optional["gspread.Client"]:
        """
        Get an authenticated gspread client.

        Returns:
            Authenticated gspread Client, or None if credentials unavailable
        """
        if not GSPREAD_AVAILABLE:
            return None

        if not os.path.exists(self.credentials_path):
            return None

        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=SCOPES,
            )
            return gspread.authorize(credentials)
        except Exception:
            return None

    def _create_sheet_online(self, client: "gspread.Client", structure: dict) -> str:
        """
        Create a Google Sheet and return its URL.

        Args:
            client: Authenticated gspread client
            structure: Sheet structure definition

        Returns:
            URL of the created spreadsheet
        """
        title = structure.get("title", "New Spreadsheet")
        worksheets = structure.get("worksheets", [])

        # Create spreadsheet
        spreadsheet = client.create(title)

        # Process each worksheet
        for i, ws_def in enumerate(worksheets):
            ws_name = ws_def.get("name", f"Sheet{i + 1}")
            headers = ws_def.get("headers", [])
            formulas = ws_def.get("formulas", {})
            sample_data = ws_def.get("sample_data", [])

            # Use first worksheet or create new
            if i == 0:
                worksheet = spreadsheet.sheet1
                worksheet.update_title(ws_name)
            else:
                worksheet = spreadsheet.add_worksheet(
                    title=ws_name,
                    rows=100,
                    cols=len(headers) + 5,
                )

            # Add headers
            if headers:
                worksheet.update("A1", [headers])

            # Add sample data
            if sample_data:
                start_row = 2
                for row_idx, row_data in enumerate(sample_data):
                    worksheet.update(
                        f"A{start_row + row_idx}",
                        [row_data],
                    )

            # Add formulas
            for cell, formula in formulas.items():
                worksheet.update_acell(cell, formula)

        # Set sharing permissions (anyone with link can view)
        spreadsheet.share(None, perm_type="anyone", role="reader")

        return spreadsheet.url

    def _generate_sheet_structure(self, spec: ProductSpec) -> dict:
        """
        Generate sheet structure using Claude or default template.

        Args:
            spec: ProductSpec to generate content for

        Returns:
            Sheet structure dictionary
        """
        if self.claude_client:
            try:
                prompt = SHEETS_CONTENT_PROMPT.format(
                    problem=spec.problem,
                    solution_name=spec.solution_name,
                    target_audience=spec.target_audience,
                    key_benefits=", ".join(spec.key_benefits),
                )
                response = self.claude_client.generate(prompt)
                # Parse JSON from response
                structure = json.loads(response)
                return structure
            except Exception:
                # Fall back to default structure
                pass

        # Default structure
        return self._default_sheet_structure(spec)

    def _default_sheet_structure(self, spec: ProductSpec) -> dict:
        """
        Create a default sheet structure when Claude is not available.

        Args:
            spec: ProductSpec to create content for

        Returns:
            Default sheet structure
        """
        return {
            "title": spec.solution_name,
            "worksheets": [
                {
                    "name": "Dashboard",
                    "headers": ["Item", "Value", "Target", "Status"],
                    "formulas": {
                        "D2": '=IF(B2>=C2, "On Track", "Behind")',
                        "D3": '=IF(B3>=C3, "On Track", "Behind")',
                    },
                    "sample_data": [
                        ["Metric 1", 75, 100],
                        ["Metric 2", 150, 100],
                    ],
                    "notes": f"Dashboard for tracking {spec.problem}",
                },
                {
                    "name": "Data Entry",
                    "headers": ["Date", "Category", "Amount", "Notes"],
                    "formulas": {},
                    "sample_data": [
                        ["2024-01-01", "Type A", 100, "Sample entry"],
                        ["2024-01-02", "Type B", 200, "Another entry"],
                    ],
                    "notes": "Enter your raw data here",
                },
            ],
        }

    def _generate_readme(
        self, spec: ProductSpec, structure: dict, sheet_url: Optional[str]
    ) -> str:
        """
        Generate README documentation for the Sheets template.

        Args:
            spec: ProductSpec used for generation
            structure: Generated sheet structure
            sheet_url: URL of created sheet (if online mode)

        Returns:
            README content as string
        """
        title = structure.get("title", spec.solution_name)
        worksheets = structure.get("worksheets", [])

        worksheet_list = "\n".join(
            f"- **{ws.get('name', 'Sheet')}**: {ws.get('notes', 'Data sheet')}"
            for ws in worksheets
        )

        access_section = ""
        if sheet_url:
            access_section = f"""## Access Your Template

Your Google Sheet is ready at:
**{sheet_url}**

To make a copy for your own use:
1. Open the link above
2. File > Make a copy
3. Rename and save to your Google Drive
"""
        else:
            access_section = """## Creating Your Sheet

This template was generated in offline mode. See `MANUAL_SETUP.md` for step-by-step instructions to create the sheet manually.

Alternatively, use the `sheet_definition.json` file to programmatically create the sheet when you have Google API credentials.
"""

        return f"""# {title}

## About This Template

This Google Sheets template was generated to help {spec.target_audience} solve the problem of:

> {spec.problem}

## Worksheets Included

{worksheet_list}

## Key Benefits

{chr(10).join(f"- {b}" for b in spec.key_benefits)}

{access_section}

## How to Use

1. Make a copy of the template
2. Replace sample data with your own
3. Formulas will automatically calculate
4. Customize column headers if needed
5. Share with your team as needed

## Files Included

- `sheet_definition.json` - Full template structure (for backup/programmatic use)
- `MANUAL_SETUP.md` - Instructions to create manually
- `README.md` - This file
"""

    def _generate_manual_instructions(self, structure: dict) -> str:
        """
        Generate step-by-step instructions to create the sheet manually.

        Args:
            structure: Sheet structure definition

        Returns:
            Manual setup instructions as string
        """
        title = structure.get("title", "New Spreadsheet")
        worksheets = structure.get("worksheets", [])

        instructions = [
            f"""# Manual Setup Instructions

Follow these steps to create the "{title}" spreadsheet manually in Google Sheets.

## Step 1: Create a New Spreadsheet

1. Go to [sheets.google.com](https://sheets.google.com)
2. Click the "+" button to create a new spreadsheet
3. Name it: **{title}**

"""
        ]

        for i, ws in enumerate(worksheets, 1):
            ws_name = ws.get("name", f"Sheet{i}")
            headers = ws.get("headers", [])
            formulas = ws.get("formulas", {})
            sample_data = ws.get("sample_data", [])

            instructions.append(f"""## Step {i + 1}: Create "{ws_name}" Worksheet

""")

            if i > 1:
                instructions.append(f"""1. Click the "+" at the bottom to add a new sheet
2. Double-click the tab and rename it to: **{ws_name}**

""")
            else:
                instructions.append(f"""1. Double-click "Sheet1" tab at the bottom
2. Rename it to: **{ws_name}**

""")

            if headers:
                instructions.append(f"""### Headers (Row 1)

Enter these headers in row 1:

| Cell | Value |
|------|-------|
""")
                for col_idx, header in enumerate(headers):
                    col_letter = chr(65 + col_idx)  # A, B, C, etc.
                    instructions.append(f"| {col_letter}1 | {header} |\n")
                instructions.append("\n")

            if sample_data:
                instructions.append("""### Sample Data

Enter this sample data (starting row 2):

""")
                for row_idx, row in enumerate(sample_data):
                    instructions.append(f"**Row {row_idx + 2}:** ")
                    cells = []
                    for col_idx, value in enumerate(row):
                        col_letter = chr(65 + col_idx)
                        cells.append(f"{col_letter}{row_idx + 2}={value}")
                    instructions.append(", ".join(cells) + "\n\n")

            if formulas:
                instructions.append("""### Formulas

Add these formulas:

| Cell | Formula |
|------|---------|
""")
                for cell, formula in formulas.items():
                    instructions.append(f"| {cell} | `{formula}` |\n")
                instructions.append("\n")

        instructions.append("""## Step Final: Save and Share

1. Your spreadsheet auto-saves to Google Drive
2. To share: Click "Share" button in top right
3. Choose sharing settings appropriate for your use case

---

*Generated from sheet_definition.json*
""")

        return "".join(instructions)
