"""
Tests for the Product Factory orchestrator.

Tests cover:
- ProductFactory instantiation
- discover_pain_points() returns list with suggestions
- create_product() calls ProductPackager
- from_pain_point() extracts problem correctly
- _suggest_product_types() logic for different categories
- CLI argument parsing
"""

import json
import pytest
from unittest.mock import MagicMock, patch, mock_open

from execution.product_factory import (
    ProductFactory,
    PRODUCT_TYPES,
    CATEGORY_PRODUCT_MAP,
    main,
)


class TestProductFactoryInstantiation:
    """Tests for ProductFactory initialization."""

    def test_instantiates_with_defaults(self):
        """ProductFactory can be instantiated with default parameters."""
        factory = ProductFactory()
        assert factory.claude_client is None
        assert factory.output_dir == "output/products"
        assert factory._packager is not None

    def test_instantiates_with_custom_client(self):
        """ProductFactory accepts custom Claude client."""
        mock_client = MagicMock()
        factory = ProductFactory(claude_client=mock_client)
        assert factory.claude_client is mock_client

    def test_instantiates_with_custom_output_dir(self):
        """ProductFactory accepts custom output directory."""
        factory = ProductFactory(output_dir="custom/output")
        assert factory.output_dir == "custom/output"


class TestDiscoverPainPoints:
    """Tests for discover_pain_points() method."""

    @patch("execution.product_factory.get_top_pain_points")
    def test_returns_list_with_suggestions(self, mock_get_top):
        """discover_pain_points returns list with suggested product types."""
        mock_get_top.return_value = [
            {
                "id": "abc123",
                "title": "Conversion rate is killing me",
                "body": "My store has traffic but no sales",
                "score": 100,
                "comments": 50,
                "engagement_score": 150,
                "url": "https://reddit.com/r/shopify/abc123",
                "keyword": "conversion",
                "subreddit": "shopify",
                "category": "conversion",
            }
        ]

        factory = ProductFactory()
        results = factory.discover_pain_points(limit=10)

        assert len(results) == 1
        assert "suggested_product_types" in results[0]
        assert isinstance(results[0]["suggested_product_types"], list)
        assert len(results[0]["suggested_product_types"]) > 0

    @patch("execution.product_factory.get_top_pain_points")
    def test_respects_limit_parameter(self, mock_get_top):
        """discover_pain_points passes limit to get_top_pain_points."""
        mock_get_top.return_value = []

        factory = ProductFactory()
        factory.discover_pain_points(limit=5)

        mock_get_top.assert_called_once_with(limit=5)

    @patch("execution.product_factory.get_top_pain_points")
    def test_handles_empty_results(self, mock_get_top):
        """discover_pain_points handles empty results gracefully."""
        mock_get_top.return_value = []

        factory = ProductFactory()
        results = factory.discover_pain_points()

        assert results == []


class TestCreateProduct:
    """Tests for create_product() method."""

    @patch("execution.product_factory.ProductPackager")
    def test_calls_packager_with_correct_spec(self, mock_packager_class):
        """create_product calls ProductPackager.package with correct spec."""
        mock_packager = MagicMock()
        mock_result = {
            "product_id": "abc123",
            "path": "output/products/abc123",
            "manifest": {"id": "abc123"},
            "url": None,
            "zip_path": "output/products/abc123/abc123.zip",
        }
        mock_packager.package.return_value = mock_result
        mock_packager_class.return_value = mock_packager

        factory = ProductFactory()

        result = factory.create_product(
            product_type="html_tool",
            solution_name="Profit Calculator",
            problem="Can't calculate profit margins",
            target_audience="Shopify owners",
            key_benefits=["Quick results", "Easy to use"],
        )

        # Verify packager was called
        mock_packager.package.assert_called_once()

        # Check the spec passed to packager
        call_args = mock_packager.package.call_args
        spec = call_args[0][0]
        assert spec.product_type == "html_tool"
        assert spec.solution_name == "Profit Calculator"
        assert spec.problem == "Can't calculate profit margins"
        assert spec.target_audience == "Shopify owners"
        assert spec.key_benefits == ["Quick results", "Easy to use"]

        # Verify result is returned
        assert result["product_id"] == "abc123"

    def test_raises_for_invalid_product_type(self):
        """create_product raises ValueError for invalid product type."""
        factory = ProductFactory()

        with pytest.raises(ValueError) as exc_info:
            factory.create_product(
                product_type="invalid_type",
                solution_name="Test",
                problem="Test problem",
                target_audience="Test audience",
                key_benefits=["Benefit"],
            )

        assert "Unknown product type: invalid_type" in str(exc_info.value)
        assert "Valid types:" in str(exc_info.value)


class TestFromPainPoint:
    """Tests for from_pain_point() method."""

    @patch.object(ProductFactory, "create_product")
    def test_extracts_problem_from_pain_point(self, mock_create):
        """from_pain_point extracts problem from title and body."""
        mock_create.return_value = {"product_id": "test123"}

        factory = ProductFactory()
        pain_point = {
            "title": "Shipping costs are killing my margins",
            "body": "Every order I ship costs me more than expected...",
            "category": "shipping",
        }

        factory.from_pain_point(pain_point, product_type="automation")

        # Check create_product was called with extracted problem
        call_args = mock_create.call_args
        problem = call_args[1]["problem"]
        assert "Shipping costs are killing my margins" in problem
        assert "Every order I ship" in problem

    @patch.object(ProductFactory, "create_product")
    def test_auto_suggests_product_type(self, mock_create):
        """from_pain_point auto-suggests product type when not provided."""
        mock_create.return_value = {"product_id": "test123"}

        factory = ProductFactory()
        pain_point = {
            "title": "Conversion rate is low",
            "body": "Need help with checkout",
            "category": "conversion",
        }

        factory.from_pain_point(pain_point)

        # For conversion category, should suggest html_tool or gpt_config
        call_args = mock_create.call_args
        product_type = call_args[1]["product_type"]
        assert product_type in ["html_tool", "gpt_config"]

    @patch.object(ProductFactory, "create_product")
    def test_generates_solution_name(self, mock_create):
        """from_pain_point generates a solution name from title."""
        mock_create.return_value = {"product_id": "test123"}

        factory = ProductFactory()
        pain_point = {
            "title": "Pricing strategy is broken",
            "body": "",
            "category": "pricing",
        }

        factory.from_pain_point(pain_point, product_type="html_tool")

        call_args = mock_create.call_args
        name = call_args[1]["solution_name"]
        # Should contain key words and type suffix
        assert "Calculator" in name  # html_tool suffix


class TestSuggestProductTypes:
    """Tests for _suggest_product_types() method."""

    def test_shipping_suggests_automation_sheets(self):
        """Shipping category suggests automation and sheets."""
        factory = ProductFactory()
        pain_point = {"title": "Test", "body": "", "category": "shipping"}

        suggestions = factory._suggest_product_types(pain_point)

        assert "automation" in suggestions
        assert "sheets" in suggestions

    def test_conversion_suggests_html_tool_gpt(self):
        """Conversion category suggests html_tool and gpt_config."""
        factory = ProductFactory()
        pain_point = {"title": "Test", "body": "", "category": "conversion"}

        suggestions = factory._suggest_product_types(pain_point)

        assert "html_tool" in suggestions
        assert "gpt_config" in suggestions

    def test_calculator_keyword_adds_html_tool(self):
        """Calculator keyword boosts html_tool suggestion."""
        factory = ProductFactory()
        pain_point = {
            "title": "Need a profit calculator",
            "body": "How do I calculate margins?",
            "category": "other",
        }

        suggestions = factory._suggest_product_types(pain_point)

        # html_tool should be first due to "calculator" keyword
        assert suggestions[0] == "html_tool"

    def test_automate_keyword_adds_automation(self):
        """Automation keyword boosts automation suggestion."""
        factory = ProductFactory()
        pain_point = {
            "title": "How to automate fulfillment",
            "body": "Tired of manual work",
            "category": "other",
        }

        suggestions = factory._suggest_product_types(pain_point)

        assert "automation" in suggestions[:2]

    def test_gpt_keyword_adds_gpt_config(self):
        """GPT/AI keyword boosts gpt_config suggestion."""
        factory = ProductFactory()
        pain_point = {
            "title": "ChatGPT for customer service",
            "body": "Want AI to help with support",
            "category": "other",
        }

        suggestions = factory._suggest_product_types(pain_point)

        assert "gpt_config" in suggestions[:2]

    def test_categorizes_uncategorized_pain_point(self):
        """_suggest_product_types categorizes pain point if needed."""
        factory = ProductFactory()
        pain_point = {
            "title": "Shipping nightmare",
            "body": "Delivery issues everywhere",
            # No category key
        }

        suggestions = factory._suggest_product_types(pain_point)

        # Should have run categorization and returned suggestions
        assert len(suggestions) > 0


class TestCLIArgumentParsing:
    """Tests for CLI argument parsing."""

    @patch("execution.product_factory.ProductFactory")
    @patch("execution.product_factory.ClaudeClient")
    def test_discover_flag_calls_discover(self, mock_claude, mock_factory_class):
        """--discover flag calls discover_pain_points."""
        mock_factory = MagicMock()
        mock_factory.discover_pain_points.return_value = []
        mock_factory_class.return_value = mock_factory

        with patch("sys.argv", ["product_factory.py", "--discover"]):
            main()

        mock_factory.discover_pain_points.assert_called_once()

    @patch("execution.product_factory.ProductFactory")
    @patch("execution.product_factory.ClaudeClient")
    def test_create_requires_type_name_problem(self, mock_claude, mock_factory_class):
        """--create requires --type, --name, and --problem."""
        with patch("sys.argv", ["product_factory.py", "--create"]):
            with pytest.raises(SystemExit):
                main()

    @patch("execution.product_factory.ProductFactory")
    @patch("execution.product_factory.ClaudeClient")
    def test_create_with_all_args_calls_create(self, mock_claude, mock_factory_class):
        """--create with all required args calls create_product."""
        mock_factory = MagicMock()
        mock_factory.create_product.return_value = {
            "product_id": "test123",
            "path": "output/products/test123",
            "manifest": {
                "pricing": {"price_display": "$27", "perceived_value": "$100+"}
            },
            "url": None,
            "zip_path": "output/products/test123/test123.zip",
        }
        mock_factory_class.return_value = mock_factory

        with patch(
            "sys.argv",
            [
                "product_factory.py",
                "--create",
                "--type",
                "html_tool",
                "--name",
                "Test Product",
                "--problem",
                "Test problem",
            ],
        ):
            main()

        mock_factory.create_product.assert_called_once()

    @patch("execution.product_factory.ProductFactory")
    @patch("execution.product_factory.ClaudeClient")
    @patch("builtins.open", mock_open(read_data='{"title": "Test", "body": ""}'))
    def test_from_pain_point_reads_file(self, mock_claude, mock_factory_class):
        """--from-pain-point reads JSON file and calls from_pain_point."""
        mock_factory = MagicMock()
        mock_factory.from_pain_point.return_value = {
            "product_id": "test123",
            "path": "output/products/test123",
            "manifest": {"pricing": {"price_display": "$27"}},
            "url": None,
            "zip_path": "output/products/test123/test123.zip",
        }
        mock_factory_class.return_value = mock_factory

        with patch(
            "sys.argv",
            [
                "product_factory.py",
                "--from-pain-point",
                "test.json",
                "--type",
                "automation",
            ],
        ):
            main()

        mock_factory.from_pain_point.assert_called_once()


class TestCLIFailsGracefully:
    """Tests for graceful CLI failure handling."""

    def test_cli_requires_mode_selection(self):
        """CLI requires one of --discover, --create, or --from-pain-point."""
        with patch("sys.argv", ["product_factory.py"]):
            with pytest.raises(SystemExit):
                main()

    @patch("execution.product_factory.ClaudeClient")
    def test_continues_without_claude_client(self, mock_claude_class):
        """CLI continues even if Claude client initialization fails."""
        mock_claude_class.side_effect = ValueError("No API key")

        with patch("execution.product_factory.ProductFactory") as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory.discover_pain_points.return_value = []
            mock_factory_class.return_value = mock_factory

            with patch("sys.argv", ["product_factory.py", "--discover"]):
                main()  # Should not raise

            # Factory should be created with claude_client=None
            mock_factory_class.assert_called_once()
            call_kwargs = mock_factory_class.call_args[1]
            assert call_kwargs["claude_client"] is None
