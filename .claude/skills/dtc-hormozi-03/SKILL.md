---
name: dtc-hormozi-03
description: Review newsletter copy using Alex Hormozi's 100M Hooks framework. Use to strengthen subject lines, hooks, and opening content for maximum engagement.
---

<objective>
Apply Alex Hormozi's 100M Hooks framework to review and improve newsletter copy.
Analyze subject lines and opening hooks against proven patterns, then provide
scored feedback with concrete rewrites using the 121-hook database.
</objective>

<hormozi_framework>

<hook_components>
Every effective hook has two parts:

1. CALL OUT - Gets the prospect to say "This is for me"
   - Identifies the specific audience
   - Makes them feel seen/understood
   - Creates instant recognition

2. CONDITION FOR VALUE - Why they should consume this content
   - What they'll get from reading
   - The transformation or benefit
   - The curiosity gap or tension
</hook_components>

<hook_types>
Use these 9 proven hook types when reviewing and rewriting:

LABEL - Calls out specific audience directly
- Pattern: "[Audience], I have [something] for you"
- Example: "Local business owners, I have a gift for you"
- Best for: Tight niche targeting, making readers self-select

QUESTION - Engages by asking what they want
- Pattern: "Would you [desirable thing]?" / "Do you ever [pain point]?"
- Example: "Would you pay $1,000 to have the business of your dreams in 30 days?"
- Best for: Qualifying interest, creating agreement

CONDITIONAL - Speaks to specific situations
- Pattern: "If you're [situation], then [hook]"
- Example: "If you're working all the time and your business isn't growing..."
- Best for: Addressing specific pain points, segmentation

COMMAND - Direct instruction that implies value
- Pattern: "Read this if..." / "Do this..." / "Stop [bad thing]"
- Example: "Read this if you want to win"
- Best for: Urgency, authority positioning, direct response

STATEMENT - Bold claim or truth bomb
- Pattern: "The [thing] that [result]" / "How to [result]"
- Example: "The smartest thing you can do today"
- Best for: Thought leadership, curiosity, authority

STORY - Opens with narrative tension
- Pattern: "[Person] just [achieved result]" / "When I [situation]..."
- Example: "My first nine businesses didn't really amount to anything. Nine."
- Best for: Relatability, proof, emotional connection

PARADOX - Unexpected contradiction that demands explanation
- Pattern: "How a [unlikely person] [achieved result]"
- Example: "How a bald-headed barber saved my hair"
- Best for: Maximum curiosity, pattern interrupts

LIST - Promise of multiple value items
- Pattern: "[Number] ways to [result]" / "[Number] [things] that [outcome]"
- Example: "3 hacks to make life suck less"
- Best for: Scannable value, clear expectations

CURIOSITY - Creates information gap that must be closed
- Pattern: Incomplete thought or unexpected statement
- Example: "The rumors are true..." / "Btw... (I have a favor to ask)"
- Best for: Open rates, stopping the scroll
</hook_types>

<top_performers>
Reference these proven hooks (from Hormozi's top 20):

1. "Real quick question..." (question - ranked #1)
2. "You might be wondering why I just caught a banana..." (curiosity - #2)
3. "That's weird... I don't see your name on the invite list?" (curiosity - #3)
4. "The rumors are true..." (statement - #4)
5. "Would you pay $1,000 to have the business of your dreams?" (question - #5)
6. "$4,664 per month... That's what Kyle... the last person on the leaderboard..." (proof - #6)
7. "Which would you rather be? The guy pushing the boulder..." (question - #7)
8. "Throw out your morning routine and switch to a money routine" (command - #8)
9. "Local business owners, I have a gift for you" (label - #10)
10. "I have a confession..." (confession - #11)

Full database: data/hormozi_hooks_db.json
Quick reference: references/hormozi-hooks-db.md
</top_performers>

</hormozi_framework>

<review_process>

<step_1_extract>
Extract the hooks from the newsletter draft:
- Subject line (primary hook)
- Preview text / preheader
- Opening sentence/paragraph (secondary hook)
- Any subheads that function as hooks
</step_1_extract>

<step_2_analyze>
For each extracted hook, analyze:
1. Does it have a clear CALL OUT? (Who is this for?)
2. Does it have a CONDITION FOR VALUE? (Why consume?)
3. What hook TYPE is being used?
4. How does it compare to top performers?
</step_2_analyze>

<step_3_score>
Score each hook 0-10 using the criteria below
</step_3_score>

<step_4_rewrite>
Generate 3-5 alternative versions using DIFFERENT hook types:
- Keep the core message/offer intact
- Adapt proven patterns from the database
- Match the newsletter's voice/tone
</step_4_rewrite>

<step_5_recommend>
Provide final recommendation:
- Best rewrite option with rationale
- Quick wins (small tweaks to existing)
- Overall hook strategy notes
</step_5_recommend>

</review_process>

<scoring_criteria>

<dimension_1_attention>
ATTENTION GRAB (0-10): Does it stop the scroll in under 3 seconds?

0-2: Generic, could be any newsletter
3-4: Mildly interesting but skippable  
5-6: Would make some people pause
7-8: Strong pattern interrupt, curiosity gap
9-10: Irresistible - must click/read
</dimension_1_attention>

<dimension_2_targeting>
TARGETING CLARITY (0-10): Is it clear who this is for?

0-2: No audience signal
3-4: Vague audience implied
5-6: Audience somewhat clear
7-8: Specific audience, they'd self-identify
9-10: Laser-targeted, readers say "this is for ME"
</dimension_2_targeting>

<dimension_3_value>
VALUE PROMISE (0-10): Is the benefit of reading clear?

0-2: No reason to read
3-4: Weak or unclear benefit
5-6: Some value implied
7-8: Clear transformation or insight promised
9-10: Compelling, specific value that demands attention
</dimension_3_value>

<overall_score>
OVERALL HOOK STRENGTH = (Attention + Targeting + Value) / 3

0-3: Weak - needs complete rewrite
4-5: Below average - significant improvements needed
6-7: Average - room for optimization
8-9: Strong - minor tweaks only
10: Exceptional - ship it
</overall_score>

</scoring_criteria>

<output_format>

Deliver the review in this structure:

```
## HOOK REVIEW: [Newsletter Title/Subject]

### EXTRACTED HOOKS
| Location | Current Hook | Type Used |
|----------|--------------|-----------|
| Subject Line | ... | ... |
| Preview Text | ... | ... |
| Opening Line | ... | ... |

### SCORES

**Subject Line: "[current subject]"**
- Attention: X/10 - [brief note]
- Targeting: X/10 - [brief note]  
- Value: X/10 - [brief note]
- **Overall: X/10**

[Repeat for each hook location]

### ANALYSIS
- Call Out Present: Yes/No - [analysis]
- Condition for Value: Yes/No - [analysis]
- Hook Type Effectiveness: [analysis of type choice]

### REWRITES

**Subject Line Alternatives:**
1. [LABEL] "[Audience], [value hook]"
2. [QUESTION] "Would you [desire]?"
3. [COMMAND] "Read this if [condition]"
4. [CURIOSITY] "[pattern interrupt]..."
5. [STATEMENT] "The [thing] that [result]"

**Opening Line Alternatives:**
[Same format]

### RECOMMENDATION
**Best Option:** [#X] because [rationale]
**Quick Win:** [Small tweak to current that improves score]
**Strategy Note:** [Any broader observations]
```

</output_format>

<success_criteria>
The review is complete when:
1. All hooks are extracted and identified by type
2. Each hook is scored on all 3 dimensions
3. At least 3 rewrites provided per major hook (subject/opening)
4. Rewrites use DIFFERENT hook types from database
5. Clear recommendation with rationale provided
6. Rewrites maintain the newsletter's core message and voice
</success_criteria>

<usage_examples>

<example_trigger_phrases>
- "Review this newsletter with Hormozi hooks"
- "Hormozi review my subject line"
- "Apply 100M hooks framework to this draft"
- "Strengthen the hooks in this newsletter"
- "Score my newsletter hooks"
</example_trigger_phrases>

<example_input>
Subject: Tips for Growing Your Store
Preview: Learn how to get more sales
Opening: In this issue, we'll cover some strategies for increasing your revenue...
</example_input>

<example_output_snippet>
**Subject Line: "Tips for Growing Your Store"**
- Attention: 2/10 - Generic, no pattern interrupt
- Targeting: 3/10 - "Your store" implies owners but very weak
- Value: 3/10 - "Tips" is vague, no specific outcome
- **Overall: 2.7/10 - Needs complete rewrite**

**Subject Line Alternatives:**
1. [LABEL] "Store owners doing under $10K/mo - read this"
2. [QUESTION] "Still stuck at the same revenue for months?"
3. [COMMAND] "Read this if you want to 2x sales this quarter"
4. [CURIOSITY] "The $47 change that 3x'd her store revenue..."
5. [STATEMENT] "How to get ahead of 99% of store owners"
</example_output_snippet>

</usage_examples>

<references>
- Full hooks database: data/hormozi_hooks_db.json
- Quick reference guide: references/hormozi-hooks-db.md
- Source: 100M Hooks Playbook by Alex Hormozi
</references>
