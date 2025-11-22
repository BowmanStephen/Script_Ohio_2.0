#!/usr/bin/env python3
"""
Data Synchronization Script for Weeks 1-12
==========================================

Synchronizes all Week 1-12 data across starter pack, model pack, and training data.
Fetches missing data, runs migration, and extends training dataset.

Usage:
    python scripts/synchronize_weeks_1_12_data.py [--dry-run]
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Output directory
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


class DataSynchronizer:
    """Synchronize Week 1-12 data across all systems"""
    
    def __init__(self, dry_run: bool = False):
        self.project_root = PROJECT_ROOT
        self.dry_run = dry_run
        self.reports_dir = REPORTS_DIR
        
        # File paths
        self.starter_games = self.project_root / "starter_pack" / "data" / "games.csv"
        self.model_pack_path = self.project_root / "model_pack"
        self.training_data = self.model_pack_path / "updated_training_data.csv"
        
        # Script paths
        self.migration_script = self.model_pack_path / "migrate_starter_pack_data.py"
        self.data_workflows_script = self.project_root / "project_management" / "core_tools" / "data_workflows.py"
        
        # Results storage
        self.sync_results = {
            "sync_date": datetime.now().isoformat(),
            "season": 2025,
            "target_weeks": list(range(1, 13)),
            "dry_run": dry_run,
            "steps": [],
            "summary": {}
        }
    
    def check_starter_pack_completeness(self) -> Dict[str, Any]:
        """Check if starter pack has complete Week 1-12 data"""
        print("\n" + "=" * 80)
        print("STEP 1: CHECKING STARTER PACK DATA COMPLETENESS")
        print("=" * 80)
        
        if not self.starter_games.exists():
            print(f"❌ Starter pack games file not found: {self.starter_games}")
            return {"status": "error", "message": "File not found"}
        
        games_df = pd.read_csv(self.starter_games, low_memory=False)
        
        # Filter for 2025, weeks 1-12
        current_season = games_df[games_df['season'] == 2025].copy()
        weeks_1_12 = current_season[current_season['week'].between(1, 12)].copy()
        
        games_by_week = weeks_1_12.groupby('week').size().to_dict()
        
        # Check for missing weeks
        missing_weeks = [w for w in range(1, 13) if w not in games_by_week or games_by_week[w] == 0]
        
        result = {
            "status": "complete" if not missing_weeks else "incomplete",
            "total_games": len(weeks_1_12),
            "games_by_week": games_by_week,
            "missing_weeks": missing_weeks,
            "needs_fetch": len(missing_weeks) > 0
        }
        
        print(f"Found {len(weeks_1_12)} games for weeks 1-12")
        print(f"Games by week: {games_by_week}")
        
        if missing_weeks:
            print(f"⚠️  Missing weeks: {missing_weeks}")
            print("   Run fetch scripts for missing weeks")
        else:
            print("✅ All weeks 1-12 present in starter pack")
        
        self.sync_results["steps"].append({
            "step": "check_starter_pack",
            "result": result
        })
        
        return result
    
    def fetch_missing_data(self, missing_weeks: list) -> Dict[str, Any]:
        """Fetch missing week data from CFBD API"""
        if not missing_weeks:
            print("\n✅ No missing weeks to fetch")
            return {"status": "skipped", "reason": "No missing weeks"}
        
        print("\n" + "=" * 80)
        print("STEP 2: FETCHING MISSING WEEK DATA")
        print("=" * 80)
        
        if self.dry_run:
            print("DRY RUN: Would fetch data for weeks:", missing_weeks)
            return {"status": "dry_run", "weeks": missing_weeks}
        
        api_key = os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
        if not api_key:
            print("⚠️  CFBD_API_KEY not set - skipping fetch")
            return {"status": "skipped", "reason": "No API key"}
        
        fetch_script_dir = self.project_root / "project_management" / "TOOLS_AND_CONFIG"
        fetch_script = fetch_script_dir / "fetch_future_week.py"
        
        if not fetch_script.exists():
            print(f"⚠️  Fetch script not found: {fetch_script}")
            return {"status": "error", "message": "Fetch script not found"}
        
        results = []
        for week in missing_weeks:
            print(f"\nFetching Week {week} data...")
            try:
                result = subprocess.run(
                    [sys.executable, str(fetch_script), "--week", str(week), "--season", "2025"],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    print(f"✅ Week {week} fetched successfully")
                    results.append({"week": week, "status": "success"})
                else:
                    print(f"❌ Week {week} fetch failed: {result.stderr}")
                    results.append({"week": week, "status": "error", "message": result.stderr})
            except Exception as e:
                print(f"❌ Week {week} fetch error: {e}")
                results.append({"week": week, "status": "error", "message": str(e)})
        
        result = {
            "status": "complete",
            "weeks_fetched": [r["week"] for r in results if r["status"] == "success"],
            "weeks_failed": [r["week"] for r in results if r["status"] == "error"],
            "details": results
        }
        
        self.sync_results["steps"].append({
            "step": "fetch_missing_data",
            "result": result
        })
        
        return result
    
    def run_migration(self) -> Dict[str, Any]:
        """Run migration script to migrate Week 1-12 data"""
        print("\n" + "=" * 80)
        print("STEP 3: RUNNING DATA MIGRATION")
        print("=" * 80)
        
        if not self.migration_script.exists():
            print(f"❌ Migration script not found: {self.migration_script}")
            return {"status": "error", "message": "Migration script not found"}
        
        if self.dry_run:
            print("DRY RUN: Would run migration script")
            return {"status": "dry_run"}
        
        print(f"Running: {self.migration_script}")
        try:
            result = subprocess.run(
                [sys.executable, str(self.migration_script)],
                cwd=str(self.model_pack_path),
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                print("✅ Migration completed successfully")
                print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
                return {"status": "success", "output": result.stdout}
            else:
                print(f"❌ Migration failed: {result.stderr}")
                return {"status": "error", "message": result.stderr}
        except Exception as e:
            print(f"❌ Migration error: {e}")
            return {"status": "error", "message": str(e)}
    
    def extend_training_data(self) -> Dict[str, Any]:
        """Extend training data with migrated Week 1-12 data"""
        print("\n" + "=" * 80)
        print("STEP 4: EXTENDING TRAINING DATA")
        print("=" * 80)
        
        # Find migrated file
        migrated_files = list(self.model_pack_path.glob("*2025*weeks*migrated.csv"))
        
        if not migrated_files:
            print("⚠️  No migrated files found")
            return {"status": "error", "message": "No migrated files found"}
        
        # Use the most recent migrated file
        migrated_file = max(migrated_files, key=lambda p: p.stat().st_mtime)
        print(f"Using migrated file: {migrated_file.name}")
        
        if self.dry_run:
            print("DRY RUN: Would extend training data")
            return {"status": "dry_run", "migrated_file": str(migrated_file)}
        
        if not self.data_workflows_script.exists():
            print(f"⚠️  Data workflows script not found: {self.data_workflows_script}")
            return {"status": "error", "message": "Data workflows script not found"}
        
        print(f"Running: {self.data_workflows_script} refresh-training")
        try:
            result = subprocess.run(
                [sys.executable, str(self.data_workflows_script), 
                 "refresh-training", 
                 "--migrated-file", str(migrated_file)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                print("✅ Training data extended successfully")
                return {"status": "success", "migrated_file": str(migrated_file), "output": result.stdout}
            else:
                print(f"❌ Training data extension failed: {result.stderr}")
                return {"status": "error", "message": result.stderr}
        except Exception as e:
            print(f"❌ Training data extension error: {e}")
            return {"status": "error", "message": str(e)}
    
    def verify_integration(self) -> Dict[str, Any]:
        """Verify all games are present in training data"""
        print("\n" + "=" * 80)
        print("STEP 5: VERIFYING INTEGRATION")
        print("=" * 80)
        
        if not self.training_data.exists():
            print(f"❌ Training data file not found: {self.training_data}")
            return {"status": "error", "message": "Training data not found"}
        
        # Load starter pack games
        starter_games_df = pd.read_csv(self.starter_games, low_memory=False)
        starter_2025 = starter_games_df[starter_games_df['season'] == 2025].copy()
        starter_weeks_1_12 = starter_2025[starter_2025['week'].between(1, 12)].copy()
        starter_ids = set(starter_weeks_1_12['id'].dropna().astype(int).unique())
        
        # Load training data
        training_df = pd.read_csv(self.training_data, low_memory=False)
        training_2025 = training_df[training_df['season'] == 2025].copy()
        training_weeks_1_12 = training_2025[training_2025['week'].between(1, 12)].copy()
        training_ids = set(training_weeks_1_12['id'].dropna().astype(int).unique())
        
        # Compare
        missing_in_training = starter_ids - training_ids
        extra_in_training = training_ids - starter_ids
        
        result = {
            "status": "complete" if not missing_in_training else "incomplete",
            "starter_pack_games": len(starter_ids),
            "training_data_games": len(training_ids),
            "missing_in_training": len(missing_in_training),
            "missing_game_ids": sorted(list(missing_in_training)) if missing_in_training else [],
            "extra_in_training": len(extra_in_training),
            "synchronized": len(missing_in_training) == 0
        }
        
        print(f"Starter Pack: {len(starter_ids)} games")
        print(f"Training Data: {len(training_ids)} games")
        print(f"Missing in Training: {len(missing_in_training)}")
        
        if missing_in_training:
            print(f"⚠️  Missing game IDs: {sorted(list(missing_in_training))[:10]}...")
        else:
            print("✅ All games present in training data")
        
        self.sync_results["steps"].append({
            "step": "verify_integration",
            "result": result
        })
        
        return result
    
    def update_data_status(self) -> Dict[str, Any]:
        """Update DATA_STATUS.md with current state"""
        print("\n" + "=" * 80)
        print("STEP 6: UPDATING DATA STATUS DOCUMENTATION")
        print("=" * 80)
        
        if self.dry_run:
            print("DRY RUN: Would update DATA_STATUS.md")
            return {"status": "dry_run"}
        
        status_file = self.project_root / "project_management" / "DATA_STATUS.md"
        
        if not status_file.exists():
            print(f"⚠️  DATA_STATUS.md not found: {status_file}")
            return {"status": "skipped", "reason": "File not found"}
        
        # Read current status
        with open(status_file, 'r') as f:
            content = f.read()
        
        # Update last updated date
        new_date = datetime.now().strftime("%Y-%m-%d")
        content = content.replace(
            "## Last Updated: 2025-11-14",
            f"## Last Updated: {new_date}"
        )
        
        # Update data coverage if verification passed
        verification = self.sync_results["steps"][-1]["result"] if self.sync_results["steps"] else None
        if verification and verification.get("synchronized"):
            content = content.replace(
                "- **Starter Pack:** Weeks 1-12 (2025 season)",
                "- **Starter Pack:** Weeks 1-12 (2025 season) ✅ Verified"
            )
            content = content.replace(
                "- **Training Data:** Extended through Week 12, 2025",
                "- **Training Data:** Extended through Week 12, 2025 ✅ Synchronized"
            )
        
        # Write updated content
        with open(status_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {status_file}")
        
        return {"status": "success", "file": str(status_file)}
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate synchronization summary"""
        print("\n" + "=" * 80)
        print("SYNCHRONIZATION SUMMARY")
        print("=" * 80)
        
        all_steps_successful = all(
            step.get("result", {}).get("status") in ["success", "complete", "skipped", "dry_run"]
            for step in self.sync_results["steps"]
        )
        
        verification = None
        for step in self.sync_results["steps"]:
            if step.get("step") == "verify_integration":
                verification = step.get("result")
                break
        
        summary = {
            "overall_status": "success" if all_steps_successful else "partial",
            "synchronized": verification.get("synchronized", False) if verification else False,
            "steps_completed": len([s for s in self.sync_results["steps"] if s.get("result", {}).get("status") in ["success", "complete", "skipped"]]),
            "total_steps": len(self.sync_results["steps"]),
            "dry_run": self.dry_run
        }
        
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Synchronized: {summary['synchronized']}")
        print(f"Steps Completed: {summary['steps_completed']}/{summary['total_steps']}")
        
        self.sync_results["summary"] = summary
        return summary
    
    def save_report(self) -> Path:
        """Save synchronization report"""
        report_path = self.reports_dir / "data_synchronization_report.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.sync_results, f, indent=2, default=str)
        
        print(f"\n✅ Synchronization report saved to: {report_path}")
        return report_path
    
    def run_complete_synchronization(self) -> Dict[str, Any]:
        """Run complete synchronization process"""
        print("=" * 80)
        print("DATA SYNCHRONIZATION - WEEKS 1-12")
        print("=" * 80)
        print(f"Sync Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Season: 2025")
        print(f"Target Weeks: 1-12")
        if self.dry_run:
            print("DRY RUN MODE - No changes will be made")
        
        # Step 1: Check starter pack completeness
        starter_check = self.check_starter_pack_completeness()
        
        # Step 2: Fetch missing data if needed
        if starter_check.get("needs_fetch"):
            missing_weeks = starter_check.get("missing_weeks", [])
            self.fetch_missing_data(missing_weeks)
        
        # Step 3: Run migration
        migration_result = self.run_migration()
        if migration_result.get("status") == "error":
            print("⚠️  Migration failed - continuing with verification")
        
        # Step 4: Extend training data
        extension_result = self.extend_training_data()
        if extension_result.get("status") == "error":
            print("⚠️  Training data extension failed - continuing with verification")
        
        # Step 5: Verify integration
        verification = self.verify_integration()
        
        # Step 6: Update documentation
        self.update_data_status()
        
        # Generate summary
        summary = self.generate_summary()
        
        # Save report
        report_path = self.save_report()
        
        return {
            "status": summary["overall_status"],
            "synchronized": summary["synchronized"],
            "report_path": str(report_path),
            "summary": summary
        }


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Synchronize Week 1-12 data across all systems")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no changes)")
    
    args = parser.parse_args()
    
    synchronizer = DataSynchronizer(dry_run=args.dry_run)
    results = synchronizer.run_complete_synchronization()
    
    print("\n" + "=" * 80)
    print("SYNCHRONIZATION COMPLETE")
    print("=" * 80)
    print(f"Report saved to: {results['report_path']}")
    print(f"Status: {results['status'].upper()}")
    print(f"Synchronized: {results['synchronized']}")
    
    return 0 if results['synchronized'] else 1


if __name__ == "__main__":
    sys.exit(main())

