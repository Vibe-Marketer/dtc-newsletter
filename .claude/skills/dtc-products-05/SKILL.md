---
name: dtc-products-05
description: Insert natural product mentions into DTCNews newsletter content. Ensures 2-3 organic mentions per issue with proper placement and tone.
---

<objective>
Naturally weave product mentions into newsletter content so they feel like helpful recommendations, not ads. Each issue should have 2-3 mentions total that enhance rather than interrupt the reader experience.

Input: Newsletter draft content (full issue or individual sections)
Output: Content with integrated mentions + placement report showing what was added and where
</objective>

<products>
  <product id="starter-pack">
    <name>AI Store Starter Pack</name>
    <price>$19</price>
    <value_prop>GPTs and templates to launch first Shopify store in 7 days</value_prop>
    <url_slug>starter-pack</url_slug>
    
    <triggers>
      <!-- Words/phrases in content that make this product relevant -->
      <trigger>prompt</trigger>
      <trigger>AI</trigger>
      <trigger>GPT</trigger>
      <trigger>template</trigger>
      <trigger>store setup</trigger>
      <trigger>product descriptions</trigger>
      <trigger>getting started</trigger>
      <trigger>launch</trigger>
      <trigger>beginner</trigger>
      <trigger>first store</trigger>
    </triggers>
    
    <best_sections>
      <section priority="1">After Section 1 (Instant Reward)</section>
      <section priority="2">Section 4 (Prompt Drop)</section>
    </best_sections>
  </product>

  <product id="sales-sprint">
    <name>First 10 Sales Sprint</name>
    <price>$49-59</price>
    <value_prop>Get first 10 orders in 30 days using ads and AI</value_prop>
    <url_slug>first-10-sales</url_slug>
    
    <triggers>
      <trigger>traffic</trigger>
      <trigger>ads</trigger>
      <trigger>sales</trigger>
      <trigger>customers</trigger>
      <trigger>orders</trigger>
      <trigger>first sale</trigger>
      <trigger>Meta ads</trigger>
      <trigger>Facebook ads</trigger>
      <trigger>acquisition</trigger>
      <trigger>conversion</trigger>
      <trigger>getting customers</trigger>
    </triggers>
    
    <best_sections>
      <section priority="1">After Section 2 (Deep Dive)</section>
      <section priority="2">Section 5 (PS)</section>
    </best_sections>
  </product>

  <product id="vault">
    <name>Ecom Prompt and Template Vault</name>
    <price>$19/4 weeks</price>
    <value_prop>Monthly prompts, templates, and teardowns delivered weekly</value_prop>
    <url_slug>vault</url_slug>
    
    <triggers>
      <trigger>tool</trigger>
      <trigger>resource</trigger>
      <trigger>template</trigger>
      <trigger>weekly</trigger>
      <trigger>new this week</trigger>
      <trigger>swipe file</trigger>
      <trigger>teardown</trigger>
      <trigger>collection</trigger>
    </triggers>
    
    <best_sections>
      <section priority="1">Section 3 (Tool of Week)</section>
      <section priority="2">Section 4 (Prompt Drop)</section>
    </best_sections>
  </product>
</products>

<mention_templates>
  <product id="starter-pack">
    <soft>
      <template>This prompt is from our AI Store Starter Pack.</template>
      <template>We pulled this from the Starter Pack vault.</template>
      <template>One of 47 prompts in the Starter Pack.</template>
    </soft>
    <medium>
      <template>Get 47 more prompts like this in the Starter Pack ($19).</template>
      <template>The AI Store Starter Pack has the full collection of these ($19).</template>
      <template>Want more? The Starter Pack includes 47 GPTs and templates for $19.</template>
    </medium>
  </product>

  <product id="sales-sprint">
    <soft>
      <template>This exact strategy is in our First 10 Sales Sprint.</template>
      <template>We cover this in depth in the Sales Sprint.</template>
      <template>This is step 3 of the First 10 Sales playbook.</template>
    </soft>
    <medium>
      <template>Want the complete playbook? The Sprint walks you through it ($49).</template>
      <template>The First 10 Sales Sprint gives you the full system for $49.</template>
      <template>Get all 30 days mapped out in the Sales Sprint ($49).</template>
    </medium>
  </product>

  <product id="vault">
    <soft>
      <template>Vault members got this template yesterday.</template>
      <template>This dropped in the Vault last week.</template>
      <template>From this month's Vault collection.</template>
    </soft>
    <medium>
      <template>Join the Vault for weekly resources ($19/month).</template>
      <template>The Vault delivers fresh templates like this every week ($19/mo).</template>
      <template>Get a new batch every week in the Vault ($19/month).</template>
    </medium>
  </product>
</mention_templates>

<placement_rules>
  <rule type="forbidden">
    <location>Opening paragraph of any section</location>
    <reason>Always lead with pure value. Earn attention before mentioning products.</reason>
  </rule>

  <rule type="allowed" mention_level="soft">
    <location>After Section 1 (Instant Reward)</location>
    <condition>Only if content directly relates to a product</condition>
    <products>starter-pack, vault</products>
  </rule>

  <rule type="allowed" mention_level="soft,medium">
    <location>After Section 2 (Deep Dive)</location>
    <condition>When content covers strategy that a product expands on</condition>
    <products>sales-sprint, starter-pack</products>
  </rule>

  <rule type="allowed" mention_level="soft,medium">
    <location>Section 3 (Tool of Week)</location>
    <condition>Natural fit for Vault mentions</condition>
    <products>vault</products>
  </rule>

  <rule type="allowed" mention_level="soft,medium">
    <location>Section 4 (Prompt Drop)</location>
    <condition>Direct connection to prompt-based products</condition>
    <products>starter-pack, vault</products>
  </rule>

  <rule type="allowed" mention_level="medium">
    <location>Section 5 (PS)</location>
    <condition>Can be more direct here, reader is at the end</condition>
    <products>sales-sprint, starter-pack</products>
  </rule>

  <rule type="required">
    <location>Footer</location>
    <format>List all 3 products with one-line descriptions</format>
  </rule>

  <frequency>
    <total_per_issue min="2" max="3"/>
    <soft_mentions min="1" max="1"/>
    <medium_mentions min="1" max="2"/>
    <strong_mentions min="0" max="0"/>
  </frequency>
</placement_rules>

<process>
  <step order="1">
    <action>Scan content for trigger words</action>
    <details>
      Read through the newsletter draft and identify words/phrases that match product triggers.
      Note which sections contain which triggers.
    </details>
  </step>

  <step order="2">
    <action>Map triggers to products</action>
    <details>
      For each trigger found, identify which product(s) it relates to.
      Prioritize products where the content is a natural lead-in.
    </details>
  </step>

  <step order="3">
    <action>Identify insertion points</action>
    <details>
      Find paragraph breaks or natural transitions where a mention fits.
      Never insert mid-paragraph or mid-thought.
      Prefer end of sections or after delivering a complete piece of value.
    </details>
  </step>

  <step order="4">
    <action>Select mention intensity</action>
    <details>
      Use soft mention if the connection is tangential.
      Use medium mention if the content directly demonstrates what the product teaches.
      Never use strong/aggressive mentions.
    </details>
  </step>

  <step order="5">
    <action>Draft the mention</action>
    <details>
      Use templates as starting points but customize to match newsletter voice.
      Ensure the mention flows naturally from the preceding content.
      Read it aloud - if it sounds like an ad, rewrite it.
    </details>
  </step>

  <step order="6">
    <action>Check frequency limits</action>
    <details>
      Count total mentions. Must be 2-3.
      Count soft vs medium. Target: 1 soft, 1-2 medium.
      If over limit, remove the weakest connection.
    </details>
  </step>

  <step order="7">
    <action>Add footer block</action>
    <details>
      Ensure footer contains all 3 products in standard format.
      This does not count toward the 2-3 in-content mentions.
    </details>
  </step>

  <step order="8">
    <action>Generate placement report</action>
    <details>
      Document what was added, where, and why.
      Include the trigger that justified each mention.
    </details>
  </step>
</process>

<output_format>
  <integrated_content>
    The full newsletter content with mentions inserted.
    Mentions should be marked with HTML comments for easy review:
    &lt;!-- PRODUCT MENTION: [product-id] [soft/medium] --&gt;
  </integrated_content>

  <placement_report>
    ## Product Integration Report
    
    **Total Mentions:** [X] (target: 2-3)
    
    | Location | Product | Type | Trigger | Mention Text |
    |----------|---------|------|---------|--------------|
    | After Section 1 | starter-pack | soft | "prompt" | "This prompt is from..." |
    
    **Footer Products:** [Confirmed/Missing]
    
    **Notes:** [Any concerns about naturalness or fit]
  </placement_report>
</output_format>

<success_criteria>
  <criterion priority="critical">
    Mentions feel like helpful recommendations, not advertisements.
    Test: Read the section aloud. Does it sound like a friend sharing a resource?
  </criterion>

  <criterion priority="critical">
    No mention appears before value is delivered.
    Test: Is there at least one complete, useful paragraph before any mention?
  </criterion>

  <criterion priority="high">
    Frequency is within limits (2-3 total, 1 soft, 1-2 medium).
    Test: Count mentions. Footer doesn't count.
  </criterion>

  <criterion priority="high">
    Each mention has a clear content trigger justifying its placement.
    Test: Can you point to the specific word/phrase that made this product relevant?
  </criterion>

  <criterion priority="medium">
    Mention variety - not all mentions for the same product.
    Test: At least 2 different products mentioned (excluding footer).
  </criterion>

  <criterion priority="medium">
    Mentions are spread across sections, not clustered.
    Test: No two mentions within 3 paragraphs of each other.
  </criterion>
</success_criteria>

<footer_template>
---

**Level up your store:**

- **AI Store Starter Pack** - Launch your first Shopify store in 7 days with 47 GPTs and templates. [$19]
- **First 10 Sales Sprint** - Get your first 10 orders in 30 days with our ads + AI playbook. [$49]
- **Ecom Prompt and Template Vault** - Fresh prompts, templates, and teardowns delivered weekly. [$19/mo]
</footer_template>

<examples>
  <example type="good">
    <context>Section about writing product descriptions with AI</context>
    <content>
      ...and that's how you get Claude to write descriptions that actually convert.
      
      This prompt is from our AI Store Starter Pack - it's one of 47 we use daily.
    </content>
    <why_it_works>
      - Comes after complete value delivery
      - Direct connection to content (AI, prompts, descriptions)
      - Soft mention, doesn't interrupt
      - Sounds like sharing a resource, not selling
    </why_it_works>
  </example>

  <example type="good">
    <context>Deep dive on getting first customers</context>
    <content>
      ...once you have those 3 ad sets running, you're ready to scale.
      
      Want the complete playbook? The First 10 Sales Sprint walks you through all 30 days ($49).
    </content>
    <why_it_works>
      - Placed at section end after full strategy delivered
      - Medium mention appropriate for depth of content
      - Natural bridge: "want the complete playbook?"
      - Price included but not pushy
    </why_it_works>
  </example>

  <example type="bad">
    <context>Opening of any section</context>
    <content>
      Before we dive in, check out our AI Store Starter Pack for more prompts like this!
      
      Today we're covering...
    </content>
    <why_it_fails>
      - Mention before any value delivered
      - Interrupts reader before they're engaged
      - Feels like an ad, not a recommendation
      - Violates "pure value first" rule
    </why_it_fails>
  </example>

  <example type="bad">
    <context>Multiple mentions close together</context>
    <content>
      ...this template is from the Vault.
      
      Speaking of templates, the Starter Pack has 47 more.
      
      And if you want the full system, grab the Sales Sprint.
    </content>
    <why_it_fails>
      - Three mentions in rapid succession
      - Feels like a sales pitch, not content
      - Breaks trust with reader
      - Violates frequency and spacing rules
    </why_it_fails>
  </example>
</examples>
