#!/usr/bin/env python3
"""
Generate Week 14 Analysis Outputs
Creates prediction insights, recommendations, comprehensive predictions, and enhanced analysis reports
"""

import pandas as pd
import json
from pathlib import Path
import sys
from datetime import datetime
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent

def generate_prediction_insights(unified_df):
    """Generate prediction insights JSON"""
    insights = {
        'total_predictions': len(unified_df),
        'home_win_predictions': int((unified_df.get('home_win_probability', 0) > 0.5).sum()) if 'home_win_probability' in unified_df.columns else 0,
        'away_win_predictions': int((unified_df.get('away_win_probability', 0) > 0.5).sum()) if 'away_win_probability' in unified_df.columns else 0,
        'average_confidence': float(unified_df.get('ensemble_confidence', 0).mean()) if 'ensemble_confidence' in unified_df.columns else 0.0,
        'high_confidence_predictions': int((unified_df.get('ensemble_confidence', 0) > 0.75).sum()) if 'ensemble_confidence' in unified_df.columns else 0,
        'average_predicted_margin': float(unified_df.get('predicted_margin', 0).mean()) if 'predicted_margin' in unified_df.columns else 0.0,
        'upset_predictions': 0,
        'close_games': 0,
        'blowout_predictions': 0,
        'prediction_patterns': {}
    }
    
    # Calculate upset predictions (away team favored by models but home team favored by spread)
    if 'predicted_margin' in unified_df.columns and 'spread' in unified_df.columns:
        # Upset: predicted margin suggests away win but spread favors home
        upsets = ((unified_df['predicted_margin'] < 0) & (unified_df['spread'] > 0)) | \
                 ((unified_df['predicted_margin'] > 0) & (unified_df['spread'] < 0))
        insights['upset_predictions'] = int(upsets.sum())
    
    # Close games (predicted margin within 7 points)
    if 'predicted_margin' in unified_df.columns:
        close = unified_df['predicted_margin'].abs() <= 7
        insights['close_games'] = int(close.sum())
    
    # Blowouts (predicted margin > 21 points)
    if 'predicted_margin' in unified_df.columns:
        blowouts = unified_df['predicted_margin'].abs() > 21
        insights['blowout_predictions'] = int(blowouts.sum())
    
    # Prediction patterns
    if insights['total_predictions'] > 0:
        insights['prediction_patterns'] = {
            'home_win_rate': insights['home_win_predictions'] / insights['total_predictions'],
            'upset_rate': insights['upset_predictions'] / insights['total_predictions'],
            'close_game_rate': insights['close_games'] / insights['total_predictions'],
            'blowout_rate': insights['blowout_predictions'] / insights['total_predictions']
        }
    
    return insights

def generate_recommendations(unified_df):
    """Generate recommendations CSV"""
    recommendations = []
    
    for _, row in unified_df.iterrows():
        matchup = f"{row.get('away_team', 'Away')} @ {row.get('home_team', 'Home')}"
        game_id = row.get('game_id', '')
        spread = row.get('spread', 0)
        predicted_margin = row.get('predicted_margin', 0)
        confidence = row.get('ensemble_confidence', 0)
        edge_pts = row.get('model_edge_pts', 0)
        
        # Determine recommendation type
        rec_type = 'moderate_confidence'
        if edge_pts >= 7 and confidence >= 0.7:
            rec_type = 'high_confidence'
        elif edge_pts < 3 or confidence < 0.5:
            rec_type = 'low_confidence'
        
        # Close game detection
        if abs(predicted_margin) <= 3:
            rec_type = 'close_game'
        
        # Build recommendation
        if rec_type == 'high_confidence':
            ats_pick = row.get('ats_pick', 'No Edge')
            recommendation = f"Strong bet on {ats_pick.split()[0] if ats_pick != 'No Edge' else 'No Edge'} ({confidence*100:.0f}% confidence)"
            action = "Consider strong bet"
        elif rec_type == 'close_game':
            recommendation = f"Very close game expected ({predicted_margin:.1f} margin)"
            action = "Consider prop bets"
        else:
            recommendation = f"Moderate confidence bet ({confidence*100:.0f}% confidence)"
            action = "Consider moderate bet"
        
        recommendations.append({
            'type': rec_type,
            'game_id': game_id,
            'teams': matchup,
            'recommendation': recommendation,
            'action': action,
            'confidence': float(confidence)
        })
    
    return pd.DataFrame(recommendations)

def generate_comprehensive_predictions(unified_df):
    """Generate comprehensive predictions CSV with all details"""
    return unified_df.copy()

def generate_enhanced_analysis_report(unified_df):
    """Generate enhanced analysis report (JSON and markdown)"""
    report_json = {
        'generated_at': datetime.now().isoformat(),
        'week': 14,
        'season': 2025,
        'total_games': len(unified_df),
        'summary_statistics': {},
        'top_value_games': [],
        'key_insights': [],
        'model_performance': {}
    }
    
    # Summary statistics
    if 'ensemble_confidence' in unified_df.columns:
        report_json['summary_statistics']['average_confidence'] = float(unified_df['ensemble_confidence'].mean())
        report_json['summary_statistics']['high_confidence_games'] = int((unified_df['ensemble_confidence'] > 0.75).sum())
        report_json['summary_statistics']['moderate_confidence_games'] = int(((unified_df['ensemble_confidence'] >= 0.5) & (unified_df['ensemble_confidence'] <= 0.75)).sum())
        report_json['summary_statistics']['low_confidence_games'] = int((unified_df['ensemble_confidence'] < 0.5).sum())
    
    if 'predicted_margin' in unified_df.columns:
        report_json['summary_statistics']['average_predicted_margin'] = float(unified_df['predicted_margin'].mean())
    
    # Top value games (by edge)
    if 'model_edge_pts' in unified_df.columns:
        top_value = unified_df.nlargest(10, 'model_edge_pts')
        for _, row in top_value.iterrows():
            report_json['top_value_games'].append({
                'matchup': f"{row.get('away_team', 'Away')} @ {row.get('home_team', 'Home')}",
                'spread': float(row.get('spread', 0)),
                'predicted_margin': float(row.get('predicted_margin', 0)),
                'edge_pts': float(row.get('model_edge_pts', 0)),
                'confidence': float(row.get('ensemble_confidence', 0)),
                'ats_pick': str(row.get('ats_pick', 'No Edge'))
            })
    
    # Key insights
    if 'home_win_probability' in unified_df.columns:
        avg_home_win = unified_df['home_win_probability'].mean()
        report_json['key_insights'].append(f"Average home win probability: {avg_home_win:.1%}")
    
    if 'predicted_margin' in unified_df.columns:
        avg_margin = unified_df['predicted_margin'].mean()
        report_json['key_insights'].append(f"Average predicted margin: {avg_margin:.1f} points")
    
    # Generate markdown report
    md_report = f"""# Week 14 Enhanced Analysis Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics

- Total Games: {report_json['total_games']}
- Average Confidence: {report_json['summary_statistics'].get('average_confidence', 0):.1%}
- High Confidence Games: {report_json['summary_statistics'].get('high_confidence_games', 0)}
- Moderate Confidence Games: {report_json['summary_statistics'].get('moderate_confidence_games', 0)}
- Low Confidence Games: {report_json['summary_statistics'].get('low_confidence_games', 0)}

## Top Value Games

"""
    
    for i, game in enumerate(report_json['top_value_games'][:10], 1):
        md_report += f"""
### {i}. {game['matchup']}

- **Spread**: {game['spread']:.1f}
- **Predicted Margin**: {game['predicted_margin']:.1f}
- **Edge**: {game['edge_pts']:.1f} points
- **Confidence**: {game['confidence']:.1%}
- **ATS Pick**: {game['ats_pick']}

"""
    
    md_report += f"""
## Key Insights

"""
    for insight in report_json['key_insights']:
        md_report += f"- {insight}\n"
    
    return report_json, md_report

def main():
    """Main execution"""
    print("📊 Generating Week 14 Analysis Outputs...")
    print("=" * 60)
    
    predictions_dir = PROJECT_ROOT / "predictions" / "week14"
    analysis_dir = PROJECT_ROOT / "analysis" / "week14"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Load unified predictions
    unified_path = predictions_dir / "week14_predictions_unified.csv"
    if not unified_path.exists():
        print(f"❌ Unified predictions not found: {unified_path}")
        return 1
    
    unified_df = pd.read_csv(unified_path)
    print(f"✅ Loaded unified predictions: {len(unified_df)} games")
    
    # Generate prediction insights
    print("\n1. Generating prediction insights...")
    insights = generate_prediction_insights(unified_df)
    insights_path = predictions_dir / "prediction_insights.json"
    with open(insights_path, 'w') as f:
        json.dump(insights, f, indent=2)
    print(f"   ✅ Saved: {insights_path}")
    
    # Generate recommendations
    print("\n2. Generating recommendations...")
    recommendations_df = generate_recommendations(unified_df)
    recommendations_path = predictions_dir / "week14_recommendations.csv"
    recommendations_df.to_csv(recommendations_path, index=False)
    print(f"   ✅ Saved: {recommendations_path} ({len(recommendations_df)} recommendations)")
    
    # Generate comprehensive predictions
    print("\n3. Generating comprehensive predictions...")
    comprehensive_df = generate_comprehensive_predictions(unified_df)
    comprehensive_path = predictions_dir / "week14_comprehensive_predictions.csv"
    comprehensive_df.to_csv(comprehensive_path, index=False)
    print(f"   ✅ Saved: {comprehensive_path}")
    
    # Generate enhanced analysis report
    print("\n4. Generating enhanced analysis report...")
    report_json, report_md = generate_enhanced_analysis_report(unified_df)
    
    report_json_path = predictions_dir / "week14_enhanced_analysis_report.json"
    with open(report_json_path, 'w') as f:
        json.dump(report_json, f, indent=2)
    print(f"   ✅ Saved JSON: {report_json_path}")
    
    report_md_path = predictions_dir / "week14_enhanced_analysis.md"
    with open(report_md_path, 'w') as f:
        f.write(report_md)
    print(f"   ✅ Saved Markdown: {report_md_path}")
    
    print("\n" + "=" * 60)
    print("✅ Week 14 Analysis Outputs Generated Successfully!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

