"""
Tests for monetization output formatter.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile

from execution.affiliate_discovery import AffiliateProgram
from execution.product_alternatives import ProductIdea
from execution.monetization_output import (
    MonetizationOption,
    affiliate_to_option,
    product_to_option,
    format_monetization_output,
    generate_ranking_rationale,
    save_output,
    load_output,
)


# Test fixtures
@pytest.fixture
def sample_affiliate() -> AffiliateProgram:
    """Create a sample affiliate program."""
    return AffiliateProgram(
        name="Klaviyo Partner Program",
        company="Klaviyo",
        commission_rate="20%",
        commission_type="percentage",
        is_recurring=True,
        product_description="Email marketing platform for e-commerce",
        topic_fit="Perfect for email deliverability topic",
        network="PartnerStack",
        signup_accessible=True,
    )


@pytest.fixture
def sample_product() -> ProductIdea:
    """Create a sample product idea."""
    return ProductIdea(
        concept="Email deliverability checker tool",
        product_type="HTML tool",
        estimated_value="$47-67",
        build_complexity="medium",
        why_beats_affiliate="Keep 100% of revenue instead of 20%",
        pitch_angle="Check your deliverability in 30 seconds. No signup required.",
    )


@pytest.fixture
def sample_affiliates() -> list[AffiliateProgram]:
    """Create a list of sample affiliates."""
    return [
        AffiliateProgram(
            name="Klaviyo Partner Program",
            company="Klaviyo",
            commission_rate="20%",
            commission_type="percentage",
            is_recurring=True,
            product_description="Email marketing platform",
            topic_fit="Perfect for email deliverability",
            network="PartnerStack",
            signup_accessible=True,
        ),
        AffiliateProgram(
            name="Sendgrid Affiliate",
            company="Sendgrid",
            commission_rate="15%",
            commission_type="percentage",
            is_recurring=True,
            product_description="Email delivery service",
            topic_fit="Good for email infrastructure",
            network="Impact",
            signup_accessible=True,
        ),
        AffiliateProgram(
            name="Mailgun Program",
            company="Mailgun",
            commission_rate="$50",
            commission_type="flat_fee",
            is_recurring=False,
            product_description="Email API service",
            topic_fit="Technical email sending",
            network="direct",
            signup_accessible=True,
        ),
    ]


@pytest.fixture
def sample_products() -> list[ProductIdea]:
    """Create a list of sample products."""
    return [
        ProductIdea(
            concept="Email deliverability checker tool",
            product_type="HTML tool",
            estimated_value="$47-67",
            build_complexity="medium",
            why_beats_affiliate="Keep 100% of revenue",
            pitch_angle="Check deliverability in 30 seconds.",
        ),
        ProductIdea(
            concept="Subject line A/B test calculator",
            product_type="Google Sheet",
            estimated_value="$27-37",
            build_complexity="easy",
            why_beats_affiliate="Simple, immediate value",
            pitch_angle="Know which subject line wins in 2 minutes.",
        ),
        ProductIdea(
            concept="Email automation workflow templates",
            product_type="PDF",
            estimated_value="$37-47",
            build_complexity="easy",
            why_beats_affiliate="One-time creation, unlimited sales",
            pitch_angle="Copy these 5 workflows that convert.",
        ),
    ]


class TestMonetizationOption:
    """Tests for MonetizationOption dataclass."""

    def test_affiliate_option(self):
        """Test creating an affiliate option."""
        option = MonetizationOption(
            type="affiliate",
            name="Klaviyo",
            description="Email marketing",
            pitch_angle="Great for emails",
            commission_rate="20%",
            commission_quality="excellent",
            network="PartnerStack",
        )
        assert option.type == "affiliate"
        assert option.commission_rate == "20%"
        assert option.product_type is None

    def test_product_option(self):
        """Test creating a product option."""
        option = MonetizationOption(
            type="product",
            name="Email Checker",
            description="Checks deliverability",
            pitch_angle="Check in 30 seconds",
            product_type="HTML tool",
            build_complexity="medium",
            estimated_value="$47",
        )
        assert option.type == "product"
        assert option.product_type == "HTML tool"
        assert option.commission_rate is None


class TestAffiliateToOption:
    """Tests for affiliate_to_option conversion."""

    def test_converts_affiliate(self, sample_affiliate):
        """Test converting affiliate to option."""
        option = affiliate_to_option(sample_affiliate, "Test pitch")

        assert option.type == "affiliate"
        assert option.name == "Klaviyo Partner Program"
        assert option.description == "Email marketing platform for e-commerce"
        assert option.pitch_angle == "Test pitch"
        assert option.commission_rate == "20%"
        assert option.commission_quality == "excellent"  # 20% recurring
        assert option.network == "PartnerStack"

    def test_empty_pitch(self, sample_affiliate):
        """Test converting affiliate without pitch."""
        option = affiliate_to_option(sample_affiliate)

        assert option.pitch_angle == ""

    def test_classifies_commission(self):
        """Test that commission is classified correctly."""
        # Low recurring should be mediocre
        affiliate = AffiliateProgram(
            name="Test",
            company="Test",
            commission_rate="5%",
            commission_type="percentage",
            is_recurring=True,
            product_description="Test",
            topic_fit="Test",
            network="direct",
            signup_accessible=True,
        )
        option = affiliate_to_option(affiliate)
        assert option.commission_quality == "mediocre"

        # High one-time should be good
        affiliate2 = AffiliateProgram(
            name="Test2",
            company="Test2",
            commission_rate="35%",
            commission_type="percentage",
            is_recurring=False,
            product_description="Test",
            topic_fit="Test",
            network="direct",
            signup_accessible=True,
        )
        option2 = affiliate_to_option(affiliate2)
        assert option2.commission_quality == "good"


class TestProductToOption:
    """Tests for product_to_option conversion."""

    def test_converts_product(self, sample_product):
        """Test converting product to option."""
        option = product_to_option(sample_product)

        assert option.type == "product"
        assert option.name == "Email deliverability checker tool"
        assert option.description == "Keep 100% of revenue instead of 20%"
        assert (
            option.pitch_angle
            == "Check your deliverability in 30 seconds. No signup required."
        )
        assert option.product_type == "HTML tool"
        assert option.build_complexity == "medium"
        assert option.estimated_value == "$47-67"


class TestFormatMonetizationOutput:
    """Tests for format_monetization_output function."""

    def test_formats_full_output(self, sample_affiliates, sample_products):
        """Test formatting with both affiliates and products."""
        pitches = {
            "Klaviyo Partner Program": "Klaviyo pitch",
            "Sendgrid Affiliate": "Sendgrid pitch",
        }

        output = format_monetization_output(
            affiliates=sample_affiliates,
            products=sample_products,
            topic="email deliverability",
            pitches=pitches,
            include_rationale=False,  # Skip API call
        )

        # Check header
        assert "# Monetization Options: email deliverability" in output

        # Check affiliate table
        assert "## Top 3 Affiliate Opportunities" in output
        assert "Klaviyo Partner Program" in output
        assert "20%" in output
        assert "PartnerStack" in output

        # Check product table
        assert "## Top 3 Product Alternatives" in output
        assert "Email deliverability checker" in output
        assert "HTML tool" in output
        assert "$47-67" in output

        # Check full details
        assert "## Full Details" in output
        assert "### Affiliate #1" in output
        assert "### Product #1" in output

    def test_handles_empty_affiliates(self, sample_products):
        """Test handling when no affiliates found."""
        output = format_monetization_output(
            affiliates=[],
            products=sample_products,
            topic="test topic",
            pitches={},
            include_rationale=False,
        )

        assert "*No affiliate programs found for this topic.*" in output

    def test_handles_empty_products(self, sample_affiliates):
        """Test handling when no products generated."""
        output = format_monetization_output(
            affiliates=sample_affiliates,
            products=[],
            topic="test topic",
            pitches={},
            include_rationale=False,
        )

        assert "*No product alternatives generated.*" in output

    def test_handles_single_affiliate(self):
        """Test note when only one affiliate found."""
        affiliate = AffiliateProgram(
            name="Only One",
            company="Only",
            commission_rate="10%",
            commission_type="percentage",
            is_recurring=True,
            product_description="Test",
            topic_fit="Test",
            network="direct",
            signup_accessible=True,
        )

        output = format_monetization_output(
            affiliates=[affiliate],
            products=[],
            topic="test",
            pitches={},
            include_rationale=False,
        )

        assert "Limited affiliate options" in output

    def test_limits_to_three(self, sample_affiliates, sample_products):
        """Test that output is limited to 3 of each."""
        # Add more affiliates and products
        extra_affiliate = AffiliateProgram(
            name="Extra",
            company="Extra",
            commission_rate="10%",
            commission_type="percentage",
            is_recurring=True,
            product_description="Test",
            topic_fit="Test",
            network="direct",
            signup_accessible=True,
        )
        extra_product = ProductIdea(
            concept="Extra product",
            product_type="PDF",
            estimated_value="$27",
            build_complexity="easy",
            why_beats_affiliate="Extra",
            pitch_angle="Extra pitch",
        )

        affiliates = sample_affiliates + [extra_affiliate]
        products = sample_products + [extra_product]

        output = format_monetization_output(
            affiliates=affiliates,
            products=products,
            topic="test",
            pitches={},
            include_rationale=False,
        )

        # Count occurrences of "Affiliate #" and "Product #"
        affiliate_details = output.count("### Affiliate #")
        product_details = output.count("### Product #")

        assert affiliate_details == 3
        assert product_details == 3

    def test_includes_timestamp(self, sample_affiliates, sample_products):
        """Test that output includes timestamp."""
        output = format_monetization_output(
            affiliates=sample_affiliates,
            products=sample_products,
            topic="test",
            pitches={},
            include_rationale=False,
        )

        assert "*Generated:" in output
        assert "UTC*" in output

    def test_truncates_long_concepts(self, sample_products):
        """Test that long concept names are truncated in table."""
        long_product = ProductIdea(
            concept="This is a very long concept name that should be truncated in the table display because it would break the formatting",
            product_type="PDF",
            estimated_value="$27",
            build_complexity="easy",
            why_beats_affiliate="Test",
            pitch_angle="Test",
        )

        output = format_monetization_output(
            affiliates=[],
            products=[long_product],
            topic="test",
            pitches={},
            include_rationale=False,
        )

        # Check table has truncated version
        assert "..." in output


class TestGenerateRankingRationale:
    """Tests for generate_ranking_rationale function."""

    def test_generates_rationale(self):
        """Test rationale generation with mocked API."""
        affiliate_options = [
            MonetizationOption(
                type="affiliate",
                name="Affiliate 1",
                description="Test",
                pitch_angle="Test",
                commission_rate="20%",
                commission_quality="excellent",
                network="PartnerStack",
            ),
            MonetizationOption(
                type="affiliate",
                name="Affiliate 2",
                description="Test",
                pitch_angle="Test",
                commission_rate="10%",
                commission_quality="good",
                network="Impact",
            ),
        ]

        product_options = [
            MonetizationOption(
                type="product",
                name="Product 1",
                description="Test",
                pitch_angle="Test",
                product_type="HTML tool",
                build_complexity="medium",
                estimated_value="$67",
            ),
        ]

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps(
            {
                "affiliates": ["#1 beats #2 because: Higher commission rate"],
                "products": ["#1 is the only option"],
            }
        )

        with patch("execution.monetization_output.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response

            result = generate_ranking_rationale(affiliate_options, product_options)

            assert "affiliates" in result
            assert "products" in result
            assert len(result["affiliates"]) == 1

    def test_handles_no_api_key(self):
        """Test graceful handling when no API key."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=True):
            result = generate_ranking_rationale([], [])
            assert result == {"affiliates": [], "products": []}

    def test_handles_api_error(self):
        """Test graceful handling of API errors."""
        affiliate_options = [
            MonetizationOption(
                type="affiliate",
                name="Test",
                description="Test",
                pitch_angle="Test",
            )
        ]

        with patch("execution.monetization_output.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.side_effect = Exception(
                "API Error"
            )

            result = generate_ranking_rationale(affiliate_options, [])

            # Should return empty, not raise
            assert result == {"affiliates": [], "products": []}


class TestSaveAndLoadOutput:
    """Tests for save_output and load_output functions."""

    def test_save_creates_file(self):
        """Test that save creates the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "monetization"
            content = "# Test Content\n\nThis is test content."

            filepath = save_output(content, "test-topic", output_dir=output_dir)

            assert filepath.exists()
            assert "test-topic" in filepath.name
            assert filepath.suffix == ".md"

    def test_save_creates_directory(self):
        """Test that save creates directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "monetization"
            content = "# Test"

            filepath = save_output(content, "test", output_dir=output_dir)

            assert filepath.exists()
            assert output_dir.exists()

    def test_save_includes_date(self):
        """Test that filename includes date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            content = "# Test"

            filepath = save_output(content, "test", output_dir=output_dir)

            # Filename should start with date
            from datetime import datetime

            today = datetime.now().strftime("%Y-%m-%d")
            assert filepath.name.startswith(today)

    def test_save_cleans_slug(self):
        """Test that topic slug is cleaned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            content = "# Test"

            filepath = save_output(
                content, "Email Deliverability & Open Rates!", output_dir=output_dir
            )

            # Should be lowercase, no special chars
            assert "email-deliverability" in filepath.name.lower()
            assert "&" not in filepath.name
            assert "!" not in filepath.name

    def test_load_returns_content(self):
        """Test that load returns file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            content = "# Test Content\n\nWith multiple lines."

            filepath = save_output(content, "test", output_dir=output_dir)
            loaded = load_output(filepath)

            assert loaded == content

    def test_load_raises_on_missing(self):
        """Test that load raises for missing file."""
        with pytest.raises(FileNotFoundError):
            load_output(Path("/nonexistent/file.md"))


class TestOutputFormat:
    """Tests for specific output format requirements per CONTEXT.md."""

    def test_table_headers(self, sample_affiliates, sample_products):
        """Test that table headers match spec."""
        output = format_monetization_output(
            affiliates=sample_affiliates,
            products=sample_products,
            topic="test",
            pitches={},
            include_rationale=False,
        )

        # Affiliate table headers
        assert "| # | Program | Commission | Quality | Network |" in output

        # Product table headers
        assert "| # | Concept | Type | Complexity | Value |" in output

    def test_pitch_angle_block_quote(self, sample_affiliates, sample_products):
        """Test that pitch angles use block quotes."""
        pitches = {"Klaviyo Partner Program": "This is the pitch"}

        output = format_monetization_output(
            affiliates=sample_affiliates,
            products=sample_products,
            topic="test",
            pitches=pitches,
            include_rationale=False,
        )

        # Pitch angles should be in block quotes
        assert "> This is the pitch" in output
        assert "> Check deliverability in 30 seconds." in output

    def test_includes_why_beats_affiliate(self, sample_products):
        """Test that 'Why It Beats Affiliate' is included for products."""
        output = format_monetization_output(
            affiliates=[],
            products=sample_products,
            topic="test",
            pitches={},
            include_rationale=False,
        )

        assert "**Why It Beats Affiliate:**" in output
        assert "Keep 100% of revenue" in output
