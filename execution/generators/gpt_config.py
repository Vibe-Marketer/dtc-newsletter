"""
GPT Configuration Generator for the Product Factory.

Generates Custom GPT configuration packages including:
- gpt_config.json: Complete configuration for ChatGPT
- INSTRUCTIONS.md: Full system prompt/instructions
- SETUP_GUIDE.md: Step-by-step guide for creating the GPT
- conversation_starters.txt: 4 starter prompts
"""

import json
from typing import Optional

from .base_generator import BaseGenerator, GeneratedProduct, ProductSpec

# Prompt for Claude to generate GPT configuration
GPT_CONFIG_PROMPT = """You are creating a Custom GPT configuration for ChatGPT.

Given the following product specification:
- Problem being solved: {problem}
- Solution name: {solution_name}
- Target audience: {target_audience}
- Key benefits: {key_benefits}

Generate a complete GPT configuration as JSON with the following structure:

{{
    "name": "<GPT name, under 25 characters>",
    "description": "<Short description of what this GPT does, under 300 characters>",
    "instructions": "<Detailed system prompt, 500-2000 words. This is the most important part. Include:
        - Clear role definition
        - Specific behaviors and tone
        - Step-by-step guidance for common tasks
        - Constraints and limitations
        - Output format expectations
        - Examples of ideal responses>",
    "conversation_starters": [
        "<Starter 1: Most common use case>",
        "<Starter 2: Quick win scenario>",
        "<Starter 3: Advanced use case>",
        "<Starter 4: Exploratory question>"
    ],
    "capabilities": {{
        "web_browsing": <true if GPT needs current info, false otherwise>,
        "dall_e": <true if GPT creates images, false otherwise>,
        "code_interpreter": <true if GPT analyzes data/code, false otherwise>
    }}
}}

Important:
1. The name MUST be under 25 characters
2. The description MUST be under 300 characters
3. Instructions should be 500-2000 words of detailed guidance
4. Exactly 4 conversation starters
5. Return ONLY valid JSON, no markdown code blocks

Generate the configuration now:"""


# Template for setup guide
SETUP_GUIDE_TEMPLATE = """# How to Create Your Custom GPT: {gpt_name}

This guide walks you through creating your Custom GPT in ChatGPT.

## Prerequisites

- ChatGPT Plus or Team subscription (Custom GPTs require paid plans)
- Access to chat.openai.com

## Step 1: Access the GPT Builder

1. Go to [chat.openai.com](https://chat.openai.com)
2. Click your profile icon in the bottom-left
3. Select "My GPTs"
4. Click "+ Create a GPT" or "Create"

## Step 2: Configure Basic Settings

1. **Name**: Enter the GPT name from `gpt_config.json`
   - Copy the `name` field value
   - Paste into the "Name" field in GPT Builder

2. **Description**: Enter the description
   - Copy the `description` field value
   - Paste into the "Description" field

3. **Profile Picture** (optional):
   - Upload a custom image or use DALL-E to generate one
   - Recommended: 512x512 pixels

## Step 3: Add Instructions

This is the most important step:

1. Click the "Configure" tab in GPT Builder
2. Find the "Instructions" text area
3. Open `INSTRUCTIONS.md` from this package
4. Copy the ENTIRE contents
5. Paste into the Instructions field

**Tip**: The instructions define how your GPT behaves. Don't skip or shorten them.

## Step 4: Add Conversation Starters

1. Scroll to "Conversation starters" section
2. Open `conversation_starters.txt`
3. Add each line as a separate starter
4. These appear as quick-start buttons for users

## Step 5: Configure Capabilities

Based on your `gpt_config.json` capabilities:

1. **Web Browsing**: Toggle ON if your config shows `"web_browsing": true`
   - Allows GPT to search the internet for current information

2. **DALL-E Image Generation**: Toggle ON if `"dall_e": true`
   - Allows GPT to create images

3. **Code Interpreter**: Toggle ON if `"code_interpreter": true`
   - Allows GPT to run Python code and analyze files

## Step 6: Add Knowledge Files (Optional)

If you have supplementary documents:

1. Click "Upload files" under Knowledge
2. Add PDFs, docs, or text files the GPT should reference
3. Files are searchable by the GPT during conversations

## Step 7: Test Your GPT

Before publishing:

1. Click "Preview" in the top-right
2. Try each conversation starter
3. Test edge cases and common questions
4. Verify the GPT follows your instructions

## Step 8: Save and Publish

1. Click "Create" or "Update" to save
2. Choose visibility:
   - **Only me**: Private, only you can use it
   - **Anyone with a link**: Share via link
   - **Public**: Listed in GPT Store (requires review)

## Troubleshooting

**GPT doesn't follow instructions well:**
- Ensure full instructions were pasted (check for truncation)
- Add more specific examples in the instructions
- Use phrases like "You MUST" and "NEVER" for critical rules

**Responses are too short/long:**
- Add explicit length guidance in instructions
- Example: "Provide responses of 200-400 words unless asked for more detail"

**GPT goes off-topic:**
- Add constraints in instructions
- Example: "If asked about topics outside [domain], politely redirect"

## File Reference

| File | Purpose |
|------|---------|
| `gpt_config.json` | Complete configuration in JSON format |
| `INSTRUCTIONS.md` | Full instructions to paste into GPT Builder |
| `SETUP_GUIDE.md` | This guide |
| `conversation_starters.txt` | Pre-made conversation starters |

---

*Generated by Product Factory*
"""


class GptConfigGenerator(BaseGenerator):
    """
    Generator for Custom GPT configuration packages.

    Creates complete configuration packages for creating Custom GPTs in ChatGPT,
    including instructions, setup guide, and conversation starters.
    """

    def __init__(self, claude_client=None):
        """
        Initialize the GPT config generator.

        Args:
            claude_client: Optional Claude API client for AI-assisted generation.
        """
        super().__init__(claude_client)

    def get_product_type(self) -> str:
        """Return the product type for GPT configs."""
        return "gpt_config"

    def generate(self, spec: ProductSpec) -> GeneratedProduct:
        """
        Generate a GPT configuration package.

        Args:
            spec: ProductSpec with problem, solution_name, target_audience, key_benefits

        Returns:
            GeneratedProduct with gpt_config.json, INSTRUCTIONS.md,
            SETUP_GUIDE.md, and conversation_starters.txt
        """
        # Format the prompt with spec values
        prompt = GPT_CONFIG_PROMPT.format(
            problem=spec.problem,
            solution_name=spec.solution_name,
            target_audience=spec.target_audience,
            key_benefits=", ".join(spec.key_benefits),
        )

        # Generate GPT config using Claude
        if self.claude_client:
            response = self.claude_client.generate(prompt)
            gpt_config = self._parse_gpt_config(response)
        else:
            # Fallback for testing without Claude client
            gpt_config = self._generate_fallback_config(spec)

        # Create the files
        files = {}

        # 1. gpt_config.json - Complete configuration
        files["gpt_config.json"] = json.dumps(gpt_config, indent=2).encode("utf-8")

        # 2. INSTRUCTIONS.md - Full instructions in markdown
        instructions_md = self._format_instructions_md(gpt_config)
        files["INSTRUCTIONS.md"] = instructions_md.encode("utf-8")

        # 3. SETUP_GUIDE.md - Step-by-step setup guide
        setup_guide = self._generate_setup_guide(
            gpt_config.get("name", spec.solution_name)
        )
        files["SETUP_GUIDE.md"] = setup_guide.encode("utf-8")

        # 4. conversation_starters.txt - One per line
        starters = gpt_config.get("conversation_starters", [])
        starters_txt = "\n".join(starters)
        files["conversation_starters.txt"] = starters_txt.encode("utf-8")

        # Create manifest
        manifest = self._create_manifest(spec, list(files.keys()))

        # Add GPT-specific metadata to manifest
        manifest["gpt_name"] = gpt_config.get("name", "")
        manifest["capabilities"] = gpt_config.get("capabilities", {})

        return GeneratedProduct(files=files, manifest=manifest)

    def validate(self, product: GeneratedProduct) -> bool:
        """
        Validate a generated GPT configuration package.

        Checks:
        - gpt_config.json exists and is valid JSON
        - name is under 25 characters
        - description is under 300 characters
        - instructions is 500+ words
        - exactly 4 conversation starters

        Args:
            product: GeneratedProduct to validate

        Returns:
            True if valid, False otherwise
        """
        # Check required files exist
        required_files = [
            "gpt_config.json",
            "INSTRUCTIONS.md",
            "SETUP_GUIDE.md",
            "conversation_starters.txt",
        ]
        for filename in required_files:
            if filename not in product.files:
                return False

        # Parse and validate gpt_config.json
        try:
            config_bytes = product.files["gpt_config.json"]
            config = json.loads(config_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False

        # Validate name length (under 25 chars)
        name = config.get("name", "")
        if not name or len(name) > 25:
            return False

        # Validate description length (under 300 chars)
        description = config.get("description", "")
        if not description or len(description) > 300:
            return False

        # Validate instructions word count (500+ words)
        instructions = config.get("instructions", "")
        word_count = len(instructions.split())
        if word_count < 500:
            return False

        # Validate exactly 4 conversation starters
        starters = config.get("conversation_starters", [])
        if len(starters) != 4:
            return False

        return True

    def _generate_setup_guide(self, gpt_name: str) -> str:
        """
        Generate the setup guide with the GPT name.

        Args:
            gpt_name: Name of the GPT being created

        Returns:
            Formatted setup guide markdown
        """
        return SETUP_GUIDE_TEMPLATE.format(gpt_name=gpt_name)

    def _format_instructions_md(self, gpt_config: dict) -> str:
        """
        Format the instructions as markdown for easy copying.

        Args:
            gpt_config: Parsed GPT configuration

        Returns:
            Markdown formatted instructions
        """
        name = gpt_config.get("name", "Custom GPT")
        instructions = gpt_config.get("instructions", "")
        description = gpt_config.get("description", "")

        return f"""# {name} - Instructions

## Description

{description}

## System Instructions

Copy everything below this line into the GPT Builder "Instructions" field:

---

{instructions}

---

*End of instructions*
"""

    def _parse_gpt_config(self, response: str) -> dict:
        """
        Parse Claude's response into a GPT config dict.

        Args:
            response: Raw response from Claude

        Returns:
            Parsed GPT configuration dict
        """
        # Try to parse as JSON directly
        try:
            # Handle potential markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```"):
                # Extract content between code blocks
                lines = clean_response.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith("```") and not in_block:
                        in_block = True
                        continue
                    elif line.startswith("```") and in_block:
                        break
                    elif in_block:
                        json_lines.append(line)
                clean_response = "\n".join(json_lines)

            return json.loads(clean_response)
        except json.JSONDecodeError:
            # Return empty config if parsing fails
            return {
                "name": "GPT",
                "description": "A custom GPT",
                "instructions": "",
                "conversation_starters": [],
                "capabilities": {
                    "web_browsing": False,
                    "dall_e": False,
                    "code_interpreter": False,
                },
            }

    def _generate_fallback_config(self, spec: ProductSpec) -> dict:
        """
        Generate a fallback config when Claude client is not available.

        Used for testing and development.

        Args:
            spec: ProductSpec to generate config from

        Returns:
            Basic GPT configuration dict
        """
        # Generate instructions based on spec
        benefits_text = "\n".join(f"- {benefit}" for benefit in spec.key_benefits)

        instructions = f"""You are {spec.solution_name}, a specialized assistant designed to help {spec.target_audience} with {spec.problem}.

## Your Role

You are an expert in solving the following problem:
{spec.problem}

Your goal is to provide practical, actionable advice that helps users achieve these benefits:
{benefits_text}

## How to Respond

1. **Be Specific**: Give concrete, actionable advice rather than vague suggestions
2. **Be Concise**: Respect users' time while being thorough
3. **Be Supportive**: Encourage users and acknowledge their challenges
4. **Ask Questions**: When needed, ask clarifying questions to give better advice

## Conversation Guidelines

- Start by understanding the user's specific situation
- Break complex problems into manageable steps
- Provide examples when helpful
- Offer alternatives when the first solution doesn't fit
- Summarize key takeaways at the end of longer conversations

## Constraints

- Stay focused on {spec.problem}
- If asked about unrelated topics, politely redirect to your area of expertise
- Don't make up information - be honest about limitations
- Protect user privacy - don't ask for unnecessary personal details

## Output Format

- Use bullet points for lists
- Use numbered steps for processes
- Use headers to organize longer responses
- Keep paragraphs short (2-3 sentences)

## Example Interaction

User: "I'm struggling with [aspect of {spec.problem}]"

Good Response:
"I understand that can be frustrating. Let me help you with that.

Here's what I recommend:
1. [First step]
2. [Second step]
3. [Third step]

Would you like me to go deeper into any of these steps?"

Remember: Your purpose is to make {spec.target_audience} more successful by solving {spec.problem}."""

        # Truncate name to 25 chars if needed
        name = (
            spec.solution_name[:25]
            if len(spec.solution_name) > 25
            else spec.solution_name
        )

        # Generate description under 300 chars
        description = f"Helps {spec.target_audience} solve {spec.problem}. Get actionable advice and step-by-step guidance."
        if len(description) > 300:
            description = description[:297] + "..."

        return {
            "name": name,
            "description": description,
            "instructions": instructions,
            "conversation_starters": [
                f"Help me with {spec.problem}",
                "What's the first step I should take?",
                "Can you give me a detailed strategy?",
                "What mistakes should I avoid?",
            ],
            "capabilities": {
                "web_browsing": False,
                "dall_e": False,
                "code_interpreter": False,
            },
        }
