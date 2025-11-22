# Interactive Infographics Module

A reusable Python component library that generates standalone interactive HTML infographics using Plotly. These components enhance markdown documentation and generated reports with interactive visualizations that improve comprehension without requiring a build step.

## Quick Start

```python
from src.infographics import AgentArchitectureVisualizer

# Create visualizer
visualizer = AgentArchitectureVisualizer(
    title="Agent System Architecture",
    description="Interactive visualization of the multi-agent system"
)

# Generate HTML
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

html_path = visualizer.generate_html(data, "outputs/infographics/agent_arch.html")
```

## Component Catalog

### 1. AgentArchitectureVisualizer

Interactive flowchart of agent system architecture.

**Features:**
- Interactive network graph showing agent relationships
- Click-to-expand agent details (capabilities, permissions)
- Filter by permission level (READ_ONLY, READ_EXECUTE, etc.)
- Hover tooltips with agent metadata

**Usage:**
```python
from src.infographics import AgentArchitectureVisualizer

visualizer = AgentArchitectureVisualizer(
    title="Agent System Architecture",
    show_capabilities=True,
    interactive=True
)

data = {
    'agents': [
        {
            'name': 'Agent Name',
            'agent_type': 'agent_type',
            'permission_level': 'READ_EXECUTE',
            'capabilities': ['cap1', 'cap2']
        }
    ]
}

html_path = visualizer.generate_html(data, "outputs/agent_arch.html")
```

### 2. ModelComparisonDashboard

Side-by-side model performance comparison dashboard.

**Features:**
- Side-by-side comparison of Ridge/XGBoost/FastAI models
- Interactive slider for feature importance exploration
- Toggle between metrics (R², MAE, RMSE, accuracy)
- Performance timeline if historical data available

**Usage:**
```python
from src.infographics import ModelComparisonDashboard

dashboard = ModelComparisonDashboard(
    title="Model Performance Comparison"
)

data = {
    'models': [
        {
            'name': 'Ridge Regression',
            'metrics': {
                'r2': 0.75,
                'mae': 8.5,
                'rmse': 12.3,
                'accuracy': 0.72
            }
        }
        # ... more models
    ]
}

html_path = dashboard.generate_html(data, "outputs/model_comparison.html")
```

### 3. PredictionConfidenceAnalyzer

Interactive scatter plot analyzer for prediction confidence.

**Features:**
- Interactive scatter plot: spread vs confidence
- Filter controls (conference, team, week)
- Upset probability calculator (slider for threshold)
- Hover details showing game info and prediction breakdown

**Usage:**
```python
from src.infographics import PredictionConfidenceAnalyzer

analyzer = PredictionConfidenceAnalyzer(
    title="Prediction Confidence Analysis"
)

data = {
    'predictions': [
        {
            'away_team': 'Ohio State',
            'home_team': 'Michigan',
            'spread': 3.5,
            'confidence': 0.85,
            'conference': 'Big Ten',
            'week': 13
        }
        # ... more predictions
    ]
}

html_path = analyzer.generate_html(data, "outputs/prediction_analyzer.html")
```

### 4. DataFlowExplorer

Interactive pipeline diagram showing data transformations.

**Features:**
- Interactive pipeline diagram showing data transformations
- Hover reveals feature engineering steps
- Week-by-week progression slider
- Click nodes to see data samples

**Usage:**
```python
from src.infographics import DataFlowExplorer

explorer = DataFlowExplorer(
    title="Data Processing Pipeline"
)

data = {
    'pipeline': [
        {'name': 'Data Ingestion', 'type': 'input'},
        {'name': 'Feature Engineering', 'type': 'transform'},
        {'name': 'Model Prediction', 'type': 'process'},
        {'name': 'Output Generation', 'type': 'output'}
    ]
}

html_path = explorer.generate_html(data, "outputs/data_flow.html")
```

### 5. LearningPathNavigator

Interactive notebook progression guide.

**Features:**
- Interactive notebook progression tree
- Skill level indicators (beginner/intermediate/advanced)
- Prerequisite dependencies visualization
- Click to view notebook objectives

**Usage:**
```python
from src.infographics import LearningPathNavigator

navigator = LearningPathNavigator(
    title="Learning Path Navigator"
)

data = {
    'notebooks': [
        {
            'name': 'Data Dictionary',
            'skill_level': 'beginner'
        }
        # ... more notebooks
    ]
}

html_path = navigator.generate_html(data, "outputs/learning_path.html")
```

## API Reference

### BaseComponent

Base class for all infographic components.

**Methods:**
- `generate_html(data: Dict[str, Any], output_path: Union[str, Path]) -> Path`
  - Generate standalone HTML file from component data

### Component Classes

All components inherit from `BaseComponent` and implement:
- `__init__(title: str, description: Optional[str], interactive: bool)`
- `generate_html(data: Dict[str, Any], output_path: Union[str, Path]) -> Path`

### Utility Functions

- `get_component(component_type: str)` - Get component class by type name
- `validate_component_data(data: Dict, required_fields: List[str])` - Validate data structure
- `generate_standalone_html(figure: go.Figure, output_path: Path, ...)` - Generate HTML from Plotly figure
- `sample_data(data: List[Any], max_samples: int)` - Sample large datasets for performance

## Integration Patterns

### 1. Embedding in Markdown Documentation

Generate the component and embed via iframe:

```markdown
## Agent System Architecture

<iframe src="infographics/agent_architecture.html" width="100%" height="600px" frameborder="0"></iframe>
```

### 2. Using CLI Tool

```bash
# Generate agent architecture with demo data
python scripts/generate_infographics.py --component agent_architecture --output docs/infographics/

# Generate model comparison from JSON file
python scripts/generate_infographics.py --component model_comparison --data model_pack/models.json --output outputs/

# Generate with custom title
python scripts/generate_infographics.py --component prediction_analyzer --output outputs/ --title "Week 13 Predictions"
```

### 3. Agent Integration

Use via InsightGeneratorAgent:

```python
from agents.insight_generator_agent import InsightGeneratorAgent

agent = InsightGeneratorAgent(agent_id="insight_001")

result = agent._execute_action(
    "generate_infographic",
    {
        "component_type": "agent_architecture",
        "data": {"agents": [...]},
        "output_path": "outputs/infographics/",
        "title": "Custom Title"
    },
    {"user_id": "user_001"}
)

print(result["html_path"])  # Path to generated HTML
```

### 4. Programmatic Usage

```python
from src.infographics import get_component
from pathlib import Path

# Get component by type
component_class = get_component("model_comparison")

# Create instance
component = component_class(title="Model Comparison")

# Generate HTML
data = {"models": [...]}
html_path = component.generate_html(data, Path("outputs/model_comparison.html"))
```

## Examples

See `src/infographics/examples/` for complete working examples:

- `agent_architecture_demo.py` - Agent architecture visualization
- `model_comparison_demo.py` - Model comparison dashboard
- `prediction_analyzer_demo.py` - Prediction confidence analyzer

Run examples:
```bash
python src/infographics/examples/agent_architecture_demo.py
```

## Technical Details

### HTML Output Format

- Standalone HTML files (no external dependencies except Plotly.js CDN)
- Embedded CSS with dark mode support (`prefers-color-scheme: dark`)
- Vanilla JavaScript for interactions (no framework dependencies)
- Responsive design (mobile-first, max-width containers)
- Accessibility: ARIA labels, keyboard navigation, screen reader support

### Performance Considerations

- Large datasets (>1000 items) are automatically sampled
- Efficient Plotly figure generation
- Lazy loading for large visualizations
- HTML file size optimization

### Dependencies

- `plotly>=5.17.0` (already in requirements.txt)
- Standard library: `json`, `pathlib`, `typing`, `logging`

## Troubleshooting

### Component Not Found

If you get `Component type 'X' not available`, ensure:
1. Component class is imported in `src/infographics/__init__.py`
2. Component is registered in `get_component()` function

### Data Validation Errors

If data validation fails:
1. Check required fields using `get_component_metadata(component_type)`
2. Ensure data structure matches component requirements
3. Use demo mode (empty data dict) to test component

### HTML Generation Fails

If HTML generation fails:
1. Check output directory permissions
2. Ensure Plotly is installed: `pip install plotly>=5.17.0`
3. Check logs for detailed error messages

## Future Enhancements

- Real-time data updates (WebSocket integration)
- Export to PNG/SVG/PDF
- Custom theme builder
- Component composition (combine multiple components)
- Interactive data editing

## License

Part of Script Ohio 2.0 project.

