#!/usr/bin/env python3
"""
DTCNews unified newsletter pipeline.
DOE-VERSION: 2026.02.04

Orchestrates the full newsletter generation workflow:

PHASE 1 - FIND WHAT'S CRUSHING IT:
  1. Content aggregation (content_aggregate.py)
  2. Outlier ranking (outlier_ranker.py) - find the BIGGEST viral content

PHASE 2 - CREATE GENUINE VALUE:
  3. Deep dive generation (deep_dive_generator.py) - WHO, WHAT, WHY, HOW
  4. Content selection (content_selector.py)
  5. Newsletter assembly (newsletter_generator.py)

PHASE 3 - POLISH FOR MAXIMUM IMPACT:
  6. Hormozi hook review (copy_review_hormozi.py)
  7. Schwartz copy review (copy_review_schwartz.py)
  8. Product integration (product_integrator.py)
  9. Final editing (editor_agent.py)

PHASE 4 - HUMAN APPROVAL:
  10. Human review checkpoint

Usage:
    # Full pipeline
    python execution/dtcnews_pipeline.py

    # Start from specific step
    python execution/dtcnews_pipeline.py --start-from rank

    # Run specific steps only
    python execution/dtcnews_pipeline.py --steps rank,deep_dive,generate

    # Dry run (show what would happen)
    python execution/dtcnews_pipeline.py --dry-run
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DOE_VERSION = "2026.02.04"

# =============================================================================
# PIPELINE STEPS
# =============================================================================

PIPELINE_STEPS = [
    # === PHASE 1: FIND WHAT'S CRUSHING IT ===
    {
        "id": "aggregate",
        "name": "Content Aggregation",
        "script": "content_aggregate.py",
        "description": "Fetch viral content from Reddit, YouTube, Perplexity",
        "output": "output/content_{date}.json",
    },
    {
        "id": "rank",
        "name": "Outlier Ranking",
        "script": "outlier_ranker.py",
        "description": "Rank by outlier score + virality analysis to find what's CRUSHING it",
        "input": "output/content_{date}.json",
        "output": "output/content_ranked_{date}.json",
    },
    # === PHASE 2: CREATE GENUINE VALUE ===
    {
        "id": "deep_dive",
        "name": "Deep Dive Generation",
        "script": "deep_dive_generator.py",
        "description": "Create genuine deep dive: WHO did it, WHAT they did, WHY it worked, HOW beginners can apply it",
        "input": "output/content_ranked_{date}.json",
        "output": "output/deep_dive_{date}.json",
    },
    {
        "id": "select",
        "name": "Content Selection",
        "script": "content_selector.py",
        "description": "Select content for other sections (instant reward, tool, etc.)",
        "input": "output/content_ranked_{date}.json",
        "output": "output/content_selected_{date}.json",
    },
    {
        "id": "generate",
        "name": "Newsletter Assembly",
        "script": "newsletter_generator.py",
        "description": "Assemble full newsletter from deep dive + selected content",
        "input": "output/content_selected_{date}.json",
        "output": "output/newsletter_draft_{date}.md",
    },
    # === PHASE 3: POLISH FOR MAXIMUM IMPACT ===
    {
        "id": "hormozi",
        "name": "Hormozi Hook Review",
        "script": "copy_review_hormozi.py",
        "description": "Strengthen hooks using 100M Hooks framework",
        "input": "output/newsletter_draft_{date}.md",
        "output": "output/review_hormozi_{date}.json",
    },
    {
        "id": "schwartz",
        "name": "Schwartz Copy Review",
        "script": "copy_review_schwartz.py",
        "description": "Strengthen claims using Breakthrough Advertising principles",
        "input": "output/newsletter_draft_{date}.md",
        "output": "output/review_schwartz_{date}.json",
    },
    {
        "id": "products",
        "name": "Product Integration",
        "script": "product_integrator.py",
        "description": "Insert natural product mentions (2-3 per issue)",
        "input": "output/newsletter_draft_{date}.md",
        "output": "output/newsletter_integrated_{date}.md",
    },
    {
        "id": "edit",
        "name": "Final Editing",
        "script": "editor_agent.py",
        "description": "Reading level, jargon, spam triggers, voice check",
        "input": "output/newsletter_integrated_{date}.md",
        "output": "output/newsletter_final_{date}.md",
    },
    # === PHASE 4: HUMAN APPROVAL ===
    {
        "id": "review",
        "name": "Human Review Checkpoint",
        "script": None,  # Manual step
        "description": "Human reviews and approves final newsletter",
        "input": "output/newsletter_final_{date}.md",
        "output": "output/newsletter_approved_{date}.md",
    },
]


def get_step_index(step_id: str) -> int:
    """Get index of step by ID."""
    for i, step in enumerate(PIPELINE_STEPS):
        if step["id"] == step_id:
            return i
    raise ValueError(f"Unknown step: {step_id}")


def resolve_path(template: str, date_str: str) -> Path:
    """Resolve path template with date."""
    return Path(template.format(date=date_str))


def run_step(step: dict, date_str: str, dry_run: bool = False) -> tuple[bool, str]:
    """
    Run a single pipeline step.

    Args:
        step: Step definition dict
        date_str: Date string for file naming
        dry_run: If True, just show what would happen

    Returns:
        Tuple of (success, message)
    """
    step_id = step["id"]
    step_name = step["name"]
    script = step.get("script")

    print(f"\n{'=' * 60}")
    print(f"STEP: {step_name}")
    print(f"{'=' * 60}")

    if script is None:
        # Manual step
        if step_id == "review":
            input_path = resolve_path(step["input"], date_str)
            print(f"Manual review required: {input_path}")
            print("Please review the newsletter and approve before continuing.")
            return True, "Awaiting human review"
        return True, "Manual step"

    print(f"Script: execution/{script}")
    print(f"Description: {step['description']}")

    if step.get("input"):
        input_path = resolve_path(step["input"], date_str)
        print(f"Input: {input_path}")
        if not input_path.exists() and not dry_run:
            return False, f"Input file not found: {input_path}"

    if step.get("output"):
        output_path = resolve_path(step["output"], date_str)
        print(f"Output: {output_path}")

    if dry_run:
        print("[DRY RUN] Would execute this step")
        return True, "Dry run - skipped"

    # Build command
    script_path = Path("execution") / script
    if not script_path.exists():
        return False, f"Script not found: {script_path}"

    # Import and run the module
    try:
        import subprocess

        cmd = [sys.executable, str(script_path)]

        # Add input argument if applicable
        if step.get("input") and step_id not in ["aggregate"]:
            input_path = resolve_path(step["input"], date_str)
            if step_id == "filter":
                cmd.extend(["--input", str(input_path)])
            elif step_id in ["hormozi", "schwartz", "products", "edit"]:
                cmd.extend(["--file", str(input_path)])
            elif step_id == "prompt":
                cmd.extend(["--file", str(input_path), "--section", "deep_dive"])

        # Add output argument if applicable
        if step.get("output") and step_id in ["products", "edit"]:
            output_path = resolve_path(step["output"], date_str)
            cmd.extend(["--output", str(output_path)])

        print(f"\nRunning: {' '.join(cmd)}")
        print("-" * 40)

        result = subprocess.run(cmd, capture_output=False)

        if result.returncode != 0:
            return False, f"Script exited with code {result.returncode}"

        return True, "Completed successfully"

    except Exception as e:
        return False, f"Error running step: {e}"


def run_pipeline(
    start_from: Optional[str] = None,
    steps: Optional[list[str]] = None,
    dry_run: bool = False,
) -> dict:
    """
    Run the newsletter pipeline.

    Args:
        start_from: Step ID to start from (skips earlier steps)
        steps: Specific step IDs to run (runs only these)
        dry_run: If True, show what would happen without executing

    Returns:
        Dict with results for each step
    """
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"DTCNews Pipeline v{DOE_VERSION}")
    print(f"Date: {date_str}")
    print()

    # Determine which steps to run
    if steps:
        steps_to_run = [s for s in PIPELINE_STEPS if s["id"] in steps]
    elif start_from:
        start_idx = get_step_index(start_from)
        steps_to_run = PIPELINE_STEPS[start_idx:]
    else:
        steps_to_run = PIPELINE_STEPS

    print(f"Steps to run: {', '.join(s['id'] for s in steps_to_run)}")

    if dry_run:
        print("\n[DRY RUN MODE - No changes will be made]")

    results = {}

    for step in steps_to_run:
        success, message = run_step(step, date_str, dry_run)
        results[step["id"]] = {
            "success": success,
            "message": message,
        }

        if not success:
            print(f"\nPipeline stopped at step '{step['id']}': {message}")
            break

        # Human review is a stopping point
        if step["id"] == "review":
            print("\nPipeline paused for human review.")
            break

    return results


def show_pipeline_status():
    """Show current pipeline status and available steps."""
    print("DTCNews Pipeline Steps")
    print("=" * 60)
    print()

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for i, step in enumerate(PIPELINE_STEPS, 1):
        script_status = "Manual" if step.get("script") is None else "Automated"
        print(f"{i}. [{step['id']}] {step['name']}")
        print(f"   {step['description']}")
        print(f"   Type: {script_status}")

        # Check if output exists
        if step.get("output"):
            output_path = resolve_path(step["output"], date_str)
            if output_path.exists():
                print(f"   Output: {output_path} (EXISTS)")
            else:
                print(f"   Output: {output_path} (pending)")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="DTCNews unified newsletter pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run full pipeline
    python execution/dtcnews_pipeline.py
    
    # Start from filtering step (skip aggregation)
    python execution/dtcnews_pipeline.py --start-from filter
    
    # Run only specific steps
    python execution/dtcnews_pipeline.py --steps filter,select,generate
    
    # Show pipeline status
    python execution/dtcnews_pipeline.py --status
    
    # Dry run (show what would happen)
    python execution/dtcnews_pipeline.py --dry-run

Available steps:
    
    PHASE 1 - FIND WHAT'S CRUSHING IT:
    aggregate  - Fetch viral content from sources
    rank       - Rank by outlier + virality (find the BIGGEST things)
    
    PHASE 2 - CREATE GENUINE VALUE:
    deep_dive  - Generate deep dive (WHO, WHAT, WHY, HOW for beginners)
    select     - Select content for other sections
    generate   - Assemble full newsletter
    
    PHASE 3 - POLISH FOR IMPACT:
    hormozi    - Strengthen hooks (100M Hooks framework)
    schwartz   - Strengthen claims (Breakthrough Advertising)
    products   - Integrate product mentions naturally
    edit       - Final editing pass
    
    PHASE 4 - HUMAN APPROVAL:
    review     - Human review checkpoint
        """,
    )
    parser.add_argument(
        "--start-from",
        choices=[s["id"] for s in PIPELINE_STEPS],
        help="Step to start from (skips earlier steps)",
    )
    parser.add_argument(
        "--steps",
        help="Comma-separated list of specific steps to run",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show pipeline status and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without executing",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for generated files (default: output)",
    )
    args = parser.parse_args()

    # Ensure output directory exists
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    if args.status:
        show_pipeline_status()
        return 0

    # Parse steps if provided
    steps = None
    if args.steps:
        steps = [s.strip() for s in args.steps.split(",")]
        invalid = [s for s in steps if s not in [st["id"] for st in PIPELINE_STEPS]]
        if invalid:
            print(f"ERROR: Unknown steps: {', '.join(invalid)}")
            return 1

    # Run pipeline
    results = run_pipeline(
        start_from=args.start_from,
        steps=steps,
        dry_run=args.dry_run,
    )

    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)

    success_count = sum(1 for r in results.values() if r["success"])
    total_count = len(results)

    print(f"Steps completed: {success_count}/{total_count}")
    print()

    for step_id, result in results.items():
        status = "OK" if result["success"] else "FAILED"
        print(f"  [{status}] {step_id}: {result['message']}")

    # Check if all succeeded
    if all(r["success"] for r in results.values()):
        print("\nPipeline completed successfully.")
        return 0
    else:
        print("\nPipeline had failures. Check logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
