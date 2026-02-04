# Prompts

This folder contains all AI prompts used by the DTCNews newsletter system, following [PromptForge standards](https://github.com/prompt-forge).

## Folder Structure

```
prompts/
├── _partials/          # Reusable prompt components
│   ├── no-fluff.md     # Remove preamble/postamble
│   ├── json-strict.md  # Force valid JSON output
│   ├── dtc-voice.md    # DTC newsletter voice/tone
│   └── beginner-friendly.md
│
├── generation/         # Prompts that create content
│   ├── section-1-hook.md
│   ├── section-4-prompt.md
│   ├── section-5-action.md
│   ├── subject-preview.md
│   └── ps-teaser.md
│
├── extraction/         # Prompts that extract data (future)
├── analysis/           # Prompts that evaluate (future)
└── README.md
```

## Prompt Format

Each prompt is a `.md` file with YAML frontmatter and XML-tagged content:

```markdown
---
id: my-prompt
name: Human Readable Name
version: 1.0.0
model: anthropic/claude-sonnet-4
temperature: 0.7
max_tokens: 500
tags: [category, type]
variables: [input_var_1, input_var_2]
output_format: text  # or json, xml
description: What this prompt does
---

<role>
Who the AI should be
</role>

{{>partial_name}}

<input>
{{input_var_1}}
{{input_var_2}}
</input>

<output_format>
How to format the response
</output_format>
```

## Usage in Python

```python
from execution.prompt_loader import load_prompt, render_prompt

# Load prompt config
config = load_prompt("generation/section-1-hook")
print(config.model)       # anthropic/claude-sonnet-4
print(config.temperature) # 0.7
print(config.variables)   # ['viral_edge_title', ...]

# Render with variables
rendered = render_prompt("generation/section-1-hook", {
    "viral_edge_title": "How to 10x your ROAS",
    "viral_edge_summary": "A dropshipper shared...",
    "viral_edge_results": "$50k/month",
    "deep_dive_headline": "The Day-1 ROAS Secret",
    "deep_dive_key_insight": "Speed beats precision",
})

# Use with ClaudeClient
from execution.claude_client import ClaudeClient
client = ClaudeClient()
result = client.generate(rendered, max_tokens=config.max_tokens)
```

## Partials

Partials are reusable chunks included with `{{>partial_name}}`:

| Partial | Purpose |
|---------|---------|
| `no-fluff` | Removes preamble/postamble from outputs |
| `json-strict` | Forces valid JSON-only output |
| `dtc-voice` | DTC newsletter voice and tone |
| `beginner-friendly` | Scales tactics for beginners |

## Adding New Prompts

1. Create `prompts/{category}/your-prompt.md`
2. Add YAML frontmatter with required fields (`id`, `model`)
3. Use XML tags for structure
4. Use `{{variable}}` for inputs
5. Use `{{>partial}}` for reusable chunks
6. Test with `python execution/prompt_loader.py`

## Versioning

When changing a prompt significantly:
1. Bump the `version` in frontmatter
2. Document what changed in commit message
3. Consider A/B testing both versions
