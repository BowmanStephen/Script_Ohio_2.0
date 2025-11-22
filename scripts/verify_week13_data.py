#!/usr/bin/env python3
"""
Week 13 Data Verification Script
================================

Verifies Week 13 data completeness in starter pack, migration status,
features generation, and prediction model usage.

Usage:
    python scripts/verify_week13_data.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Output directory
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


class Week13DataVerifier:
    """Verify Week 13 data across all systems"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.reports_dir = REPORTS_DIR
        
        # File paths
        self.starter_games = self.project_root / "starter_pack" / "data" / "games.csv"
        self.model_pack_path = self.project_root / "model_pack"
        self.week13_data_dir = self.project_root / "data" / "week13" / "enhanced"
        self.week13_analysis_dir = self.project_root / "analysis" / "week13"
        self.week13_predictions_dir = self.project_root / "predictions" / "week13"
        
        # Results storage
        self.verification_results = {
            "verification_date": datetime.now().isoformat(),
            "season": 2025,
            "week": 13,
            "checks": {},
            "summary": {}
        }
    
    def verify_starter_pack_data(self) -> Dict[str, Any]:
        """Verify Week 13 data in starter pack"""
        print("\n" + "=" * 80)
        print("CHECK 1: VERIFYING STARTER PACK WEEK 13 DATA")
        print("=" * 80)
        
        if not self.starter_games.exists():
            print(f"❌ Starter pack games file not found: {self.starter_games}")
            return {"status": "error", "message": "File not found"}
        
        games_df = pd.read_csv(self.starter_games, low_memory=False)
        
        # Filter for 2025, week 13
        week13_games = games_df[
            (games_df['season'] == 2025) & 
            (games_df['week'] == 13)
        ].copy()
        
        # Get game IDs
        game_ids = set(week13_games['id'].dropna().astype(int).unique())
        
        # Check for scores
        games_with_scores = week13_games[
            week13_games['home_points'].notna() & 
            week13_games['away_points'].notna()
        ]
        
        # Check for FBS teams only
        fbs_games = week13_games[
            (week13_games['home_classification'] == 'fbs') &
            (week13_games['away_classification'] == 'fbs')
        ]
        
        result = {
            "status": "complete" if len(week13_games) > 0 else "missing",
            "total_games": len(week13_games),
            "fbs_games": len(fbs_games),
            "unique_game_ids": len(game_ids),
            "games_with_scores": len(games_with_scores),
            "games_without_scores": len(week13_games) - len(games_with_scores),
            "game_ids": sorted(list(game_ids)),
            "teams": {
                "home_teams": sorted(week13_games['home_team'].dropna().unique().tolist()),
                "away_teams": sorted(week13_games['away_team'].dropna().unique().tolist())
            }
        }
        
        print(f"Found {len(week13_games)} Week 13 games")
        print(f"FBS games: {len(fbs_games)}")
        print(f"Games with scores: {len(games_with_scores)}")
        
        if len(week13_games) == 0:
            print("⚠️  No Week 13 games found in starter pack")
        else:
            print("✅ Week 13 games present in starter pack")
        
        self.verification_results["checks"]["starter_pack"] = result
        return result
    
    def verify_migration_status(self) -> Dict[str, Any]:
        """Check if Week 13 data has been migrated"""
        print("\n" + "=" * 80)
        print("CHECK 2: VERIFYING MIGRATION STATUS")
        print("=" * 80)
        
        # Check for migrated files containing Week 13
        migrated_files = list(self.model_pack_path.glob("*2025*weeks*migrated.csv"))
        migrated_files.extend(list(self.model_pack_path.glob("*2025*migrated.csv")))
        
        week13_in_migration = False
        week13_game_count = 0
        
        for migrated_file in migrated_files:
            try:
                df = pd.read_csv(migrated_file, low_memory=False)
                week13_data = df[(df['season'] == 2025) & (df['week'] == 13)]
                if len(week13_data) > 0:
                    week13_in_migration = True
                    week13_game_count = len(week13_data)
                    print(f"✅ Found Week 13 data in: {migrated_file.name}")
                    print(f"   Games: {week13_game_count}")
                    break
            except Exception as e:
                print(f"⚠️  Error reading {migrated_file.name}: {e}")
        
        # Check training data
        training_data = self.model_pack_path / "updated_training_data.csv"
        week13_in_training = False
        training_week13_count = 0
        
        if training_data.exists():
            try:
                df = pd.read_csv(training_data, low_memory=False)
                week13_training = df[(df['season'] == 2025) & (df['week'] == 13)]
                if len(week13_training) > 0:
                    week13_in_training = True
                    training_week13_count = len(week13_training)
                    print(f"✅ Found Week 13 data in training data")
                    print(f"   Games: {training_week13_count}")
            except Exception as e:
                print(f"⚠️  Error reading training data: {e}")
        
        result = {
            "status": "migrated" if week13_in_migration else "not_migrated",
            "in_migration_file": week13_in_migration,
            "migration_game_count": week13_game_count,
            "in_training_data": week13_in_training,
            "training_game_count": training_week13_count
        }
        
        if not week13_in_migration:
            print("⚠️  Week 13 data not found in migrated files")
        if not week13_in_training:
            print("⚠️  Week 13 data not found in training data")
        
        self.verification_results["checks"]["migration"] = result
        return result
    
    def verify_features_generation(self) -> Dict[str, Any]:
        """Verify Week 13 features have been generated"""
        print("\n" + "=" * 80)
        print("CHECK 3: VERIFYING FEATURES GENERATION")
        print("=" * 80)
        
        if not self.week13_data_dir.exists():
            print(f"⚠️  Week 13 data directory not found: {self.week13_data_dir}")
            return {"status": "error", "message": "Directory not found"}
        
        # Check for required files
        required_files = {
            "enhanced_games": self.week13_data_dir / "week13_enhanced_games.csv",
            "features_86": self.week13_data_dir / "week13_features_86.csv",
            "features_model_compatible": self.week13_data_dir / "week13_features_86_model_compatible.csv"
        }
        
        file_status = {}
        for file_type, file_path in required_files.items():
            exists = file_path.exists()
            file_status[file_type] = {
                "exists": exists,
                "path": str(file_path)
            }
            
            if exists:
                try:
                    df = pd.read_csv(file_path, low_memory=False)
                    file_status[file_type]["row_count"] = len(df)
                    file_status[file_type]["columns"] = len(df.columns)
                    print(f"✅ {file_type}: {len(df)} rows, {len(df.columns)} columns")
                except Exception as e:
                    file_status[file_type]["error"] = str(e)
                    print(f"⚠️  {file_type}: Error reading file - {e}")
            else:
                print(f"❌ {file_type}: File not found")
        
        # Check if features have 86 columns
        features_86_path = required_files["features_86"]
        has_86_features = False
        if features_86_path.exists():
            try:
                df = pd.read_csv(features_86_path, low_memory=False)
                has_86_features = len(df.columns) == 86
                if has_86_features:
                    print("✅ Features file has 86 columns (correct)")
                else:
                    print(f"⚠️  Features file has {len(df.columns)} columns (expected 86)")
            except Exception as e:
                print(f"⚠️  Error checking features: {e}")
        
        result = {
            "status": "complete" if all(f["exists"] for f in file_status.values()) else "incomplete",
            "files": file_status,
            "has_86_features": has_86_features,
            "all_files_exist": all(f["exists"] for f in file_status.values())
        }
        
        self.verification_results["checks"]["features"] = result
        return result
    
    def verify_predictions(self) -> Dict[str, Any]:
        """Verify Week 13 predictions exist and use correct models"""
        print("\n" + "=" * 80)
        print("CHECK 4: VERIFYING PREDICTIONS")
        print("=" * 80)
        
        if not self.week13_predictions_dir.exists():
            print(f"⚠️  Week 13 predictions directory not found: {self.week13_predictions_dir}")
            return {"status": "error", "message": "Directory not found"}
        
        # Check for prediction files
        prediction_files = {
            "predictions_json": self.week13_predictions_dir / "week13_predictions.json",
            "predictions_csv": self.week13_predictions_dir / "week13_predictions_all_60_games.csv",
            "summary": self.week13_predictions_dir / "week13_prediction_summary.json"
        }
        
        file_status = {}
        for file_type, file_path in prediction_files.items():
            exists = file_path.exists()
            file_status[file_type] = {"exists": exists, "path": str(file_path)}
            
            if exists:
                try:
                    if file_path.suffix == '.json':
                        import json
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        file_status[file_type]["data_keys"] = list(data.keys()) if isinstance(data, dict) else "list"
                        print(f"✅ {file_type}: Found")
                    else:
                        df = pd.read_csv(file_path, low_memory=False)
                        file_status[file_type]["row_count"] = len(df)
                        print(f"✅ {file_type}: {len(df)} rows")
                except Exception as e:
                    file_status[file_type]["error"] = str(e)
                    print(f"⚠️  {file_type}: Error reading - {e}")
            else:
                print(f"❌ {file_type}: File not found")
        
        # Check model timestamps (verify models are recent)
        model_files = {
            "ridge": self.model_pack_path / "ridge_model_2025.joblib",
            "xgb": self.model_pack_path / "xgb_home_win_model_2025.pkl",
            "fastai": self.model_pack_path / "fastai_home_win_model_2025.pkl"
        }
        
        model_status = {}
        for model_name, model_path in model_files.items():
            if model_path.exists():
                import os
                mtime = os.path.getmtime(model_path)
                model_date = datetime.fromtimestamp(mtime)
                model_status[model_name] = {
                    "exists": True,
                    "last_modified": model_date.isoformat(),
                    "days_old": (datetime.now() - model_date).days
                }
                print(f"✅ {model_name} model: Last modified {model_date.strftime('%Y-%m-%d')}")
            else:
                model_status[model_name] = {"exists": False}
                print(f"⚠️  {model_name} model: Not found")
        
        result = {
            "status": "complete" if all(f["exists"] for f in file_status.values()) else "incomplete",
            "prediction_files": file_status,
            "models": model_status,
            "all_predictions_exist": all(f["exists"] for f in file_status.values())
        }
        
        self.verification_results["checks"]["predictions"] = result
        return result
    
    def verify_analysis(self) -> Dict[str, Any]:
        """Verify Week 13 analysis exists"""
        print("\n" + "=" * 80)
        print("CHECK 5: VERIFYING ANALYSIS")
        print("=" * 80)
        
        if not self.week13_analysis_dir.exists():
            print(f"⚠️  Week 13 analysis directory not found: {self.week13_analysis_dir}")
            return {"status": "error", "message": "Directory not found"}
        
        # Check for analysis files
        analysis_files = {
            "comprehensive": self.week13_analysis_dir / "week13_comprehensive_analysis.json",
            "power_rankings": self.week13_analysis_dir / "week13_power_rankings.csv",
            "strategic_recommendations": self.week13_analysis_dir / "week13_strategic_recommendations.csv",
            "upset_alerts": self.week13_analysis_dir / "week13_upset_alerts.csv"
        }
        
        file_status = {}
        for file_type, file_path in analysis_files.items():
            exists = file_path.exists()
            file_status[file_type] = {"exists": exists, "path": str(file_path)}
            
            if exists:
                try:
                    if file_path.suffix == '.json':
                        import json
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        file_status[file_type]["has_data"] = len(data) > 0 if isinstance(data, (dict, list)) else False
                        print(f"✅ {file_type}: Found")
                    else:
                        df = pd.read_csv(file_path, low_memory=False)
                        file_status[file_type]["row_count"] = len(df)
                        print(f"✅ {file_type}: {len(df)} rows")
                except Exception as e:
                    file_status[file_type]["error"] = str(e)
                    print(f"⚠️  {file_type}: Error reading - {e}")
            else:
                print(f"❌ {file_type}: File not found")
        
        result = {
            "status": "complete" if all(f["exists"] for f in file_status.values()) else "incomplete",
            "analysis_files": file_status,
            "all_analysis_exist": all(f["exists"] for f in file_status.values())
        }
        
        self.verification_results["checks"]["analysis"] = result
        return result
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate verification summary"""
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        
        checks = self.verification_results["checks"]
        
        all_checks_passed = all(
            check.get("status") in ["complete", "migrated"] 
            for check in checks.values()
        )
        
        summary = {
            "overall_status": "complete" if all_checks_passed else "incomplete",
            "starter_pack_ready": checks.get("starter_pack", {}).get("status") == "complete",
            "migration_complete": checks.get("migration", {}).get("status") == "migrated",
            "features_generated": checks.get("features", {}).get("status") == "complete",
            "predictions_exist": checks.get("predictions", {}).get("status") == "complete",
            "analysis_exists": checks.get("analysis", {}).get("status") == "complete",
            "recommendations": self._generate_recommendations()
        }
        
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Starter Pack: {'✅' if summary['starter_pack_ready'] else '❌'}")
        print(f"Migration: {'✅' if summary['migration_complete'] else '❌'}")
        print(f"Features: {'✅' if summary['features_generated'] else '❌'}")
        print(f"Predictions: {'✅' if summary['predictions_exist'] else '❌'}")
        print(f"Analysis: {'✅' if summary['analysis_exists'] else '❌'}")
        
        self.verification_results["summary"] = summary
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []
        checks = self.verification_results["checks"]
        
        if checks.get("starter_pack", {}).get("status") != "complete":
            recommendations.append("Fetch Week 13 data from CFBD API to starter pack")
        
        if checks.get("migration", {}).get("status") != "migrated":
            recommendations.append("Run migration script for Week 13 data")
        
        if checks.get("features", {}).get("status") != "complete":
            recommendations.append("Generate Week 13 features (86 columns)")
        
        if checks.get("predictions", {}).get("status") != "complete":
            recommendations.append("Generate Week 13 predictions using updated models")
        
        if checks.get("analysis", {}).get("status") != "complete":
            recommendations.append("Run Week 13 comprehensive analysis")
        
        if not recommendations:
            recommendations.append("Week 13 data appears complete - no action needed")
        
        return recommendations
    
    def save_report(self) -> Path:
        """Save verification report"""
        report_path = self.reports_dir / "week13_verification_report.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.verification_results, f, indent=2, default=str)
        
        print(f"\n✅ Verification report saved to: {report_path}")
        return report_path
    
    def run_complete_verification(self) -> Dict[str, Any]:
        """Run complete Week 13 verification"""
        print("=" * 80)
        print("WEEK 13 DATA VERIFICATION")
        print("=" * 80)
        print(f"Verification Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Season: 2025, Week: 13")
        
        # Run all checks
        self.verify_starter_pack_data()
        self.verify_migration_status()
        self.verify_features_generation()
        self.verify_predictions()
        self.verify_analysis()
        
        # Generate summary
        summary = self.generate_summary()
        
        # Save report
        report_path = self.save_report()
        
        return {
            "status": summary["overall_status"],
            "report_path": str(report_path),
            "summary": summary
        }


def main():
    """Main execution"""
    verifier = Week13DataVerifier()
    results = verifier.run_complete_verification()
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print(f"Report saved to: {results['report_path']}")
    print(f"Status: {results['status'].upper()}")
    
    return 0 if results['status'] == 'complete' else 1


if __name__ == "__main__":
    sys.exit(main())

