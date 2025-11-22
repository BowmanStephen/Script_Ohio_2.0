#!/usr/bin/env python3
"""
Example: Prediction Confidence Analyzer

Demonstrates how to generate an interactive prediction confidence analyzer.

Author: Claude Code Assistant
Created: 2025-11-19
Version: 1.0
"""

import sys
import random
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infographics import PredictionConfidenceAnalyzer


def main():
    """Generate prediction confidence analyzer"""
    # Sample prediction data
    teams = ['Ohio State', 'Michigan', 'Alabama', 'Georgia', 'Texas', 'Oregon', 
             'USC', 'Notre Dame', 'Penn State', 'LSU', 'Oklahoma', 'Clemson']
    conferences = ['Big Ten', 'SEC', 'Big 12', 'Pac-12', 'ACC']
    
    predictions_data = {
        'predictions': [
            {
                'away_team': random.choice(teams),
                'home_team': random.choice(teams),
                'spread': round(random.uniform(-20, 20), 1),
                'confidence': round(random.uniform(0.5, 0.95), 3),
                'conference': random.choice(conferences),
                'week': random.randint(1, 13),
                'upset_probability': round(random.uniform(0.1, 0.4), 3)
            }
            for _ in range(100)
        ]
    }
    
    # Create analyzer
    analyzer = PredictionConfidenceAnalyzer(
        title="Prediction Confidence Analysis",
        description="Interactive scatter plot of spread vs confidence with filters",
        interactive=True
    )
    
    # Generate HTML
    output_path = project_root / "outputs" / "infographics" / "prediction_analyzer.html"
    html_path = analyzer.generate_html(predictions_data, output_path)
    
    print(f"✅ Generated prediction analyzer: {html_path}")
    print(f"   Open in browser: file://{html_path.absolute()}")


if __name__ == "__main__":
    main()

