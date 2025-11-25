#!/usr/bin/env python3
"""
Extract Week 14 Analysis Components
Extracts matchup analysis and model validation from comprehensive analysis
"""

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent

def main():
    """Extract analysis components"""
    print("📋 Extracting Week 14 Analysis Components...")
    print("=" * 60)
    
    analysis_dir = PROJECT_ROOT / "analysis" / "week14"
    validation_dir = PROJECT_ROOT / "validation" / "week14"
    
    # Load comprehensive analysis
    comprehensive_path = analysis_dir / "week14_comprehensive_analysis.json"
    if not comprehensive_path.exists():
        print(f"❌ Comprehensive analysis not found: {comprehensive_path}")
        return 1
    
    with open(comprehensive_path) as f:
        comprehensive = json.load(f)
    
    print(f"✅ Loaded comprehensive analysis")
    
    # Extract matchup analysis
    matchup_analysis = {
        'metadata': comprehensive.get('analysis_metadata', {}),
        'team_rankings': comprehensive.get('team_rankings', []),
        'head_to_head': comprehensive.get('detailed_analysis', {}).get('head_to_head', {}),
        'team_strengths': comprehensive.get('detailed_analysis', {}).get('team_strengths', {}),
        'matchup_insights': comprehensive.get('detailed_analysis', {}).get('matchup_insights', []),
        'situational_factors': comprehensive.get('detailed_analysis', {}).get('situational_factors', {}),
        'advanced_stats': comprehensive.get('detailed_analysis', {}).get('advanced_stats', {})
    }
    
    matchup_path = analysis_dir / "week14_matchup_analysis.json"
    with open(matchup_path, 'w') as f:
        json.dump(matchup_analysis, f, indent=2, default=str)
    print(f"✅ Saved matchup analysis: {matchup_path}")
    
    # Check for validation report
    validation_dir.mkdir(parents=True, exist_ok=True)
    validation_report_path = validation_dir / "week14_model_validation_report.json"
    
    if validation_report_path.exists():
        with open(validation_report_path) as f:
            validation_report = json.load(f)
        
        # Create simplified model validation JSON for analysis directory
        model_validation = {
            'week': 14,
            'season': 2025,
            'validation_summary': validation_report.get('summary', {}),
            'models_validated': validation_report.get('detailed_results', {}).get('model_validation', {}),
            'data_quality': validation_report.get('detailed_results', {}).get('data_validation', {}),
            'overall_status': validation_report.get('summary', {}).get('overall_validation_passed', False)
        }
        
        validation_path = analysis_dir / "week14_model_validation.json"
        with open(validation_path, 'w') as f:
            json.dump(model_validation, f, indent=2, default=str)
        print(f"✅ Saved model validation: {validation_path}")
    else:
        print(f"⚠️  Validation report not found: {validation_report_path}")
        # Create placeholder
        model_validation = {
            'week': 14,
            'season': 2025,
            'status': 'pending',
            'note': 'Validation report not found in validation/week14/'
        }
        validation_path = analysis_dir / "week14_model_validation.json"
        with open(validation_path, 'w') as f:
            json.dump(model_validation, f, indent=2)
        print(f"   Created placeholder: {validation_path}")
    
    print("\n" + "=" * 60)
    print("✅ Week 14 Analysis Components Extracted Successfully!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

