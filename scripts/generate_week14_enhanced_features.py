#!/usr/bin/env python3
"""
Generate Week 14 Enhanced Features
Creates 86-feature enhanced data from training data for Week 14
"""

import pandas as pd
import json
from pathlib import Path
import sys
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def generate_week14_enhanced_features():
    """Generate Week 14 enhanced features"""
    print("🔧 Generating Week 14 Enhanced Features...")
    print("=" * 60)
    
    # Load training data
    training_path = PROJECT_ROOT / "data" / "training" / "weekly" / "training_data_2025_week14.csv"
    if not training_path.exists():
        print(f"❌ Training data not found: {training_path}")
        return 1
    
    df = pd.read_csv(training_path)
    print(f"✅ Loaded training data: {len(df)} games, {len(df.columns)} features")
    
    # Check if we need to add missing columns to match Week 13 structure
    week13_features_path = PROJECT_ROOT / "data" / "week13" / "enhanced" / "week13_features_86.csv"
    if week13_features_path.exists():
        week13_sample = pd.read_csv(week13_features_path, nrows=1)
        week13_columns = set(week13_sample.columns)
        week14_columns = set(df.columns)
        missing_columns = week13_columns - week14_columns
        
        if missing_columns:
            print(f"📝 Adding {len(missing_columns)} missing columns to match Week 13 structure...")
            for col in missing_columns:
                if col == 'home_points':
                    df['home_points'] = None  # Games not played yet
                elif col == 'away_points':
                    df['away_points'] = None
                elif col == 'margin':
                    df['margin'] = None
                elif col == 'game_id':
                    # Use 'id' column if it exists, otherwise create from game info
                    if 'id' in df.columns:
                        df['game_id'] = df['id']
                    else:
                        # Create game_id from teams and date
                        df['game_id'] = df.apply(
                            lambda row: hash(f"{row['home_team']}_{row['away_team']}_{row['start_date']}") % 1000000000,
                            axis=1
                        )
                else:
                    df[col] = None  # Fill with None for other missing columns
    
    # Reorder columns to match Week 13 structure if possible
    if week13_features_path.exists():
        week13_sample = pd.read_csv(week13_features_path, nrows=1)
        week13_col_order = week13_sample.columns.tolist()
        # Only reorder columns that exist in both
        common_cols = [c for c in week13_col_order if c in df.columns]
        extra_cols = [c for c in df.columns if c not in week13_col_order]
        df = df[common_cols + extra_cols]
    
    # Ensure we have exactly 86 features (or as close as possible)
    print(f"📊 Final feature count: {len(df.columns)}")
    
    # Use canonical path structure
    from model_pack.utils.path_utils import get_weekly_enhanced_dir, ensure_directory_exists
    
    enhanced_dir = get_weekly_enhanced_dir(14)
    ensure_directory_exists(enhanced_dir)
    
    # Save enhanced features
    features_path = enhanced_dir / "week14_features_86.csv"
    df.to_csv(features_path, index=False)
    print(f"✅ Saved enhanced features: {features_path}")
    print(f"   Games: {len(df)}, Features: {len(df.columns)}")
    
    # Create enhanced games file (subset with game metadata)
    games_cols = ['id', 'game_id', 'start_date', 'season', 'week', 'home_team', 'away_team', 
                  'home_conference', 'away_conference', 'spread', 'neutral_site']
    games_cols = [c for c in games_cols if c in df.columns]
    games_df = df[games_cols].copy()
    
    games_path = enhanced_dir / "week14_enhanced_games.csv"
    games_df.to_csv(games_path, index=False)
    print(f"✅ Saved enhanced games: {games_path}")
    
    # Create metadata
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'week': 14,
        'season': 2025,
        'source_file': str(training_path),
        'games_count': len(df),
        'features_count': len(df.columns),
        'canonical_location': str(enhanced_dir),
        'files_generated': {
            'features': str(features_path),
            'games': str(games_path)
        }
    }
    
    metadata_path = enhanced_dir / "enhancement_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Saved metadata: {metadata_path}")
    
    print("\n" + "=" * 60)
    print("✅ Week 14 Enhanced Features Generated Successfully!")
    print(f"   Location: {enhanced_dir}")
    print(f"   Features: {features_path}")
    print(f"   Games: {games_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(generate_week14_enhanced_features())

