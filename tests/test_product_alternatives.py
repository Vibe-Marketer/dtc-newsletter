"""
Tests for product alternatives module.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from execution.product_alternatives import (
    ProductIdea,
    ProductAlternativesResult,
    generate_product_alternatives,
    generate_product_ideas,
    rank_products,
    research_pain_points,
)


class TestProductIdeaModel:
    """Tests for ProductIdea Pydantic model."""

    def test_valid_product_idea(self):
        """Test creating a valid ProductIdea."""
        idea = ProductIdea(
            concept="Calculator for inventory ordering",
            product_type="HTML tool",
            estimated_value="$47-67",
            build_complexity="medium",
            why_beats_affiliate="Keep 100% of revenue",
            pitch_angle="Stop guessing. Plug in 3 numbers. Get your order.",
        )
        assert idea.concept == "Calculator for inventory ordering"
        assert idea.product_type == "HTML tool"
        assert idea.build_complexity == "medium"

    def test_all_product_types(self):
        """Test all valid product types."""
        valid_types = [
            "HTML tool",
            "automation",
            "GPT",
            "Google Sheet",
            "PDF",
            "prompt pack",
        ]
        for product_type in valid_types:
            idea = ProductIdea(
                concept="Test product",
                product_type=product_type,
                estimated_value="$47",
                build_complexity="easy",
                why_beats_affiliate="Test reason",
                pitch_angle="Test pitch",
            )
            assert idea.product_type == product_type

    def test_all_complexity_levels(self):
        """Test all valid complexity levels."""
        for complexity in ["easy", "medium", "hard"]:
            idea = ProductIdea(
                concept="Test product",
                product_type="PDF",
                estimated_value="$47",
                build_complexity=complexity,
                why_beats_affiliate="Test reason",
                pitch_angle="Test pitch",
            )
            assert idea.build_complexity == complexity

    def test_invalid_product_type(self):
        """Test that invalid product type raises error."""
        with pytest.raises(Exception):
            ProductIdea(
                concept="Test product",
                product_type="invalid_type",
                estimated_value="$47",
                build_complexity="easy",
                why_beats_affiliate="Test reason",
                pitch_angle="Test pitch",
            )

    def test_invalid_complexity(self):
        """Test that invalid complexity raises error."""
        with pytest.raises(Exception):
            ProductIdea(
                concept="Test product",
                product_type="PDF",
                estimated_value="$47",
                build_complexity="impossible",
                why_beats_affiliate="Test reason",
                pitch_angle="Test pitch",
            )


class TestProductAlternativesResult:
    """Tests for ProductAlternativesResult model."""

    def test_valid_result(self):
        """Test creating a valid result."""
        product = ProductIdea(
            concept="Test product",
            product_type="PDF",
            estimated_value="$47",
            build_complexity="easy",
            why_beats_affiliate="Test reason",
            pitch_angle="Test pitch",
        )
        result = ProductAlternativesResult(
            products=[product],
            topic="email deliverability",
            generated_at="2026-01-31T15:00:00Z",
        )
        assert len(result.products) == 1
        assert result.topic == "email deliverability"

    def test_empty_products_list(self):
        """Test result with empty products list."""
        result = ProductAlternativesResult(
            products=[],
            topic="test topic",
            generated_at="2026-01-31T15:00:00Z",
        )
        assert result.products == []


class TestRankProducts:
    """Tests for rank_products function."""

    def test_ranks_by_value_complexity_ratio(self):
        """Test that products are ranked by value/complexity ratio."""
        # High value, low complexity = best
        product_best = ProductIdea(
            concept="Best product",
            product_type="PDF",
            estimated_value="$97",
            build_complexity="easy",
            why_beats_affiliate="Test",
            pitch_angle="Test",
        )
        # Low value, high complexity = worst
        product_worst = ProductIdea(
            concept="Worst product",
            product_type="HTML tool",
            estimated_value="$27",
            build_complexity="hard",
            why_beats_affiliate="Test",
            pitch_angle="Test",
        )
        # Medium
        product_mid = ProductIdea(
            concept="Mid product",
            product_type="GPT",
            estimated_value="$47",
            build_complexity="medium",
            why_beats_affiliate="Test",
            pitch_angle="Test",
        )

        ranked = rank_products([product_worst, product_mid, product_best])

        assert ranked[0].concept == "Best product"
        assert ranked[2].concept == "Worst product"

    def test_handles_price_ranges(self):
        """Test that price ranges are handled correctly."""
        product_high = ProductIdea(
            concept="High value",
            product_type="PDF",
            estimated_value="$67-97",  # Average: 82
            build_complexity="easy",
            why_beats_affiliate="Test",
            pitch_angle="Test",
        )
        product_low = ProductIdea(
            concept="Low value",
            product_type="PDF",
            estimated_value="$27-37",  # Average: 32
            build_complexity="easy",
            why_beats_affiliate="Test",
            pitch_angle="Test",
        )

        ranked = rank_products([product_low, product_high])

        # Higher average value should rank first
        assert ranked[0].concept == "High value"

    def test_handles_single_price(self):
        """Test that single prices are handled correctly."""
        product = ProductIdea(
            concept="Test",
            product_type="PDF",
            estimated_value="$67",
            build_complexity="easy",
            why_beats_affiliate="Test",
            pitch_angle="Test",
        )

        ranked = rank_products([product])
        assert len(ranked) == 1

    def test_handles_no_price(self):
        """Test fallback for value strings without numbers."""
        product = ProductIdea(
            concept="Test",
            product_type="PDF",
            estimated_value="Variable pricing",
            build_complexity="easy",
            why_beats_affiliate="Test",
            pitch_angle="Test",
        )

        ranked = rank_products([product])
        assert len(ranked) == 1

    def test_empty_list(self):
        """Test ranking empty list."""
        ranked = rank_products([])
        assert ranked == []

    def test_preserves_product_data(self):
        """Test that ranking preserves all product data."""
        product = ProductIdea(
            concept="Original concept",
            product_type="automation",
            estimated_value="$97",
            build_complexity="hard",
            why_beats_affiliate="Original reason",
            pitch_angle="Original pitch angle",
        )

        ranked = rank_products([product])

        assert ranked[0].concept == "Original concept"
        assert ranked[0].product_type == "automation"
        assert ranked[0].why_beats_affiliate == "Original reason"
        assert ranked[0].pitch_angle == "Original pitch angle"


class TestResearchPainPoints:
    """Tests for research_pain_points function."""

    def test_calls_perplexity_api(self):
        """Test that Perplexity API is called correctly."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Pain point 1: Issue with X"

        with patch(
            "execution.product_alternatives.get_perplexity_client"
        ) as mock_client:
            mock_client.return_value.chat.completions.create.return_value = (
                mock_response
            )

            result = research_pain_points("email deliverability")

            assert "Pain point 1" in result
            mock_client.return_value.chat.completions.create.assert_called_once()

    def test_includes_newsletter_context(self):
        """Test that newsletter context is included in prompt."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Research result"

        with patch(
            "execution.product_alternatives.get_perplexity_client"
        ) as mock_client:
            mock_client.return_value.chat.completions.create.return_value = (
                mock_response
            )

            research_pain_points("topic", newsletter_context="This week covers spam")

            call_args = mock_client.return_value.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]
            assert "This week covers spam" in messages[1]["content"]

    def test_raises_on_api_error(self):
        """Test that API errors are raised as RuntimeError."""
        with patch(
            "execution.product_alternatives.get_perplexity_client"
        ) as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception(
                "API Error"
            )

            with pytest.raises(RuntimeError, match="Perplexity API error"):
                research_pain_points("topic")


class TestGenerateProductIdeas:
    """Tests for generate_product_ideas function."""

    def test_parses_claude_json_response(self):
        """Test that Claude JSON response is parsed correctly."""
        json_response = json.dumps(
            [
                {
                    "concept": "Test concept",
                    "product_type": "PDF",
                    "estimated_value": "$47",
                    "build_complexity": "easy",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Test pitch",
                }
            ]
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json_response

        with patch("execution.product_alternatives.get_claude_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response

            result = generate_product_ideas("topic", "pain points")

            assert len(result) == 1
            assert result[0].concept == "Test concept"

    def test_handles_markdown_code_blocks(self):
        """Test that markdown code blocks are stripped."""
        json_response = """```json
[
    {
        "concept": "Test concept",
        "product_type": "PDF",
        "estimated_value": "$47",
        "build_complexity": "easy",
        "why_beats_affiliate": "Test reason",
        "pitch_angle": "Test pitch"
    }
]
```"""

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json_response

        with patch("execution.product_alternatives.get_claude_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response

            result = generate_product_ideas("topic", "pain points")

            assert len(result) == 1
            assert result[0].concept == "Test concept"

    def test_skips_invalid_products(self):
        """Test that invalid products are skipped."""
        json_response = json.dumps(
            [
                {
                    "concept": "Valid product",
                    "product_type": "PDF",
                    "estimated_value": "$47",
                    "build_complexity": "easy",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Test pitch",
                },
                {
                    "concept": "Invalid product",
                    "product_type": "INVALID_TYPE",  # Invalid
                    "estimated_value": "$47",
                    "build_complexity": "easy",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Test pitch",
                },
            ]
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json_response

        with patch("execution.product_alternatives.get_claude_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response

            result = generate_product_ideas("topic", "pain points")

            # Only valid product should be returned
            assert len(result) == 1
            assert result[0].concept == "Valid product"

    def test_raises_on_api_error(self):
        """Test that API errors are raised as RuntimeError."""
        with patch("execution.product_alternatives.get_claude_client") as mock_client:
            mock_client.return_value.messages.create.side_effect = Exception(
                "API Error"
            )

            with pytest.raises(RuntimeError, match="Claude API error"):
                generate_product_ideas("topic", "pain points")


class TestGenerateProductAlternatives:
    """Tests for generate_product_alternatives main function."""

    def test_two_stage_generation(self):
        """Test that both Perplexity and Claude are called."""
        # Mock Perplexity response
        perplexity_response = MagicMock()
        perplexity_response.choices = [MagicMock()]
        perplexity_response.choices[0].message.content = "Pain points"

        # Mock Claude response
        claude_response = MagicMock()
        claude_response.content = [MagicMock()]
        claude_response.content[0].text = json.dumps(
            [
                {
                    "concept": "Test product",
                    "product_type": "PDF",
                    "estimated_value": "$47",
                    "build_complexity": "easy",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Test pitch",
                }
            ]
        )

        with patch(
            "execution.product_alternatives.get_perplexity_client"
        ) as mock_perplexity:
            with patch(
                "execution.product_alternatives.get_claude_client"
            ) as mock_claude:
                mock_perplexity.return_value.chat.completions.create.return_value = (
                    perplexity_response
                )
                mock_claude.return_value.messages.create.return_value = claude_response

                result = generate_product_alternatives("email deliverability")

                # Both APIs should be called
                mock_perplexity.return_value.chat.completions.create.assert_called_once()
                mock_claude.return_value.messages.create.assert_called_once()

                assert len(result.products) == 1
                assert result.topic == "email deliverability"

    def test_retries_perplexity_on_failure(self):
        """Test that Perplexity is retried once on failure."""
        # Mock Perplexity to fail first, succeed second
        perplexity_response = MagicMock()
        perplexity_response.choices = [MagicMock()]
        perplexity_response.choices[0].message.content = "Pain points"

        # Mock Claude response
        claude_response = MagicMock()
        claude_response.content = [MagicMock()]
        claude_response.content[0].text = json.dumps(
            [
                {
                    "concept": "Test product",
                    "product_type": "PDF",
                    "estimated_value": "$47",
                    "build_complexity": "easy",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Test pitch",
                }
            ]
        )

        with patch(
            "execution.product_alternatives.get_perplexity_client"
        ) as mock_perplexity:
            with patch(
                "execution.product_alternatives.get_claude_client"
            ) as mock_claude:
                # First call fails, second succeeds
                mock_perplexity.return_value.chat.completions.create.side_effect = [
                    Exception("API Error"),
                    perplexity_response,
                ]
                mock_claude.return_value.messages.create.return_value = claude_response

                result = generate_product_alternatives("topic")

                # Perplexity should be called twice (retry)
                assert (
                    mock_perplexity.return_value.chat.completions.create.call_count == 2
                )
                assert len(result.products) == 1

    def test_uses_generic_pain_points_on_double_failure(self):
        """Test fallback to generic pain points when Perplexity fails twice."""
        # Mock Claude response
        claude_response = MagicMock()
        claude_response.content = [MagicMock()]
        claude_response.content[0].text = json.dumps(
            [
                {
                    "concept": "Test product",
                    "product_type": "PDF",
                    "estimated_value": "$47",
                    "build_complexity": "easy",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Test pitch",
                }
            ]
        )

        with patch(
            "execution.product_alternatives.get_perplexity_client"
        ) as mock_perplexity:
            with patch(
                "execution.product_alternatives.get_claude_client"
            ) as mock_claude:
                # Always fail
                mock_perplexity.return_value.chat.completions.create.side_effect = (
                    Exception("API Error")
                )
                mock_claude.return_value.messages.create.return_value = claude_response

                result = generate_product_alternatives("topic")

                # Perplexity should be called twice (initial + retry)
                assert (
                    mock_perplexity.return_value.chat.completions.create.call_count == 2
                )

                # Should still return products (using generic pain points)
                assert len(result.products) == 1

    def test_limits_to_three_products(self):
        """Test that result is limited to 3 products."""
        # Mock Perplexity response
        perplexity_response = MagicMock()
        perplexity_response.choices = [MagicMock()]
        perplexity_response.choices[0].message.content = "Pain points"

        # Mock Claude response with 5 products
        claude_response = MagicMock()
        claude_response.content = [MagicMock()]
        claude_response.content[0].text = json.dumps(
            [
                {
                    "concept": f"Product {i}",
                    "product_type": "PDF",
                    "estimated_value": "$47",
                    "build_complexity": "easy",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Test pitch",
                }
                for i in range(5)
            ]
        )

        with patch(
            "execution.product_alternatives.get_perplexity_client"
        ) as mock_perplexity:
            with patch(
                "execution.product_alternatives.get_claude_client"
            ) as mock_claude:
                mock_perplexity.return_value.chat.completions.create.return_value = (
                    perplexity_response
                )
                mock_claude.return_value.messages.create.return_value = claude_response

                result = generate_product_alternatives("topic")

                # Should be limited to 3
                assert len(result.products) == 3

    def test_includes_timestamp(self):
        """Test that result includes generation timestamp."""
        # Mock Perplexity response
        perplexity_response = MagicMock()
        perplexity_response.choices = [MagicMock()]
        perplexity_response.choices[0].message.content = "Pain points"

        # Mock Claude response
        claude_response = MagicMock()
        claude_response.content = [MagicMock()]
        claude_response.content[0].text = json.dumps(
            [
                {
                    "concept": "Test product",
                    "product_type": "PDF",
                    "estimated_value": "$47",
                    "build_complexity": "easy",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Test pitch",
                }
            ]
        )

        with patch(
            "execution.product_alternatives.get_perplexity_client"
        ) as mock_perplexity:
            with patch(
                "execution.product_alternatives.get_claude_client"
            ) as mock_claude:
                mock_perplexity.return_value.chat.completions.create.return_value = (
                    perplexity_response
                )
                mock_claude.return_value.messages.create.return_value = claude_response

                result = generate_product_alternatives("topic")

                # Should have ISO timestamp
                assert result.generated_at is not None
                # Verify it's parseable
                datetime.fromisoformat(result.generated_at.replace("Z", "+00:00"))

    def test_products_are_ranked(self):
        """Test that products are ranked by value/complexity."""
        # Mock Perplexity response
        perplexity_response = MagicMock()
        perplexity_response.choices = [MagicMock()]
        perplexity_response.choices[0].message.content = "Pain points"

        # Mock Claude response with products in wrong order
        claude_response = MagicMock()
        claude_response.content = [MagicMock()]
        claude_response.content[0].text = json.dumps(
            [
                {
                    "concept": "Worst - low value, hard",
                    "product_type": "HTML tool",
                    "estimated_value": "$27",
                    "build_complexity": "hard",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Test pitch",
                },
                {
                    "concept": "Best - high value, easy",
                    "product_type": "PDF",
                    "estimated_value": "$97",
                    "build_complexity": "easy",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Test pitch",
                },
            ]
        )

        with patch(
            "execution.product_alternatives.get_perplexity_client"
        ) as mock_perplexity:
            with patch(
                "execution.product_alternatives.get_claude_client"
            ) as mock_claude:
                mock_perplexity.return_value.chat.completions.create.return_value = (
                    perplexity_response
                )
                mock_claude.return_value.messages.create.return_value = claude_response

                result = generate_product_alternatives("topic")

                # Best product should be first
                assert "Best" in result.products[0].concept


class TestPitchAngles:
    """Tests for pitch angle generation."""

    def test_pitch_angle_included_in_product(self):
        """Test that pitch angles are included in products."""
        # Mock Perplexity response
        perplexity_response = MagicMock()
        perplexity_response.choices = [MagicMock()]
        perplexity_response.choices[0].message.content = "Pain points"

        # Mock Claude response with specific pitch angle
        claude_response = MagicMock()
        claude_response.content = [MagicMock()]
        claude_response.content[0].text = json.dumps(
            [
                {
                    "concept": "Test product",
                    "product_type": "PDF",
                    "estimated_value": "$47",
                    "build_complexity": "easy",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Stop guessing. This tool gives you the answer in 30 seconds.",
                }
            ]
        )

        with patch(
            "execution.product_alternatives.get_perplexity_client"
        ) as mock_perplexity:
            with patch(
                "execution.product_alternatives.get_claude_client"
            ) as mock_claude:
                mock_perplexity.return_value.chat.completions.create.return_value = (
                    perplexity_response
                )
                mock_claude.return_value.messages.create.return_value = claude_response

                result = generate_product_alternatives("topic")

                assert "Stop guessing" in result.products[0].pitch_angle

    def test_voice_guidance_in_prompt(self):
        """Test that voice guidance is included in Claude prompt."""
        # Mock Perplexity response
        perplexity_response = MagicMock()
        perplexity_response.choices = [MagicMock()]
        perplexity_response.choices[0].message.content = "Pain points"

        # Mock Claude response
        claude_response = MagicMock()
        claude_response.content = [MagicMock()]
        claude_response.content[0].text = json.dumps(
            [
                {
                    "concept": "Test product",
                    "product_type": "PDF",
                    "estimated_value": "$47",
                    "build_complexity": "easy",
                    "why_beats_affiliate": "Test reason",
                    "pitch_angle": "Test pitch",
                }
            ]
        )

        with patch(
            "execution.product_alternatives.get_perplexity_client"
        ) as mock_perplexity:
            with patch(
                "execution.product_alternatives.get_claude_client"
            ) as mock_claude:
                mock_perplexity.return_value.chat.completions.create.return_value = (
                    perplexity_response
                )
                mock_claude.return_value.messages.create.return_value = claude_response

                generate_product_alternatives("topic")

                # Check that voice guidance was in the prompt
                call_args = mock_claude.return_value.messages.create.call_args
                messages = call_args.kwargs["messages"]
                prompt = messages[0]["content"]
                assert "Hormozi/Suby" in prompt
                assert "fluff" in prompt
