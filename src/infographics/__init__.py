#!/usr/bin/env python3
"""
Interactive Infographics Module

A reusable Python component library that generates standalone interactive HTML
infographics using Plotly. Components can be embedded in markdown documentation
or generated reports.

Author: Claude Code Assistant
Created: 2025-11-19
Version: 1.0
"""

from typing import Dict, Any, Optional
from pathlib import Path

# Import component classes (will be available after components.py is created)
try:
    from src.infographics.components import (
        AgentArchitectureVisualizer,
        ModelComparisonDashboard,
        PredictionConfidenceAnalyzer,
        DataFlowExplorer,
        LearningPathNavigator
    )
except ImportError:
    # Components not yet implemented
    AgentArchitectureVisualizer = None
    ModelComparisonDashboard = None
    PredictionConfidenceAnalyzer = None
    DataFlowExplorer = None
    LearningPathNavigator = None

# Import utilities
from src.infographics.utils import (
    validate_component_data,
    generate_standalone_html,
    sample_data,
    serialize_plotly_data,
    create_info_panel_html,
    ensure_output_directory,
    get_component_metadata
)

# Import templates
from src.infographics.templates import (
    get_base_template,
    get_standalone_html,
    get_controls_html
)

__all__ = [
    # Component classes
    'AgentArchitectureVisualizer',
    'ModelComparisonDashboard',
    'PredictionConfidenceAnalyzer',
    'DataFlowExplorer',
    'LearningPathNavigator',
    # Utility functions
    'validate_component_data',
    'generate_standalone_html',
    'sample_data',
    'serialize_plotly_data',
    'create_info_panel_html',
    'ensure_output_directory',
    'get_component_metadata',
    # Template functions
    'get_base_template',
    'get_standalone_html',
    'get_controls_html',
    # Helper function
    'get_component',
]


def get_component(component_type: str):
    """
    Get a component instance by type name.
    
    Args:
        component_type: Component type identifier ('agent_architecture', 
                       'model_comparison', 'prediction_analyzer', 'data_flow', 
                       'learning_path')
        
    Returns:
        Component class instance
        
    Raises:
        ValueError: If component type is not recognized
        ImportError: If components module is not available
    """
    if AgentArchitectureVisualizer is None:
        raise ImportError("Components module not yet implemented")
    
    component_map = {
        'agent_architecture': AgentArchitectureVisualizer,
        'model_comparison': ModelComparisonDashboard,
        'prediction_analyzer': PredictionConfidenceAnalyzer,
        'data_flow': DataFlowExplorer,
        'learning_path': LearningPathNavigator
    }
    
    component_class = component_map.get(component_type)
    if component_class is None:
        raise ValueError(
            f"Unknown component type: {component_type}. "
            f"Available types: {', '.join(component_map.keys())}"
        )
    
    return component_class

