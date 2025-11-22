#!/usr/bin/env python3
"""
Quick Demo: Interactive Infographics

Demonstrates all 5 infographic components with demo data.

Author: Claude Code Assistant
Created: 2025-11-19
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infographics import (
    AgentArchitectureVisualizer,
    ModelComparisonDashboard,
    PredictionConfidenceAnalyzer,
    DataFlowExplorer,
    LearningPathNavigator
)

def main():
    """Generate all infographic components"""
    output_dir = project_root / "outputs" / "infographics"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🎨 Generating Interactive Infographics...")
    print("=" * 60)
    
    # 1. Agent Architecture
    print("\n1️⃣  Agent Architecture Visualizer")
    visualizer = AgentArchitectureVisualizer(
        title="Script Ohio 2.0 Agent System Architecture",
        description="Interactive visualization of the multi-agent analytics platform"
    )
    html_path = visualizer.generate_html({}, output_dir / "agent_architecture.html")
    print(f"   ✅ Generated: {html_path}")
    print(f"   📂 Open: file://{html_path.absolute()}")
    
    # 2. Model Comparison
    print("\n2️⃣  Model Comparison Dashboard")
    dashboard = ModelComparisonDashboard(
        title="Model Performance Comparison",
        description="Side-by-side comparison of Ridge, XGBoost, and FastAI models"
    )
    html_path = dashboard.generate_html({}, output_dir / "model_comparison.html")
    print(f"   ✅ Generated: {html_path}")
    print(f"   📂 Open: file://{html_path.absolute()}")
    
    # 3. Prediction Analyzer
    print("\n3️⃣  Prediction Confidence Analyzer")
    analyzer = PredictionConfidenceAnalyzer(
        title="Prediction Confidence Analysis",
        description="Interactive scatter plot of spread vs confidence"
    )
    html_path = analyzer.generate_html({}, output_dir / "prediction_analyzer.html")
    print(f"   ✅ Generated: {html_path}")
    print(f"   📂 Open: file://{html_path.absolute()}")
    
    # 4. Data Flow Explorer
    print("\n4️⃣  Data Flow Explorer")
    explorer = DataFlowExplorer(
        title="Data Processing Pipeline",
        description="Interactive visualization of data transformations"
    )
    html_path = explorer.generate_html({}, output_dir / "data_flow.html")
    print(f"   ✅ Generated: {html_path}")
    print(f"   📂 Open: file://{html_path.absolute()}")
    
    # 5. Learning Path Navigator
    print("\n5️⃣  Learning Path Navigator")
    navigator = LearningPathNavigator(
        title="Starter Pack Learning Path",
        description="Interactive guide through Script Ohio 2.0 notebooks"
    )
    html_path = navigator.generate_html({}, output_dir / "learning_path.html")
    print(f"   ✅ Generated: {html_path}")
    print(f"   📂 Open: file://{html_path.absolute()}")
    
    print("\n" + "=" * 60)
    print("✨ All infographics generated successfully!")
    print(f"\n📁 Output directory: {output_dir}")
    print("\n💡 Tip: Open any HTML file in your browser to see the interactive visualizations")
    print("   All components support dark mode (based on system preferences)")

if __name__ == "__main__":
    main()

