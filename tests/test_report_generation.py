"""
Test report generation.
"""
import pytest
import sys
from pathlib import Path
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from agents.report_generator_agent import ReportGeneratorAgent

def test_report_generation():
    """Test report generator agent."""
    week = 99  # Test week
    agent = ReportGeneratorAgent(week=week)
    
    # Clean up before
    if agent.output_dir.exists():
        shutil.rmtree(agent.output_dir)
    agent.output_dir.mkdir(parents=True, exist_ok=True)
    
    result = agent.execute_task({})
    
    assert result['status'] == 'success'
    assert 'generated_files' in result
    
    # Check file existence
    report_file = agent.output_dir / f"week{week}_comprehensive_report.html"
    assert report_file.exists()
    assert report_file.stat().st_size > 0
    
    # Cleanup
    shutil.rmtree(agent.output_dir)

