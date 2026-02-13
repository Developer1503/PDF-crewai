"""
Test Data Analysis Feature
Demonstrates automatic numerical data extraction and visualization
"""

from utils.data_analyzer import DataAnalyzer
from utils.data_visualizer import DataVisualizer
import plotly.graph_objects as go


def test_data_analysis():
    """Test data analysis with sample data"""
    
    print("\n" + "="*70)
    print("📊 DATA ANALYSIS TEST")
    print("="*70)
    
    # Sample text with numerical data
    sample_text = """
    QUARTERLY SALES REPORT - Q1 2024
    
    Regional Performance:
    North Region:    $125,000 (35%)
    South Region:    $98,500  (27%)
    East Region:     $87,300  (24%)
    West Region:     $52,200  (14%)
    
    Total Revenue:   $363,000
    
    Key Metrics:
    - Customer Satisfaction: 92%
    - Growth Rate: 15.5%
    - Market Share: 28%
    - Employee Retention: 87%
    
    Top Products:
    Product A: $89,000
    Product B: $76,500
    Product C: $54,200
    Product D: $43,800
    Product E: $32,100
    
    Expenses:
    Salaries:    $125,000
    Marketing:   $45,000
    Operations:  $38,500
    R&D:         $28,000
    
    Net Profit: $126,500
    Profit Margin: 34.8%
    """
    
    print("\n📄 Sample Text:")
    print("-"*70)
    print(sample_text[:200] + "...")
    print("-"*70)
    
    # Initialize analyzer
    print("\n🔍 Initializing Data Analyzer...")
    analyzer = DataAnalyzer()
    
    # Analyze text
    print("📊 Analyzing text...")
    analysis = analyzer.analyze_text(sample_text)
    
    # Display results
    print("\n" + "="*70)
    print("📊 ANALYSIS RESULTS")
    print("="*70)
    
    # Summary
    summary = analyzer.create_summary(analysis)
    print("\n" + summary)
    
    # Detailed statistics
    if analysis['numbers']['count'] > 0:
        print("\n" + "-"*70)
        print("📈 DETAILED STATISTICS")
        print("-"*70)
        
        stats = analysis['numbers']['statistics']
        
        print(f"\n{'Metric':<20} {'Value':>15}")
        print("-"*40)
        print(f"{'Count':<20} {stats['count']:>15}")
        print(f"{'Sum':<20} {stats['sum']:>15,.2f}")
        print(f"{'Mean':<20} {stats['mean']:>15,.2f}")
        print(f"{'Median':<20} {stats['median']:>15,.2f}")
        print(f"{'Std Dev':<20} {stats['std']:>15,.2f}")
        print(f"{'Min':<20} {stats['min']:>15,.2f}")
        print(f"{'Max':<20} {stats['max']:>15,.2f}")
        print(f"{'Range':<20} {stats['range']:>15,.2f}")
        print(f"{'Q1':<20} {stats['q1']:>15,.2f}")
        print(f"{'Q3':<20} {stats['q3']:>15,.2f}")
        print(f"{'IQR':<20} {stats['iqr']:>15,.2f}")
    
    # Currency analysis
    if analysis['currencies']['count'] > 0:
        print("\n" + "-"*70)
        print("💰 CURRENCY ANALYSIS")
        print("-"*70)
        
        print(f"\nFound {analysis['currencies']['count']} currency values:")
        for i, curr in enumerate(analysis['currencies']['values'][:5], 1):
            print(f"  {i}. {curr['formatted']}")
        
        if analysis['currencies']['count'] > 5:
            print(f"  ... and {analysis['currencies']['count'] - 5} more")
        
        curr_stats = analysis['currencies']['statistics']
        print(f"\nTotal: ${curr_stats['total']:,.2f}")
        print(f"Average: ${curr_stats['mean']:,.2f}")
        print(f"Range: ${curr_stats['min']:,.2f} - ${curr_stats['max']:,.2f}")
    
    # Percentage analysis
    if analysis['percentages']['count'] > 0:
        print("\n" + "-"*70)
        print("📈 PERCENTAGE ANALYSIS")
        print("-"*70)
        
        print(f"\nFound {analysis['percentages']['count']} percentages:")
        for i, pct in enumerate(analysis['percentages']['values'], 1):
            print(f"  {i}. {pct}%")
        
        pct_stats = analysis['percentages']['statistics']
        print(f"\nAverage: {pct_stats['mean']:.1f}%")
        print(f"Range: {pct_stats['min']:.1f}% - {pct_stats['max']:.1f}%")
    
    # Visualization
    print("\n" + "="*70)
    print("📊 CREATING VISUALIZATIONS")
    print("="*70)
    
    viz = DataVisualizer()
    
    print("\n✅ Creating dashboard...")
    fig = viz.create_dashboard(analysis)
    
    # Save as HTML
    output_file = "data_analysis_dashboard.html"
    fig.write_html(output_file)
    print(f"✅ Dashboard saved to: {output_file}")
    
    # Export data
    print("\n" + "="*70)
    print("💾 EXPORTING DATA")
    print("="*70)
    
    # Export to CSV
    csv_file = analyzer.export_to_csv(analysis, "analysis_data.csv")
    if csv_file:
        print(f"✅ CSV exported to: {csv_file}")
    
    # Export to JSON
    json_file = analyzer.export_to_json(analysis, "analysis_results.json")
    if json_file:
        print(f"✅ JSON exported to: {json_file}")
    
    print("\n" + "="*70)
    print("✨ TEST COMPLETE")
    print("="*70)
    print("\n📂 Generated Files:")
    print(f"  - {output_file} (Interactive dashboard)")
    print(f"  - {csv_file} (Numerical data)")
    print(f"  - {json_file} (Complete analysis)")
    print("\n💡 Open the HTML file in your browser to view the interactive dashboard!")
    print("="*70 + "\n")


def test_custom_visualizations():
    """Test individual visualization types"""
    
    print("\n" + "="*70)
    print("🎨 CUSTOM VISUALIZATIONS TEST")
    print("="*70)
    
    viz = DataVisualizer()
    
    # Sample data
    import numpy as np
    numbers = np.random.normal(100, 15, 50).tolist()
    
    print("\n📊 Creating individual charts...")
    
    # Histogram
    print("  1. Histogram...")
    fig1 = viz.create_histogram(numbers, "Distribution Test", bins=10)
    fig1.write_html("histogram_test.html")
    
    # Box plot
    print("  2. Box Plot...")
    fig2 = viz.create_box_plot(numbers, "Box Plot Test")
    fig2.write_html("boxplot_test.html")
    
    # Bar chart
    print("  3. Bar Chart...")
    labels = ['Product A', 'Product B', 'Product C', 'Product D']
    values = [125, 98, 87, 52]
    fig3 = viz.create_bar_chart(labels, values, "Sales Comparison")
    fig3.write_html("barchart_test.html")
    
    # Pie chart
    print("  4. Pie Chart...")
    fig4 = viz.create_pie_chart(labels, values, "Market Share")
    fig4.write_html("piechart_test.html")
    
    print("\n✅ All charts created successfully!")
    print("\n📂 Generated Files:")
    print("  - histogram_test.html")
    print("  - boxplot_test.html")
    print("  - barchart_test.html")
    print("  - piechart_test.html")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Run tests
    test_data_analysis()
    
    print("\n" + "="*70)
    print("🎯 NEXT STEPS")
    print("="*70)
    print("\n1. View the interactive dashboard:")
    print("   Open 'data_analysis_dashboard.html' in your browser")
    print("\n2. Run the full demo:")
    print("   streamlit run ocr_data_analysis_demo.py")
    print("\n3. Test with your own data:")
    print("   Upload an image with numerical data")
    print("\n4. Integrate into app_v2.py:")
    print("   See DATA_ANALYSIS_README.md for instructions")
    print("\n" + "="*70 + "\n")
    
    # Optional: Run custom visualizations test
    response = input("Run custom visualizations test? (y/n): ")
    if response.lower() == 'y':
        test_custom_visualizations()
