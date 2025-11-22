#!/usr/bin/env python3
"""
🔧 DATA REMEDIATION SCRIPT

Script Ohio 2.0 - Fix and Enhance Data Quality

Purpose: Fix missing columns, validate features, and enhance data quality
"""

import pandas as pd
import numpy as np
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import sys

class DataRemediator:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.training_file = self.project_root / "model_pack/updated_training_data.csv"
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "fixes_applied": [],
            "summary": {},
            "backup_file": None
        }
    
    def log(self, message, level="INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
            "DATA": "📊"
        }.get(level, "→ ")
        print(f"{prefix} [{timestamp}] {message}")
    
    def create_backup(self):
        """Create backup of training data before modifications"""
        if not self.training_file.exists():
            self.log("Training data file not found - cannot create backup", "ERROR")
            return False
        
        backup_dir = self.training_file.parent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"updated_training_data_BACKUP_{timestamp}.csv"
        
        try:
            shutil.copy(self.training_file, backup_file)
            self.report["backup_file"] = str(backup_file)
            self.log(f"Backup created: {backup_file.name}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"ERROR creating backup: {e}", "ERROR")
            return False
    
    def fix_missing_columns(self, df):
        """Fix missing game_key and conference_game columns"""
        print("\n" + "="*80)
        print("🔧 FIXING MISSING COLUMNS")
        print("="*80)
        
        fixes_applied = []
        
        # Fix game_key
        if 'game_key' not in df.columns or df['game_key'].isnull().all():
            self.log("Creating game_key column...", "INFO")
            df['game_key'] = df.apply(
                lambda row: f"{row['season']}_{row['week']}_{row['home_team'].replace(' ', '_')}_{row['away_team'].replace(' ', '_')}",
                axis=1
            )
            fixes_applied.append("Created game_key column")
            self.log("✅ game_key created", "SUCCESS")
        elif df['game_key'].isnull().sum() > 0:
            # Fill missing game_key values
            missing_mask = df['game_key'].isnull()
            df.loc[missing_mask, 'game_key'] = df[missing_mask].apply(
                lambda row: f"{row['season']}_{row['week']}_{row['home_team'].replace(' ', '_')}_{row['away_team'].replace(' ', '_')}",
                axis=1
            )
            fixes_applied.append(f"Filled {missing_mask.sum()} missing game_key values")
            self.log(f"✅ Filled {missing_mask.sum()} missing game_key values", "SUCCESS")
        else:
            self.log("✅ game_key already populated", "SUCCESS")
        
        # Fix conference_game
        if 'conference_game' not in df.columns or df['conference_game'].isnull().all():
            self.log("Creating conference_game column...", "INFO")
            df['conference_game'] = (
                df['home_conference'].notna() & 
                df['away_conference'].notna() &
                (df['home_conference'] == df['away_conference'])
            )
            fixes_applied.append("Created conference_game column")
            self.log("✅ conference_game created", "SUCCESS")
        elif df['conference_game'].isnull().sum() > 0:
            # Fill missing conference_game values
            missing_mask = df['conference_game'].isnull()
            df.loc[missing_mask, 'conference_game'] = (
                df.loc[missing_mask, 'home_conference'].notna() & 
                df.loc[missing_mask, 'away_conference'].notna() &
                (df.loc[missing_mask, 'home_conference'] == df.loc[missing_mask, 'away_conference'])
            )
            fixes_applied.append(f"Filled {missing_mask.sum()} missing conference_game values")
            self.log(f"✅ Filled {missing_mask.sum()} missing conference_game values", "SUCCESS")
        else:
            self.log("✅ conference_game already populated", "SUCCESS")
        
        self.report["fixes_applied"].extend(fixes_applied)
        return df, fixes_applied
    
    def validate_model_features(self, df):
        """Validate all required model features are present"""
        print("\n" + "="*80)
        print("🔍 VALIDATING MODEL FEATURES")
        print("="*80)
        
        # Ridge features
        ridge_features = [
            'home_talent', 'away_talent', 'home_elo', 'away_elo',
            'home_adjusted_epa', 'home_adjusted_epa_allowed',
            'away_adjusted_epa', 'away_adjusted_epa_allowed'
        ]
        
        print("\nRidge Regression Features:")
        ridge_ok = True
        for feat in ridge_features:
            if feat in df.columns:
                missing = df[feat].isnull().sum()
                if missing == 0:
                    self.log(f"  ✅ {feat}", "SUCCESS")
                else:
                    self.log(f"  ⚠️  {feat} ({missing} missing)", "WARNING")
                    ridge_ok = False
            else:
                self.log(f"  ❌ {feat} - MISSING", "ERROR")
                ridge_ok = False
        
        # XGBoost features
        xgb_features = [
            'home_talent', 'away_talent', 'spread', 'home_elo', 'away_elo',
            'home_adjusted_epa', 'home_adjusted_epa_allowed',
            'away_adjusted_epa', 'away_adjusted_epa_allowed',
            'home_adjusted_success', 'home_adjusted_success_allowed',
            'away_adjusted_success', 'away_adjusted_success_allowed'
        ]
        
        print("\nXGBoost Features:")
        xgb_ok = True
        for feat in xgb_features:
            if feat in df.columns:
                missing = df[feat].isnull().sum()
                if missing == 0:
                    self.log(f"  ✅ {feat}", "SUCCESS")
                else:
                    self.log(f"  ⚠️  {feat} ({missing} missing)", "WARNING")
                    if feat != 'spread':  # Spread can be 0.0
                        xgb_ok = False
            else:
                self.log(f"  ❌ {feat} - MISSING", "ERROR")
                xgb_ok = False
        
        # Opponent-adjusted features count
        adj_features = [col for col in df.columns if 'adjusted' in col]
        print(f"\nOpponent-Adjusted Features: {len(adj_features)} total")
        
        self.report["summary"]["ridge_features_ok"] = ridge_ok
        self.report["summary"]["xgb_features_ok"] = xgb_ok
        self.report["summary"]["opponent_adj_features"] = len(adj_features)
        
        return ridge_ok and xgb_ok
    
    def validate_team_names(self, df):
        """Validate team name consistency"""
        print("\n" + "="*80)
        print("🔍 VALIDATING TEAM NAMES")
        print("="*80)
        
        df_2025 = df[df['season'] == 2025]
        teams_2025 = set(df_2025['home_team'].unique()) | set(df_2025['away_team'].unique())
        
        self.log(f"2025 unique teams: {len(teams_2025)}", "DATA")
        self.log(f"Expected FBS teams: ~122", "INFO")
        
        if len(teams_2025) >= 120 and len(teams_2025) <= 130:
            self.log("✅ Team count in expected range", "SUCCESS")
        else:
            self.log(f"⚠️  Team count outside expected range", "WARNING")
        
        return True
    
    def validate_conferences(self, df):
        """Validate conference data"""
        print("\n" + "="*80)
        print("🔍 VALIDATING CONFERENCE DATA")
        print("="*80)
        
        df_2025 = df[df['season'] == 2025]
        
        home_conf_missing = df_2025['home_conference'].isnull().sum()
        away_conf_missing = df_2025['away_conference'].isnull().sum()
        
        if home_conf_missing == 0 and away_conf_missing == 0:
            self.log("✅ All games have conference data", "SUCCESS")
        else:
            self.log(f"⚠️  Missing conference data: Home={home_conf_missing}, Away={away_conf_missing}", "WARNING")
        
        # Check conference_game calculation
        if 'conference_game' in df_2025.columns:
            conf_games = df_2025['conference_game'].sum()
            self.log(f"Conference games: {conf_games}/{len(df_2025)}", "DATA")
        
        return True
    
    def run_remediation(self):
        """Run complete remediation process"""
        print("\n" + "="*80)
        print("🔧 DATA REMEDIATION")
        print("Script Ohio 2.0 - College Football Analytics")
        print("="*80)
        
        if not self.training_file.exists():
            self.log("Training data file not found!", "ERROR")
            return False
        
        # Create backup
        if not self.create_backup():
            self.log("WARNING: Proceeding without backup", "WARNING")
        
        try:
            # Load data
            self.log("Loading training data...", "INFO")
            df = pd.read_csv(self.training_file)
            self.log(f"Loaded {len(df):,} games, {len(df.columns)} columns", "DATA")
            
            # Apply fixes
            df, fixes = self.fix_missing_columns(df)
            
            # Validate features
            features_ok = self.validate_model_features(df)
            
            # Validate team names
            self.validate_team_names(df)
            
            # Validate conferences
            self.validate_conferences(df)
            
            # Save fixed data
            self.log("\nSaving fixed data...", "INFO")
            df.to_csv(self.training_file, index=False)
            self.log(f"✅ Data saved: {self.training_file}", "SUCCESS")
            
            # Update report
            self.report["summary"]["rows"] = len(df)
            self.report["summary"]["columns"] = len(df.columns)
            self.report["summary"]["fixes_applied"] = len(fixes)
            
            # Save report
            report_file = self.project_root / "project_management" / "DATA_REMEDIATION_REPORT.json"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(self.report, f, indent=2)
            
            self.log(f"✅ Report saved: {report_file}", "SUCCESS")
            
            # Final summary
            print("\n" + "="*80)
            print("🟢 REMEDIATION COMPLETE")
            print("="*80)
            print(f"✅ Fixes applied: {len(fixes)}")
            for fix in fixes:
                print(f"  • {fix}")
            print(f"\n✅ Dataset ready:")
            print(f"  • Rows: {len(df):,}")
            print(f"  • Columns: {len(df.columns)}")
            print(f"  • Ridge features: {'OK' if features_ok else 'ISSUES'}")
            print(f"  • Opponent-adjusted features: {self.report['summary'].get('opponent_adj_features', 'N/A')}")
            print("="*80)
            
            return True
            
        except Exception as e:
            self.log(f"ERROR during remediation: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    # Get project root
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = Path(__file__).parent
    
    print(f"\n🔧 Using project root: {project_root}\n")
    
    remediator = DataRemediator(project_root)
    success = remediator.run_remediation()
    
    sys.exit(0 if success else 1)

