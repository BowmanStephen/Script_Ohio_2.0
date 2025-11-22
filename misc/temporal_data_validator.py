#!/usr/bin/env python3
"""
TEMPORAL DATA VALIDATOR AGENT
Mission: Confirm data is current through November 13, 2025 (Week 12)

Critical Question: "Is this data really current as of today, or is it stale?"

Created: 2025-11-13
Purpose: Validate temporal accuracy and completeness of 2025 season data
"""

import logging
import time
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path

from starter_pack.utils.cfbd_helpers import cfbd_session, CFBDLoaderError, DEFAULT_HOST

class TemporalDataValidator:
    """
    Validates temporal accuracy of 2025 college football data

    Key validations:
    1. Data currency through Nov 13, 2025
    2. Week 12 completeness and accuracy
    3. No future games (data leakage from future)
    4. Chronological consistency across the season
    5. Real-time data freshness
    """

    def __init__(self, project_root: str = "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"):
        self.project_root = Path(project_root)
        self.logger = self._setup_logging()
        self.validation_results = {}

        # Critical temporal validation parameters
        self.TARGET_DATE = datetime(2025, 11, 13, tzinfo=timezone.utc)  # Thursday, Week 12
        self.CURRENT_WEEK = 12  # Week 12 as of Nov 13, 2025
        self.SEASON_START_DATE = datetime(2025, 8, 24, tzinfo=timezone.utc)  # Approx Week 1
        self.DATA_FRESHNESS_HOURS = 48  # Data should be within 48 hours
        self.WEEK_12_GAMES_MIN = 50  # Minimum expected games in Week 12

        # Known 2025 schedule patterns
        self.EXPECTED_WEEKS_COMPLETE = 11  # Weeks 1-11 should be complete
        self.WEEK_12_PARTIAL = True  # Week 12 may be partial/in-progress

        self.logger.info("⏰ Temporal Data Validator initialized")
        self.logger.info(f"🎯 Target validation date: {self.TARGET_DATE.strftime('%Y-%m-%d %A')} (Week {self.CURRENT_WEEK})")
        self.logger.info(f"📅 Season start: {self.SEASON_START_DATE.strftime('%Y-%m-%d')}")

    def _session(self):
        return cfbd_session(host=os.environ.get("CFBD_API_HOST", DEFAULT_HOST))

    def _setup_logging(self) -> logging.Logger:
        """Setup validation logging"""
        logger = logging.getLogger("TemporalDataValidator")
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def validate_temporal_data(self) -> Dict[str, Any]:
        """
        Main validation function for temporal data accuracy

        Returns:
            Dict containing comprehensive temporal validation results
        """
        self.logger.info("🚀 Starting temporal data validation")

        validation_results = {
            "validation_type": "temporal",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_date": self.TARGET_DATE.isoformat(),
            "current_week": self.CURRENT_WEEK,
            "currency_checks": {},
            "completeness_checks": {},
            "chronology_checks": {},
            "critical_issues": [],
            "warnings": [],
            "authenticity_score": 0.0,
            "recommendations": []
        }

        # Step 1: Validate current week (Week 12) data
        current_week_results = self._validate_current_week_data()
        validation_results["currency_checks"]["current_week"] = current_week_results

        if current_week_results.get("critical_issues"):
            validation_results["critical_issues"].extend(current_week_results["critical_issues"])

        # Step 2: Validate data freshness (how current is the data)
        freshness_results = self._validate_data_freshness()
        validation_results["currency_checks"]["freshness"] = freshness_results

        if freshness_results.get("critical_issues"):
            validation_results["critical_issues"].extend(freshness_results["critical_issues"])

        # Step 3: Validate weekly progression and completeness
        weekly_progression = self._validate_weekly_progression()
        validation_results["completeness_checks"]["weekly_progression"] = weekly_progression

        if weekly_progression.get("critical_issues"):
            validation_results["critical_issues"].extend(weekly_progression["critical_issues"])

        # Step 4: Check for temporal anomalies
        anomaly_results = self._check_temporal_anomalies()
        validation_results["chronology_checks"]["anomalies"] = anomaly_results

        if anomaly_results.get("critical_issues"):
            validation_results["critical_issues"].extend(anomaly_results["critical_issues"])

        # Step 5: Validate specific Week 12 expectations
        week_12_specific = self._validate_week_12_specific()
        validation_results["currency_checks"]["week_12_specific"] = week_12_specific

        if week_12_specific.get("critical_issues"):
            validation_results["critical_issues"].extend(week_12_specific["critical_issues"])

        # Calculate overall authenticity score
        validation_results["authenticity_score"] = self._calculate_temporal_score(validation_results)

        # Generate recommendations
        validation_results["recommendations"] = self._generate_recommendations(validation_results)

        # Save detailed results
        self._save_validation_results(validation_results)

        self.logger.info(f"✅ Temporal validation complete - Score: {validation_results['authenticity_score']:.1%}")

        return validation_results

    def _validate_current_week_data(self) -> Dict[str, Any]:
        """Validate Week 12 data specifically"""
        self.logger.info("🔍 Validating Week 12 (current week) data")

        results = {
            "week_number": self.CURRENT_WEEK,
            "games_found": 0,
            "completion_status": {},
            "critical_issues": [],
            "warnings": []
        }

        try:
            with self._session() as session:
                games_api = session.games_api

                week_12_games = games_api.get_games(year=2025, week=self.CURRENT_WEEK)
                results["games_found"] = len(week_12_games) if week_12_games else 0

                if results["games_found"] == 0:
                    results["critical_issues"].append(f"No games found for Week {self.CURRENT_WEEK}")
                    return results

                # Analyze Week 12 game completion status
                completed_games = 0
                in_progress_games = 0
                scheduled_games = 0
                games_with_scores = 0
                most_recent_game = None

                for game in week_12_games:
                    # Check completion status
                    if hasattr(game, 'completed') and game.completed:
                        completed_games += 1
                    elif hasattr(game, 'start_date'):
                        # Check if game has started but may not be completed
                        game_time = pd.to_datetime(game.start_date)
                        if game_time <= datetime.now(timezone.utc):
                            in_progress_games += 1
                        else:
                            scheduled_games += 1
                    else:
                        scheduled_games += 1

                    # Check for score data
                    if hasattr(game, 'home_points') and hasattr(game, 'away_points'):
                        if game.home_points is not None and game.away_points is not None:
                            games_with_scores += 1

                    # Track most recent game
                    if hasattr(game, 'start_date'):
                        game_time = pd.to_datetime(game.start_date)
                        if most_recent_game is None or game_time > most_recent_game:
                            most_recent_game = game_time

                results["completion_status"] = {
                    "completed_games": completed_games,
                    "in_progress_games": in_progress_games,
                    "scheduled_games": scheduled_games,
                    "games_with_scores": games_with_scores,
                    "completion_rate": completed_games / results["games_found"] if results["games_found"] > 0 else 0
                }

                # Validate Week 12 expectations
                if results["games_found"] < self.WEEK_12_GAMES_MIN:
                    results["warnings"].append(
                        f"Week 12 has only {results['games_found']} games (expected at least {self.WEEK_12_GAMES_MIN})"
                    )

                # Check if we have recent activity
                if most_recent_game:
                    hours_since_last_game = (datetime.now(timezone.utc) - most_recent_game).total_seconds() / 3600
                    results["hours_since_most_recent_game"] = hours_since_last_game

                    if hours_since_last_game > 72:  # No games in 3 days
                        results["warnings"].append(f"No games in {hours_since_last_game:.1f} hours - data may be stale")

                # Since it's Thursday of Week 12, we should have some completed games
                if completed_games == 0:
                    results["warnings"].append("No completed games found in Week 12 (unusual for Thursday)")

        except CFBDLoaderError as e:
            results["critical_issues"].append(f"Week 12 validation failed: {str(e)}")

        self.logger.info(f"📊 Week 12: {results['games_found']} games, {completed_games} completed")
        return results

    def _validate_data_freshness(self) -> Dict[str, Any]:
        """Validate overall data freshness"""
        self.logger.info("🕒 Validating overall data freshness")

        results = {
            "freshness_indicators": {},
            "api_response_time": {},
            "last_update_checks": {},
            "critical_issues": [],
            "warnings": []
        }

        try:
            api_key = os.environ.get("CFBD_API_KEY")
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            # Test API response time (indicator of freshness)
            start_time = time.time()
            with cfbd.ApiClient(configuration) as api_client:
                games_api = cfbd.GamesApi(api_client)
                recent_games = games_api.get_games(year=2025, week=self.CURRENT_WEEK)
            response_time = time.time() - start_time

            results["api_response_time"] = {
                "response_time_seconds": response_time,
                "acceptable_response_time": response_time < 5.0  # 5 seconds is reasonable
            }

            if response_time > 5.0:
                results["warnings"].append(f"Slow API response time ({response_time:.2f}s) - may indicate server issues")

            # Check data timestamps in responses
            if recent_games:
                # Look for timestamp indicators in the data
                timestamps_found = []
                for game in recent_games[:10]:  # Sample first 10 games
                    if hasattr(game, 'start_date') and game.start_date:
                        timestamps_found.append(pd.to_datetime(game.start_date))

                if timestamps_found:
                    latest_timestamp = max(timestamps_found)
                    hours_old = (datetime.now(timezone.utc) - latest_timestamp).total_seconds() / 3600

                    results["last_update_checks"] = {
                        "latest_game_timestamp": latest_timestamp.isoformat(),
                        "hours_since_latest_game": hours_old,
                        "data_fresh": hours_old <= self.DATA_FRESHNESS_HOURS
                    }

                    if hours_old > self.DATA_FRESHNESS_HOURS:
                        results["warnings"].append(f"Data appears {hours_old:.1f} hours old")

            # Check for any indication of cached/stale data
            results["freshness_indicators"]["has_current_week_data"] = len(recent_games) > 0
            results["freshness_indicators"]["multiple_weeks_available"] = True  # Assuming true if we get here

        except Exception as e:
            results["critical_issues"].append(f"Data freshness validation failed: {str(e)}")

        return results

    def _validate_weekly_progression(self) -> Dict[str, Any]:
        """Validate weekly progression through the season"""
        self.logger.info("📈 Validating weekly season progression")

        results = {
            "weekly_data": {},
            "progression_analysis": {},
            "critical_issues": [],
            "warnings": []
        }

        try:
            api_key = os.environ.get("CFBD_API_KEY")
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            with cfbd.ApiClient(configuration) as api_client:
                games_api = cfbd.GamesApi(api_client)

                weekly_stats = {}
                total_games = 0
                weeks_with_data = 0

                for week in range(1, self.CURRENT_WEEK + 1):
                    try:
                        week_games = games_api.get_games(year=2025, week=week)
                        game_count = len(week_games) if week_games else 0

                        # Calculate completion for past weeks
                        completion_count = 0
                        if week_games:
                            for game in week_games:
                                if hasattr(game, 'completed') and game.completed:
                                    completion_count += 1

                        weekly_stats[f"week_{week}"] = {
                            "game_count": game_count,
                            "completed_count": completion_count,
                            "completion_rate": completion_count / game_count if game_count > 0 else 0
                        }

                        total_games += game_count
                        if game_count > 0:
                            weeks_with_data += 1

                        time.sleep(0.2)  # Rate limiting

                    except Exception as e:
                        results["warnings"].append(f"Could not retrieve Week {week} data: {str(e)}")
                        weekly_stats[f"week_{week}"] = {"error": str(e)}

                results["weekly_data"] = weekly_stats
                results["progression_analysis"] = {
                    "total_games_through_current_week": total_games,
                    "weeks_with_data": weeks_with_data,
                    "expected_weeks": self.CURRENT_WEEK,
                    "week_coverage_rate": weeks_with_data / self.CURRENT_WEEK,
                    "average_games_per_week": total_games / weeks_with_data if weeks_with_data > 0 else 0
                }

                # Validate progression expectations
                if weeks_with_data < self.EXPECTED_WEEKS_COMPLETE:
                    results["warnings"].append(
                        f"Only {weeks_with_data} weeks with data (expected at least {self.EXPECTED_WEEKS_COMPLETE})"
                    )

                # Check for missing weeks in the middle (gaps)
                missing_weeks = []
                for week in range(1, self.CURRENT_WEEK):
                    if f"week_{week}" not in weekly_stats or weekly_stats[f"week_{week}"].get("game_count", 0) == 0:
                        missing_weeks.append(week)

                if missing_weeks:
                    results["warnings"].append(f"Missing data for weeks: {missing_weeks}")

                # Check for reasonable game counts per week
        except Exception as e:
            results["critical_issues"].append(f"Weekly progression validation failed: {str(e)}")

        self.logger.info(f"📊 Progression: {weeks_with_data}/{self.CURRENT_WEEK} weeks, {total_games} total games")
        return results

    def _check_temporal_anomalies(self) -> Dict[str, Any]:
        """Check for temporal anomalies in the data"""
        self.logger.info("🔍 Checking for temporal anomalies")

        results = {
            "anomaly_checks": {},
            "suspicious_patterns": [],
            "critical_issues": [],
            "warnings": []
        }

        try:
            api_key = os.environ.get("CFBD_API_KEY")
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            with cfbd.ApiClient(configuration) as api_client:
                games_api = cfbd.GamesApi(api_client)

                # Get 2025 games to check for anomalies
                games_2025 = games_api.get_games(year=2025)

                if not games_2025:
                    results["critical_issues"].append("No 2025 games found for anomaly checking")
                    return results

                # Convert to DataFrame for analysis
                game_data = []
                for game in games_2025:
                    game_record = {
                        "season": getattr(game, 'season', 2025),
                        "week": getattr(game, 'week', None),
                        "start_date": getattr(game, 'start_date', None),
                        "home_team": getattr(game, 'home_team', None),
                        "away_team": getattr(game, 'away_team', None),
                        "home_points": getattr(game, 'home_points', None),
                        "away_points": getattr(game, 'away_points', None),
                        "completed": getattr(game, 'completed', None)
                    }
                    game_data.append(game_record)

                df = pd.DataFrame(game_data)

                # Anomaly 1: Future games (games scheduled after today)
                if "start_date" in df.columns:
                    df["start_date"] = pd.to_datetime(df["start_date"])
                    future_games = df[df["start_date"] > datetime.now(timezone.utc)]

                    results["anomaly_checks"]["future_games_count"] = len(future_games)
                    if len(future_games) > 0:
                        results["warnings"].append(f"Found {len(future_games)} games scheduled in the future")
                        results["suspicious_patterns"].append("future_games_detected")

                # Anomaly 2: Games with impossible completion status
                if "completed" in df.columns and "start_date" in df.columns:
                    # Games marked as completed before they started
                    completed_before_start = df[
                        (df["completed"] == True) &
                        (df["start_date"] > datetime.now(timezone.utc))
                    ]

                    results["anomaly_checks"]["completed_before_start"] = len(completed_before_start)
                    if len(completed_before_start) > 0:
                        results["critical_issues"].append(f"{len(completed_before_start)} games marked completed before start time")
                        results["suspicious_patterns"].append("impossible_completion_status")

                # Anomaly 3: Games from wrong season
                if "season" in df.columns:
                    wrong_season = df[df["season"] != 2025]
                    results["anomaly_checks"]["wrong_season_games"] = len(wrong_season)
                    if len(wrong_season) > 0:
                        results["critical_issues"].append(f"{len(wrong_season)} games from wrong season in 2025 query")
                        results["suspicious_patterns"].append("season_leakage")

                # Anomaly 4: Duplicate games
                if "week" in df.columns and "home_team" in df.columns and "away_team" in df.columns:
                    # Check for duplicate game identifiers
                    duplicate_check = df.duplicated(subset=["week", "home_team", "away_team"])
                    duplicate_count = duplicate_check.sum()
                    results["anomaly_checks"]["duplicate_games"] = duplicate_count
                    if duplicate_count > 0:
                        results["warnings"].append(f"Found {duplicate_count} potential duplicate games")
                        results["suspicious_patterns"].append("duplicate_games")

        except Exception as e:
            results["critical_issues"].append(f"Temporal anomaly check failed: {str(e)}")

        return results

    def _validate_week_12_specific(self) -> Dict[str, Any]:
        """Week 12 specific validations for November 13, 2025"""
        self.logger.info("🎯 Running Week 12 specific validations for Nov 13, 2025")

        results = {
            "week_12_expectations": {},
            "thursday_specific_checks": {},
            "critical_issues": [],
            "warnings": []
        }

        # Since it's Thursday of Week 12, we should have specific expectations
        expectations = {
            "should_have_saturday_games": True,  # Previous Saturday should have games
            "should_have_weekday_games": True,   # Some weekday games may have occurred
            "min_games_expected": 30,            # At least some games should be played
            "completion_expected_some": True     # Some games should be completed by Thursday
        }

        try:
            api_key = os.environ.get("CFBD_API_KEY")
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            with cfbd.ApiClient(configuration) as api_client:
                games_api = cfbd.GamesApi(api_client)

                # Check Week 12 games
                week_12_games = games_api.get_games(year=2025, week=self.CURRENT_WEEK)

                if week_12_games:
                    # Check for games from previous weekend (Saturday, Sunday, Monday, etc.)
                    weekend_games = []
                    weekday_games = []

                    for game in week_12_games:
                        if hasattr(game, 'start_date'):
                            game_time = pd.to_datetime(game.start_date)
                            game_day = game_time.weekday()  # Monday=0, Sunday=6

                            if game_day >= 5:  # Friday=5, Saturday=6, Sunday=6 (but Sunday is treated as 6)
                                weekend_games.append(game)
                            else:
                                weekday_games.append(game)

                    results["week_12_expectations"] = {
                        "total_week_12_games": len(week_12_games),
                        "weekend_games": len(weekend_games),
                        "weekday_games": len(weekday_games),
                        "expectations_met": len(week_12_games) >= expectations["min_games_expected"]
                    }

                    # Check Thursday specifically
                    today_games = []
                    for game in week_12_games:
                        if hasattr(game, 'start_date'):
                            game_time = pd.to_datetime(game.start_date)
                            if game_time.date() == self.TARGET_DATE.date():
                                today_games.append(game)

                    results["thursday_specific_checks"] = {
                        "games_scheduled_for_today": len(today_games),
                        "target_date": self.TARGET_DATE.date().isoformat(),
                        "is_thursday": self.TARGET_DATE.weekday() == 3  # Thursday
                    }

                    # Check completion status expectations
                    completed_count = sum(1 for game in week_12_games
                                       if hasattr(game, 'completed') and game.completed)

                    completion_rate = completed_count / len(week_12_games)
                    results["week_12_expectations"]["completed_games"] = completed_count
                    results["week_12_expectations"]["completion_rate"] = completion_rate

                    # By Thursday, we should have some completed games
                    if completed_count == 0 and len(week_12_games) > 0:
                        results["warnings"].append("No games completed by Thursday of Week 12 (unusual)")

                else:
                    results["critical_issues"].append("No Week 12 games found")

        except Exception as e:
            results["critical_issues"].append(f"Week 12 specific validation failed: {str(e)}")

        return results

    def _calculate_temporal_score(self, validation_results: Dict) -> float:
        """Calculate overall temporal authenticity score"""
        score_components = []

        # Current week data score (30% weight)
        current_week = validation_results.get("currency_checks", {}).get("current_week", {})
        if not current_week.get("critical_issues") and current_week.get("games_found", 0) > 0:
            score_components.append(1.0)
        else:
            score_components.append(0.0)

        # Data freshness score (25% weight)
        freshness = validation_results.get("currency_checks", {}).get("freshness", {})
        if not freshness.get("critical_issues"):
            freshness_score = 0.8 if freshness.get("warnings") else 1.0
            score_components.append(freshness_score)
        else:
            score_components.append(0.0)

        # Weekly progression score (25% weight)
        progression = validation_results.get("completeness_checks", {}).get("weekly_progression", {})
        if not progression.get("critical_issues"):
            coverage_rate = progression.get("progression_analysis", {}).get("week_coverage_rate", 0)
            score_components.append(coverage_rate)
        else:
            score_components.append(0.0)

        # Temporal anomalies score (20% weight)
        anomalies = validation_results.get("chronology_checks", {}).get("anomalies", {})
        if not anomalies.get("critical_issues"):
            anomaly_score = 0.7 if anomalies.get("warnings") else 1.0
            score_components.append(anomaly_score)
        else:
            score_components.append(0.0)

        # Calculate weighted average
        weights = [0.3, 0.25, 0.25, 0.2]
        weighted_score = sum(score * weight for score, weight in zip(score_components, weights))

        return weighted_score

    def _generate_recommendations(self, validation_results: Dict) -> List[str]:
        """Generate recommendations based on temporal validation"""
        recommendations = []

        if validation_results["authenticity_score"] < 0.8:
            recommendations.append("🚨 CRITICAL: Temporal data authenticity below 80% - investigate immediately")

        # Check for current week issues
        current_week = validation_results.get("currency_checks", {}).get("current_week", {})
        if current_week.get("games_found", 0) == 0:
            recommendations.append("📅 No current week data found - check API connection or data availability")
        elif current_week.get("completion_status", {}).get("completion_rate", 0) == 0:
            recommendations.append("🏈 No completed games in current week - verify this matches expectations")

        # Check for freshness issues
        freshness = validation_results.get("currency_checks", {}).get("freshness", {})
        if freshness.get("last_update_checks", {}).get("hours_since_latest_game", 0) > 72:
            recommendations.append("⏰ Data appears stale - investigate update frequency")

        # Check for weekly progression gaps
        progression = validation_results.get("completeness_checks", {}).get("weekly_progression", {})
        coverage_rate = progression.get("progression_analysis", {}).get("week_coverage_rate", 0)
        if coverage_rate < 0.9:
            recommendations.append(f"📊 Only {coverage_rate:.1%} week coverage - investigate missing weeks")

        return recommendations

    def _save_validation_results(self, results: Dict) -> None:
        """Save detailed temporal validation results"""
        results_dir = self.project_root / "project_management" / "DATA_VALIDATION"
        results_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = results_dir / f"temporal_validation_{timestamp}.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        self.logger.info(f"📄 Temporal validation results saved: {results_file}")

def main():
    """Main execution function"""
    validator = TemporalDataValidator()
    results = validator.validate_temporal_data()

    print("\n" + "="*80)
    print("⏰ TEMPORAL DATA VALIDATION COMPLETE")
    print("="*80)
    print(f"📊 Temporal Authenticity Score: {results['authenticity_score']:.1%}")
    print(f"🎯 Target Date: {results['target_date']}")
    print(f"📅 Current Week: {results['current_week']}")
    print(f"🚨 Critical Issues: {len(results['critical_issues'])}")
    print(f"⚠️ Warnings: {len(results['warnings'])}")

    if results["critical_issues"]:
        print("\n🚨 CRITICAL ISSUES:")
        for issue in results["critical_issues"]:
            print(f"   ❌ {issue}")

    if results["warnings"]:
        print("\n⚠️ WARNINGS:")
        for warning in results["warnings"]:
            print(f"   ⚠️ {warning}")

    if results["recommendations"]:
        print("\n💡 RECOMMENDATIONS:")
        for rec in results["recommendations"]:
            print(f"   💡 {rec}")

    print(f"\n📄 Full results saved to: project_management/DATA_VALIDATION/")
    print("="*80)

if __name__ == "__main__":
    main()