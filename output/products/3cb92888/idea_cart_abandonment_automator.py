#!/usr/bin/env python3
"""
Idea Cart Abandonment Automator

A comprehensive tool for analyzing and identifying reasons for cart abandonment
in e-commerce stores. This script analyzes multiple factors that could contribute
to high cart abandonment rates and provides actionable insights.

The script examines:
- Page load times and performance metrics
- Checkout process complexity
- Mobile responsiveness
- Payment method availability
- Trust signals and security indicators
- Shipping costs and policies
- User experience friction points

Author: E-commerce Automation Tools
Version: 1.0
"""

import argparse
import json
import sys
import time
import urllib.parse
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import ssl
import socket


@dataclass
class CartAbandonmentAnalysis:
    """Data class to store cart abandonment analysis results."""
    site_url: str
    load_time: float
    ssl_enabled: bool
    mobile_friendly: bool
    checkout_steps: int
    payment_methods: List[str]
    shipping_info_visible: bool
    trust_signals: List[str]
    recommendations: List[str]
    abandonment_score: int


class CartAbandonmentAnalyzer:
    """Analyzes websites for common cart abandonment issues."""
    
    def __init__(self, timeout: int = 10):
        """Initialize the analyzer with request timeout.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    def analyze_site(self, url: str) -> CartAbandonmentAnalysis:
        """Perform comprehensive cart abandonment analysis.
        
        Args:
            url: The website URL to analyze
            
        Returns:
            CartAbandonmentAnalysis object with results
            
        Raises:
            ValueError: If URL is invalid
            URLError: If site cannot be reached
        """
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL format: {url}")
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print(f"Analyzing cart abandonment factors for: {url}")
        
        # Perform various checks
        load_time = self._check_load_time(url)
        ssl_enabled = self._check_ssl(url)
        html_content = self._fetch_page_content(url)
        mobile_friendly = self._check_mobile_friendliness(html_content)
        checkout_steps = self._estimate_checkout_complexity(html_content)
        payment_methods = self._detect_payment_methods(html_content)
        shipping_visible = self._check_shipping_info(html_content)
        trust_signals = self._detect_trust_signals(html_content)
        
        # Generate recommendations and calculate score
        recommendations = self._generate_recommendations(
            load_time, ssl_enabled, mobile_friendly, checkout_steps,
            payment_methods, shipping_visible, trust_signals
        )
        
        abandonment_score = self._calculate_abandonment_risk(
            load_time, ssl_enabled, mobile_friendly, checkout_steps,
            len(payment_methods), shipping_visible, len(trust_signals)
        )
        
        return CartAbandonmentAnalysis(
            site_url=url,
            load_time=load_time,
            ssl_enabled=ssl_enabled,
            mobile_friendly=mobile_friendly,
            checkout_steps=checkout_steps,
            payment_methods=payment_methods,
            shipping_info_visible=shipping_visible,
            trust_signals=trust_signals,
            recommendations=recommendations,
            abandonment_score=abandonment_score
        )
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme or True, result.netloc or '.' in url])
        except Exception:
            return False
    
    def _check_load_time(self, url: str) -> float:
        """Measure page load time."""
        try:
            start_time = time.time()
            request = Request(url, headers={'User-Agent': self.user_agent})
            with urlopen(request, timeout=self.timeout) as response:
                response.read()
            return round(time.time() - start_time, 2)
        except Exception as e:
            print(f"Warning: Could not measure load time: {e}")
            return 0.0
    
    def _check_ssl(self, url: str) -> bool:
        """Check if site uses SSL/HTTPS."""
        return url.startswith('https://')
    
    def _fetch_page_content(self, url: str) -> str:
        """Fetch and return page HTML content."""
        try:
            request = Request(url, headers={'User-Agent': self.user_agent})
            with urlopen(request, timeout=self.timeout) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Warning: Could not fetch page content: {e}")
            return ""
    
    def _check_mobile_friendliness(self, html: str) -> bool:
        """Check for mobile-friendly indicators."""
        mobile_indicators = [
            'viewport',
            'responsive',
            'mobile-friendly',
            'device-width',
            '@media'
        ]
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in mobile_indicators)
    
    def _estimate_checkout_complexity(self, html: str) -> int:
        """Estimate number of checkout steps based on form fields."""
        form_fields = [
            'email', 'password', 'firstname', 'lastname', 'address',
            'city', 'state', 'zip', 'country', 'phone', 'card',
            'cvv', 'expiry'
        ]
        
        html_lower = html.lower()
        field_count = sum(1 for field in form_fields if field in html_lower)
        
        # Estimate steps based on field complexity
        if field_count <= 3:
            return 1
        elif field_count <= 8:
            return 2
        elif field_count <= 12:
            return 3
        else:
            return 4
    
    def _detect_payment_methods(self, html: str) -> List[str]:
        """Detect available payment methods."""
        payment_methods = {
            'visa': 'Visa',
            'mastercard': 'Mastercard',
            'american express': 'American Express',
            'paypal': 'PayPal',
            'apple pay': 'Apple Pay',
            'google pay': 'Google Pay',
            'stripe': 'Stripe',
            'square': 'Square'
        }
        
        html_lower = html.lower()
        detected = [method for keyword, method in payment_methods.items() 
                   if keyword in html_lower]
        
        return detected or ['Credit Card']  # Default assumption
    
    def _check_shipping_info(self, html: str) -> bool:
        """Check if shipping information is clearly visible."""
        shipping_indicators = [
            'free shipping', 'shipping cost', 'delivery',
            'shipping policy', 'shipping info', 'shipping rate'
        ]
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in shipping_indicators)
    
    def _detect_trust_signals(self, html: str) -> List[str]:
        """Detect trust signals on the website."""
        trust_signals = {
            'ssl': 'SSL Certificate',
            'secure': 'Security Badges',
            'guarantee': 'Money Back Guarantee',
            'reviews': 'Customer Reviews',
            'testimonial': 'Customer Testimonials',
            'certified': 'Certifications',
            'award': 'Industry Awards',
            'contact': 'Contact Information'
        }
        
        html_lower = html.lower()
        detected = [signal for keyword, signal in trust_signals.items() 
                   if keyword in html_lower]
        
        return detected
    
    def _generate_recommendations(self, load_time: float, ssl_enabled: bool,
                                mobile_friendly: bool, checkout_steps: int,
                                payment_methods: List[str], shipping_visible: bool,
                                trust_signals: List[str]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        if load_time > 3.0:
            recommendations.append(
                "Optimize page load time (currently {:.1f}s, aim for <3s)".format(load_time)
            )
        
        if not ssl_enabled:
            recommendations.append("Enable SSL/HTTPS for security")
        
        if not mobile_friendly:
            recommendations.append("Implement responsive design for mobile users")
        
        if checkout_steps > 2:
            recommendations.append(
                "Simplify checkout process (currently {} steps, aim for 1-2)".format(checkout_steps)
            )
        
        if len(payment_methods) < 3:
            recommendations.append("Add more payment options (PayPal, Apple Pay, Google Pay)")
        
        if not shipping_visible:
            recommendations.append("Display shipping costs and policies upfront")
        
        if len(trust_signals) < 3:
            recommendations.append("Add trust signals (reviews, guarantees, security badges)")
        
        if not recommendations:
            recommendations.append("Consider A/B testing different checkout flows")
        
        return recommendations
    
    def _calculate_abandonment_risk(self, load_time: float, ssl_enabled: bool,
                                  mobile_friendly: bool, checkout_steps: int,
                                  payment_method_count: int, shipping_visible: bool,
                                  trust_signal_count: int) -> int:
        """Calculate abandonment risk score (0-100, higher = more risk)."""
        score = 0
        
        # Load time impact (0-25 points)
        if load_time > 5:
            score += 25
        elif load_time > 3:
            score += 15
        elif load_time > 2:
            score += 10
        
        # Security impact (0-15 points)
        if not ssl_enabled:
            score += 15
        
        # Mobile impact (0-15 points)
        if not mobile_friendly:
            score += 15
        
        # Checkout complexity (0-20 points)
        if checkout_steps > 3:
            score += 20
        elif checkout_steps > 2:
            score += 10
        
        # Payment options (0-10 points)
        if payment_method_count < 2:
            score += 10
        elif payment_method_count < 3:
            score += 5
        
        # Shipping transparency (0-10 points)
        if not shipping_visible:
            score += 10
        
        # Trust signals (0-5 points)
        if trust_signal_count < 2:
            score += 5
        
        return min(score, 100)


def print_analysis_report(analysis: CartAbandonmentAnalysis) -> None:
    """Print a formatted analysis report.
    
    Args:
        analysis: The analysis results to display
    """
    print("\n" + "="*60)
    print("         CART ABANDONMENT ANALYSIS REPORT")
    print("="*60)
    print(f"Website: {analysis.site_url}")
    print(f"Abandonment Risk Score: {analysis.abandonment_score}/100")
    
    # Risk level interpretation
    if analysis.abandonment_score >= 70:
        risk_level = "HIGH RISK"
    elif analysis.abandonment_score >= 40:
        risk_level = "MEDIUM RISK"
    else:
        risk_level = "LOW RISK"
    
    print(f"Risk Level: {risk_level}")
    
    print("\nTECHNICAL ANALYSIS:")
    print("-" * 30)
    print(f"Page Load Time: {analysis.load_time}s")
    print(f"SSL Enabled: {'Yes' if analysis.ssl_enabled else 'No'}")
    print(f"Mobile Friendly: {'Yes' if analysis.mobile_friendly else 'No'}")
    print(f"Estimated Checkout Steps: {analysis.checkout_steps}")
    print(f"Payment Methods: {', '.join(analysis.payment_methods) if analysis.payment_methods else 'None detected'}")
    print(f"Shipping Info Visible: {'Yes' if analysis.shipping_info_visible else 'No'}")
    print(f"Trust Signals: {', '.join(analysis.trust_signals) if analysis.trust_signals else 'None detected'}")
    
    print("\nRECOMMENDATIONS:")
    print("-" * 30)
    for i, rec in enumerate(analysis.recommendations, 1):
        print(f"{i}. {rec}")
    
    print("\nADDITIONAL FACTORS TO CONSIDER:")
    print("-" * 30)
    print("• Unexpected shipping costs at checkout")
    print("• Required account creation")
    print("• Complex return policy")
    print("• Limited customer support options")
    print("• Lack of product images/descriptions")
    print("• No guest checkout option")
    print("• Poor site search functionality")
    print("="*60)


def export_to_json(analysis: CartAbandonmentAnalysis, filename: str) -> None:
    """Export analysis results to JSON file.
    
    Args:
        analysis: The analysis results to export
        filename: Output filename
    """
    data = {
        'site_url': analysis.site_url,
        'abandonment_risk_score': analysis.abandonment_score,
        'technical_analysis': {
            'load_time_seconds': analysis.load_time,
            'ssl_enabled': analysis.ssl_enabled,
            'mobile_friendly': analysis.mobile_friendly,
            'checkout_steps': analysis.checkout_steps,
            'payment_methods': analysis.payment_methods,
            'shipping_info_visible': analysis.shipping_info_visible,
            'trust_signals': analysis.trust_signals
        },
        'recommendations': analysis.recommendations
    }
    
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nAnalysis exported to: {filename}")
    except Exception as e:
        print(f"Error exporting to JSON: {e}")


def main() -> None:
    """Main function to handle CLI interface and execute analysis."""
    parser = argparse.ArgumentParser(
        description='Analyze e-commerce sites for cart abandonment factors',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python cart_abandonment_analyzer.py https://mystore.com
  python cart_abandonment_analyzer.py mystore.com --export results.json
  python cart_abandonment_analyzer.py https://example.com --timeout 15
        """
    )
    
    parser.add_argument(
        'url',
        help='Website URL to analyze (e.g., https://mystore.com)'
    )
    
    parser.add_argument(
        '--export',
        metavar='FILE',
        help='Export results to JSON file'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Request timeout in seconds (default: 10)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = CartAbandonmentAnalyzer(timeout=args.timeout)
        
        # Perform analysis
        analysis = analyzer.analyze_site(args.url)
        
        # Display results
        print_analysis_report(analysis)
        
        # Export if requested
        if args.export:
            export_to_json(analysis, args.export)
        
        # Exit with appropriate code based on risk level
        sys.exit(0 if analysis.abandonment_score < 70 else 1)
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except (URLError, HTTPError) as e:
        print(f"Error: Unable to access website - {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()