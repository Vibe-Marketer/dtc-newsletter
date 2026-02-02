"""
Automation Generator for the Product Factory.

Generates documented Python scripts with CLI interfaces for automating
common e-commerce and business tasks.
"""

import ast
import json
import re
from typing import Optional

from .base_generator import BaseGenerator, GeneratedProduct, ProductSpec


AUTOMATION_PROMPT = """You are creating a Python automation script that solves a specific problem.

PROBLEM TO SOLVE:
{problem}

SCRIPT NAME: {solution_name}

KEY BENEFITS:
{benefits}

TARGET AUDIENCE: {target_audience}

Generate a complete, production-ready Python script with the following requirements:

1. DOCUMENTATION:
   - Module docstring explaining what the script does
   - Function docstrings with args/returns documentation
   - Inline comments for complex logic

2. CLI INTERFACE:
   - Use argparse for command-line arguments
   - Provide sensible defaults where appropriate
   - Include --help documentation for all arguments

3. ERROR HANDLING:
   - Use try/except blocks for operations that might fail
   - Provide clear error messages to the user
   - Exit with appropriate exit codes (0 for success, 1 for error)

4. CODE QUALITY:
   - Follow PEP 8 style guidelines
   - Use type hints for function parameters
   - Keep functions small and focused

Return a JSON object with exactly these keys:
{{
    "script_code": "# Full Python script code",
    "requirements": ["dependency1", "dependency2"],
    "usage_instructions": "How to use the script"
}}

The requirements should only include external packages (not stdlib).
If no external packages are needed, return an empty list for requirements.

Return ONLY the JSON object, no markdown code blocks or additional text."""


class AutomationGenerator(BaseGenerator):
    """
    Generator for Python automation scripts.

    Creates documented Python scripts with argparse CLI interfaces
    and proper error handling.
    """

    def __init__(self, claude_client=None):
        """
        Initialize the automation generator.

        Args:
            claude_client: Claude API client for AI-assisted generation
        """
        super().__init__(claude_client)

    def get_product_type(self) -> str:
        """Return the product type this generator handles."""
        return "automation"

    def generate(self, spec: ProductSpec) -> GeneratedProduct:
        """
        Generate a Python automation script from the specification.

        Args:
            spec: ProductSpec defining what to generate

        Returns:
            GeneratedProduct containing the script, requirements.txt, and README

        Raises:
            ValueError: If spec is invalid for automations
            RuntimeError: If generation fails
        """
        if spec.product_type != "automation":
            raise ValueError(
                f"Invalid product type '{spec.product_type}' for AutomationGenerator"
            )

        if self.claude_client is None:
            raise RuntimeError("Claude client is required for generation")

        # Format the prompt with spec details
        prompt = AUTOMATION_PROMPT.format(
            problem=spec.problem,
            solution_name=spec.solution_name,
            benefits="\n".join(f"- {b}" for b in spec.key_benefits),
            target_audience=spec.target_audience,
        )

        # Call Claude to generate the script content
        # Use higher token limit for complex automation scripts
        response = self.claude_client.generate(prompt, max_tokens=8192)

        # Parse the JSON response
        try:
            script_content = self._parse_response(response)
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Failed to parse Claude response: {e}")

        # Generate filename from solution name
        script_name = self._sanitize_filename(spec.solution_name) + ".py"

        # Generate requirements.txt
        requirements_content = self._generate_requirements_txt(
            script_content.get("requirements", [])
        )

        # Generate README
        readme_content = self._generate_readme(
            spec, script_name, script_content.get("usage_instructions", "")
        )

        # Create manifest
        files_list = [script_name, "requirements.txt", "README.md"]
        manifest = self._create_manifest(spec, files_list)

        return GeneratedProduct(
            files={
                script_name: script_content["script_code"].encode("utf-8"),
                "requirements.txt": requirements_content.encode("utf-8"),
                "README.md": readme_content.encode("utf-8"),
            },
            manifest=manifest,
        )

    def validate(self, product: GeneratedProduct) -> bool:
        """
        Validate a generated automation product.

        Checks:
        - .py file exists
        - requirements.txt exists
        - Script has a docstring
        - Script has if __name__ == "__main__" block
        - Python syntax is valid (ast.parse)

        Args:
            product: GeneratedProduct to validate

        Returns:
            True if product is valid, False otherwise
        """
        # Find the Python file
        py_file = None
        py_filename = None
        for filename, content in product.files.items():
            if filename.endswith(".py"):
                py_file = content.decode("utf-8")
                py_filename = filename
                break

        if py_file is None:
            return False

        # Check for requirements.txt
        if "requirements.txt" not in product.files:
            return False

        # Check for docstring
        if not self._has_docstring(py_file):
            return False

        # Check for __main__ block
        if (
            'if __name__ == "__main__"' not in py_file
            and "if __name__ == '__main__'" not in py_file
        ):
            return False

        # Validate Python syntax
        try:
            ast.parse(py_file)
        except SyntaxError:
            return False

        return True

    def _parse_response(self, response: str) -> dict:
        """
        Parse the Claude response to extract script content.

        Args:
            response: Raw response from Claude

        Returns:
            Dict with script_code, requirements, usage_instructions
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
        if "script_code" not in data:
            raise KeyError("Missing required key: script_code")

        # Ensure requirements is a list
        if "requirements" not in data:
            data["requirements"] = []
        elif not isinstance(data["requirements"], list):
            data["requirements"] = [data["requirements"]]

        # Ensure usage_instructions exists
        if "usage_instructions" not in data:
            data["usage_instructions"] = ""

        return data

    def _sanitize_filename(self, name: str) -> str:
        """
        Convert a solution name to a safe Python filename.

        Args:
            name: Solution name

        Returns:
            Safe filename (without extension)
        """
        # Convert to lowercase, replace spaces with underscores
        filename = name.lower().strip()
        filename = re.sub(r"\s+", "_", filename)
        # Remove non-alphanumeric characters except underscores
        filename = re.sub(r"[^a-z0-9_]", "", filename)
        # Remove multiple consecutive underscores
        filename = re.sub(r"_+", "_", filename)
        # Remove leading/trailing underscores
        filename = filename.strip("_")
        # Ensure doesn't start with number
        if filename and filename[0].isdigit():
            filename = "script_" + filename

        return filename or "automation"

    def _has_docstring(self, code: str) -> bool:
        """
        Check if Python code has a module-level docstring.

        Args:
            code: Python source code

        Returns:
            True if docstring exists, False otherwise
        """
        try:
            tree = ast.parse(code)
            if tree.body:
                first_node = tree.body[0]
                if isinstance(first_node, ast.Expr):
                    if isinstance(first_node.value, ast.Constant) and isinstance(
                        first_node.value.value, str
                    ):
                        return True
                    # Python 3.7 compatibility
                    if hasattr(ast, "Str") and isinstance(first_node.value, ast.Str):
                        return True
        except SyntaxError:
            pass
        return False

    def _generate_requirements_txt(self, requirements: list[str]) -> str:
        """
        Generate a requirements.txt file.

        Args:
            requirements: List of package names

        Returns:
            requirements.txt content
        """
        if not requirements:
            return "# No external dependencies required\n"

        # Sort and deduplicate
        unique_reqs = sorted(set(requirements))
        return "\n".join(unique_reqs) + "\n"

    def _generate_readme(self, spec: ProductSpec, script_name: str, usage: str) -> str:
        """
        Generate a README file for the automation script.

        Args:
            spec: ProductSpec used for generation
            script_name: Name of the generated Python file
            usage: Usage instructions from Claude

        Returns:
            README content as string
        """
        benefits_list = "\n".join(f"- {b}" for b in spec.key_benefits)

        # Clean up usage instructions
        usage_section = usage.strip() if usage else "See script help for usage details."

        return f"""# {spec.solution_name}

## Problem Solved

{spec.problem}

## Target Audience

{spec.target_audience}

## Key Benefits

{benefits_list}

## Installation

1. Ensure you have Python 3.8 or later installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

{usage_section}

For full options, run:
```bash
python {script_name} --help
```

## Files Included

- `{script_name}` - The main automation script
- `requirements.txt` - Python dependencies
- `README.md` - This documentation file

## Technical Details

- **Python 3.8+:** Requires Python 3.8 or later
- **CLI Interface:** Uses argparse for command-line arguments
- **Error Handling:** Graceful error handling with clear messages

---

*Generated by DTC Newsletter Product Factory*
"""
