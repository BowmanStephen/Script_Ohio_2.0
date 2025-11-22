#!/usr/bin/env python3
"""
ADVANCED METRICS AUTHENTICATOR AGENT
Mission: Verify advanced metrics (EPA, PPA, success rates) are 2025-specific, not historical averages

Critical Question: "Are these complex metrics calculated using 2025 data or 2020-2024 baselines?"

Created: 2025-11-13
Purpose: Validate that advanced metrics use 2025 context, not historical fallbacks
"""

import logging
import time
import json
import os
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

try:
    import cfbd
except ImportError:
    print("❌ CFBD library not installed")
    cfbd = None

class AdvancedMetricsAuthenticator:
    """
    Validates that advanced metrics are calculated using 2025-specific data

    Key validations:
    1. EPA (Expected Points Added) uses 2025 season context
    2. PPA (Predicted Points Added) uses 2025 predictive models
    3. Success rates use 2025 down-distance context
    4. Opponent adjustments use 2025 season performance
    5. No pre-season projections mixed with actual results
    """

    def __init__(self, project_root: str = "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"):
        self.project_root = Path(project_root)
        self.logger = self._setup_logging()
        self.validation_results = {}

        # Advanced metrics validation parameters
        self.TARGET_DATE = datetime(2025, 11, 13, tzinfo=timezone.utc)
        self.CURRENT_WEEK = 12
        self.MIN_PLAYS_FOR_ANALYSIS = 100  # Minimum plays needed for metric validation
        self.EPA_REASONABLE_RANGE = (-3, 3)  # Reasonable EPA per play range
        self.SUCCESS_RATE_REASONABLE_RANGE = (0.2, 0.6)  # Reasonable success rate range

        # Historical baselines for comparison
        self.HISTORICAL_EPA_BASelines = {
            "2020_to_2024_avg": 0.05,  # Average EPA across 2020-2024
            "pass_epa_avg": 0.15,
            "rush_epa_avg": -0.02
        }

        self.logger.info("📊 Advanced Metrics Authenticator initialized")
        self.logger.info("🎯 Focus: EPA, PPA, success rates, opponent adjustments for 2025")

    def _setup_logging(self) -> logging.Logger:
        """Setup validation logging"""
        logger = logging.getLogger("AdvancedMetricsAuthenticator")
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

    def validate_advanced_metrics(self) -> Dict[str, Any]:
        """
        Main validation function for advanced metrics authenticity

        Returns:
            Dict containing comprehensive metrics validation results
        """
        self.logger.info("🚀 Starting advanced metrics authenticity validation")

        validation_results = {
            "validation_type": "advanced_metrics",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "epa_validation": {},
            "ppa_validation": {},
            "success_rate_validation": {},
            "opponent_adjustment_validation": {},
            "play_by_play_analysis": {},
            "critical_issues": [],
            "warnings": [],
            "authenticity_score": 0.0,
            "recommendations": []
        }

        # Step 1: Validate EPA (Expected Points Added) calculations
        epa_results = self._validate_epa_metrics()
        validation_results["epa_validation"] = epa_results

        if epa_results.get("critical_issues"):
            validation_results["critical_issues"].extend(epa_results["critical_issues"])

        # Step 2: Validate PPA (Predicted Points Added) if available
        ppa_results = self._validate_ppa_metrics()
        validation_results["ppa_validation"] = ppa_results

        if ppa_results.get("critical_issues"):
            validation_results["critical_issues"].extend(ppa_results["critical_issues"])

        # Step 3: Validate success rate calculations
        success_rate_results = self._validate_success_rate_metrics()
        validation_results["success_rate_validation"] = success_rate_results

        if success_rate_results.get("critical_issues"):
            validation_results["critical_issues"].extend(success_rate_results["critical_issues"])

        # Step 4: Validate opponent adjustments
        opponent_results = self._validate_opponent_adjustments()
        validation_results["opponent_adjustment_validation"] = opponent_results

        if opponent_results.get("critical_issues"):
            validation_results["critical_issues"].extend(opponent_results["critical_issues"])

        # Step 5: Analyze play-by-play data for 2025-specific patterns
        pbp_analysis = self._analyze_play_by_play_data()
        validation_results["play_by_play_analysis"] = pbp_analysis

        if pbp_analysis.get("critical_issues"):
            validation_results["critical_issues"].extend(pbp_analysis["critical_issues"])

        # Step 6: Check for pre-season projection contamination
        projection_check = self._check_projection_contamination()
        validation_results["projection_contamination_check"] = projection_check

        if projection_check.get("critical_issues"):
            validation_results["critical_issues"].extend(projection_check["critical_issues"])

        # Calculate overall authenticity score
        validation_results["authenticity_score"] = self._calculate_metrics_score(validation_results)

        # Generate recommendations
        validation_results["recommendations"] = self._generate_recommendations(validation_results)

        # Save detailed results
        self._save_validation_results(validation_results)

        self.logger.info(f"✅ Advanced metrics validation complete - Score: {validation_results['authenticity_score']:.1%}")

        return validation_results

    def _validate_epa_metrics(self) -> Dict[str, Any]:
        """Validate EPA calculations use 2025-specific context"""
        self.logger.info("📈 Validating EPA (Expected Points Added) metrics")

        results = {
            "epa_data_available": False,
            "epa_analysis": {},
            "historical_comparison": {},
            "critical_issues": [],
            "warnings": []
        }

        try:
            api_key = os.environ.get("CFBD_API_KEY")
            if not api_key:
                results["critical_issues"].append("CFBD_API_KEY not found")
                return results

            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            with cfbd.ApiClient(configuration) as api_client:
                # Try to get play-by-play data for EPA analysis
                try:
                    pbp_api = cfbd.PlaysApi(api_client)

                    # Get recent plays for EPA analysis
                    recent_plays = pbp_api.get_plays(year=2025, week=self.CURRENT_WEEK - 1)  # Previous completed week

                    if recent_plays and len(recent_plays) >= self.MIN_PLAYS_FOR_ANALYSIS:
                        results["epa_data_available"] = True

                        # Analyze EPA values in the data
                        epa_values = []
                        play_types = []

                        for play in recent_plays[:500]:  # Sample 500 plays for analysis
                            if hasattr(play, 'epa') and play.epa is not None:
                                epa_values.append(play.epa)

                            if hasattr(play, 'play_type') and play.play_type:
                                play_types.append(play.play_type)

                        if epa_values:
                            epa_array = np.array(epa_values)

                            results["epa_analysis"] = {
                                "total_plays_analyzed": len(epa_values),
                                "epa_mean": float(np.mean(epa_array)),
                                "epa_std": float(np.std(epa_array)),
                                "epa_min": float(np.min(epa_array)),
                                "epa_max": float(np.max(epa_array)),
                                "epa_values_in_reasonable_range": np.all(
                                    (epa_array >= self.EPA_REASONABLE_RANGE[0]) &
                                    (epa_array <= self.EPA_REASONABLE_RANGE[1])
                                ),
                                "play_type_distribution": {ptype: play_types.count(ptype) for ptype in set(play_types[:50])}
                            }

                            # Compare against historical baselines
                            current_epa_mean = np.mean(epa_array)
                            historical_avg = self.HISTORICAL_EPA_BASelines["2020_to_2024_avg"]

                            results["historical_comparison"] = {
                                "current_2025_epa_mean": current_epa_mean,
                                "historical_2020_2024_avg": historical_avg,
                                "difference_from_historical": current_epa_mean - historical_avg,
                                "percent_difference": ((current_epa_mean - historical_avg) / abs(historical_avg)) * 100 if historical_avg != 0 else 0,
                                "is_significantly_different": abs(current_epa_mean - historical_avg) > 0.05
                            }

                            # Check if EPA values seem to use 2025 context
                            if results["epa_analysis"]["epa_values_in_reasonable_range"]:
                                self.logger.info("✅ EPA values appear to be within reasonable ranges")
                            else:
                                results["warnings"].append("Some EPA values outside expected ranges")

                        else:
                            results["warnings"].append("No EPA values found in play-by-play data")

                    else:
                        results["warnings"].append("Insufficient play-by-play data for EPA analysis")

                except Exception as e:
                    results["warnings"].append(f"Could not access play-by-play API for EPA: {str(e)}")

                # Alternative: Check if EPA data is available through stats endpoints
                try:
                    stats_api = cfbd.StatsApi(api_client)
                    team_stats = stats_api.get_team_season_stats(year=2025)

                    if team_stats:
                        # Look for EPA-related stats
                        epa_related_stats = []
                        for stat in team_stats[:20]:  # Sample first 20 teams
                            if hasattr(stat, '__dict__'):
                                stat_dict = stat.__dict__
                                for key, value in stat_dict.items():
                                    if 'epa' in key.lower() and value is not None:
                                        epa_related_stats.append((key, value))

                        if epa_related_stats:
                            results["epa_analysis"]["team_epa_stats_available"] = True
                            results["epa_analysis"]["epa_stat_types"] = list(set([stat[0] for stat in epa_related_stats]))
                            self.logger.info(f"✅ Found {len(epa_related_stats)} EPA-related team stats")
                        else:
                            results["warnings"].append("No EPA-related stats found in team data")

                except Exception as e:
                    results["warnings"].append(f"Could not access team stats for EPA: {str(e)}")

        except Exception as e:
            results["critical_issues"].append(f"EPA validation failed: {str(e)}")

        return results

    def _validate_ppa_metrics(self) -> Dict[str, Any]:
        """Validate PPA (Predicted Points Added) calculations"""
        self.logger.info("🎯 Validating PPA (Predicted Points Added) metrics")

        results = {
            "ppa_data_available": False,
            "ppa_analysis": {},
            "critical_issues": [],
            "warnings": []
        }

        # PPA is often less commonly available than EPA
        # Check if PPA data exists in various CFBD endpoints

        try:
            api_key = os.environ.get("CFBD_API_KEY")
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            with cfbd.ApiClient(configuration) as api_client:
                # Check for PPA in player stats
                try:
                    player_stats_api = cfbd.PlayerStatsApi(api_client)
                    player_stats = player_stats_api.get_player_season_stats(year=2025)

                    if player_stats:
                        ppa_found = False
                        for stat in player_stats[:50]:  # Sample first 50 players
                            if hasattr(stat, '__dict__'):
                                stat_dict = stat.__dict__
                                for key in stat_dict.keys():
                                    if 'ppa' in key.lower() or 'predicted' in key.lower():
                                        ppa_found = True
                                        break
                                if ppa_found:
                                    break

                        results["ppa_data_available"] = ppa_found
                        if ppa_found:
                            self.logger.info("✅ PPA data appears to be available")
                        else:
                            results["warnings"].append("PPA data not found in player stats")

                except Exception as e:
                    results["warnings"].append(f"Could not check player stats for PPA: {str(e)}")

                # Additional PPA checks can be added here as new endpoints become available

        except Exception as e:
            results["warnings"].append(f"PPA validation encountered issues: {str(e)}")

        return results

    def _validate_success_rate_metrics(self) -> Dict[str, Any]:
        """Validate success rate calculations use 2025 context"""
        self.logger.info("📊 Validating success rate metrics")

        results = {
            "success_rate_data_available": False,
            "success_rate_analysis": {},
            "down_distance_context": {},
            "critical_issues": [],
            "warnings": []
        }

        try:
            api_key = os.environ.get("CFBD_API_KEY")
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            with cfbd.ApiClient(configuration) as api_client:
                # Get play-by-play data for success rate analysis
                try:
                    pbp_api = cfbd.PlaysApi(api_client)
                    recent_plays = pbp_api.get_plays(year=2025, week=self.CURRENT_WEEK - 1)

                    if recent_plays and len(recent_plays) >= self.MIN_PLAYS_FOR_ANALYSIS:
                        results["success_rate_data_available"] = True

                        # Analyze success rates
                        success_indicators = []
                        down_distances = []

                        for play in recent_plays[:500]:  # Sample 500 plays
                            # Look for success indicators
                            if hasattr(play, 'success') and play.success is not None:
                                success_indicators.append(play.success)

                            # Collect down-distance information
                            if hasattr(play, 'down') and hasattr(play, 'distance'):
                                if play.down is not None and play.distance is not None:
                                    down_distances.append((play.down, play.distance))

                        if success_indicators:
                            success_array = np.array(success_indicators)
                            overall_success_rate = np.mean(success_array)

                            results["success_rate_analysis"] = {
                                "total_plays_analyzed": len(success_indicators),
                                "overall_success_rate": float(overall_success_rate),
                                "success_rate_reasonable": (
                                    self.SUCCESS_RATE_REASONABLE_RANGE[0] <= overall_success_rate <= self.SUCCESS_RATE_REASONABLE_RANGE[1]
                                ),
                                "successful_plays": int(np.sum(success_array)),
                                "failed_plays": int(len(success_array) - np.sum(success_array))
                            }

                            if not results["success_rate_analysis"]["success_rate_reasonable"]:
                                results["warnings"].append(
                                    f"Success rate {overall_success_rate:.3f} outside expected range {self.SUCCESS_RATE_REASONABLE_RANGE}"
                                )

                        if down_distances:
                            # Analyze down-distance context
                            downs = [dd[0] for dd in down_distances if dd[0] is not None]
                            distances = [dd[1] for dd in down_distances if dd[1] is not None]

                            if downs and distances:
                                results["down_distance_context"] = {
                                    "downs_distribution": {down: downs.count(down) for down in set(downs)},
                                    "average_distance": float(np.mean(distances)),
                                    "reasonable_distance_range": (1 <= np.mean(distances) <= 15),
                                    "downs_present": list(set(downs))
                                }

                                # Validate we have reasonable down-distance data
                                if max(downs) > 4:
                                    results["warnings"].append("Found downs > 4 - possible data quality issues")

                        if not results["success_rate_data_available"]:
                            results["warnings"].append("Could not find success rate indicators in play data")

                    else:
                        results["warnings"].append("Insufficient play-by-play data for success rate analysis")

                except Exception as e:
                    results["warnings"].append(f"Could not analyze success rates: {str(e)}")

        except Exception as e:
            results["critical_issues"].append(f"Success rate validation failed: {str(e)}")

        return results

    def _validate_opponent_adjustments(self) -> Dict[str, Any]:
        """Validate opponent adjustments use 2025 season performance"""
        self.logger.info("⚖️ Validating opponent adjustment metrics")

        results = {
            "opponent_adjustments_detected": False,
            "adjustment_analysis": {},
            "team_strength_indicators": {},
            "critical_issues": [],
            "warnings": []
        }

        try:
            # Look for opponent-adjusted metrics in the existing data
            data_files_to_check = [
                self.project_root / "model_pack" / "updated_training_data.csv",
                self.project_root / "starter_pack" / "data" / "cfbd_2025_games.csv"
            ]

            for data_file in data_files_to_check:
                if data_file.exists():
                    try:
                        df = pd.read_csv(data_file)
                        self.logger.info(f"🔍 Checking {data_file.name} for opponent adjustments")

                        # Look for opponent-adjusted columns
                        opponent_adjusted_cols = [
                            col for col in df.columns
                            if 'adjusted' in col.lower() or 'opponent' in col.lower()
                        ]

                        if opponent_adjusted_cols:
                            results["opponent_adjustments_detected"] = True
                            results["adjustment_analysis"][f"{data_file.name}_adjusted_cols"] = opponent_adjusted_cols

                            # Analyze a few adjusted columns
                            for col in opponent_adjusted_cols[:3]:  # Check first 3
                                if col in df.columns:
                                    col_data = df[col].dropna()
                                    if len(col_data) > 0:
                                        results["adjustment_analysis"][f"{col}_stats"] = {
                                            "mean": float(col_data.mean()),
                                            "std": float(col_data.std()),
                                            "min": float(col_data.min()),
                                            "max": float(col_data.max()),
                                            "non_null_count": len(col_data)
                                        }

                            self.logger.info(f"✅ Found {len(opponent_adjusted_cols)} opponent-adjusted columns in {data_file.name}")

                    except Exception as e:
                        results["warnings"].append(f"Could not analyze {data_file}: {str(e)}")

            # Check for team strength indicators that would be used for opponent adjustments
            try:
                api_key = os.environ.get("CFBD_API_KEY")
                configuration = cfbd.Configuration()
                configuration.api_key['Authorization'] = api_key
                configuration.api_key_prefix['Authorization'] = 'Bearer'

                with cfbd.ApiClient(configuration) as api_client:
                    stats_api = cfbd.StatsApi(api_client)
                    team_stats = stats_api.get_team_season_stats(year=2025)

                    if team_stats:
                        # Look for strength-related metrics
                        strength_metrics = []
                        for stat in team_stats[:10]:  # Sample first 10 teams
                            if hasattr(stat, '__dict__'):
                                stat_dict = stat.__dict__
                                for key in stat_dict.keys():
                                    if any(keyword in key.lower() for keyword in ['strength', 'power', 'rating', 'sos']):
                                        strength_metrics.append(key)

                        if strength_metrics:
                            results["team_strength_indicators"]["available_metrics"] = list(set(strength_metrics))
                            self.logger.info("✅ Found team strength indicators for opponent adjustments")
                        else:
                            results["warnings"].append("No obvious team strength metrics found")

            except Exception as e:
                results["warnings"].append(f"Could not check team strength metrics: {str(e)}")

        except Exception as e:
            results["critical_issues"].append(f"Opponent adjustment validation failed: {str(e)}")

        return results

    def _analyze_play_by_play_data(self) -> Dict[str, Any]:
        """Analyze play-by-play data for 2025-specific patterns"""
        self.logger.info("🏈 Analyzing play-by-play data for 2025 patterns")

        results = {
            "pbp_data_available": False,
            "2025_patterns": {},
            "data_quality_checks": {},
            "critical_issues": [],
            "warnings": []
        }

        try:
            api_key = os.environ.get("CFBD_API_KEY")
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            with cfbd.ApiClient(configuration) as api_client:
                pbp_api = cfbd.PlaysApi(api_client)

                # Sample multiple weeks to look for 2025-specific patterns
                weeks_to_sample = [10, 11, self.CURRENT_WEEK - 1]  # Recent weeks
                all_plays = []

                for week in weeks_to_sample:
                    try:
                        week_plays = pbp_api.get_plays(year=2025, week=week)
                        if week_plays:
                            all_plays.extend(week_plays)
                        time.sleep(0.2)  # Rate limiting
                    except:
                        continue

                if len(all_plays) >= self.MIN_PLAYS_FOR_ANALYSIS:
                    results["pbp_data_available"] = True

                    # Analyze for 2025-specific patterns
                    play_types = []
                    quarters = []
                    clock_times = []

                    for play in all_plays[:1000]:  # Sample up to 1000 plays
                        if hasattr(play, 'play_type') and play.play_type:
                            play_types.append(play.play_type)

                        if hasattr(play, 'period') and play.period:
                            quarters.append(play.period)

                        if hasattr(play, 'clock') and play.clock:
                            clock_times.append(play.clock)

                    # Play type distribution (should reflect 2025 football trends)
                    if play_types:
                        play_type_counts = {ptype: play_types.count(ptype) for ptype in set(play_types)}
                        total_plays = len(play_types)

                        results["2025_patterns"]["play_type_distribution"] = {
                            pt: count/total_plays for pt, count in play_type_counts.items()
                        }

                        # Check for reasonable play distribution
                        pass_rush_ratio = play_types.count('Pass') / max(1, play_types.count('Rush'))
                        results["2025_patterns"]["pass_rush_ratio"] = pass_rush_ratio

                        if not (0.5 <= pass_rush_ratio <= 2.0):  # Reasonable range
                            results["warnings"].append(f"Unusual pass/rush ratio: {pass_rush_ratio:.2f}")

                    # Quarter distribution
                    if quarters:
                        quarter_dist = {q: quarters.count(q) for q in set(quarters)}
                        results["2025_patterns"]["quarter_distribution"] = quarter_dist

                        # Validate quarter data
                        if any(q > 4 for q in quarters if q is not None):
                            results["warnings"].append("Found quarters > 4 - possible overtime data")

                    # Data quality checks
                    results["data_quality_checks"] = {
                        "total_plays_analyzed": len(all_plays),
                        "plays_with_play_type": len(play_types),
                        "plays_with_quarter": len(quarters),
                        "data_completeness_rate": len(play_types) / len(all_plays) if all_plays else 0
                    }

                    if results["data_quality_checks"]["data_completeness_rate"] < 0.8:
                        results["warnings"].append("Low data completeness in play-by-play analysis")

                else:
                    results["warnings"].append("Insufficient play-by-play data for pattern analysis")

        except Exception as e:
            results["critical_issues"].append(f"Play-by-play analysis failed: {str(e)}")

        return results

    def _check_projection_contamination(self) -> Dict[str, Any]:
        """Check for pre-season projections mixed with actual data"""
        self.logger.info("🔍 Checking for pre-season projection contamination")

        results = {
            "projection_contamination_detected": False,
            "contamination_indicators": {},
            "critical_issues": [],
            "warnings": []
        }

        # Check if any data appears to be from pre-season projections
        # This would be indicated by:
        # 1. Games with unrealistic scores
        # 2. Stats that don't change from week to week
        # 3. Perfect statistical patterns

        try:
            api_key = os.environ.get("CFBD_API_KEY")
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            with cfbd.ApiClient(configuration) as api_client:
                games_api = cfbd.GamesApi(api_client)

                # Check games from multiple weeks for consistency patterns
                weeks_data = {}
                for week in range(1, min(5, self.CURRENT_WEEK)):  # Check first few weeks
                    try:
                        week_games = games_api.get_games(year=2025, week=week)
                        if week_games:
                            weeks_data[week] = week_games
                        time.sleep(0.2)
                    except:
                        continue

                # Look for suspicious patterns
                if weeks_data:
                    # Check for identical scores across weeks (suspicious)
                    score_patterns = {}
                    for week, games in weeks_data.items():
                        week_scores = []
                        for game in games:
                            if hasattr(game, 'home_points') and hasattr(game, 'away_points'):
                                if game.home_points is not None and game.away_points is not None:
                                    week_scores.append((game.home_points, game.away_points))
                        score_patterns[week] = week_scores

                    # Check for statistical patterns that suggest projections
                    all_scores = []
                    for scores in score_patterns.values():
                        all_scores.extend(scores)

                    if all_scores:
                        # Check for too many "perfect" scores (like 21-14, 28-21)
                        common_scores = [(21, 14), (28, 21), (24, 17), (31, 24), (14, 7)]
                        common_score_count = sum(all_scores.count(score) for score in common_scores)

                        results["contamination_indicators"]["common_score_percentage"] = (
                            common_score_count / len(all_scores) if all_scores else 0
                        )

                        if results["contamination_indicators"]["common_score_percentage"] > 0.3:
                            results["projection_contamination_detected"] = True
                            results["warnings"].append(
                                "High percentage of common scores detected - possible projection contamination"
                            )

        except Exception as e:
            results["warnings"].append(f"Projection contamination check failed: {str(e)}")

        return results

    def _calculate_metrics_score(self, validation_results: Dict) -> float:
        """Calculate overall advanced metrics authenticity score"""
        score_components = []

        # EPA validation score (30% weight)
        epa_results = validation_results.get("epa_validation", {})
        if epa_results.get("epa_data_available") and not epa_results.get("critical_issues"):
            epa_score = 0.8 if epa_results.get("warnings") else 1.0
            score_components.append(epa_score)
        else:
            score_components.append(0.0)

        # Success rate validation score (25% weight)
        success_results = validation_results.get("success_rate_validation", {})
        if success_results.get("success_rate_data_available") and not success_results.get("critical_issues"):
            success_score = 0.8 if success_results.get("warnings") else 1.0
            score_components.append(success_score)
        else:
            score_components.append(0.0)

        # Opponent adjustments score (25% weight)
        opponent_results = validation_results.get("opponent_adjustment_validation", {})
        if opponent_results.get("opponent_adjustments_detected") and not opponent_results.get("critical_issues"):
            opponent_score = 0.8 if opponent_results.get("warnings") else 1.0
            score_components.append(opponent_score)
        else:
            score_components.append(0.0)

        # Play-by-play analysis score (20% weight)
        pbp_results = validation_results.get("play_by_play_analysis", {})
        if pbp_results.get("pbp_data_available") and not pbp_results.get("critical_issues"):
            pbp_score = 0.8 if pbp_results.get("warnings") else 1.0
            score_components.append(pbp_score)
        else:
            score_components.append(0.0)

        # Calculate weighted average
        weights = [0.3, 0.25, 0.25, 0.2]
        weighted_score = sum(score * weight for score, weight in zip(score_components, weights))

        return weighted_score

    def _generate_recommendations(self, validation_results: Dict) -> List[str]:
        """Generate recommendations based on advanced metrics validation"""
        recommendations = []

        if validation_results["authenticity_score"] < 0.7:
            recommendations.append("🚨 CRITICAL: Advanced metrics authenticity below 70% - major concerns about 2025 data")

        # EPA-specific recommendations
        epa_results = validation_results.get("epa_validation", {})
        if not epa_results.get("epa_data_available"):
            recommendations.append("📈 EPA data not available - verify CFBD subscription level includes advanced metrics")
        elif epa_results.get("warnings"):
            recommendations.append("📈 EPA values outside expected ranges - verify calculation methodology")

        # Success rate recommendations
        success_results = validation_results.get("success_rate_validation", {})
        if not success_results.get("success_rate_data_available"):
            recommendations.append("📊 Success rate data missing - check play-by-play data availability")

        # Opponent adjustment recommendations
        opponent_results = validation_results.get("opponent_adjustment_validation", {})
        if not opponent_results.get("opponent_adjustments_detected"):
            recommendations.append("⚖️ No opponent adjustments found - models may not be using 2025 context")

        # Projection contamination
        if validation_results.get("projection_contamination_check", {}).get("projection_contamination_detected"):
            recommendations.append("🔍 Projection contamination detected - investigate data source purity")

        return recommendations

    def _save_validation_results(self, results: Dict) -> None:
        """Save detailed advanced metrics validation results"""
        results_dir = self.project_root / "project_management" / "DATA_VALIDATION"
        results_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = results_dir / f"advanced_metrics_validation_{timestamp}.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        self.logger.info(f"📄 Advanced metrics validation results saved: {results_file}")

def main():
    """Main execution function"""
    authenticator = AdvancedMetricsAuthenticator()
    results = authenticator.validate_advanced_metrics()

    print("\n" + "="*80)
    print("📊 ADVANCED METRICS VALIDATION COMPLETE")
    print("="*80)
    print(f"📈 Metrics Authenticity Score: {results['authenticity_score']:.1%}")
    print(f"🚨 Critical Issues: {len(results['critical_issues'])}")
    print(f"⚠️ Warnings: {len(results['warnings'])}")

    # EPA Results
    epa_results = results.get("epa_validation", {})
    print(f"\n📈 EPA Validation:")
    print(f"   Data Available: {'✅' if epa_results.get('epa_data_available') else '❌'}")
    if epa_results.get("epa_analysis"):
        print(f"   Plays Analyzed: {epa_results['epa_analysis'].get('total_plays_analyzed', 0)}")
        print(f"   EPA Mean: {epa_results['epa_analysis'].get('epa_mean', 0):.3f}")

    # Success Rate Results
    success_results = results.get("success_rate_validation", {})
    print(f"\n📊 Success Rate Validation:")
    print(f"   Data Available: {'✅' if success_results.get('success_rate_data_available') else '❌'}")
    if success_results.get("success_rate_analysis"):
        print(f"   Overall Success Rate: {success_results['success_rate_analysis'].get('overall_success_rate', 0):.3f}")

    # Opponent Adjustments
    opponent_results = results.get("opponent_adjustment_validation", {})
    print(f"\n⚖️ Opponent Adjustments:")
    print(f"   Detected: {'✅' if opponent_results.get('opponent_adjustments_detected') else '❌'}")

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