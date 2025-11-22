#!/usr/bin/env python3
"""
Comprehensive Data Audit Script
================================

Audits data coverage across starter pack, model pack, and training data.
Compares game counts by week, verifies game IDs match, and identifies gaps.

Usage:
    python scripts/comprehensive_data_audit.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Output directory
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


class ComprehensiveDataAuditor:
    """Comprehensive data audit across all systems"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.starter_pack_path = self.project_root / "starter_pack" / "data"
        self.model_pack_path = self.project_root / "model_pack"
        self.reports_dir = REPORTS_DIR
        
        # File paths
        self.starter_games = self.starter_pack_path / "games.csv"
        self.training_data = self.model_pack_path / "updated_training_data.csv"
        
        # Find migrated files
        self.migrated_files = list(self.model_pack_path.glob("*2025*weeks*migrated.csv"))
        
        # Results storage
        self.audit_results = {
            "audit_date": datetime.now().isoformat(),
            "season": 2025,
            "target_weeks": list(range(1, 13)),  # Weeks 1-12
            "starter_pack": {},
            "model_pack": {},
            "training_data": {},
            "comparisons": {},
            "gaps": [],
            "duplicates": [],
            "summary": {}
        }
    
    def audit_starter_pack(self) -> Dict[str, Any]:
        """Audit starter pack data for weeks 1-12"""
        print("\n" + "=" * 80)
        print("AUDITING STARTER PACK DATA")
        print("=" * 80)
        
        if not self.starter_games.exists():
            print(f"❌ Starter pack games file not found: {self.starter_games}")
            return {"error": "File not found"}
        
        print(f"Loading: {self.starter_games}")
        games_df = pd.read_csv(self.starter_games, low_memory=False)
        
        # Filter for 2025 season, weeks 1-12
        current_season = games_df[games_df['season'] == 2025].copy()
        weeks_1_12 = current_season[current_season['week'].between(1, 12)].copy()
        
        # Get game IDs
        game_ids = set(weeks_1_12['id'].dropna().astype(int).unique())
        
        # Count by week
        games_by_week = weeks_1_12.groupby('week').size().to_dict()
        
        # Check for missing scores
        games_with_scores = weeks_1_12[
            weeks_1_12['home_points'].notna() & 
            weeks_1_12['away_points'].notna()
        ]
        
        results = {
            "file_path": str(self.starter_games),
            "total_2025_games": len(current_season),
            "weeks_1_12_games": len(weeks_1_12),
            "unique_game_ids": len(game_ids),
            "games_by_week": games_by_week,
            "games_with_scores": len(games_with_scores),
            "games_without_scores": len(weeks_1_12) - len(games_with_scores),
            "game_ids": sorted(list(game_ids)),
            "columns": list(weeks_1_12.columns),
            "status": "complete" if len(weeks_1_12) > 0 else "empty"
        }
        
        print(f"✅ Found {len(weeks_1_12)} games for weeks 1-12")
        print(f"   Games with scores: {len(games_with_scores)}")
        print(f"   Games by week: {games_by_week}")
        
        self.audit_results["starter_pack"] = results
        return results
    
    def audit_model_pack(self) -> Dict[str, Any]:
        """Audit model pack migrated data"""
        print("\n" + "=" * 80)
        print("AUDITING MODEL PACK MIGRATED DATA")
        print("=" * 80)
        
        if not self.migrated_files:
            print("⚠️  No migrated files found in model_pack")
            return {"error": "No migrated files found"}
        
        all_migrated_data = []
        all_game_ids = set()
        
        for migrated_file in self.migrated_files:
            print(f"Loading: {migrated_file.name}")
            try:
                df = pd.read_csv(migrated_file, low_memory=False)
                
                # Filter for 2025, weeks 1-12
                current_season = df[df['season'] == 2025].copy()
                weeks_1_12 = current_season[current_season['week'].between(1, 12)].copy()
                
                if len(weeks_1_12) > 0:
                    all_migrated_data.append(weeks_1_12)
                    game_ids = set(weeks_1_12['id'].dropna().astype(int).unique())
                    all_game_ids.update(game_ids)
                    print(f"   Found {len(weeks_1_12)} games in {migrated_file.name}")
            except Exception as e:
                print(f"   ⚠️  Error loading {migrated_file.name}: {e}")
        
        if not all_migrated_data:
            return {"error": "No data found in migrated files"}
        
        # Combine all migrated data
        combined = pd.concat(all_migrated_data, ignore_index=True)
        
        # Remove duplicates by game ID
        if 'id' in combined.columns:
            combined = combined.drop_duplicates(subset=['id'], keep='last')
        
        games_by_week = combined.groupby('week').size().to_dict()
        
        results = {
            "migrated_files": [str(f) for f in self.migrated_files],
            "total_games": len(combined),
            "unique_game_ids": len(all_game_ids),
            "games_by_week": games_by_week,
            "game_ids": sorted(list(all_game_ids)),
            "columns": list(combined.columns),
            "status": "complete" if len(combined) > 0 else "empty"
        }
        
        print(f"✅ Total migrated games: {len(combined)}")
        print(f"   Games by week: {games_by_week}")
        
        self.audit_results["model_pack"] = results
        return results
    
    def audit_training_data(self) -> Dict[str, Any]:
        """Audit training data for 2025 games"""
        print("\n" + "=" * 80)
        print("AUDITING TRAINING DATA")
        print("=" * 80)
        
        if not self.training_data.exists():
            print(f"❌ Training data file not found: {self.training_data}")
            return {"error": "File not found"}
        
        print(f"Loading: {self.training_data}")
        training_df = pd.read_csv(self.training_data, low_memory=False)
        
        # Filter for 2025 season, weeks 1-12
        current_season = training_df[training_df['season'] == 2025].copy()
        weeks_1_12 = current_season[current_season['week'].between(1, 12)].copy()
        
        # Get game IDs
        game_ids = set(weeks_1_12['id'].dropna().astype(int).unique())
        
        # Count by week
        games_by_week = weeks_1_12.groupby('week').size().to_dict()
        
        # Check for required columns (86 features + metadata)
        required_columns = ['id', 'season', 'week', 'home_team', 'away_team', 
                          'home_points', 'away_points', 'home_adjusted_epa', 
                          'away_adjusted_epa']
        missing_columns = [col for col in required_columns if col not in weeks_1_12.columns]
        
        results = {
            "file_path": str(self.training_data),
            "total_games": len(training_df),
            "total_2025_games": len(current_season),
            "weeks_1_12_games": len(weeks_1_12),
            "unique_game_ids": len(game_ids),
            "games_by_week": games_by_week,
            "game_ids": sorted(list(game_ids)),
            "columns_count": len(weeks_1_12.columns),
            "missing_required_columns": missing_columns,
            "status": "complete" if len(weeks_1_12) > 0 else "empty"
        }
        
        print(f"✅ Found {len(weeks_1_12)} games for weeks 1-12 in training data")
        print(f"   Total columns: {len(weeks_1_12.columns)}")
        print(f"   Games by week: {games_by_week}")
        if missing_columns:
            print(f"   ⚠️  Missing required columns: {missing_columns}")
        
        self.audit_results["training_data"] = results
        return results
    
    def compare_systems(self) -> Dict[str, Any]:
        """Compare data across all systems"""
        print("\n" + "=" * 80)
        print("COMPARING DATA ACROSS SYSTEMS")
        print("=" * 80)
        
        starter_ids = set(self.audit_results["starter_pack"].get("game_ids", []))
        model_ids = set(self.audit_results["model_pack"].get("game_ids", []))
        training_ids = set(self.audit_results["training_data"].get("game_ids", []))
        
        # Find gaps
        gaps = []
        
        # Games in starter but not in model pack
        missing_in_model = starter_ids - model_ids
        if missing_in_model:
            gaps.append({
                "type": "missing_in_model_pack",
                "count": len(missing_in_model),
                "game_ids": sorted(list(missing_in_model))
            })
        
        # Games in starter but not in training
        missing_in_training = starter_ids - training_ids
        if missing_in_training:
            gaps.append({
                "type": "missing_in_training",
                "count": len(missing_in_training),
                "game_ids": sorted(list(missing_in_training))
            })
        
        # Games in model pack but not in training
        missing_migration = model_ids - training_ids
        if missing_migration:
            gaps.append({
                "type": "migrated_but_not_in_training",
                "count": len(missing_migration),
                "game_ids": sorted(list(missing_migration))
            })
        
        # Find duplicates (games in multiple systems with different counts)
        starter_by_week = self.audit_results["starter_pack"].get("games_by_week", {})
        model_by_week = self.audit_results["model_pack"].get("games_by_week", {})
        training_by_week = self.audit_results["training_data"].get("games_by_week", {})
        
        week_comparisons = {}
        for week in range(1, 13):
            starter_count = starter_by_week.get(week, 0)
            model_count = model_by_week.get(week, 0)
            training_count = training_by_week.get(week, 0)
            
            week_comparisons[week] = {
                "starter_pack": starter_count,
                "model_pack": model_count,
                "training_data": training_count,
                "consistent": starter_count == model_count == training_count
            }
        
        # Overall comparison
        comparison = {
            "starter_pack_game_ids": len(starter_ids),
            "model_pack_game_ids": len(model_ids),
            "training_data_game_ids": len(training_ids),
            "common_game_ids": len(starter_ids & model_ids & training_ids),
            "week_by_week_comparison": week_comparisons,
            "gaps": gaps
        }
        
        print(f"Starter Pack: {len(starter_ids)} games")
        print(f"Model Pack: {len(model_ids)} games")
        print(f"Training Data: {len(training_ids)} games")
        print(f"Common to all: {len(starter_ids & model_ids & training_ids)} games")
        
        if gaps:
            print(f"\n⚠️  Found {len(gaps)} gap types:")
            for gap in gaps:
                print(f"   - {gap['type']}: {gap['count']} games")
        
        self.audit_results["comparisons"] = comparison
        self.audit_results["gaps"] = gaps
        return comparison
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of audit results"""
        print("\n" + "=" * 80)
        print("GENERATING AUDIT SUMMARY")
        print("=" * 80)
        
        starter_status = self.audit_results["starter_pack"].get("status", "unknown")
        model_status = self.audit_results["model_pack"].get("status", "unknown")
        training_status = self.audit_results["training_data"].get("status", "unknown")
        
        starter_count = self.audit_results["starter_pack"].get("weeks_1_12_games", 0)
        model_count = self.audit_results["model_pack"].get("total_games", 0)
        training_count = self.audit_results["training_data"].get("weeks_1_12_games", 0)
        
        gaps_count = len(self.audit_results["gaps"])
        
        # Determine overall status
        if gaps_count == 0 and starter_count > 0 and model_count > 0 and training_count > 0:
            overall_status = "synchronized"
        elif gaps_count > 0:
            overall_status = "gaps_detected"
        else:
            overall_status = "incomplete"
        
        summary = {
            "overall_status": overall_status,
            "starter_pack_status": starter_status,
            "model_pack_status": model_status,
            "training_data_status": training_status,
            "starter_pack_games": starter_count,
            "model_pack_games": model_count,
            "training_data_games": training_count,
            "gaps_detected": gaps_count,
            "synchronization_needed": gaps_count > 0,
            "recommendations": self._generate_recommendations()
        }
        
        print(f"Overall Status: {overall_status.upper()}")
        print(f"Starter Pack: {starter_count} games ({starter_status})")
        print(f"Model Pack: {model_count} games ({model_status})")
        print(f"Training Data: {training_count} games ({training_status})")
        print(f"Gaps Detected: {gaps_count}")
        
        self.audit_results["summary"] = summary
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on audit results"""
        recommendations = []
        
        gaps = self.audit_results.get("gaps", [])
        
        if any(gap["type"] == "missing_in_model_pack" for gap in gaps):
            recommendations.append("Run migration script to migrate missing games to model pack")
        
        if any(gap["type"] == "missing_in_training" for gap in gaps):
            recommendations.append("Extend training data with missing games from starter pack")
        
        if any(gap["type"] == "migrated_but_not_in_training" for gap in gaps):
            recommendations.append("Run training data extension workflow to include migrated games")
        
        starter_count = self.audit_results["starter_pack"].get("weeks_1_12_games", 0)
        if starter_count == 0:
            recommendations.append("Fetch Week 1-12 data from CFBD API to starter pack")
        
        if not recommendations:
            recommendations.append("Data appears synchronized - no action needed")
        
        return recommendations
    
    def save_report(self) -> Path:
        """Save audit report to JSON file"""
        report_path = self.reports_dir / "data_audit_report.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.audit_results, f, indent=2, default=str)
        
        print(f"\n✅ Audit report saved to: {report_path}")
        return report_path
    
    def run_complete_audit(self) -> Dict[str, Any]:
        """Run complete audit process"""
        print("=" * 80)
        print("COMPREHENSIVE DATA AUDIT - WEEKS 1-12")
        print("=" * 80)
        print(f"Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Season: 2025")
        print(f"Target Weeks: 1-12")
        
        # Run all audit steps
        self.audit_starter_pack()
        self.audit_model_pack()
        self.audit_training_data()
        self.compare_systems()
        self.generate_summary()
        
        # Save report
        report_path = self.save_report()
        
        return {
            "status": "complete",
            "report_path": str(report_path),
            "summary": self.audit_results["summary"]
        }


def main():
    """Main execution"""
    auditor = ComprehensiveDataAuditor()
    results = auditor.run_complete_audit()
    
    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)
    print(f"Report saved to: {results['report_path']}")
    print(f"Overall Status: {results['summary']['overall_status'].upper()}")
    
    return 0 if results['summary']['overall_status'] == 'synchronized' else 1


if __name__ == "__main__":
    sys.exit(main())
