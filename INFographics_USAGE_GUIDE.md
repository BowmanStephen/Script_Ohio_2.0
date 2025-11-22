# Interactive Infographics Usage Guide

## Quick Demo

Run the demo script to generate all 5 components:

```bash
python3 demo_infographics.py
```

This generates all infographics in `outputs/infographics/` with demo data.

## Three Ways to Use Infographics

### 1. Command Line (CLI)

Generate components directly from the command line:

```bash
# Generate agent architecture (uses demo data)
python3 scripts/generate_infographics.py --component agent_architecture --output outputs/infographics/

# Generate with custom title
python3 scripts/generate_infographics.py --component model_comparison --output outputs/ --title "2025 Model Performance"

# Generate from JSON data file
python3 scripts/generate_infographics.py --component prediction_analyzer --data predictions.json --output outputs/
```

**Available components:**
- `agent_architecture` - Agent system visualization
- `model_comparison` - Model performance dashboard
- `prediction_analyzer` - Prediction confidence scatter plot
- `data_flow` - Data pipeline diagram
- `learning_path` - Notebook progression guide

### 2. Programmatic Usage

Use components directly in Python:

```python
from src.infographics import AgentArchitectureVisualizer
from pathlib import Path

# Create visualizer
visualizer = AgentArchitectureVisualizer(
    title="My Agent System",
    description="Custom description",
    interactive=True
)

# Generate with your data
data = {
    'agents': [
        {
            'name': 'Learning Navigator',
            'agent_type': 'learning_navigator',
            'permission_level': 'READ_EXECUTE',
            'capabilities': ['guide_learning_path', 'recommend_content']
        }
        # ... more agents
    ]
}

html_path = visualizer.generate_html(data, Path("outputs/my_agents.html"))
print(f"Generated: {html_path}")
```

**Or use demo mode (no data required):**

```python
# Empty dict triggers demo mode
html_path = visualizer.generate_html({}, Path("outputs/demo.html"))
```

### 3. Via InsightGeneratorAgent

Generate infographics through the agent system:

```python
from agents.insight_generator_agent import InsightGeneratorAgent

agent = InsightGeneratorAgent(agent_id="insight_001")

result = agent._execute_action(
    "generate_infographic",
    {
        "component_type": "agent_architecture",
        "data": {
            "agents": [
                {
                    "name": "Learning Navigator",
                    "agent_type": "learning_navigator",
                    "permission_level": "READ_EXECUTE",
                    "capabilities": ["guide_learning_path"]
                }
            ]
        },
        "output_path": "outputs/infographics/",
        "title": "Script Ohio 2.0 Agent System"
    },
    {"user_id": "user_001"}
)

print(f"Generated: {result['html_path']}")
```

## Component Features

### All Components Include:
- ✅ **Standalone HTML** - No build step, just open in browser
- ✅ **Dark Mode Support** - Automatically adapts to system preferences
- ✅ **Responsive Design** - Works on mobile, tablet, desktop
- ✅ **Interactive Controls** - Filters, sliders, toggles
- ✅ **Accessibility** - ARIA labels, keyboard navigation
- ✅ **Plotly Integration** - Professional interactive charts

### Component-Specific Features:

**AgentArchitectureVisualizer:**
- Network graph of agent relationships
- Filter by permission level
- Hover tooltips with agent details

**ModelComparisonDashboard:**
- Side-by-side metric comparison
- Toggle between R², MAE, RMSE, accuracy
- Feature importance exploration

**PredictionConfidenceAnalyzer:**
- Scatter plot: spread vs confidence
- Filter by conference, team, week
- Upset probability calculator

**DataFlowExplorer:**
- Interactive pipeline diagram
- Week-by-week progression slider
- Hover reveals transformation steps

**LearningPathNavigator:**
- Notebook progression tree
- Skill level indicators
- Prerequisite visualization

## Embedding in Documentation

Generated HTML files can be embedded in markdown:

```markdown
## Agent System Architecture

<iframe src="infographics/agent_architecture.html" width="100%" height="600px" frameborder="0"></iframe>
```

Or link directly:

```markdown
[View Interactive Agent Architecture](infographics/agent_architecture.html)
```

## Example Output Files

After running `demo_infographics.py`, you'll have:

```
outputs/infographics/
├── agent_architecture.html  (15KB)
├── model_comparison.html     (15KB)
├── prediction_analyzer.html  (19KB)
├── data_flow.html           (~15KB)
└── learning_path.html        (~15KB)
```

Open any file in your browser to see the interactive visualization!

## Next Steps

1. **Try the demo**: `python3 demo_infographics.py`
2. **Open in browser**: Navigate to `outputs/infographics/` and open any HTML file
3. **Customize**: Modify the example scripts with your own data
4. **Integrate**: Add components to your documentation or reports

For detailed API reference, see [`src/infographics/README.md`](src/infographics/README.md).

