#!/usr/bin/env python3
"""
Interactive Infographic Components

Core component classes for generating standalone interactive HTML infographics
using Plotly. Each component generates a complete, embeddable visualization.

Author: Claude Code Assistant
Created: 2025-11-19
Version: 1.0
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

from src.infographics.utils import (
    validate_component_data,
    generate_standalone_html,
    sample_data,
    ensure_output_directory,
    create_info_panel_html
)
from src.infographics.templates import get_controls_html

# Set up logging
logger = logging.getLogger(__name__)


class BaseComponent(ABC):
    """Base class for all infographic components"""
    
    def __init__(self, title: str = "Interactive Infographic", 
                 description: Optional[str] = None,
                 interactive: bool = True):
        """
        Initialize base component.
        
        Args:
            title: Component title
            description: Optional description
            interactive: Whether component should be interactive
        """
        self.title = title
        self.description = description
        self.interactive = interactive
    
    @abstractmethod
    def generate_html(self, data: Dict[str, Any], 
                     output_path: Union[str, Path]) -> Path:
        """
        Generate standalone HTML file.
        
        Args:
            data: Component-specific data dictionary
            output_path: Path where HTML should be written
            
        Returns:
            Path to generated HTML file
        """
        pass
    
    def _create_figure(self) -> go.Figure:
        """Create base Plotly figure with common styling"""
        fig = go.Figure()
        fig.update_layout(
            template="plotly_white",
            font=dict(family="Arial, sans-serif", size=12),
            plot_bgcolor="white",
            paper_bgcolor="white",
            hovermode="closest"
        )
        return fig


class AgentArchitectureVisualizer(BaseComponent):
    """
    Interactive flowchart of agent system architecture.
    
    Features:
    - Interactive network graph showing agent relationships
    - Click-to-expand agent details (capabilities, permissions)
    - Filter by permission level
    - Hover tooltips with agent metadata
    """
    
    def __init__(self, title: str = "Agent System Architecture",
                 description: Optional[str] = None,
                 show_capabilities: bool = True,
                 interactive: bool = True):
        """
        Initialize Agent Architecture Visualizer.
        
        Args:
            title: Component title
            description: Optional description
            show_capabilities: Whether to show agent capabilities
            interactive: Whether component should be interactive
        """
        super().__init__(title, description, interactive)
        self.show_capabilities = show_capabilities
    
    def generate_html(self, data: Dict[str, Any],
                     output_path: Union[str, Path]) -> Path:
        """
        Generate agent architecture visualization.
        
        Args:
            data: Dictionary with 'agents' key containing list of agent metadata
            output_path: Path where HTML should be written
            
        Returns:
            Path to generated HTML file
        """
        try:
            # Check for demo mode (empty data dict)
            if not data or 'agents' not in data or not data.get('agents'):
                # Demo mode - create sample agent data
                agents = self._get_demo_agents()
                logger.info("Using demo agent data")
            else:
                # Validate data
                validate_component_data(
                    data,
                    required_fields=['agents'],
                    field_types={'agents': list}
                )
                agents = data['agents']
            
            # Create network graph
            fig = self._create_agent_network(agents)
            
            # Generate controls if interactive
            controls_html = ""
            if self.interactive:
                controls = self._create_controls(agents)
                controls_html = get_controls_html(controls)
            
            # Generate standalone HTML
            output_path = ensure_output_directory(output_path)
            if not output_path.suffix:
                output_path = output_path / "agent_architecture.html"
            
            html_path = generate_standalone_html(
                figure=fig,
                output_path=output_path,
                title=self.title,
                description=self.description or "Interactive visualization of Script Ohio 2.0 agent system architecture"
            )
            
            # Inject controls if needed
            if controls_html:
                html_content = html_path.read_text(encoding='utf-8')
                html_content = html_content.replace(
                    '<div class="component-wrapper">',
                    f'<div class="component-wrapper">{controls_html}'
                )
                html_path.write_text(html_content, encoding='utf-8')
            
            logger.info(f"Generated agent architecture visualization: {html_path}")
            return html_path
            
        except Exception as e:
            logger.error(f"Error generating agent architecture: {str(e)}")
            raise
    
    def _create_agent_network(self, agents: List[Dict[str, Any]]) -> go.Figure:
        """Create network graph of agents"""
        # Extract agent information
        agent_names = []
        agent_types = []
        permission_levels = []
        capability_counts = []
        
        for agent in agents:
            agent_names.append(agent.get('name', agent.get('agent_type', 'Unknown')))
            agent_types.append(agent.get('agent_type', 'unknown'))
            permission_levels.append(agent.get('permission_level', 'READ_EXECUTE'))
            capabilities = agent.get('capabilities', [])
            capability_counts.append(len(capabilities) if isinstance(capabilities, list) else 0)
        
        # Create scatter plot with agent positions
        fig = go.Figure()
        
        # Group agents by permission level for better visualization
        permission_colors = {
            'READ_ONLY': '#6c757d',
            'READ_EXECUTE': '#0d6efd',
            'READ_EXECUTE_WRITE': '#28a745',
            'ADMIN': '#dc3545'
        }
        
        # Create traces for each permission level
        for perm_level in set(permission_levels):
            indices = [i for i, p in enumerate(permission_levels) if p == perm_level]
            if not indices:
                continue
            
            x_vals = [i % 4 for i in indices]  # Simple grid layout
            y_vals = [i // 4 for i in indices]
            
            hover_texts = [
                f"<b>{agent_names[i]}</b><br>"
                f"Type: {agent_types[i]}<br>"
                f"Permission: {permission_levels[i]}<br>"
                f"Capabilities: {capability_counts[i]}"
                for i in indices
            ]
            
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='markers+text',
                name=perm_level,
                text=[agent_names[i] for i in indices],
                textposition="middle right",
                marker=dict(
                    size=[20 + cap * 2 for cap in [capability_counts[i] for i in indices]],
                    color=permission_colors.get(perm_level, '#6c757d'),
                    line=dict(width=2, color='white')
                ),
                hovertemplate='%{text}<extra></extra>',
                customdata=[indices]
            ))
        
        fig.update_layout(
            title=self.title,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            height=600,
            showlegend=True,
            hovermode='closest'
        )
        
        return fig
    
    def _create_controls(self, agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create interactive controls"""
        permission_levels = sorted(set(agent.get('permission_level', 'READ_EXECUTE') for agent in agents))
        
        return [
            {
                'type': 'select',
                'id': 'permission-filter',
                'label': 'Filter by Permission Level',
                'options': [{'value': 'all', 'label': 'All'}] + [
                    {'value': perm, 'label': perm} for perm in permission_levels
                ],
                'default': 'all'
            }
        ]
    
    def _get_demo_agents(self) -> List[Dict[str, Any]]:
        """Get demo agent data for testing"""
        return [
            {
                'name': 'Learning Navigator',
                'agent_type': 'learning_navigator',
                'permission_level': 'READ_EXECUTE',
                'capabilities': ['guide_learning_path', 'recommend_content']
            },
            {
                'name': 'Model Execution Engine',
                'agent_type': 'model_engine',
                'permission_level': 'READ_EXECUTE',
                'capabilities': ['run_prediction', 'generate_batch_predictions']
            },
            {
                'name': 'Insight Generator',
                'agent_type': 'insight_generator',
                'permission_level': 'READ_EXECUTE_WRITE',
                'capabilities': ['generate_analysis', 'create_visualizations']
            }
        ]


class ModelComparisonDashboard(BaseComponent):
    """
    Side-by-side model performance comparison dashboard.
    
    Features:
    - Side-by-side comparison of Ridge/XGBoost/FastAI models
    - Interactive slider for feature importance exploration
    - Toggle between metrics (R², MAE, RMSE, accuracy)
    - Performance timeline if historical data available
    """
    
    def __init__(self, title: str = "Model Comparison Dashboard",
                 description: Optional[str] = None,
                 interactive: bool = True):
        super().__init__(title, description, interactive)
    
    def generate_html(self, data: Dict[str, Any],
                     output_path: Union[str, Path]) -> Path:
        """
        Generate model comparison dashboard.
        
        Args:
            data: Dictionary with 'models' key containing model metadata
            output_path: Path where HTML should be written
            
        Returns:
            Path to generated HTML file
        """
        try:
            # Check for demo mode (empty data dict)
            if not data or 'models' not in data or not data.get('models'):
                models = self._get_demo_models()
                logger.info("Using demo model data")
            else:
                # Validate data
                validate_component_data(
                    data,
                    required_fields=['models'],
                    field_types={'models': list}
                )
                models = data['models']
            
            # Create comparison dashboard
            fig = self._create_comparison_dashboard(models)
            
            # Generate controls
            controls_html = ""
            if self.interactive:
                controls = self._create_controls(models)
                controls_html = get_controls_html(controls)
            
            # Generate standalone HTML
            output_path = ensure_output_directory(output_path)
            if not output_path.suffix:
                output_path = output_path / "model_comparison.html"
            
            html_path = generate_standalone_html(
                figure=fig,
                output_path=output_path,
                title=self.title,
                description=self.description or "Interactive comparison of machine learning model performance"
            )
            
            # Inject controls
            if controls_html:
                html_content = html_path.read_text(encoding='utf-8')
                html_content = html_content.replace(
                    '<div class="component-wrapper">',
                    f'<div class="component-wrapper">{controls_html}'
                )
                html_path.write_text(html_content, encoding='utf-8')
            
            logger.info(f"Generated model comparison dashboard: {html_path}")
            return html_path
            
        except Exception as e:
            logger.error(f"Error generating model comparison: {str(e)}")
            raise
    
    def _create_comparison_dashboard(self, models: List[Dict[str, Any]]) -> go.Figure:
        """Create model comparison dashboard"""
        # Extract model metrics
        model_names = [m.get('name', 'Unknown') for m in models]
        metrics = ['r2', 'mae', 'rmse', 'accuracy']
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('R² Score', 'MAE', 'RMSE', 'Accuracy'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Add traces for each metric
        colors = ['#0d6efd', '#28a745', '#ffc107', '#dc3545']
        
        for idx, metric in enumerate(metrics):
            row = (idx // 2) + 1
            col = (idx % 2) + 1
            
            values = [m.get('metrics', {}).get(metric, 0) for m in models]
            
            fig.add_trace(
                go.Bar(
                    x=model_names,
                    y=values,
                    name=metric.upper(),
                    marker_color=colors[idx % len(colors)],
                    showlegend=False
                ),
                row=row, col=col
            )
        
        fig.update_layout(
            title=self.title,
            height=800,
            showlegend=False
        )
        
        return fig
    
    def _create_controls(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create interactive controls"""
        return [
            {
                'type': 'select',
                'id': 'metric-select',
                'label': 'Metric',
                'options': [
                    {'value': 'r2', 'label': 'R² Score'},
                    {'value': 'mae', 'label': 'MAE'},
                    {'value': 'rmse', 'label': 'RMSE'},
                    {'value': 'accuracy', 'label': 'Accuracy'}
                ],
                'default': 'r2'
            }
        ]
    
    def _get_demo_models(self) -> List[Dict[str, Any]]:
        """Get demo model data"""
        return [
            {
                'name': 'Ridge Regression',
                'metrics': {'r2': 0.75, 'mae': 8.5, 'rmse': 12.3, 'accuracy': 0.72}
            },
            {
                'name': 'XGBoost',
                'metrics': {'r2': 0.82, 'mae': 7.2, 'rmse': 10.1, 'accuracy': 0.78}
            },
            {
                'name': 'FastAI',
                'metrics': {'r2': 0.79, 'mae': 7.8, 'rmse': 11.2, 'accuracy': 0.75}
            }
        ]


class PredictionConfidenceAnalyzer(BaseComponent):
    """
    Interactive scatter plot analyzer for prediction confidence.
    
    Features:
    - Interactive scatter plot: spread vs confidence
    - Filter controls (conference, team, week)
    - Upset probability calculator (slider for threshold)
    - Hover details showing game info and prediction breakdown
    """
    
    def __init__(self, title: str = "Prediction Confidence Analyzer",
                 description: Optional[str] = None,
                 interactive: bool = True):
        super().__init__(title, description, interactive)
    
    def generate_html(self, data: Dict[str, Any],
                     output_path: Union[str, Path]) -> Path:
        """
        Generate prediction confidence analyzer.
        
        Args:
            data: Dictionary with 'predictions' key containing prediction data
            output_path: Path where HTML should be written
            
        Returns:
            Path to generated HTML file
        """
        try:
            # Check for demo mode (empty data dict)
            if not data or 'predictions' not in data or not data.get('predictions'):
                predictions = self._get_demo_predictions()
                logger.info("Using demo prediction data")
            else:
                # Validate data
                validate_component_data(
                    data,
                    required_fields=['predictions'],
                    field_types={'predictions': list}
                )
                predictions = data['predictions']
            
            # Sample if too large
            if len(predictions) > 1000:
                predictions = sample_data(predictions, max_samples=1000)
            
            # Create scatter plot
            fig = self._create_scatter_plot(predictions)
            
            # Generate controls
            controls_html = ""
            if self.interactive:
                controls = self._create_controls(predictions)
                controls_html = get_controls_html(controls)
            
            # Generate standalone HTML
            output_path = ensure_output_directory(output_path)
            if not output_path.suffix:
                output_path = output_path / "prediction_analyzer.html"
            
            html_path = generate_standalone_html(
                figure=fig,
                output_path=output_path,
                title=self.title,
                description=self.description or "Interactive analysis of prediction confidence vs spread"
            )
            
            # Inject controls
            if controls_html:
                html_content = html_path.read_text(encoding='utf-8')
                html_content = html_content.replace(
                    '<div class="component-wrapper">',
                    f'<div class="component-wrapper">{controls_html}'
                )
                html_path.write_text(html_content, encoding='utf-8')
            
            logger.info(f"Generated prediction analyzer: {html_path}")
            return html_path
            
        except Exception as e:
            logger.error(f"Error generating prediction analyzer: {str(e)}")
            raise
    
    def _create_scatter_plot(self, predictions: List[Dict[str, Any]]) -> go.Figure:
        """Create scatter plot of spread vs confidence"""
        spreads = [p.get('spread', 0) for p in predictions]
        confidences = [p.get('confidence', 0) for p in predictions]
        games = [f"{p.get('away_team', 'Away')} @ {p.get('home_team', 'Home')}" for p in predictions]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=spreads,
            y=confidences,
            mode='markers',
            marker=dict(
                size=10,
                color=confidences,
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Confidence")
            ),
            text=games,
            hovertemplate='<b>%{text}</b><br>Spread: %{x}<br>Confidence: %{y:.2%}<extra></extra>'
        ))
        
        fig.update_layout(
            title=self.title,
            xaxis_title="Spread",
            yaxis_title="Confidence",
            height=600,
            hovermode='closest'
        )
        
        return fig
    
    def _create_controls(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create interactive controls"""
        conferences = sorted(set(p.get('conference', '') for p in predictions if p.get('conference')))
        weeks = sorted(set(p.get('week', 0) for p in predictions if p.get('week')))
        
        controls = [
            {
                'type': 'slider',
                'id': 'upset-threshold',
                'label': 'Upset Probability Threshold',
                'min': 0,
                'max': 100,
                'step': 5,
                'default': 30
            }
        ]
        
        if conferences:
            controls.append({
                'type': 'select',
                'id': 'conference-filter',
                'label': 'Conference',
                'options': [{'value': 'all', 'label': 'All'}] + [
                    {'value': conf, 'label': conf} for conf in conferences
                ],
                'default': 'all'
            })
        
        if weeks:
            controls.append({
                'type': 'select',
                'id': 'week-filter',
                'label': 'Week',
                'options': [{'value': 'all', 'label': 'All'}] + [
                    {'value': str(w), 'label': f'Week {w}'} for w in weeks
                ],
                'default': 'all'
            })
        
        return controls
    
    def _get_demo_predictions(self) -> List[Dict[str, Any]]:
        """Get demo prediction data"""
        import random
        teams = ['Ohio State', 'Michigan', 'Alabama', 'Georgia', 'Texas', 'Oregon']
        conferences = ['Big Ten', 'SEC', 'Big 12', 'Pac-12']
        
        return [
            {
                'away_team': random.choice(teams),
                'home_team': random.choice(teams),
                'spread': random.uniform(-20, 20),
                'confidence': random.uniform(0.5, 0.95),
                'conference': random.choice(conferences),
                'week': random.randint(1, 13)
            }
            for _ in range(50)
        ]


class DataFlowExplorer(BaseComponent):
    """
    Interactive pipeline diagram showing data transformations.
    
    Features:
    - Interactive pipeline diagram showing data transformations
    - Hover reveals feature engineering steps
    - Week-by-week progression slider
    - Click nodes to see data samples
    """
    
    def __init__(self, title: str = "Data Flow Explorer",
                 description: Optional[str] = None,
                 interactive: bool = True):
        super().__init__(title, description, interactive)
    
    def generate_html(self, data: Dict[str, Any],
                     output_path: Union[str, Path]) -> Path:
        """
        Generate data flow explorer.
        
        Args:
            data: Dictionary with 'pipeline' key containing pipeline steps
            output_path: Path where HTML should be written
            
        Returns:
            Path to generated HTML file
        """
        try:
            # Check for demo mode (empty data dict)
            if not data or 'pipeline' not in data or not data.get('pipeline'):
                pipeline = self._get_demo_pipeline()
                logger.info("Using demo pipeline data")
            else:
                # Validate data
                validate_component_data(
                    data,
                    required_fields=['pipeline'],
                    field_types={'pipeline': list}
                )
                pipeline = data['pipeline']
            
            # Create pipeline diagram
            fig = self._create_pipeline_diagram(pipeline)
            
            # Generate controls
            controls_html = ""
            if self.interactive:
                controls = self._create_controls(pipeline)
                controls_html = get_controls_html(controls)
            
            # Generate standalone HTML
            output_path = ensure_output_directory(output_path)
            if not output_path.suffix:
                output_path = output_path / "data_flow.html"
            
            html_path = generate_standalone_html(
                figure=fig,
                output_path=output_path,
                title=self.title,
                description=self.description or "Interactive visualization of data processing pipeline"
            )
            
            # Inject controls
            if controls_html:
                html_content = html_path.read_text(encoding='utf-8')
                html_content = html_content.replace(
                    '<div class="component-wrapper">',
                    f'<div class="component-wrapper">{controls_html}'
                )
                html_path.write_text(html_content, encoding='utf-8')
            
            logger.info(f"Generated data flow explorer: {html_path}")
            return html_path
            
        except Exception as e:
            logger.error(f"Error generating data flow explorer: {str(e)}")
            raise
    
    def _create_pipeline_diagram(self, pipeline: List[Dict[str, Any]]) -> go.Figure:
        """Create pipeline diagram using Sankey diagram"""
        # Extract pipeline steps
        labels = [step.get('name', f"Step {i+1}") for i, step in enumerate(pipeline)]
        
        # Create simple flow diagram
        fig = go.Figure()
        
        # Create horizontal flow
        x_positions = [i / (len(pipeline) - 1) if len(pipeline) > 1 else 0.5 for i in range(len(pipeline))]
        y_positions = [0.5] * len(pipeline)
        
        # Add nodes
        for i, (label, x, y) in enumerate(zip(labels, x_positions, y_positions)):
            fig.add_trace(go.Scatter(
                x=[x],
                y=[y],
                mode='markers+text',
                name=label,
                text=[label],
                textposition="middle center",
                marker=dict(size=50, color='#0d6efd'),
                hovertemplate=f'<b>{label}</b><br>%{{text}}<extra></extra>'
            ))
        
        # Add connections
        for i in range(len(pipeline) - 1):
            fig.add_trace(go.Scatter(
                x=[x_positions[i], x_positions[i+1]],
                y=[y_positions[i], y_positions[i+1]],
                mode='lines',
                line=dict(width=3, color='#6c757d'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        fig.update_layout(
            title=self.title,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-0.1, 1.1]),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, 1]),
            height=400,
            showlegend=False
        )
        
        return fig
    
    def _create_controls(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create interactive controls"""
        return [
            {
                'type': 'slider',
                'id': 'week-slider',
                'label': 'Week',
                'min': 1,
                'max': 13,
                'step': 1,
                'default': 1
            }
        ]
    
    def _get_demo_pipeline(self) -> List[Dict[str, Any]]:
        """Get demo pipeline data"""
        return [
            {'name': 'Data Ingestion', 'type': 'input'},
            {'name': 'Feature Engineering', 'type': 'transform'},
            {'name': 'Model Prediction', 'type': 'process'},
            {'name': 'Output Generation', 'type': 'output'}
        ]


class LearningPathNavigator(BaseComponent):
    """
    Interactive notebook progression guide.
    
    Features:
    - Interactive notebook progression tree
    - Skill level indicators (beginner/intermediate/advanced)
    - Prerequisite dependencies visualization
    - Click to view notebook objectives
    """
    
    def __init__(self, title: str = "Learning Path Navigator",
                 description: Optional[str] = None,
                 interactive: bool = True):
        super().__init__(title, description, interactive)
    
    def generate_html(self, data: Dict[str, Any],
                     output_path: Union[str, Path]) -> Path:
        """
        Generate learning path navigator.
        
        Args:
            data: Dictionary with 'notebooks' key containing notebook metadata
            output_path: Path where HTML should be written
            
        Returns:
            Path to generated HTML file
        """
        try:
            # Check for demo mode (empty data dict)
            if not data or 'notebooks' not in data or not data.get('notebooks'):
                notebooks = self._get_demo_notebooks()
                logger.info("Using demo notebook data")
            else:
                # Validate data
                validate_component_data(
                    data,
                    required_fields=['notebooks'],
                    field_types={'notebooks': list}
                )
                notebooks = data['notebooks']
            
            # Create learning path visualization
            fig = self._create_learning_path(notebooks)
            
            # Generate controls
            controls_html = ""
            if self.interactive:
                controls = self._create_controls(notebooks)
                controls_html = get_controls_html(controls)
            
            # Generate standalone HTML
            output_path = ensure_output_directory(output_path)
            if not output_path.suffix:
                output_path = output_path / "learning_path.html"
            
            html_path = generate_standalone_html(
                figure=fig,
                output_path=output_path,
                title=self.title,
                description=self.description or "Interactive guide through Script Ohio 2.0 learning path"
            )
            
            # Inject controls
            if controls_html:
                html_content = html_path.read_text(encoding='utf-8')
                html_content = html_content.replace(
                    '<div class="component-wrapper">',
                    f'<div class="component-wrapper">{controls_html}'
                )
                html_path.write_text(html_content, encoding='utf-8')
            
            logger.info(f"Generated learning path navigator: {html_path}")
            return html_path
            
        except Exception as e:
            logger.error(f"Error generating learning path navigator: {str(e)}")
            raise
    
    def _create_learning_path(self, notebooks: List[Dict[str, Any]]) -> go.Figure:
        """Create learning path visualization"""
        # Extract notebook information
        notebook_names = [nb.get('name', f"Notebook {i+1}") for i, nb in enumerate(notebooks)]
        skill_levels = [nb.get('skill_level', 'beginner') for nb in notebooks]
        
        # Create horizontal progression
        fig = go.Figure()
        
        # Color mapping for skill levels
        skill_colors = {
            'beginner': '#28a745',
            'intermediate': '#ffc107',
            'advanced': '#dc3545'
        }
        
        x_positions = list(range(len(notebooks)))
        y_positions = [0] * len(notebooks)
        
        # Add notebook nodes
        for i, (name, skill) in enumerate(zip(notebook_names, skill_levels)):
            fig.add_trace(go.Scatter(
                x=[x_positions[i]],
                y=[y_positions[i]],
                mode='markers+text',
                name=name,
                text=[f"{i+1}. {name}"],
                textposition="top center",
                marker=dict(
                    size=30,
                    color=skill_colors.get(skill, '#6c757d'),
                    line=dict(width=2, color='white')
                ),
                hovertemplate=f'<b>{name}</b><br>Skill Level: {skill}<extra></extra>'
            ))
        
        # Add connections
        for i in range(len(notebooks) - 1):
            fig.add_trace(go.Scatter(
                x=[x_positions[i], x_positions[i+1]],
                y=[y_positions[i], y_positions[i+1]],
                mode='lines',
                line=dict(width=2, color='#6c757d', dash='dash'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        fig.update_layout(
            title=self.title,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-0.5, 0.5]),
            height=400,
            showlegend=False
        )
        
        return fig
    
    def _create_controls(self, notebooks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create interactive controls"""
        skill_levels = sorted(set(nb.get('skill_level', 'beginner') for nb in notebooks))
        
        return [
            {
                'type': 'select',
                'id': 'skill-filter',
                'label': 'Skill Level',
                'options': [{'value': 'all', 'label': 'All'}] + [
                    {'value': skill, 'label': skill.title()} for skill in skill_levels
                ],
                'default': 'all'
            }
        ]
    
    def _get_demo_notebooks(self) -> List[Dict[str, Any]]:
        """Get demo notebook data"""
        return [
            {'name': 'Data Dictionary', 'skill_level': 'beginner'},
            {'name': 'Intro to Data', 'skill_level': 'beginner'},
            {'name': 'Simple Rankings', 'skill_level': 'beginner'},
            {'name': 'Metrics Comparison', 'skill_level': 'intermediate'},
            {'name': 'Team Similarity', 'skill_level': 'intermediate'},
            {'name': 'Matchup Predictor', 'skill_level': 'advanced'}
        ]

