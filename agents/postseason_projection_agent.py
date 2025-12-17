#!/usr/bin/env python3
"""
Postseason Projection Agent

Coordinates:
- Training data integration (Week 15 + completed postseason)
- Model retraining
- Postseason projection generation (for upcoming bowls)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel


class PostseasonProjectionAgent(BaseAgent):
    """Agent to run a single-command postseason pipeline."""

    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            name="Postseason Projection Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
        )

    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="run_postseason_pipeline",
                description="Integrate data, retrain models, and generate bowl projections",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=[],
                data_access=["data/", "model_pack/", "predictions/", "scripts/"],
                execution_time_estimate=60.0,
            )
        ]

    def _execute_action(
        self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        if action != "run_postseason_pipeline":
            raise ValueError(f"Unknown action: {action}")

        skip_fastai = bool(parameters.get("skip_fastai", False))
        allow_incomplete_new_rows = bool(parameters.get("allow_incomplete_new_rows", False))
        run_validation_agent = bool(parameters.get("run_validation_agent", False))

        def _load_script(module_name: str, rel_path: str):
            script_path = Path(__file__).resolve().parent.parent / rel_path
            spec = importlib.util.spec_from_file_location(module_name, str(script_path))
            if spec is None or spec.loader is None:
                raise ImportError(f"Unable to load {module_name} from {script_path}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)  # type: ignore[assignment]
            return module

        integrate_module = _load_script(
            "integrate_week15_postseason", "scripts/integrate_week15_postseason.py"
        )
        retrain_module = _load_script(
            "retrain_models_current", "scripts/retrain_models_current.py"
        )
        predict_module = _load_script("predict_postseason_2025", "scripts/predict_postseason_2025.py")

        integrate_result = integrate_module.integrate_week15_postseason(
            dry_run=False,
            allow_incomplete_new_rows=allow_incomplete_new_rows,
            run_validation_agent=run_validation_agent,
        )
        retrain_result = retrain_module.retrain_models_current(skip_fastai=skip_fastai)
        prediction_path = predict_module.predict_postseason_2025()

        return {
            "status": "success",
            "integrate": integrate_result.to_dict(),
            "retrain": retrain_result,
            "predictions_path": str(Path(prediction_path)),
        }
