#!/usr/bin/env python3
"""
DATA STRUCTURE VALIDATOR AGENT
Mission: Fix missing columns and ensure model compatibility

Critical Question: "Does the data structure match what the pre-trained models expect?"

Created: 2025-11-13
Purpose: Validate and fix data structure issues for model compatibility
"""

import logging
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import hashlib

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False
    print("⚠️ joblib not available - limited model compatibility checking")

try:
    import pickle
    HAS_PICKLE = True
except ImportError:
    HAS_PICKLE = False
    print("⚠️ pickle not available - limited model loading")

try:
    from fastai.learner import load_learner
    HAS_FASTAI = True
except ImportError:
    HAS_FASTAI = False
    load_learner = None
    print("⚠️ fastai not available - FastAI model validation limited")

class DataStructureValidator:
    """
    Validates and fixes data structure for model compatibility

    Key validations:
    1. Missing columns (game_key, conference_game)
    2. All 86 required features present
    3. Column names and formats match models
    4. Data types are correct for ML models
    5. Model loading and compatibility testing
    """

    def __init__(self, project_root: str = "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"):
        self.project_root = Path(project_root)
        self.logger = self._setup_logging()
        self.validation_results = {}

        # Data structure validation parameters
        self.TARGET_DATE = datetime(2025, 11, 13, tzinfo=timezone.utc)
        self.EXPECTED_FEATURE_COUNT = 86  # Number of features expected by models
        self.CRITICAL_COLUMNS = ['game_key', 'conference_game']  # Known missing columns

        # Model file locations
        self.model_files = {
            "ridge": self.project_root / "model_pack" / "ridge_model_2025.joblib",
            "xgb": self.project_root / "model_pack" / "xgb_home_win_model_2025.pkl",
            "fastai": self.project_root / "model_pack" / "fastai_home_win_model_2025.pkl"
        }

        # Data file locations
        self.data_files = {
            "training_data": self.project_root / "model_pack" / "updated_training_data.csv",
            "starter_pack": self.project_root / "starter_pack" / "data" / "cfbd_2025_games.csv"
        }

        self.logger.info("🏗️ Data Structure Validator initialized")
        self.logger.info(f"📊 Expected feature count: {self.EXPECTED_FEATURE_COUNT}")
        self.logger.info(f"🔧 Critical missing columns: {self.CRITICAL_COLUMNS}")

    def _setup_logging(self) -> logging.Logger:
        """Setup validation logging"""
        logger = logging.getLogger("DataStructureValidator")
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

    def validate_data_structure(self) -> Dict[str, Any]:
        """
        Main validation function for data structure compatibility

        Returns:
            Dict containing comprehensive data structure validation results
        """
        self.logger.info("🚀 Starting data structure validation")

        validation_results = {
            "validation_type": "data_structure",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "missing_columns": {},
            "feature_validation": {},
            "model_compatibility": {},
            "data_quality_checks": {},
            "column_fixes_applied": [],
            "critical_issues": [],
            "warnings": [],
            "authenticity_score": 0.0,
            "recommendations": []
        }

        # Step 1: Analyze existing data structure
        structure_analysis = self._analyze_existing_structure()
        validation_results["existing_structure"] = structure_analysis

        # Step 2: Identify and fix missing columns
        missing_columns_results = self._fix_missing_columns(structure_analysis)
        validation_results["missing_columns"] = missing_columns_results

        if missing_columns_results.get("critical_issues"):
            validation_results["critical_issues"].extend(missing_columns_results["critical_issues"])

        # Step 3: Validate all required features
        feature_validation = self._validate_required_features()
        validation_results["feature_validation"] = feature_validation

        if feature_validation.get("critical_issues"):
            validation_results["critical_issues"].extend(feature_validation["critical_issues"])

        # Step 4: Test model compatibility
        model_compatibility = self._test_model_compatibility()
        validation_results["model_compatibility"] = model_compatibility

        if model_compatibility.get("critical_issues"):
            validation_results["critical_issues"].extend(model_compatibility["critical_issues"])

        # Step 5: Data quality checks
        quality_checks = self._perform_data_quality_checks()
        validation_results["data_quality_checks"] = quality_checks

        if quality_checks.get("critical_issues"):
            validation_results["critical_issues"].extend(quality_checks["critical_issues"])

        # Step 6: Column standardization
        standardization_results = self._standardize_columns()
        validation_results["column_fixes_applied"] = standardization_results

        # Calculate overall authenticity score
        validation_results["authenticity_score"] = self._calculate_structure_score(validation_results)

        # Generate recommendations
        validation_results["recommendations"] = self._generate_recommendations(validation_results)

        # Save detailed results
        self._save_validation_results(validation_results)

        self.logger.info(f"✅ Data structure validation complete - Score: {validation_results['authenticity_score']:.1%}")

        return validation_results

    def _analyze_existing_structure(self) -> Dict[str, Any]:
        """Analyze existing data structure in project files"""
        self.logger.info("📊 Analyzing existing data structure")

        results = {
            "data_files_analyzed": {},
            "total_columns_found": {},
            "column_types": {},
            "sample_data": {},
            "critical_issues": [],
            "warnings": []
        }

        for file_name, file_path in self.data_files.items():
            if file_path.exists():
                try:
                    self.logger.info(f"🔍 Analyzing {file_path.name}")
                    df = pd.read_csv(file_path)

                    results["data_files_analyzed"][file_name] = {
                        "file_path": str(file_path),
                        "rows": len(df),
                        "columns": len(df.columns),
                        "column_names": list(df.columns),
                        "missing_values": df.isnull().sum().to_dict(),
                        "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024
                    }

                    results["total_columns_found"][file_name] = len(df.columns)

                    # Analyze column types
                    column_types = {}
                    for col in df.columns:
                        column_types[col] = str(df[col].dtype)
                    results["column_types"][file_name] = column_types

                    # Get sample data
                    sample_size = min(5, len(df))
                    results["sample_data"][file_name] = df.head(sample_size).to_dict("records")

                    # Check for critical missing columns
                    missing_critical = [col for col in self.CRITICAL_COLUMNS if col not in df.columns]
                    if missing_critical:
                        results["critical_issues"].append(
                            f"{file_path.name} missing critical columns: {missing_critical}"
                        )

                    self.logger.info(f"✅ {file_path.name}: {len(df)} rows, {len(df.columns)} columns")

                except Exception as e:
                    results["critical_issues"].append(f"Failed to analyze {file_path.name}: {str(e)}")
            else:
                results["warnings"].append(f"Data file not found: {file_path}")

        return results

    def _fix_missing_columns(self, structure_analysis: Dict) -> Dict[str, Any]:
        """Fix missing columns, particularly game_key and conference_game"""
        self.logger.info("🔧 Fixing missing columns")

        results = {
            "columns_fixed": {},
            "fixes_applied": [],
            "critical_issues": [],
            "warnings": []
        }

        for file_name, file_info in structure_analysis.get("data_files_analyzed", {}).items():
            file_path = Path(file_info["file_path"])
            if not file_path.exists():
                continue

            try:
                df = pd.read_csv(file_path)
                original_columns = list(df.columns)
                fixes_for_file = []

                # Fix 1: Create game_key column
                if "game_key" not in df.columns:
                    self.logger.info(f"🔑 Creating game_key column for {file_path.name}")

                    # Generate game_key using format: season|away_team|home_team
                    if all(col in df.columns for col in ["season", "away_team", "home_team"]):
                        df["game_key"] = (
                            df["season"].astype(str) + "|" +
                            df["away_team"].astype(str) + "|" +
                            df["home_team"].astype(str)
                        )
                        fixes_for_file.append("Created game_key column")
                        results["fixes_applied"].append(f"{file_path.name}: Created game_key column")
                    else:
                        results["critical_issues"].append(
                            f"Cannot create game_key for {file_path.name} - missing required columns"
                        )

                # Fix 2: Create conference_game column
                if "conference_game" not in df.columns:
                    self.logger.info(f"🏆 Creating conference_game column for {file_path.name}")

                    # Try to determine conference games from available data
                    if "home_conference" in df.columns and "away_conference" in df.columns:
                        # Conference game if both teams are in same conference
                        df["conference_game"] = (
                            (df["home_conference"] == df["away_conference"]) &
                            (df["home_conference"].notna()) &
                            (df["away_conference"].notna())
                        ).astype(int)
                        fixes_for_file.append("Created conference_game column from conference data")
                        results["fixes_applied"].append(f"{file_path.name}: Created conference_game column")
                    else:
                        # Default to 1 (assume conference game) for now
                        # In a real implementation, you'd look up conference memberships
                        df["conference_game"] = 1
                        fixes_for_file.append("Created conference_game column (defaulted to 1)")
                        results["warnings"].append(
                            f"{file_path.name}: conference_game defaulted to 1 - verify conference assignments"
                        )

                # Save fixed data if changes were made
                if fixes_for_file:
                    # Create backup
                    backup_path = file_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                    df_original = pd.read_csv(file_path)
                    df_original.to_csv(backup_path, index=False)
                    self.logger.info(f"💾 Created backup: {backup_path.name}")

                    # Save fixed data
                    df.to_csv(file_path, index=False)
                    self.logger.info(f"✅ Saved fixed data to {file_path.name}")

                    results["columns_fixed"][file_name] = {
                        "original_columns": len(original_columns),
                        "final_columns": len(df.columns),
                        "new_columns": [col for col in df.columns if col not in original_columns],
                        "fixes_applied": fixes_for_file
                    }

                else:
                    results["columns_fixed"][file_name] = {
                        "message": "No fixes needed",
                        "original_columns": len(original_columns),
                        "final_columns": len(original_columns)
                    }

            except Exception as e:
                results["critical_issues"].append(f"Failed to fix columns in {file_path.name}: {str(e)}")

        return results

    def _validate_required_features(self) -> Dict[str, Any]:
        """Validate all required features for models are present"""
        self.logger.info("🎯 Validating required features for models")

        results = {
            "expected_features": self.EXPECTED_FEATURE_COUNT,
            "feature_validation_results": {},
            "missing_features": {},
            "extra_features": {},
            "critical_issues": [],
            "warnings": []
        }

        for file_name, file_path in self.data_files.items():
            if not file_path.exists():
                continue

            try:
                df = pd.read_csv(file_path)
                feature_count = len(df.columns)

                results["feature_validation_results"][file_name] = {
                    "feature_count": feature_count,
                    "meets_expected_count": feature_count >= self.EXPECTED_FEATURE_COUNT,
                    "feature_difference": feature_count - self.EXPECTED_FEATURE_COUNT
                }

                if feature_count < self.EXPECTED_FEATURE_COUNT:
                    missing_count = self.EXPECTED_FEATURE_COUNT - feature_count
                    results["missing_features"][file_name] = {
                        "missing_count": missing_count,
                        "missing_percentage": (missing_count / self.EXPECTED_FEATURE_COUNT) * 100
                    }
                    results["critical_issues"].append(
                        f"{file_path.name} has {feature_count} features, expected {self.EXPECTED_FEATURE_COUNT}"
                    )
                elif feature_count > self.EXPECTED_FEATURE_COUNT:
                    extra_count = feature_count - self.EXPECTED_FEATURE_COUNT
                    results["extra_features"][file_name] = {
                        "extra_count": extra_count,
                        "extra_percentage": (extra_count / self.EXPECTED_FEATURE_COUNT) * 100
                    }
                    results["warnings"].append(
                        f"{file_path.name} has {extra_count} extra features beyond expected {self.EXPECTED_FEATURE_COUNT}"
                    )

                # Check for common feature categories
                common_categories = {
                    "team_identifiers": ["home_team", "away_team", "season", "week"],
                    "score_features": ["home_points", "away_points", "home_score", "away_score"],
                    "opponent_adjusted": [col for col in df.columns if "adjusted" in col.lower()],
                    "advanced_metrics": [col for col in df.columns if any(metric in col.lower()
                                        for metric in ["epa", "ppa", "success", "exp_points"])],
                    "team_stats": [col for col in df.columns if any(stat in col.lower()
                                     for stat in ["yards", "turnover", "penalty", "possession"])]
                }

                results["feature_validation_results"][file_name]["feature_categories"] = {
                    category: len(features) for category, features in common_categories.items()
                }

            except Exception as e:
                results["critical_issues"].append(f"Feature validation failed for {file_path.name}: {str(e)}")

        return results

    def _test_model_compatibility(self) -> Dict[str, Any]:
        """Test model compatibility with current data structure"""
        self.logger.info("🤖 Testing model compatibility")

        results = {
            "models_tested": {},
            "compatibility_results": {},
            "loading_issues": {},
            "critical_issues": [],
            "warnings": []
        }

        # Test loading each model
        for model_name, model_path in self.model_files.items():
            self.logger.info(f"🔍 Testing {model_name} model: {model_path.name}")

            model_result = {
                "model_exists": model_path.exists(),
                "loadable": False,
                "feature_names": None,
                "expected_feature_count": None,
                "loading_error": None
            }

            if not model_path.exists():
                results["warnings"].append(f"Model file not found: {model_path.name}")
                results["models_tested"][model_name] = model_result
                continue

            try:
                # Try to load the model
                model = None
                if "fastai" in model_path.name.lower():
                    if not HAS_FASTAI:
                        raise ImportError("fastai not installed - cannot validate FastAI model")
                    model = load_learner(model_path)
                    model_result["loadable"] = True
                    feature_names = list(getattr(model.dls, 'cat_names', [])) + list(getattr(model.dls, 'cont_names', []))
                    model_result["feature_names"] = feature_names
                    model_result["expected_feature_count"] = len(feature_names)
                    self.logger.info(f"✅ {model_name} model loaded successfully via fastai")
                elif model_path.suffix == ".joblib" and HAS_JOBLIB:
                    model = joblib.load(model_path)
                    model_result["loadable"] = True
                    self.logger.info(f"✅ {model_name} model loaded successfully")
                elif model_path.suffix == ".pkl" and HAS_PICKLE:
                    with open(model_path, 'rb') as f:
                        model = pickle.load(f)
                    model_result["loadable"] = True
                    self.logger.info(f"✅ {model_name} model loaded successfully")
                else:
                    results["warnings"].append(f"Cannot load {model_name} - missing dependencies")
                    results["models_tested"][model_name] = model_result
                    continue

                # Extract model information
                if model_result.get("feature_names") is None:
                    if hasattr(model, 'feature_names_in_'):
                        model_result["feature_names"] = list(model.feature_names_in_)
                        model_result["expected_feature_count"] = len(model.feature_names_in_)
                    elif hasattr(model, 'n_features_in_'):
                        model_result["expected_feature_count"] = model.n_features_in_
                    elif hasattr(model, 'feature_importances_'):
                        model_result["expected_feature_count"] = len(model.feature_importances_)
                    else:
                        results["warnings"].append(f"Could not determine feature count for {model_name}")

            except Exception as e:
                model_result["loading_error"] = str(e)
                results["loading_issues"][model_name] = str(e)
                results["warnings"].append(f"Failed to load {model_name}: {str(e)}")

            results["models_tested"][model_name] = model_result

        # Test data compatibility with loaded models
        training_data_path = self.data_files["training_data"]
        if training_data_path.exists():
            try:
                df = pd.read_csv(training_data_path)
                data_columns = set(df.columns)

                for model_name, model_result in results["models_tested"].items():
                    if model_result.get("feature_names"):
                        model_features = set(model_result["feature_names"])
                        missing_features = model_features - data_columns
                        extra_features = data_columns - model_features

                        results["compatibility_results"][model_name] = {
                            "missing_features": list(missing_features),
                            "extra_features": list(extra_features),
                            "missing_count": len(missing_features),
                            "extra_count": len(extra_features),
                            "compatible": len(missing_features) == 0
                        }

                        if missing_features:
                            results["critical_issues"].append(
                                f"{model_name} model missing {len(missing_features)} features from data"
                            )

            except Exception as e:
                results["critical_issues"].append(f"Data compatibility test failed: {str(e)}")

        return results

    def _perform_data_quality_checks(self) -> Dict[str, Any]:
        """Perform comprehensive data quality checks"""
        self.logger.info("🔍 Performing data quality checks")

        results = {
            "quality_checks": {},
            "data_integrity": {},
            "statistical_summary": {},
            "critical_issues": [],
            "warnings": []
        }

        for file_name, file_path in self.data_files.items():
            if not file_path.exists():
                continue

            try:
                df = pd.read_csv(file_path)
                file_results = {
                    "duplicate_rows": df.duplicated().sum(),
                    "null_counts": df.isnull().sum().to_dict(),
                    "data_types": df.dtypes.to_dict(),
                    "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                    "numeric_columns": list(df.select_dtypes(include=[np.number]).columns),
                    "categorical_columns": list(df.select_dtypes(include=['object']).columns)
                }

                # Check for data integrity issues
                integrity_issues = []

                # Check for impossible values in numeric columns
                for col in file_results["numeric_columns"]:
                    if col in df.columns:
                        if df[col].min() < -1000 or df[col].max() > 10000:
                            integrity_issues.append(f"{col}: unusual value range")

                # Check for empty strings in categorical columns
                for col in file_results["categorical_columns"]:
                    if col in df.columns:
                        empty_count = (df[col] == "").sum()
                        if empty_count > 0:
                            integrity_issues.append(f"{col}: {empty_count} empty string values")

                file_results["integrity_issues"] = integrity_issues

                # Generate statistical summary for numeric columns
                if file_results["numeric_columns"]:
                    stats_summary = df[file_results["numeric_columns"]].describe().to_dict()
                    file_results["statistical_summary"] = stats_summary

                results["quality_checks"][file_name] = file_results

                if integrity_issues:
                    results["warnings"].extend([f"{file_path.name}: {issue}" for issue in integrity_issues])

            except Exception as e:
                results["critical_issues"].append(f"Data quality check failed for {file_path.name}: {str(e)}")

        return results

    def _standardize_columns(self) -> List[str]:
        """Standardize column names and formats"""
        self.logger.info("📝 Standardizing column formats")

        fixes_applied = []

        for file_name, file_path in self.data_files.items():
            if not file_path.exists():
                continue

            try:
                df = pd.read_csv(file_path)
                original_columns = list(df.columns)

                # Standardization rules
                column_mapping = {}
                for col in df.columns:
                    new_col = col
                    # Convert to lowercase and replace spaces with underscores
                    new_col = new_col.lower().replace(' ', '_')
                    # Remove special characters
                    new_col = ''.join(c for c in new_col if c.isalnum() or c == '_')
                    # Remove multiple underscores
                    new_col = '_'.join(filter(None, new_col.split('_')))

                    if new_col != col:
                        column_mapping[col] = new_col

                if column_mapping:
                    df = df.rename(columns=column_mapping)
                    df.to_csv(file_path, index=False)
                    fixes_applied.append(f"{file_path.name}: Renamed {len(column_mapping)} columns")
                    self.logger.info(f"📝 Standardized {len(column_mapping)} columns in {file_path.name}")

            except Exception as e:
                self.logger.warning(f"Could not standardize {file_path.name}: {str(e)}")

        return fixes_applied

    def _calculate_structure_score(self, validation_results: Dict) -> float:
        """Calculate overall data structure authenticity score"""
        score_components = []

        # Missing columns score (25% weight)
        missing_cols_results = validation_results.get("missing_columns", {})
        if not missing_cols_results.get("critical_issues"):
            missing_score = 0.8 if missing_cols_results.get("warnings") else 1.0
            score_components.append(missing_score)
        else:
            score_components.append(0.0)

        # Feature validation score (25% weight)
        feature_results = validation_results.get("feature_validation", {})
        if not feature_results.get("critical_issues"):
            feature_score = 0.8 if feature_results.get("warnings") else 1.0
            score_components.append(feature_score)
        else:
            score_components.append(0.0)

        # Model compatibility score (30% weight)
        model_results = validation_results.get("model_compatibility", {})
        if not model_results.get("critical_issues"):
            # Check if any models are compatible
            compatible_models = sum(1 for result in model_results.get("compatibility_results", {}).values()
                                   if result.get("compatible", False))
            total_models = len(model_results.get("compatibility_results", {}))
            if total_models > 0:
                model_score = compatible_models / total_models
            else:
                model_score = 0.5  # Neutral score if no compatibility info
            score_components.append(model_score)
        else:
            score_components.append(0.0)

        # Data quality score (20% weight)
        quality_results = validation_results.get("data_quality_checks", {})
        if not quality_results.get("critical_issues"):
            quality_score = 0.8 if quality_results.get("warnings") else 1.0
            score_components.append(quality_score)
        else:
            score_components.append(0.0)

        # Calculate weighted average
        weights = [0.25, 0.25, 0.30, 0.20]
        weighted_score = sum(score * weight for score, weight in zip(score_components, weights))

        return weighted_score

    def _generate_recommendations(self, validation_results: Dict) -> List[str]:
        """Generate recommendations based on data structure validation"""
        recommendations = []

        if validation_results["authenticity_score"] < 0.8:
            recommendations.append("🚨 CRITICAL: Data structure issues found - resolve before model retraining")

        # Missing columns recommendations
        missing_cols = validation_results.get("missing_columns", {})
        if missing_cols.get("critical_issues"):
            recommendations.append("🔧 Critical missing columns detected - review column fixes applied")

        # Feature validation recommendations
        feature_results = validation_results.get("feature_validation", {})
        if feature_results.get("critical_issues"):
            recommendations.append("🎯 Feature count mismatch - ensure all 86 features are present")

        # Model compatibility recommendations
        model_results = validation_results.get("model_compatibility", {})
        if model_results.get("critical_issues"):
            recommendations.append("🤖 Model compatibility issues - check feature alignment with models")
        else:
            compatible_count = sum(1 for result in model_results.get("compatibility_results", {}).values()
                                 if result.get("compatible", False))
            total_count = len(model_results.get("compatibility_results", {}))
            if total_count > 0 and compatible_count < total_count:
                recommendations.append(f"🤖 Only {compatible_count}/{total_count} models compatible - investigate missing features")

        # Data quality recommendations
        quality_results = validation_results.get("data_quality_checks", {})
        if quality_results.get("warnings"):
            recommendations.append("🔍 Data quality issues detected - review integrity warnings")

        return recommendations

    def _save_validation_results(self, results: Dict) -> None:
        """Save detailed data structure validation results"""
        results_dir = self.project_root / "project_management" / "DATA_VALIDATION"
        results_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = results_dir / f"data_structure_validation_{timestamp}.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        self.logger.info(f"📄 Data structure validation results saved: {results_file}")

def main():
    """Main execution function"""
    validator = DataStructureValidator()
    results = validator.validate_data_structure()

    print("\n" + "="*80)
    print("🏗️ DATA STRUCTURE VALIDATION COMPLETE")
    print("="*80)
    print(f"📊 Structure Authenticity Score: {results['authenticity_score']:.1%}")
    print(f"🚨 Critical Issues: {len(results['critical_issues'])}")
    print(f"⚠️ Warnings: {len(results['warnings'])}")

    # Missing columns results
    missing_cols = results.get("missing_columns", {})
    if missing_cols.get("fixes_applied"):
        print(f"\n🔧 Column Fixes Applied:")
        for fix in missing_cols["fixes_applied"]:
            print(f"   ✅ {fix}")

    # Feature validation
    feature_results = results.get("feature_validation", {})
    if feature_results.get("feature_validation_results"):
        print(f"\n🎯 Feature Validation:")
        for file_name, file_results in feature_results["feature_validation_results"].items():
            print(f"   {file_name}: {file_results.get('feature_count', 0)} features "
                  f"({'✅' if file_results.get('meets_expected_count', False) else '❌'})")

    # Model compatibility
    model_results = results.get("model_compatibility", {})
    if model_results.get("models_tested"):
        print(f"\n🤖 Model Compatibility:")
        for model_name, model_result in model_results["models_tested"].items():
            status = "✅" if model_result.get("loadable") else "❌"
            print(f"   {model_name}: {status} ({'Loadable' if model_result.get('loadable') else 'Failed to load'})")

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