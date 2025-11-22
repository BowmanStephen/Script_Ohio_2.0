#!/usr/bin/env python3
"""
Comprehensive verification script for starter pack data completeness.

Verifies all 2025 weeks 1-12 data files are present, complete, and properly formatted.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "starter_pack" / "data"
YEAR = 2025
START_WEEK = 1
END_WEEK = 12


class StarterPackDataVerifier:
    """Verify starter pack data completeness and quality."""

    def __init__(self):
        self.data_dir = DATA_DIR
        self.results = {
            "file_existence": {},
            "schema_compliance": {},
            "data_completeness": {},
            "data_quality": {},
            "cross_reference": {},
            "issues": [],
            "summary": {}
        }

    def verify_file_existence(self) -> Dict[str, bool]:
        """Check that all required files exist."""
        print("\n" + "=" * 80)
        print("STEP 1: Verifying File Existence")
        print("=" * 80)

        files_to_check = {
            "advanced_game_stats": self.data_dir / "advanced_game_stats" / f"{YEAR}.csv",
            "advanced_season_stats": self.data_dir / "advanced_season_stats" / f"{YEAR}.csv",
            "drives": self.data_dir / "drives" / f"drives_{YEAR}.csv",
            "game_stats": self.data_dir / "game_stats" / f"{YEAR}.csv",
            "season_stats": self.data_dir / "season_stats" / f"{YEAR}.csv",
            "games": self.data_dir / "games.csv",
            "teams": self.data_dir / "teams.csv",
            "conferences": self.data_dir / "conferences.csv",
        }

        # Add weekly play files
        for week in range(START_WEEK, END_WEEK + 1):
            files_to_check[f"plays_week_{week}"] = (
                self.data_dir / "plays" / str(YEAR) / f"regular_{week}_plays.csv"
            )

        # Add reference files
        reference_files = {
            "ref_advanced_game_stats": self.data_dir / "advanced_game_stats" / "2024.csv",
            "ref_advanced_season_stats": self.data_dir / "advanced_season_stats" / "2024.csv",
            "ref_drives": self.data_dir / "drives" / "drives_2024.csv",
            "ref_game_stats": self.data_dir / "game_stats" / "2024.csv",
            "ref_season_stats": self.data_dir / "season_stats" / "2024.csv",
            "ref_plays": self.data_dir / "plays" / "2024" / "regular_1_plays.csv",
        }
        files_to_check.update(reference_files)

        results = {}
        for name, path in files_to_check.items():
            exists = path.exists()
            results[name] = {
                "exists": exists,
                "path": str(path),
                "size_mb": path.stat().st_size / (1024 * 1024) if exists else 0
            }
            status = "✅" if exists else "❌"
            print(f"{status} {name}: {path.name}")

        self.results["file_existence"] = results
        return results

    def verify_schema_compliance(self) -> Dict[str, Dict]:
        """Verify column counts match 2024 reference files."""
        print("\n" + "=" * 80)
        print("STEP 2: Verifying Schema Compliance")
        print("=" * 80)

        schema_checks = {
            "advanced_game_stats": {
                "file": self.data_dir / "advanced_game_stats" / f"{YEAR}.csv",
                "ref_file": self.data_dir / "advanced_game_stats" / "2024.csv",
                "expected_cols": 61
            },
            "advanced_season_stats": {
                "file": self.data_dir / "advanced_season_stats" / f"{YEAR}.csv",
                "ref_file": self.data_dir / "advanced_season_stats" / "2024.csv",
                "expected_cols": 82
            },
            "drives": {
                "file": self.data_dir / "drives" / f"drives_{YEAR}.csv",
                "ref_file": self.data_dir / "drives" / "drives_2024.csv",
                "expected_cols": 24
            },
            "game_stats": {
                "file": self.data_dir / "game_stats" / f"{YEAR}.csv",
                "ref_file": self.data_dir / "game_stats" / "2024.csv",
                "expected_cols": 46
            },
            "season_stats": {
                "file": self.data_dir / "season_stats" / f"{YEAR}.csv",
                "ref_file": self.data_dir / "season_stats" / "2024.csv",
                "expected_cols": 66
            },
            "plays": {
                "file": self.data_dir / "plays" / str(YEAR) / "regular_1_plays.csv",
                "ref_file": self.data_dir / "plays" / "2024" / "regular_1_plays.csv",
                "expected_cols": 27
            }
        }

        results = {}
        for name, config in schema_checks.items():
            if not config["file"].exists():
                results[name] = {"status": "SKIP", "reason": "File not found"}
                print(f"⏭️  {name}: File not found, skipping")
                continue

            if not config["ref_file"].exists():
                results[name] = {"status": "WARN", "reason": "Reference file not found"}
                print(f"⚠️  {name}: Reference file not found")
                continue

            try:
                df = pd.read_csv(config["file"], nrows=0)
                ref_df = pd.read_csv(config["ref_file"], nrows=0)

                actual_cols = len(df.columns)
                ref_cols = len(ref_df.columns)
                expected_cols = config["expected_cols"]

                # Check column count
                matches_expected = actual_cols == expected_cols
                matches_ref = actual_cols == ref_cols

                # Check column names match (allow extra columns, but not missing required ones)
                missing_cols = set(ref_df.columns) - set(df.columns)
                extra_cols = set(df.columns) - set(ref_df.columns)
                cols_match = len(missing_cols) == 0  # Missing columns are errors, extra columns are OK

                # Status: PASS if no missing columns (extra columns are acceptable enhancements)
                status = "✅" if (len(missing_cols) == 0) else "❌"

                results[name] = {
                    "status": "PASS" if (len(missing_cols) == 0) else "FAIL",
                    "actual_columns": actual_cols,
                    "reference_columns": ref_cols,
                    "expected_columns": expected_cols,
                    "columns_match": cols_match,
                    "missing_columns": list(missing_cols),
                    "extra_columns": list(extra_cols),
                    "note": "Extra columns are acceptable enhancements" if extra_cols else None
                }

                print(f"{status} {name}: {actual_cols} columns (expected: {expected_cols}, ref: {ref_cols})")
                if missing_cols:
                    print(f"   ⚠️  Missing: {list(missing_cols)[:5]}")
                if extra_cols:
                    print(f"   ℹ️  Extra (acceptable): {list(extra_cols)[:5]}")

            except Exception as e:
                results[name] = {"status": "ERROR", "error": str(e)}
                print(f"❌ {name}: Error - {e}")

        self.results["schema_compliance"] = results
        return results

    def verify_data_completeness(self) -> Dict[str, Dict]:
        """Verify week coverage and record counts."""
        print("\n" + "=" * 80)
        print("STEP 3: Verifying Data Completeness")
        print("=" * 80)

        results = {}

        # Check advanced_game_stats
        try:
            df = pd.read_csv(self.data_dir / "advanced_game_stats" / f"{YEAR}.csv")
            weeks = sorted(df["week"].unique()) if "week" in df.columns else []
            week_range = f"{min(weeks)}-{max(weeks)}" if weeks else "N/A"
            has_all_weeks = set(range(START_WEEK, END_WEEK + 1)).issubset(set(weeks))
            missing_weeks = set(range(START_WEEK, END_WEEK + 1)) - set(weeks)

            results["advanced_game_stats"] = {
                "total_records": len(df),
                "unique_games": df["gameId"].nunique() if "gameId" in df.columns else 0,
                "weeks_present": weeks,
                "week_range": week_range,
                "has_all_weeks": has_all_weeks,
                "missing_weeks": list(missing_weeks)
            }
            status = "✅" if has_all_weeks else "❌"
            print(f"{status} Advanced Game Stats: {len(df)} records, weeks {week_range}")
            if missing_weeks:
                print(f"   Missing weeks: {missing_weeks}")

        except Exception as e:
            results["advanced_game_stats"] = {"error": str(e)}
            print(f"❌ Advanced Game Stats: Error - {e}")

        # Check plays files
        plays_results = {}
        all_play_weeks = []
        total_plays = 0
        for week in range(START_WEEK, END_WEEK + 1):
            play_file = self.data_dir / "plays" / str(YEAR) / f"regular_{week}_plays.csv"
            if play_file.exists():
                try:
                    df = pd.read_csv(play_file)
                    plays_results[week] = {
                        "exists": True,
                        "records": len(df),
                        "file_size_mb": play_file.stat().st_size / (1024 * 1024)
                    }
                    all_play_weeks.append(week)
                    total_plays += len(df)
                    print(f"✅ Week {week} plays: {len(df)} records")
                except Exception as e:
                    plays_results[week] = {"exists": True, "error": str(e)}
                    print(f"❌ Week {week} plays: Error - {e}")
            else:
                plays_results[week] = {"exists": False}
                print(f"❌ Week {week} plays: File not found")

        results["plays"] = {
            "weekly_files": plays_results,
            "weeks_present": all_play_weeks,
            "total_plays": total_plays,
            "has_all_weeks": len(all_play_weeks) == (END_WEEK - START_WEEK + 1)
        }

        # Check games.csv for 2025 data
        try:
            df = pd.read_csv(self.data_dir / "games.csv", low_memory=False)
            df_2025 = df[df["season"] == YEAR] if "season" in df.columns else pd.DataFrame()
            if len(df_2025) > 0:
                weeks = sorted(df_2025["week"].unique()) if "week" in df_2025.columns else []
                week_range = f"{min(weeks)}-{max(weeks)}" if weeks else "N/A"
                has_weeks_1_12 = set(range(START_WEEK, END_WEEK + 1)).issubset(set(weeks))

                results["games"] = {
                    "total_2025_records": len(df_2025),
                    "weeks_present": weeks,
                    "week_range": week_range,
                    "has_weeks_1_12": has_weeks_1_12
                }
                status = "✅" if has_weeks_1_12 else "⚠️"
                print(f"{status} Games.csv 2025: {len(df_2025)} records, weeks {week_range}")
            else:
                results["games"] = {"total_2025_records": 0, "error": "No 2025 data found"}
                print(f"⚠️  Games.csv: No 2025 data found")

        except Exception as e:
            results["games"] = {"error": str(e)}
            print(f"❌ Games.csv: Error - {e}")

        # Check other files
        for file_type in ["advanced_season_stats", "drives", "game_stats", "season_stats"]:
            try:
                if file_type == "drives":
                    file_path = self.data_dir / "drives" / f"drives_{YEAR}.csv"
                else:
                    file_path = self.data_dir / file_type / f"{YEAR}.csv"

                if file_path.exists():
                    df = pd.read_csv(file_path)
                    weeks = sorted(df["week"].unique()) if "week" in df.columns else []
                    results[file_type] = {
                        "total_records": len(df),
                        "weeks_present": weeks if weeks else "N/A (season-level data)"
                    }
                    print(f"✅ {file_type}: {len(df)} records")
                else:
                    results[file_type] = {"error": "File not found"}
                    print(f"❌ {file_type}: File not found")

            except Exception as e:
                results[file_type] = {"error": str(e)}
                print(f"❌ {file_type}: Error - {e}")

        self.results["data_completeness"] = results
        return results

    def verify_data_quality(self) -> Dict[str, Dict]:
        """Perform quality checks."""
        print("\n" + "=" * 80)
        print("STEP 4: Verifying Data Quality")
        print("=" * 80)

        results = {}

        # Check advanced_game_stats quality
        try:
            df = pd.read_csv(self.data_dir / "advanced_game_stats" / f"{YEAR}.csv")
            quality = {
                "total_records": len(df),
                "null_counts": df.isnull().sum().to_dict(),
                "critical_nulls": {},
                "week_range_valid": True,
                "season_valid": True,
                "duplicates": 0
            }

            # Check critical columns
            critical_cols = ["gameId", "season", "week", "team", "opponent"]
            for col in critical_cols:
                if col in df.columns:
                    null_count = df[col].isnull().sum()
                    quality["critical_nulls"][col] = null_count
                    if null_count > 0:
                        print(f"⚠️  {col}: {null_count} null values")

            # Check week range
            if "week" in df.columns:
                invalid_weeks = df[(df["week"] < START_WEEK) | (df["week"] > END_WEEK)]
                quality["week_range_valid"] = len(invalid_weeks) == 0
                if len(invalid_weeks) > 0:
                    print(f"⚠️  Invalid weeks found: {invalid_weeks['week'].unique()}")

            # Check season
            if "season" in df.columns:
                invalid_season = df[df["season"] != YEAR]
                quality["season_valid"] = len(invalid_season) == 0
                if len(invalid_season) > 0:
                    print(f"⚠️  Invalid season values: {invalid_season['season'].unique()}")

            # Check duplicates
            if "gameId" in df.columns and "team" in df.columns:
                duplicates = df.duplicated(subset=["gameId", "team"]).sum()
                quality["duplicates"] = duplicates
                if duplicates > 0:
                    print(f"⚠️  Found {duplicates} duplicate gameId-team combinations")

            results["advanced_game_stats"] = quality
            status = "✅" if (quality["week_range_valid"] and quality["season_valid"] and quality["duplicates"] == 0) else "⚠️"
            print(f"{status} Advanced Game Stats quality check")

        except Exception as e:
            results["advanced_game_stats"] = {"error": str(e)}
            print(f"❌ Advanced Game Stats: Error - {e}")

        # Check plays quality
        plays_quality = {}
        for week in range(START_WEEK, END_WEEK + 1):
            play_file = self.data_dir / "plays" / str(YEAR) / f"regular_{week}_plays.csv"
            if play_file.exists():
                try:
                    df = pd.read_csv(play_file)
                    quality = {
                        "total_records": len(df),
                        "null_counts": df.isnull().sum().sum(),
                        "has_game_id": "gameId" in df.columns,
                        "has_week": "week" in df.columns
                    }
                    plays_quality[week] = quality
                except Exception as e:
                    plays_quality[week] = {"error": str(e)}

        results["plays"] = plays_quality

        self.results["data_quality"] = results
        return results

    def cross_reference_validation(self) -> Dict[str, Dict]:
        """Verify consistency across files."""
        print("\n" + "=" * 80)
        print("STEP 5: Cross-Reference Validation")
        print("=" * 80)

        results = {}

        try:
            # Load games.csv 2025 data
            games_df = pd.read_csv(self.data_dir / "games.csv", low_memory=False)
            games_2025 = games_df[games_df["season"] == YEAR] if "season" in games_df.columns else pd.DataFrame()

            # Load advanced_game_stats
            adv_stats_df = pd.read_csv(self.data_dir / "advanced_game_stats" / f"{YEAR}.csv")

            if len(games_2025) > 0 and len(adv_stats_df) > 0:
                # Filter to only weeks 1-12 for fair comparison
                games_2025_weeks_1_12 = games_2025[
                    (games_2025["week"] >= START_WEEK) & (games_2025["week"] <= END_WEEK)
                ] if "week" in games_2025.columns else pd.DataFrame()

                # Check game ID consistency (only for weeks 1-12)
                games_ids = set(games_2025_weeks_1_12["id"].unique()) if len(games_2025_weeks_1_12) > 0 and "id" in games_2025_weeks_1_12.columns else set()
                adv_stats_ids = set(adv_stats_df["gameId"].unique()) if "gameId" in adv_stats_df.columns else set()

                missing_in_adv = games_ids - adv_stats_ids
                missing_in_games = adv_stats_ids - games_ids

                # Calculate coverage percentage for weeks 1-12
                coverage_pct = (len(adv_stats_ids) / len(games_ids) * 100) if len(games_ids) > 0 else 0

                results["game_id_consistency"] = {
                    "games_csv_ids_weeks_1_12": len(games_ids),
                    "adv_stats_ids": len(adv_stats_ids),
                    "missing_in_adv_stats": len(missing_in_adv),
                    "missing_in_games": len(missing_in_games),
                    "coverage_percentage": round(coverage_pct, 1),
                    "consistent": coverage_pct >= 95.0  # Allow 5% variance for incomplete games
                }

                status = "✅" if results["game_id_consistency"]["consistent"] else "⚠️"
                print(f"{status} Game ID consistency (weeks 1-12): {len(games_ids)} in games.csv, {len(adv_stats_ids)} in adv_stats ({coverage_pct:.1f}% coverage)")
                if missing_in_adv and len(missing_in_adv) > 10:
                    print(f"   ℹ️  {len(missing_in_adv)} game IDs in games.csv but not in adv_stats (likely incomplete games)")
                if missing_in_games:
                    print(f"   ℹ️  {len(missing_in_games)} game IDs in adv_stats but not in games.csv")

            # Check team name consistency
            try:
                teams_df = pd.read_csv(self.data_dir / "teams.csv")
                teams_list = set(teams_df["school"].unique()) if "school" in teams_df.columns else set()

                if "team" in adv_stats_df.columns:
                    adv_teams = set(adv_stats_df["team"].unique())
                    missing_teams = adv_teams - teams_list

                    results["team_consistency"] = {
                        "teams_in_reference": len(teams_list),
                        "teams_in_adv_stats": len(adv_teams),
                        "missing_teams": len(missing_teams),
                        "consistent": len(missing_teams) == 0
                    }

                    status = "✅" if results["team_consistency"]["consistent"] else "⚠️"
                    print(f"{status} Team name consistency: {len(teams_list)} reference teams, {len(adv_teams)} in adv_stats")
                    if missing_teams:
                        print(f"   {len(missing_teams)} teams in adv_stats not in reference: {list(missing_teams)[:5]}")

            except Exception as e:
                results["team_consistency"] = {"error": str(e)}
                print(f"⚠️  Team consistency check: Error - {e}")

        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Cross-reference validation: Error - {e}")

        self.results["cross_reference"] = results
        return results

    def generate_report(self) -> Dict:
        """Generate comprehensive verification report."""
        print("\n" + "=" * 80)
        print("STEP 6: Generating Verification Report")
        print("=" * 80)

        # Calculate summary statistics
        file_existence = self.results["file_existence"]
        # Count only actual data files (exclude reference files)
        main_file_keys = [k for k in file_existence.keys() if not k.startswith("ref_") and not k.startswith("plays_week_")]
        files_exist = sum(1 for k in main_file_keys if file_existence[k].get("exists", False))
        total_files = len(main_file_keys)
        total_play_files = len([k for k in file_existence.keys() if k.startswith("plays_week_")])
        play_files_exist = sum(1 for k, v in file_existence.items() if k.startswith("plays_week_") and v.get("exists", False))

        schema_passed = sum(1 for v in self.results["schema_compliance"].values() if v.get("status") == "PASS")
        schema_total = len(self.results["schema_compliance"])

        completeness = self.results["data_completeness"]
        has_all_weeks = (
            completeness.get("advanced_game_stats", {}).get("has_all_weeks", False) and
            completeness.get("plays", {}).get("has_all_weeks", False)
        )

        # Check cross-reference consistency
        cross_ref = self.results["cross_reference"]
        game_id_consistent = cross_ref.get("game_id_consistency", {}).get("consistent", False)

        # Overall status: PASS if all critical checks pass
        overall_pass = (
            files_exist == total_files and
            play_files_exist == total_play_files and
            schema_passed == schema_total and
            has_all_weeks and
            game_id_consistent
        )

        self.results["summary"] = {
            "verification_date": pd.Timestamp.now().isoformat(),
            "year": YEAR,
            "week_range": f"{START_WEEK}-{END_WEEK}",
            "files_exist": f"{files_exist}/{total_files} main files, {play_files_exist}/{total_play_files} play files",
            "schema_compliance": f"{schema_passed}/{schema_total} files pass",
            "has_all_weeks": has_all_weeks,
            "game_id_consistency": game_id_consistent,
            "overall_status": "PASS" if overall_pass else "REVIEW"
        }

        # Print summary
        print(f"\n{'='*80}")
        print("VERIFICATION SUMMARY")
        print(f"{'='*80}")
        print(f"Year: {YEAR}")
        print(f"Week Range: {START_WEEK}-{END_WEEK}")
        print(f"Files Exist: {files_exist}/{total_files} main files, {play_files_exist}/{total_play_files} play files")
        print(f"Schema Compliance: {schema_passed}/{schema_total} files pass")
        print(f"Has All Weeks: {'✅' if has_all_weeks else '❌'}")
        print(f"Game ID Consistency: {'✅' if game_id_consistent else '⚠️'}")
        print(f"Overall Status: {self.results['summary']['overall_status']}")

        return self.results

    def save_report(self, output_path: Optional[Path] = None):
        """Save verification report to JSON file."""
        if output_path is None:
            output_path = self.data_dir / f"{YEAR}_verification_report.json"

        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n✅ Report saved to: {output_path}")
        
        # Also print a clear status message
        status = self.results["summary"]["overall_status"]
        if status == "PASS":
            print(f"\n✅ VERIFICATION COMPLETE: All checks passed!")
            print(f"   Starter pack data is ready for use with model packs and notebooks.")
        else:
            print(f"\n⚠️  VERIFICATION COMPLETE: Status is {status}")
            print(f"   Review the report above for details.")

    def run_all_checks(self):
        """Run all verification steps."""
        print("=" * 80)
        print("STARTER PACK DATA VERIFICATION")
        print(f"Year: {YEAR}, Weeks: {START_WEEK}-{END_WEEK}")
        print("=" * 80)

        self.verify_file_existence()
        self.verify_schema_compliance()
        self.verify_data_completeness()
        self.verify_data_quality()
        self.cross_reference_validation()
        self.generate_report()
        self.save_report()

        return self.results


def main():
    """Main execution function."""
    verifier = StarterPackDataVerifier()
    results = verifier.run_all_checks()

    # Exit with appropriate code
    if results["summary"]["overall_status"] == "PASS":
        print("\n✅ All verification checks passed!")
        return 0
    else:
        print("\n⚠️  Some verification checks need review. See report for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

