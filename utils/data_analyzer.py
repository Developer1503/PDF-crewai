"""
Data Analyzer - Extract and analyze numerical data from text
Supports automatic detection, statistical analysis, and visualization
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import json


class DataAnalyzer:
    """
    Analyze numerical data from extracted text
    """
    
    def __init__(self):
        self.number_pattern = r'-?\d+\.?\d*'
        self.currency_pattern = r'[\$£€¥₹]\s*\d+\.?\d*'
        self.percentage_pattern = r'\d+\.?\d*\s*%'
        self.date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
    
    def extract_numbers(self, text: str) -> List[float]:
        """
        Extract all numbers from text
        
        Args:
            text: Input text
            
        Returns:
            List of numbers found
        """
        numbers = re.findall(self.number_pattern, text)
        return [float(n) for n in numbers if n]
    
    def extract_currency_values(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract currency values with symbols
        
        Args:
            text: Input text
            
        Returns:
            List of dictionaries with currency and value
        """
        matches = re.findall(self.currency_pattern, text)
        results = []
        
        for match in matches:
            symbol = match[0]
            value = float(re.findall(r'\d+\.?\d*', match)[0])
            results.append({
                'symbol': symbol,
                'value': value,
                'formatted': match.strip()
            })
        
        return results
    
    def extract_percentages(self, text: str) -> List[float]:
        """
        Extract percentage values
        
        Args:
            text: Input text
            
        Returns:
            List of percentage values (as decimals)
        """
        matches = re.findall(self.percentage_pattern, text)
        return [float(re.findall(r'\d+\.?\d*', m)[0]) for m in matches]
    
    def detect_tables(self, text: str) -> List[pd.DataFrame]:
        """
        Detect and extract tabular data from text
        
        Args:
            text: Input text
            
        Returns:
            List of DataFrames representing detected tables
        """
        tables = []
        lines = text.split('\n')
        
        # Look for lines with multiple numbers separated by whitespace or tabs
        potential_table_lines = []
        for line in lines:
            numbers = self.extract_numbers(line)
            if len(numbers) >= 2:  # At least 2 numbers in a row
                potential_table_lines.append(line)
        
        if len(potential_table_lines) >= 2:
            # Try to parse as table
            try:
                # Split by whitespace
                rows = []
                for line in potential_table_lines:
                    # Split by multiple spaces or tabs
                    parts = re.split(r'\s{2,}|\t', line.strip())
                    rows.append(parts)
                
                # Create DataFrame
                if rows:
                    df = pd.DataFrame(rows[1:], columns=rows[0] if len(rows) > 1 else None)
                    tables.append(df)
            except:
                pass
        
        return tables
    
    def calculate_statistics(self, numbers: List[float]) -> Dict[str, float]:
        """
        Calculate statistical measures for a list of numbers
        
        Args:
            numbers: List of numbers
            
        Returns:
            Dictionary with statistical measures
        """
        if not numbers:
            return {}
        
        numbers_array = np.array(numbers)
        
        stats = {
            'count': len(numbers),
            'sum': float(np.sum(numbers_array)),
            'mean': float(np.mean(numbers_array)),
            'median': float(np.median(numbers_array)),
            'std': float(np.std(numbers_array)),
            'min': float(np.min(numbers_array)),
            'max': float(np.max(numbers_array)),
            'range': float(np.max(numbers_array) - np.min(numbers_array)),
            'q1': float(np.percentile(numbers_array, 25)),
            'q3': float(np.percentile(numbers_array, 75)),
        }
        
        # Add IQR
        stats['iqr'] = stats['q3'] - stats['q1']
        
        return stats
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of text for numerical data
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with analysis results
        """
        # Extract different types of data
        numbers = self.extract_numbers(text)
        currencies = self.extract_currency_values(text)
        percentages = self.extract_percentages(text)
        tables = self.detect_tables(text)
        
        # Calculate statistics
        stats = self.calculate_statistics(numbers) if numbers else {}
        
        # Analyze currencies
        currency_stats = {}
        if currencies:
            currency_values = [c['value'] for c in currencies]
            currency_stats = self.calculate_statistics(currency_values)
            currency_stats['total'] = sum(currency_values)
            currency_stats['symbols'] = list(set(c['symbol'] for c in currencies))
        
        # Analyze percentages
        percentage_stats = {}
        if percentages:
            percentage_stats = self.calculate_statistics(percentages)
        
        return {
            'numbers': {
                'values': numbers,
                'count': len(numbers),
                'statistics': stats
            },
            'currencies': {
                'values': currencies,
                'count': len(currencies),
                'statistics': currency_stats
            },
            'percentages': {
                'values': percentages,
                'count': len(percentages),
                'statistics': percentage_stats
            },
            'tables': {
                'count': len(tables),
                'data': tables
            },
            'has_numerical_data': len(numbers) > 0 or len(currencies) > 0 or len(percentages) > 0
        }
    
    def create_summary(self, analysis: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of the analysis
        
        Args:
            analysis: Analysis results from analyze_text()
            
        Returns:
            Summary string
        """
        summary_parts = []
        
        # Numbers summary
        if analysis['numbers']['count'] > 0:
            stats = analysis['numbers']['statistics']
            summary_parts.append(
                f"📊 Found {stats['count']} numbers\n"
                f"   Range: {stats['min']:.2f} to {stats['max']:.2f}\n"
                f"   Mean: {stats['mean']:.2f}, Median: {stats['median']:.2f}"
            )
        
        # Currency summary
        if analysis['currencies']['count'] > 0:
            stats = analysis['currencies']['statistics']
            symbols = ', '.join(stats['symbols'])
            summary_parts.append(
                f"💰 Found {analysis['currencies']['count']} currency values ({symbols})\n"
                f"   Total: {stats['total']:.2f}\n"
                f"   Range: {stats['min']:.2f} to {stats['max']:.2f}"
            )
        
        # Percentage summary
        if analysis['percentages']['count'] > 0:
            stats = analysis['percentages']['statistics']
            summary_parts.append(
                f"📈 Found {analysis['percentages']['count']} percentages\n"
                f"   Range: {stats['min']:.1f}% to {stats['max']:.1f}%\n"
                f"   Average: {stats['mean']:.1f}%"
            )
        
        # Tables summary
        if analysis['tables']['count'] > 0:
            summary_parts.append(
                f"📋 Detected {analysis['tables']['count']} table(s)"
            )
        
        if not summary_parts:
            return "No numerical data detected in the text."
        
        return "\n\n".join(summary_parts)
    
    def export_to_csv(self, analysis: Dict[str, Any], filename: str = "data_export.csv"):
        """
        Export numerical data to CSV
        
        Args:
            analysis: Analysis results
            filename: Output filename
        """
        # Create DataFrame from numbers
        if analysis['numbers']['count'] > 0:
            df = pd.DataFrame({
                'Value': analysis['numbers']['values']
            })
            df.to_csv(filename, index=False)
            return filename
        return None
    
    def export_to_json(self, analysis: Dict[str, Any], filename: str = "data_export.json"):
        """
        Export analysis to JSON
        
        Args:
            analysis: Analysis results
            filename: Output filename
        """
        # Convert DataFrames to dict for JSON serialization
        export_data = {
            'numbers': analysis['numbers'],
            'currencies': analysis['currencies'],
            'percentages': analysis['percentages'],
            'tables': {
                'count': analysis['tables']['count'],
                'data': [df.to_dict() for df in analysis['tables']['data']]
            },
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return filename


# Convenience function
def quick_analyze(text: str) -> Dict[str, Any]:
    """
    Quick analysis of text
    
    Args:
        text: Input text
        
    Returns:
        Analysis results
    """
    analyzer = DataAnalyzer()
    return analyzer.analyze_text(text)


if __name__ == "__main__":
    # Example usage
    sample_text = """
    Sales Report Q1 2024
    
    Total Revenue: $125,000
    Expenses: $45,000
    Profit Margin: 64%
    
    Regional Performance:
    North: $50,000 (40%)
    South: $35,000 (28%)
    East: $25,000 (20%)
    West: $15,000 (12%)
    
    Growth Rate: 15.5%
    Customer Satisfaction: 92%
    """
    
    analyzer = DataAnalyzer()
    results = analyzer.analyze_text(sample_text)
    
    print("="*60)
    print("DATA ANALYSIS RESULTS")
    print("="*60)
    print(analyzer.create_summary(results))
