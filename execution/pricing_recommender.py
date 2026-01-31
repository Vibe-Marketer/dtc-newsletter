"""
Pricing recommender for the Product Factory.
DOE-VERSION: 2026.01.31

Recommends optimal pricing for digital products based on:
- Product type (determines base price range)
- Value signals (time saved, money impact, complexity, exclusivity)
- Perceived value multiplier (what alternatives cost)

Price ranges: $17-$97 based on product type and value signals.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Pricing tiers by product type
# base: starting price with weak signals
# premium: max price with strong signals
# perceived_multiplier: factor to calculate perceived value (e.g., 10x = "$470+ worth")
PRICING_TIERS = {
    "html_tool": {
        "base": 27,
        "premium": 47,
        "perceived_multiplier": 10,
        "description": "Single-file HTML tools and calculators",
    },
    "automation": {
        "base": 47,
        "premium": 97,
        "perceived_multiplier": 15,
        "description": "Python automation scripts with CLI",
    },
    "gpt_config": {
        "base": 27,
        "premium": 47,
        "perceived_multiplier": 8,
        "description": "Custom GPT configuration packages",
    },
    "sheets": {
        "base": 27,
        "premium": 47,
        "perceived_multiplier": 10,
        "description": "Google Sheets templates and trackers",
    },
    "pdf": {
        "base": 17,
        "premium": 37,
        "perceived_multiplier": 5,
        "description": "PDF guides and frameworks",
    },
    "prompt_pack": {
        "base": 17,
        "premium": 27,
        "perceived_multiplier": 5,
        "description": "Curated prompt collections",
    },
}

# Value signals that affect pricing
# Each signal has a weight that contributes to signal_strength calculation
VALUE_SIGNALS = {
    "time_saved": {
        "description": "saves X hours/week",
        "weight": 0.3,
        "examples": ["2 hours/week", "10 hours/month", "full day"],
    },
    "money_impact": {
        "description": "generates/saves $X",
        "weight": 0.35,
        "examples": ["$500/month", "2x ROAS", "$10k saved"],
    },
    "complexity": {
        "description": "replaces X-step process",
        "weight": 0.2,
        "examples": ["10-step process", "3 tools", "manual work"],
    },
    "exclusivity": {
        "description": "insider/advanced technique",
        "weight": 0.15,
        "examples": [
            "used by 7-figure brands",
            "not available elsewhere",
            "proprietary",
        ],
    },
}


class PricingRecommender:
    """
    Recommends optimal pricing for digital products.

    Uses product type to determine base price range, then adjusts
    based on value signals (time saved, money impact, etc.).
    """

    def __init__(self):
        """Initialize the pricing recommender."""
        self._pricing_tiers = PRICING_TIERS
        self._value_signals = VALUE_SIGNALS

    def recommend(
        self,
        product_type: str,
        value_signals: Optional[dict] = None,
    ) -> dict:
        """
        Recommend pricing for a product.

        Args:
            product_type: One of the product types in PRICING_TIERS
            value_signals: Optional dict with signal values (0.0-1.0)
                          Keys: time_saved, money_impact, complexity, exclusivity

        Returns:
            Dict with:
                - price_cents: Recommended price in cents
                - price_display: Formatted price string (e.g., "$47")
                - perceived_value: Perceived value statement
                - justification: Why this price makes sense

        Raises:
            ValueError: If product_type is not recognized
        """
        # Validate product type
        if product_type not in self._pricing_tiers:
            valid_types = ", ".join(self._pricing_tiers.keys())
            raise ValueError(
                f"Unknown product type: {product_type}. Valid types: {valid_types}"
            )

        tier = self._pricing_tiers[product_type]

        # Calculate signal strength
        if value_signals:
            signal_strength = self._calculate_signal_strength(value_signals)
        else:
            signal_strength = 0.5  # Default to middle

        # Select tier based on signal strength
        selected_tier = self._select_tier(product_type, signal_strength)

        # Calculate price
        if selected_tier == "premium":
            price = tier["premium"]
        else:
            price = tier["base"]

        # Calculate perceived value
        perceived_value = self._calculate_perceived_value(product_type, value_signals)

        # Generate justification
        justification = self._generate_justification(
            product_type, price, perceived_value, value_signals
        )

        return {
            "price_cents": price * 100,  # Convert to cents
            "price_display": f"${price}",
            "perceived_value": perceived_value,
            "justification": justification,
        }

    def _calculate_perceived_value(
        self,
        product_type: str,
        value_signals: Optional[dict] = None,
    ) -> str:
        """
        Generate perceived value statement.

        Args:
            product_type: Product type
            value_signals: Optional value signals dict

        Returns:
            Perceived value string (e.g., "$500+ worth of tools")
        """
        tier = self._pricing_tiers[product_type]
        multiplier = tier["perceived_multiplier"]

        # Get premium price and multiply
        perceived_amount = tier["premium"] * multiplier

        # Determine suffix based on product type
        suffix_map = {
            "html_tool": "worth of development time",
            "automation": "worth of automation work",
            "gpt_config": "worth of AI consulting",
            "sheets": "worth of spreadsheet templates",
            "pdf": "worth of consulting advice",
            "prompt_pack": "worth of prompt engineering",
        }
        suffix = suffix_map.get(product_type, "worth of value")

        # Add money_impact if provided
        if value_signals and value_signals.get("money_impact", 0) > 0.7:
            return f"${perceived_amount}+ {suffix} (could generate 10x in revenue)"

        return f"${perceived_amount}+ {suffix}"

    def _select_tier(self, product_type: str, signal_strength: float) -> str:
        """
        Select base or premium tier based on signal strength.

        Args:
            product_type: Product type
            signal_strength: Calculated signal strength (0.0-1.0)

        Returns:
            "base" or "premium"
        """
        # Premium if signal strength > 0.6
        if signal_strength > 0.6:
            return "premium"
        return "base"

    def _calculate_signal_strength(self, value_signals: dict) -> float:
        """
        Calculate overall signal strength from value signals.

        Args:
            value_signals: Dict with signal values (0.0-1.0)

        Returns:
            Weighted signal strength (0.0-1.0)
        """
        total_weight = 0.0
        weighted_sum = 0.0

        for signal_name, signal_info in self._value_signals.items():
            weight = signal_info["weight"]
            value = value_signals.get(signal_name, 0.0)

            # Clamp value to 0-1
            value = max(0.0, min(1.0, value))

            weighted_sum += weight * value
            total_weight += weight

        if total_weight == 0:
            return 0.5

        return weighted_sum / total_weight

    def _generate_justification(
        self,
        product_type: str,
        price: int,
        perceived_value: str,
        value_signals: Optional[dict] = None,
    ) -> str:
        """
        Generate price justification text.

        Args:
            product_type: Product type
            price: Selected price
            perceived_value: Perceived value statement
            value_signals: Optional value signals

        Returns:
            Justification string
        """
        tier = self._pricing_tiers[product_type]

        parts = []

        # Start with perceived value
        parts.append(f"This represents {perceived_value}.")

        # Add time-based justification if strong time_saved signal
        if value_signals and value_signals.get("time_saved", 0) > 0.5:
            parts.append(f"At ${price}, it pays for itself in the first use.")

        # Add money-based justification if strong money_impact signal
        if value_signals and value_signals.get("money_impact", 0) > 0.5:
            parts.append(f"The ROI potential makes ${price} a no-brainer.")

        # Add comparison to alternatives
        if tier["premium"] >= 47:
            parts.append(
                f"Similar tools charge ${tier['premium'] * 2}+/month. This is a one-time investment."
            )
        else:
            parts.append(
                f"Compare to paying a freelancer ${tier['premium'] * 5}+ for the same work."
            )

        return " ".join(parts)

    def get_product_types(self) -> list[str]:
        """
        Get list of supported product types.

        Returns:
            List of product type strings
        """
        return list(self._pricing_tiers.keys())


def recommend_price(
    product_type: str,
    value_signals: Optional[dict] = None,
) -> dict:
    """
    Convenience function to recommend pricing.

    Args:
        product_type: One of the product types in PRICING_TIERS
        value_signals: Optional dict with signal values (0.0-1.0)

    Returns:
        Dict with price_cents, price_display, perceived_value, justification

    Raises:
        ValueError: If product_type is not recognized
    """
    recommender = PricingRecommender()
    return recommender.recommend(product_type, value_signals)
