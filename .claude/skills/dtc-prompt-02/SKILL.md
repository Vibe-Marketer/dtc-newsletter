---
name: dtc-prompt-02
description: Extract or create copy-paste ChatGPT prompts from tactical content. Use when generating the "Prompt Drop" section for DTCNews newsletter issues.
---

<objective>
Transform tactical Deep Dive content into immediately executable ChatGPT prompts for the "Prompt Drop" newsletter section. Every prompt must be copy-paste ready for a complete beginner with zero editing required beyond filling one bracketed variable.
</objective>

<context>
DTCNews readers are busy ecommerce operators who want AI shortcuts, not AI education. The Prompt Drop section delivers a single, high-value prompt that:
- Executes the issue's main tactic automatically
- Produces usable output in under 60 seconds
- Requires minimal customization (one variable only)
- Demonstrates immediate ROI from reading the newsletter

This is often the most-saved section of each issue. Quality matters more than complexity.
</context>

<process>
<step name="analyze_content">
Read the Deep Dive tactical content and identify:
- The core action the reader should take
- What output would save them the most time
- Whether an existing prompt is embedded in the content
</step>

<step name="extract_or_create">
IF the content contains an existing prompt:
- Extract it verbatim
- Verify it meets quality requirements
- Simplify if over 150 words

IF no prompt exists:
- Identify the single most valuable automation
- Write a prompt that produces that output
- Include specific output format instructions
</step>

<step name="add_single_variable">
Insert exactly ONE bracketed variable for customization:
- [YOUR PRODUCT] - for product-specific prompts
- [YOUR NICHE] - for market/audience prompts  
- [YOUR OFFER] - for pricing/promotion prompts
- [YOUR BRAND] - for voice/positioning prompts

Never use multiple variables. Beginners get overwhelmed.
</step>

<step name="specify_output">
Every prompt must tell ChatGPT exactly what to produce:
- "Give me 5 options..."
- "Create a table with..."
- "Write a single paragraph..."
- "List the top 3..."

Vague prompts produce vague results.
</step>

<step name="validate">
Run through success criteria checklist before finalizing.
</step>
</process>

<quality_requirements>
<requirement name="word_limit">
Maximum 150 words total. Shorter is better. Most great prompts are 50-80 words.
</requirement>

<requirement name="single_variable">
Exactly ONE bracketed variable. Not zero, not two. One.
</requirement>

<requirement name="immediate_utility">
Output must be directly usable - not a plan, not suggestions, not education. Something they can copy into their store, ads, or emails today.
</requirement>

<requirement name="output_specification">
Prompt must specify exact output format (number of items, structure, length).
</requirement>

<requirement name="tactic_alignment">
Prompt must execute the Deep Dive's core tactic, not a tangentially related task.
</requirement>

<requirement name="beginner_ready">
A person who has never used ChatGPT could paste this and get useful results. No assumed knowledge.
</requirement>
</quality_requirements>

<output_format>
Return a JSON object with these exact fields:

```json
{
  "prompt_text": "The complete, copy-paste ready prompt under 150 words",
  "what_it_produces": "One sentence describing the output",
  "how_to_customize": "Instructions for the bracketed variable",
  "advanced_variation": "Optional enhancement for power users"
}
```

Example output:

```json
{
  "prompt_text": "I sell [YOUR PRODUCT]. Write 5 unique product descriptions for my website. Each should be 2-3 sentences, highlight a different benefit, and end with a soft call-to-action. Make them sound confident but not salesy.",
  "what_it_produces": "5 ready-to-use product descriptions with different angles",
  "how_to_customize": "Replace [YOUR PRODUCT] with your product name and one key feature (e.g., 'organic cotton t-shirts' or 'wireless earbuds with 40-hour battery')",
  "advanced_variation": "Add 'Write in the voice of [brand you admire]' for brand-specific tone"
}
```
</output_format>

<examples>
<example name="product_research">
<input_tactic>
Deep Dive about validating product ideas using Amazon reviews before sourcing.
</input_tactic>
<output>
{
  "prompt_text": "I'm considering selling [YOUR PRODUCT]. Analyze what customers love and hate about this product based on common Amazon review patterns. Give me: 1) Top 3 features customers rave about, 2) Top 3 complaints to avoid, 3) One product improvement that would beat competitors. Format as a simple list.",
  "what_it_produces": "Product validation summary with competitive advantage angle",
  "how_to_customize": "Replace [YOUR PRODUCT] with the exact product you're researching (e.g., 'silicone kitchen spatulas' or 'yoga knee pads')",
  "advanced_variation": "Add 'Also suggest 3 bundle ideas based on frequently-bought-together patterns'"
}
</output>
</example>

<example name="ad_copy">
<input_tactic>
Deep Dive about writing curiosity-driven Facebook ad headlines.
</input_tactic>
<output>
{
  "prompt_text": "Write 10 Facebook ad headlines for [YOUR PRODUCT]. Each headline should create curiosity without clickbait. Use these patterns: question headlines, 'how I...' headlines, counterintuitive statements, and specific number claims. Keep each under 10 words.",
  "what_it_produces": "10 scroll-stopping headlines ready to test in ads",
  "how_to_customize": "Replace [YOUR PRODUCT] with your product and its main benefit (e.g., 'posture corrector that eliminates back pain')",
  "advanced_variation": "Add 'Include one headline specifically targeting [competitor product] users'"
}
</output>
</example>

<example name="email_subject">
<input_tactic>
Deep Dive about re-engaging lapsed customers with email.
</input_tactic>
<output>
{
  "prompt_text": "Write 7 email subject lines to win back customers who haven't purchased from [YOUR BRAND] in 90+ days. Mix these approaches: curiosity, FOMO, direct offer, personal check-in, and 'we miss you' angles. Keep each under 50 characters. No spam trigger words.",
  "what_it_produces": "7 win-back email subject lines ready to A/B test",
  "how_to_customize": "Replace [YOUR BRAND] with your store name",
  "advanced_variation": "Add 'Include preview text for each subject line that increases open rates'"
}
</output>
</example>
</examples>

<success_criteria>
Before finalizing any prompt, verify ALL of these:

<checklist>
- [ ] Under 150 words (count them)
- [ ] Exactly one [BRACKETED] variable
- [ ] Output format is specified (number, structure, length)
- [ ] A beginner could use this without any editing beyond the variable
- [ ] Output is immediately usable (not educational or advisory)
- [ ] Prompt directly executes the Deep Dive's main tactic
- [ ] No jargon or assumed ChatGPT knowledge
- [ ] Tone is direct and confident, not apologetic or hedging
</checklist>

Common failures to avoid:
- Prompts that produce "ideas" instead of finished copy
- Multiple variables that require research to fill
- Missing output specifications (user gets wall of text)
- Prompts about the tactic instead of executing the tactic
</success_criteria>

<edge_cases>
<case name="no_clear_automation">
If the Deep Dive tactic doesn't lend itself to AI automation (e.g., "negotiate better shipping rates"), create a prompt for related prep work like "Write a negotiation script for..." or "List my leverage points for..."
</case>

<case name="existing_prompt_too_long">
If extracting an existing prompt over 150 words, cut:
1. Preamble/context (ChatGPT doesn't need it)
2. Multiple examples (one is enough)
3. Redundant instructions
4. Politeness ("please", "thank you", "I'd like you to")
</case>

<case name="highly_technical_tactic">
For technical tactics (tracking pixels, code snippets), pivot to a prompt that explains implementation: "Write step-by-step instructions for setting up [TECHNICAL THING] on a Shopify store. Assume I'm not technical. Include what to click and where."
</case>
</edge_cases>
