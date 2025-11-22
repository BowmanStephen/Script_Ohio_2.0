#!/usr/bin/env python3
"""
Unit Tests for Interactive Infographics Components

Tests for component generation, HTML output, and data validation.

Author: Claude Code Assistant
Created: 2025-11-19
Version: 1.0
"""

import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any

from src.infographics import (
    AgentArchitectureVisualizer,
    ModelComparisonDashboard,
    PredictionConfidenceAnalyzer,
    DataFlowExplorer,
    LearningPathNavigator,
    get_component,
    validate_component_data,
    get_component_metadata
)
from src.infographics.utils import ensure_output_directory


class TestAgentArchitectureVisualizer:
    """Tests for AgentArchitectureVisualizer component"""
    
    def test_initialization(self):
        """Test component initialization"""
        visualizer = AgentArchitectureVisualizer(
            title="Test Title",
            description="Test Description",
            show_capabilities=True,
            interactive=True
        )
        assert visualizer.title == "Test Title"
        assert visualizer.description == "Test Description"
        assert visualizer.show_capabilities is True
        assert visualizer.interactive is True
    
    def test_generate_html_with_data(self):
        """Test HTML generation with provided data"""
        visualizer = AgentArchitectureVisualizer()
        data = {
            'agents': [
                {
                    'name': 'Test Agent',
                    'agent_type': 'test_agent',
                    'permission_level': 'READ_EXECUTE',
                    'capabilities': ['cap1', 'cap2']
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_agent_arch.html"
            html_path = visualizer.generate_html(data, output_path)
            
            assert html_path.exists()
            assert html_path.suffix == '.html'
            
            # Check HTML content
            html_content = html_path.read_text(encoding='utf-8')
            assert 'Test Agent' in html_content
            assert 'plotly' in html_content.lower()
    
    def test_generate_html_demo_mode(self):
        """Test HTML generation with demo data (empty data dict)"""
        visualizer = AgentArchitectureVisualizer()
        data = {}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_demo.html"
            html_path = visualizer.generate_html(data, output_path)
            
            assert html_path.exists()
            html_content = html_path.read_text(encoding='utf-8')
            assert 'plotly' in html_content.lower()


class TestModelComparisonDashboard:
    """Tests for ModelComparisonDashboard component"""
    
    def test_initialization(self):
        """Test component initialization"""
        dashboard = ModelComparisonDashboard(
            title="Model Comparison",
            interactive=True
        )
        assert dashboard.title == "Model Comparison"
        assert dashboard.interactive is True
    
    def test_generate_html_with_data(self):
        """Test HTML generation with model data"""
        dashboard = ModelComparisonDashboard()
        data = {
            'models': [
                {
                    'name': 'Ridge',
                    'metrics': {
                        'r2': 0.75,
                        'mae': 8.5,
                        'rmse': 12.3,
                        'accuracy': 0.72
                    }
                },
                {
                    'name': 'XGBoost',
                    'metrics': {
                        'r2': 0.82,
                        'mae': 7.2,
                        'rmse': 10.1,
                        'accuracy': 0.78
                    }
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_model_comparison.html"
            html_path = dashboard.generate_html(data, output_path)
            
            assert html_path.exists()
            html_content = html_path.read_text(encoding='utf-8')
            assert 'Ridge' in html_content or 'plotly' in html_content.lower()


class TestPredictionConfidenceAnalyzer:
    """Tests for PredictionConfidenceAnalyzer component"""
    
    def test_initialization(self):
        """Test component initialization"""
        analyzer = PredictionConfidenceAnalyzer(
            title="Prediction Analysis"
        )
        assert analyzer.title == "Prediction Analysis"
    
    def test_generate_html_with_data(self):
        """Test HTML generation with prediction data"""
        analyzer = PredictionConfidenceAnalyzer()
        data = {
            'predictions': [
                {
                    'away_team': 'Team A',
                    'home_team': 'Team B',
                    'spread': 3.5,
                    'confidence': 0.85,
                    'conference': 'Big Ten',
                    'week': 13
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_prediction.html"
            html_path = analyzer.generate_html(data, output_path)
            
            assert html_path.exists()
            html_content = html_path.read_text(encoding='utf-8')
            assert 'plotly' in html_content.lower()


class TestDataFlowExplorer:
    """Tests for DataFlowExplorer component"""
    
    def test_initialization(self):
        """Test component initialization"""
        explorer = DataFlowExplorer(title="Data Flow")
        assert explorer.title == "Data Flow"
    
    def test_generate_html_with_data(self):
        """Test HTML generation with pipeline data"""
        explorer = DataFlowExplorer()
        data = {
            'pipeline': [
                {'name': 'Step 1', 'type': 'input'},
                {'name': 'Step 2', 'type': 'transform'}
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_data_flow.html"
            html_path = explorer.generate_html(data, output_path)
            
            assert html_path.exists()
            html_content = html_path.read_text(encoding='utf-8')
            assert 'plotly' in html_content.lower()


class TestLearningPathNavigator:
    """Tests for LearningPathNavigator component"""
    
    def test_initialization(self):
        """Test component initialization"""
        navigator = LearningPathNavigator(title="Learning Path")
        assert navigator.title == "Learning Path"
    
    def test_generate_html_with_data(self):
        """Test HTML generation with notebook data"""
        navigator = LearningPathNavigator()
        data = {
            'notebooks': [
                {'name': 'Notebook 1', 'skill_level': 'beginner'},
                {'name': 'Notebook 2', 'skill_level': 'intermediate'}
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_learning_path.html"
            html_path = navigator.generate_html(data, output_path)
            
            assert html_path.exists()
            html_content = html_path.read_text(encoding='utf-8')
            assert 'plotly' in html_content.lower()


class TestUtilityFunctions:
    """Tests for utility functions"""
    
    def test_validate_component_data_success(self):
        """Test successful data validation"""
        data = {
            'agents': [
                {'name': 'Agent 1', 'type': 'test'}
            ]
        }
        result = validate_component_data(
            data,
            required_fields=['agents'],
            field_types={'agents': list}
        )
        assert result is True
    
    def test_validate_component_data_missing_field(self):
        """Test data validation with missing required field"""
        data = {}
        with pytest.raises(ValueError, match="Missing required fields"):
            validate_component_data(data, required_fields=['agents'])
    
    def test_validate_component_data_wrong_type(self):
        """Test data validation with wrong field type"""
        data = {'agents': 'not a list'}
        with pytest.raises(TypeError):
            validate_component_data(
                data,
                required_fields=['agents'],
                field_types={'agents': list}
            )
    
    def test_get_component(self):
        """Test getting component by type"""
        component_class = get_component('agent_architecture')
        assert component_class == AgentArchitectureVisualizer
        
        component_class = get_component('model_comparison')
        assert component_class == ModelComparisonDashboard
    
    def test_get_component_invalid_type(self):
        """Test getting component with invalid type"""
        with pytest.raises(ValueError):
            get_component('invalid_type')
    
    def test_get_component_metadata(self):
        """Test getting component metadata"""
        metadata = get_component_metadata('agent_architecture')
        assert metadata['name'] == 'Agent Architecture Visualizer'
        assert 'required_fields' in metadata
        assert 'estimated_time' in metadata
    
    def test_ensure_output_directory(self):
        """Test output directory creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with file path
            file_path = Path(tmpdir) / "subdir" / "file.html"
            result = ensure_output_directory(file_path)
            assert result.parent.exists()
            
            # Test with directory path
            dir_path = Path(tmpdir) / "newdir"
            result = ensure_output_directory(dir_path)
            assert result.exists()
            assert result.is_dir()


class TestIntegration:
    """Integration tests for HTML generation"""
    
    def test_full_workflow(self):
        """Test complete workflow from data to HTML"""
        visualizer = AgentArchitectureVisualizer()
        data = {
            'agents': [
                {
                    'name': 'Test Agent',
                    'agent_type': 'test',
                    'permission_level': 'READ_EXECUTE',
                    'capabilities': ['test_cap']
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "integration_test.html"
            html_path = visualizer.generate_html(data, output_path)
            
            # Verify file exists and is valid HTML
            assert html_path.exists()
            html_content = html_path.read_text(encoding='utf-8')
            
            # Check for essential HTML elements
            assert '<!DOCTYPE html>' in html_content
            assert '<html' in html_content
            assert '</html>' in html_content
            assert 'plotly' in html_content.lower()
            
            # Check for dark mode support
            assert 'prefers-color-scheme' in html_content or ':root' in html_content
    
    def test_all_components_demo_mode(self):
        """Test all components can generate HTML in demo mode"""
        components = [
            AgentArchitectureVisualizer(),
            ModelComparisonDashboard(),
            PredictionConfidenceAnalyzer(),
            DataFlowExplorer(),
            LearningPathNavigator()
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, component in enumerate(components):
                output_path = Path(tmpdir) / f"demo_{i}.html"
                html_path = component.generate_html({}, output_path)
                assert html_path.exists()
                assert html_path.suffix == '.html'

