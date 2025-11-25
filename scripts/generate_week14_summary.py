#!/usr/bin/env python3
"""
Generate Week 14 projection summary
Creates summary JSON with key insights and top value games
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sys

PROJECT_ROOT = Path(__file__).parent.parent

def generate_summary():
    """Generate Week 14 projection summary"""
    print("📊 Generating Week 14 projection summary...")
    print("=" * 60)
    
    pred_file = PROJECT_ROOT / "predictions" / "week14" / "week14_model_predictions.csv"
    
    if not pred_file.exists():
        print(f"❌ Predictions file not found: {pred_file}")
        return 1
    
    df = pd.read_csv(pred_file)
    print(f"✅ Loaded {len(df)} Week 14 predictions")
    
    # Create summary
    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_games': len(df),
        'high_confidence_games': 0,
        'moderate_confidence_games': 0,
        'low_confidence_games': 0,
        'top_value_games': [],
        'key_insights': []
    }
    
    # Calculate confidence distribution
    if 'ensemble_confidence' in df.columns:
        summary['high_confidence_games'] = len(df[df['ensemble_confidence'] > 75])
        summary['moderate_confidence_games'] = len(df[(df['ensemble_confidence'] >= 50) & (df['ensemble_confidence'] <= 75)])
        summary['low_confidence_games'] = len(df[df['ensemble_confidence'] < 50])
    elif 'confidence' in df.columns:
        summary['high_confidence_games'] = len(df[df['confidence'] > 75])
        summary['moderate_confidence_games'] = len(df[(df['confidence'] >= 50) & (df['confidence'] <= 75)])
        summary['low_confidence_games'] = len(df[df['confidence'] < 50])
    
    # Top 10 value games (by line value)
    if 'predicted_margin' in df.columns and 'spread' in df.columns:
        df['line_value'] = abs(df['predicted_margin'] - df['spread'])
        top_value = df.nlargest(10, 'line_value')
        
        for _, row in top_value.iterrows():
            game_info = {
                'matchup': f"{row.get('away_team', 'Away')} @ {row.get('home_team', 'Home')}",
                'spread': float(row.get('spread', 0)),
                'predicted_margin': float(row.get('predicted_margin', 0)),
                'line_value': float(row['line_value']),
                'confidence': float(row.get('ensemble_confidence', row.get('confidence', 0)))
            }
            summary['top_value_games'].append(game_info)
    
    # Key insights
    if 'ensemble_home_win_probability' in df.columns:
        avg_home_win_prob = df['ensemble_home_win_probability'].mean()
        summary['key_insights'].append(f"Average home win probability: {avg_home_win_prob:.1%}")
    
    if 'predicted_margin' in df.columns:
        avg_margin = df['predicted_margin'].mean()
        summary['key_insights'].append(f"Average predicted margin: {avg_margin:.1f} points")
    
    # Save summary
    summary_file = PROJECT_ROOT / "predictions" / "week14" / "week14_summary.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Summary saved to {summary_file}")
    print(f"\nSummary Statistics:")
    print(f"  Total games: {summary['total_games']}")
    print(f"  High confidence: {summary['high_confidence_games']}")
    print(f"  Moderate confidence: {summary['moderate_confidence_games']}")
    print(f"  Low confidence: {summary['low_confidence_games']}")
    print(f"  Top value games: {len(summary['top_value_games'])}")
    
    return 0

if __name__ == "__main__":
    sys.exit(generate_summary())

