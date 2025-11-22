#!/usr/bin/env python3
"""
Identify missing games by comparing training data against CFBD API.

This script:
1. Queries CFBD API for all FBS games (2016-2025, Week 5+ for historical, all weeks for 2025)
2. Compares against current training data
3. Identifies missing game IDs
4. Generates a report of gaps
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Set
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import cfbd
    from cfbd import ApiClient, Configuration, GamesApi
    from cfbd.rest import ApiException
except ImportError:
    print("ERROR: cfbd package not installed. Install with: pip install cfbd")
    sys.exit(1)

# Get API key
API_KEY = os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")

# Configure API (only if key is available)
api_client = None
games_api = None
if API_KEY:
    configuration = Configuration()
    configuration.access_token = API_KEY
    configuration.host = "https://api.collegefootballdata.com"
    api_client = ApiClient(configuration)
    games_api = GamesApi(api_client)

# FBS conferences
FBS_CONFERENCES = {
    'ACC', 'Big 12', 'Big Ten', 'SEC', 'Pac-12',
    'American Athletic', 'Conference USA', 'Mid-American', 
    'Mountain West', 'Sun Belt', 'FBS Independents'
}

def is_fbs_game(game) -> bool:
    """Check if game is between FBS teams."""
    home_conf = getattr(game, 'home_conference', None)
    away_conf = getattr(game, 'away_conference', None)
    
    if hasattr(home_conf, 'name'):
        home_conf = home_conf.name
    if hasattr(away_conf, 'name'):
        away_conf = away_conf.name
    
    return (home_conf in FBS_CONFERENCES) or (away_conf in FBS_CONFERENCES)

def fetch_cfbd_games(year: int, week: int = None) -> List[Dict]:
    """Fetch games from CFBD API with rate limiting."""
    try:
        time.sleep(0.17)  # Rate limit: 6 req/sec
        if week:
            games = games_api.get_games(year=year, week=week)
        else:
            games = games_api.get_games(year=year)
        
        # Filter FBS games and convert to dict
        fbs_games = []
        for game in games:
            if is_fbs_game(game):
                game_dict = {
                    'id': getattr(game, 'id', None),
                    'season': getattr(game, 'season', year),
                    'week': getattr(game, 'week', week),
                    'home_team': getattr(game, 'home_team', ''),
                    'away_team': getattr(game, 'away_team', ''),
                    'season_type': getattr(game, 'season_type', 'regular'),
                }
                fbs_games.append(game_dict)
        
        return fbs_games
    except ApiException as e:
        print(f"API error for {year} Week {week}: {e.status} - {e.reason}")
        return []
    except Exception as e:
        print(f"Error fetching {year} Week {week}: {str(e)}")
        return []

def get_expected_games() -> Dict[int, Dict[int, List[Dict]]]:
    """Get all expected FBS games from CFBD API."""
    if not games_api:
        print("WARNING: No API key available. Cannot fetch expected games from CFBD API.")
        print("Please set CFBD_API_KEY environment variable to enable full gap analysis.")
        return {}
    
    print("Fetching expected games from CFBD API...")
    expected = {}
    
    # Historical seasons: 2016-2024, Week 5+
    for year in range(2016, 2025):
        if year == 2020:  # Skip COVID year
            continue
        print(f"  Fetching {year} (Week 5+)...")
        expected[year] = {}
        
        # Fetch all games for the year, then filter by week
        all_games = fetch_cfbd_games(year)
        for game in all_games:
            week = game.get('week', 0)
            if week >= 5:
                if week not in expected[year]:
                    expected[year][week] = []
                expected[year][week].append(game)
    
    # 2025: All weeks (1-12 or more)
    print(f"  Fetching 2025 (all weeks)...")
    year = 2025
    expected[year] = {}
    all_games = fetch_cfbd_games(year)
    for game in all_games:
        week = game.get('week', 0)
        if week not in expected[year]:
            expected[year][week] = []
        expected[year][week].append(game)
    
    return expected

def load_training_data() -> pd.DataFrame:
    """Load current training data."""
    training_path = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
    if not training_path.exists():
        print(f"ERROR: Training data not found at {training_path}")
        sys.exit(1)
    
    df = pd.read_csv(training_path, low_memory=False)
    print(f"Loaded {len(df)} games from training data")
    return df

def compare_games(expected: Dict, training_df: pd.DataFrame) -> Dict:
    """Compare expected vs actual games."""
    print("\nComparing expected vs actual games...")
    
    # Get training data game IDs by season/week
    training_games = {}
    for _, row in training_df.iterrows():
        season = int(row['season'])
        week = int(row['week'])
        game_id = str(row['id']).strip()
        
        if season not in training_games:
            training_games[season] = {}
        if week not in training_games[season]:
            training_games[season][week] = set()
        training_games[season][week].add(game_id)
    
    # Compare
    missing_games = {}
    stats = {
        'expected_total': 0,
        'actual_total': len(training_df),
        'missing_total': 0,
        'by_season': {},
        'by_week': {}
    }
    
    for season, weeks in expected.items():
        season_expected = 0
        season_actual = len(training_df[training_df['season'] == season]) if season in training_df['season'].values else 0
        season_missing = 0
        
        if season not in missing_games:
            missing_games[season] = {}
        
        for week, games in weeks.items():
            week_expected = len(games)
            season_expected += week_expected
            
            # Get expected game IDs
            expected_ids = {str(g.get('id', '')).strip() for g in games if g.get('id')}
            
            # Get actual game IDs for this season/week
            actual_ids = training_games.get(season, {}).get(week, set())
            
            # Find missing
            missing_ids = expected_ids - actual_ids
            if missing_ids:
                missing_games[season][week] = [
                    g for g in games 
                    if str(g.get('id', '')).strip() in missing_ids
                ]
                season_missing += len(missing_ids)
            
            stats['by_week'][f"{season}_W{week}"] = {
                'expected': week_expected,
                'actual': len(actual_ids),
                'missing': len(missing_ids)
            }
        
        stats['by_season'][season] = {
            'expected': season_expected,
            'actual': season_actual,
            'missing': season_missing
        }
        stats['expected_total'] += season_expected
        stats['missing_total'] += season_missing
    
    return missing_games, stats

def generate_report(missing_games: Dict, stats: Dict, output_path: Path):
    """Generate detailed gap report."""
    print(f"\nGenerating report: {output_path}")
    
    with open(output_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("MISSING GAMES ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"SUMMARY:\n")
        f.write(f"  Expected Total: {stats['expected_total']:,} games\n")
        f.write(f"  Actual Total: {stats['actual_total']:,} games\n")
        f.write(f"  Missing Total: {stats['missing_total']:,} games\n")
        f.write(f"  Coverage: {(1 - stats['missing_total']/stats['expected_total'])*100:.1f}%\n\n")
        
        f.write("BY SEASON:\n")
        for season in sorted(stats['by_season'].keys()):
            s = stats['by_season'][season]
            f.write(f"  {season}: Expected {s['expected']}, Actual {s['actual']}, Missing {s['missing']}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("MISSING GAMES DETAIL:\n")
        f.write("=" * 80 + "\n\n")
        
        total_missing = 0
        for season in sorted(missing_games.keys()):
            if missing_games[season]:
                f.write(f"\n{season}:\n")
                for week in sorted(missing_games[season].keys()):
                    games = missing_games[season][week]
                    f.write(f"  Week {week}: {len(games)} missing games\n")
                    for game in games[:10]:  # Show first 10
                        f.write(f"    - ID: {game.get('id')}, {game.get('home_team')} vs {game.get('away_team')}\n")
                    if len(games) > 10:
                        f.write(f"    ... and {len(games) - 10} more\n")
                    total_missing += len(games)
        
        f.write(f"\n\nTotal missing games: {total_missing}\n")
    
    print(f"Report saved to: {output_path}")

def analyze_training_data_structure(training_df: pd.DataFrame) -> Dict:
    """Analyze training data structure to identify potential gaps."""
    print("\nAnalyzing training data structure...")
    
    analysis = {
        'total_games': len(training_df),
        'by_season': {},
        'by_week': {},
        'potential_issues': []
    }
    
    # Analyze by season
    for season in sorted(training_df['season'].unique()):
        season_df = training_df[training_df['season'] == season]
        week_counts = season_df['week'].value_counts().sort_index()
        
        analysis['by_season'][season] = {
            'total': len(season_df),
            'weeks': week_counts.to_dict(),
            'week_range': (int(season_df['week'].min()), int(season_df['week'].max()))
        }
        
        # Check for gaps in weeks
        if season < 2025:
            # Historical: should have Week 5+
            min_week = int(season_df['week'].min())
            if min_week > 5:
                analysis['potential_issues'].append(
                    f"{season}: Starts at Week {min_week}, expected Week 5+"
                )
            max_week = int(season_df['week'].max())
            if max_week < 15:
                analysis['potential_issues'].append(
                    f"{season}: Ends at Week {max_week}, may be missing postseason"
                )
    
    return analysis

def main():
    """Main execution."""
    print("=" * 80)
    print("IDENTIFYING MISSING GAMES")
    print("=" * 80)
    
    # Step 1: Load training data
    training_df = load_training_data()
    
    # Step 2: Analyze training data structure
    structure_analysis = analyze_training_data_structure(training_df)
    
    # Step 3: Get expected games from CFBD API (if API key available)
    expected = get_expected_games()
    
    if not expected:
        # No API key - provide structure analysis only
        print("\n" + "=" * 80)
        print("TRAINING DATA STRUCTURE ANALYSIS (No API Comparison)")
        print("=" * 80)
        
        output_dir = PROJECT_ROOT / 'reports'
        output_dir.mkdir(exist_ok=True)
        report_path = output_dir / 'missing_games_report.txt'
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("TRAINING DATA STRUCTURE ANALYSIS\n")
            f.write("=" * 80 + "\n\n")
            f.write("NOTE: CFBD API key not available. Full gap analysis requires API access.\n\n")
            f.write(f"Current Training Data:\n")
            f.write(f"  Total Games: {structure_analysis['total_games']:,}\n\n")
            
            f.write("By Season:\n")
            for season in sorted(structure_analysis['by_season'].keys()):
                s = structure_analysis['by_season'][season]
                f.write(f"  {season}: {s['total']} games, Weeks {s['week_range'][0]}-{s['week_range'][1]}\n")
            
            if structure_analysis['potential_issues']:
                f.write("\nPotential Issues:\n")
                for issue in structure_analysis['potential_issues']:
                    f.write(f"  - {issue}\n")
        
        print(f"\nStructure analysis saved to: {report_path}")
        print("\nTo perform full gap analysis, set CFBD_API_KEY environment variable and run again.")
        return
    
    # Step 4: Compare expected vs actual
    missing_games, stats = compare_games(expected, training_df)
    
    # Step 5: Generate report
    output_dir = PROJECT_ROOT / 'reports'
    output_dir.mkdir(exist_ok=True)
    report_path = output_dir / 'missing_games_report.txt'
    generate_report(missing_games, stats, report_path)
    
    # Step 6: Save missing games as CSV for easy processing
    missing_list = []
    for season in sorted(missing_games.keys()):
        for week in sorted(missing_games[season].keys()):
            for game in missing_games[season][week]:
                missing_list.append({
                    'id': game.get('id'),
                    'season': season,
                    'week': week,
                    'home_team': game.get('home_team'),
                    'away_team': game.get('away_team'),
                    'season_type': game.get('season_type', 'regular')
                })
    
    if missing_list:
        missing_df = pd.DataFrame(missing_list)
        csv_path = output_dir / 'missing_games.csv'
        missing_df.to_csv(csv_path, index=False)
        print(f"\nMissing games list saved to: {csv_path}")
        print(f"Total missing games: {len(missing_list)}")
    else:
        print("\nNo missing games found!")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()

