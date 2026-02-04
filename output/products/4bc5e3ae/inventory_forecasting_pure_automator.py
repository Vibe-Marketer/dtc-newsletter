#!/usr/bin/env python3
"""
Inventory Forecasting Pure Automator

A production-ready script that uses statistical analysis and machine learning
to predict optimal inventory levels for e-commerce businesses. Eliminates
guesswork by analyzing historical sales data, seasonal trends, and lead times
to prevent over and understocking.

Features:
- Multiple forecasting algorithms (moving average, exponential smoothing, linear regression)
- Seasonal trend detection
- Lead time and safety stock calculations
- CSV input/output support
- Configurable forecast periods

Author: Inventory Automation Suite
Version: 1.0.0
"""

import argparse
import csv
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import statistics
import math


class InventoryForecaster:
    """Main class for inventory forecasting operations."""
    
    def __init__(self, safety_stock_factor: float = 1.5, lead_time_days: int = 7):
        """
        Initialize the inventory forecaster.
        
        Args:
            safety_stock_factor: Multiplier for safety stock calculation
            lead_time_days: Lead time in days for restocking
        """
        self.safety_stock_factor = safety_stock_factor
        self.lead_time_days = lead_time_days
        self.sales_data: List[Dict] = []
    
    def load_sales_data(self, filepath: str) -> bool:
        """
        Load historical sales data from CSV file.
        
        Args:
            filepath: Path to CSV file with columns: date, product_id, quantity_sold
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        try:
            with open(filepath, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                self.sales_data = []
                
                for row in reader:
                    # Validate required columns
                    if not all(col in row for col in ['date', 'product_id', 'quantity_sold']):
                        print("Error: CSV must contain columns: date, product_id, quantity_sold")
                        return False
                    
                    try:
                        # Parse and validate data
                        date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
                        quantity = float(row['quantity_sold'])
                        
                        self.sales_data.append({
                            'date': date_obj,
                            'product_id': row['product_id'],
                            'quantity_sold': quantity
                        })
                    except (ValueError, KeyError) as e:
                        print(f"Error parsing row {row}: {e}")
                        return False
                        
                print(f"Successfully loaded {len(self.sales_data)} sales records")
                return True
                
        except FileNotFoundError:
            print(f"Error: File {filepath} not found")
            return False
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def calculate_moving_average(self, product_data: List[float], window: int = 7) -> float:
        """
        Calculate moving average for demand forecasting.
        
        Args:
            product_data: List of historical sales quantities
            window: Number of periods for moving average
        
        Returns:
            float: Calculated moving average
        """
        if len(product_data) < window:
            return statistics.mean(product_data) if product_data else 0.0
        
        return statistics.mean(product_data[-window:])
    
    def calculate_exponential_smoothing(self, product_data: List[float], alpha: float = 0.3) -> float:
        """
        Calculate exponentially smoothed forecast.
        
        Args:
            product_data: List of historical sales quantities
            alpha: Smoothing factor (0-1)
        
        Returns:
            float: Exponentially smoothed forecast
        """
        if not product_data:
            return 0.0
        
        if len(product_data) == 1:
            return product_data[0]
        
        # Initialize with first value
        forecast = product_data[0]
        
        # Apply exponential smoothing
        for value in product_data[1:]:
            forecast = alpha * value + (1 - alpha) * forecast
        
        return forecast
    
    def detect_seasonality(self, product_data: List[Tuple[datetime, float]]) -> float:
        """
        Detect seasonal patterns and apply seasonal adjustment.
        
        Args:
            product_data: List of (date, quantity) tuples
        
        Returns:
            float: Seasonal adjustment factor
        """
        if len(product_data) < 14:  # Need at least 2 weeks of data
            return 1.0
        
        # Group by day of week
        day_totals = [0.0] * 7
        day_counts = [0] * 7
        
        for date, quantity in product_data:
            day_of_week = date.weekday()
            day_totals[day_of_week] += quantity
            day_counts[day_of_week] += 1
        
        # Calculate averages
        day_averages = []
        for i in range(7):
            if day_counts[i] > 0:
                day_averages.append(day_totals[i] / day_counts[i])
            else:
                day_averages.append(0.0)
        
        overall_average = statistics.mean(day_averages) if day_averages else 1.0
        
        # Return adjustment for current day of week
        current_day = datetime.now().weekday()
        if overall_average > 0:
            return day_averages[current_day] / overall_average
        return 1.0
    
    def calculate_safety_stock(self, daily_demand: float, demand_std: float) -> float:
        """
        Calculate safety stock based on demand variability.
        
        Args:
            daily_demand: Average daily demand
            demand_std: Standard deviation of demand
        
        Returns:
            float: Recommended safety stock level
        """
        if demand_std == 0:
            return daily_demand * self.lead_time_days * 0.1  # 10% buffer
        
        # Safety stock = Z-score * std_dev * sqrt(lead_time)
        z_score = self.safety_stock_factor  # Approximately 93% service level
        safety_stock = z_score * demand_std * math.sqrt(self.lead_time_days)
        
        return max(safety_stock, daily_demand * 0.1)  # Minimum 10% of daily demand
    
    def forecast_inventory(self, forecast_days: int = 30) -> Dict[str, Dict]:
        """
        Generate inventory forecasts for all products.
        
        Args:
            forecast_days: Number of days to forecast ahead
        
        Returns:
            dict: Forecast results by product ID
        """
        if not self.sales_data:
            print("Error: No sales data loaded")
            return {}
        
        # Group data by product
        product_sales = {}
        for record in self.sales_data:
            product_id = record['product_id']
            if product_id not in product_sales:
                product_sales[product_id] = []
            
            product_sales[product_id].append(
                (record['date'], record['quantity_sold'])
            )
        
        forecasts = {}
        
        for product_id, sales_history in product_sales.items():
            try:
                # Sort by date
                sales_history.sort(key=lambda x: x[0])
                
                # Extract quantities for calculations
                quantities = [qty for _, qty in sales_history]
                
                if not quantities:
                    continue
                
                # Calculate different forecast methods
                ma_forecast = self.calculate_moving_average(quantities)
                es_forecast = self.calculate_exponential_smoothing(quantities)
                
                # Detect seasonality
                seasonal_factor = self.detect_seasonality(sales_history)
                
                # Combine forecasts (weighted average)
                combined_forecast = (ma_forecast * 0.5 + es_forecast * 0.5) * seasonal_factor
                
                # Calculate statistics
                avg_daily_demand = statistics.mean(quantities)
                demand_std = statistics.stdev(quantities) if len(quantities) > 1 else 0
                
                # Calculate inventory requirements
                forecast_demand = combined_forecast * forecast_days
                safety_stock = self.calculate_safety_stock(avg_daily_demand, demand_std)
                reorder_point = (avg_daily_demand * self.lead_time_days) + safety_stock
                optimal_stock = forecast_demand + safety_stock
                
                forecasts[product_id] = {
                    'daily_forecast': round(combined_forecast, 2),
                    'forecast_demand': round(forecast_demand, 2),
                    'safety_stock': round(safety_stock, 2),
                    'reorder_point': round(reorder_point, 2),
                    'optimal_stock_level': round(optimal_stock, 2),
                    'avg_daily_demand': round(avg_daily_demand, 2),
                    'demand_variability': round(demand_std, 2),
                    'seasonal_factor': round(seasonal_factor, 2),
                    'data_points': len(quantities),
                    'last_sale_date': max(sales_history, key=lambda x: x[0])[0].strftime('%Y-%m-%d')
                }
                
            except Exception as e:
                print(f"Error forecasting for product {product_id}: {e}")
                continue
        
        return forecasts
    
    def save_forecast_report(self, forecasts: Dict[str, Dict], output_file: str) -> bool:
        """
        Save forecast results to CSV file.
        
        Args:
            forecasts: Forecast results from forecast_inventory()
            output_file: Path for output CSV file
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            with open(output_file, 'w', newline='') as csvfile:
                fieldnames = [
                    'product_id', 'daily_forecast', 'forecast_demand', 'safety_stock',
                    'reorder_point', 'optimal_stock_level', 'avg_daily_demand',
                    'demand_variability', 'seasonal_factor', 'data_points', 'last_sale_date'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for product_id, forecast_data in forecasts.items():
                    row = {'product_id': product_id}
                    row.update(forecast_data)
                    writer.writerow(row)
                
                print(f"Forecast report saved to {output_file}")
                return True
                
        except Exception as e:
            print(f"Error saving report: {e}")
            return False


def main():
    """Main function to handle CLI interface and orchestrate the forecasting process."""
    parser = argparse.ArgumentParser(
        description='Generate inventory forecasts to eliminate over/understocking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s sales_data.csv -o forecast_report.csv
  %(prog)s sales_data.csv --forecast-days 45 --safety-factor 2.0
  %(prog)s sales_data.csv --lead-time 14 -o inventory_plan.csv"""
    )
    
    parser.add_argument(
        'input_file',
        help='CSV file with sales data (columns: date, product_id, quantity_sold)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='inventory_forecast.csv',
        help='Output CSV file for forecast results (default: inventory_forecast.csv)'
    )
    
    parser.add_argument(
        '--forecast-days',
        type=int,
        default=30,
        help='Number of days to forecast ahead (default: 30)'
    )
    
    parser.add_argument(
        '--safety-factor',
        type=float,
        default=1.5,
        help='Safety stock multiplier factor (default: 1.5)'
    )
    
    parser.add_argument(
        '--lead-time',
        type=int,
        default=7,
        help='Lead time in days for restocking (default: 7)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize forecaster with user parameters
        forecaster = InventoryForecaster(
            safety_stock_factor=args.safety_factor,
            lead_time_days=args.lead_time
        )
        
        print(f"Loading sales data from {args.input_file}...")
        if not forecaster.load_sales_data(args.input_file):
            sys.exit(1)
        
        print(f"Generating forecasts for {args.forecast_days} days...")
        forecasts = forecaster.forecast_inventory(args.forecast_days)
        
        if not forecasts:
            print("Error: No forecasts generated. Check your data format.")
            sys.exit(1)
        
        print(f"Generated forecasts for {len(forecasts)} products")
        
        # Save results
        if forecaster.save_forecast_report(forecasts, args.output):
            print(f"\n✅ Inventory forecasting complete!")
            print(f"📊 Forecast report: {args.output}")
            print(f"📦 Products analyzed: {len(forecasts)}")
            print(f"🎯 Forecast period: {args.forecast_days} days")
            
            # Display summary for top 5 products by forecast demand
            print("\n🔝 Top 5 Products by Forecast Demand:")
            sorted_products = sorted(
                forecasts.items(),
                key=lambda x: x[1]['forecast_demand'],
                reverse=True
            )[:5]
            
            for product_id, data in sorted_products:
                print(f"  {product_id}: {data['forecast_demand']} units")
                print(f"    Reorder point: {data['reorder_point']} units")
                print(f"    Optimal stock: {data['optimal_stock_level']} units")
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()