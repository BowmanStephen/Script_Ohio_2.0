#!/usr/bin/env python3
"""
CLI Tool for Generating Interactive Infographics

Command-line interface for generating standalone interactive HTML infographics
using the infographics component library.

Author: Claude Code Assistant
Created: 2025-11-19
Version: 1.0
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infographics import (
    get_component,
    AgentArchitectureVisualizer,
    ModelComparisonDashboard,
    PredictionConfidenceAnalyzer,
    DataFlowExplorer,
    LearningPathNavigator
)


def load_data_from_file(data_path: Path) -> Dict[str, Any]:
    """
    Load data from JSON file.
    
    Args:
        data_path: Path to JSON file
        
    Returns:
        Dictionary with loaded data
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_component(component_type: str,
                      output_path: Path,
                      data: Optional[Dict[str, Any]] = None,
                      data_file: Optional[Path] = None,
                      title: Optional[str] = None,
                      description: Optional[str] = None) -> Path:
    """
    Generate an infographic component.
    
    Args:
        component_type: Type of component to generate
        output_path: Path where HTML should be written
        data: Optional data dictionary
        data_file: Optional path to JSON data file
        title: Optional custom title
        description: Optional custom description
        
    Returns:
        Path to generated HTML file
    """
    # Load data if file provided
    if data_file:
        data = load_data_from_file(data_file)
    elif data is None:
        data = {}  # Empty dict triggers demo mode in components
    
    # Get component class
    try:
        component_class = get_component(component_type)
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"❌ Error: Components not available: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create component instance
    component_kwargs = {}
    if title:
        component_kwargs['title'] = title
    if description:
        component_kwargs['description'] = description
    
    component = component_class(**component_kwargs)
    
    # Generate HTML
    try:
        html_path = component.generate_html(data, output_path)
        return html_path
    except Exception as e:
        print(f"❌ Error generating component: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate interactive infographic components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate agent architecture with demo data
  python scripts/generate_infographics.py --component agent_architecture --output docs/infographics/
  
  # Generate model comparison from JSON file
  python scripts/generate_infographics.py --component model_comparison --data model_pack/models.json --output outputs/
  
  # Generate prediction analyzer with custom title
  python scripts/generate_infographics.py --component prediction_analyzer --output outputs/ --title "Week 13 Predictions"
        """
    )
    
    parser.add_argument(
        '--component',
        required=True,
        choices=['agent_architecture', 'model_comparison', 'prediction_analyzer', 
                 'data_flow', 'learning_path'],
        help='Type of component to generate'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('outputs/infographics/'),
        help='Output directory or file path (default: outputs/infographics/)'
    )
    
    parser.add_argument(
        '--data',
        type=Path,
        help='Path to JSON file containing component data'
    )
    
    parser.add_argument(
        '--title',
        help='Custom title for the component'
    )
    
    parser.add_argument(
        '--description',
        help='Custom description for the component'
    )
    
    args = parser.parse_args()
    
    # Generate component
    try:
        html_path = generate_component(
            component_type=args.component,
            output_path=args.output,
            data_file=args.data,
            title=args.title,
            description=args.description
        )
        
        print(f"✅ Generated {args.component} component: {html_path}")
        print(f"   Open in browser: file://{html_path.absolute()}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

