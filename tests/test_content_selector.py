"""
Tests for content selector module.
DOE-VERSION: 2026.01.31
"""

import pytest

from execution.content_selector import (
    ContentSelection,
    _is_quotable,
    _is_tactical,
    _has_narrative_potential,
    _get_unique_sources,
    select_content_for_sections,
    get_selection_summary,
)


# === Test Data ===


def make_content(
    title: str,
    outlier_score: float = 3.0,
    source: str = "reddit",
    summary: str = "",
    content_id: str | None = None,
) -> dict:
    """Helper to create test content items."""
    return {
        "id": content_id or f"id_{title[:10]}",
        "title": title,
        "outlier_score": outlier_score,
        "source": source,
        "summary": summary,
        "url": f"https://example.com/{title[:10].replace(' ', '-')}",
    }


# === ContentSelection Dataclass Tests ===


class TestContentSelection:
    """Tests for ContentSelection dataclass."""

    def test_empty_selection(self):
        """Empty selection has all None values."""
        selection = ContentSelection()
        assert selection.section_1 is None
        assert selection.section_2 is None
        assert selection.section_3 is None
        assert selection.section_4_tool is None
        assert selection.sources_used == []

    def test_partial_selection(self):
        """Partial selection preserves values."""
        content = make_content("Test", 5.0, "youtube")
        selection = ContentSelection(
            section_1=content,
            sources_used=["youtube"],
        )
        assert selection.section_1 == content
        assert selection.section_2 is None
        assert selection.sources_used == ["youtube"]


# === Helper Function Tests ===


class TestIsQuotable:
    """Tests for _is_quotable helper."""

    def test_short_title_with_numbers(self):
        """Short title with numbers is quotable."""
        item = make_content("Made $50K in 30 days", summary="Revenue stats")
        assert _is_quotable(item) is True

    def test_short_title_with_percentage(self):
        """Short title with percentage is quotable."""
        item = make_content("Conversion rate jumped 200%")
        assert _is_quotable(item) is True

    def test_very_short_title(self):
        """Very short titles are quotable."""
        item = make_content("This changes everything")
        assert _is_quotable(item) is True

    def test_quote_indicator(self):
        """Title with quote indicator is quotable."""
        item = make_content('He said "Never give up on your dreams"')
        assert _is_quotable(item) is True

    def test_viral_indicator(self):
        """Title with viral indicator is quotable."""
        item = make_content("This viral TikTok strategy")
        assert _is_quotable(item) is True

    def test_long_generic_title(self):
        """Long generic title without indicators is not quotable."""
        item = make_content(
            "A comprehensive guide to understanding the fundamental principles of e-commerce marketing in the modern digital landscape"
        )
        assert _is_quotable(item) is False


class TestIsTactical:
    """Tests for _is_tactical helper."""

    def test_how_to_title(self):
        """How-to title is tactical."""
        item = make_content("How to increase ROAS by 50%")
        assert _is_tactical(item) is True

    def test_step_title(self):
        """Step-by-step title is tactical."""
        item = make_content("5 steps to launch your first product")
        assert _is_tactical(item) is True

    def test_strategy_title(self):
        """Strategy title is tactical."""
        item = make_content("My winning Facebook strategy for Q4")
        assert _is_tactical(item) is True

    def test_hack_title(self):
        """Hack title is tactical."""
        item = make_content("The one hack that doubled my conversions")
        assert _is_tactical(item) is True

    def test_tip_in_summary(self):
        """Tip in summary is tactical."""
        item = make_content("Quick win", summary="A great tip for beginners")
        assert _is_tactical(item) is True

    def test_framework_title(self):
        """Framework title is tactical."""
        item = make_content("My framework for product research")
        assert _is_tactical(item) is True

    def test_increased_keyword(self):
        """Increased results keyword is tactical."""
        item = make_content("What increased my sales by 3x")
        assert _is_tactical(item) is True

    def test_generic_title_not_tactical(self):
        """Generic title without keywords is not tactical."""
        item = make_content("Random thoughts about e-commerce")
        assert _is_tactical(item) is False


class TestHasNarrativePotential:
    """Tests for _has_narrative_potential helper."""

    def test_case_study_title(self):
        """Case study title has narrative potential."""
        item = make_content("Case study: How Brand X scaled to $1M")
        assert _has_narrative_potential(item) is True

    def test_story_title(self):
        """Story title has narrative potential."""
        item = make_content("My story from $0 to $100K")
        assert _has_narrative_potential(item) is True

    def test_lessons_learned(self):
        """Lessons learned has narrative potential."""
        item = make_content("What I learned after failing 3 times")
        assert _has_narrative_potential(item) is True

    def test_mistake_title(self):
        """Mistake title has narrative potential."""
        item = make_content("The costly mistake I made with ads")
        assert _has_narrative_potential(item) is True

    def test_journey_title(self):
        """Journey title has narrative potential."""
        item = make_content("My journey to 6 figures")
        assert _has_narrative_potential(item) is True

    def test_transformation_summary(self):
        """Transformation in summary has narrative potential."""
        item = make_content(
            "Brand update", summary="Complete transformation in 90 days"
        )
        assert _has_narrative_potential(item) is True

    def test_why_title(self):
        """Why title has narrative potential."""
        item = make_content("Why most DTC brands fail")
        assert _has_narrative_potential(item) is True

    def test_generic_not_narrative(self):
        """Generic title without keywords has no narrative potential."""
        item = make_content("Product announcement")
        assert _has_narrative_potential(item) is False


class TestGetUniqueSources:
    """Tests for _get_unique_sources helper."""

    def test_empty_selection(self):
        """Empty selection has 0 unique sources."""
        selection = ContentSelection()
        assert _get_unique_sources(selection) == 0

    def test_single_source(self):
        """Single source selection."""
        content = make_content("Test", source="reddit")
        selection = ContentSelection(section_1=content)
        assert _get_unique_sources(selection) == 1

    def test_two_unique_sources(self):
        """Two different sources."""
        selection = ContentSelection(
            section_1=make_content("Test1", source="reddit"),
            section_2=make_content("Test2", source="youtube"),
        )
        assert _get_unique_sources(selection) == 2

    def test_three_same_sources(self):
        """Three sections, same source."""
        selection = ContentSelection(
            section_1=make_content("Test1", source="reddit"),
            section_2=make_content("Test2", source="reddit"),
            section_3=make_content("Test3", source="reddit"),
        )
        assert _get_unique_sources(selection) == 1

    def test_three_different_sources(self):
        """Three sections, different sources."""
        selection = ContentSelection(
            section_1=make_content("Test1", source="reddit"),
            section_2=make_content("Test2", source="youtube"),
            section_3=make_content("Test3", source="perplexity"),
        )
        assert _get_unique_sources(selection) == 3


# === Main Selection Function Tests ===


class TestSelectContentForSections:
    """Tests for select_content_for_sections main function."""

    def test_empty_input(self):
        """Empty input returns empty selection."""
        selection = select_content_for_sections([])
        assert selection.section_1 is None
        assert selection.section_2 is None
        assert selection.section_3 is None
        assert selection.sources_used == []

    def test_single_item(self):
        """Single item is used for all applicable sections."""
        items = [make_content("How to scale to $1M", 5.0, "reddit")]
        selection = select_content_for_sections(items)

        # Should be used for section 1 (quotable) and section 2 (tactical)
        assert selection.section_1 is not None
        assert selection.section_2 is not None

    def test_highest_outlier_selected(self):
        """Highest outlier score items are prioritized."""
        items = [
            make_content("Low score item", 2.0, "reddit"),
            make_content("How to win", 5.0, "youtube"),
            make_content("Medium score", 3.0, "reddit"),
        ]
        selection = select_content_for_sections(items)

        # Section 2 should get the highest tactical item
        assert selection.section_2 is not None
        assert selection.section_2.get("outlier_score") == 5.0

    def test_diversity_constraint(self):
        """At least 2 different sources when possible."""
        items = [
            make_content("How to win big", 5.0, "reddit", content_id="1"),
            make_content("My journey to success", 4.5, "youtube", content_id="2"),
            make_content("The story of my brand", 4.0, "perplexity", content_id="3"),
        ]
        selection = select_content_for_sections(items)

        # Should have at least 2 different sources
        assert len(selection.sources_used) >= 2

    def test_tactical_prioritized_for_section_2(self):
        """Section 2 prioritizes tactical content."""
        items = [
            make_content(
                "Random news", 6.0, "reddit", content_id="1"
            ),  # Higher score but not tactical
            make_content(
                "5 steps to success", 5.0, "youtube", content_id="2"
            ),  # Tactical
        ]
        selection = select_content_for_sections(items)

        # Section 2 should get tactical content even if not highest score
        assert selection.section_2 is not None
        assert "steps" in selection.section_2.get("title", "").lower()

    def test_narrative_prioritized_for_section_3(self):
        """Section 3 prioritizes narrative content."""
        items = [
            make_content("How to win", 5.0, "reddit", content_id="1"),  # Tactical
            make_content(
                "My journey from $0 to $1M", 4.5, "youtube", content_id="2"
            ),  # Narrative
        ]
        selection = select_content_for_sections(items)

        # Section 3 should get narrative content
        assert selection.section_3 is not None
        assert "journey" in selection.section_3.get("title", "").lower()

    def test_quotable_for_section_1(self):
        """Section 1 prioritizes quotable content."""
        items = [
            make_content(
                "A very long comprehensive guide to understanding complex topics",
                5.0,
                "reddit",
            ),
            make_content("Made $50K in 7 days", 4.0, "youtube"),  # Short with numbers
        ]
        selection = select_content_for_sections(items)

        # Section 1 should get quotable content
        assert selection.section_1 is not None
        assert "$50K" in selection.section_1.get("title", "")

    def test_fallback_when_no_tactical(self):
        """Falls back to highest score when no tactical content."""
        items = [
            make_content("Random news item", 5.0, "reddit", content_id="1"),
            make_content("Another random post", 4.0, "youtube", content_id="2"),
        ]
        selection = select_content_for_sections(items)

        # Section 2 should fall back to highest score
        assert selection.section_2 is not None
        assert selection.section_2.get("outlier_score") == 5.0

    def test_fallback_when_no_narrative(self):
        """Falls back with different angle flag when no narrative content."""
        items = [
            make_content("How to win", 5.0, "reddit", content_id="1"),
            make_content("Another tactical post", 4.0, "youtube", content_id="2"),
        ]
        selection = select_content_for_sections(items)

        # Section 3 should have content (possibly with angle flag)
        assert selection.section_3 is not None

    def test_no_exact_duplicates_sections_2_3(self):
        """Sections 2 and 3 don't use the exact same content."""
        items = [
            make_content(
                "How to scale: my journey", 5.0, "reddit", content_id="1"
            ),  # Both tactical and narrative
            make_content("Another item", 4.0, "youtube", content_id="2"),
        ]
        selection = select_content_for_sections(items)

        # If both sections have content, they should be different
        if selection.section_2 and selection.section_3:
            s2_id = selection.section_2.get("id")
            s3_id = selection.section_3.get("id")
            assert s2_id != s3_id

    def test_section_1_can_overlap(self):
        """Section 1 can use same content as other sections (quote/hook is different use)."""
        items = [
            make_content(
                "Made $100K using this strategy", 5.0, "reddit", content_id="1"
            ),
        ]
        selection = select_content_for_sections(items)

        # Section 1 can share content with section 2
        assert selection.section_1 is not None
        assert selection.section_2 is not None

    def test_sources_used_populated(self):
        """sources_used list is correctly populated."""
        items = [
            make_content("How to win", 5.0, "reddit", content_id="1"),
            make_content("My story", 4.0, "youtube", content_id="2"),
        ]
        selection = select_content_for_sections(items)

        assert len(selection.sources_used) > 0
        assert all(isinstance(s, str) for s in selection.sources_used)


class TestGetSelectionSummary:
    """Tests for get_selection_summary helper."""

    def test_empty_selection(self):
        """Empty selection produces basic summary."""
        selection = ContentSelection()
        summary = get_selection_summary(selection)

        assert "Content Selection Summary" in summary
        assert "Diversity: 0 unique sources" in summary

    def test_full_selection(self):
        """Full selection produces detailed summary."""
        selection = ContentSelection(
            section_1=make_content("Quote item", 4.5, "reddit"),
            section_2=make_content("Tactical item", 5.0, "youtube"),
            section_3=make_content("Story item", 4.0, "perplexity"),
            sources_used=["reddit", "youtube", "perplexity"],
        )
        summary = get_selection_summary(selection)

        assert "Section 1 (Instant Reward)" in summary
        assert "Section 2 (What's Working)" in summary
        assert "Section 3 (The Breakdown)" in summary
        assert "reddit" in summary
        assert "youtube" in summary

    def test_different_angle_flag(self):
        """Different angle flag is shown in summary."""
        content = make_content("Test", 4.0, "reddit")
        content["_different_angle_needed"] = True
        selection = ContentSelection(
            section_3=content,
            sources_used=["reddit"],
        )
        summary = get_selection_summary(selection)

        assert "DIFFERENT ANGLE NEEDED" in summary
