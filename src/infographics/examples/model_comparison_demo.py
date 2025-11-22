#!/usr/bin/env python3
"""
Example: Model Comparison Dashboard

Demonstrates how to generate an interactive model comparison dashboard.

Author: Claude Code Assistant
Created: 2025-11-19
Version: 1.0
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infographics import ModelComparisonDashboard


def main():
    """Generate model comparison dashboard"""
    # Sample model data
    models_data = {
        'models': [
            {
                'name': 'Ridge Regression',
                'metrics': {
                    'r2': 0.75,
                    'mae': 8.5,
                    'rmse': 12.3,
                    'accuracy': 0.72
                },
                'features': 86,
                'training_samples': 4989
            },
            {
                'name': 'XGBoost',
                'metrics': {
                    'r2': 0.82,
                    'mae': 7.2,
                    'rmse': 10.1,
                    'accuracy': 0.78
                },
                'features': 86,
                'training_samples': 4989
            },
            {
                'name': 'FastAI',
                'metrics': {
                    'r2': 0.79,
                    'mae': 7.8,
                    'rmse': 11.2,
                    'accuracy': 0.75
                },
                'features': 86,
                'training_samples': 4989
            }
        ]
    }
    
    # Create dashboard
    dashboard = ModelComparisonDashboard(
        title="Model Performance Comparison",
        description="Side-by-side comparison of Ridge, XGBoost, and FastAI models",
        interactive=True
    )
    
    # Generate HTML
    output_path = project_root / "outputs" / "infographics" / "model_comparison.html"
    html_path = dashboard.generate_html(models_data, output_path)
    
    print(f"✅ Generated model comparison dashboard: {html_path}")
    print(f"   Open in browser: file://{html_path.absolute()}")


if __name__ == "__main__":
    main()

