#!/usr/bin/env python3
"""
Notebook Analyzer Agent
Analyzes all 12 Jupyter notebooks in the starter pack to extract insights
"""

import json
import os
import nbformat
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

class NotebookAnalyzerAgent:
    """
    Agent responsible for analyzing all Jupyter notebooks in starter pack
    """
    
    def __init__(self):
        self.notebook_path = Path("starter_pack")
        self.notebooks = [
            "00_data_dictionary.ipynb",
            "01_intro_to_data.ipynb",
            "02_build_simple_rankings.ipynb",
            "03_metrics_comparison.ipynb",
            "04_team_similarity.ipynb",
            "05_matchup_predictor.ipynb",
            "06_custom_rankings_by_metric.ipynb",
            "07_drive_efficiency.ipynb",
            "08_offense_vs_defense_comparison.ipynb",
            "09_opponent_adjustments.ipynb",
            "10_srs_adjusted_metrics.ipynb",
            "11_metric_distribution_explorer.ipynb",
            "12_efficiency_dashboards.ipynb"
        ]
        
    def analyze_all_notebooks(self) -> Dict[str, Any]:
        """
        Analyze all 12 notebooks and extract key insights
        """
        print("📓 Analyzing all Jupyter notebooks...")
        
        results = {
            "total_notebooks": len(self.notebooks),
            "analyzed_notebooks": [],
            "errors": [],
            "global_insights": [],
            "data_metrics": {},
            "team_rankings": {},
            "prediction_models": {}
        }
        
        for notebook_file in self.notebooks:
            try:
                result = self._analyze_single_notebook(notebook_file)
                results["analyzed_notebooks"].append(notebook_file)
                results["global_insights"].extend(result["insights"])
                
                # Aggregate results
                if "team_rankings" in result:
                    results["team_rankings"].update(result["team_rankings"])
                if "prediction_models" in result:
                    results["prediction_models"].update(result["prediction_models"])
                if "data_metrics" in result:
                    results["data_metrics"].update(result["data_metrics"])
                    
                print(f"✅ Analyzed: {notebook_file}")
                
            except Exception as e:
                error_msg = f"Failed to analyze {notebook_file}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
        
        return results
    
    def _analyze_single_notebook(self, notebook_file: str) -> Dict[str, Any]:
        """
        Analyze a single notebook and extract insights
        """
        result = {
            "notebook": notebook_file,
            "insights": [],
            "data_metrics": {},
            "team_rankings": {},
            "prediction_models": {}
        }
        
        notebook_path = self.notebook_path / notebook_file
        if not notebook_path.exists():
            raise FileNotFoundError(f"Notebook not found: {notebook_path}")
        
        # Read the notebook
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)
        
        # Extract insights from notebook cells
        for cell in notebook.cells:
            if cell.cell_type == 'markdown':
                insights = self._extract_markdown_insights(cell.source)
                result["insights"].extend(insights)
            elif cell.cell_type == 'code':
                # Look for dataframes and visualizations
                code_data = cell.source
                extracted_data = self._extract_code_insights(code_data)
                result["data_metrics"].update(extracted_data["metrics"])
                result["team_rankings"].update(extracted_data["rankings"])
                result["prediction_models"].update(extracted_data["models"])
        
        return result
    
    def _extract_markdown_insights(self, markdown_content: str) -> List[str]:
        """
        Extract insights from markdown cells
        """
        insights = []
        
        # Look for key insights patterns
        if "🔥" in markdown_content:
            insights.append("Key performance highlight found")
        if "📈" in markdown_content:
            insights.append("Growth trend identified")
        if "⚠️" in markdown_content:
            insights.append("Warning or cautionary note")
        if "💡" in markdown_content:
            insights.append("Strategic insight identified")
        if "🏆" in markdown_content:
            insights.append("Championship-level analysis")
        if "🎯" in markdown_content:
            insights.append("Performance metric focus")
        
        # Look for specific patterns
        if "top 5" in markdown_content.lower():
            insights.append("Top 5 ranking analysis")
        if "underdog" in markdown_content.lower():
            insights.append("Underdog potential identified")
        if "upset" in markdown_content.lower():
            insights.append("Upset possibility detected")
        
        return insights
    
    def _extract_code_insights(self, code_content: str) -> Dict[str, Any]:
        """
        Extract insights from code cells
        """
        result = {
            "metrics": {},
            "rankings": {},
            "models": {}
        }
        
        # Look for dataframe creation and analysis
        if "DataFrame" in code_content or "pd.read" in code_content:
            result["metrics"]["data_operation"] = True
            
            # Look for ranking operations
            if ".rank" in code_content:
                result["rankings"]["ranking_computed"] = True
                if "desc" in code_content:
                    result["rankings"]["direction"] = "descending"
        
        # Look for model operations
        if "model" in code_content.lower() or "fit" in code_content:
            result["models"]["model_operation"] = True
            
            if "predict" in code_content.lower():
                result["models"]["prediction_generated"] = True
        
        # Look for statistical operations
        if ".mean" in code_content or ".sum" in code_content or ".std" in code_content:
            result["metrics"]["statistical_analysis"] = True
        
        return result

if __name__ == "__main__":
    agent = NotebookAnalyzerAgent()
    result = agent.analyze_all_notebooks()
    print(json.dumps(result, indent=2))
