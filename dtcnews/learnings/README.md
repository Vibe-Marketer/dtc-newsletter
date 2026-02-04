# Learnings
<!-- DOE-VERSION: 2026.02.04 -->

Things we've learned that improve the newsletter system.

## 2026.02.04 - Initial Setup

### Don't Filter by "Beginner Keywords"
**Problem:** Filtering content by words like "beginner", "first sale", "simple" filters OUT great content that uses advanced language but contains beginner-executable tactics.

**Solution:** Rank by actual viral performance (outlier score + virality analysis), then assess if the underlying TACTIC is beginner-executable. A $1M case study might contain a $0 tactic.

### Same Principles Scale
**Problem:** "Beginner-friendly" content often means dumbed-down, low-value content.

**Solution:** Extract the MECHANISM (why something worked) and show how the same principle applies at any scale. A store sending 5 emails/week and a store sending 1 email/week are using the SAME principle.

### Executable Today
**Problem:** Vague advice like "provide value" or "engage your audience" isn't actionable.

**Solution:** Every deep dive must end with 3 specific actions completable in 2 hours with tools they already have. Include the specific tool to use.

### ChatGPT Prompts Are Valuable
**Problem:** Generic action steps don't help beginners who don't know where to start.

**Solution:** Every deep dive includes a copy-paste ChatGPT prompt that helps them execute one of the action steps. Max 100 words, one [VARIABLE] to fill in.

---

## 2026.02.04 - Integration Fixes

### Deep Dive Must Flow Into Section 2
**Problem:** Generating Section 2 separately from the deep dive loses the rich WHO/WHAT/WHY/HOW structure.

**Solution:** `generate_section_2_from_deep_dive()` takes the pre-generated deep dive and formats it for the newsletter while preserving all the genuine value.

### Pipeline Must Chain Outputs
**Problem:** Running scripts independently doesn't pass the deep dive to the newsletter generator.

**Solution:** Pipeline's `generate` step now explicitly passes `--deep-dive-file` to newsletter_generator.py when the deep dive file exists.

---

*Add new learnings above this line*
