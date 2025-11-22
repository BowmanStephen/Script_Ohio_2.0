#!/usr/bin/env python3
"""
Pick'em League Point Allocation Optimizer
Helps assign points to games based on prediction confidence
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

# Point allocation strategies
STRATEGIES = {
    'standard': {
        'name': 'Standard (2 locks + 6 regular)',
        'allocation': [2, 2, 1, 1, 1, 1, 1, 1],
        'description': 'Two "locks" (2pts each) and six one-point games'
    },
    'aggressive': {
        'name': 'Aggressive (1 mortal lock + 1 lock + 5 regular)',
        'allocation': [3, 2, 1, 1, 1, 1, 1],
        'description': 'One "mortal lock" (3pts), one "lock" (2pts), and five one-point games'
    },
    'super_aggressive': {
        'name': 'Super Aggressive (1 super mortal lock + 5 regular)',
        'allocation': [5, 1, 1, 1, 1, 1],
        'description': 'One "super mortal lock" (5pts) and five one-point games. Can only be used ONCE per season.'
    }
}

def load_predictions():
    """Load Week 13 predictions"""
    preds_path = project_root / 'predictions' / 'week13' / 'week13_predictions_all_60_games.csv'
    if not preds_path.exists():
        print(f"❌ Predictions file not found: {preds_path}")
        return None
    
    df = pd.read_csv(preds_path)
    return df

def calculate_confidence_score(row):
    """Calculate confidence score for a game based on prediction and external line"""
    external_line = row.get('external_line', None)
    external_prob = row.get('external_prob', None)
    external_margin = row.get('external_margin', None)
    
    # If we have external data, use it as primary confidence source
    if external_line is not None and not pd.isna(external_line):
        # Use external probability as confidence (market consensus)
        if external_prob is not None and not pd.isna(external_prob):
            # Confidence is how far from 50/50 (closer to 0 or 1 = more confident)
            prob_confidence = abs(external_prob - 0.5) * 2  # 0 to 1 scale
            
            # Also consider the line magnitude (bigger lines = more confident)
            line_confidence = min(abs(external_line) / 30.0, 1.0)  # Cap at 30 point line
            
            # Combined: weight probability more heavily
            confidence = (prob_confidence * 0.7 + line_confidence * 0.3)
        else:
            # Fall back to line magnitude
            confidence = min(abs(external_line) / 30.0, 1.0)
    else:
        # Fall back to our predictions
        prob = row.get('ensemble_home_win_prob', 0.5)
        margin = row.get('ensemble_margin', 0.0)
        prob_confidence = abs(prob - 0.5) * 2
        margin_confidence = min(abs(margin) / 20.0, 1.0)
        confidence = (prob_confidence * 0.6 + margin_confidence * 0.4)
    
    return min(confidence, 1.0)

def optimize_point_allocation(df, strategy='standard', use_super_mortal=False):
    """Optimize point allocation based on confidence scores"""
    
    if strategy not in STRATEGIES:
        print(f"❌ Unknown strategy: {strategy}")
        return None
    
    strategy_info = STRATEGIES[strategy]
    allocation = strategy_info['allocation'].copy()
    
    # Calculate confidence for each game
    df = df.copy()
    df['confidence_score'] = df.apply(calculate_confidence_score, axis=1)
    
    # Determine which team to pick based on external line (if available) or prediction
    def determine_pick(row):
        external_line = row.get('external_line', None)
        external_prob = row.get('external_prob', None)
        
        # Use external line if available (more reliable)
        # Line format: positive = home team favored, negative = away team favored
        if external_line is not None and not pd.isna(external_line):
            if external_line > 0:
                # Home team favored, pick home team
                return row['home_team'], 'home', external_line
            else:
                # Away team favored (negative line), pick away team
                return row['away_team'], 'away', abs(external_line)
        else:
            # Fall back to our prediction
            prob = row.get('ensemble_home_win_prob', 0.5)
            margin = row.get('ensemble_margin', 0.0)
            if prob > 0.5:
                return row['home_team'], 'home', abs(margin) if margin > 0 else 0
            else:
                return row['away_team'], 'away', abs(margin) if margin < 0 else 0
    
    picks = df.apply(determine_pick, axis=1, result_type='expand')
    df['pick_team'] = picks[0]
    df['pick_type'] = picks[1]
    df['pick_spread'] = picks[2]
    
    # Sort by confidence (highest first)
    df_sorted = df.sort_values('confidence_score', ascending=False).copy()
    
    # Assign points
    df_sorted['assigned_points'] = 0
    df_sorted['pick_label'] = ''
    
    point_idx = 0
    for idx, row in df_sorted.iterrows():
        if point_idx < len(allocation):
            points = allocation[point_idx]
            df_sorted.at[idx, 'assigned_points'] = points
            
            # Label the pick
            if points == 5:
                df_sorted.at[idx, 'pick_label'] = 'SUPER MORTAL LOCK'
            elif points == 3:
                df_sorted.at[idx, 'pick_label'] = 'MORTAL LOCK'
            elif points == 2:
                df_sorted.at[idx, 'pick_label'] = 'LOCK'
            else:
                df_sorted.at[idx, 'pick_label'] = 'Regular'
            
            point_idx += 1
    
    # Filter to only games with assigned points
    picks = df_sorted[df_sorted['assigned_points'] > 0].copy()
    
    # Calculate expected value
    picks['expected_points'] = picks.apply(lambda row:
        row['assigned_points'] * row['confidence_score'], axis=1)
    
    total_expected = picks['expected_points'].sum()
    
    return {
        'strategy': strategy_info['name'],
        'description': strategy_info['description'],
        'picks': picks,
        'total_points': picks['assigned_points'].sum(),
        'expected_points': total_expected,
        'allocation_used': allocation
    }

def format_picks_for_display(result):
    """Format picks for easy reading"""
    picks = result['picks'].copy()
    
    output = []
    output.append("=" * 80)
    output.append(f"PICK'EM LEAGUE - WEEK 13 POINT ALLOCATION")
    output.append("=" * 80)
    output.append(f"\nStrategy: {result['strategy']}")
    output.append(f"Description: {result['description']}")
    output.append(f"Total Points: {result['total_points']}")
    output.append(f"Expected Points: {result['expected_points']:.2f}")
    output.append("\n" + "=" * 80)
    output.append("YOUR PICKS:")
    output.append("=" * 80)
    
    # Sort by points (highest first)
    picks_sorted = picks.sort_values('assigned_points', ascending=False)
    
    for idx, row in picks_sorted.iterrows():
        home = row['home_team']
        away = row['away_team']
        pick = row['pick_team']
        points = int(row['assigned_points'])
        label = row['pick_label']
        confidence = row['confidence_score']
        margin = row.get('ensemble_margin', 0)
        prob = row.get('ensemble_home_win_prob', 0.5)
        line = row.get('external_line', 'N/A')
        
        # Format the pick with spread
        spread = row.get('pick_spread', abs(margin))
        if row['pick_type'] == 'home':
            pick_str = f"{home} (-{spread:.1f})"
        else:
            pick_str = f"{away} (+{spread:.1f})"
        
        output.append(f"\n{label} ({points} pts)")
        output.append(f"  {away} @ {home}")
        output.append(f"  Pick: {pick_str}")
        output.append(f"  Confidence: {confidence:.1%} | Line: {line} | Our Margin: {margin:.1f}")
    
    output.append("\n" + "=" * 80)
    
    return "\n".join(output)

def create_picks_csv(result, output_path):
    """Create CSV file with picks"""
    picks = result['picks'].copy()
    
    # Select relevant columns
    output_cols = [
        'pick_label', 'assigned_points', 'home_team', 'away_team', 'pick_team',
        'pick_type', 'ensemble_margin', 'ensemble_home_win_prob', 
        'external_line', 'confidence_score', 'expected_points'
    ]
    
    available_cols = [col for col in output_cols if col in picks.columns]
    picks_output = picks[available_cols].sort_values('assigned_points', ascending=False)
    
    picks_output.to_csv(output_path, index=False)
    return picks_output

def main():
    print("=" * 80)
    print("PICK'EM LEAGUE POINT ALLOCATION OPTIMIZER")
    print("=" * 80)
    
    # Load predictions
    print("\n📊 Loading Week 13 predictions...")
    df = load_predictions()
    if df is None:
        return 1
    
    print(f"✅ Loaded {len(df)} games")
    
    # Check if external line data is available
    has_external = df['external_line'].notna().sum() > 0
    if has_external:
        print(f"✅ External betting lines available for {df['external_line'].notna().sum()} games")
    else:
        print("⚠️  No external betting lines found - using predictions only")
    
    # Generate recommendations for each strategy
    print("\n" + "=" * 80)
    print("GENERATING RECOMMENDATIONS")
    print("=" * 80)
    
    results = {}
    
    for strategy_name in ['standard', 'aggressive', 'super_aggressive']:
        print(f"\n📊 Strategy: {STRATEGIES[strategy_name]['name']}")
        result = optimize_point_allocation(df, strategy=strategy_name)
        if result:
            results[strategy_name] = result
            print(f"   Expected Points: {result['expected_points']:.2f}")
            print(f"   Total Points: {result['total_points']}")
    
    # Display all strategies
    print("\n" + "=" * 80)
    print("RECOMMENDED STRATEGY COMPARISON")
    print("=" * 80)
    
    for strategy_name, result in results.items():
        print(f"\n{result['strategy']}")
        print(f"  Expected Points: {result['expected_points']:.2f}")
        print(f"  Description: {result['description']}")
    
    # Find best strategy
    best_strategy = max(results.items(), key=lambda x: x[1]['expected_points'])
    print(f"\n🏆 BEST STRATEGY: {best_strategy[1]['strategy']}")
    print(f"   Expected Points: {best_strategy[1]['expected_points']:.2f}")
    
    # Display detailed picks for best strategy
    print("\n" + format_picks_for_display(best_strategy[1]))
    
    # Save picks to file
    output_dir = project_root / 'predictions' / 'week13'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save best strategy picks
    best_csv_path = output_dir / 'week13_pickem_league_picks.csv'
    create_picks_csv(best_strategy[1], best_csv_path)
    print(f"\n✅ Picks saved to: {best_csv_path}")
    
    # Save all strategies
    all_strategies_path = output_dir / 'week13_pickem_all_strategies.json'
    strategies_data = {}
    for name, result in results.items():
        strategies_data[name] = {
            'strategy': result['strategy'],
            'description': result['description'],
            'expected_points': float(result['expected_points']),
            'total_points': int(result['total_points']),
            'picks': result['picks'][['home_team', 'away_team', 'pick_team', 'assigned_points', 
                                     'pick_label', 'confidence_score', 'external_line']].to_dict('records')
        }
    
    with open(all_strategies_path, 'w') as f:
        json.dump(strategies_data, f, indent=2)
    
    print(f"✅ All strategies saved to: {all_strategies_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

