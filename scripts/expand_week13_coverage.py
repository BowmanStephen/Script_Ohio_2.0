#!/usr/bin/env python3
"""
Expand Week 13 coverage to all 60 games and fix feature compatibility
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from project_management.TOOLS_AND_CONFIG.model_features import RIDGE_FEATURES, XGB_FEATURES

# External predictions data (from user input - all 60 games)
EXTERNAL_GAMES = [
    {'home': 'Air Force', 'away': 'New Mexico', 'line': -2, 'margin': -1.49, 'prob': 0.4642},
    {'home': 'Appalachian St.', 'away': 'Marshall', 'line': -3.5, 'margin': -5.02, 'prob': 0.3775},
    {'home': 'Arizona', 'away': 'Baylor', 'line': 6.5, 'margin': 8.18, 'prob': 0.6874},
    {'home': 'Arkansas St.', 'away': 'Louisiana-Lafayette', 'line': 2.5, 'margin': 2.64, 'prob': 0.5645},
    {'home': 'Army', 'away': 'Tulsa', 'line': 10.5, 'margin': 14, 'prob': 0.8057},
    {'home': 'Boise St.', 'away': 'Colorado St.', 'line': 16.5, 'margin': 18.26, 'prob': 0.8695},
    {'home': 'Bowling Green', 'away': 'Akron', 'line': 3.5, 'margin': 5.54, 'prob': 0.6337},
    {'home': 'Buffalo', 'away': 'Miami (Ohio)', 'line': 2, 'margin': -3.03, 'prob': 0.4261},
    {'home': 'Central Florida', 'away': 'Oklahoma St.', 'line': 14.5, 'margin': 17.31, 'prob': 0.8565},
    {'home': 'Cincinnati', 'away': 'BYU', 'line': -2, 'margin': -6.67, 'prob': 0.3391},
    {'home': 'Colorado', 'away': 'Arizona St.', 'line': -7.5, 'margin': -6.53, 'prob': 0.343},
    {'home': 'Florida', 'away': 'Tennessee', 'line': -3.5, 'margin': -4.48, 'prob': 0.3906},
    {'home': 'Florida Atlantic', 'away': 'Connecticut', 'line': -7.5, 'margin': -5.71, 'prob': 0.3624},
    {'home': 'Florida Intl.', 'away': 'Jacksonville St.', 'line': -1, 'margin': -0.46, 'prob': 0.4885},
    {'home': 'Fresno St.', 'away': 'Utah St.', 'line': 2.5, 'margin': 4.17, 'prob': 0.6021},
    {'home': 'Georgia', 'away': 'Charlotte', 'line': 45, 'margin': 46.08, 'prob': 0.9958},
    {'home': 'Georgia Southern', 'away': 'Old Dominion', 'line': -10.5, 'margin': -8.88, 'prob': 0.2942},
    {'home': 'Georgia Tech', 'away': 'Pittsburgh', 'line': 2.5, 'margin': 0.85, 'prob': 0.5208},
    {'home': 'Houston', 'away': 'TCU', 'line': 2.5, 'margin': 1.33, 'prob': 0.5322},
    {'home': 'Iowa', 'away': 'Michigan St.', 'line': 17, 'margin': 21.37, 'prob': 0.9046},
    {'home': 'Iowa St.', 'away': 'Kansas', 'line': 4, 'margin': 7.56, 'prob': 0.6797},
    {'home': 'James Madison', 'away': 'Washington St.', 'line': 14, 'margin': 12.19, 'prob': 0.7694},
    {'home': 'Kennesaw St.', 'away': 'Missouri St.', 'line': 6.5, 'margin': 5.41, 'prob': 0.6303},
    {'home': 'Kent', 'away': 'Central Mich.', 'line': -8, 'margin': -6.92, 'prob': 0.3351},
    {'home': 'LSU', 'away': 'Western Kentucky', 'line': 21.5, 'margin': 21.69, 'prob': 0.8937},
    {'home': 'Louisiana Tech', 'away': 'Liberty', 'line': 1, 'margin': 5.96, 'prob': 0.6422},
    {'home': 'Maryland', 'away': 'Michigan', 'line': -13.5, 'margin': -10.51, 'prob': 0.2588},
    {'home': 'Middle Tenn.', 'away': 'Sam Houston St.', 'line': 6.5, 'margin': 4.23, 'prob': 0.601},
    {'home': 'NC St.', 'away': 'Florida St.', 'line': -4.5, 'margin': -4.78, 'prob': 0.3865},
    {'home': 'North Carolina', 'away': 'Duke', 'line': -6.5, 'margin': -6.23, 'prob': 0.351},
    {'home': 'Northern Ill.', 'away': 'Western Mich.', 'line': -6.5, 'margin': -5.9, 'prob': 0.3593},
    {'home': 'Northwestern', 'away': 'Minnesota', 'line': 4.5, 'margin': 4.74, 'prob': 0.6136},
    {'home': 'Notre Dame', 'away': 'Syracuse', 'line': 35, 'margin': 33.1, 'prob': 0.9756},
    {'home': 'Ohio', 'away': 'Massachusetts', 'line': 32.5, 'margin': 33.04, 'prob': 0.9775},
    {'home': 'Ohio St.', 'away': 'Rutgers', 'line': 30.5, 'margin': 31.42, 'prob': 0.9675},
    {'home': 'Oklahoma', 'away': 'Missouri', 'line': 9.5, 'margin': 7.09, 'prob': 0.6679},
    {'home': 'Oregon', 'away': 'USC', 'line': 9.5, 'margin': 9.51, 'prob': 0.721},
    {'home': 'Penn St.', 'away': 'Nebraska', 'line': 9.5, 'margin': 7.72, 'prob': 0.68},
    {'home': 'Rice', 'away': 'North Texas', 'line': -18, 'margin': -19.46, 'prob': 0.1216},
    {'home': 'SMU', 'away': 'Louisville', 'line': 3, 'margin': 5.34, 'prob': 0.6294},
    {'home': 'San Diego St.', 'away': 'San Jose St.', 'line': 11.5, 'margin': 17.39, 'prob': 0.8495},
    {'home': 'South Alabama', 'away': 'Southern Miss.', 'line': -3, 'margin': -1.26, 'prob': 0.47},
    {'home': 'South Carolina', 'away': 'Coastal Carolina', 'line': 23, 'margin': 20.75, 'prob': 0.8899},
    {'home': 'Stanford', 'away': 'California', 'line': -2.5, 'margin': -0.98, 'prob': 0.4759},
    {'home': 'Temple', 'away': 'Tulane', 'line': -8, 'margin': -7.39, 'prob': 0.3247},
    {'home': 'Texas', 'away': 'Arkansas', 'line': 10.5, 'margin': 11.37, 'prob': 0.7568},
    {'home': 'Texas St.', 'away': 'Louisiana-Monroe', 'line': 19, 'margin': 19.6, 'prob': 0.8858},
    {'home': 'Texas-San Antonio', 'away': 'East Carolina', 'line': -3, 'margin': -4.36, 'prob': 0.3941},
    {'home': 'Toledo', 'away': 'Ball St.', 'line': 27.5, 'margin': 26.13, 'prob': 0.9405},
    {'home': 'Troy St.', 'away': 'Georgia St.', 'line': 11, 'margin': 14.34, 'prob': 0.8089},
    {'home': 'UAB', 'away': 'South Florida', 'line': -21, 'margin': -21.73, 'prob': 0.0972},
    {'home': 'UCLA', 'away': 'Washington', 'line': -10.5, 'margin': -12.07, 'prob': 0.2379},
    {'home': 'UNLV', 'away': 'Hawaii', 'line': 3.5, 'margin': 3.91, 'prob': 0.594},
    {'home': 'UTEP', 'away': 'New Mexico St.', 'line': 3, 'margin': 2.81, 'prob': 0.5694},
    {'home': 'Utah', 'away': 'Kansas St.', 'line': 16.5, 'margin': 19.01, 'prob': 0.8669},
    {'home': 'Vanderbilt', 'away': 'Kentucky', 'line': 10, 'margin': 10, 'prob': 0.7316},
    {'home': 'Virginia Tech', 'away': 'Miami (Fla.)', 'line': -17, 'margin': -20.09, 'prob': 0.1122},
    {'home': 'Wake Forest', 'away': 'Delaware', 'line': 17, 'margin': 19.61, 'prob': 0.8764},
    {'home': 'Wisconsin', 'away': 'Illinois', 'line': -9.5, 'margin': -8.55, 'prob': 0.2988},
    {'home': 'Wyoming', 'away': 'Nevada', 'line': 7, 'margin': 7.85, 'prob': 0.686},
]

def normalize_team_name(name):
    """Normalize team names to match our system"""
    name = name.strip()
    # Common variations
    replacements = {
        'Appalachian St.': 'Appalachian State',
        'Boise St.': 'Boise State',
        'Colorado St.': 'Colorado State',
        'Fresno St.': 'Fresno State',
        'Georgia St.': 'Georgia State',
        'Iowa St.': 'Iowa State',
        'Kansas St.': 'Kansas State',
        'Michigan St.': 'Michigan State',
        'NC St.': 'NC State',
        'Oklahoma St.': 'Oklahoma State',
        'Penn St.': 'Penn State',
        'San Diego St.': 'San Diego State',
        'San Jose St.': 'San Jose State',
        'Utah St.': 'Utah State',
        'Washington St.': 'Washington State',
        'Arizona St.': 'Arizona State',
        'Troy St.': 'Troy',
        'Middle Tenn.': 'Middle Tennessee',
        'Sam Houston St.': 'Sam Houston State',
        'Central Mich.': 'Central Michigan',
        'Western Mich.': 'Western Michigan',
        'Ball St.': 'Ball State',
        'New Mexico St.': 'New Mexico State',
        'Ohio St.': 'Ohio State',
        'Southern Miss.': 'Southern Miss',
        'Jacksonville St.': 'Jacksonville State',
        'Kennesaw St.': 'Kennesaw State',
        'Missouri St.': 'Missouri State',
        'Louisiana-Lafayette': 'Louisiana',
        'Louisiana-Monroe': 'Louisiana Monroe',
        'Texas-San Antonio': 'UTSA',
        'Central Florida': 'UCF',
        'Miami (Ohio)': 'Miami OH',
        'Miami (Fla.)': 'Miami',
        'Florida Intl.': 'FIU',
        'Florida Atlantic': 'FAU',
        'Northern Ill.': 'Northern Illinois',
    }
    return replacements.get(name, name)

def load_training_data_defaults():
    """Load training data to get default values for features"""
    training_path = project_root / 'model_pack' / 'updated_training_data.csv'
    if not training_path.exists():
        print(f"⚠️  Training data not found at {training_path}")
        return {}
    
    df = pd.read_csv(training_path)
    
    # Get mean values for numeric features
    defaults = {}
    for feature in RIDGE_FEATURES + XGB_FEATURES:
        if feature in df.columns:
            defaults[feature] = df[feature].mean()
        else:
            defaults[feature] = 0.0
    
    return defaults

def get_team_metrics(team_name, training_df):
    """Get average metrics for a team from training data"""
    if training_df is None or len(training_df) == 0:
        # Fallback to defaults if no training data
        return {
            'talent': 750.0,
            'elo': 1500.0,
            'adjusted_epa': 0.0,
            'adjusted_epa_allowed': 0.0,
            'adjusted_success': 0.5,
            'adjusted_success_allowed': 0.5,
        }
    
    # Find games where this team played (either home or away)
    home_games = training_df[training_df['home_team'] == team_name]
    away_games = training_df[training_df['away_team'] == team_name]
    
    # Calculate metrics from home games
    talent_values = []
    elo_values = []
    epa_values = []
    epa_allowed_values = []
    success_values = []
    success_allowed_values = []
    
    if len(home_games) > 0:
        talent_values.extend(home_games['home_talent'].dropna().tolist())
        elo_values.extend(home_games['home_elo'].dropna().tolist())
        epa_values.extend(home_games['home_adjusted_epa'].dropna().tolist())
        epa_allowed_values.extend(home_games['home_adjusted_epa_allowed'].dropna().tolist())
        success_values.extend(home_games['home_adjusted_success'].dropna().tolist())
        success_allowed_values.extend(home_games['home_adjusted_success_allowed'].dropna().tolist())
    
    if len(away_games) > 0:
        talent_values.extend(away_games['away_talent'].dropna().tolist())
        elo_values.extend(away_games['away_elo'].dropna().tolist())
        epa_values.extend(away_games['away_adjusted_epa'].dropna().tolist())
        epa_allowed_values.extend(away_games['away_adjusted_epa_allowed'].dropna().tolist())
        success_values.extend(away_games['away_adjusted_success'].dropna().tolist())
        success_allowed_values.extend(away_games['away_adjusted_success_allowed'].dropna().tolist())
    
    # Calculate averages with fallbacks
    return {
        'talent': np.mean(talent_values) if talent_values else 750.0,
        'elo': np.mean(elo_values) if elo_values else 1500.0,
        'adjusted_epa': np.mean(epa_values) if epa_values else 0.0,
        'adjusted_epa_allowed': np.mean(epa_allowed_values) if epa_allowed_values else 0.0,
        'adjusted_success': np.mean(success_values) if success_values else 0.5,
        'adjusted_success_allowed': np.mean(success_allowed_values) if success_allowed_values else 0.5,
    }

def generate_model_compatible_features(external_games, training_defaults):
    """Generate features compatible with ML models"""
    print(f"\n🔄 Generating model-compatible features for {len(external_games)} games...")
    
    # Load training data for team lookups
    training_path = project_root / 'model_pack' / 'updated_training_data.csv'
    training_df = None
    if training_path.exists():
        training_df = pd.read_csv(training_path)
        print(f"✅ Loaded training data with {len(training_df)} records")
    
    features_list = []
    
    for idx, game in enumerate(external_games):
        home_team = normalize_team_name(game['home'])
        away_team = normalize_team_name(game['away'])
        spread = game.get('line', 0.0)
        
        # Get team metrics (simplified - would use actual team data in production)
        home_metrics = get_team_metrics(home_team, training_df)
        away_metrics = get_team_metrics(away_team, training_df)
        
        # Create feature row with all required features
        feature_row = {
            'game_id': f"2025_week13_{idx+1:03d}",
            'home_team': home_team,
            'away_team': away_team,
            'season': 2025,
            'week': 13,
            'spread': spread,
            
            # Core features
            'home_talent': home_metrics['talent'],
            'away_talent': away_metrics['talent'],
            'home_elo': home_metrics['elo'],
            'away_elo': away_metrics['elo'],
            
            # EPA features
            'home_adjusted_epa': home_metrics['adjusted_epa'],
            'home_adjusted_epa_allowed': home_metrics['adjusted_epa_allowed'],
            'away_adjusted_epa': away_metrics['adjusted_epa'],
            'away_adjusted_epa_allowed': away_metrics['adjusted_epa_allowed'],
            
            # Success rate features
            'home_adjusted_success': home_metrics['adjusted_success'],
            'home_adjusted_success_allowed': home_metrics['adjusted_success_allowed'],
            'away_adjusted_success': away_metrics['adjusted_success'],
            'away_adjusted_success_allowed': away_metrics['adjusted_success_allowed'],
        }
        
        # Add all other required features with defaults
        all_features = set(RIDGE_FEATURES + XGB_FEATURES)
        for feature in all_features:
            if feature not in feature_row:
                feature_row[feature] = training_defaults.get(feature, 0.0)
        
        features_list.append(feature_row)
        
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(external_games)} games...")
    
    features_df = pd.DataFrame(features_list)
    print(f"✅ Generated features for {len(features_df)} games")
    print(f"✅ Total features: {len(features_df.columns)}")
    
    return features_df

def main():
    print("=" * 80)
    print("EXPAND WEEK 13 COVERAGE TO ALL 60 GAMES")
    print("=" * 80)
    
    # Step 1: Load training data defaults
    print("\n📊 Step 1: Loading training data defaults...")
    training_defaults = load_training_data_defaults()
    print(f"✅ Loaded defaults for {len(training_defaults)} features")
    
    # Step 2: Generate model-compatible features
    print("\n📊 Step 2: Generating model-compatible features...")
    features_df = generate_model_compatible_features(EXTERNAL_GAMES, training_defaults)
    
    # Step 3: Save features
    output_dir = project_root / 'data' / 'week13' / 'enhanced'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    features_path = output_dir / 'week13_features_86_model_compatible.csv'
    features_df.to_csv(features_path, index=False)
    print(f"\n✅ Saved features to: {features_path}")
    
    # Step 4: Create enhanced games file
    enhanced_games = []
    for idx, game in enumerate(EXTERNAL_GAMES):
        enhanced_games.append({
            'id': f"2025_week13_{idx+1:03d}",
            'season': 2025,
            'week': 13,
            'home_team': normalize_team_name(game['home']),
            'away_team': normalize_team_name(game['away']),
            'external_line': game.get('line', None),
            'external_margin': game.get('margin', None),
            'external_prob': game.get('prob', None),
        })
    
    enhanced_games_df = pd.DataFrame(enhanced_games)
    enhanced_path = output_dir / 'week13_enhanced_games_all_60.csv'
    enhanced_games_df.to_csv(enhanced_path, index=False)
    print(f"✅ Saved enhanced games to: {enhanced_path}")
    
    # Step 5: Validate features
    print("\n📊 Step 5: Validating features...")
    missing_ridge = [f for f in RIDGE_FEATURES if f not in features_df.columns]
    missing_xgb = [f for f in XGB_FEATURES if f not in features_df.columns]
    
    if missing_ridge:
        print(f"⚠️  Missing Ridge features: {missing_ridge}")
    else:
        print("✅ All Ridge features present")
    
    if missing_xgb:
        print(f"⚠️  Missing XGBoost features: {missing_xgb}")
    else:
        print("✅ All XGBoost features present")
    
    print("\n" + "=" * 80)
    print("✅ EXPANSION COMPLETE")
    print("=" * 80)
    print(f"\nGenerated features for {len(features_df)} games")
    print(f"Features file: {features_path}")
    print(f"Enhanced games file: {enhanced_path}")
    print("\nNext step: Run predictions using these features")

if __name__ == "__main__":
    main()

