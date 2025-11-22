#!/usr/bin/env python3
"""
API SOURCE VALIDATOR AGENT
Mission: Verify CFBD API returns authentic 2025 data, not fallbacks/cached data

Critical Question: "Is this REAL 2025 data or a fallback from previous seasons?"

Created: 2025-11-13
Purpose: Comprehensive CFBD API authentication and data freshness validation
"""

import logging
import time
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

try:
    import cfbd
except ImportError:
    print("❌ CFBD library not installed")
    cfbd = None

class APISourceValidator:
    """
    Validates that CFBD API returns authentic, current 2025 data

    Key validations:
    1. API authentication and rate limiting
    2. Data freshness (current through Nov 13, 2025)
    3. No 2024/2023 data leakage in 2025 queries
    4. Response quality and completeness
    """

    def __init__(self, project_root: str = "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"):
        self.project_root = project_root
        self.logger = self._setup_logging()
        self.validation_results = {}

        # Critical validation parameters
        self.TARGET_DATE = datetime(2025, 11, 13, tzinfo=timezone.utc)
        self.CURRENT_WEEK = 12  # Week 12 as of Nov 13, 2025
        self.EXPECTED_2025_GAMES_MIN = 600  # Minimum games expected by Week 12
        self.FRESHNESS_THRESHOLD_DAYS = 7  # Data must be within 7 days

        self.logger.info("🔍 API Source Validator initialized")
        self.logger.info(f"🎯 Target validation date: {self.TARGET_DATE.strftime('%Y-%m-%d')}")
        self.logger.info(f"📊 Current week: {self.CURRENT_WEEK}")

    def _setup_logging(self) -> logging.Logger:
        """Setup validation logging"""
        logger = logging.getLogger("APISourceValidator")
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

    def validate_api_source(self) -> Dict[str, Any]:
        """
        Main validation function for CFBD API source

        Returns:
            Dict containing comprehensive API validation results
        """
        self.logger.info("🚀 Starting CFBD API source validation")

        validation_results = {
            "validation_type": "api_source",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "authenticity_checks": {},
            "freshness_checks": {},
            "completeness_checks": {},
            "critical_issues": [],
            "warnings": [],
            "tested_endpoints": [],
            "authenticity_score": 0.0,
            "recommendations": []
        }

        # Step 1: Environment and authentication check
        auth_results = self._validate_authentication()
        validation_results["authenticity_checks"]["authentication"] = auth_results

        if auth_results.get("critical_issues"):
            validation_results["critical_issues"].extend(auth_results["critical_issues"])
            self.logger.error("❌ Authentication failed - cannot proceed")
            return validation_results

        # Step 2: Test critical 2025 endpoints
        endpoint_results = self._test_2025_endpoints()
        validation_results["tested_endpoints"] = endpoint_results["endpoints"]
        validation_results["authenticity_checks"]["endpoints"] = endpoint_results

        if endpoint_results.get("critical_issues"):
            validation_results["critical_issues"].extend(endpoint_results["critical_issues"])

        # Step 3: Data freshness validation
        freshness_results = self._validate_data_freshness()
        validation_results["freshness_checks"] = freshness_results

        if freshness_results.get("critical_issues"):
            validation_results["critical_issues"].extend(freshness_results["critical_issues"])

        # Step 4: Data completeness validation
        completeness_results = self._validate_data_completeness()
        validation_results["completeness_checks"] = completeness_results

        if completeness_results.get("critical_issues"):
            validation_results["critical_issues"].extend(completeness_results["critical_issues"])

        # Step 5: Check for data leakage (2024/2023 data in 2025 responses)
        leakage_results = self._check_data_leakage()
        validation_results["authenticity_checks"]["data_leakage"] = leakage_results

        if leakage_results.get("critical_issues"):
            validation_results["critical_issues"].extend(leakage_results["critical_issues"])

        # Calculate overall authenticity score
        validation_results["authenticity_score"] = self._calculate_authenticity_score(validation_results)

        # Generate recommendations
        validation_results["recommendations"] = self._generate_recommendations(validation_results)

        # Save detailed results
        self._save_validation_results(validation_results)

        self.logger.info(f"✅ API Source validation complete - Authenticity Score: {validation_results['authenticity_score']:.1%}")

        return validation_results

    def _validate_authentication(self) -> Dict[str, Any]:
        """Validate CFBD API authentication"""
        self.logger.info("🔐 Validating CFBD API authentication")

        results = {
            "authentication_successful": False,
            "api_key_present": False,
            "connection_successful": False,
            "critical_issues": [],
            "warnings": []
        }

        # Check for API key
        api_key = os.environ.get("CFBD_API_KEY")
        if not api_key:
            results["critical_issues"].append("CFBD_API_KEY not found in environment variables")
            return results

        results["api_key_present"] = True
        self.logger.info("✅ CFBD API key found")

        # Test API connection
        if cfbd is None:
            results["critical_issues"].append("CFBD Python library not installed")
            return results

        try:
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            with cfbd.ApiClient(configuration) as api_client:
                # Simple test call
                teams_api = cfbd.TeamsApi(api_client)
                teams = teams_api.get_fbs_teams(year=2025)

                if teams is not None:
                    results["connection_successful"] = True
                    results["authentication_successful"] = True
                    self.logger.info("✅ CFBD API authentication successful")
                else:
                    results["critical_issues"].append("API returned None response")

        except Exception as e:
            error_msg = f"CFBD API connection failed: {str(e)}"
            results["critical_issues"].append(error_msg)
            self.logger.error(error_msg)

        return results

    def _test_2025_endpoints(self) -> Dict[str, Any]:
        """Test critical CFBD endpoints for 2025 data"""
        self.logger.info("🧪 Testing critical 2025 endpoints")

        results = {
            "endpoints": [],
            "critical_issues": [],
            "warnings": []
        }

        # Define critical endpoints to test
        test_endpoints = [
            {
                "name": "2025 Games Week 12",
                "api_method": "get_games",
                "params": {"year": 2025, "week": 12},
                "expected_min_records": 30,
                "authenticity_checks": ["season_2025", "week_12", "reasonable_teams"]
            },
            {
                "name": "2025 Games All",
                "api_method": "get_games",
                "params": {"year": 2025},
                "expected_min_records": self.EXPECTED_2025_GAMES_MIN,
                "authenticity_checks": ["season_2025", "reasonable_game_count", "date_range_2025"]
            },
            {
                "name": "2025 Teams",
                "api_method": "get_fbs_teams",
                "params": {"year": 2025},
                "expected_min_records": 130,  # FBS teams
                "authenticity_checks": ["fbs_team_count", "team_data_quality"]
            },
            {
                "name": "2025 Games Week 11",
                "api_method": "get_games",
                "params": {"year": 2025, "week": 11},
                "expected_min_records": 30,
                "authenticity_checks": ["season_2025", "week_11", "completion_status"]
            }
        ]

        # Get API configuration
        api_key = os.environ.get("CFBD_API_KEY")
        configuration = cfbd.Configuration()
        configuration.api_key['Authorization'] = api_key
        configuration.api_key_prefix['Authorization'] = 'Bearer'

        try:
            with cfbd.ApiClient(configuration) as api_client:
                for endpoint_test in test_endpoints:
                    self.logger.info(f"🔍 Testing: {endpoint_test['name']}")

                    endpoint_result = self._test_single_endpoint(api_client, endpoint_test)
                    results["endpoints"].append(endpoint_result)

                    # Check for critical issues
                    if endpoint_result["status"] != "success":
                        results["critical_issues"].append(
                            f"Endpoint test failed: {endpoint_test['name']} - {endpoint_result.get('error', 'Unknown error')}"
                        )

                    # Rate limiting
                    time.sleep(0.2)

        except Exception as e:
            results["critical_issues"].append(f"Endpoint testing failed: {str(e)}")

        self.logger.info(f"✅ Endpoint testing complete - {len(results['endpoints'])} endpoints tested")

        return results

    def _test_single_endpoint(self, api_client, endpoint_config: Dict) -> Dict[str, Any]:
        """Test a single CFBD endpoint"""
        try:
            # Determine API method
            if endpoint_config["api_method"] == "get_games":
                api = cfbd.GamesApi(api_client)
                if "week" in endpoint_config["params"]:
                    data = api.get_games(
                        year=endpoint_config["params"]["year"],
                        week=endpoint_config["params"]["week"]
                    )
                else:
                    data = api.get_games(year=endpoint_config["params"]["year"])

            elif endpoint_config["api_method"] == "get_fbs_teams":
                api = cfbd.TeamsApi(api_client)
                data = api.get_fbs_teams(year=endpoint_config["params"]["year"])

            else:
                return {
                    "name": endpoint_config["name"],
                    "status": "error",
                    "error": f"Unknown API method: {endpoint_config['api_method']}",
                    "authenticity_checks": {}
                }

            # Analyze response for authenticity
            authenticity_result = self._analyze_response_authenticity(
                data, endpoint_config
            )

            return {
                "name": endpoint_config["name"],
                "status": "success",
                "record_count": len(data) if data else 0,
                "authenticity_checks": authenticity_result,
                "sample_data": self._create_sample_data(data, endpoint_config) if data else []
            }

        except Exception as e:
            return {
                "name": endpoint_config["name"],
                "status": "error",
                "error": str(e),
                "authenticity_checks": {}
            }

    def _analyze_response_authenticity(self, data, endpoint_config: Dict) -> Dict[str, Any]:
        """Analyze API response for 2025 authenticity indicators"""
        authenticity_checks = {}

        if not data:
            authenticity_checks["no_data_returned"] = True
            return authenticity_checks

        # Convert to DataFrame for analysis
        if hasattr(data[0], '__dict__'):  # CFBD objects
            records = []
            for item in data:
                record = {}
                for attr in dir(item):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(item, attr)
                            if not callable(value):
                                record[attr] = value
                        except:
                            pass
                df = pd.DataFrame([record]) if record else pd.DataFrame()
            records = [record for record in records if record]
            df = pd.DataFrame(records) if records else pd.DataFrame()
        else:
            df = pd.DataFrame(data)

        # Run authenticity checks based on endpoint type
        if "games" in endpoint_config["api_method"]:
            authenticity_checks = self._check_games_authenticity(df, endpoint_config)
        elif "teams" in endpoint_config["api_method"]:
            authenticity_checks = self._check_teams_authenticity(df, endpoint_config)

        return authenticity_checks

    def _check_games_authenticity(self, df: pd.DataFrame, endpoint_config: Dict) -> Dict[str, Any]:
        """Check games data for 2025 authenticity"""
        checks = {}

        if df.empty:
            checks["empty_dataframe"] = True
            return checks

        # Check all games are from 2025
        if "season" in df.columns:
            checks["all_2025_season"] = (df["season"] == 2025).all()
        else:
            checks["season_column_missing"] = True

        # Check correct week
        if "week" in df.columns and "week" in endpoint_config["params"]:
            expected_week = endpoint_config["params"]["week"]
            checks["correct_week"] = (df["week"] == expected_week).all()
        else:
            checks["week_column_present"] = "week" in df.columns

        # Check for reasonable team count
        if "home_team" in df.columns:
            unique_teams = len(pd.concat([df["home_team"], df["away_team"]]).unique())
            checks["reasonable_team_count"] = unique_teams >= 50  # Reasonable for a week

        # Check for score data (indicates completed games)
        has_scores = False
        if "home_points" in df.columns and "away_points" in df.columns:
            has_scores = (df["home_points"].notna() & df["away_points"].notna()).any()
        checks["has_score_data"] = has_scores

        # Check date ranges
        if "start_date" in df.columns:
            try:
                df["start_date"] = pd.to_datetime(df["start_date"])
                checks["dates_in_2025"] = (df["start_date"].dt.year == 2025).all()

                # Check if dates are reasonable for 2025 season
                season_start = datetime(2025, 8, 1, tzinfo=timezone.utc)
                season_end = self.TARGET_DATE
                checks["reasonable_date_range"] = (
                    (df["start_date"] >= season_start) &
                    (df["start_date"] <= season_end)
                ).all()
            except:
                checks["date_parsing_failed"] = True

        # Check completion status
        if "completed" in df.columns:
            checks["completion_status_present"] = True
            # For past weeks, most games should be completed
            if "week" in endpoint_config["params"] and endpoint_config["params"]["week"] < self.CURRENT_WEEK:
                completion_rate = df["completed"].mean() if df["completed"].dtype != 'object' else 0
                checks["reasonable_completion_rate"] = completion_rate >= 0.8

        return checks

    def _check_teams_authenticity(self, df: pd.DataFrame, endpoint_config: Dict) -> Dict[str, Any]:
        """Check teams data for 2025 authenticity"""
        checks = {}

        if df.empty:
            checks["empty_dataframe"] = True
            return checks

        # Check for reasonable number of FBS teams
        checks["fbs_team_count"] = len(df) >= 130  # Approximate FBS team count

        # Check for essential team data columns
        essential_columns = ["school", "conference"]
        checks["essential_columns_present"] = all(col in df.columns for col in essential_columns)

        # Check for 2025-specific data if available
        if "year" in df.columns:
            checks["all_2025_teams"] = (df["year"] == 2025).all()

        # Check conference data quality
        if "conference" in df.columns:
            unique_conferences = df["conference"].nunique()
            checks["reasonable_conference_count"] = 10 <= unique_conferences <= 15  # Reasonable range

        return checks

    def _create_sample_data(self, data, endpoint_config: Dict) -> List[Dict]:
        """Create sample data for inspection"""
        if not data:
            return []

        sample_size = min(3, len(data))
        sample_data = []

        for i in range(sample_size):
            item = data[i]
            if hasattr(item, '__dict__'):  # CFBD object
                record = {}
                for attr in dir(item):
                    if not attr.startswith('_') and not callable(getattr(item, attr)):
                        try:
                            value = getattr(item, attr)
                            if value is not None:
                                record[attr] = value
                        except:
                            pass
                sample_data.append(record)

        return sample_data

    def _validate_data_freshness(self) -> Dict[str, Any]:
        """Validate data freshness - current through Nov 13, 2025"""
        self.logger.info("🕒 Validating data freshness")

        results = {
            "freshness_checks": {},
            "critical_issues": [],
            "warnings": []
        }

        # Check most recent game data
        try:
            api_key = os.environ.get("CFBD_API_KEY")
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            with cfbd.ApiClient(configuration) as api_client:
                games_api = cfbd.GamesApi(api_client)

                # Get games from current week
                current_week_games = games_api.get_games(year=2025, week=self.CURRENT_WEEK)

                if current_week_games:
                    # Find the most recent game
                    most_recent_date = None
                    for game in current_week_games:
                        if hasattr(game, 'start_date') and game.start_date:
                            game_date = pd.to_datetime(game.start_date)
                            if most_recent_date is None or game_date > most_recent_date:
                                most_recent_date = game_date

                    if most_recent_date:
                        days_old = (self.TARGET_DATE - most_recent_date).days
                        results["freshness_checks"]["days_since_last_game"] = days_old
                        results["freshness_checks"]["data_current"] = days_old <= self.FRESHNESS_THRESHOLD_DAYS

                        if days_old > self.FRESHNESS_THRESHOLD_DAYS:
                            results["warnings"].append(f"Data may be stale - last game {days_old} days ago")
                    else:
                        results["critical_issues"].append("Could not determine most recent game date")
                else:
                    results["warnings"].append(f"No games found for Week {self.CURRENT_WEEK}")

        except Exception as e:
            results["critical_issues"].append(f"Freshness validation failed: {str(e)}")

        return results

    def _validate_data_completeness(self) -> Dict[str, Any]:
        """Validate data completeness for 2025 season"""
        self.logger.info("📊 Validating data completeness")

        results = {
            "completeness_metrics": {},
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

                # Count games for each week up to current week
                weekly_game_counts = {}
                total_games = 0

                for week in range(1, self.CURRENT_WEEK + 1):
                    try:
                        week_games = games_api.get_games(year=2025, week=week)
                        game_count = len(week_games) if week_games else 0
                        weekly_game_counts[f"week_{week}"] = game_count
                        total_games += game_count

                        # Check for suspiciously low game counts
                        if game_count < 20:  # Unusually low for a regular season week
                            results["warnings"].append(f"Week {week} has only {game_count} games")

                        time.sleep(0.2)  # Rate limiting
                    except Exception as e:
                        results["warnings"].append(f"Could not retrieve Week {week} games: {str(e)}")

                results["completeness_metrics"]["weekly_game_counts"] = weekly_game_counts
                results["completeness_metrics"]["total_games_through_current_week"] = total_games
                results["completeness_metrics"]["average_games_per_week"] = total_games / self.CURRENT_WEEK

                # Check if total games meet expectations
                if total_games < self.EXPECTED_2025_GAMES_MIN:
                    results["critical_issues"].append(
                        f"Total games ({total_games}) below expected minimum ({self.EXPECTED_2025_GAMES_MIN})"
                    )

        except Exception as e:
            results["critical_issues"].append(f"Completeness validation failed: {str(e)}")

        return results

    def _check_data_leakage(self) -> Dict[str, Any]:
        """Check for data leakage from previous seasons"""
        self.logger.info("🔍 Checking for data leakage")

        results = {
            "leakage_checks": {},
            "critical_issues": [],
            "warnings": []
        }

        # Test 2025-specific queries don't return 2024/2023 data
        try:
            api_key = os.environ.get("CFBD_API_KEY")
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            with cfbd.ApiClient(configuration) as api_client:
                games_api = cfbd.GamesApi(api_client)

                # Get 2025 games and check for any that aren't actually 2025
                games_2025 = games_api.get_games(year=2025)

                if games_2025:
                    # Check for any games with wrong season
                    wrong_season_count = 0
                    for game in games_2025:
                        if hasattr(game, 'season') and game.season != 2025:
                            wrong_season_count += 1

                    results["leakage_checks"]["wrong_season_games"] = wrong_season_count

                    if wrong_season_count > 0:
                        results["critical_issues"].append(f"Found {wrong_season_count} games with wrong season in 2025 query")
                    else:
                        results["leakage_checks"]["no_season_leakage"] = True

                # Additional leakage checks can be added here

        except Exception as e:
            results["critical_issues"].append(f"Leakage check failed: {str(e)}")

        return results

    def _calculate_authenticity_score(self, validation_results: Dict) -> float:
        """Calculate overall API authenticity score"""
        score_components = []

        # Authentication score (30% weight)
        auth_checks = validation_results.get("authenticity_checks", {})
        if auth_checks.get("authentication", {}).get("authentication_successful", False):
            score_components.append(1.0)
        else:
            score_components.append(0.0)

        # Endpoint success score (40% weight)
        endpoints = validation_results.get("tested_endpoints", [])
        if endpoints:
            successful_endpoints = sum(1 for ep in endpoints if ep.get("status") == "success")
            endpoint_score = successful_endpoints / len(endpoints)
            score_components.append(endpoint_score)
        else:
            score_components.append(0.0)

        # Freshness score (15% weight)
        freshness = validation_results.get("freshness_checks", {})
        if freshness.get("freshness_checks", {}).get("data_current", False):
            score_components.append(1.0)
        else:
            score_components.append(0.5)  # Partial credit for having some data

        # Completeness score (15% weight)
        completeness = validation_results.get("completeness_checks", {})
        if not completeness.get("critical_issues"):
            score_components.append(1.0)
        else:
            score_components.append(0.0)

        # Calculate weighted average
        weights = [0.3, 0.4, 0.15, 0.15]
        weighted_score = sum(score * weight for score, weight in zip(score_components, weights))

        return weighted_score

    def _generate_recommendations(self, validation_results: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        if validation_results["authenticity_score"] < 0.8:
            recommendations.append("🚨 CRITICAL: API authenticity score below 80% - investigate immediately")

        if validation_results["critical_issues"]:
            recommendations.append(f"🚨 Address {len(validation_results['critical_issues'])} critical issues before proceeding")

        if validation_results["warnings"]:
            recommendations.append(f"⚠️ Review {len(validation_results['warnings'])} warnings for optimal performance")

        # Specific recommendations based on check results
        freshness = validation_results.get("freshness_checks", {})
        if not freshness.get("freshness_checks", {}).get("data_current", True):
            recommendations.append("📅 Data may be stale - consider refreshing API cache or checking update frequency")

        completeness = validation_results.get("completeness_checks", {})
        total_games = completeness.get("completeness_metrics", {}).get("total_games_through_current_week", 0)
        if total_games < self.EXPECTED_2025_GAMES_MIN:
            recommendations.append(f"📊 Game count ({total_games}) below expectations - investigate missing games")

        return recommendations

    def _save_validation_results(self, results: Dict) -> None:
        """Save detailed validation results"""
        results_dir = f"{self.project_root}/project_management/DATA_VALIDATION"
        os.makedirs(results_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"{results_dir}/api_validation_{timestamp}.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        self.logger.info(f"📄 API validation results saved: {results_file}")

def main():
    """Main execution function"""
    validator = APISourceValidator()
    results = validator.validate_api_source()

    print("\n" + "="*80)
    print("🔍 API SOURCE VALIDATION COMPLETE")
    print("="*80)
    print(f"📊 Authenticity Score: {results['authenticity_score']:.1%}")
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