#!/usr/bin/env python3
"""
Example: Agent Architecture Visualizer

Demonstrates how to generate an interactive agent architecture visualization.

Author: Claude Code Assistant
Created: 2025-11-19
Version: 1.0
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infographics import AgentArchitectureVisualizer


def main():
    """Generate agent architecture visualization"""
    # Sample agent data
    agents_data = {
        'agents': [
            {
                'name': 'Learning Navigator',
                'agent_type': 'learning_navigator',
                'permission_level': 'READ_EXECUTE',
                'capabilities': ['guide_learning_path', 'recommend_content', 'track_progress']
            },
            {
                'name': 'Model Execution Engine',
                'agent_type': 'model_engine',
                'permission_level': 'READ_EXECUTE',
                'capabilities': ['run_prediction', 'generate_batch_predictions', 'get_model_metadata']
            },
            {
                'name': 'Insight Generator',
                'agent_type': 'insight_generator',
                'permission_level': 'READ_EXECUTE_WRITE',
                'capabilities': ['generate_analysis', 'create_visualizations', 'comparative_analysis']
            },
            {
                'name': 'Workflow Automator',
                'agent_type': 'workflow_automator',
                'permission_level': 'READ_EXECUTE_WRITE',
                'capabilities': ['create_workflow', 'execute_workflow', 'chain_analysis']
            },
            {
                'name': 'CFBD Integration',
                'agent_type': 'cfbd_integration',
                'permission_level': 'READ_EXECUTE_WRITE',
                'capabilities': ['cfbd_data_acquisition', 'get_games', 'get_stats']
            }
        ]
    }
    
    # Create visualizer
    visualizer = AgentArchitectureVisualizer(
        title="Script Ohio 2.0 Agent System Architecture",
        description="Interactive visualization of the multi-agent analytics platform",
        show_capabilities=True,
        interactive=True
    )
    
    # Generate HTML
    output_path = project_root / "outputs" / "infographics" / "agent_architecture.html"
    html_path = visualizer.generate_html(agents_data, output_path)
    
    print(f"✅ Generated agent architecture visualization: {html_path}")
    print(f"   Open in browser: file://{html_path.absolute()}")


if __name__ == "__main__":
    main()

