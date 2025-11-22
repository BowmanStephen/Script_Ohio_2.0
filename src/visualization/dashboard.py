"""
Interactive Dashboard Module using Plotly.
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any, Optional

def create_team_efficiency_dashboard(teams_data: pd.DataFrame, x_col: str = 'offense_ppa', y_col: str = 'defense_ppa', 
                                   title: str = 'Team Efficiency', hover_data: Optional[List[str]] = None) -> go.Figure:
    """
    Create scatter plot of Team Efficiency (e.g. Offense vs Defense PPA).
    
    Args:
        teams_data: DataFrame with team metrics
        x_col: Column for X axis (e.g. Offense)
        y_col: Column for Y axis (e.g. Defense)
        title: Chart title
        hover_data: Columns to show on hover
        
    Returns:
        Plotly Figure
    """
    if hover_data is None:
        hover_data = ['team', 'conference', 'record'] if 'record' in teams_data.columns else ['team', 'conference']
        
    # Invert Y axis for defense stats where lower is better (like PPA allowed/Defense PPA)
    # Usually Defense PPA means "Points Added by Defense" (negative is good) or "Points Allowed" (lower is good).
    # If it's PPA Allowed, we might want to invert.
    # Assuming standard scatter for now.
    
    fig = px.scatter(teams_data, x=x_col, y=y_col, color='conference', 
                     hover_data=hover_data, title=title,
                     text='team' if len(teams_data) < 30 else None)
                     
    fig.update_traces(textposition='top center')
    fig.update_layout(height=800, width=1000)
    
    # Add quadrant lines (averages)
    x_mean = teams_data[x_col].mean()
    y_mean = teams_data[y_col].mean()
    
    fig.add_hline(y=y_mean, line_dash="dash", line_color="gray", annotation_text="Avg Defense")
    fig.add_vline(x=x_mean, line_dash="dash", line_color="gray", annotation_text="Avg Offense")
    
    return fig

def create_metric_distribution_explorer(metrics_data: pd.DataFrame, metrics: List[str]) -> go.Figure:
    """
    Create histograms/distributions for multiple metrics.
    
    Args:
        metrics_data: DataFrame containing metrics
        metrics: List of metric columns to plot
        
    Returns:
        Plotly Figure (subplot or dropdown)
    """
    # Create a figure with dropdown to select metric
    fig = go.Figure()

    for metric in metrics:
        if metric in metrics_data.columns:
            fig.add_trace(go.Histogram(x=metrics_data[metric], name=metric, visible=False, opacity=0.75))

    # Make first trace visible
    if fig.data:
        fig.data[0].visible = True

    # Create dropdown buttons
    buttons = []
    for i, metric in enumerate(metrics):
        visible = [False] * len(fig.data)
        if i < len(visible):
            visible[i] = True
            
        buttons.append(dict(
            label=metric,
            method="update",
            args=[{"visible": visible},
                  {"title": f"Distribution of {metric}"}]
        ))

    fig.update_layout(
        updatemenus=[dict(active=0, buttons=buttons)],
        title=f"Metric Distribution: {metrics[0] if metrics else ''}",
        xaxis_title="Value",
        yaxis_title="Count"
    )
    
    return fig

