#!/usr/bin/env python3
"""
Consolidate Week 14 Predictions
Merges model predictions with ATS analysis into unified format
"""

import pandas as pd
import json
from pathlib import Path
import sys
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent

def consolidate_week14_predictions():
    """Consolidate Week 14 predictions into unified format"""
    print("📊 Consolidating Week 14 Predictions...")
    print("=" * 60)
    
    predictions_dir = PROJECT_ROOT / "predictions" / "week14"
    
    # Load model predictions JSON
    model_preds_json_path = predictions_dir / "week14_model_predictions.json"
    if not model_preds_json_path.exists():
        print(f"❌ Model predictions JSON not found: {model_preds_json_path}")
        return 1
    
    with open(model_preds_json_path) as f:
        model_preds = json.load(f)
    
    print(f"✅ Loaded model predictions: {len(model_preds)} games")
    
    # Convert to DataFrame
    model_df = pd.DataFrame(model_preds)
    
    # Load ATS table
    ats_table_path = predictions_dir / "week14_ats_full_table.csv"
    if not ats_table_path.exists():
        print(f"❌ ATS table not found: {ats_table_path}")
        return 1
    
    ats_df = pd.read_csv(ats_table_path)
    print(f"✅ Loaded ATS table: {len(ats_df)} games")
    
    # Create matchup key for merging
    if 'matchup' not in model_df.columns:
        model_df['matchup'] = model_df['away_team'] + ' @ ' + model_df['home_team']
    
    # Merge on matchup
    unified_df = model_df.merge(
        ats_df[['matchup', 'ats_pick', 'confidence_grade', 'model_summary', 'model_edge_pts']],
        on='matchup',
        how='left',
        suffixes=('', '_ats')
    )
    
    # Add any additional fields from enhanced predictions if available
    enhanced_path = predictions_dir / "week14_predictions_enhanced.csv"
    if enhanced_path.exists():
        enhanced_df = pd.read_csv(enhanced_path)
        print(f"✅ Loaded enhanced predictions: {len(enhanced_df)} games")
        
        # Merge additional fields that don't conflict
        if 'matchup' not in enhanced_df.columns:
            enhanced_df['matchup'] = enhanced_df['away_team'] + ' @ ' + enhanced_df['home_team']
        
        # Get columns that don't exist in unified_df
        new_cols = [c for c in enhanced_df.columns if c not in unified_df.columns and c != 'matchup']
        if new_cols:
            unified_df = unified_df.merge(
                enhanced_df[['matchup'] + new_cols],
                on='matchup',
                how='left'
            )
            print(f"   Added {len(new_cols)} additional columns from enhanced predictions")
    
    # Ensure all key fields are present
    required_fields = [
        'game_id', 'season', 'week', 'home_team', 'away_team',
        'spread', 'predicted_margin', 'home_win_probability', 'away_win_probability',
        'ensemble_confidence', 'model_agreement', 'ats_pick', 'confidence_grade'
    ]
    
    missing_fields = [f for f in required_fields if f not in unified_df.columns]
    if missing_fields:
        print(f"⚠️  Missing fields: {missing_fields}")
    
    # Sort by game_id or matchup
    if 'game_id' in unified_df.columns:
        unified_df = unified_df.sort_values('game_id')
    else:
        unified_df = unified_df.sort_values('matchup')
    
    # Save unified predictions
    unified_json_path = predictions_dir / "week14_predictions_unified.json"
    unified_df.to_json(unified_json_path, orient='records', indent=2)
    print(f"✅ Saved unified predictions JSON: {unified_json_path}")
    
    unified_csv_path = predictions_dir / "week14_predictions_unified.csv"
    unified_df.to_csv(unified_csv_path, index=False)
    print(f"✅ Saved unified predictions CSV: {unified_csv_path}")
    
    # Validation summary
    print("\n" + "=" * 60)
    print("Consolidation Summary:")
    print(f"   Total games: {len(unified_df)}")
    print(f"   Total columns: {len(unified_df.columns)}")
    print(f"   Games with ATS picks: {unified_df['ats_pick'].notna().sum()}")
    print(f"   Games with confidence grades: {unified_df['confidence_grade'].notna().sum()}")
    
    # Check for any inconsistencies
    if len(unified_df) != len(model_preds):
        print(f"⚠️  Warning: Unified predictions ({len(unified_df)}) != Model predictions ({len(model_preds)})")
    
    print("\n✅ Week 14 Predictions Consolidated Successfully!")
    
    return 0

if __name__ == "__main__":
    sys.exit(consolidate_week14_predictions())

