#!/usr/bin/env python3
"""
Model Execution Agent - Tier 4 Security Level
Advanced ML model execution with GPU acceleration and ensemble methods

Implements comprehensive model execution framework with multiple ML algorithms,
GPU acceleration, ensemble predictions, and real-time inference capabilities.
"""

import logging
import json
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import joblib
import pickle
import os
from pathlib import Path
import traceback

# ML libraries
import sklearn
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

try:
    import xgboost as xgb

    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from agents.core.enhanced_agent_framework import EnhancedBaseAgent
from agents.core.security_manager import security_manager, PermissionLevel


class ModelType(Enum):
    """Supported model types"""

    RIDGE_REGRESSION = "ridge_regression"
    LOGISTIC_REGRESSION = "logistic_regression"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"
    AUTO_ML = "auto_ml"


class PredictionType(Enum):
    """Prediction output types"""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    PROBABILITY = "probability"
    SCORE = "score"


class ModelStatus(Enum):
    """Model status enumeration"""

    LOADING = "loading"
    READY = "ready"
    PREDICTING = "predicting"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


@dataclass
class ModelInfo:
    """Model information and metadata"""

    model_id: str
    model_type: ModelType
    model_path: str
    feature_columns: List[str]
    target_column: str
    prediction_type: PredictionType
    version: str
    trained_at: datetime
    accuracy: float = 0.0
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionRequest:
    """Prediction request with metadata"""

    request_id: str
    model_id: str
    data: Union[pd.DataFrame, List[Dict], np.ndarray]
    return_probabilities: bool = False
    batch_size: Optional[int] = None
    priority: int = 5  # 1-10, 10 being highest
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionResult:
    """Prediction result with detailed information"""

    request_id: str
    model_id: str
    predictions: Union[List, np.ndarray]
    probabilities: Optional[Union[List, np.ndarray]] = None
    confidence_scores: Optional[List[float]] = None
    feature_importance: Optional[Dict[str, float]] = None
    execution_time_seconds: float = 0.0
    record_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class ModelExecutionAgent(EnhancedBaseAgent):
    """
    Model Execution Agent - Advanced ML model execution with GPU acceleration

    Capabilities:
    - Multi-algorithm model execution (Ridge, XGBoost, Neural Networks)
    - GPU acceleration for supported models
    - Ensemble model predictions with weighted voting
    - Real-time batch prediction processing
    - Model versioning and hot-swapping
    - Performance monitoring and optimization
    - Feature preprocessing and scaling
    """

    def __init__(self, agent_id: str = "model_execution_agent"):
        super().__init__(
            agent_id=agent_id,
            agent_name="Model Execution Agent",
            permission_level=PermissionLevel.READ_EXECUTE,
        )

        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

        # Model configuration
        self.models_directory = Path("/app/models")
        self.models_directory.mkdir(parents=True, exist_ok=True)
        self.production_models_directory = Path("/app/models/production")
        self.production_models_directory.mkdir(parents=True, exist_ok=True)

        # Loaded models cache
        self.loaded_models: Dict[str, Any] = {}
        self.model_info: Dict[str, ModelInfo] = {}

        # Execution configuration
        self.default_batch_size = 1000
        self.max_concurrent_predictions = 10
        self.gpu_available = self._check_gpu_availability()
        self.use_gpu = (
            self.gpu_available
            and os.getenv("GPU_ACCELERATION", "true").lower() == "true"
        )

        # Performance metrics
        self.metrics = {
            "predictions_executed": 0,
            "records_predicted": 0,
            "average_prediction_time": 0.0,
            "model_usage": {},
            "gpu_utilization": 0.0,
            "memory_usage_mb": 0.0,
            "error_rate": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Load production models
        self._load_production_models()

    def _define_capabilities(self) -> List:
        """Define model execution capabilities"""
        return [
            {
                "name": "execute_model_predictions",
                "description": "Execute predictions using loaded ML models",
                "execution_time_estimate": 8.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["model_id", "data", "prediction_config"],
                "returns": {
                    "predictions": "array",
                    "probabilities": "array",
                    "confidence_scores": "array",
                },
            },
            {
                "name": "ensemble_predictions",
                "description": "Generate ensemble predictions from multiple models",
                "execution_time_estimate": 15.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["model_ids", "data", "ensemble_method"],
                "returns": {
                    "ensemble_predictions": "array",
                    "individual_predictions": "dict",
                    "weights": "list",
                },
            },
            {
                "name": "batch_predict",
                "description": "Execute batch predictions with optimized processing",
                "execution_time_estimate": 12.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["requests", "parallel_execution", "optimization_level"],
                "returns": {
                    "results": "list",
                    "performance_metrics": "dict",
                    "summary": "dict",
                },
            },
            {
                "name": "load_model",
                "description": "Load or reload ML models into memory",
                "execution_time_estimate": 5.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE_WRITE],
                "parameters": ["model_path", "model_type", "force_reload"],
                "returns": {
                    "model_id": "string",
                    "load_status": "string",
                    "model_info": "object",
                },
            },
            {
                "name": "get_model_info",
                "description": "Get detailed information about loaded models",
                "execution_time_estimate": 2.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["model_id", "include_metrics"],
                "returns": {
                    "model_info": "object",
                    "performance_metrics": "dict",
                    "usage_stats": "dict",
                },
            },
        ]

    def _execute_action(
        self, action: str, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Execute model execution actions"""
        try:
            # Create security context
            context = security_manager.create_security_context(
                user_id=user_context.get("user_id", "model_execution_system"),
                permissions=["model_execution", "gpu_acceleration", "inference_access"],
            )

            if action == "execute_model_predictions":
                return self._execute_model_predictions(parameters, context)
            elif action == "ensemble_predictions":
                return self._ensemble_predictions(parameters, context)
            elif action == "batch_predict":
                return self._batch_predict(parameters, context)
            elif action == "load_model":
                return self._load_model(parameters, context)
            elif action == "get_model_info":
                return self._get_model_info(parameters, context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            self.logger.error(f"Model execution action {action} failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _execute_model_predictions(self, parameters: Dict, context) -> Dict:
        """Execute predictions using loaded ML models"""
        self.logger.info("Executing model predictions")

        model_id = parameters.get("model_id")
        data = parameters.get("data", [])
        prediction_config = parameters.get("prediction_config", {})

        if not model_id:
            return {"status": "error", "error": "Model ID is required for prediction"}

        if not data:
            return {"status": "error", "error": "No data provided for prediction"}

        # Create prediction request
        request = PredictionRequest(
            request_id=f"pred_{int(time.time())}_{len(data)}",
            model_id=model_id,
            data=data,
            return_probabilities=prediction_config.get("return_probabilities", False),
            batch_size=prediction_config.get("batch_size", self.default_batch_size),
            priority=parameters.get("priority", 5),
            metadata=prediction_config.get("metadata", {}),
        )

        # Execute prediction
        start_time = time.time()
        result = self._execute_prediction(request, context)
        execution_time = time.time() - start_time

        if result.error_message:
            return {
                "status": "error",
                "error": result.error_message,
                "request_id": request.request_id,
                "execution_time": execution_time,
                "agent_id": self.agent_id,
            }
        else:
            # Update metrics
            self._update_prediction_metrics(result, execution_time)

            return {
                "status": "success",
                "data": {
                    "predictions": (
                        result.predictions.tolist()
                        if hasattr(result.predictions, "tolist")
                        else result.predictions
                    ),
                    "probabilities": (
                        result.probabilities.tolist()
                        if result.probabilities is not None
                        and hasattr(result.probabilities, "tolist")
                        else result.probabilities
                    ),
                    "confidence_scores": result.confidence_scores,
                    "feature_importance": result.feature_importance,
                    "record_count": result.record_count,
                    "execution_time_seconds": result.execution_time_seconds,
                    "model_info": {
                        "model_id": result.model_id,
                        "model_type": (
                            self.model_info.get(model_id, {}).model_type.value
                            if model_id in self.model_info
                            else "unknown"
                        ),
                    },
                },
                "execution_time": execution_time,
                "request_id": request.request_id,
                "agent_id": self.agent_id,
            }

    def _ensemble_predictions(self, parameters: Dict, context) -> Dict:
        """Generate ensemble predictions from multiple models"""
        self.logger.info("Executing ensemble predictions")

        model_ids = parameters.get("model_ids", [])
        data = parameters.get("data", [])
        ensemble_method = parameters.get("ensemble_method", "weighted_average")
        weights = parameters.get("weights", None)

        if not model_ids:
            return {
                "status": "error",
                "error": "At least one model ID is required for ensemble prediction",
            }

        if not data:
            return {
                "status": "error",
                "error": "No data provided for ensemble prediction",
            }

        start_time = time.time()

        try:
            # Collect predictions from all models
            individual_predictions = {}
            model_weights = {}

            for model_id in model_ids:
                # Create prediction request for each model
                request = PredictionRequest(
                    request_id=f"ensemble_{model_id}_{int(time.time())}",
                    model_id=model_id,
                    data=data,
                    return_probabilities=True,
                    priority=parameters.get("priority", 5),
                )

                result = self._execute_prediction(request, context)
                if not result.error_message:
                    individual_predictions[model_id] = result.predictions
                    # Use model accuracy as default weight if not provided
                    model_weights[model_id] = (
                        self.model_info.get(model_id, {}).accuracy or 1.0
                    )
                else:
                    self.logger.warning(
                        f"Model {model_id} failed in ensemble: {result.error_message}"
                    )

            if not individual_predictions:
                return {
                    "status": "error",
                    "error": "No models provided valid predictions for ensemble",
                }

            # Normalize weights if not provided
            if weights is None:
                total_weight = sum(model_weights.values())
                weights = {k: v / total_weight for k, v in model_weights.items()}

            # Generate ensemble predictions
            ensemble_predictions = self._combine_ensemble_predictions(
                individual_predictions, ensemble_method, weights
            )

            # Calculate ensemble confidence scores
            confidence_scores = self._calculate_ensemble_confidence(
                individual_predictions, ensemble_predictions
            )

            execution_time = time.time() - start_time

            return {
                "status": "success",
                "data": {
                    "ensemble_predictions": (
                        ensemble_predictions.tolist()
                        if hasattr(ensemble_predictions, "tolist")
                        else ensemble_predictions
                    ),
                    "individual_predictions": {
                        model_id: preds.tolist() if hasattr(preds, "tolist") else preds
                        for model_id, preds in individual_predictions.items()
                    },
                    "weights": weights,
                    "ensemble_method": ensemble_method,
                    "confidence_scores": confidence_scores,
                    "model_count": len(individual_predictions),
                    "record_count": len(data),
                },
                "execution_time": execution_time,
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Ensemble prediction failed: {str(e)}",
                "execution_time": time.time() - start_time,
                "agent_id": self.agent_id,
            }

    def _batch_predict(self, parameters: Dict, context) -> Dict:
        """Execute batch predictions with optimized processing"""
        self.logger.info("Executing batch predictions")

        requests = parameters.get("requests", [])
        parallel_execution = parameters.get("parallel_execution", True)
        optimization_level = parameters.get("optimization_level", "standard")

        if not requests:
            return {
                "status": "error",
                "error": "No prediction requests provided for batch execution",
            }

        start_time = time.time()

        try:
            if parallel_execution:
                results = self._execute_batch_parallel(
                    requests, context, optimization_level
                )
            else:
                results = self._execute_batch_sequential(
                    requests, context, optimization_level
                )

            # Calculate performance metrics
            successful_requests = sum(1 for r in results if r.get("success", False))
            total_records = sum(r.get("record_count", 0) for r in results)
            total_execution_time = sum(r.get("execution_time", 0) for r in results)

            execution_time = time.time() - start_time

            return {
                "status": "success",
                "data": {
                    "results": results,
                    "performance_metrics": {
                        "total_requests": len(requests),
                        "successful_requests": successful_requests,
                        "failed_requests": len(requests) - successful_requests,
                        "success_rate": successful_requests / len(requests) * 100,
                        "total_records": total_records,
                        "total_execution_time": total_execution_time,
                        "average_time_per_request": (
                            total_execution_time / len(requests) if requests else 0
                        ),
                        "records_per_second": (
                            total_records / execution_time if execution_time > 0 else 0
                        ),
                    },
                    "summary": {
                        "batch_id": f"batch_{int(time.time())}",
                        "optimization_level": optimization_level,
                        "parallel_execution": parallel_execution,
                    },
                },
                "execution_time": execution_time,
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Batch prediction failed: {str(e)}",
                "execution_time": time.time() - start_time,
                "agent_id": self.agent_id,
            }

    def _load_model(self, parameters: Dict, context) -> Dict:
        """Load or reload ML models into memory"""
        self.logger.info("Loading model")

        model_path = parameters.get("model_path")
        model_type = parameters.get("model_type", "auto")
        force_reload = parameters.get("force_reload", False)

        if not model_path:
            return {"status": "error", "error": "Model path is required"}

        model_path = Path(model_path)
        if not model_path.exists():
            return {"status": "error", "error": f"Model file not found: {model_path}"}

        start_time = time.time()

        try:
            # Generate model ID
            model_id = f"model_{model_path.stem}_{int(time.time())}"

            # Auto-detect model type if not specified
            if model_type == "auto":
                model_type = self._detect_model_type(model_path)

            # Load model
            model = self._load_model_from_file(model_path, model_type)

            # Store loaded model
            self.loaded_models[model_id] = model

            # Create model info
            model_info = ModelInfo(
                model_id=model_id,
                model_type=ModelType(model_type),
                model_path=str(model_path),
                feature_columns=parameters.get("feature_columns", []),
                target_column=parameters.get("target_column", ""),
                prediction_type=PredictionType(
                    parameters.get("prediction_type", "classification")
                ),
                version=parameters.get("version", "1.0"),
                trained_at=datetime.fromtimestamp(model_path.stat().st_mtime),
                accuracy=parameters.get("accuracy", 0.0),
                description=parameters.get("description", ""),
                parameters=parameters.get("model_parameters", {}),
            )

            self.model_info[model_id] = model_info

            execution_time = time.time() - start_time

            # Log model loading
            security_manager.log_security_event(
                event_type="model_loaded",
                user_id=context.get("user_id", "model_execution_system"),
                resource_id=model_id,
                details={
                    "model_path": str(model_path),
                    "model_type": model_type,
                    "force_reload": force_reload,
                },
            )

            return {
                "status": "success",
                "data": {
                    "model_id": model_id,
                    "load_status": "loaded",
                    "model_info": {
                        "model_type": model_info.model_type.value,
                        "prediction_type": model_info.prediction_type.value,
                        "version": model_info.version,
                        "trained_at": model_info.trained_at.isoformat(),
                        "accuracy": model_info.accuracy,
                        "feature_count": len(model_info.feature_columns),
                    },
                },
                "execution_time": execution_time,
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Model loading failed: {str(e)}",
                "execution_time": time.time() - start_time,
                "agent_id": self.agent_id,
            }

    def _get_model_info(self, parameters: Dict, context) -> Dict:
        """Get detailed information about loaded models"""
        self.logger.info("Retrieving model information")

        model_id = parameters.get("model_id")
        include_metrics = parameters.get("include_metrics", True)

        if model_id and model_id not in self.loaded_models:
            return {
                "status": "error",
                "error": f"Model {model_id} not found or not loaded",
            }

        start_time = time.time()

        try:
            if model_id:
                # Return info for specific model
                model_info = self.model_info.get(model_id)
                if model_info:
                    result = {
                        "model_info": {
                            "model_id": model_info.model_id,
                            "model_type": model_info.model_type.value,
                            "prediction_type": model_info.prediction_type.value,
                            "feature_columns": model_info.feature_columns,
                            "target_column": model_info.target_column,
                            "version": model_info.version,
                            "trained_at": model_info.trained_at.isoformat(),
                            "accuracy": model_info.accuracy,
                            "description": model_info.description,
                            "parameters": model_info.parameters,
                        },
                        "usage_stats": self.metrics.get("model_usage", {}).get(
                            model_id, {}
                        ),
                        "status": (
                            "loaded" if model_id in self.loaded_models else "not_loaded"
                        ),
                    }

                    if include_metrics:
                        result["performance_metrics"] = (
                            self._get_model_performance_metrics(model_id)
                        )

                    return {
                        "status": "success",
                        "data": result,
                        "execution_time": time.time() - start_time,
                        "agent_id": self.agent_id,
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"No information available for model {model_id}",
                    }
            else:
                # Return info for all loaded models
                models_info = {}
                for mid, info in self.model_info.items():
                    models_info[mid] = {
                        "model_type": info.model_type.value,
                        "prediction_type": info.prediction_type.value,
                        "feature_count": len(info.feature_columns),
                        "accuracy": info.accuracy,
                        "version": info.version,
                        "status": (
                            "loaded" if mid in self.loaded_models else "not_loaded"
                        ),
                    }

                return {
                    "status": "success",
                    "data": {
                        "models_info": models_info,
                        "total_models": len(models_info),
                        "loaded_models": len(self.loaded_models),
                        "system_metrics": {
                            "gpu_available": self.gpu_available,
                            "gpu_in_use": self.use_gpu,
                            "total_predictions": self.metrics["predictions_executed"],
                            "total_records_predicted": self.metrics[
                                "records_predicted"
                            ],
                        },
                    },
                    "execution_time": time.time() - start_time,
                    "agent_id": self.agent_id,
                }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to retrieve model information: {str(e)}",
                "execution_time": time.time() - start_time,
                "agent_id": self.agent_id,
            }

    # Core prediction execution methods
    def _execute_prediction(
        self, request: PredictionRequest, context
    ) -> PredictionResult:
        """Execute a single prediction request"""
        start_time = time.time()

        try:
            # Check if model is loaded
            if request.model_id not in self.loaded_models:
                # Try to load the model
                model_info = self._find_model_info(request.model_id)
                if model_info:
                    self._load_model_from_file(
                        model_info.model_path, model_info.model_type.value
                    )
                else:
                    return PredictionResult(
                        request_id=request.request_id,
                        model_id=request.model_id,
                        predictions=[],
                        error_message=f"Model {request.model_id} not found or not loaded",
                    )

            model = self.loaded_models[request.model_id]
            model_info = self.model_info.get(request.model_id)

            # Prepare data
            df = self._prepare_prediction_data(request.data, model_info)

            if df.empty:
                return PredictionResult(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    predictions=[],
                    record_count=0,
                    error_message="No valid data provided for prediction",
                )

            # Execute prediction based on model type
            predictions, probabilities = self._predict_with_model(
                model, df, model_info, request
            )

            # Calculate confidence scores if available
            confidence_scores = self._calculate_confidence_scores(
                predictions, probabilities
            )

            # Get feature importance if available
            feature_importance = self._get_feature_importance(model, model_info)

            execution_time = time.time() - start_time

            return PredictionResult(
                request_id=request.request_id,
                model_id=request.model_id,
                predictions=predictions,
                probabilities=probabilities if request.return_probabilities else None,
                confidence_scores=confidence_scores,
                feature_importance=feature_importance,
                execution_time_seconds=execution_time,
                record_count=len(df),
                metadata=request.metadata,
            )

        except Exception as e:
            return PredictionResult(
                request_id=request.request_id,
                model_id=request.model_id,
                predictions=[],
                error_message=f"Prediction execution failed: {str(e)}",
                execution_time_seconds=time.time() - start_time,
            )

    def _predict_with_model(
        self,
        model: Any,
        df: pd.DataFrame,
        model_info: ModelInfo,
        request: PredictionRequest,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Execute prediction with specific model"""
        try:
            # Select relevant features
            if model_info.feature_columns:
                features_df = df[model_info.feature_columns]
            else:
                features_df = df

            # Handle missing values
            features_df = features_df.fillna(features_df.mean())

            # Convert to numpy if needed
            X = features_df.values if hasattr(features_df, "values") else features_df

            # Execute prediction based on model type
            if model_info.model_type == ModelType.RIDGE_REGRESSION:
                predictions = model.predict(X)
                probabilities = None

            elif model_info.model_type == ModelType.LOGISTIC_REGRESSION:
                predictions = model.predict(X)
                if hasattr(model, "predict_proba") and request.return_probabilities:
                    probabilities = model.predict_proba(X)
                else:
                    probabilities = None

            elif model_info.model_type == ModelType.RANDOM_FOREST:
                predictions = model.predict(X)
                if hasattr(model, "predict_proba") and request.return_probabilities:
                    probabilities = model.predict_proba(X)
                else:
                    probabilities = None

            elif model_info.model_type == ModelType.XGBOOST:
                predictions = model.predict(X)
                if hasattr(model, "predict_proba") and request.return_probabilities:
                    probabilities = model.predict_proba(X)
                else:
                    probabilities = None

            elif model_info.model_type == ModelType.NEURAL_NETWORK:
                # Handle PyTorch neural network
                if isinstance(model, nn.Module):
                    model.eval()
                    with torch.no_grad():
                        X_tensor = torch.FloatTensor(X)
                        if self.use_gpu and torch.cuda.is_available():
                            X_tensor = X_tensor.cuda()
                            model = model.cuda()

                        outputs = model(X_tensor)
                        predictions = outputs.cpu().numpy()

                        if request.return_probabilities and hasattr(
                            torch.nn.functional, "softmax"
                        ):
                            probabilities = (
                                torch.nn.functional.softmax(outputs, dim=1)
                                .cpu()
                                .numpy()
                            )
                        else:
                            probabilities = None
                else:
                    predictions = model.predict(X)
                    probabilities = None

            else:
                # Default prediction
                predictions = model.predict(X)
                probabilities = None

            return predictions, probabilities

        except Exception as e:
            self.logger.error(f"Model prediction failed: {str(e)}")
            raise e

    # Helper methods
    def _check_gpu_availability(self) -> bool:
        """Check if GPU is available for ML acceleration"""
        try:
            if TORCH_AVAILABLE:
                return torch.cuda.is_available()
            else:
                # Check for other GPU libraries
                return False
        except Exception:
            return False

    def _load_production_models(self) -> None:
        """Load production models from default directory"""
        try:
            # Look for production models
            model_files = (
                list(self.production_models_directory.glob("*.joblib"))
                + list(self.production_models_directory.glob("*.pkl"))
                + list(self.production_models_directory.glob("*.pth"))
            )

            for model_file in model_files:
                try:
                    model_type = self._detect_model_type(model_file)
                    model_id = f"prod_{model_file.stem}"

                    # Try to load model
                    model = self._load_model_from_file(model_file, model_type)
                    self.loaded_models[model_id] = model

                    # Create basic model info
                    self.model_info[model_id] = ModelInfo(
                        model_id=model_id,
                        model_type=ModelType(model_type),
                        model_path=str(model_file),
                        feature_columns=[],
                        target_column="",
                        prediction_type=PredictionType.CLASSIFICATION,
                        version="1.0",
                        trained_at=datetime.fromtimestamp(model_file.stat().st_mtime),
                    )

                    self.logger.info(f"Loaded production model: {model_id}")

                except Exception as e:
                    self.logger.warning(
                        f"Failed to load production model {model_file}: {e}"
                    )

        except Exception as e:
            self.logger.warning(f"Failed to load production models: {e}")

    def _detect_model_type(self, model_path: Path) -> str:
        """Auto-detect model type from file path and content"""
        filename = model_path.name.lower()

        if "ridge" in filename:
            return ModelType.RIDGE_REGRESSION.value
        elif "logistic" in filename:
            return ModelType.LOGISTIC_REGRESSION.value
        elif "random_forest" in filename or "rf" in filename:
            return ModelType.RANDOM_FOREST.value
        elif "xgboost" in filename or "xgb" in filename:
            return ModelType.XGBOOST.value
        elif "neural" in filename or "nn" in filename or "torch" in filename:
            return ModelType.NEURAL_NETWORK.value
        else:
            # Try to inspect the file
            try:
                if model_path.suffix == ".pth":
                    return ModelType.NEURAL_NETWORK.value
                elif model_path.suffix in [".pkl", ".joblib"]:
                    # Could be any sklearn model, default to random forest
                    return ModelType.RANDOM_FOREST.value
                else:
                    return ModelType.RANDOM_FOREST.value
            except Exception:
                return ModelType.RANDOM_FOREST.value

    def _load_model_from_file(self, model_path: Path, model_type: str) -> Any:
        """Load model from file based on type"""
        try:
            if (
                model_type == ModelType.NEURAL_NETWORK.value
                and model_path.suffix == ".pth"
            ):
                # Load PyTorch model
                if TORCH_AVAILABLE:
                    return torch.load(model_path, map_location="cpu")
                else:
                    raise ImportError(
                        "PyTorch not available for neural network loading"
                    )
            else:
                # Load sklearn-style models
                if model_path.suffix == ".joblib":
                    return joblib.load(model_path)
                elif model_path.suffix == ".pkl":
                    with open(model_path, "rb") as f:
                        return pickle.load(f)
                else:
                    raise ValueError(
                        f"Unsupported model file format: {model_path.suffix}"
                    )

        except Exception as e:
            self.logger.error(f"Failed to load model {model_path}: {str(e)}")
            raise e

    def _prepare_prediction_data(
        self, data: Any, model_info: Optional[ModelInfo]
    ) -> pd.DataFrame:
        """Prepare data for prediction"""
        try:
            if isinstance(data, pd.DataFrame):
                return data
            elif isinstance(data, list) and data and isinstance(data[0], dict):
                return pd.DataFrame(data)
            elif isinstance(data, np.ndarray):
                # Convert numpy array to DataFrame
                if model_info and model_info.feature_columns:
                    return pd.DataFrame(data, columns=model_info.feature_columns)
                else:
                    return pd.DataFrame(data)
            elif isinstance(data, dict):
                return pd.DataFrame([data])
            else:
                # Convert to DataFrame with single value
                return pd.DataFrame({"value": [data]})
        except Exception as e:
            self.logger.error(f"Failed to prepare prediction data: {str(e)}")
            raise e

    def _calculate_confidence_scores(
        self, predictions: np.ndarray, probabilities: Optional[np.ndarray]
    ) -> Optional[List[float]]:
        """Calculate confidence scores for predictions"""
        try:
            if probabilities is not None:
                # Use max probability as confidence
                return np.max(probabilities, axis=1).tolist()
            elif len(predictions.shape) == 1:
                # For binary classification, use distance from decision boundary
                return np.abs(predictions).tolist()
            else:
                # For multi-class, use softmax-like normalization
                exp_preds = np.exp(predictions)
                sum_exp = np.sum(exp_preds, axis=1, keepdims=True)
                return np.max(exp_preds / sum_exp, axis=1).tolist()
        except Exception:
            return None

    def _get_feature_importance(
        self, model: Any, model_info: Optional[ModelInfo]
    ) -> Optional[Dict[str, float]]:
        """Get feature importance from model if available"""
        try:
            if hasattr(model, "feature_importances_"):
                # Tree-based models
                if model_info and model_info.feature_columns:
                    return dict(
                        zip(model_info.feature_columns, model.feature_importances_)
                    )
                else:
                    return {
                        f"feature_{i}": imp
                        for i, imp in enumerate(model.feature_importances_)
                    }
            elif hasattr(model, "coef_"):
                # Linear models
                coef = model.coef_
                if len(coef.shape) > 1:
                    coef = coef[0]  # Take first class for multi-class
                if model_info and model_info.feature_columns:
                    return dict(zip(model_info.feature_columns, np.abs(coef)))
                else:
                    return {
                        f"feature_{i}": float(np.abs(imp)) for i, imp in enumerate(coef)
                    }
            else:
                return None
        except Exception:
            return None

    def _combine_ensemble_predictions(
        self,
        individual_predictions: Dict[str, np.ndarray],
        ensemble_method: str,
        weights: Dict[str, float],
    ) -> np.ndarray:
        """Combine individual model predictions into ensemble prediction"""
        try:
            predictions_array = np.array(list(individual_predictions.values()))
            weight_array = np.array(
                [weights[model_id] for model_id in individual_predictions.keys()]
            )

            if ensemble_method == "weighted_average":
                # Weighted average
                ensemble_pred = np.average(
                    predictions_array, axis=0, weights=weight_array
                )
            elif ensemble_method == "majority_vote":
                # Majority voting (for classification)
                ensemble_pred = np.apply_along_axis(
                    lambda x: np.bincount(x.astype(int)).argmax(),
                    axis=0,
                    arr=predictions_array.astype(int),
                )
            elif ensemble_method == "max_confidence":
                # Use prediction from model with highest weight
                max_weight_model = max(weights.items(), key=lambda x: x[1])[0]
                ensemble_pred = individual_predictions[max_weight_model]
            else:
                # Simple average
                ensemble_pred = np.mean(predictions_array, axis=0)

            return ensemble_pred

        except Exception as e:
            self.logger.error(f"Ensemble combination failed: {str(e)}")
            # Fallback to simple average
            return np.mean(list(individual_predictions.values()), axis=0)

    def _calculate_ensemble_confidence(
        self,
        individual_predictions: Dict[str, np.ndarray],
        ensemble_predictions: np.ndarray,
    ) -> List[float]:
        """Calculate confidence scores for ensemble predictions"""
        try:
            # Calculate standard deviation across individual predictions
            predictions_array = np.array(list(individual_predictions.values()))
            std_dev = np.std(predictions_array, axis=0)

            # Convert std deviation to confidence (inverse relationship)
            max_std = np.max(std_dev)
            if max_std > 0:
                confidence = 1 - (std_dev / max_std)
            else:
                confidence = np.ones_like(std_dev)

            return confidence.tolist()

        except Exception:
            # Default to high confidence if calculation fails
            return [0.9] * len(ensemble_predictions)

    def _execute_batch_parallel(
        self, requests: List[Dict], context, optimization_level: str
    ) -> List[Dict]:
        """Execute batch predictions in parallel"""
        # For simplicity, implement sequential execution with optimization hints
        # In production, this would use ThreadPoolExecutor or similar
        return self._execute_batch_sequential(requests, context, optimization_level)

    def _execute_batch_sequential(
        self, requests: List[Dict], context, optimization_level: str
    ) -> List[Dict]:
        """Execute batch predictions sequentially"""
        results = []

        for req_data in requests:
            try:
                # Create prediction request
                pred_request = PredictionRequest(
                    request_id=req_data.get(
                        "request_id", f"batch_{int(time.time())}_{len(results)}"
                    ),
                    model_id=req_data["model_id"],
                    data=req_data["data"],
                    return_probabilities=req_data.get("return_probabilities", False),
                    batch_size=req_data.get("batch_size"),
                    priority=req_data.get("priority", 5),
                )

                # Execute prediction
                result = self._execute_prediction(pred_request, context)

                # Format result for batch response
                batch_result = {
                    "request_id": result.request_id,
                    "model_id": result.model_id,
                    "success": not result.error_message,
                    "predictions": (
                        result.predictions.tolist()
                        if hasattr(result.predictions, "tolist")
                        else result.predictions
                    ),
                    "probabilities": (
                        result.probabilities.tolist()
                        if result.probabilities is not None
                        and hasattr(result.probabilities, "tolist")
                        else result.probabilities
                    ),
                    "confidence_scores": result.confidence_scores,
                    "record_count": result.record_count,
                    "execution_time": result.execution_time_seconds,
                    "error_message": result.error_message,
                }

                results.append(batch_result)

            except Exception as e:
                # Add failed result
                results.append(
                    {
                        "request_id": req_data.get("request_id", "unknown"),
                        "model_id": req_data.get("model_id", "unknown"),
                        "success": False,
                        "error_message": str(e),
                        "record_count": 0,
                        "execution_time": 0,
                    }
                )

        return results

    def _find_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Find model info by ID or partial match"""
        # Try exact match first
        if model_id in self.model_info:
            return self.model_info[model_id]

        # Try partial match (for production models)
        for info in self.model_info.values():
            if model_id in info.model_id or info.model_id in model_id:
                return info

        return None

    def _update_prediction_metrics(
        self, result: PredictionResult, execution_time: float
    ) -> None:
        """Update prediction performance metrics"""
        self.metrics["predictions_executed"] += 1
        self.metrics["records_predicted"] += result.record_count

        # Update average prediction time
        current_avg = self.metrics["average_prediction_time"]
        total_predictions = self.metrics["predictions_executed"]
        self.metrics["average_prediction_time"] = (
            current_avg * (total_predictions - 1) + execution_time
        ) / total_predictions

        # Update model usage
        if result.model_id not in self.metrics["model_usage"]:
            self.metrics["model_usage"][result.model_id] = 0
        self.metrics["model_usage"][result.model_id] += 1

    def _get_model_performance_metrics(self, model_id: str) -> Dict:
        """Get performance metrics for specific model"""
        usage_count = self.metrics.get("model_usage", {}).get(model_id, 0)
        total_predictions = self.metrics.get("predictions_executed", 1)

        return {
            "usage_count": usage_count,
            "usage_percentage": (
                (usage_count / total_predictions * 100) if total_predictions > 0 else 0
            ),
            "last_used": datetime.utcnow().isoformat(),
            "average_records_per_request": self.metrics.get("records_predicted", 0)
            / max(usage_count, 1),
        }


# Agent registration function
def register_model_execution_agent():
    """Register the model execution agent with the system"""
    agent = ModelExecutionAgent()

    registration_details = {
        "agent_id": agent.agent_id,
        "agent_name": agent.agent_name,
        "class_name": "ModelExecutionAgent",
        "file_path": __file__,
        "created_by": "system_architect",
        "capabilities": [
            "execute_model_predictions",
            "ensemble_predictions",
            "batch_predict",
            "load_model",
            "get_model_info",
        ],
        "dependencies": [
            "enhanced_agent_framework",
            "security_manager",
            "scikit-learn",
            "numpy",
            "pandas",
        ],
        "max_execution_time": 600,  # 10 minutes
        "memory_limit_mb": 2048,
        "security_tier": 4,
        "permission_level": "READ_EXECUTE",
        "gpu_acceleration": True,
    }

    return agent, registration_details


# Example usage and testing
if __name__ == "__main__":
    # Create agent
    agent = ModelExecutionAgent()

    # Test model prediction (if models are available)
    test_data = [
        {
            "team_1_rank": 1,
            "team_2_rank": 5,
            "team_1_record": "10-0",
            "team_2_record": "8-2",
            "location": "home",
        },
        {
            "team_1_rank": 3,
            "team_2_rank": 7,
            "team_1_record": "9-1",
            "team_2_record": "7-3",
            "location": "away",
        },
    ]

    # Try to use a production model
    if agent.loaded_models:
        model_id = list(agent.loaded_models.keys())[0]
        result = agent.execute_action(
            "execute_model_predictions",
            {
                "model_id": model_id,
                "data": test_data,
                "prediction_config": {"return_probabilities": True},
            },
        )
        print("Model Prediction Result:")
        print(json.dumps(result, indent=2))
    else:
        print(
            "No production models loaded. Please ensure models are available in /app/models/production/"
        )
