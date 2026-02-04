"""
Virality analyzer for content.
DOE-VERSION: 2026.01.31

Produces structured, AI-parseable virality analysis (not prose summaries).
Primary consumer is the newsletter engine (Phase 4), not humans.

Per CONTEXT.md:
- "prove and define virality with a high degree of certainty"
- "uncover the ultimate legend or key to breaking norms"
- "scientific breakdown: given circumstances + variables → why was virality almost inevitable?"
"""

from typing import Optional

# Schema for virality analysis output
VIRALITY_SCHEMA = {
    "hook_analysis": {
        "hook_type": str,  # question, statement, number, controversy, story
        "hook_text": str,  # The actual hook
        "attention_elements": list,  # What grabs attention
    },
    "emotional_triggers": [
        {
            "trigger": str,  # fear, greed, curiosity, urgency, fomo, hope
            "evidence": str,  # Specific text/element that triggers this
            "intensity": str,  # low, medium, high
        }
    ],
    "timing_factors": {
        "day_relevance": str,  # Why this timing worked
        "trending_topics": list,  # Related trending topics
        "seasonal_hook": None,  # Seasonal relevance if any (str | None)
    },
    "success_factors": {
        "key_drivers": list,  # Primary reasons for virality
        "reproducible_elements": list,  # What can be replicated
        "unique_circumstances": list,  # One-time factors
    },
    "virality_confidence": str,  # definite, likely, possible, unclear
    "replication_notes": str,  # How to replicate this success
}


def analyze_virality(content: dict, transcript: Optional[str] = None) -> dict:
    """
    Analyze content for virality factors.

    Args:
        content: Content dict with title, description, views, etc.
        transcript: Optional transcript text for deeper analysis

    Returns:
        Structured virality analysis dict matching VIRALITY_SCHEMA
    """
    title = content.get("title", "")
    description = content.get("description", content.get("selftext", ""))

    analysis = {
        "hook_analysis": _analyze_hook(title),
        "emotional_triggers": _identify_triggers(title, description),
        "timing_factors": _analyze_timing(content),
        "success_factors": _identify_success_factors(content, transcript),
        "virality_confidence": _assess_confidence(content),
        "replication_notes": "",  # Filled after all analysis
    }

    # Generate replication notes from analysis
    analysis["replication_notes"] = _generate_replication_notes(analysis)

    return analysis


def _analyze_hook(title: str) -> dict:
    """Analyze the hook/title for attention-grabbing elements."""
    hook_types = {
        "question": ["?", "how", "why", "what", "when", "where"],
        "number": any(c.isdigit() for c in title),
        "controversy": ["unpopular", "wrong", "nobody", "truth"],
        "story": ["i ", "my ", "we ", "our "],
        "statement": True,  # Default
    }

    title_lower = title.lower()

    # Detect hook type (priority order)
    detected_type = "statement"
    if "?" in title:
        detected_type = "question"
    elif any(c.isdigit() for c in title):
        detected_type = "number"
    elif any(kw in title_lower for kw in hook_types["controversy"]):
        detected_type = "controversy"
    elif any(title_lower.startswith(kw) for kw in hook_types["story"]):
        detected_type = "story"

    # Identify attention elements
    attention_elements = []
    if "$" in title or any(kw in title_lower for kw in ["revenue", "profit", "income"]):
        attention_elements.append("money")
    if any(kw in title_lower for kw in ["secret", "hidden", "nobody knows"]):
        attention_elements.append("exclusivity")
    if any(kw in title_lower for kw in ["fast", "quick", "instant", "minutes"]):
        attention_elements.append("speed")
    if any(c.isdigit() for c in title):
        attention_elements.append("specificity")

    return {
        "hook_type": detected_type,
        "hook_text": title[:100],  # First 100 chars
        "attention_elements": attention_elements,
    }


def _identify_triggers(title: str, description: str) -> list[dict]:
    """Identify emotional triggers in content."""
    text = f"{title} {description}".lower()
    triggers = []

    trigger_patterns = {
        "fear": ["lose", "miss", "fail", "mistake", "wrong", "risk"],
        "greed": ["money", "profit", "revenue", "$", "income", "rich"],
        "curiosity": ["secret", "hidden", "discover", "reveal", "truth"],
        "urgency": ["now", "today", "limited", "last chance", "deadline"],
        "fomo": ["everyone", "trending", "viral", "popular", "others"],
        "hope": ["success", "achieve", "transform", "change", "better"],
    }

    for trigger, keywords in trigger_patterns.items():
        matches = [kw for kw in keywords if kw in text]
        if matches:
            triggers.append(
                {
                    "trigger": trigger,
                    "evidence": f"Keywords: {', '.join(matches[:3])}",
                    "intensity": "high"
                    if len(matches) >= 3
                    else ("medium" if len(matches) >= 2 else "low"),
                }
            )

    return triggers


def _analyze_timing(content: dict) -> dict:
    """Analyze timing factors."""
    return {
        "day_relevance": "standard",  # Would need date context
        "trending_topics": [],  # Would need external trend data
        "seasonal_hook": None,
    }


def _identify_success_factors(content: dict, transcript: Optional[str]) -> dict:
    """Identify success factors."""
    outlier_score = content.get("outlier_score", 0)
    engagement_mods = content.get("engagement_modifiers", [])

    key_drivers = []
    reproducible = []
    unique = []

    if outlier_score >= 10:
        key_drivers.append("exceptional_performance_10x+")
    elif outlier_score >= 5:
        key_drivers.append("strong_performance_5x+")

    if engagement_mods:
        if isinstance(engagement_mods, list):
            key_drivers.extend(engagement_mods)
            reproducible.append(f"engagement_hooks: {', '.join(engagement_mods)}")
        elif isinstance(engagement_mods, (int, float)):
            if engagement_mods > 1.0:
                key_drivers.append(f"high_engagement_{engagement_mods:.1f}x")

    return {
        "key_drivers": key_drivers,
        "reproducible_elements": reproducible,
        "unique_circumstances": unique,
    }


def _assess_confidence(content: dict) -> str:
    """Assess confidence in virality assessment."""
    score = content.get("outlier_score", 0)

    if score >= 10:
        return "definite"
    elif score >= 5:
        return "likely"
    elif score >= 3:
        return "possible"
    else:
        return "unclear"


def _generate_replication_notes(analysis: dict) -> str:
    """Generate actionable replication notes from analysis."""
    notes = []

    hook = analysis.get("hook_analysis", {})
    if hook.get("hook_type"):
        notes.append(f"Hook pattern: {hook['hook_type']}")
    if hook.get("attention_elements"):
        notes.append(f"Use elements: {', '.join(hook['attention_elements'])}")

    triggers = analysis.get("emotional_triggers", [])
    high_triggers = [t["trigger"] for t in triggers if t.get("intensity") == "high"]
    if high_triggers:
        notes.append(f"Strong triggers: {', '.join(high_triggers)}")

    factors = analysis.get("success_factors", {})
    if factors.get("reproducible_elements"):
        notes.append(f"Replicate: {'; '.join(factors['reproducible_elements'])}")

    return " | ".join(notes) if notes else "Analyze manually"
