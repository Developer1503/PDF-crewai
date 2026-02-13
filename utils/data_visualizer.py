"""
Data Visualizer - Create beautiful visualizations from numerical data
Supports multiple chart types with Plotly for interactive visualizations
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional


class DataVisualizer:
    """
    Create interactive visualizations from numerical data
    """
    
    def __init__(self, theme: str = 'plotly_white'):
        """
        Initialize visualizer
        
        Args:
            theme: Plotly theme ('plotly', 'plotly_white', 'plotly_dark', 'ggplot2', 'seaborn')
        """
        self.theme = theme
        self.color_palette = px.colors.qualitative.Set3
    
    def create_histogram(
        self, 
        numbers: List[float], 
        title: str = "Distribution of Numbers",
        bins: int = 20
    ) -> go.Figure:
        """
        Create histogram of numbers
        
        Args:
            numbers: List of numbers
            title: Chart title
            bins: Number of bins
            
        Returns:
            Plotly figure
        """
        fig = go.Figure(data=[
            go.Histogram(
                x=numbers,
                nbinsx=bins,
                marker_color='rgb(99, 110, 250)',
                opacity=0.75
            )
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title="Value",
            yaxis_title="Frequency",
            template=self.theme,
            hovermode='x unified'
        )
        
        return fig
    
    def create_box_plot(
        self,
        numbers: List[float],
        title: str = "Box Plot Analysis"
    ) -> go.Figure:
        """
        Create box plot for statistical analysis
        
        Args:
            numbers: List of numbers
            title: Chart title
            
        Returns:
            Plotly figure
        """
        fig = go.Figure(data=[
            go.Box(
                y=numbers,
                name="Data",
                marker_color='rgb(99, 110, 250)',
                boxmean='sd'  # Show mean and standard deviation
            )
        ])
        
        fig.update_layout(
            title=title,
            yaxis_title="Value",
            template=self.theme,
            showlegend=False
        )
        
        return fig
    
    def create_statistics_card(
        self,
        statistics: Dict[str, float],
        title: str = "Statistical Summary"
    ) -> go.Figure:
        """
        Create visual statistics card
        
        Args:
            statistics: Dictionary of statistics
            title: Chart title
            
        Returns:
            Plotly figure
        """
        # Create table
        stats_to_show = ['count', 'mean', 'median', 'std', 'min', 'max', 'range']
        
        labels = []
        values = []
        
        for stat in stats_to_show:
            if stat in statistics:
                labels.append(stat.upper())
                values.append(f"{statistics[stat]:.2f}")
        
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['<b>Metric</b>', '<b>Value</b>'],
                fill_color='rgb(99, 110, 250)',
                font=dict(color='white', size=14),
                align='left'
            ),
            cells=dict(
                values=[labels, values],
                fill_color='lavender',
                align='left',
                font=dict(size=12)
            )
        )])
        
        fig.update_layout(
            title=title,
            template=self.theme,
            height=400
        )
        
        return fig
    
    def create_pie_chart(
        self,
        labels: List[str],
        values: List[float],
        title: str = "Distribution"
    ) -> go.Figure:
        """
        Create pie chart
        
        Args:
            labels: Category labels
            values: Values for each category
            title: Chart title
            
        Returns:
            Plotly figure
        """
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,  # Donut chart
                marker=dict(colors=self.color_palette)
            )
        ])
        
        fig.update_layout(
            title=title,
            template=self.theme
        )
        
        return fig
    
    def create_bar_chart(
        self,
        labels: List[str],
        values: List[float],
        title: str = "Comparison",
        horizontal: bool = False
    ) -> go.Figure:
        """
        Create bar chart
        
        Args:
            labels: Category labels
            values: Values for each category
            title: Chart title
            horizontal: If True, create horizontal bar chart
            
        Returns:
            Plotly figure
        """
        if horizontal:
            fig = go.Figure(data=[
                go.Bar(
                    y=labels,
                    x=values,
                    orientation='h',
                    marker_color='rgb(99, 110, 250)'
                )
            ])
            fig.update_layout(
                xaxis_title="Value",
                yaxis_title="Category"
            )
        else:
            fig = go.Figure(data=[
                go.Bar(
                    x=labels,
                    y=values,
                    marker_color='rgb(99, 110, 250)'
                )
            ])
            fig.update_layout(
                xaxis_title="Category",
                yaxis_title="Value"
            )
        
        fig.update_layout(
            title=title,
            template=self.theme
        )
        
        return fig
    
    def create_line_chart(
        self,
        x_values: List[Any],
        y_values: List[float],
        title: str = "Trend Analysis",
        x_label: str = "X",
        y_label: str = "Y"
    ) -> go.Figure:
        """
        Create line chart
        
        Args:
            x_values: X-axis values
            y_values: Y-axis values
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            
        Returns:
            Plotly figure
        """
        fig = go.Figure(data=[
            go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                line=dict(color='rgb(99, 110, 250)', width=3),
                marker=dict(size=8)
            )
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            template=self.theme,
            hovermode='x unified'
        )
        
        return fig
    
    def create_dashboard(
        self,
        analysis: Dict[str, Any]
    ) -> go.Figure:
        """
        Create comprehensive dashboard from analysis results
        
        Args:
            analysis: Analysis results from DataAnalyzer
            
        Returns:
            Plotly figure with subplots
        """
        # Determine number of subplots needed
        subplots_needed = []
        
        if analysis['numbers']['count'] > 0:
            subplots_needed.append('histogram')
            subplots_needed.append('box')
        
        if analysis['currencies']['count'] > 0:
            subplots_needed.append('currency_bar')
        
        if analysis['percentages']['count'] > 0:
            subplots_needed.append('percentage_bar')
        
        if not subplots_needed:
            # No data to visualize
            fig = go.Figure()
            fig.add_annotation(
                text="No numerical data to visualize",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # Create subplots
        rows = (len(subplots_needed) + 1) // 2
        cols = 2 if len(subplots_needed) > 1 else 1
        
        subplot_titles = []
        for subplot in subplots_needed:
            if subplot == 'histogram':
                subplot_titles.append('Distribution')
            elif subplot == 'box':
                subplot_titles.append('Box Plot')
            elif subplot == 'currency_bar':
                subplot_titles.append('Currency Values')
            elif subplot == 'percentage_bar':
                subplot_titles.append('Percentages')
        
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles
        )
        
        # Add traces
        current_row = 1
        current_col = 1
        
        for subplot in subplots_needed:
            if subplot == 'histogram':
                numbers = analysis['numbers']['values']
                fig.add_trace(
                    go.Histogram(
                        x=numbers,
                        marker_color='rgb(99, 110, 250)',
                        name='Distribution'
                    ),
                    row=current_row,
                    col=current_col
                )
            
            elif subplot == 'box':
                numbers = analysis['numbers']['values']
                fig.add_trace(
                    go.Box(
                        y=numbers,
                        marker_color='rgb(99, 110, 250)',
                        name='Box Plot',
                        boxmean='sd'
                    ),
                    row=current_row,
                    col=current_col
                )
            
            elif subplot == 'currency_bar':
                currencies = analysis['currencies']['values']
                labels = [f"{c['symbol']}{c['value']}" for c in currencies[:10]]  # Top 10
                values = [c['value'] for c in currencies[:10]]
                
                fig.add_trace(
                    go.Bar(
                        x=labels,
                        y=values,
                        marker_color='rgb(34, 197, 94)',
                        name='Currencies'
                    ),
                    row=current_row,
                    col=current_col
                )
            
            elif subplot == 'percentage_bar':
                percentages = analysis['percentages']['values'][:10]  # Top 10
                labels = [f"Value {i+1}" for i in range(len(percentages))]
                
                fig.add_trace(
                    go.Bar(
                        x=labels,
                        y=percentages,
                        marker_color='rgb(234, 88, 12)',
                        name='Percentages'
                    ),
                    row=current_row,
                    col=current_col
                )
            
            # Update position
            current_col += 1
            if current_col > cols:
                current_col = 1
                current_row += 1
        
        fig.update_layout(
            height=400 * rows,
            showlegend=False,
            template=self.theme,
            title_text="Data Analysis Dashboard"
        )
        
        return fig
    
    def create_comparison_chart(
        self,
        data: Dict[str, List[float]],
        title: str = "Comparison"
    ) -> go.Figure:
        """
        Create grouped bar chart for comparing multiple datasets
        
        Args:
            data: Dictionary with labels as keys and lists of values
            title: Chart title
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        for i, (label, values) in enumerate(data.items()):
            fig.add_trace(go.Bar(
                name=label,
                x=list(range(len(values))),
                y=values,
                marker_color=self.color_palette[i % len(self.color_palette)]
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Index",
            yaxis_title="Value",
            template=self.theme,
            barmode='group'
        )
        
        return fig


if __name__ == "__main__":
    # Example usage
    viz = DataVisualizer()
    
    # Sample data
    numbers = np.random.normal(100, 15, 100).tolist()
    
    # Create histogram
    fig = viz.create_histogram(numbers, "Sample Distribution")
    fig.show()
