#!/usr/bin/env python3
"""
Product Launcher - Makes generated products instantly usable.

Usage:
    python execution/launch_product.py <product_id>
    python execution/launch_product.py --list
    python execution/launch_product.py --serve <product_id>  # Start local server

Examples:
    python execution/launch_product.py 92d5c513      # Opens HTML tool in browser
    python execution/launch_product.py --list        # Shows all products
    python execution/launch_product.py --serve all   # Serves all products on localhost
"""

import argparse
import http.server
import json
import os
import socketserver
import subprocess
import sys
import webbrowser
from pathlib import Path
from functools import partial

# Product directory
PRODUCTS_DIR = Path("output/products")


def list_products() -> list[dict]:
    """List all available products with their types and names."""
    products = []

    if not PRODUCTS_DIR.exists():
        return products

    for product_dir in PRODUCTS_DIR.iterdir():
        if not product_dir.is_dir():
            continue

        manifest_path = product_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        try:
            with open(manifest_path) as f:
                manifest = json.load(f)

            products.append(
                {
                    "id": product_dir.name,
                    "name": manifest.get("name", "Unknown"),
                    "type": manifest.get("type", "unknown"),
                    "path": str(product_dir),
                    "problem": manifest.get("problem", "")[:50],
                }
            )
        except (json.JSONDecodeError, KeyError):
            continue

    return products


def find_product(product_id: str) -> dict | None:
    """Find a product by ID (can be partial match)."""
    products = list_products()

    # Exact match
    for p in products:
        if p["id"] == product_id:
            return p

    # Partial match
    for p in products:
        if product_id in p["id"]:
            return p

    return None


def launch_html_tool(product_path: Path) -> None:
    """Launch an HTML tool by opening it in the default browser."""
    html_files = list(product_path.glob("*.html"))

    if not html_files:
        print(f"No HTML file found in {product_path}")
        return

    html_file = html_files[0]
    file_url = f"file://{html_file.absolute()}"

    print(f"Opening {html_file.name} in browser...")
    webbrowser.open(file_url)
    print(f"✓ Opened: {file_url}")


def launch_automation(product_path: Path) -> None:
    """Show how to run an automation."""
    py_files = list(product_path.glob("*.py"))
    py_files = [f for f in py_files if f.name != "__init__.py"]

    if not py_files:
        print(f"No Python files found in {product_path}")
        return

    main_file = py_files[0]

    print(f"\n{'=' * 60}")
    print(f"AUTOMATION: {product_path.name}")
    print(f"{'=' * 60}")
    print(f"\nTo run this automation:")
    print(f"\n    python {main_file}")
    print(f"\nOr with arguments:")
    print(f"\n    python {main_file} --help")
    print(f"\n{'=' * 60}")

    # Show first 20 lines of the file to give context
    with open(main_file) as f:
        lines = f.readlines()[:20]

    print("\nFirst 20 lines of the script:")
    print("-" * 40)
    for line in lines:
        print(line.rstrip())


def launch_gpt_config(product_path: Path) -> None:
    """Show GPT config instructions."""
    instructions_path = product_path / "INSTRUCTIONS.md"
    setup_path = product_path / "SETUP_GUIDE.md"

    if instructions_path.exists():
        print(f"\n{'=' * 60}")
        print(f"GPT CONFIG: {product_path.name}")
        print(f"{'=' * 60}")
        print(f"\n1. Go to: https://chat.openai.com/gpts/editor")
        print(f"2. Click 'Create a GPT'")
        print(f"3. Copy the contents of: {instructions_path}")
        print(f"4. Paste into the 'Instructions' field")

        if setup_path.exists():
            print(f"\nDetailed setup guide: {setup_path}")

        print(f"\n{'=' * 60}")

        # Show a preview
        with open(instructions_path) as f:
            content = f.read()

        preview = content[:500]
        print("\nInstructions preview:")
        print("-" * 40)
        print(preview)
        if len(content) > 500:
            print(f"\n... ({len(content) - 500} more characters)")
    else:
        print(f"No INSTRUCTIONS.md found in {product_path}")


def launch_sheets(product_path: Path) -> None:
    """Show sheets setup instructions."""
    setup_path = product_path / "MANUAL_SETUP.md"
    definition_path = product_path / "sheet_definition.json"

    print(f"\n{'=' * 60}")
    print(f"GOOGLE SHEETS: {product_path.name}")
    print(f"{'=' * 60}")

    if definition_path.exists():
        print(f"\nSheet definition: {definition_path}")
        with open(definition_path) as f:
            definition = json.load(f)
        print(f"Title: {definition.get('title', 'Unknown')}")
        print(f"Sheets: {len(definition.get('sheets', []))}")

    if setup_path.exists():
        print(f"\nManual setup guide: {setup_path}")
        print("\nTo create this sheet:")
        print("1. Go to: https://sheets.google.com")
        print("2. Create a new spreadsheet")
        print(f"3. Follow instructions in: {setup_path}")

    print(f"\n{'=' * 60}")


def launch_prompt_pack(product_path: Path) -> None:
    """Show prompt pack contents."""
    prompts_md = product_path / "prompts.md"
    quick_start = product_path / "QUICK_START.md"

    print(f"\n{'=' * 60}")
    print(f"PROMPT PACK: {product_path.name}")
    print(f"{'=' * 60}")

    if quick_start.exists():
        print(f"\nQuick start: {quick_start}")
        with open(quick_start) as f:
            content = f.read()
        print("\n" + content[:1000])
        if len(content) > 1000:
            print(f"\n... (see {quick_start} for full content)")
    elif prompts_md.exists():
        print(f"\nAll prompts: {prompts_md}")
        with open(prompts_md) as f:
            content = f.read()
        print("\n" + content[:1000])
        if len(content) > 1000:
            print(f"\n... (see {prompts_md} for full content)")
    else:
        print("No prompts found!")

    print(f"\n{'=' * 60}")


def launch_pdf(product_path: Path) -> None:
    """Open PDF in default viewer."""
    pdf_files = list(product_path.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF file found in {product_path}")
        return

    pdf_file = pdf_files[0]
    print(f"Opening {pdf_file.name}...")

    if sys.platform == "darwin":
        subprocess.run(["open", str(pdf_file)])
    elif sys.platform == "win32":
        os.startfile(str(pdf_file))
    else:
        subprocess.run(["xdg-open", str(pdf_file)])

    print(f"✓ Opened: {pdf_file}")


def launch_product(product_id: str) -> None:
    """Launch a product based on its type."""
    product = find_product(product_id)

    if not product:
        print(f"Product not found: {product_id}")
        print("\nAvailable products:")
        for p in list_products():
            print(f"  {p['id']}: {p['name']} ({p['type']})")
        return

    product_path = Path(product["path"])
    product_type = product["type"]

    print(f"\nLaunching: {product['name']} ({product_type})")

    launchers = {
        "html_tool": launch_html_tool,
        "automation": launch_automation,
        "gpt_config": launch_gpt_config,
        "sheets": launch_sheets,
        "prompt_pack": launch_prompt_pack,
        "pdf": launch_pdf,
    }

    launcher = launchers.get(product_type)
    if launcher:
        launcher(product_path)
    else:
        print(f"Unknown product type: {product_type}")
        print(f"Product directory: {product_path}")


def serve_products(product_id: str = "all", port: int = 8000) -> None:
    """
    Start a local HTTP server to serve product files.

    This makes HTML tools accessible via localhost URLs.
    """
    if product_id == "all":
        serve_dir = PRODUCTS_DIR
    else:
        product = find_product(product_id)
        if not product:
            print(f"Product not found: {product_id}")
            return
        serve_dir = Path(product["path"])

    os.chdir(serve_dir)

    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(serve_dir))

    print(f"\n{'=' * 60}")
    print(f"Serving products at: http://localhost:{port}")
    print(f"Directory: {serve_dir}")
    print(f"{'=' * 60}")

    if product_id == "all":
        print("\nAvailable products:")
        for p in list_products():
            if p["type"] == "html_tool":
                html_files = list(Path(p["path"]).glob("*.html"))
                if html_files:
                    rel_path = html_files[0].relative_to(serve_dir)
                    print(f"  http://localhost:{port}/{rel_path}")
    else:
        html_files = list(serve_dir.glob("*.html"))
        for f in html_files:
            print(f"  http://localhost:{port}/{f.name}")

    print(f"\nPress Ctrl+C to stop the server")
    print(f"{'=' * 60}\n")

    with socketserver.TCPServer(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


def print_products_table() -> None:
    """Print a formatted table of all products."""
    products = list_products()

    if not products:
        print("No products found in output/products/")
        return

    print(f"\n{'=' * 80}")
    print(f"{'ID':<12} {'TYPE':<12} {'NAME':<40}")
    print(f"{'=' * 80}")

    for p in products:
        name = p["name"][:38] if len(p["name"]) > 38 else p["name"]
        print(f"{p['id']:<12} {p['type']:<12} {name:<40}")

    print(f"{'=' * 80}")
    print(f"\nTotal: {len(products)} products")
    print(f"\nUsage:")
    print(f"  python execution/launch_product.py <id>        # Launch specific product")
    print(
        f"  python execution/launch_product.py --serve all # Serve all on localhost:8000"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Launch and serve generated products",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python execution/launch_product.py 92d5c513        # Opens product in appropriate app
  python execution/launch_product.py --list          # Shows all products
  python execution/launch_product.py --serve all     # HTTP server for all products
  python execution/launch_product.py --serve 92d5    # HTTP server for one product
        """,
    )

    parser.add_argument(
        "product_id",
        nargs="?",
        help="Product ID to launch (can be partial match)",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available products",
    )

    parser.add_argument(
        "--serve",
        metavar="ID",
        nargs="?",
        const="all",
        help="Start HTTP server (use 'all' for all products)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP server (default: 8000)",
    )

    args = parser.parse_args()

    if args.list:
        print_products_table()
    elif args.serve:
        serve_products(args.serve, args.port)
    elif args.product_id:
        launch_product(args.product_id)
    else:
        print_products_table()


if __name__ == "__main__":
    main()
