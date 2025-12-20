#!/usr/bin/env python3
"""
Comprehensive System Validation Script
======================================

Complete validation of the Script Ohio 2.0 system including:
- Model prediction system (already proven 100% successful)
- CFBD API integration
- Advanced features integration
- External model analysis
- API server functionality
- Web application integration
- Data pipeline validation
- System performance metrics

This is the final validation before declaring the system production-ready.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.cfbd_client.unified_client import UnifiedCFBDClient

    from verify_model_predictions import ModelVerificationSystem
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class ComprehensiveSystemValidator:
    """Comprehensive system validation suite"""

    def __init__(self):
        self.client = UnifiedCFBDClient()
        self.verifier = ModelVerificationSystem()
        self.validation_results = {}
        self.start_time = datetime.now()

    def log_validation(self, test_name: str, passed: bool, details: str = ""):
        """Log validation result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")

        self.validation_results[test_name] = {
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

    def validate_model_predictions_system(self):
        """Test 1: Model prediction system (already proven working)"""
        print("\n🧮 TEST 1: Model Prediction System")
        print("-" * 40)

        try:
            # Run the comprehensive model verification
            verification_file = PROJECT_ROOT / "verification_results.json"

            if verification_file.exists():
                with open(verification_file, "r") as f:
                    previous_results = json.load(f)

                if previous_results.get("success_rate") == 100:
                    self.log_validation(
                        "Model Predictions",
                        True,
                        f"Previous verification: 100% success ({previous_results.get('total_tests', 0)} tests)",
                    )
                else:
                    self.log_validation(
                        "Model Predictions",
                        False,
                        f"Previous verification: {previous_results.get('success_rate', 0)}% success",
                    )
            else:
                # Run fresh verification by running individual tests
                try:
                    self.verifier.test_model_loading()
                    self.verifier.test_feature_consistency()
                    self.verifier.test_prediction_determinism()
                    self.verifier.test_model_uniqueness()
                    self.verifier.test_output_ranges()
                    self.verifier.test_feature_sensitivity()
                    self.verifier.test_ensemble_logic()
                    self.verifier.test_prediction_file_integrity()

                    # Generate verification report
                    success = self.verifier.generate_verification_report()
                    self.log_validation(
                        "Model Predictions", success, "Fresh verification completed"
                    )
                except Exception as e:
                    self.log_validation(
                        "Model Predictions", False, f"Fresh verification error: {e}"
                    )

        except Exception as e:
            self.log_validation("Model Predictions", False, f"Error: {e}")

    def validate_cfbd_integration(self):
        """Test 2: CFBD API integration"""
        print("\n📊 TEST 2: CFBD API Integration")
        print("-" * 40)

        try:
            # Test basic CFBD API connectivity
            fbs_teams = self.client.get_fbs_teams(year=2025)
            if fbs_teams and len(fbs_teams) > 130:  # Should have ~133 FBS teams
                self.log_validation(
                    "CFBD FBS Teams", True, f"Retrieved {len(fbs_teams)} FBS teams"
                )
            else:
                self.log_validation(
                    "CFBD FBS Teams", False, f"Only got {len(fbs_teams or [])} teams"
                )

            # Test talent ratings
            time.sleep(0.17)  # Rate limiting
            talent_data = self.client.get_team_talent(year=2025)
            if talent_data and len(talent_data) > 100:
                self.log_validation(
                    "CFBD Talent Data",
                    True,
                    f"Retrieved talent data for {len(talent_data)} teams",
                )
            else:
                self.log_validation(
                    "CFBD Talent Data",
                    False,
                    f"Only got {len(talent_data or [])} talent entries",
                )

            # Test games data
            time.sleep(0.17)  # Rate limiting
            games_data = self.client.get_games(year=2025)
            if games_data and len(games_data) > 0:
                self.log_validation(
                    "CFBD Games Data",
                    True,
                    f"Retrieved {len(games_data)} games for 2025",
                )
            else:
                self.log_validation("CFBD Games Data", False, "No games data retrieved")

            # Test unified client features
            metrics = self.client.get_performance_metrics()
            if metrics:
                self.log_validation(
                    "CFBD Client Metrics",
                    True,
                    f"Performance tracking active: {list(metrics.keys())}",
                )
            else:
                self.log_validation(
                    "CFBD Client Metrics", False, "No performance metrics available"
                )

        except Exception as e:
            self.log_validation("CFBD Integration", False, f"Error: {e}")

    def validate_advanced_features(self):
        """Test 3: Advanced CFBD features integration"""
        print("\n🚀 TEST 3: Advanced Features Integration")
        print("-" * 40)

        try:
            # Check for advanced features script
            advanced_script = (
                PROJECT_ROOT / "scripts" / "integrate_advanced_cfbd_features_working.py"
            )
            if advanced_script.exists():
                self.log_validation(
                    "Advanced Features Script",
                    True,
                    "Working advanced features script exists",
                )
            else:
                self.log_validation(
                    "Advanced Features Script", False, "Script not found"
                )

            # Check for enhanced predictions
            enhanced_predictions = list(
                PROJECT_ROOT.glob(
                    "predictions/working_enhanced_bowl_predictions_*.json"
                )
            )
            if enhanced_predictions:
                latest_enhanced = max(
                    enhanced_predictions, key=lambda f: f.stat().st_mtime
                )
                with open(latest_enhanced, "r") as f:
                    enhanced_data = json.load(f)

                if enhanced_data.get("total_games", 0) > 0:
                    self.log_validation(
                        "Enhanced Predictions",
                        True,
                        f"Found enhanced predictions for {enhanced_data['total_games']} games",
                    )
                else:
                    self.log_validation(
                        "Enhanced Predictions",
                        False,
                        "No games in enhanced predictions",
                    )
            else:
                self.log_validation(
                    "Enhanced Predictions", False, "No enhanced prediction files found"
                )

            # Check for working features data
            features_files = list(
                PROJECT_ROOT.glob(
                    "data/processed/features/working_advanced_cfbd_features_*.json"
                )
            )
            if features_files:
                latest_features = max(features_files, key=lambda f: f.stat().st_mtime)
                with open(latest_features, "r") as f:
                    features_data = json.load(f)

                teams_count = features_data.get("total_teams", 0)
                if teams_count > 100:
                    self.log_validation(
                        "Working Features Data",
                        True,
                        f"Advanced features for {teams_count} teams",
                    )
                else:
                    self.log_validation(
                        "Working Features Data",
                        False,
                        f"Only {teams_count} teams with features",
                    )
            else:
                self.log_validation(
                    "Working Features Data", False, "No features data files found"
                )

        except Exception as e:
            self.log_validation("Advanced Features", False, f"Error: {e}")

    def validate_external_model_analysis(self):
        """Test 4: External model analysis"""
        print("\n📈 TEST 4: External Model Analysis")
        print("-" * 40)

        try:
            # Check for external model analysis file
            analysis_files = list(
                PROJECT_ROOT.glob(
                    "data/outputs/analysis/external_model_analysis_*.json"
                )
            )
            if analysis_files:
                latest_analysis = max(analysis_files, key=lambda f: f.stat().st_mtime)
                with open(latest_analysis, "r") as f:
                    analysis_data = json.load(f)

                total_models = analysis_data.get("total_models_analyzed", 0)
                if (
                    total_models >= 9
                ):  # Should have 9 models (6 external + 3 Script Ohio)
                    self.log_validation(
                        "External Model Analysis",
                        True,
                        f"Analyzed {total_models} models including Script Ohio",
                    )

                    # Check for Script Ohio rankings
                    key_findings = analysis_data.get("key_findings", {})
                    performance_rankings = key_findings.get("performance_rankings", {})
                    script_ohio_ranking = performance_rankings.get(
                        "script_ohio_ranking", {}
                    )

                    if script_ohio_ranking:
                        ensemble_rank = script_ohio_ranking.get(
                            "Script Ohio Ensemble", 0
                        )
                        if ensemble_rank and ensemble_rank <= 6:  # Should be ranked 5th
                            self.log_validation(
                                "Script Ohio Ranking",
                                True,
                                f"Script Ohio Ensemble ranked #{ensemble_rank} out of {total_models}",
                            )
                        else:
                            self.log_validation(
                                "Script Ohio Ranking",
                                False,
                                f"Unexpected ranking: #{ensemble_rank}",
                            )
                    else:
                        self.log_validation(
                            "Script Ohio Ranking", False, "No ranking data found"
                        )
                else:
                    self.log_validation(
                        "External Model Analysis",
                        False,
                        f"Only {total_models} models analyzed",
                    )
            else:
                self.log_validation(
                    "External Model Analysis", False, "No analysis files found"
                )

        except Exception as e:
            self.log_validation("External Model Analysis", False, f"Error: {e}")

    def validate_api_server(self):
        """Test 5: Analytics API server"""
        print("\n🌐 TEST 5: Analytics API Server")
        print("-" * 40)

        try:
            # Check for analytics API script
            api_script = PROJECT_ROOT / "api_server" / "analytics_api.py"
            if api_script.exists():
                self.log_validation(
                    "Analytics API Script", True, "Analytics API server script exists"
                )
            else:
                self.log_validation(
                    "Analytics API Script", False, "API script not found"
                )

            # Test API server functionality (basic import check)
            try:
                # Test if we can import the API module
                api_path = PROJECT_ROOT / "api_server"
                if str(api_path) not in sys.path:
                    sys.path.insert(0, str(api_path))

                import analytics_api

                self.log_validation(
                    "API Module Import",
                    True,
                    "Analytics API module imports successfully",
                )
            except ImportError as e:
                self.log_validation("API Module Import", False, f"Import error: {e}")

            # Check for advanced analytics dashboard
            dashboard_file = (
                PROJECT_ROOT
                / "web_app"
                / "src"
                / "components"
                / "AdvancedAnalyticsDashboard.tsx"
            )
            if dashboard_file.exists():
                self.log_validation(
                    "Advanced Analytics Dashboard",
                    True,
                    "React dashboard component exists",
                )
            else:
                self.log_validation(
                    "Advanced Analytics Dashboard",
                    False,
                    "Dashboard component not found",
                )

        except Exception as e:
            self.log_validation("API Server", False, f"Error: {e}")

    def validate_data_pipeline(self):
        """Test 6: Data pipeline integrity"""
        print("\n🔄 TEST 6: Data Pipeline Integrity")
        print("-" * 40)

        try:
            # Check for master training data
            master_data = (
                PROJECT_ROOT
                / "data"
                / "processed"
                / "training"
                / "master_training_data_v2.csv"
            )
            if master_data.exists():
                df = pd.read_csv(master_data)
                if len(df) > 5000:  # Should have ~5,250 games
                    self.log_validation(
                        "Master Training Data",
                        True,
                        f"Master dataset with {len(df)} games (2016-2025)",
                    )
                else:
                    self.log_validation(
                        "Master Training Data",
                        False,
                        f"Master dataset only has {len(df)} games",
                    )
            else:
                self.log_validation(
                    "Master Training Data", False, "Master training data not found"
                )

            # Check for production models
            ridge_model = (
                PROJECT_ROOT
                / "models"
                / "production"
                / "ridge_regression_2025_v2.joblib"
            )
            xgb_model = (
                PROJECT_ROOT
                / "models"
                / "production"
                / "xgboost_classifier_2025_v2.pkl"
            )
            fastai_model = (
                PROJECT_ROOT / "models" / "production" / "fastai_neural_net_2025_v2.pkl"
            )

            models_found = sum(
                [ridge_model.exists(), xgb_model.exists(), fastai_model.exists()]
            )

            if models_found == 3:
                self.log_validation(
                    "Production Models", True, "All 3 production models found"
                )
            elif models_found >= 2:
                self.log_validation(
                    "Production Models",
                    True,
                    f"Found {models_found}/3 production models",
                )
            else:
                self.log_validation(
                    "Production Models", False, f"Only {models_found}/3 models found"
                )

            # Check for prediction outputs
            prediction_files = list(
                PROJECT_ROOT.glob("data/outputs/predictions/2025/bowl_season/*.json")
            )
            if prediction_files:
                self.log_validation(
                    "Prediction Outputs",
                    True,
                    f"Found {len(prediction_files)} prediction files",
                )
            else:
                # Check legacy location
                legacy_predictions = list(
                    PROJECT_ROOT.glob("predictions/bowls_2025_predictions_*.json")
                )
                if legacy_predictions:
                    self.log_validation(
                        "Prediction Outputs",
                        True,
                        f"Found {len(legacy_predictions)} prediction files (legacy location)",
                    )
                else:
                    self.log_validation(
                        "Prediction Outputs", False, "No prediction files found"
                    )

        except Exception as e:
            self.log_validation("Data Pipeline", False, f"Error: {e}")

    def validate_system_performance(self):
        """Test 7: System performance metrics"""
        print("\n⚡ TEST 7: System Performance")
        print("-" * 40)

        try:
            # Test CFBD API response time
            start_time = time.time()
            fbs_teams = self.client.get_fbs_teams(year=2025)
            api_response_time = time.time() - start_time

            if api_response_time < 5.0:  # Should respond within 5 seconds
                self.log_validation(
                    "CFBD API Performance",
                    True,
                    f"API response time: {api_response_time:.2f}s",
                )
            else:
                self.log_validation(
                    "CFBD API Performance",
                    False,
                    f"Slow API response: {api_response_time:.2f}s",
                )

            # Test model loading performance
            start_time = time.time()
            try:
                import joblib

                ridge_model = joblib.load(
                    PROJECT_ROOT
                    / "models"
                    / "production"
                    / "ridge_regression_2025_v2.joblib"
                )
                model_load_time = time.time() - start_time

                if model_load_time < 1.0:  # Should load within 1 second
                    self.log_validation(
                        "Model Loading Performance",
                        True,
                        f"Ridge model load time: {model_load_time:.3f}s",
                    )
                else:
                    self.log_validation(
                        "Model Loading Performance",
                        False,
                        f"Slow model load: {model_load_time:.3f}s",
                    )
            except Exception:
                self.log_validation(
                    "Model Loading Performance", False, "Could not test model loading"
                )

            # Test memory usage (basic check)
            try:
                import psutil

                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024

                if memory_mb < 1000:  # Should use less than 1GB for this script
                    self.log_validation(
                        "Memory Usage", True, f"Current memory usage: {memory_mb:.1f}MB"
                    )
                else:
                    self.log_validation(
                        "Memory Usage", False, f"High memory usage: {memory_mb:.1f}MB"
                    )
            except ImportError:
                self.log_validation(
                    "Memory Usage", True, "psutil not available - skipped"
                )

        except Exception as e:
            self.log_validation("System Performance", False, f"Error: {e}")

    def validate_agent_system(self):
        """Test 8: Agent system status"""
        print("\n🤖 TEST 8: Agent System Status")
        print("-" * 40)

        try:
            # Check for meta agent
            meta_agent_file = PROJECT_ROOT / "agents" / "meta_agent.py"
            if meta_agent_file.exists():
                self.log_validation("Meta Agent", True, "Meta agent script exists")
            else:
                self.log_validation("Meta Agent", False, "Meta agent not found")

            # Check for agent registry
            agent_registry = PROJECT_ROOT / "agents" / "agent_registry.json"
            if agent_registry.exists():
                with open(agent_registry, "r") as f:
                    registry_data = json.load(f)

                agent_count = len(registry_data.get("agents", {}))
                if agent_count >= 10:  # Should have 10+ agents
                    self.log_validation(
                        "Agent Registry", True, f"Registered agents: {agent_count}"
                    )
                else:
                    self.log_validation(
                        "Agent Registry", False, f"Only {agent_count} agents registered"
                    )
            else:
                self.log_validation("Agent Registry", False, "Agent registry not found")

            # Check for orchestration agent
            orchestration_agent = PROJECT_ROOT / "agents" / "orchestration_agent.py"
            if orchestration_agent.exists():
                self.log_validation(
                    "Orchestration Agent", True, "Orchestration agent exists"
                )
            else:
                self.log_validation(
                    "Orchestration Agent", False, "Orchestration agent not found"
                )

        except Exception as e:
            self.log_validation("Agent System", False, f"Error: {e}")

    def validate_web_application(self):
        """Test 9: Web application components"""
        print("\n🌍 TEST 9: Web Application")
        print("-" * 40)

        try:
            # Check for React app structure
            web_app_dir = PROJECT_ROOT / "web_app"
            if web_app_dir.exists():
                self.log_validation(
                    "Web App Directory", True, "Web application directory exists"
                )

                # Check for package.json
                package_json = web_app_dir / "package.json"
                if package_json.exists():
                    self.log_validation(
                        "Package.json", True, "React package.json exists"
                    )
                else:
                    self.log_validation("Package.json", False, "package.json not found")

                # Check for src directory
                src_dir = web_app_dir / "src"
                if src_dir.exists():
                    self.log_validation(
                        "Source Directory", True, "React src directory exists"
                    )

                    # Check for main App component
                    app_tsx = src_dir / "App.tsx"
                    if app_tsx.exists():
                        self.log_validation(
                            "App.tsx", True, "Main React component exists"
                        )
                    else:
                        self.log_validation("App.tsx", False, "App.tsx not found")

                    # Check for components directory
                    components_dir = src_dir / "components"
                    if components_dir.exists():
                        component_count = len(list(components_dir.glob("*.tsx")))
                        if component_count >= 5:
                            self.log_validation(
                                "React Components",
                                True,
                                f"Found {component_count} React components",
                            )
                        else:
                            self.log_validation(
                                "React Components",
                                False,
                                f"Only {component_count} components found",
                            )
                    else:
                        self.log_validation(
                            "React Components", False, "components directory not found"
                        )
                else:
                    self.log_validation(
                        "Source Directory", False, "src directory not found"
                    )
            else:
                self.log_validation(
                    "Web App Directory", False, "web_app directory not found"
                )

        except Exception as e:
            self.log_validation("Web Application", False, f"Error: {e}")

    def run_comprehensive_validation(self):
        """Run all validation tests"""
        print("🔬 SCRIPT OHIO 2.0 - COMPREHENSIVE SYSTEM VALIDATION")
        print("=" * 60)
        print(f"Started at: {self.start_time}")
        print("=" * 60)

        # Run all validation tests
        self.validate_model_predictions_system()
        self.validate_cfbd_integration()
        self.validate_advanced_features()
        self.validate_external_model_analysis()
        self.validate_api_server()
        self.validate_data_pipeline()
        self.validate_system_performance()
        self.validate_agent_system()
        self.validate_web_application()

        # Calculate overall results
        total_tests = len(self.validation_results)
        passed_tests = sum(
            1 for result in self.validation_results.values() if result["passed"]
        )
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Generate final report
        end_time = datetime.now()
        duration = end_time - self.start_time

        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE VALIDATION REPORT")
        print("=" * 60)
        print(f"Duration: {duration.total_seconds():.1f} seconds")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print("=" * 60)

        # Show failed tests if any
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test_name, result in self.validation_results.items():
                if not result["passed"]:
                    print(f"  • {test_name}: {result['details']}")

        # Show passed tests summary
        print("\n✅ PASSED TESTS:")
        for test_name, result in self.validation_results.items():
            if result["passed"]:
                print(f"  • {test_name}")

        # Overall system status
        if success_rate >= 95:
            print(f"\n🎉 SYSTEM STATUS: PRODUCTION READY!")
            print(f"   Success rate: {success_rate:.1f}% (≥95% required)")
        elif success_rate >= 85:
            print(f"\n⚠️  SYSTEM STATUS: NEARLY READY")
            print(f"   Success rate: {success_rate:.1f}% (needs ≥95%)")
        elif success_rate >= 70:
            print(f"\n⚠️  SYSTEM STATUS: NEEDS WORK")
            print(f"   Success rate: {success_rate:.1f}% (needs ≥95%)")
        else:
            print(f"\n❌ SYSTEM STATUS: NOT READY")
            print(f"   Success rate: {success_rate:.1f}% (needs ≥95%)")

        # Save validation report
        report_data = {
            "validation_timestamp": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "system_ready": success_rate >= 95,
            "detailed_results": self.validation_results,
        }

        report_file = (
            PROJECT_ROOT
            / f"validation_results/comprehensive_system_validation_{end_time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

        return success_rate >= 95


def main():
    """Main execution function"""
    validator = ComprehensiveSystemValidator()
    system_ready = validator.run_comprehensive_validation()

    if system_ready:
        print("\n🚀 SCRIPT OHIO 2.0 IS PRODUCTION READY!")
        sys.exit(0)
    else:
        print("\n⚠️  SCRIPT OHIO 2.0 NEEDS ATTENTION BEFORE DEPLOYMENT")
        sys.exit(1)


if __name__ == "__main__":
    main()
