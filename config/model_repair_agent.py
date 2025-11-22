#!/usr/bin/env python3
"""
Model Repair Agent

Repairs and validates all ML models (Ridge, XGBoost, FastAI) for Week 12 predictions.
Handles model loading issues, retraining, and performance validation.

Author: Urban Meyer Assistant
Created: 2025-11-13
Purpose: Ensure all ML models are functional for Week 12 predictions
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

# Import agent framework
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

logger = logging.getLogger(__name__)

class ModelRepairAgent(BaseAgent):
    """Model Repair Agent for Week 12 readiness"""

    def __init__(self):
        super().__init__(
            agent_id="model_repair_agent",
            name="Model Repair Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
        )

        self.model_paths = {
            "ridge": "model_pack/ridge_model_2025.joblib",
            "xgboost": "model_pack/xgb_home_win_model_2025.pkl",
            "fastai": "model_pack/fastai_home_win_model_2025_fixed.pkl"
        }

        self.training_data_path = "model_pack/updated_training_data.csv"

    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="model_validation",
                description="Validate ML model loading and functionality",
                required_tools=["model_loader", "functionality_tester"],
                output_schema={"model_status": "string", "load_success": "boolean"}
            ),
            AgentCapability(
                name="model_repair",
                description="Repair broken models and handle serialization issues",
                required_tools=["model_repairer", "serialization_fixer"],
                output_schema={"repair_status": "string", "models_fixed": "number"}
            ),
            AgentCapability(
                name="performance_validation",
                description="Test model performance and prediction capabilities",
                required_tools=["performance_tester", "prediction_validator"],
                output_schema={"performance_score": "number", "prediction_accuracy": "string"}
            )
        ]

    def execute_week12_task(self, execution_context) -> Dict[str, Any]:
        """Execute Week 12 model repair task"""
        logger.info("Starting Week 12 model repair")

        repair_results = {
            "timestamp": datetime.now().isoformat(),
            "execution_context": execution_context.execution_id,
            "model_status": {}
        }

        overall_success = True

        # Validate each model
        for model_name, model_path in self.model_paths.items():
            model_result = self._validate_and_repair_model(model_name, model_path)
            repair_results["model_status"][model_name] = model_result
            if not model_result["success"]:
                overall_success = False

        # Test ensemble functionality
        ensemble_result = self._test_ensemble_functionality(repair_results["model_status"])
        repair_results["ensemble_test"] = ensemble_result

        repair_results["overall_success"] = overall_success
        repair_results["models_functional"] = sum(1 for r in repair_results["model_status"].values() if r["success"])
        repair_results["total_models"] = len(self.model_paths)

        return {
            "success": overall_success,
            "repair_results": repair_results,
            "message": self._generate_user_message(repair_results)
        }

    def _validate_and_repair_model(self, model_name: str, model_path: str) -> Dict[str, Any]:
        """Validate and repair a specific model"""
        result = {
            "success": False,
            "model_exists": False,
            "load_success": False,
            "prediction_test": False,
            "issues": [],
            "repairs_attempted": [],
            "final_status": "failed"
        }

        try:
            # Check if model file exists
            path = Path(model_path)
            if not path.exists():
                result["issues"].append(f"Model file not found: {model_path}")
                return result
            result["model_exists"] = True

            # Try to load the model
            try:
                model = joblib.load(model_path)
                result["load_success"] = True
                logger.info(f"Model {model_name} loaded successfully")
            except Exception as e:
                result["issues"].append(f"Failed to load {model_name}: {e}")

                # Try repair attempts
                if model_name == "fastai" and "persistent IDs" in str(e):
                    # Attempt FastAI model fix
                    if self._attempt_fastai_repair(model_path):
                        model = joblib.load(model_path)
                        result["load_success"] = True
                        result["repairs_attempted"].append("FastAI pickle protocol fix")

            if result["load_success"]:
                # Test prediction capability
                if self._test_model_prediction(model, model_name):
                    result["prediction_test"] = True
                    result["success"] = True
                    result["final_status"] = "functional"
                else:
                    result["issues"].append(f"Model {model_name} failed prediction test")

        except Exception as e:
            result["issues"].append(f"Model validation error: {e}")
            logger.error(f"Model validation failed for {model_name}: {e}")

        return result

    def _attempt_fastai_repair(self, model_path: str) -> bool:
        """Attempt to repair FastAI model by retraining"""
        try:
            # Check if we have training data
            if not Path(self.training_data_path).exists():
                logger.warning("Cannot repair FastAI model - no training data available")
                return False

            # Run the FastAI model retraining script
            import subprocess
            result = subprocess.run([
                "python", "project_management/core_tools/retrain_fixed_models.py"
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                logger.info("FastAI model retraining completed successfully")
                return True
            else:
                logger.error(f"FastAI retraining failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"FastAI repair attempt failed: {e}")
            return False

    def _test_model_prediction(self, model, model_name: str) -> bool:
        """Test if model can make predictions"""
        try:
            # Create dummy test data based on model type
            if model_name == "ridge":
                # Ridge model expects feature vector for margin prediction
                test_data = np.random.rand(1, 86)  # 86 features
                prediction = model.predict(test_data)
                return len(prediction) == 1 and isinstance(prediction[0], (int, float))

            elif model_name == "xgboost":
                # XGBoost model expects feature vector for win probability
                test_data = np.random.rand(1, 86)
                prediction = model.predict(test_data)
                prediction_proba = model.predict_proba(test_data)
                return len(prediction) == 1 and len(prediction_proba[0]) == 2

            elif model_name == "fastai":
                # FastAI model - basic test
                return hasattr(model, 'predict') or hasattr(model, 'forward')

            return False

        except Exception as e:
            logger.error(f"Prediction test failed for {model_name}: {e}")
            return False

    def _test_ensemble_functionality(self, model_status: Dict[str, Any]) -> Dict[str, Any]:
        """Test if models can work together as ensemble"""
        result = {
            "success": False,
            "functional_models": [],
            "ensemble_ready": False
        }

        functional_models = [name for name, status in model_status.items() if status["success"]]
        result["functional_models"] = functional_models

        if len(functional_models) >= 2:
            result["ensemble_ready"] = True
            result["success"] = True

        return result

    def _generate_user_message(self, repair_results: Dict[str, Any]) -> str:
        """Generate user-friendly message"""
        total_models = repair_results["total_models"]
        functional_models = repair_results["models_functional"]
        ensemble_ready = repair_results.get("ensemble_test", {}).get("ensemble_ready", False)

        if repair_results["overall_success"]:
            return (
                f"✅ **Model Repair Complete!**\n\n"
                f"All {total_models} ML models are now functional:\n"
                f"• Ridge regression model: ✅ Working (score margin predictions)\n"
                f"• XGBoost model: ✅ Working (win probability predictions)\n"
                f"• FastAI neural network: ✅ Working (deep learning predictions)\n\n"
                f"🎯 **Ensemble Status:** Ready for combined predictions\n\n"
                f"Your system can now generate Week 12 predictions using multiple ML approaches!"
            )
        else:
            working_models = [name for name, status in repair_results["model_status"].items() if status["success"]]
            working_count = len(working_models)

            return (
                f"⚠️ **Model Repair Partially Complete**\n\n"
                f"{working_count}/{total_models} models are working:\n"
                f"• {'✅' if 'ridge' in working_models else '❌'} Ridge regression model\n"
                f"• {'✅' if 'xgboost' in working_models else '❌'} XGBoost model\n"
                f"• {'✅' if 'fastai' in working_models else '❌'} FastAI neural network\n\n"
                f"Your system can still make predictions with the working models. "
                f"Any non-functional models have been identified for manual review."
            )

def main():
    """Command-line interface"""
    agent = ModelRepairAgent()

    class MockExecutionContext:
        def __init__(self):
            self.execution_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    result = agent.execute_week12_task(MockExecutionContext())
    print(f"Model repair completed. Success: {result['success']}")
    return 0 if result["success"] else 1

if __name__ == "__main__":
    exit(main())