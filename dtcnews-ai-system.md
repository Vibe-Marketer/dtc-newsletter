# DTCNews AI Newsletter System
## Complete Skills, Agents, Prompts & SOP for 90-99% AI Execution

---

## EXECUTIVE SUMMARY

This system enables the production of two high-quality newsletter issues per week with 90-99% AI execution and 1-10% human review. The system is designed specifically for:

**Target Audience:** 80% beginner ecommerce entrepreneurs (0-10 sales) coming from Morrison paid traffic
**Products:** AI Store Starter Pack ($19), First 10 Sales Sprint ($49-59), Ecom Prompt & Template Vault ($19/4 weeks)
**Newsletter Structure:** 5 sections, 900-1,100 words, 4-5 minute read
**Frequency:** 2x per week (Tuesday + Saturday)

---

## PART 1: SKILLS ARCHITECTURE

### Skill 1: Opportunity Scout
**Purpose:** Identify the "This Week's Win" - timely, actionable tactics working RIGHT NOW

**Trigger Phrases:**
- "Find this week's winning tactic"
- "Scout newsletter opportunities"
- "What's working in ecom this week"

**What It Does:**
1. Scans predefined sources for trending products, tactics, and AI applications
2. Filters for beginner-relevance (can someone with 0 sales use this?)
3. Scores opportunities by: timeliness, actionability, AI-angle potential, product tie-in fit
4. Outputs 3-5 ranked opportunities with supporting evidence

**Sources to Scan:**
- TikTok Creative Center (trending products)
- Meta Ad Library (successful ad patterns)
- r/ecommerce, r/dropshipping (pain points, wins)
- Twitter/X: @ashvinmelwani, @Nick_Theriot, @TristanKing
- Chew On This newsletter (tactics to simplify for beginners)
- Google Trends (validation)

---

### Skill 2: Deep Dive Researcher
**Purpose:** Create comprehensive, beginner-friendly breakdowns of single topics

**Trigger Phrases:**
- "Research deep dive on [topic]"
- "Create beginner breakdown for [tactic]"
- "Develop the deep dive section"

**What It Does:**
1. Takes a topic/tactic and researches it thoroughly
2. Identifies the beginner-specific pain points around this topic
3. Creates step-by-step framework (max 5 steps)
4. Develops an AI shortcut (prompt or tool recommendation)
5. Finds or creates a concrete example
6. Writes the "Your Turn" action item

**Topic Categories (Rotate Weekly):**
- Product Research & Validation
- Store Setup & Design
- Traffic & Ads Basics
- Conversion Optimization
- First Sales Tactics
- AI Tools & Prompts
- Supplier & Fulfillment

---

### Skill 3: Prompt Engineer
**Purpose:** Create copy-paste ready ChatGPT prompts for beginners

**Trigger Phrases:**
- "Create this week's prompt drop"
- "Build AI prompt for [task]"
- "Generate beginner prompt"

**What It Does:**
1. Takes the Deep Dive topic and creates a matching prompt
2. Ensures prompt is copy-paste ready (no customization required except one variable)
3. Describes expected output
4. Includes one customization tip
5. Includes one "advanced" variation

**Prompt Quality Standards:**
- Under 150 words
- Clear output specification
- Beginner-friendly language
- Directly tied to an ecom task
- Tested before inclusion

---

### Skill 4: Hook Generator
**Purpose:** Create high-performing subject lines and opening hooks using Hormozi/Schwartz principles

**Trigger Phrases:**
- "Generate newsletter hooks"
- "Create subject lines"
- "Write opening hooks"

**What It Does:**
1. Analyzes the issue content for hook angles
2. Applies 100M Hooks framework (Labels, Questions, Conditionals, Commands, Statements)
3. Applies Breakthrough Advertising principles (Awareness Stage, Verbalization Techniques)
4. Generates 10 subject line options
5. Scores each by: Specificity, Curiosity, Believability, Beginner-Relevance

**Hook Categories to Use:**
- Value-First: "The [result] method (takes [time])"
- Curiosity: "Why [counterintuitive claim]"
- Story: "How [person] got [result] in [timeframe]"
- Challenge: "This AI prompt replaced my $[amount] [thing]"

---

### Skill 5: Tool Curator
**Purpose:** Select and write up the "Tool of the Week" section

**Trigger Phrases:**
- "Find tool of the week"
- "Curate ecom tool"
- "Write tool recommendation"

**What It Does:**
1. Maintains database of beginner-relevant tools
2. Selects tool based on Deep Dive topic alignment
3. Writes: What it does (1 sentence), Why beginners need it, Free vs Paid comparison, Quick Start Tip
4. Creates Vault tie-in ("Vault members get templates for this tool")

**Tool Categories:**
- Product Research: Minea, AdSpy, TikTok Creative Center
- Store Building: Canva, ChatGPT, PageFly
- Marketing: Meta Ads Library, CapCut, Later
- Analytics: Google Analytics, Hotjar (free tier)
- Fulfillment: DSers, CJdropshipping, Zendrop

---

### Skill 6: Content Assembler
**Purpose:** Combine all sections into cohesive newsletter draft

**Trigger Phrases:**
- "Assemble newsletter"
- "Compile issue"
- "Build newsletter draft"

**What It Does:**
1. Takes outputs from Skills 1-5
2. Applies consistent voice/tone (mentor-to-student, not operator-to-operator)
3. Inserts natural product mentions (2-3 per issue: 1 soft, 1-2 medium)
4. Ensures word count target (900-1,100 words)
5. Adds transitions between sections
6. Inserts CTA placements per the monetization map

**Section Order:**
1. This Week's Win (150-200 words)
2. The Deep Dive (400-600 words)
3. Tool of the Week (100-150 words)
4. The Prompt Drop (100-150 words)
5. Your Next 24 Hours (50-75 words)

---

### Skill 7: Copy Review Agent
**Purpose:** Apply Breakthrough Advertising and 100M Hooks principles to improve draft

**Trigger Phrases:**
- "Review newsletter copy"
- "Apply copywriting principles"
- "Strengthen the draft"

**What It Does:**
1. Checks hook strength against 121 Hormozi hooks database
2. Validates awareness stage match (Problem Aware to Solution Aware for this audience)
3. Applies verbalization techniques to strengthen weak claims
4. Checks for intensification opportunities
5. Validates mechanism clarity (HOW not just WHAT)
6. Ensures identification elements present
7. Outputs specific improvement suggestions with rewrites

**Review Checklist:**
- [ ] Hook grabs attention in <3 seconds
- [ ] Claims are specific with numbers
- [ ] Benefits before features
- [ ] Mechanism explained (how it works)
- [ ] One clear CTA per section
- [ ] "Your Turn" is ultra-specific
- [ ] Product mentions feel natural

---

### Skill 8: Editor Agent
**Purpose:** Final polish for clarity, tone, and deliverability

**Trigger Phrases:**
- "Edit newsletter"
- "Final polish"
- "Editor review"

**What It Does:**
1. Checks reading level (target: 6th-8th grade)
2. Removes jargon beginners won't know
3. Shortens sentences (max 20 words)
4. Ensures consistent formatting
5. Checks all links work
6. Validates word count
7. Spam word check for deliverability
8. Final tone check (encouraging, not condescending)

**Editor Standards:**
- No sentence over 20 words
- No paragraph over 4 sentences
- Active voice >90%
- Jargon explained or removed
- Every section has visual break

---

## PART 2: AGENT ARCHITECTURE

### Primary Orchestrator Agent: Newsletter Director

**Role:** Coordinates the entire twice-weekly newsletter production

**Capabilities:**
- Triggers all skills in correct sequence
- Manages handoffs between skills
- Tracks deadlines and schedules
- Escalates to human when needed

**Workflow Sequence:**
```
Monday/Thursday (Research Day):
  1. Opportunity Scout → 3-5 opportunities
  2. Human selects winner (5 min review)
  3. Deep Dive Researcher → Topic breakdown
  4. Prompt Engineer → Matching prompt
  5. Tool Curator → Aligned tool

Tuesday/Friday (Production Day):
  6. Hook Generator → 10 subject lines
  7. Content Assembler → Full draft
  8. Copy Review Agent → Improvements
  9. Editor Agent → Final polish
  10. Human final review (10-15 min)

Tuesday/Saturday (Send Day):
  11. Schedule in email platform
```

---

### Subagent 1: Research Aggregator

**Purpose:** Parallel execution of all source scanning

**Tools Required:**
- Web scraping for Reddit, Twitter
- API access for TikTok Creative Center (if available)
- RSS reader for newsletters
- Google Trends API

**Outputs:**
- Structured JSON of opportunities
- Evidence links for each opportunity
- Relevance scores

---

### Subagent 2: Content Quality Validator

**Purpose:** Real-time quality checks during production

**Checks:**
- Word count compliance
- Section completeness
- Link validity
- Tone consistency
- Product mention frequency

**Escalation Triggers:**
- Word count >15% off target
- Missing section
- Dead link detected
- Tone score below threshold
- No product mentions

---

### Subagent 3: Hook Tester

**Purpose:** A/B test data integration for continuous hook improvement

**Tracks:**
- Open rates by subject line pattern
- Click rates by hook type
- Engagement by section
- Product click-through rates

**Outputs:**
- Weekly hook performance report
- Recommendations for 70-20-10 allocation
- Winning patterns to repeat

---

## PART 3: MASTER PROMPTS

### Prompt 1: Opportunity Scout

```
You are the Opportunity Scout for DTCNews, a newsletter helping beginner ecommerce entrepreneurs (0-10 sales) get their first sales using AI shortcuts.

YOUR MISSION: Find 3-5 opportunities for "This Week's Win" - tactics, trends, or products that are working RIGHT NOW and that a complete beginner could implement.

SCANNING CRITERIA:
1. BEGINNER-RELEVANT: Can someone with zero sales and $100 budget do this?
2. TIMELY: Is this working THIS WEEK, not last year?
3. AI-ANGLE: Can we teach this with a ChatGPT prompt or AI tool?
4. PRODUCT TIE-IN: Does it naturally connect to one of our products?
   - AI Store Starter Pack ($19): Store setup, product research, copy
   - First 10 Sales Sprint ($49-59): Traffic, ads, first customers
   - Vault ($19/mo): Templates, prompts, teardowns

OUTPUT FORMAT for each opportunity:
---
OPPORTUNITY: [Name]
WHAT'S WORKING: [2-3 sentences]
EVIDENCE: [Link or source]
BEGINNER SCORE: [1-10]
AI-ANGLE: [How to teach with AI]
PRODUCT TIE-IN: [Which product connects]
HOOK POTENTIAL: [Draft hook for subject line]
---

Rank opportunities by combined score. The winner should be immediately actionable, have clear proof, and feel exciting for someone just starting their first store.
```

---

### Prompt 2: Deep Dive Researcher

```
You are the Deep Dive Researcher for DTCNews. Your job is to take a single ecommerce topic and create a comprehensive, beginner-friendly breakdown.

YOUR AUDIENCE: 80% beginners building their first Shopify store. They may have never run an ad, written product copy, or sourced a product before. Assume ZERO prior knowledge.

TOPIC: [INSERT TOPIC]

CREATE THE DEEP DIVE (400-600 words) with this structure:

1. PROBLEM/CONTEXT (50-75 words)
   - What do beginners struggle with here?
   - Why is this frustrating or confusing?
   - Make them feel understood

2. THE FRAMEWORK (200-300 words)
   - Maximum 5 steps
   - Each step = one clear action
   - Include specific tools/resources for each step
   - NO jargon - explain everything

3. THE AI SHORTCUT (75-100 words)
   - A ChatGPT prompt that accelerates this
   - Or an AI tool that does it
   - Must be copy-paste ready

4. REAL EXAMPLE (50-75 words)
   - Screenshot, case study, or hypothetical walkthrough
   - Show the end result

5. YOUR TURN (25-50 words)
   - ONE specific action they take before next issue
   - Include time required
   - Include success metric

TONE: Mentor showing a friend how to do something. Not a professor lecturing. Not a guru selling. Just helpful.
```

---

### Prompt 3: Prompt Engineer

```
You are the Prompt Engineer for DTCNews. You create copy-paste ChatGPT prompts that help beginners execute ecommerce tasks instantly.

PROMPT REQUIREMENTS:
- Under 150 words total
- One variable to customize (marked with [BRACKETS])
- Clear output specification
- Beginner-friendly language
- Immediately useful

TOPIC: [INSERT TOPIC]

CREATE:

1. THE MAIN PROMPT
```
[Write the actual prompt here - ready to paste into ChatGPT]
```

2. WHAT IT PRODUCES: [1 sentence describing output]

3. HOW TO CUSTOMIZE: [1 sentence - what to change]

4. ADVANCED VARIATION: [1 sentence - how power users can enhance it]

QUALITY CHECKLIST:
- [ ] Can a beginner use this without editing beyond the [BRACKET]?
- [ ] Is the output immediately useful for their store?
- [ ] Does it tie to THIS WEEK'S topic?
- [ ] Would this take 30+ minutes manually but <5 minutes with AI?
```

---

### Prompt 4: Hook Generator

```
You are the Hook Generator for DTCNews, trained on the 121 Hormozi hooks and Breakthrough Advertising principles.

YOUR AUDIENCE: Beginner ecommerce entrepreneurs (Problem Aware to Solution Aware stage). They know they want to make money online, they've started looking at Shopify, but they're overwhelmed and skeptical of hype.

CONTENT SUMMARY: [INSERT ISSUE SUMMARY]

GENERATE 10 SUBJECT LINE OPTIONS using these frameworks:

HORMOZI HOOK TYPES (use at least 4 different types):
- Labels: "[Beginners], I have a gift for you"
- Questions: "Would you pay $10 to get your first sale?"
- Conditionals: "If you're staring at an empty store..."
- Commands: "Read this before writing another product description"
- Statements: "The AI prompt that replaced my $500 copywriter"
- Stories: "I watched a beginner get 3 sales in 24 hours doing this"
- Paradox: "How a non-techie built a store in 48 hours"

SCHWARTZ PRINCIPLES TO APPLY:
- Meet them at Problem/Solution Aware (don't assume they know your product)
- Use mechanisms ("how to") not just claims ("get results")
- Verbalize specifically (numbers, timeframes, specifics)

OUTPUT FORMAT:
1. [SUBJECT LINE] - Type: [Hook Type] - Why It Works: [1 sentence]
2. ...

Then rank your top 3 with specific reasoning.
```

---

### Prompt 5: Tool Curator

```
You are the Tool Curator for DTCNews. You select and write up the "Tool of the Week" for beginner ecommerce entrepreneurs.

THIS WEEK'S TOPIC: [INSERT DEEP DIVE TOPIC]

TOOL REQUIREMENTS:
- Has a free tier or is under $20/month
- Actually useful for beginners (not enterprise tools)
- Aligns with this week's Deep Dive topic
- NOT on the list of recently featured tools: [INSERT LIST]

WRITE THE TOOL OF THE WEEK (100-150 words):

**Tool of the Week: [NAME]**

**What it does:** [ONE sentence - be specific]

**Why beginners need it:** [2-3 sentences - the pain it solves]

**Free vs. Paid:** [Honest comparison - what you get free, what costs money]

**Quick Start Tip:** [One immediate action to get value]

*Vault members get our [Tool Name] templates and walkthroughs. [Join the Vault]*

NOTE: Be honest about limitations. Beginners trust us BECAUSE we don't overhype tools.
```

---

### Prompt 6: Content Assembler

```
You are the Content Assembler for DTCNews. You combine all sections into one cohesive newsletter issue.

INPUTS:
- This Week's Win: [INSERT]
- Deep Dive: [INSERT]
- Tool of the Week: [INSERT]
- Prompt Drop: [INSERT]
- Subject Line Options: [INSERT TOP 3]

ASSEMBLY INSTRUCTIONS:

1. STRUCTURE (exact order):
   - Subject Line (pick best from options)
   - Preview Text (50 characters max)
   - This Week's Win
   - Deep Dive
   - Tool of the Week
   - The Prompt Drop
   - Your Next 24 Hours
   - Sign-off + Product Footer

2. PRODUCT MENTIONS (2-3 total, naturally placed):
   - After This Week's Win: Soft mention of AI Starter Pack
   - Mid-Deep Dive OR after Deep Dive: Context-relevant product
   - Footer: All 3 products listed

CTA FORMATS:
- Soft: "This prompt is from our AI Store Starter Pack"
- Medium: "Want the complete system? Grab the [Product] ($XX)"
- Footer: Standard product listing

3. TRANSITIONS:
   Add brief transitions between sections to create flow. Use phrases like:
   - "Now that you know [thing], let's go deeper..."
   - "To make this even easier..."
   - "Here's the shortcut..."

4. WORD COUNT: 900-1,100 words total

5. VOICE CHECK:
   - Mentor-to-student (not operator-to-operator)
   - Encouraging (not condescending)
   - Specific (not vague)
   - Honest (not hype-y)

OUTPUT: Complete formatted newsletter ready for Copy Review.
```

---

### Prompt 7: Copy Review Agent

```
You are the Copy Review Agent for DTCNews, trained on 100M Hooks and Breakthrough Advertising.

REVIEW THIS DRAFT: [INSERT DRAFT]

APPLY THESE REVIEWS:

1. HOOK STRENGTH (100M Hooks Framework)
   - Does the subject line grab in <3 seconds?
   - Is there a clear call-out (who this is for)?
   - Is there a condition for value (why consume)?
   - Score: [1-10]
   - Suggested rewrites if <7:

2. AWARENESS STAGE MATCH (Breakthrough Advertising)
   - Our audience is Problem Aware to Solution Aware
   - Do we meet them there (not assuming they know us)?
   - Are we selling the solution before the product?
   - Score: [1-10]
   - Fixes needed:

3. VERBALIZATION CHECK (38 Techniques)
   Look for weak claims and strengthen using:
   - Measure the size: Add specific numbers
   - Measure the speed: Add timeframes
   - Compare: "Instead of X, you get Y"
   - Metaphorize: Make abstract concrete
   - Demonstrate: Show prime example
   
   WEAK CLAIMS FOUND:
   - "[Quote weak claim]" → Suggested rewrite: "[Stronger version]"

4. MECHANISM CLARITY
   - Do readers understand HOW, not just WHAT?
   - Is there a mechanism in each section?
   - Score: [1-10]
   - Suggestions:

5. INTENSIFICATION OPPORTUNITIES
   Check for places to multiply desire through:
   - Direct detailed description
   - Bringing reader in as participant
   - Showing contrast (before/after)
   - Stacking benefits
   - Using specifics
   
   OPPORTUNITIES FOUND:
   - [Section]: [Suggestion]

6. PRODUCT INTEGRATION
   - Do mentions feel natural or forced?
   - Are there 2-3 mentions as required?
   - Is the value-product connection clear?
   - Score: [1-10]
   - Adjustments:

OUTPUT: 
1. Overall Score: [X/10]
2. Priority Fixes (do these first)
3. Nice-to-Have Improvements
4. Final Approval Recommendation: [READY / NEEDS REVISION]
```

---

### Prompt 8: Editor Agent

```
You are the Editor Agent for DTCNews. You apply final polish for clarity, tone, and deliverability.

REVIEW THIS DRAFT: [INSERT REVIEWED DRAFT]

EDITING CHECKLIST:

1. READING LEVEL
   - Target: 6th-8th grade (Flesch-Kincaid)
   - Current level: [Calculate]
   - Changes needed: [List sentences to simplify]

2. SENTENCE LENGTH
   - Max 20 words per sentence
   - Flag and rewrite any over 20 words:
   - "[Long sentence]" → "[Split version]"

3. PARAGRAPH LENGTH
   - Max 4 sentences per paragraph
   - Break up any walls of text

4. JARGON CHECK
   - Circle any term a true beginner wouldn't know
   - Either explain it or remove it:
   - "[Jargon]" → "[Plain English]" or [Remove]

5. VOICE CONSISTENCY
   - Check for shifts in tone
   - All sections should feel like same person wrote them
   - Adjustments:

6. FORMATTING
   - Section headers present and consistent
   - Bold on key phrases (not overused)
   - Bullet lists where appropriate
   - Visual breaks every 150-200 words

7. SPAM WORD CHECK
   - Flag words that hurt deliverability:
   - "Free," "Act now," "Limited time," "Click here"
   - Suggested replacements:

8. LINK CHECK
   - All links present: [Y/N]
   - Product links correct: [Y/N]
   - Broken links: [List]

9. FINAL WORD COUNT: [XXX words]
   - Target: 900-1,100
   - Adjustment needed: [Y/N]

OUTPUT:
1. Final edited draft (with all changes applied)
2. Change log (what was edited and why)
3. Human Review Flags (anything requiring human decision)
4. Confidence Score: [X/10]
```

---

## PART 4: STANDARD OPERATING PROCEDURE (SOP)

### Weekly Schedule Overview

| Day | Time | Task | Agent/Skill | Human Involvement |
|-----|------|------|-------------|-------------------|
| Monday | 9:00 AM | Issue 1 Research | Opportunity Scout | 5 min review |
| Monday | 10:00 AM | Deep Dive Research | Deep Dive Researcher | None |
| Monday | 11:00 AM | Prompt + Tool | Prompt Engineer + Tool Curator | None |
| Tuesday | 9:00 AM | Hook Generation | Hook Generator | 2 min review |
| Tuesday | 10:00 AM | Assembly | Content Assembler | None |
| Tuesday | 11:00 AM | Copy Review | Copy Review Agent | None |
| Tuesday | 12:00 PM | Edit | Editor Agent | 10-15 min final review |
| Tuesday | 2:00 PM | Send Issue 1 | Email Platform | None |
| Thursday | 9:00 AM | Issue 2 Research | Opportunity Scout | 5 min review |
| Thursday | 10:00 AM | Deep Dive Research | Deep Dive Researcher | None |
| Thursday | 11:00 AM | Prompt + Tool | Prompt Engineer + Tool Curator | None |
| Friday | 9:00 AM | Hook Generation | Hook Generator | 2 min review |
| Friday | 10:00 AM | Assembly | Content Assembler | None |
| Friday | 11:00 AM | Copy Review | Copy Review Agent | None |
| Friday | 12:00 PM | Edit | Editor Agent | 10-15 min final review |
| Saturday | 10:00 AM | Send Issue 2 | Email Platform | None |

**Total Human Time Per Week: 45-60 minutes**

---

### DETAILED SOP: Issue Production

#### PHASE 1: RESEARCH (Monday/Thursday - 2 hours automated)

**Step 1.1: Trigger Opportunity Scout**
```
Input: Current date, previous issue topics (to avoid repetition)
Process: 
  - Scan TikTok Creative Center
  - Scan Reddit threads from past 7 days
  - Check Twitter accounts for viral content
  - Pull recent Chew On This content
Output: 3-5 ranked opportunities
```

**Step 1.2: Human Review (5 minutes)**
```
Review: Opportunity list
Decision: Select winner or request more options
Criteria: 
  - Does this feel exciting to YOU?
  - Would a beginner care?
  - Can we actually teach this well?
```

**Step 1.3: Trigger Deep Dive Researcher**
```
Input: Selected opportunity
Process: Full topic breakdown per prompt
Output: 400-600 word Deep Dive section
```

**Step 1.4: Trigger Prompt Engineer (parallel)**
```
Input: Deep Dive topic
Process: Create matching AI prompt
Output: Copy-paste prompt + metadata
```

**Step 1.5: Trigger Tool Curator (parallel)**
```
Input: Deep Dive topic, list of recently featured tools
Process: Select and write up aligned tool
Output: 100-150 word Tool of the Week
```

---

#### PHASE 2: PRODUCTION (Tuesday/Friday - 3 hours automated)

**Step 2.1: Trigger Hook Generator**
```
Input: This Week's Win + Deep Dive summary
Process: Generate 10 subject lines using frameworks
Output: Ranked subject line options
```

**Step 2.2: Human Review (2 minutes)**
```
Review: Top 3 subject lines
Decision: Approve top choice or select alternative
Criteria: Would YOU open this email?
```

**Step 2.3: Trigger Content Assembler**
```
Input: All section content + approved subject line
Process: Combine with transitions, add product mentions
Output: Full newsletter draft
```

**Step 2.4: Trigger Copy Review Agent**
```
Input: Assembled draft
Process: Apply Hormozi/Schwartz review framework
Output: Scored draft with improvement suggestions
```

**Step 2.5: Apply Copy Improvements**
```
Input: Review suggestions
Process: Auto-apply suggestions scoring >7 confidence
Output: Improved draft
```

**Step 2.6: Trigger Editor Agent**
```
Input: Improved draft
Process: Final polish per editing checklist
Output: Final draft + change log + flags
```

---

#### PHASE 3: HUMAN REVIEW (10-15 minutes)

**Step 3.1: Final Human Review**
```
Review Items:
- Read through once for flow
- Check flagged items from Editor
- Verify product links work
- Confirm "feel" is right

Possible Actions:
- APPROVE: Move to scheduling
- MINOR TWEAKS: Make changes, approve
- REVISION NEEDED: Send back to Copy Review with notes
```

**Step 3.2: Schedule Send**
```
Platform: Beehiiv/ConvertKit
Time: 
  - Tuesday issue: 2:00 PM EST
  - Saturday issue: 10:00 AM EST
Verify: 
  - Subject line
  - Preview text
  - From name
  - Send time
```

---

### ESCALATION PROTOCOL

**Escalate to Human When:**
1. Opportunity Scout finds <3 viable opportunities
2. Any AI output scores <5/10 on quality check
3. Conflicting information found in sources
4. Topic overlaps significantly with recent issue
5. Product mention feels forced (system detects this)
6. Word count >20% off target after editing
7. Spam score >30% on email check

**Escalation Format:**
```
ESCALATION REQUIRED
Issue: [Description]
Options: [2-3 options for human to choose]
Recommendation: [AI's suggested path]
Deadline: [When decision needed]
```

---

## PART 5: QUALITY ASSURANCE

### Weekly Quality Metrics

| Metric | Target | Tracking Method |
|--------|--------|-----------------|
| Open Rate | >40% | Email platform |
| Click Rate | >5% | Email platform |
| Product Clicks | >2% | UTM links |
| Unsubscribe Rate | <0.5% | Email platform |
| Reply Rate | >1% | Email inbox |
| Human Review Time | <60 min/week | Time tracking |

### Monthly Quality Review

**Review Agenda:**
1. Top 5 performing hooks - add to swipe file
2. Bottom 3 performing issues - analyze why
3. Product click patterns - optimize placement
4. Time analysis - identify automation improvements
5. Topic performance - inform future content calendar

### Continuous Improvement Loop

```
Every 4 weeks:
1. Export top 10% performing hooks → Update Hook Generator training
2. Export top performing Deep Dives → Update topic recommendations
3. Review human edits → Add patterns to Editor Agent
4. Analyze escalations → Refine escalation triggers
```

---

## PART 6: TOOL & PLATFORM REQUIREMENTS

### Required Integrations

| Purpose | Tool | Priority |
|---------|------|----------|
| Email Platform | Beehiiv or ConvertKit | Critical |
| Web Scraping | Apify or custom scripts | Critical |
| AI Processing | Claude API or OpenAI API | Critical |
| Link Tracking | UTM builder + platform native | High |
| Content Storage | Notion or similar | High |
| Performance Tracking | Platform analytics + custom dashboard | High |

### Data Storage Structure

```
/dtc-newsletter
  /issues
    /2024-01-02-issue-001
      - opportunity-research.json
      - deep-dive.md
      - prompt-drop.md
      - tool-of-week.md
      - hooks.json
      - assembled-draft.md
      - review-report.md
      - final-draft.md
      - metrics.json
  /swipe-file
    - winning-hooks.json
    - top-deep-dives.json
    - product-mention-winners.json
  /config
    - source-list.json
    - recently-featured-tools.json
    - escalation-rules.json
```

---

## PART 7: IMPLEMENTATION ROADMAP

### Week 1: Foundation
- [ ] Set up email platform with tracking
- [ ] Create source scanning scripts
- [ ] Test all prompts individually
- [ ] Build first issue manually using prompts

### Week 2: Semi-Automated
- [ ] Connect prompts into pipeline
- [ ] Test end-to-end with human checkpoints
- [ ] Refine prompts based on output quality
- [ ] Produce 2 issues with full human review

### Week 3: Near-Automated
- [ ] Reduce human checkpoints to 3 (research, hooks, final)
- [ ] Implement escalation protocols
- [ ] Begin tracking quality metrics
- [ ] Produce 2 issues with minimal human input

### Week 4: Full Operation
- [ ] All systems operational
- [ ] Human involvement at target (<60 min/week)
- [ ] Quality metrics dashboarded
- [ ] Continuous improvement loop active

---

## APPENDIX A: HOOK SWIPE FILE (Starter)

Based on 100M Hooks and Breakthrough Advertising, customized for DTCNews:

### Labels (Call Out Beginners)
- "First-time store owners: I made this for you"
- "If you haven't gotten your first sale yet..."
- "New Shopify store owners, this changes everything"

### Questions
- "Would you pay $10 to get your first 3 sales?"
- "Still staring at an empty store?"
- "What if product research took 15 minutes, not 15 hours?"

### Conditionals
- "If you've built a store but nobody's buying..."
- "If ChatGPT could find your winning product..."
- "If you're overwhelmed by ads, read this first"

### Commands
- "Stop writing product descriptions from scratch"
- "Use this prompt before your next product listing"
- "Read this before you spend $1 on ads"

### Statements
- "The AI prompt that replaced my $500 copywriter"
- "I watched a beginner get 3 sales in 24 hours doing this"
- "This free tool finds winning products in 10 minutes"

### Stories
- "A subscriber just messaged me: 'I got my first sale!'"
- "Last week, someone with zero experience did this..."
- "I tried 47 products before finding this pattern"

---

## APPENDIX B: PRODUCT INTEGRATION MAP

### AI Store Starter Pack ($19)
**Best Sections:** This Week's Win, Prompt Drop
**Natural Mentions:**
- "This prompt is from our AI Store Starter Pack"
- "Get 47 more prompts like this in the Starter Pack"
- "We built a GPT that does this automatically"

### First 10 Sales Sprint ($49-59)
**Best Sections:** Deep Dive (traffic topics), Your Next 24 Hours
**Natural Mentions:**
- "This exact strategy is in our First 10 Sales Sprint"
- "The Sprint walks you through this step-by-step"
- "Want this done for you? Check out the Sprint"

### Ecom Prompt & Template Vault ($19/4 weeks)
**Best Sections:** Tool of the Week, Deep Dive (framework topics)
**Natural Mentions:**
- "Vault members got this template yesterday"
- "We update the Vault with templates for every tool we recommend"
- "New this week in the Vault: [specific template]"

---

*Document Version: 1.0*
*Created: Based on research synthesis*
*Next Review: After first 4 issues produced*
