#!/usr/bin/env python3
"""
Utility Functions for Interactive Infographics

Helper functions for data validation, HTML generation, and component utilities.

Author: Claude Code Assistant
Created: 2025-11-19
Version: 1.0
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import plotly.graph_objects as go

# Set up logging
logger = logging.getLogger(__name__)


def validate_component_data(data: Dict[str, Any], 
                           required_fields: List[str],
                           field_types: Optional[Dict[str, type]] = None) -> bool:
    """
    Validate that data structure matches component requirements.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        field_types: Optional dict mapping field names to expected types
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    if field_types:
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                raise TypeError(
                    f"Field '{field}' must be of type {expected_type.__name__}, "
                    f"got {type(data[field]).__name__}"
                )
    
    return True


def generate_standalone_html(figure: go.Figure,
                             output_path: Path,
                             title: str = "Interactive Infographic",
                             description: Optional[str] = None,
                             additional_css: Optional[str] = None,
                             additional_js: Optional[str] = None) -> Path:
    """
    Generate standalone HTML file from Plotly figure.
    
    Args:
        figure: Plotly figure object
        output_path: Path where HTML file should be written
        title: Page title
        description: Optional description
        additional_css: Optional additional CSS
        additional_js: Optional additional JavaScript
        
    Returns:
        Path to generated HTML file
    """
    from src.infographics.templates import get_standalone_html
    
    # Generate figure HTML (without full HTML wrapper)
    figure_html = figure.to_html(full_html=False, include_plotlyjs='cdn')
    
    # Wrap in standalone HTML template
    html_content = get_standalone_html(
        figure_html=figure_html,
        title=title,
        description=description,
        additional_css=additional_css,
        additional_js=additional_js
    )
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write HTML file
    output_path.write_text(html_content, encoding='utf-8')
    logger.info(f"Generated standalone HTML: {output_path}")
    
    return output_path


def sample_data(data: List[Any], max_samples: int = 1000) -> List[Any]:
    """
    Sample data for large datasets to improve performance.
    
    Args:
        data: List of data items
        max_samples: Maximum number of samples to return
        
    Returns:
        Sampled data list
    """
    if len(data) <= max_samples:
        return data
    
    # Use systematic sampling for better distribution
    step = len(data) / max_samples
    sampled = [data[int(i * step)] for i in range(max_samples)]
    logger.info(f"Sampled {len(data)} items down to {len(sampled)} for performance")
    return sampled


def serialize_plotly_data(figure: go.Figure) -> Dict[str, Any]:
    """
    Serialize Plotly figure to JSON-serializable dict.
    
    Args:
        figure: Plotly figure object
        
    Returns:
        Dictionary representation of figure
    """
    return {
        'data': json.loads(figure.to_json()),
        'layout': json.loads(figure.layout.to_json()) if figure.layout else {}
    }


def create_info_panel_html(title: str, content: str, info_type: str = "info") -> str:
    """
    Create HTML for informational panel.
    
    Args:
        title: Panel title
        content: Panel content (can be HTML)
        info_type: Type of info ('info', 'warning', 'success', 'error')
        
    Returns:
        HTML string for info panel
    """
    type_classes = {
        'info': 'border-left: 4px solid var(--primary-color);',
        'warning': 'border-left: 4px solid #ffc107;',
        'success': 'border-left: 4px solid #28a745;',
        'error': 'border-left: 4px solid #dc3545;'
    }
    
    border_style = type_classes.get(info_type, type_classes['info'])
    
    return f"""
    <div class="info-panel" style="{border_style}">
        <strong>{title}</strong>
        <div style="margin-top: 10px;">{content}</div>
    </div>
    """


def ensure_output_directory(output_path: Union[str, Path]) -> Path:
    """
    Ensure output directory exists, creating if necessary.
    
    Args:
        output_path: Path to output file or directory
        
    Returns:
        Path object with directory created
    """
    output_path = Path(output_path)
    if output_path.suffix:  # It's a file path
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:  # It's a directory path
        output_path.mkdir(parents=True, exist_ok=True)
    
    return output_path


def get_component_metadata(component_type: str) -> Dict[str, Any]:
    """
    Get metadata for a component type.
    
    Args:
        component_type: Component type identifier
        
    Returns:
        Dictionary with component metadata
    """
    metadata = {
        'agent_architecture': {
            'name': 'Agent Architecture Visualizer',
            'description': 'Interactive flowchart of agent system',
            'required_fields': ['agents'],
            'estimated_time': 2.0
        },
        'model_comparison': {
            'name': 'Model Comparison Dashboard',
            'description': 'Side-by-side model performance comparison',
            'required_fields': ['models'],
            'estimated_time': 2.5
        },
        'prediction_analyzer': {
            'name': 'Prediction Confidence Analyzer',
            'description': 'Interactive scatter plots with filters',
            'required_fields': ['predictions'],
            'estimated_time': 2.0
        },
        'data_flow': {
            'name': 'Data Flow Explorer',
            'description': 'Interactive pipeline diagram',
            'required_fields': ['pipeline'],
            'estimated_time': 2.5
        },
        'learning_path': {
            'name': 'Learning Path Navigator',
            'description': 'Interactive notebook progression guide',
            'required_fields': ['notebooks'],
            'estimated_time': 2.0
        }
    }
    
    return metadata.get(component_type, {
        'name': 'Unknown Component',
        'description': 'Component type not recognized',
        'required_fields': [],
        'estimated_time': 2.0
    })

