#!/usr/bin/env python3
"""
Tool Loader - Dynamic Tool Loading and Management for Agents

This module provides dynamic loading and management of tools that agents
can use for various analytics tasks in the Script Ohio 2.0 platform.

Author: Claude Code Assistant
Created: 2025-11-07
Version: 1.0
"""

import os
import importlib.util
import inspect
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToolCategory(Enum):
    """Categories of tools for organization"""
    DATA_LOADING = "data_loading"
    MODEL_EXECUTION = "model_execution"
    VISUALIZATION = "visualization"
    ANALYSIS = "analysis"
    UTILITY = "utility"
    EXPORT = "export"

class ToolStatus(Enum):
    """Status of loaded tools"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"

@dataclass
class ToolMetadata:
    """Metadata for a loaded tool"""
    name: str
    description: str
    category: ToolCategory
    permission_required: int
    execution_time_estimate: float
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    dependencies: List[str]
    author: str
    version: str
    file_path: str

@dataclass
class ToolExecutionResult:
    """Result of tool execution"""
    success: bool
    result: Any
    error_message: Optional[str]
    execution_time: float
    metadata: Dict[str, Any]

class Tool:
    """
    Wrapper class for dynamically loaded tools
    """

    def __init__(self, metadata: ToolMetadata, tool_function: Callable):
        self.metadata = metadata
        self.tool_function = tool_function
        self.status = ToolStatus.ACTIVE
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_execution_time = None
        self.error_count = 0

        logger.info(f"Loaded tool: {metadata.name} ({metadata.category.value})")

    def execute(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the tool with given parameters

        Args:
            parameters: Tool execution parameters
            user_context: User context for permissions and optimization

        Returns:
            Tool execution result
        """
        start_time = time.time()
        self.status = ToolStatus.LOADING

        try:
            # Validate parameters against input schema
            self._validate_parameters(parameters)

            # Execute the tool function
            result = self.tool_function(parameters, user_context)

            # Update metrics
            execution_time = time.time() - start_time
            self._update_metrics(execution_time, success=True)

            self.status = ToolStatus.ACTIVE

            return ToolExecutionResult(
                success=True,
                result=result,
                error_message=None,
                execution_time=execution_time,
                metadata={
                    'tool_name': self.metadata.name,
                    'category': self.metadata.category.value,
                    'execution_count': self.execution_count
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_metrics(execution_time, success=False)

            error_message = f"Error executing tool {self.metadata.name}: {str(e)}"
            logger.error(error_message)

            self.status = ToolStatus.ERROR
            return ToolExecutionResult(
                success=False,
                result=None,
                error_message=error_message,
                execution_time=execution_time,
                metadata={'tool_name': self.metadata.name}
            )

    def _validate_parameters(self, parameters: Dict[str, Any]):
        """Validate parameters against input schema"""
        required_params = self.metadata.input_schema.get('required', [])

        # Check required parameters
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"Required parameter missing: {param}")

        # Type validation
        param_types = self.metadata.input_schema.get('properties', {})
        for param_name, param_value in parameters.items():
            if param_name in param_types:
                expected_type = param_types[param_name].get('type')
                if expected_type and not self._check_type(param_value, expected_type):
                    raise TypeError(f"Parameter {param_name} should be of type {expected_type}")

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict
        }

        expected_python_type = type_map.get(expected_type)
        return expected_python_type is None or isinstance(value, expected_python_type)

    def _update_metrics(self, execution_time: float, success: bool):
        """Update tool execution metrics"""
        self.execution_count += 1
        self.total_execution_time += execution_time
        self.last_execution_time = time.time()

        if not success:
            self.error_count += 1

    def get_status(self) -> Dict[str, Any]:
        """Get current tool status and metrics"""
        return {
            'name': self.metadata.name,
            'category': self.metadata.category.value,
            'status': self.status.value,
            'execution_count': self.execution_count,
            'average_execution_time': self.total_execution_time / max(1, self.execution_count),
            'error_rate': self.error_count / max(1, self.execution_count),
            'last_execution': self.last_execution_time
        }

class ToolLoader:
    """
    .. deprecated:: 2025-11-19
        ToolLoader is deprecated and will be removed in 30 days.
        Agents perform work directly without tool abstraction.
        Migration: Agents should perform work directly (see WeeklyAnalysisOrchestrator pattern).
    """
    """
    Dynamic tool loading and management system
    """

    def __init__(self, tools_directory: str = None, base_path: str = None):
        import warnings
        warnings.warn(
            "ToolLoader is deprecated and will be removed on 2025-12-19. "
            "Agents should perform work directly (see WeeklyAnalysisOrchestrator pattern).",
            DeprecationWarning,
            stacklevel=2
        )
        self.base_path = base_path or os.getcwd()
        self.tools_directory = tools_directory or os.path.join(self.base_path, "agents", "tools")
        self.tools: Dict[str, Tool] = {}
        self.tool_registry: Dict[str, ToolMetadata] = {}

        # Create tools directory if it doesn't exist
        Path(self.tools_directory).mkdir(parents=True, exist_ok=True)

        # Load built-in tools
        self._load_builtin_tools()

        # Load external tools
        self._load_external_tools()

        logger.info(f"Tool Loader initialized with {len(self.tools)} tools")

    def _load_builtin_tools(self):
        """Load built-in analytics tools"""

        # Data loading tools
        self._register_builtin_tool(
            name="load_notebook_metadata",
            description="Load metadata from Jupyter notebooks",
            category=ToolCategory.DATA_LOADING,
            permission_required=1,
            execution_time_estimate=1.0,
            input_schema={
                "type": "object",
                "properties": {
                    "notebook_paths": {"type": "array", "items": {"type": "string"}},
                    "include_content": {"type": "boolean", "default": False}
                },
                "required": ["notebook_paths"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "metadata": {"type": "array"},
                    "summary": {"type": "object"}
                }
            },
            function=self._load_notebook_metadata
        )

        self._register_builtin_tool(
            name="load_model_info",
            description="Load information about trained ML models",
            category=ToolCategory.DATA_LOADING,
            permission_required=2,
            execution_time_estimate=0.5,
            input_schema={
                "type": "object",
                "properties": {
                    "model_files": {"type": "array", "items": {"type": "string"}},
                    "include_metrics": {"type": "boolean", "default": True}
                },
                "required": ["model_files"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "models": {"type": "array"},
                    "total_models": {"type": "number"}
                }
            },
            function=self._load_model_info
        )

        # Model execution tools
        self._register_builtin_tool(
            name="predict_game_outcome",
            description="Predict game outcome using trained models",
            category=ToolCategory.MODEL_EXECUTION,
            permission_required=2,
            execution_time_estimate=2.0,
            input_schema={
                "type": "object",
                "properties": {
                    "home_team": {"type": "string"},
                    "away_team": {"type": "string"},
                    "model_type": {"type": "string", "enum": ["ridge", "xgboost", "fastai", "ensemble"]},
                    "features": {"type": "object"}
                },
                "required": ["home_team", "away_team"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "prediction": {"type": "object"},
                    "confidence": {"type": "number"},
                    "model_used": {"type": "string"}
                }
            },
            function=self._predict_game_outcome
        )

        # Visualization tools
        self._register_builtin_tool(
            name="create_learning_path_chart",
            description="Create visualization for learning paths",
            category=ToolCategory.VISUALIZATION,
            permission_required=1,
            execution_time_estimate=1.5,
            input_schema={
                "type": "object",
                "properties": {
                    "path_data": {"type": "array"},
                    "chart_type": {"type": "string", "enum": ["flowchart", "timeline", "progress"]},
                    "format": {"type": "string", "enum": ["json", "html", "png"], "default": "json"}
                },
                "required": ["path_data"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "chart_url": {"type": "string"},
                    "chart_data": {"type": "object"}
                }
            },
            function=self._create_learning_path_chart
        )

        # Analysis tools
        self._register_builtin_tool(
            name="analyze_feature_importance",
            description="Analyze feature importance using SHAP values",
            category=ToolCategory.ANALYSIS,
            permission_required=2,
            execution_time_estimate=3.0,
            input_schema={
                "type": "object",
                "properties": {
                    "model_path": {"type": "string"},
                    "feature_names": {"type": "array"},
                    "sample_data": {"type": "array"}
                },
                "required": ["model_path", "feature_names"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "importance_scores": {"type": "object"},
                    "summary_insights": {"type": "array"}
                }
            },
            function=self._analyze_feature_importance
        )

        # Export tools
        self._register_builtin_tool(
            name="export_analysis_results",
            description="Export analysis results to various formats",
            category=ToolCategory.EXPORT,
            permission_required=1,
            execution_time_estimate=1.0,
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "object"},
                    "format": {"type": "string", "enum": ["json", "csv", "pdf", "html"]},
                    "filename": {"type": "string"}
                },
                "required": ["data", "format"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "export_path": {"type": "string"},
                    "file_size": {"type": "number"},
                    "success": {"type": "boolean"}
                }
            },
            function=self._export_analysis_results
        )

        # TOON format conversion tool
        self._register_builtin_tool(
            name="convert_to_toon",
            description="Convert JSON data to TOON format for token optimization",
            category=ToolCategory.EXPORT,
            permission_required=1,
            execution_time_estimate=1.5,
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "object"},
                    "output_path": {"type": "string"},
                    "estimate_savings": {"type": "boolean", "default": False}
                },
                "required": ["data"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "toon_output": {"type": "string"},
                    "token_savings_percent": {"type": "number"},
                    "output_path": {"type": "string"},
                    "success": {"type": "boolean"},
                    "error": {"type": "string"}
                }
            },
            function=self._convert_to_toon
        )

    def _register_builtin_tool(self, name: str, description: str, category: ToolCategory,
                              permission_required: int, execution_time_estimate: float,
                              input_schema: Dict, output_schema: Dict, function: Callable):
        """Register a built-in tool"""
        metadata = ToolMetadata(
            name=name,
            description=description,
            category=category,
            permission_required=permission_required,
            execution_time_estimate=execution_time_estimate,
            input_schema=input_schema,
            output_schema=output_schema,
            dependencies=[],
            author="System",
            version="1.0",
            file_path="builtin"
        )

        tool = Tool(metadata, function)
        self.tools[name] = tool
        self.tool_registry[name] = metadata

    def _load_external_tools(self):
        """Load external tools from the tools directory"""
        tools_path = Path(self.tools_directory)

        if not tools_path.exists():
            return

        for tool_file in tools_path.glob("*.py"):
            if tool_file.name.startswith("__"):
                continue

            try:
                self._load_tool_from_file(tool_file)
            except Exception as e:
                logger.error(f"Error loading tool from {tool_file}: {str(e)}")

    def _load_tool_from_file(self, tool_file: Path):
        """Load a tool from a Python file"""
        spec = importlib.util.spec_from_file_location(tool_file.stem, tool_file)
        module = importlib.util.module_from_spec(spec)

        # Execute the module
        spec.loader.exec_module(module)

        # Look for tool registration functions
        if hasattr(module, 'register_tool'):
            tool_data = module.register_tool()

            metadata = ToolMetadata(
                name=tool_data['name'],
                description=tool_data['description'],
                category=ToolCategory(tool_data['category']),
                permission_required=tool_data['permission_required'],
                execution_time_estimate=tool_data['execution_time_estimate'],
                input_schema=tool_data['input_schema'],
                output_schema=tool_data['output_schema'],
                dependencies=tool_data.get('dependencies', []),
                author=tool_data.get('author', 'External'),
                version=tool_data.get('version', '1.0'),
                file_path=str(tool_file)
            )

            tool = Tool(metadata, tool_data['function'])
            self.tools[metadata.name] = tool
            self.tool_registry[metadata.name] = metadata

            logger.info(f"Loaded external tool: {metadata.name}")

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(tool_name)

    def list_tools(self, category: ToolCategory = None) -> List[Dict[str, Any]]:
        """List available tools, optionally filtered by category"""
        tools_list = []

        for tool in self.tools.values():
            if category is None or tool.metadata.category == category:
                tools_list.append({
                    'name': tool.metadata.name,
                    'description': tool.metadata.description,
                    'category': tool.metadata.category.value,
                    'permission_required': tool.metadata.permission_required,
                    'execution_time_estimate': tool.metadata.execution_time_estimate,
                    'status': tool.status.value
                })

        return sorted(tools_list, key=lambda x: x['name'])

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any],
                    user_context: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool by name"""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolExecutionResult(
                success=False,
                result=None,
                error_message=f"Tool not found: {tool_name}",
                execution_time=0.0,
                metadata={'tool_name': tool_name}
            )

        return tool.execute(parameters, user_context)

    def get_tools_for_permission_level(self, permission_level: int) -> List[str]:
        """Get list of tools available for a permission level"""
        available_tools = []

        for tool_name, tool in self.tools.items():
            if tool.metadata.permission_required <= permission_level:
                available_tools.append(tool_name)

        return available_tools

    def get_tool_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report for all tools"""
        total_tools = len(self.tools)
        active_tools = len([t for t in self.tools.values() if t.status == ToolStatus.ACTIVE])
        error_tools = len([t for t in self.tools.values() if t.status == ToolStatus.ERROR])

        category_counts = {}
        total_executions = 0
        total_execution_time = 0.0

        for tool in self.tools.values():
            category = tool.metadata.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            total_executions += tool.execution_count
            total_execution_time += tool.total_execution_time

        return {
            'total_tools': total_tools,
            'active_tools': active_tools,
            'error_tools': error_tools,
            'categories': category_counts,
            'total_executions': total_executions,
            'average_execution_time': total_execution_time / max(1, total_executions),
            'tools_by_status': {
                'active': [t.get_status() for t in self.tools.values() if t.status == ToolStatus.ACTIVE],
                'error': [t.get_status() for t in self.tools.values() if t.status == ToolStatus.ERROR]
            }
        }

    # Built-in tool implementations
    def _load_notebook_metadata(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Load metadata from Jupyter notebooks"""
        notebook_paths = parameters.get('notebook_paths', [])
        include_content = parameters.get('include_content', False)

        metadata_list = []

        for notebook_path in notebook_paths:
            full_path = Path(self.base_path) / notebook_path

            if full_path.exists():
                metadata = {
                    'path': notebook_path,
                    'name': full_path.stem,
                    'exists': True,
                    'size_bytes': full_path.stat().st_size if full_path.is_file() else 0,
                    'last_modified': full_path.stat().st_mtime if full_path.is_file() else None
                }

                if include_content:
                    # Could load and parse notebook content here
                    metadata['cell_count'] = 0  # Would parse actual notebook
                    metadata['has_code'] = True
                    metadata['has_markdown'] = True

                metadata_list.append(metadata)
            else:
                metadata_list.append({
                    'path': notebook_path,
                    'name': Path(notebook_path).stem,
                    'exists': False
                })

        return {
            'metadata': metadata_list,
            'summary': {
                'total_notebooks': len(metadata_list),
                'existing_notebooks': len([m for m in metadata_list if m.get('exists', False)]),
                'total_size_bytes': sum(m.get('size_bytes', 0) for m in metadata_list)
            }
        }

    def _load_model_info(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Load information about trained ML models"""
        model_files = parameters.get('model_files', [])
        include_metrics = parameters.get('include_metrics', True)

        model_info = []
        model_pack_path = Path(self.base_path) / "model_pack"

        for model_file in model_files:
            full_path = model_pack_path / model_file

            if full_path.exists():
                info = {
                    'file': model_file,
                    'name': model_file.replace('.joblib', '').replace('.pkl', ''),
                    'exists': True,
                    'size_bytes': full_path.stat().st_size,
                    'type': 'regression' if 'ridge' in model_file else 'classification'
                }

                if include_metrics:
                    # Would load actual model metrics here
                    info['metrics'] = {
                        'accuracy': 0.85,  # Placeholder
                        'features_count': 86,
                        'training_date': '2025-11-01'
                    }

                model_info.append(info)
            else:
                model_info.append({
                    'file': model_file,
                    'name': model_file.replace('.joblib', '').replace('.pkl', ''),
                    'exists': False
                })

        return {
            'models': model_info,
            'total_models': len(model_info),
            'existing_models': len([m for m in model_info if m.get('exists', False)])
        }

    def _predict_game_outcome(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict game outcome using trained models"""
        home_team = parameters.get('home_team')
        away_team = parameters.get('away_team')
        model_type = parameters.get('model_type', 'ensemble')

        # This would integrate with actual ML models
        # For now, return a mock prediction

        prediction = {
            'home_team': home_team,
            'away_team': away_team,
            'predicted_margin': 7.5,
            'predicted_winner': home_team,
            'confidence': 0.72,
            'probability': {
                'home_win': 0.72,
                'away_win': 0.28
            }
        }

        return {
            'prediction': prediction,
            'confidence': prediction['confidence'],
            'model_used': model_type,
            'features_used': ['team_strength', 'recent_performance', 'home_field_advantage']
        }

    def _create_learning_path_chart(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create visualization for learning paths"""
        path_data = parameters.get('path_data', [])
        chart_type = parameters.get('chart_type', 'flowchart')
        format_type = parameters.get('format', 'json')

        # Generate mock chart data
        chart_data = {
            'type': chart_type,
            'nodes': path_data,
            'edges': [],
            'layout': 'hierarchical'
        }

        # Create edges (connections between nodes)
        for i in range(len(path_data) - 1):
            chart_data['edges'].append({
                'from': path_data[i],
                'to': path_data[i + 1]
            })

        return {
            'chart_data': chart_data,
            'chart_url': f'/charts/{hash(str(path_data))}',  # Mock URL
            'format': format_type
        }

    def _analyze_feature_importance(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feature importance using SHAP values"""
        model_path = parameters.get('model_path')
        feature_names = parameters.get('feature_names', [])

        # Mock SHAP analysis results
        importance_scores = {
            feature_name: hash(feature_name) % 100 / 100
            for feature_name in feature_names[:10]  # Limit to top 10
        }

        # Sort by importance
        sorted_features = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)

        insights = [
            f"Most important feature: {sorted_features[0][0]} ({sorted_features[0][1]:.3f})",
            f"Top 3 features account for {sum(score for _, score in sorted_features[:3]):.1%} of predictive power",
            f"Consider feature engineering for lower-importance variables"
        ]

        return {
            'importance_scores': dict(sorted_features),
            'summary_insights': insights,
            'total_features_analyzed': len(feature_names)
        }

    def _export_analysis_results(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Export analysis results to various formats"""
        data = parameters.get('data', {})
        format_type = parameters.get('format', 'json')
        filename = parameters.get('filename', f'analysis_export.{format_type}')

        export_path = Path(self.base_path) / 'exports' / filename
        export_path.parent.mkdir(exist_ok=True)

        try:
            if format_type == 'json':
                with open(export_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            elif format_type == 'csv':
                # Simplified CSV export
                import pandas as pd
                if isinstance(data, dict):
                    df = pd.DataFrame([data])
                else:
                    df = pd.DataFrame(data)
                df.to_csv(export_path, index=False)

            file_size = export_path.stat().st_size if export_path.exists() else 0

            return {
                'export_path': str(export_path),
                'file_size': file_size,
                'success': True,
                'format': format_type
            }

        except Exception as e:
            return {
                'export_path': str(export_path),
                'file_size': 0,
                'success': False,
                'error': str(e),
                'format': format_type
            }

    def _convert_to_toon(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON data to TOON format for token optimization"""
        try:
            # Import TOON format module
            import sys
            from pathlib import Path
            project_root = Path(self.base_path).resolve()
            if str(project_root / "src") not in sys.path:
                sys.path.insert(0, str(project_root / "src"))
            
            from toon_format import encode, estimate_token_savings
            
            data = parameters.get('data', {})
            output_path = parameters.get('output_path')
            estimate_savings = parameters.get('estimate_savings', False)
            
            # Encode to TOON
            toon_output = encode(data)
            
            # Estimate token savings if requested
            token_savings = 0.0
            if estimate_savings:
                savings_data = estimate_token_savings(data, toon_output)
                token_savings = savings_data.get('token_savings_percent', 0.0)
            
            # Write to file if output_path provided
            if output_path:
                output_file = Path(self.base_path) / output_path
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(toon_output)
                logger.info(f"TOON output written to {output_file}")
            
            return {
                'toon_output': toon_output,
                'token_savings_percent': token_savings,
                'output_path': str(output_path) if output_path else None,
                'success': True
            }
            
        except ImportError as e:
            logger.error(f"TOON format module not available: {e}")
            return {
                'toon_output': '',
                'token_savings_percent': 0.0,
                'output_path': None,
                'success': False,
                'error': f"TOON format module not available: {str(e)}. Install with: npm install -g @toon-format/cli"
            }
        except Exception as e:
            logger.error(f"Error converting to TOON: {e}")
            return {
                'toon_output': '',
                'token_savings_percent': 0.0,
                'output_path': None,
                'success': False,
                'error': str(e)
            }

# Example usage
if __name__ == "__main__":
    # Initialize tool loader
    tool_loader = ToolLoader()

    # List all tools
    print("=== Available Tools ===")
    tools = tool_loader.list_tools()
    for tool in tools:
        print(f"- {tool['name']}: {tool['description']} ({tool['category']})")

    # Execute a tool
    print("\n=== Tool Execution Example ===")

    # Load notebook metadata
    result = tool_loader.execute_tool(
        "load_notebook_metadata",
        {
            "notebook_paths": [
                "starter_pack/01_intro_to_data.ipynb",
                "model_pack/03_xgboost_win_probability.ipynb"
            ],
            "include_content": False
        },
        {"role": "analyst"}
    )

    print(f"Tool execution result: {result.success}")
    if result.success:
        print(f"Found {result.result['summary']['total_notebooks']} notebooks")
    else:
        print(f"Error: {result.error_message}")

    # Get status report
    print("\n=== Tool Status Report ===")
    status = tool_loader.get_tool_status_report()
    print(f"Total tools: {status['total_tools']}")
    print(f"Active tools: {status['active_tools']}")
    print(f"Categories: {status['categories']}")