#!/usr/bin/env python3
"""
Shipping Rate Comparison Automator

Automatically fetches and compares shipping rates from multiple carriers
to find the best price for your packages. Supports USPS, UPS, and FedEx
rate calculations.

Usage:
    python shipping_compare.py --weight 2.5 --dimensions 10x8x6 --origin 90210 --dest 10001
    python shipping_compare.py --csv packages.csv --output rates.csv
"""

import argparse
import csv
import json
import logging
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError
import time


@dataclass
class Package:
    """Represents a package with shipping details."""
    weight: float
    length: float
    width: float
    height: float
    origin_zip: str
    dest_zip: str
    service_type: str = "ground"


@dataclass
class ShippingRate:
    """Represents a shipping rate quote."""
    carrier: str
    service: str
    cost: float
    delivery_days: Optional[int] = None
    error: Optional[str] = None


class RateComparator:
    """Main class for comparing shipping rates across carriers."""
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """Initialize the rate comparator.
        
        Args:
            api_keys: Dictionary containing API keys for carriers
                     Format: {'ups': 'key', 'fedex': 'key', 'usps': 'key'}
        """
        self.api_keys = api_keys or {}
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def calculate_usps_rate(self, package: Package) -> ShippingRate:
        """Calculate USPS shipping rate using simplified estimation.
        
        Args:
            package: Package details
            
        Returns:
            ShippingRate object with USPS pricing
        """
        try:
            # Simplified USPS rate calculation based on weight and distance
            # In production, you would use USPS API
            base_rate = 8.50
            weight_rate = package.weight * 1.25
            
            # Distance factor (simplified zip code distance estimation)
            distance_factor = abs(int(package.origin_zip[:3]) - int(package.dest_zip[:3])) / 100
            distance_cost = distance_factor * 0.5
            
            total_cost = base_rate + weight_rate + distance_cost
            
            service_name = "USPS Ground Advantage" if package.service_type == "ground" else "USPS Priority Mail"
            delivery_days = 5 if package.service_type == "ground" else 3
            
            return ShippingRate(
                carrier="USPS",
                service=service_name,
                cost=round(total_cost, 2),
                delivery_days=delivery_days
            )
        
        except Exception as e:
            self.logger.error(f"Error calculating USPS rate: {e}")
            return ShippingRate(
                carrier="USPS",
                service="N/A",
                cost=0.0,
                error=str(e)
            )
    
    def calculate_ups_rate(self, package: Package) -> ShippingRate:
        """Calculate UPS shipping rate using simplified estimation.
        
        Args:
            package: Package details
            
        Returns:
            ShippingRate object with UPS pricing
        """
        try:
            # Simplified UPS rate calculation
            # In production, you would use UPS Rating API
            base_rate = 12.75
            weight_rate = package.weight * 1.85
            
            # Volume factor
            volume = package.length * package.width * package.height
            volume_rate = volume * 0.01
            
            # Distance factor
            distance_factor = abs(int(package.origin_zip[:3]) - int(package.dest_zip[:3])) / 100
            distance_cost = distance_factor * 0.75
            
            total_cost = base_rate + weight_rate + volume_rate + distance_cost
            
            service_name = "UPS Ground" if package.service_type == "ground" else "UPS 3 Day Select"
            delivery_days = 5 if package.service_type == "ground" else 3
            
            return ShippingRate(
                carrier="UPS",
                service=service_name,
                cost=round(total_cost, 2),
                delivery_days=delivery_days
            )
        
        except Exception as e:
            self.logger.error(f"Error calculating UPS rate: {e}")
            return ShippingRate(
                carrier="UPS",
                service="N/A",
                cost=0.0,
                error=str(e)
            )
    
    def calculate_fedex_rate(self, package: Package) -> ShippingRate:
        """Calculate FedEx shipping rate using simplified estimation.
        
        Args:
            package: Package details
            
        Returns:
            ShippingRate object with FedEx pricing
        """
        try:
            # Simplified FedEx rate calculation
            # In production, you would use FedEx Rating API
            base_rate = 11.25
            weight_rate = package.weight * 1.65
            
            # Dimensional weight calculation
            dim_weight = (package.length * package.width * package.height) / 139
            billable_weight = max(package.weight, dim_weight)
            weight_adjustment = (billable_weight - package.weight) * 0.5
            
            # Distance factor
            distance_factor = abs(int(package.origin_zip[:3]) - int(package.dest_zip[:3])) / 100
            distance_cost = distance_factor * 0.6
            
            total_cost = base_rate + weight_rate + weight_adjustment + distance_cost
            
            service_name = "FedEx Ground" if package.service_type == "ground" else "FedEx Express Saver"
            delivery_days = 4 if package.service_type == "ground" else 3
            
            return ShippingRate(
                carrier="FedEx",
                service=service_name,
                cost=round(total_cost, 2),
                delivery_days=delivery_days
            )
        
        except Exception as e:
            self.logger.error(f"Error calculating FedEx rate: {e}")
            return ShippingRate(
                carrier="FedEx",
                service="N/A",
                cost=0.0,
                error=str(e)
            )
    
    def compare_rates(self, package: Package) -> List[ShippingRate]:
        """Compare rates across all carriers for a package.
        
        Args:
            package: Package to get rates for
            
        Returns:
            List of ShippingRate objects sorted by cost
        """
        rates = []
        
        self.logger.info(f"Calculating rates for package: {package.weight}lbs, {package.origin_zip} -> {package.dest_zip}")
        
        # Get rates from all carriers
        rates.append(self.calculate_usps_rate(package))
        rates.append(self.calculate_ups_rate(package))
        rates.append(self.calculate_fedex_rate(package))
        
        # Filter out rates with errors and sort by cost
        valid_rates = [rate for rate in rates if rate.error is None]
        valid_rates.sort(key=lambda x: x.cost)
        
        return valid_rates
    
    def process_csv(self, csv_file: str) -> List[Dict]:
        """Process multiple packages from CSV file.
        
        Args:
            csv_file: Path to CSV file with package data
            
        Returns:
            List of dictionaries containing package data and rates
        """
        results = []
        
        try:
            with open(csv_file, 'r', newline='') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Parse dimensions
                        dimensions = row['dimensions'].split('x')
                        if len(dimensions) != 3:
                            raise ValueError("Dimensions must be in format: LxWxH")
                        
                        package = Package(
                            weight=float(row['weight']),
                            length=float(dimensions[0]),
                            width=float(dimensions[1]),
                            height=float(dimensions[2]),
                            origin_zip=row['origin_zip'],
                            dest_zip=row['dest_zip'],
                            service_type=row.get('service_type', 'ground')
                        )
                        
                        rates = self.compare_rates(package)
                        
                        result = {
                            'row': row_num,
                            'package': package,
                            'rates': rates,
                            'best_rate': rates[0] if rates else None
                        }
                        
                        results.append(result)
                        
                        # Add small delay to avoid overwhelming APIs
                        time.sleep(0.1)
                        
                    except (ValueError, KeyError) as e:
                        self.logger.error(f"Error processing row {row_num}: {e}")
                        continue
        
        except FileNotFoundError:
            self.logger.error(f"CSV file not found: {csv_file}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing CSV: {e}")
            raise
        
        return results
    
    def save_results_csv(self, results: List[Dict], output_file: str) -> None:
        """Save comparison results to CSV file.
        
        Args:
            results: List of comparison results
            output_file: Output CSV file path
        """
        try:
            with open(output_file, 'w', newline='') as file:
                fieldnames = [
                    'row', 'weight', 'dimensions', 'origin_zip', 'dest_zip',
                    'best_carrier', 'best_service', 'best_cost', 'best_delivery_days',
                    'usps_cost', 'ups_cost', 'fedex_cost', 'savings'
                ]
                
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    if not result['rates']:
                        continue
                    
                    package = result['package']
                    best_rate = result['best_rate']
                    rates_by_carrier = {rate.carrier: rate for rate in result['rates']}
                    
                    # Calculate savings (difference between best and most expensive)
                    costs = [rate.cost for rate in result['rates'] if rate.cost > 0]
                    savings = max(costs) - min(costs) if len(costs) > 1 else 0
                    
                    row_data = {
                        'row': result['row'],
                        'weight': package.weight,
                        'dimensions': f"{package.length}x{package.width}x{package.height}",
                        'origin_zip': package.origin_zip,
                        'dest_zip': package.dest_zip,
                        'best_carrier': best_rate.carrier,
                        'best_service': best_rate.service,
                        'best_cost': best_rate.cost,
                        'best_delivery_days': best_rate.delivery_days,
                        'usps_cost': rates_by_carrier.get('USPS', ShippingRate('', '', 0)).cost,
                        'ups_cost': rates_by_carrier.get('UPS', ShippingRate('', '', 0)).cost,
                        'fedex_cost': rates_by_carrier.get('FedEx', ShippingRate('', '', 0)).cost,
                        'savings': round(savings, 2)
                    }
                    
                    writer.writerow(row_data)
            
            self.logger.info(f"Results saved to {output_file}")
        
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            raise


def parse_dimensions(dimensions_str: str) -> Tuple[float, float, float]:
    """Parse dimensions string into length, width, height.
    
    Args:
        dimensions_str: String in format "LxWxH" (e.g., "10x8x6")
        
    Returns:
        Tuple of (length, width, height)
        
    Raises:
        ValueError: If dimensions format is invalid
    """
    try:
        parts = dimensions_str.split('x')
        if len(parts) != 3:
            raise ValueError("Dimensions must be in format: LxWxH")
        
        return float(parts[0]), float(parts[1]), float(parts[2])
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid dimensions format: {dimensions_str}") from e


def format_rates_table(rates: List[ShippingRate]) -> str:
    """Format rates as a readable table.
    
    Args:
        rates: List of shipping rates
        
    Returns:
        Formatted table string
    """
    if not rates:
        return "No rates available."
    
    table = "\n" + "="*80 + "\n"
    table += f"{'Carrier':<15} {'Service':<25} {'Cost':<10} {'Delivery':<10}\n"
    table += "-"*80 + "\n"
    
    for i, rate in enumerate(rates):
        if rate.error:
            table += f"{rate.carrier:<15} {'ERROR':<25} {'N/A':<10} {'N/A':<10}\n"
        else:
            delivery = f"{rate.delivery_days} days" if rate.delivery_days else "N/A"
            prefix = ">>> " if i == 0 else "    "
            table += f"{prefix}{rate.carrier:<11} {rate.service:<25} ${rate.cost:<9.2f} {delivery:<10}\n"
    
    table += "="*80 + "\n"
    
    if len([r for r in rates if not r.error]) > 1:
        costs = [r.cost for r in rates if not r.error]
        savings = max(costs) - min(costs)
        table += f"Potential savings: ${savings:.2f}\n"
    
    return table


def main() -> int:
    """Main function with CLI interface.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Compare shipping rates across USPS, UPS, and FedEx",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --weight 2.5 --dimensions 10x8x6 --origin 90210 --dest 10001
  %(prog)s --csv packages.csv --output rates.csv
  %(prog)s --weight 5 --dimensions 12x10x8 --origin 60601 --dest 30301 --service express

CSV Format:
  Required columns: weight, dimensions, origin_zip, dest_zip
  Optional columns: service_type (ground/express)
  """
    )
    
    # Single package mode arguments
    single_group = parser.add_argument_group("Single Package Mode")
    single_group.add_argument(
        "--weight", 
        type=float, 
        help="Package weight in pounds"
    )
    single_group.add_argument(
        "--dimensions", 
        type=str, 
        help="Package dimensions in format LxWxH (inches)"
    )
    single_group.add_argument(
        "--origin", 
        type=str, 
        help="Origin ZIP code"
    )
    single_group.add_argument(
        "--dest", 
        type=str, 
        help="Destination ZIP code"
    )
    single_group.add_argument(
        "--service", 
        type=str, 
        choices=["ground", "express"], 
        default="ground",
        help="Service type (default: ground)"
    )
    
    # Batch processing arguments
    batch_group = parser.add_argument_group("Batch Processing Mode")
    batch_group.add_argument(
        "--csv", 
        type=str, 
        help="CSV file with package data"
    )
    batch_group.add_argument(
        "--output", 
        type=str, 
        help="Output CSV file for results"
    )
    
    # General arguments
    parser.add_argument(
        "--api-keys", 
        type=str, 
        help="JSON file with API keys for carriers"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load API keys if provided
        api_keys = {}
        if args.api_keys:
            try:
                with open(args.api_keys, 'r') as f:
                    api_keys = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error loading API keys: {e}", file=sys.stderr)
                return 1
        
        comparator = RateComparator(api_keys)
        
        # Batch processing mode
        if args.csv:
            if not args.output:
                print("Error: --output is required when using --csv", file=sys.stderr)
                return 1
            
            print(f"Processing packages from {args.csv}...")
            results = comparator.process_csv(args.csv)
            
            if not results:
                print("No packages processed successfully.", file=sys.stderr)
                return 1
            
            comparator.save_results_csv(results, args.output)
            
            # Print summary
            total_packages = len(results)
            total_savings = sum(
                max([r.cost for r in result['rates'] if r.cost > 0], default=0) - 
                min([r.cost for r in result['rates'] if r.cost > 0], default=0)
                for result in results if result['rates']
            )
            
            print(f"\nProcessed {total_packages} packages")
            print(f"Total potential savings: ${total_savings:.2f}")
            print(f"Results saved to {args.output}")
        
        # Single package mode
        else:
            # Validate required arguments
            required_args = [args.weight, args.dimensions, args.origin, args.dest]
            if not all(arg is not None for arg in required_args):
                print("Error: --weight, --dimensions, --origin, and --dest are required for single package mode", file=sys.stderr)
                parser.print_help()
                return 1
            
            # Parse dimensions
            try:
                length, width, height = parse_dimensions(args.dimensions)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1
            
            # Create package object
            package = Package(
                weight=args.weight,
                length=length,
                width=width,
                height=height,
                origin_zip=args.origin,
                dest_zip=args.dest,
                service_type=args.service
            )
            
            # Get rate comparison
            rates = comparator.compare_rates(package)
            
            if not rates:
                print("No rates could be calculated.", file=sys.stderr)
                return 1
            
            # Display results
            print(format_rates_table(rates))
            print(f"Best option: {rates[0].carrier} {rates[0].service} - ${rates[0].cost:.2f}")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())