#!/usr/bin/env python3
"""
Import Week 13 predictions from external source
Parses the provided predictions data and integrates with our Week 13 analysis
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def parse_predictions_text(text_data):
    """
    Parse the predictions text data into a DataFrame
    Format: Home | Road | Line Open | Line | Midweek Line | Prediction Avg | etc.
    """
    lines = text_data.strip().split('\n')
    
    # Skip header lines and parse data
    games = []
    data_started = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header rows
        if 'Prediction' in line or 'Home' in line and 'Road' in line:
            data_started = True
            continue
        
        if not data_started:
            continue
        
        # Split by tabs (preserving empty fields)
        parts = line.split('\t')
        
        # Clean up parts
        parts = [p.strip() if p.strip() else None for p in parts]
        
        # Need at least 11 fields (midweek line may be empty)
        if len(parts) >= 11:
            try:
                # Helper function to parse float values
                def parse_float(val):
                    if val is None:
                        return None
                    val = str(val).strip()
                    if not val or val == '' or val == '-':
                        return None
                    try:
                        return float(val)
                    except ValueError:
                        return None
                
                # Map fields: Home, Away, Line Open, Line Current, Midweek (empty), Avg, Median, Std, Min, Max, Home Win Prob, Home Covers Prob
                # When midweek is empty, fields shift: [0:Home, 1:Away, 2:LineOpen, 3:LineCurrent, 4:Avg, 5:Median, 6:Std, 7:Min, 8:Max, 9:HomeWin, 10:HomeCovers]
                
                # Check if we have 11 or 12 fields
                if len(parts) == 11:
                    # No midweek line - shift fields
                    game = {
                        'home_team': parts[0] if parts[0] else '',
                        'away_team': parts[1] if parts[1] else '',
                        'line_open': parse_float(parts[2]),
                        'line_current': parse_float(parts[3]),
                        'midweek_line': None,
                        'prediction_avg': parse_float(parts[4]),
                        'prediction_median': parse_float(parts[5]),
                        'prediction_std': parse_float(parts[6]),
                        'prediction_min': parse_float(parts[7]),
                        'prediction_max': parse_float(parts[8]),
                        'home_win_probability': parse_float(parts[9]),
                        'home_covers_probability': parse_float(parts[10]),
                    }
                elif len(parts) >= 12:
                    # Has midweek line
                    game = {
                        'home_team': parts[0] if parts[0] else '',
                        'away_team': parts[1] if parts[1] else '',
                        'line_open': parse_float(parts[2]),
                        'line_current': parse_float(parts[3]),
                        'midweek_line': parse_float(parts[4]),
                        'prediction_avg': parse_float(parts[5]),
                        'prediction_median': parse_float(parts[6]),
                        'prediction_std': parse_float(parts[7]),
                        'prediction_min': parse_float(parts[8]),
                        'prediction_max': parse_float(parts[9]),
                        'home_win_probability': parse_float(parts[10]),
                        'home_covers_probability': parse_float(parts[11]),
                    }
                else:
                    continue
                games.append(game)
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse line: {line[:80]}... Error: {e}")
                continue
    
    return pd.DataFrame(games)

def load_predictions_from_text():
    """Load predictions from the provided text data"""
    predictions_text = """
	Prediction 		Prediction 	Probability

Home 	Road 	Line Open 	Line 	Midweek Line 	Prediction Avg. 	Prediction Median 	Prediction Standard Deviation 	Prediction Min 	Prediction Max 	Home Wins 	Home Covers

Air Force 	New Mexico 	0 	-2 		-1.49 	-2.38 	4.36 	-8 	12.38 	0.4642 	0.5089

Appalachian St. 	Marshall 	-3 	-3.5 		-5.02 	-4.43 	2.28 	-9.8 	-1.5 	0.3775 	0.4734

Arizona 	Baylor 	6.5 	6.5 		8.18 	9.18 	5.13 	-6 	18.13 	0.6874 	0.5288

Arkansas St. 	Louisiana-Lafayette 	3 	2.5 		2.64 	3.16 	3.22 	-6.5 	7.09 	0.5645 	0.5025

Army 	Tulsa 	10.5 	10.5 		14 	13.88 	3.15 	6.94 	20 	0.8057 	0.5608

Boise St. 	Colorado St. 	17 	16.5 		18.26 	18.46 	3.15 	13 	24.4 	0.8695 	0.5307

Bowling Green 	Akron 	3.5 	3.5 		5.54 	6.36 	2.98 	-1.42 	10.77 	0.6337 	0.5355

Buffalo 	Miami (Ohio) 	1.5 	2 		-3.03 	-3.77 	3.16 	-9.34 	3.68 	0.4261 	0.4131

Central Florida 	Oklahoma St. 	14.5 	14.5 		17.31 	16.94 	3.22 	12.23 	26.1 	0.8565 	0.5488

Cincinnati 	BYU 	-2 	-2 		-6.67 	-6.17 	1.99 	-10.5 	-3.2 	0.3391 	0.4188

Colorado 	Arizona St. 	-7.5 	-7.5 		-6.53 	-6.73 	2.61 	-12.8 	-1 	0.343 	0.5169

Florida 	Tennessee 	-3.5 	-3.5 		-4.48 	-4.1 	2.45 	-11.49 	-0.36 	0.3906 	0.4829

Florida Atlantic 	Connecticut 	-7 	-7.5 		-5.71 	-5.88 	3.02 	-12.53 	-0.59 	0.3624 	0.5311

Florida Intl. 	Jacksonville St. 	1 	-1 		-0.46 	-0.6 	2.26 	-6.5 	3.1 	0.4885 	0.5094

Fresno St. 	Utah St. 	2.5 	2.5 		4.17 	4.44 	2.52 	-0.13 	9.3 	0.6021 	0.5292

Georgia 	Charlotte 	45 	45 		46.08 	48.18 	7.19 	24.5 	55.62 	0.9958 	0.5181

Georgia Southern 	Old Dominion 	-10 	-10.5 		-8.88 	-9.92 	3.94 	-14.06 	-1 	0.2942 	0.528

Georgia Tech 	Pittsburgh 	3 	2.5 		0.85 	0.5 	3.17 	-2.94 	11 	0.5208 	0.4712

Houston 	TCU 	2 	2.5 		1.33 	1.54 	3.98 	-7 	9 	0.5322 	0.4797

Iowa 	Michigan St. 	17 	17 		21.37 	21.47 	3.59 	15.05 	29.94 	0.9046 	0.5755

Iowa St. 	Kansas 	6 	4 		7.56 	7.02 	2.86 	4.8 	18.54 	0.6797 	0.5619

James Madison 	Washington St. 	13.5 	14 		12.19 	11.25 	4.42 	6.48 	24.7 	0.7694 	0.4687

Kennesaw St. 	Missouri St. 	6.5 	6.5 		5.41 	5.95 	3.16 	-2.48 	11.56 	0.6303 	0.4809

Kent 	Central Mich. 	-8.5 	-8 		-6.92 	-6.6 	3.13 	-12.83 	-1.5 	0.3351 	0.5189

LSU 	Western Kentucky 	21.5 	21.5 		21.69 	22.74 	7 	7.5 	36.81 	0.8937 	0.5032

Louisiana Tech 	Liberty 	0 	1 		5.96 	6.33 	3.68 	-2.5 	11.29 	0.6422 	0.5855

Maryland 	Michigan 	-12 	-13.5 		-10.51 	-10.54 	3.16 	-16.1 	-3.76 	0.2588 	0.5519

Middle Tenn. 	Sam Houston St. 	6 	6.5 		4.23 	4.87 	4.34 	-6 	12.43 	0.601 	0.4608

NC St. 	Florida St. 	-5 	-4.5 		-4.78 	-4.76 	4.58 	-13.41 	4.5 	0.3865 	0.4951

North Carolina 	Duke 	-6.5 	-6.5 		-6.23 	-7.4 	3.28 	-11.64 	-1 	0.351 	0.5047

Northern Ill. 	Western Mich. 	-6 	-6.5 		-5.9 	-5.74 	3.7 	-11.59 	5 	0.3593 	0.5105

Northwestern 	Minnesota 	4 	4.5 		4.74 	5 	3.94 	-5.5 	12.53 	0.6136 	0.5042

Notre Dame 	Syracuse 	34.5 	35 		33.1 	32.67 	5.33 	22 	42.38 	0.9756 	0.4676

Ohio 	Massachusetts 	32 	32.5 		33.04 	32.56 	4.2 	25.5 	41.69 	0.9775 	0.5094

Ohio St. 	Rutgers 	33.5 	30.5 		31.42 	31.54 	6.01 	23.5 	51.21 	0.9675 	0.5157

Oklahoma 	Missouri 	9.5 	9.5 		7.09 	7.14 	3.57 	-3.5 	13 	0.6679 	0.4582

Oregon 	USC 	10 	9.5 		9.51 	8.67 	3.13 	5.59 	16.31 	0.721 	0.5002

Penn St. 	Nebraska 	10 	9.5 		7.72 	7.39 	4.29 	-0.3 	13.93 	0.68 	0.4693

Rice 	North Texas 	-17.5 	-18 		-19.46 	-19.77 	4.9 	-27.36 	-7.5 	0.1216 	0.4749

SMU 	Louisville 	3.5 	3 		5.34 	5.04 	2.69 	0.9 	11.27 	0.6294 	0.5408

San Diego St. 	San Jose St. 	11.5 	11.5 		17.39 	17.98 	5.36 	0.5 	25.65 	0.8495 	0.5998

South Alabama 	Southern Miss. 	-1.5 	-3 		-1.26 	-2.72 	5.01 	-9.94 	11.5 	0.47 	0.5299

South Carolina 	Coastal Carolina 	23 	23 		20.75 	21.91 	5.71 	7.5 	28.51 	0.8899 	0.4617

Stanford 	California 	-3 	-2.5 		-0.98 	0 	3.31 	-8.29 	3 	0.4759 	0.5264

Temple 	Tulane 	-8.5 	-8 		-7.39 	-7.48 	3.22 	-12.5 	-0.3 	0.3247 	0.5106

Texas 	Arkansas 	10 	10.5 		11.37 	10.25 	3.61 	3.5 	19.27 	0.7568 	0.5152

Texas St. 	Louisiana-Monroe 	18.5 	19 		19.6 	19.03 	3.27 	15 	24.61 	0.8858 	0.5104

Texas-San Antonio 	East Carolina 	-3 	-3 		-4.36 	-4.08 	2.95 	-11.76 	1.45 	0.3941 	0.4764

Toledo 	Ball St. 	26 	27.5 		26.13 	26.11 	5.19 	14.5 	34.44 	0.9405 	0.4764

Troy St. 	Georgia St. 	12.5 	11 		14.34 	14.02 	3.88 	6.5 	23.11 	0.8089 	0.5576

UAB 	South Florida 	-21 	-21 		-21.73 	-23.22 	5.14 	-28.07 	-6.5 	0.0972 	0.4874

UCLA 	Washington 	-10 	-10.5 		-12.07 	-11.81 	5.68 	-31.32 	-2.5 	0.2379 	0.4733

UNLV 	Hawaii 	2.5 	3.5 		3.91 	3.28 	4.04 	-1.52 	16.5 	0.594 	0.5072

UTEP 	New Mexico St. 	3 	3 		2.81 	3.05 	1.92 	-2.57 	5.92 	0.5694 	0.4966

Utah 	Kansas St. 	16.5 	16.5 		19.01 	19.31 	6.2 	-2.5 	25.5 	0.8669 	0.5425

Vanderbilt 	Kentucky 	9 	10 		10 	10.14 	2.89 	5.29 	16.2 	0.7316 	0.5

Virginia Tech 	Miami (Fla.) 	-16.5 	-17 		-20.09 	-20.83 	4.4 	-29.19 	-10.5 	0.1122 	0.4469

Wake Forest 	Delaware 	18 	17 		19.61 	20.3 	5.76 	6.5 	33.47 	0.8764 	0.5445

Wisconsin 	Illinois 	-9 	-9.5 		-8.55 	-9.31 	2.92 	-15.29 	-3.17 	0.2988 	0.5165

Wyoming 	Nevada 	7.5 	7 		7.85 	8.04 	2.91 	-0.05 	14.65 	0.686 	0.5149
"""
    
    return parse_predictions_text(predictions_text)

def integrate_predictions():
    """Integrate external predictions with our Week 13 analysis"""
    print("📥 Loading external Week 13 predictions...")
    
    # Load external predictions
    external_preds = load_predictions_from_text()
    print(f"✅ Loaded {len(external_preds)} external predictions")
    
    # Load our predictions
    our_preds_path = Path("predictions/week13/week13_comprehensive_predictions.csv")
    if our_preds_path.exists():
        our_preds = pd.read_csv(our_preds_path)
        print(f"✅ Loaded {len(our_preds)} of our predictions")
    else:
        our_preds = pd.DataFrame()
        print("⚠️  No existing predictions found")
    
    # Normalize team names for matching
    def normalize_team_name(name):
        """Normalize team names for matching"""
        name = name.strip()
        # Handle common variations
        name = name.replace("St.", "State").replace("St", "State")
        name = name.replace(" (", " ").replace(")", "")
        name = name.replace(".", "")
        return name.upper()
    
    # Add normalized team names for matching
    external_preds['home_team_norm'] = external_preds['home_team'].apply(normalize_team_name)
    external_preds['away_team_norm'] = external_preds['away_team'].apply(normalize_team_name)
    
    if len(our_preds) > 0:
        our_preds['home_team_norm'] = our_preds['home_team'].apply(normalize_team_name)
        our_preds['away_team_norm'] = our_preds['away_team'].apply(normalize_team_name)
    
    # Merge external predictions with our data
    merged = external_preds.copy()
    merged['season'] = 2025
    merged['week'] = 13
    merged['source'] = 'external'
    merged['imported_at'] = datetime.now().isoformat()
    
    # Save integrated predictions
    output_dir = Path("predictions/week13")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save external predictions
    external_path = output_dir / "week13_external_predictions.csv"
    merged.to_csv(external_path, index=False)
    print(f"✅ Saved external predictions to: {external_path}")
    
    # Create comparison if we have our predictions
    if len(our_preds) > 0:
        # Try to match games
        matches = []
        for idx, ext_row in external_preds.iterrows():
            # Try to find matching game in our predictions
            match = our_preds[
                (our_preds['home_team_norm'] == ext_row['home_team_norm']) &
                (our_preds['away_team_norm'] == ext_row['away_team_norm'])
            ]
            
            if len(match) > 0:
                our_row = match.iloc[0]
                matches.append({
                    'home_team': ext_row['home_team'],
                    'away_team': ext_row['away_team'],
                    'external_home_win_prob': ext_row['home_win_probability'],
                    'our_home_win_prob': our_row.get('home_win_probability', None),
                    'external_margin': ext_row['prediction_avg'],
                    'our_margin': our_row.get('predicted_margin', None),
                    'line_current': ext_row['line_current'],
                    'difference_home_prob': (ext_row['home_win_probability'] - our_row.get('home_win_probability', 0.5)) if 'home_win_probability' in our_row else None,
                    'difference_margin': (ext_row['prediction_avg'] - our_row.get('predicted_margin', 0)) if 'predicted_margin' in our_row else None,
                })
        
        if matches:
            comparison_df = pd.DataFrame(matches)
            comparison_path = output_dir / "week13_prediction_comparison.csv"
            comparison_df.to_csv(comparison_path, index=False)
            print(f"✅ Created comparison with {len(matches)} matched games: {comparison_path}")
    
    # Create summary
    summary = {
        'total_external_predictions': len(external_preds),
        'total_our_predictions': len(our_preds) if len(our_preds) > 0 else 0,
        'matched_games': len(matches) if len(our_preds) > 0 else 0,
        'imported_at': datetime.now().isoformat(),
        'week': 13,
        'season': 2025
    }
    
    summary_path = output_dir / "week13_import_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Saved import summary to: {summary_path}")
    
    print(f"\n📊 Summary:")
    print(f"   External predictions: {len(external_preds)}")
    print(f"   Our predictions: {len(our_preds) if len(our_preds) > 0 else 0}")
    print(f"   Matched games: {len(matches) if len(our_preds) > 0 else 0}")
    
    return merged

if __name__ == "__main__":
    integrate_predictions()

