#!/usr/bin/env python3
"""
Fix Missing ELO and Talent Ratings Script

Fills missing ELO and talent ratings for games that are missing these values.
Uses historical averages or CFBD API to fill gaps.
Part of Script Ohio 2.0 data remediation pipeline.
"""

import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_historical_averages(df: pd.DataFrame) -> dict:
    """Calculate historical averages for ELO and talent by team."""
    historical = {}
    
    # Get historical data (excluding games with missing values)
    hist_df = df[
        (df['home_elo'].notna()) & 
        (df['away_elo'].notna()) &
        (df['home_talent'].notna()) & 
        (df['away_talent'].notna())
    ].copy()
    
    # Calculate team averages
    all_teams = set(hist_df['home_team'].unique()) | set(hist_df['away_team'].unique())
    
    for team in all_teams:
        home_games = hist_df[hist_df['home_team'] == team]
        away_games = hist_df[hist_df['away_team'] == team]
        
        elo_values = []
        talent_values = []
        
        if len(home_games) > 0:
            elo_values.extend(home_games['home_elo'].dropna().tolist())
            talent_values.extend(home_games['home_talent'].dropna().tolist())
        
        if len(away_games) > 0:
            elo_values.extend(away_games['away_elo'].dropna().tolist())
            talent_values.extend(away_games['away_talent'].dropna().tolist())
        
        historical[team] = {
            'elo': pd.Series(elo_values).mean() if elo_values else 1500.0,
            'talent': pd.Series(talent_values).mean() if talent_values else 500.0
        }
    
    return historical


def fetch_elo_talent_from_cfbd(team: str, season: int) -> dict:
    """Fetch ELO and talent from CFBD API if available."""
    try:
        from starter_pack.utils.cfbd_helpers import cfbd_session
        import os
        
        api_key = os.environ.get('CFBD_API_KEY')
        if not api_key:
            return None
        
        with cfbd_session() as session:
            # Try to get team talent
            try:
                teams_api = session.teams_api
                teams = teams_api.get_teams(year=season)
                
                for t in teams:
                    if t.school == team:
                        # Get ELO from ratings endpoint if available
                        return {
                            'talent': getattr(t, 'talent', None),
                            'elo': None  # Would need separate API call
                        }
            except:
                pass
    except Exception as e:
        pass
    
    return None


def fix_missing_elo_talent():
    """Fix missing ELO and talent ratings."""
    training_file = project_root / "model_pack" / "updated_training_data.csv"
    backup_file = project_root / "model_pack" / "updated_training_data.csv.backup2"
    
    if not training_file.exists():
        print("❌ Training data file not found")
        return False
    
    print("📊 Loading training data...")
    df = pd.read_csv(training_file, low_memory=False)
    
    # Find games with missing values
    missing_elo = df[(df['home_elo'].isna()) | (df['away_elo'].isna())].copy()
    missing_talent = df[(df['home_talent'].isna()) | (df['away_talent'].isna())].copy()
    
    if len(missing_elo) == 0 and len(missing_talent) == 0:
        print("✅ No games with missing ELO or talent ratings found")
        return True
    
    print(f"\n🔍 Found {len(missing_elo)} games with missing ELO ratings")
    print(f"🔍 Found {len(missing_talent)} games with missing talent ratings")
    
    # Create backup if first backup doesn't exist
    if not backup_file.exists():
        backup_file_orig = project_root / "model_pack" / "updated_training_data.csv.backup"
        if backup_file_orig.exists():
            import shutil
            shutil.copy(backup_file_orig, backup_file)
        else:
            df.to_csv(backup_file, index=False)
            print(f"💾 Created backup: {backup_file}")
    
    # Get historical averages
    print("\n📊 Calculating historical averages...")
    historical = get_historical_averages(df)
    print(f"   Calculated averages for {len(historical)} teams")
    
    fixed_elo = 0
    fixed_talent = 0
    
    print("\n🔧 Fixing missing values...")
    
    # Fix missing ELO
    for idx, row in missing_elo.iterrows():
        if pd.isna(row['home_elo']):
            home_team = row['home_team']
            if home_team in historical:
                df.at[idx, 'home_elo'] = historical[home_team]['elo']
                fixed_elo += 1
        
        if pd.isna(row['away_elo']):
            away_team = row['away_team']
            if away_team in historical:
                df.at[idx, 'away_elo'] = historical[away_team]['elo']
                fixed_elo += 1
    
    # Fix missing talent
    for idx, row in missing_talent.iterrows():
        if pd.isna(row['home_talent']):
            home_team = row['home_team']
            if home_team in historical:
                df.at[idx, 'home_talent'] = historical[home_team]['talent']
                fixed_talent += 1
        
        if pd.isna(row['away_talent']):
            away_team = row['away_team']
            if away_team in historical:
                df.at[idx, 'away_talent'] = historical[away_team]['talent']
                fixed_talent += 1
    
    # Save fixed data
    print(f"\n💾 Saving fixed data to: {training_file}")
    df.to_csv(training_file, index=False)
    
    print("\n✅ Summary:")
    print(f"   Missing ELO fixed: {fixed_elo}")
    print(f"   Missing talent fixed: {fixed_talent}")
    
    # Verify fix
    remaining_elo = df[(df['home_elo'].isna()) | (df['away_elo'].isna())].shape[0]
    remaining_talent = df[(df['home_talent'].isna()) | (df['away_talent'].isna())].shape[0]
    
    if remaining_elo == 0 and remaining_talent == 0:
        print("\n✅ All missing ELO and talent ratings fixed!")
        return True
    else:
        print(f"\n⚠️ {remaining_elo} ELO missing, {remaining_talent} talent missing (may need manual review)")
        return False


if __name__ == "__main__":
    success = fix_missing_elo_talent()
    sys.exit(0 if success else 1)



