#!/usr/bin/env python3
"""
Prompt loader for DTCNews.
DOE-VERSION: 2026.02.04

Loads prompts from /prompts folder following PromptForge standards:
- YAML frontmatter for config
- XML tags for structure
- {{variable}} for substitution
- {{>partial}} for includes

Usage:
    from execution.prompt_loader import load_prompt, render_prompt

    # Load prompt config
    config = load_prompt("generation/section-1-hook")
    print(config.model, config.temperature)

    # Render with variables
    rendered = render_prompt("generation/section-1-hook", {
        "viral_edge_title": "...",
        "viral_edge_summary": "...",
    })
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

DOE_VERSION = "2026.02.04"

# Cache for loaded prompts and partials
_prompt_cache: dict[str, "PromptConfig"] = {}
_partial_cache: dict[str, str] = {}

# Paths
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
PARTIALS_DIR = PROMPTS_DIR / "_partials"


@dataclass
class PromptConfig:
    """Configuration from prompt frontmatter."""

    id: str
    model: str
    prompt: str  # The raw prompt content
    file_path: str

    # Optional fields
    name: Optional[str] = None
    version: str = "1.0.0"
    temperature: float = 0.7
    max_tokens: int = 1024
    tags: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    partials: list[str] = field(default_factory=list)
    output_format: str = "text"  # text, json, xml
    description: Optional[str] = None


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full file content with --- delimiters

    Returns:
        Tuple of (frontmatter dict, remaining content)
    """
    if not content.startswith("---"):
        return {}, content

    # Find the closing ---
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return {}, content

    frontmatter_text = content[3 : end_match.start() + 3]
    remaining = content[end_match.end() + 3 :]

    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, remaining.strip()


def load_partial(name: str) -> str:
    """
    Load a partial by name from _partials folder.

    Args:
        name: Partial name (without .md extension)

    Returns:
        Partial content
    """
    if name in _partial_cache:
        return _partial_cache[name]

    partial_path = PARTIALS_DIR / f"{name}.md"
    if not partial_path.exists():
        raise FileNotFoundError(f"Partial not found: {name}")

    content = partial_path.read_text().strip()
    _partial_cache[name] = content
    return content


def resolve_partials(content: str) -> str:
    """
    Resolve all {{>partial}} includes in content.

    Args:
        content: Prompt content with partial references

    Returns:
        Content with partials inlined
    """

    def replace_partial(match: re.Match) -> str:
        partial_name = match.group(1)
        try:
            return load_partial(partial_name)
        except FileNotFoundError:
            print(f"Warning: Partial not found: {partial_name}")
            return match.group(0)  # Leave unresolved

    return re.sub(r"\{\{>(\w[\w-]*)\}\}", replace_partial, content)


def load_prompt(prompt_path: str) -> PromptConfig:
    """
    Load a prompt file by path.

    Args:
        prompt_path: Path like "generation/section-1-hook" (no .md extension)

    Returns:
        PromptConfig with all settings and content

    Example:
        config = load_prompt("generation/section-1-hook")
        print(config.model)  # "anthropic/claude-sonnet-4"
    """
    # Normalize path
    normalized = prompt_path.replace(".md", "")

    # Check cache
    if normalized in _prompt_cache:
        return _prompt_cache[normalized]

    # Build full path
    full_path = PROMPTS_DIR / f"{normalized}.md"

    if not full_path.exists():
        raise FileNotFoundError(f"Prompt not found: {full_path}")

    # Read and parse
    file_content = full_path.read_text()
    frontmatter, content = parse_frontmatter(file_content)

    # Validate required fields
    if "id" not in frontmatter:
        raise ValueError(f"Prompt missing required field 'id': {full_path}")
    if "model" not in frontmatter:
        raise ValueError(f"Prompt missing required field 'model': {full_path}")

    # Build config
    config = PromptConfig(
        id=frontmatter["id"],
        model=frontmatter["model"],
        prompt=content,
        file_path=str(full_path),
        name=frontmatter.get("name"),
        version=frontmatter.get("version", "1.0.0"),
        temperature=frontmatter.get("temperature", 0.7),
        max_tokens=frontmatter.get("max_tokens", 1024),
        tags=frontmatter.get("tags", []),
        variables=frontmatter.get("variables", []),
        partials=frontmatter.get("partials", []),
        output_format=frontmatter.get("output_format", "text"),
        description=frontmatter.get("description"),
    )

    # Cache and return
    _prompt_cache[normalized] = config
    return config


def render_prompt(prompt_path: str, variables: Optional[dict[str, str]] = None) -> str:
    """
    Render a prompt with partials resolved and variables substituted.

    Args:
        prompt_path: Path like "generation/section-1-hook"
        variables: Dict of variable values to substitute

    Returns:
        Rendered prompt string ready to send to LLM

    Example:
        rendered = render_prompt("generation/section-1-hook", {
            "viral_edge_title": "How to 10x your ads",
            "deep_dive_headline": "The $50K secret",
        })
    """
    config = load_prompt(prompt_path)
    variables = variables or {}

    # 1. Resolve partials first
    rendered = resolve_partials(config.prompt)

    # 2. Then substitute variables
    for key, value in variables.items():
        rendered = re.sub(rf"\{{\{{{key}\}}\}}", str(value), rendered)

    # 3. Warn about unsubstituted variables (not partials)
    unsubstituted = re.findall(r"\{\{(?!>)[^}]+\}\}", rendered)
    if unsubstituted:
        print(f"Warning: Unsubstituted variables: {', '.join(unsubstituted)}")

    return rendered


def list_prompts(directory: Optional[str] = None) -> list[PromptConfig]:
    """
    List all prompts in a directory.

    Args:
        directory: Folder name like "generation" or None for all

    Returns:
        List of PromptConfig objects
    """
    if directory:
        search_dir = PROMPTS_DIR / directory
    else:
        search_dir = PROMPTS_DIR

    if not search_dir.exists():
        return []

    prompts = []
    for md_file in search_dir.rglob("*.md"):
        # Skip partials
        if "_partials" in str(md_file):
            continue

        # Get relative path
        rel_path = md_file.relative_to(PROMPTS_DIR)
        prompt_path = str(rel_path).replace(".md", "")

        try:
            prompts.append(load_prompt(prompt_path))
        except (ValueError, FileNotFoundError) as e:
            print(f"Warning: Skipping {prompt_path}: {e}")

    return prompts


def list_partials() -> list[str]:
    """List all available partials."""
    if not PARTIALS_DIR.exists():
        return []

    return [f.stem for f in PARTIALS_DIR.glob("*.md")]


def clear_cache():
    """Clear the prompt and partial caches."""
    _prompt_cache.clear()
    _partial_cache.clear()


if __name__ == "__main__":
    # Quick test
    print(f"[prompt_loader] v{DOE_VERSION}")
    print(f"\nPrompts directory: {PROMPTS_DIR}")
    print(f"Partials directory: {PARTIALS_DIR}")

    print(f"\nAvailable partials: {list_partials()}")

    prompts = list_prompts()
    print(f"\nLoaded {len(prompts)} prompts:")
    for p in prompts:
        print(f"  - {p.id} ({p.file_path})")
