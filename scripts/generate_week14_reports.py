#!/usr/bin/env python3
"""
Generate Week 14 Reports
Creates intelligence consolidation JSON and master markdown report
"""

import pandas as pd
import json
from pathlib import Path
import sys
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent

def generate_intelligence_consolidation():
    """Generate intelligence consolidation JSON"""
    print("📋 Generating Intelligence Consolidation...")
    
    analysis_dir = PROJECT_ROOT / "analysis" / "week14"
    predictions_dir = PROJECT_ROOT / "predictions" / "week14"
    
    consolidation = {
        'consolidation_metadata': {
            'timestamp': datetime.now().isoformat(),
            'week': 14,
            'season': 2025,
            'agent_id': 'week14_consolidation',
            'total_processing_time': 0.0
        },
        'asset_discovery': {
            'discovered_assets': []
        },
        'quality_validation': {},
        'asset_organization': {},
        'executive_summary': {}
    }
    
    # Discover assets
    assets = []
    
    # Analysis assets
    analysis_files = [
        'week14_comprehensive_analysis.json',
        'week14_matchup_analysis.json',
        'week14_model_validation.json',
        'week14_power_rankings.csv',
        'week14_strategic_recommendations.csv',
        'week14_upset_alerts.csv',
        'week14_narrative_previews.md',
        'week14_comprehensive_report.html'
    ]
    
    for filename in analysis_files:
        file_path = analysis_dir / filename
        if file_path.exists():
            stat = file_path.stat()
            assets.append({
                'file_path': str(file_path.relative_to(PROJECT_ROOT)),
                'asset_type': 'analysis',
                'file_size': stat.st_size,
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'description': f'Week 14 {filename.replace("week14_", "").replace(".json", "").replace(".csv", "").replace(".md", "").replace(".html", "")}',
                'quality_score': 0.9
            })
    
    # Prediction assets
    prediction_files = [
        'week14_model_predictions.json',
        'week14_model_predictions.csv',
        'week14_predictions_unified.json',
        'week14_predictions_unified.csv',
        'week14_ats_full_table.csv',
        'week14_summary.json',
        'prediction_insights.json',
        'week14_recommendations.csv',
        'week14_comprehensive_predictions.csv',
        'week14_enhanced_analysis_report.json',
        'week14_enhanced_analysis.md'
    ]
    
    for filename in prediction_files:
        file_path = predictions_dir / filename
        if file_path.exists():
            stat = file_path.stat()
            assets.append({
                'file_path': str(file_path.relative_to(PROJECT_ROOT)),
                'asset_type': 'predictions',
                'file_size': stat.st_size,
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'description': f'Week 14 {filename.replace("week14_", "").replace(".json", "").replace(".csv", "").replace(".md", "")}',
                'quality_score': 0.9
            })
    
    consolidation['asset_discovery']['discovered_assets'] = assets
    
    # Executive summary
    if (predictions_dir / "week14_summary.json").exists():
        with open(predictions_dir / "week14_summary.json") as f:
            summary = json.load(f)
        
        consolidation['executive_summary'] = {
            'total_games': summary.get('total_games', 0),
            'high_confidence_games': summary.get('high_confidence_games', 0),
            'moderate_confidence_games': summary.get('moderate_confidence_games', 0),
            'low_confidence_games': summary.get('low_confidence_games', 0),
            'key_insights': summary.get('key_insights', [])
        }
    
    return consolidation

def generate_master_report():
    """Generate master markdown report"""
    print("📄 Generating Master Report...")
    
    predictions_dir = PROJECT_ROOT / "predictions" / "week14"
    analysis_dir = PROJECT_ROOT / "analysis" / "week14"
    
    # Load summary
    summary = {}
    if (predictions_dir / "week14_summary.json").exists():
        with open(predictions_dir / "week14_summary.json") as f:
            summary = json.load(f)
    
    # Load insights
    insights = {}
    if (predictions_dir / "prediction_insights.json").exists():
        with open(predictions_dir / "prediction_insights.json") as f:
            insights = json.load(f)
    
    # Generate markdown
    md = f"""# Week 14 Master Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

### Overview
- **Total Games**: {summary.get('total_games', 0)}
- **High Confidence Games**: {summary.get('high_confidence_games', 0)}
- **Moderate Confidence Games**: {summary.get('moderate_confidence_games', 0)}
- **Low Confidence Games**: {summary.get('low_confidence_games', 0)}

### Key Insights

"""
    
    for insight in summary.get('key_insights', []):
        md += f"- {insight}\n"
    
    md += f"""
## Prediction Patterns

"""
    if insights:
        patterns = insights.get('prediction_patterns', {})
        md += f"""
- **Home Win Rate**: {patterns.get('home_win_rate', 0):.1%}
- **Upset Rate**: {patterns.get('upset_rate', 0):.1%}
- **Close Game Rate**: {patterns.get('close_game_rate', 0):.1%}
- **Blowout Rate**: {patterns.get('blowout_rate', 0):.1%}
- **Average Confidence**: {insights.get('average_confidence', 0):.1%}

"""
    
    md += f"""
## Top Value Games

"""
    for i, game in enumerate(summary.get('top_value_games', [])[:10], 1):
        md += f"""
### {i}. {game.get('matchup', 'Unknown')}

- **Spread**: {game.get('spread', 0):.1f}
- **Predicted Margin**: {game.get('predicted_margin', 0):.1f}
- **Line Value**: {game.get('line_value', 0):.1f} points
- **Confidence**: {game.get('confidence', 0):.1%}

"""
    
    md += f"""
## Analysis Assets

All analysis outputs are available in:
- `analysis/week14/` - Comprehensive analysis, rankings, recommendations
- `predictions/week14/` - Model predictions, ATS analysis, insights
- `validation/week14/` - Model validation reports

## Files Generated

### Analysis Files
- week14_comprehensive_analysis.json
- week14_matchup_analysis.json
- week14_model_validation.json
- week14_power_rankings.csv
- week14_strategic_recommendations.csv
- week14_upset_alerts.csv
- week14_narrative_previews.md
- week14_comprehensive_report.html

### Prediction Files
- week14_predictions_unified.json/csv
- week14_ats_full_table.csv
- prediction_insights.json
- week14_recommendations.csv
- week14_comprehensive_predictions.csv
- week14_enhanced_analysis_report.json
- week14_enhanced_analysis.md

## Next Steps

1. Review predictions in web app
2. Monitor model performance after games complete
3. Integrate Week 14 results into training data for Week 15

"""
    
    return md

def main():
    """Main execution"""
    print("📊 Generating Week 14 Reports...")
    print("=" * 60)
    
    analysis_dir = PROJECT_ROOT / "analysis" / "week14"
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate intelligence consolidation
    consolidation = generate_intelligence_consolidation()
    consolidation_path = analysis_dir / "week14_intelligence_consolidation.json"
    with open(consolidation_path, 'w') as f:
        json.dump(consolidation, f, indent=2, default=str)
    print(f"✅ Saved intelligence consolidation: {consolidation_path}")
    
    # Generate master report
    master_report = generate_master_report()
    master_report_path = reports_dir / "week14_master_report.md"
    with open(master_report_path, 'w') as f:
        f.write(master_report)
    print(f"✅ Saved master report: {master_report_path}")
    
    print("\n" + "=" * 60)
    print("✅ Week 14 Reports Generated Successfully!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

