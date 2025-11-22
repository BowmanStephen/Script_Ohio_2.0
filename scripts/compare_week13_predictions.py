#!/usr/bin/env python3
"""
Compare our Week 13 predictions with external prediction data
"""

import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load our predictions
our_preds = pd.read_csv('predictions/week13/week13_comprehensive_predictions.csv')

# Team name normalization mapping
TEAM_MAPPING = {
    # Our name -> External name variations
    'Ohio State': ['Ohio St.', 'Ohio State'],
    'Michigan': ['Michigan'],
    'Alabama': ['Alabama'],
    'Auburn': ['Auburn'],
    'Georgia': ['Georgia'],
    'Georgia Tech': ['Georgia Tech'],
    'Florida State': ['Florida St.', 'Florida State'],
    'Florida': ['Florida'],
    'USC': ['USC'],
    'UCLA': ['UCLA'],
    'Texas': ['Texas'],
    'Texas A&M': ['Texas A&M'],
    'Oklahoma': ['Oklahoma'],
    'Oklahoma State': ['Oklahoma St.', 'Oklahoma State'],
    'Clemson': ['Clemson'],
    'South Carolina': ['South Carolina'],
    'Oregon': ['Oregon'],
    'Oregon State': ['Oregon St.', 'Oregon State'],
    'Washington': ['Washington'],
    'Washington State': ['Washington St.', 'Washington State'],
    'Arizona': ['Arizona'],
    'Arizona State': ['Arizona St.', 'Arizona State'],
    'Virginia Tech': ['Virginia Tech'],
    'Virginia': ['Virginia'],
    'North Carolina': ['North Carolina'],
    'NC State': ['NC St.', 'NC State'],
    'Kansas': ['Kansas'],
    'Kansas State': ['Kansas St.', 'Kansas State'],
    'Iowa': ['Iowa'],
    'Iowa State': ['Iowa St.', 'Iowa State'],
    'Michigan State': ['Michigan St.', 'Michigan State'],
    'Penn State': ['Penn St.', 'Penn State'],
    'Notre Dame': ['Notre Dame'],
    'Stanford': ['Stanford'],
    'Pittsburgh': ['Pittsburgh'],
    'Syracuse': ['Syracuse'],
    'Duke': ['Duke'],
    'Rutgers': ['Rutgers'],
    'Nebraska': ['Nebraska'],
    'Missouri': ['Missouri'],
    'Arkansas': ['Arkansas'],
    'Kentucky': ['Kentucky'],
    'Vanderbilt': ['Vanderbilt'],
    'Louisville': ['Louisville'],
    'SMU': ['SMU'],
    'Utah': ['Utah'],
    'BYU': ['BYU'],
    'Cincinnati': ['Cincinnati'],
}

def normalize_team(team_name, mapping):
    """Normalize team name for matching"""
    team_name = team_name.strip()
    # Direct match
    if team_name in mapping:
        return mapping[team_name]
    # Reverse lookup
    for our_name, variations in mapping.items():
        if team_name in variations:
            return our_name
    # Try partial match
    for our_name, variations in mapping.items():
        for var in variations:
            if team_name.lower() in var.lower() or var.lower() in team_name.lower():
                return our_name
    return team_name

# External predictions data (from user input)
external_data = [
    {'home': 'Air Force', 'away': 'New Mexico', 'margin': -1.49, 'prob': 0.4642, 'line': -2},
    {'home': 'Arizona', 'away': 'Baylor', 'margin': 8.18, 'prob': 0.6874, 'line': 6.5},
    {'home': 'Bowling Green', 'away': 'Akron', 'margin': 5.54, 'prob': 0.6337, 'line': 3.5},
    {'home': 'Buffalo', 'away': 'Miami (Ohio)', 'margin': -3.03, 'prob': 0.4261, 'line': 2},
    {'home': 'Central Florida', 'away': 'Oklahoma St.', 'margin': 17.31, 'prob': 0.8565, 'line': 14.5},
    {'home': 'Cincinnati', 'away': 'BYU', 'margin': -6.67, 'prob': 0.3391, 'line': -2},
    {'home': 'Florida', 'away': 'Tennessee', 'margin': -4.48, 'prob': 0.3906, 'line': -3.5},
    {'home': 'Georgia', 'away': 'Charlotte', 'margin': 46.08, 'prob': 0.9958, 'line': 45},
    {'home': 'Georgia Tech', 'away': 'Pittsburgh', 'margin': 0.85, 'prob': 0.5208, 'line': 2.5},
    {'home': 'Iowa', 'away': 'Michigan St.', 'margin': 21.37, 'prob': 0.9046, 'line': 17},
    {'home': 'Iowa St.', 'away': 'Kansas', 'margin': 7.56, 'prob': 0.6797, 'line': 4},
    {'home': 'Maryland', 'away': 'Michigan', 'margin': -10.51, 'prob': 0.2588, 'line': -13.5},
    {'home': 'NC St.', 'away': 'Florida St.', 'margin': -4.78, 'prob': 0.3865, 'line': -4.5},
    {'home': 'North Carolina', 'away': 'Duke', 'margin': -6.23, 'prob': 0.351, 'line': -6.5},
    {'home': 'Notre Dame', 'away': 'Syracuse', 'margin': 33.1, 'prob': 0.9756, 'line': 35},
    {'home': 'Ohio', 'away': 'Massachusetts', 'margin': 33.04, 'prob': 0.9775, 'line': 32.5},
    {'home': 'Ohio St.', 'away': 'Rutgers', 'margin': 31.42, 'prob': 0.9675, 'line': 30.5},
    {'home': 'Oklahoma', 'away': 'Missouri', 'margin': 7.09, 'prob': 0.6679, 'line': 9.5},
    {'home': 'Oregon', 'away': 'USC', 'margin': 9.51, 'prob': 0.721, 'line': 9.5},
    {'home': 'Penn St.', 'away': 'Nebraska', 'margin': 7.72, 'prob': 0.68, 'line': 9.5},
    {'home': 'SMU', 'away': 'Louisville', 'margin': 5.34, 'prob': 0.6294, 'line': 3},
    {'home': 'Texas', 'away': 'Arkansas', 'margin': 11.37, 'prob': 0.7568, 'line': 10.5},
    {'home': 'Utah', 'away': 'Kansas St.', 'margin': 19.01, 'prob': 0.8669, 'line': 16.5},
    {'home': 'Vanderbilt', 'away': 'Kentucky', 'margin': 10.0, 'prob': 0.7316, 'line': 10},
    {'home': 'Virginia Tech', 'away': 'Miami (Fla.)', 'margin': -20.09, 'prob': 0.1122, 'line': -17},
]

external_df = pd.DataFrame(external_data)

# Create comparison
comparisons = []
for _, our_row in our_preds.iterrows():
    our_home = our_row['home_team']
    our_away = our_row['away_team']
    our_margin = our_row['predicted_margin']
    our_prob = our_row['home_win_probability']
    
    # Try to find matching external prediction
    match_found = False
    for _, ext_row in external_df.iterrows():
        ext_home_raw = ext_row['home']
        ext_away_raw = ext_row['away']
        ext_home = normalize_team(ext_home_raw, TEAM_MAPPING)
        ext_away = normalize_team(ext_away_raw, TEAM_MAPPING)
        
        # Match teams - simple string matching with normalization
        # Create reverse mapping for easier lookup
        reverse_map = {}
        for our_name, variations in TEAM_MAPPING.items():
            for var in variations:
                reverse_map[var] = our_name
            reverse_map[our_name] = our_name
        
        # Normalize external team names
        ext_home_norm = reverse_map.get(ext_home_raw, ext_home_raw)
        ext_away_norm = reverse_map.get(ext_away_raw, ext_away_raw)
        
        # Match
        home_match = (our_home == ext_home_norm) or (our_home == ext_home_raw) or \
                     (our_home.lower() == ext_home_raw.lower()) or \
                     (our_home.lower() == ext_home_norm.lower())
        away_match = (our_away == ext_away_norm) or (our_away == ext_away_raw) or \
                     (our_away.lower() == ext_away_raw.lower()) or \
                     (our_away.lower() == ext_away_norm.lower())
        
        if home_match and away_match:
            comparisons.append({
                'home_team': our_home,
                'away_team': our_away,
                'our_margin': our_margin,
                'external_margin': ext_row['margin'],
                'margin_diff': our_margin - ext_row['margin'],
                'our_prob': our_prob,
                'external_prob': ext_row['prob'],
                'prob_diff': our_prob - ext_row['prob'],
                'external_line': ext_row['line'],
            })
            match_found = True
            break
    
    if not match_found:
        comparisons.append({
            'home_team': our_home,
            'away_team': our_away,
            'our_margin': our_margin,
            'external_margin': None,
            'margin_diff': None,
            'our_prob': our_prob,
            'external_prob': None,
            'prob_diff': None,
            'external_line': None,
        })

comp_df = pd.DataFrame(comparisons)

# Save comparison
output_path = project_root / 'predictions' / 'week13' / 'week13_prediction_comparison.csv'
comp_df.to_csv(output_path, index=False)

# Print summary
print("=" * 80)
print("WEEK 13 PREDICTION COMPARISON")
print("=" * 80)
print(f"\nOur predictions: {len(our_preds)} games")
print(f"External predictions: {len(external_df)} games")
matched = comp_df[comp_df['external_margin'].notna()]
print(f"Matched games: {len(matched)} games")

if len(matched) > 0:
    print(f"\nAverage margin difference: {matched['margin_diff'].abs().mean():.2f} points")
    print(f"Average probability difference: {matched['prob_diff'].abs().mean():.4f}")
    print(f"\nTop comparisons:")
    display_cols = ['home_team', 'away_team', 'our_margin', 'external_margin', 'margin_diff', 
                   'our_prob', 'external_prob', 'prob_diff']
    print(matched[display_cols].to_string(index=False))
else:
    print("\n⚠️  No matches found. Team names may need adjustment.")
    print("\nOur teams:")
    print(our_preds[['home_team', 'away_team']].to_string())
    print("\nExternal teams:")
    print(external_df[['home', 'away']].to_string())

print(f"\n✅ Comparison saved to: {output_path}")

