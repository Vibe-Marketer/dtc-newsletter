---
name: dtc-editor-06
description: Final editing pass for DTCNews newsletter. Checks reading level, removes jargon, validates formatting, and ensures email deliverability before human review.
---

<objective>
Apply final polish to newsletter drafts before human review. This skill runs after copy reviews and performs comprehensive editing checks including reading level analysis, jargon removal, spam trigger replacement, formatting validation, and voice compliance verification. Output is publication-ready content with a detailed change log.
</objective>

<audience_context>
DTCNews targets aspiring e-commerce entrepreneurs who are beginners. Many readers:
- Have never run an online business
- Don't know marketing terminology
- Skim content on mobile devices
- May be non-native English speakers

These standards exist because:
- 6th-8th grade reading level ensures accessibility for all backgrounds
- Jargon creates barriers and makes readers feel excluded
- Spam triggers hurt deliverability and reader trust
- Consistent formatting aids scanning and comprehension
- Mentor tone builds confidence without condescension
</audience_context>

<editing_checklist>

<reading_level>
TARGET: 6th-8th grade Flesch-Kincaid (score 60-70)

Sentence Rules:
- Maximum 20 words per sentence
- Ideal average: 12-15 words per sentence
- Flag any sentence over 25 words for mandatory splitting

Paragraph Rules:
- Maximum 4 sentences per paragraph
- Ideal: 2-3 sentences per paragraph
- Single-sentence paragraphs are encouraged for emphasis

Word Rules:
- Prefer 1-2 syllable words
- Replace 3+ syllable words when simpler alternatives exist
- No sentence should have more than 2 complex words

Measurement:
- Use execution/anti_pattern_validator.py for sentence stats
- Target rhythm: 60% short, 30% medium, 10% long sentences
- Rhythm score should be 70+ for passing
</reading_level>

<jargon_check>
All industry jargon must be either:
1. Explained in parentheses on first use
2. Replaced with plain English
3. Removed entirely if not essential

See: references/jargon-glossary.md for full list and replacements.

Common Violations:
- Acronyms without explanation (ROAS, AOV, LTV, CAC, CPA, CTR, CVR)
- Marketing terms (funnel, retargeting, lookalike, pixel, attribution)
- Tech terms (A/B test, API, integration, automation, workflow)
- Business jargon (scale, leverage, optimize, iterate, pivot)

Handling Rules:
1. First occurrence: Explain OR replace
2. Subsequent occurrences: Use plain term only
3. If term appears 3+ times: Consider if article is too technical
</jargon_check>

<spam_triggers>
Email deliverability depends on avoiding spam filter triggers.

See: references/spam-triggers.md for full list and safe alternatives.

HIGH RISK (always replace):
- "free" -> "no-cost" or "complimentary" or remove
- "act now" -> "try this today" or "start with"
- "limited time" -> remove or "this week"
- "click here" -> specific action ("read the guide", "see examples")
- "guarantee" -> "promise" or remove
- "100%" -> "fully" or specific number

MEDIUM RISK (replace if possible):
- "urgent" -> "important" or "time-sensitive"
- "exclusive" -> "early access" or "insider"
- "amazing" -> specific benefit
- "incredible" -> specific result
- "buy now" -> "get started" or "try it"

FORMATTING TRIGGERS:
- ALL CAPS words (except acronyms)
- Multiple exclamation points!!!
- Excessive bold/color (max 3 bold phrases per section)
- Dollar signs in subject lines
</spam_triggers>

<formatting_validation>
Section Headers:
- Every section needs a clear header
- Headers should be consistent style (all caps, title case, etc.)
- No orphan content before first header

Visual Hierarchy:
- Bold on key phrases: max 3 per section
- Use bold for: action items, key numbers, important names
- Never bold entire sentences

Visual Breaks:
- Insert break every 150-200 words
- Breaks can be: subheader, bullet list, blockquote, divider
- No wall-of-text blocks

Links:
- Descriptive anchor text (not "click here")
- Links should be on action phrases
- Max 3 links per section
- Primary CTA link should be obvious

Lists:
- Bullet lists: 3-7 items ideal
- Numbered lists: for sequential steps only
- Each item: 1-2 lines max
</formatting_validation>

<voice_compliance>
Use execution/anti_pattern_validator.py for automated checks.

Tone Requirements:
- Mentor-to-student: Knowledgeable friend sharing what worked
- Encouraging: "You can do this" not "You should do this"
- Specific: Real numbers, real examples, real tactics
- Humble: "Here's what I learned" not "Here's the secret"

Forbidden Patterns (from anti_pattern_validator.py):
- Buzzwords: game-changer, leverage, synergy, dive deep
- Fillers: it's worth noting, interestingly enough
- Corporate: move the needle, circle back, low-hanging fruit
- Hype: revolutionize, transform your business, secret sauce
- Fake enthusiasm: I'm excited to share, I'm thrilled to announce

Additional Voice Checks:
- No condescending explanations ("As you probably know...")
- No excessive hedging ("might possibly perhaps")
- No false urgency ("You NEED to do this NOW")
- No humble bragging ("I just happened to 10x my revenue...")
- Max 1 exclamation point per newsletter
</voice_compliance>

</editing_checklist>

<jargon_list>
Priority acronyms to explain or replace:
| Term | Plain English |
|------|---------------|
| ROAS | return on ad spend (profit per dollar spent on ads) |
| AOV | average order value (typical purchase amount) |
| LTV/CLV | customer lifetime value (total revenue from one customer) |
| CAC | customer acquisition cost (cost to get one new customer) |
| CPA | cost per acquisition (cost per sale or signup) |
| CTR | click-through rate (percentage who click) |
| CVR | conversion rate (percentage who buy) |
| CRO | conversion rate optimization (improving your checkout) |
| UGC | user-generated content (customer photos/videos) |
| DTC/D2C | direct-to-consumer (selling directly, no middleman) |

See references/jargon-glossary.md for complete list (100+ terms).
</jargon_list>

<spam_triggers_summary>
Words that trigger spam filters:
- Financial: free, cash, money, income, profit, earn, credit
- Urgency: act now, limited time, urgent, expires, deadline
- Promises: guarantee, no risk, 100%, double your, proven
- Actions: click here, buy now, order now, sign up free
- Hype: amazing, incredible, unbelievable, miracle

See references/spam-triggers.md for complete list with alternatives.
</spam_triggers_summary>

<process>
STEP 1: INTAKE
- Receive draft from copy review stage
- Note any flagged issues from previous review
- Identify content type (main story, tactics, quick hits)

STEP 2: READING LEVEL PASS
- Run sentence analysis via anti_pattern_validator.py
- Split sentences over 20 words
- Break paragraphs over 4 sentences
- Simplify 3+ syllable words where possible
- Target: Rhythm score 70+, avg words/sentence under 15

STEP 3: JARGON PASS
- Scan for all terms in jargon-glossary.md
- First occurrence: Add explanation OR replace
- Subsequent: Use plain term
- Flag if more than 5 jargon terms needed explanation

STEP 4: SPAM TRIGGER PASS
- Scan for all terms in spam-triggers.md
- Replace high-risk words immediately
- Evaluate medium-risk words in context
- Check formatting triggers (caps, exclamation, bold)
- Flag subject line if contains triggers

STEP 5: FORMATTING PASS
- Verify section headers present
- Check bold usage (max 3 per section)
- Ensure visual breaks every 150-200 words
- Validate link anchor text
- Check list lengths

STEP 6: VOICE PASS
- Run anti_pattern_validator.py
- Fix any violations
- Check for condescension markers
- Verify mentor-to-student tone
- Count exclamation points (max 1)

STEP 7: FINAL REVIEW
- Re-run all automated checks
- Calculate confidence score
- Generate change log
- Prepare output package
</process>

<output_format>
Return three components:

1. EDITED CONTENT
```
[Full newsletter content with all edits applied]
```

2. CHANGE LOG
```
## Reading Level Changes
- [Line X]: Split sentence "..." into two sentences
- [Line Y]: Simplified "utilize" to "use"

## Jargon Changes  
- [Line X]: Added explanation for "ROAS"
- [Line Y]: Replaced "funnel" with "buying journey"

## Spam Trigger Changes
- [Line X]: Replaced "free" with "no-cost"
- [Subject]: Removed "$" symbol

## Formatting Changes
- [Section 2]: Added subheader for visual break
- [Section 3]: Reduced bold phrases from 5 to 3

## Voice Changes
- [Line X]: Removed "game-changer"
- [Line Y]: Softened "You MUST" to "Consider"
```

3. METRICS SUMMARY
```
Reading Level:
- Flesch-Kincaid Grade: [X]
- Avg words/sentence: [X]
- Rhythm score: [X]/100

Content Health:
- Jargon terms explained: [X]
- Spam triggers replaced: [X]
- Voice violations fixed: [X]

Confidence Score: [X]/100
- 90-100: Ready for human review
- 70-89: Minor concerns flagged
- Below 70: Needs additional editing pass
```
</output_format>

<success_criteria>
Editing is complete when ALL conditions are met:

READING LEVEL:
- [ ] Flesch-Kincaid grade level 6-8
- [ ] No sentences over 20 words
- [ ] No paragraphs over 4 sentences
- [ ] Average words/sentence under 15
- [ ] Rhythm score 70+

JARGON:
- [ ] All acronyms explained on first use OR replaced
- [ ] No unexplained industry terms
- [ ] Max 5 explained terms (more = too technical)

SPAM:
- [ ] Zero high-risk spam triggers
- [ ] Subject line passes spam check
- [ ] No ALL CAPS (except acronyms)
- [ ] Max 1 exclamation point

FORMATTING:
- [ ] All sections have headers
- [ ] Max 3 bold phrases per section
- [ ] Visual breaks every 150-200 words
- [ ] All links have descriptive anchor text

VOICE:
- [ ] Zero anti-pattern violations
- [ ] Mentor-to-student tone verified
- [ ] No condescension markers
- [ ] No excessive hedging or hype

CONFIDENCE SCORE:
- [ ] Overall score 70+ for human review
- [ ] All blocking issues resolved
</success_criteria>

<integration>
This skill integrates with:

1. execution/anti_pattern_validator.py
   - validate_voice(content) -> (bool, violations)
   - count_sentence_stats(content) -> stats dict
   - format_validation_report(content) -> readable report

2. Previous pipeline stages:
   - Receives: Draft after copy/research review
   - Outputs: Polished content for human review

3. Reference files:
   - references/jargon-glossary.md (100+ terms)
   - references/spam-triggers.md (categorized triggers)
</integration>
