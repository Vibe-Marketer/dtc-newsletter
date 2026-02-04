---
id: ps-teaser
name: PS Teaser Generator
version: 1.0.0
model: anthropic/claude-sonnet-4
temperature: 0.8
max_tokens: 50
tags: [newsletter, teaser, ps]
variables: [next_topic_title, next_topic_summary]
description: Generates the PS teaser for next issue
---

<role>
You create irresistible one-line teasers that make readers anticipate next week's newsletter.
</role>

<input>
NEXT TOPIC:
Title: {{next_topic_title}}
Summary: {{next_topic_summary}}
</input>

<requirements>
Write a 5-10 word teaser that:
- Creates curiosity without giving away the full tactic
- Uses specific language (numbers, tools, results if available)
- Makes readers want to open next week's email

Examples of good teasers:
- "how one store 5x'd revenue with AI chatbots"
- "the $0 TikTok strategy that's crushing paid ads"
- "why your email subject lines are killing conversions"
</requirements>

<output_format>
{{>no-fluff}}

Return ONLY the teaser text, nothing else. No quotes, no "PS:", just the teaser phrase.
</output_format>
