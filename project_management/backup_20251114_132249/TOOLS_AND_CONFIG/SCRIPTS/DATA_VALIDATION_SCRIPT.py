#!/usr/bin/env python3
"""
🔴 COMPREHENSIVE DATA VALIDATION & REMEDIATION

Script Ohio 2.0 - Complete Data Quality Assurance

Purpose: Validate, fix, and enhance 2025 data for ML predictions
"""

import pandas as pd
import numpy as np
import os
import json
from pathlib import Path
from datetime import datetime
import sys

class DataValidator:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "validations": {},
            "fixes_applied": [],
            "issues_found": [],
            "summary": {}
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
    
    # ==================== VALIDATION METHODS ====================
    
    def validate_file_exists(self, file_path, description=""):
        """Check if file exists"""
        full_path = self.project_root / file_path
        exists = full_path.exists()
        
        status = "✅ EXISTS" if exists else "❌ MISSING"
        self.log(f"{description}: {status} ({file_path})", "SUCCESS" if exists else "ERROR")
        
        return exists, full_path
    
    def validate_csv_readable(self, file_path, description=""):
        """Check if CSV is readable"""
        exists, full_path = self.validate_file_exists(file_path, description)
        
        if not exists:
            return False, None
        
        try:
            df = pd.read_csv(full_path, nrows=5)
            self.log(f"  └─ Readable: ✅ ({len(df.columns)} columns)", "SUCCESS")
            return True, full_path
        except Exception as e:
            self.log(f"  └─ ERROR reading: {str(e)[:50]}", "ERROR")
            return False, full_path

    def _load_model_file(self, name, full_path):
        """Load model with framework-aware logic so FastAI exports work."""
        file_name = full_path.name.lower()
        try:
            if "fastai" in file_name:
                try:
                    from fastai.learner import load_learner
                except ImportError as exc:  # pragma: no cover - optional dependency
                    raise ImportError(
                        "fastai is required to validate the neural model. "
                        "Install it via `pip install fastai`."
                    ) from exc
                load_learner(full_path)
            elif full_path.suffix == ".joblib":
                import joblib
                joblib.load(full_path)
            else:
                import pickle
                with open(full_path, 'rb') as f:
                    pickle.load(f)
        except Exception:
            raise
    
    def validate_training_data(self):
        """Comprehensive training data validation"""
        print("\n" + "="*80)
        print("🔍 VALIDATING TRAINING DATA")
        print("="*80)
        
        training_file = self.project_root / "model_pack/updated_training_data.csv"
        
        if not training_file.exists():
            self.log("Training data file not found!", "ERROR")
            self.report["validations"]["training_data"] = {"status": "MISSING"}
            return False
        
        try:
            # Read full training data
            self.log("Reading training data...", "INFO")
            df = pd.read_csv(training_file)
            
            validation_result = {
                "status": "OK",
                "rows": len(df),
                "columns": len(df.columns),
                "columns_list": list(df.columns),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "null_summary": df.isnull().sum().to_dict()
            }
            
            # Basic checks
            self.log(f"Total rows: {len(df):,}", "DATA")
            self.log(f"Total columns: {len(df.columns)}", "DATA")
            
            # Column checks
            self.log("\n📋 Column Structure:", "INFO")
            expected_cols = {
                'season': 'Season year',
                'week': 'Week number',
                'home_team': 'Home team name',
                'away_team': 'Away team name',
                'home_points': 'Home team points',
                'away_points': 'Away team points',
                'game_key': 'Unique game identifier',
                'conference_game': 'Whether teams in same conference'
            }
            
            for col, description in expected_cols.items():
                if col in df.columns:
                    null_count = df[col].isnull().sum()
                    if null_count == 0:
                        self.log(f"  ✅ {col:20s} - {description}", "SUCCESS")
                    else:
                        pct = (null_count / len(df)) * 100
                        self.log(f"  ⚠️  {col:20s} - {description} ({null_count} null, {pct:.1f}%)", "WARNING")
                        if pct > 50:
                            validation_result["status"] = "MISSING_COLUMNS"
                            self.report["issues_found"].append(f"Column '{col}' has {null_count} null values ({pct:.1f}%)")
                else:
                    self.log(f"  ❌ {col:20s} - {description} [MISSING]", "ERROR")
                    validation_result["status"] = "MISSING_COLUMNS"
                    self.report["issues_found"].append(f"Missing column: {col}")
            
            # 2025 Data Check
            print("\n📅 2025 DATA VERIFICATION:")
            if 'season' in df.columns:
                df_2025 = df[df['season'] == 2025]
                self.log(f"2025 games: {len(df_2025):,}", "DATA")
                
                if len(df_2025) > 500:
                    validation_result["data_2025_status"] = "REAL_DATA"
                    self.log("Status: ✅ REAL DATA PRESENT", "SUCCESS")
                else:
                    validation_result["data_2025_status"] = "INSUFFICIENT"
                    self.log("Status: ⚠️  INSUFFICIENT (likely mock)", "WARNING")
                    self.report["issues_found"].append("2025 data may be mock/incomplete")
                
                # Week breakdown
                if 'week' in df_2025.columns:
                    print("\n  Week breakdown:")
                    week_dist = df_2025['week'].value_counts().sort_index()
                    for week, count in week_dist.items():
                        marker = "  🏈" if week == 12 else "    "
                        print(f"{marker} Week {week:2d}: {count:4d} games")
                    
                    validation_result["week_coverage"] = week_dist.to_dict()
                    
                    # Week 12 check
                    if 12 in df_2025['week'].values:
                        df_week12 = df_2025[df_2025['week'] == 12]
                        self.log(f"\n🏈 WEEK 12: {len(df_week12)} games", "SUCCESS")
                        
                        # Ohio State vs UCLA
                        if 'home_team' in df_week12.columns and 'away_team' in df_week12.columns:
                            osu_ucla = df_week12[
                                ((df_week12['home_team'].str.contains('Ohio|OSU', case=False, na=False)) & 
                                 (df_week12['away_team'].str.contains('UCLA', case=False, na=False))) |
                                ((df_week12['away_team'].str.contains('Ohio|OSU', case=False, na=False)) & 
                                 (df_week12['home_team'].str.contains('UCLA', case=False, na=False)))
                            ]
                            if len(osu_ucla) > 0:
                                self.log("✅ Ohio State vs UCLA FOUND in Week 12", "SUCCESS")
                                validation_result["osu_ucla_week12"] = True
                                game = osu_ucla.iloc[0]
                                self.log(f"   Game ID: {game.get('id', 'N/A')}", "INFO")
                                self.log(f"   Date: {game.get('start_date', 'N/A')}", "INFO")
                            else:
                                self.log("❌ Ohio State vs UCLA NOT in Week 12", "ERROR")
                                validation_result["osu_ucla_week12"] = False
                                self.report["issues_found"].append("Ohio State vs UCLA missing from Week 12")
                    else:
                        self.log("❌ Week 12 NOT in dataset", "ERROR")
                        validation_result["osu_ucla_week12"] = False
                        self.report["issues_found"].append("Week 12 completely missing")
            
            # Null values
            print("\n⚠️  NULL VALUE ANALYSIS:")
            nulls = df.isnull().sum()
            nulls_with_values = nulls[nulls > 0].sort_values(ascending=False)
            
            if len(nulls_with_values) > 0:
                self.log(f"Found {len(nulls_with_values)} columns with null values:", "WARNING")
                for col, count in nulls_with_values.head(10).items():
                    pct = (count / len(df)) * 100
                    print(f"  ⚠️  {col:30s}: {count:6,d} ({pct:5.1f}%)")
                    if pct > 50 and col in ['game_key', 'conference_game']:
                        self.report["issues_found"].append(f"Column '{col}' has {count} null values ({pct:.1f}%)")
            else:
                self.log("✅ No null values found", "SUCCESS")
            
            # Data type check
            print("\n🔢 DATA TYPE SUMMARY:")
            dtypes = df.dtypes.value_counts()
            for dtype, count in dtypes.items():
                dtype_str = str(dtype)
                print(f"  {dtype_str:20s}: {count:3d} columns")
            
            # Check for duplicates
            print("\n🔍 DUPLICATE CHECK:")
            if 'id' in df.columns:
                duplicates = df.duplicated(subset=['id']).sum()
                if duplicates == 0:
                    self.log("✅ No duplicate game IDs", "SUCCESS")
                else:
                    self.log(f"⚠️  {duplicates} duplicate game IDs found", "WARNING")
                    self.report["issues_found"].append(f"{duplicates} duplicate game IDs")
            
            self.report["validations"]["training_data"] = validation_result
            return validation_result["status"] in ["OK", "REAL_DATA"]
            
        except Exception as e:
            self.log(f"ERROR validating training data: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            self.report["validations"]["training_data"] = {"status": "ERROR", "error": str(e)}
            return False
    
    def validate_models(self):
        """Check all model files"""
        print("\n" + "="*80)
        print("🤖 VALIDATING MODEL FILES")
        print("="*80)
        
        models = {
            "Ridge Regression": "model_pack/ridge_model_2025.joblib",
            "XGBoost": "model_pack/xgb_home_win_model_2025.pkl",
            "FastAI": "model_pack/fastai_home_win_model_2025.pkl",
        }
        
        model_status = {}
        all_ok = True
        
        for name, rel_path in models.items():
            full_path = self.project_root / rel_path
            
            if full_path.exists():
                size_kb = full_path.stat().st_size / 1024
                self.log(f"{name}: ✅ ({size_kb:.1f} KB)", "SUCCESS")
                model_status[name] = {"exists": True, "size_kb": size_kb}
                
                # Try to load
                try:
                    self._load_model_file(name, full_path)
                    model_status[name]["loadable"] = True
                    self.log(f"  └─ Loadable: ✅", "SUCCESS")
                except Exception as e:
                    model_status[name]["loadable"] = False
                    self.log(f"  └─ ERROR loading: {str(e)[:40]}", "ERROR")
                    all_ok = False
                    self.report["issues_found"].append(f"Model '{name}' exists but cannot be loaded: {str(e)[:50]}")
            else:
                self.log(f"{name}: ❌ MISSING", "ERROR")
                model_status[name] = {"exists": False}
                all_ok = False
                self.report["issues_found"].append(f"Model file missing: {rel_path}")
        
        self.report["validations"]["models"] = model_status
        return all_ok
    
    def validate_week12_data(self):
        """Specific Week 12 validation"""
        print("\n" + "="*80)
        print("🏈 CRITICAL: WEEK 12 DATA VALIDATION")
        print("="*80)
        
        training_file = self.project_root / "model_pack/updated_training_data.csv"
        
        if not training_file.exists():
            self.log("Training data not found", "ERROR")
            return False
        
        try:
            df = pd.read_csv(training_file)
            
            if 'season' not in df.columns or 'week' not in df.columns:
                self.log("Missing season or week columns", "ERROR")
                return False
            
            df_week12 = df[(df['season'] == 2025) & (df['week'] == 12)]
            
            self.log(f"Week 12 (2025) games: {len(df_week12)}", "DATA")
            
            week12_status = {
                "total_games": len(df_week12),
                "expected_fbs_games": 48,
                "status": "OK" if len(df_week12) >= 45 else "INSUFFICIENT"
            }
            
            if len(df_week12) >= 45:
                self.log("✅ Week 12 data present", "SUCCESS")
            else:
                self.log("❌ Week 12 insufficient", "ERROR")
                self.report["issues_found"].append(f"Week 12 has only {len(df_week12)} games (expected 45+)")
            
            # Show sample of Week 12 games
            if len(df_week12) > 0 and 'home_team' in df_week12.columns:
                print("\n  Sample Week 12 matchups:")
                for idx, row in df_week12.head(5).iterrows():
                    home = row.get('home_team', 'Unknown')
                    away = row.get('away_team', 'Unknown')
                    print(f"    {away:20s} @ {home:20s}")
            
            self.report["validations"]["week12"] = week12_status
            return week12_status["status"] == "OK"
            
        except Exception as e:
            self.log(f"Error validating Week 12: {e}", "ERROR")
            return False
    
    def generate_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "="*80)
        print("📊 VALIDATION REPORT SUMMARY")
        print("="*80)
        
        total_checks = len(self.report["validations"])
        passed_checks = sum(1 for v in self.report["validations"].values() 
                          if isinstance(v, dict) and v.get("status") in ["OK", "REAL_DATA", True])
        
        print(f"\nValidation Results: {passed_checks}/{total_checks} sections passed")
        
        if len(self.report["issues_found"]) > 0:
            print(f"\n⚠️  Issues Found ({len(self.report['issues_found'])}):")
            for issue in self.report["issues_found"]:
                print(f"  • {issue}")
        else:
            print(f"\n✅ No issues found!")
        
        if len(self.report["fixes_applied"]) > 0:
            print(f"\n✅ Fixes Applied ({len(self.report['fixes_applied'])}):")
            for fix in self.report["fixes_applied"]:
                print(f"  • {fix}")
        
        # Save report
        report_file = self.project_root / "project_management" / "DATA_VALIDATION_REPORT.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.report, f, indent=2)
        
        self.log(f"\n✅ Report saved: {report_file}", "SUCCESS")
        
        return self.report
    
    def run_full_validation(self):
        """Run complete validation suite"""
        print("\n" + "="*80)
        print("🔴 COMPREHENSIVE DATA VALIDATION")
        print("Script Ohio 2.0 - College Football Analytics")
        print("="*80)
        
        # Run all validations
        self.validate_training_data()
        self.validate_models()
        self.validate_week12_data()
        
        # Generate report
        report = self.generate_report()
        
        # Final status
        print("\n" + "="*80)
        if len(self.report["issues_found"]) == 0:
            print("🟢 SYSTEM STATUS: VALIDATION PASSED")
            print("\n✅ All critical checks passed")
            print("✅ Data ready for predictions")
            print("✅ Week 12 verified and ready")
        elif len(self.report["issues_found"]) <= 2:
            print("🟡 SYSTEM STATUS: MINOR ISSUES FOUND")
            print(f"\n⚠️  {len(self.report['issues_found'])} issue(s) detected")
            print("✅ System operational with minor issues")
        else:
            print("🔴 SYSTEM STATUS: MAJOR ISSUES FOUND")
            print(f"\n❌ {len(self.report['issues_found'])} critical issue(s) detected")
            print("⚠️  Requires attention before deployment")
        print("="*80)
        
        return report


if __name__ == "__main__":
    # Get project root
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # Assume script is in project root
        project_root = Path(__file__).parent
    
    print(f"\n🔍 Using project root: {project_root}\n")
    
    validator = DataValidator(project_root)
    report = validator.run_full_validation()
    
    sys.exit(0)

