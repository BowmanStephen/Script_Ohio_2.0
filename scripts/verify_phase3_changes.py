import re
from pathlib import Path

def verify_changes():
    base_path = Path(".")
    
    # 1. Verify Model Execution Engine
    engine_path = base_path / "agents/model_execution_engine.py"
    with open(engine_path, "r") as f:
        engine_content = f.read()
        
    if "model_name = parameters.get('model_type', 'xgb_home_win_model_2025')" in engine_content:
        print("✅ ModelExecutionEngine: Default model updated to XGBoost")
    else:
        print("❌ ModelExecutionEngine: Default model NOT updated")
        
    # 2. Verify Weekly Prediction Generation Agent
    agent_path = base_path / "agents/weekly_prediction_generation_agent.py"
    with open(agent_path, "r") as f:
        agent_content = f.read()
        
    # Check weights
    weights = {
        "ridge": 0.35,
        "xgboost": 0.50,
        "fastai": 0.15
    }
    
    for model, weight in weights.items():
        # Regex to find weight associated with model type/name
        # This is a bit loose, but should catch the specific lines we changed
        if model == "ridge":
            pattern = r"'prediction_type': 'margin',\s*'weight': 0.35"
        elif model == "xgboost":
            pattern = r"'prediction_type': 'probability',\s*'weight': 0.50"
        elif model == "fastai":
            pattern = r"'prediction_type': 'probability',\s*'weight': 0.15"
            
        if re.search(pattern, agent_content):
            print(f"✅ WeeklyPredictionGenerationAgent: {model} weight updated to {weight}")
        else:
            print(f"❌ WeeklyPredictionGenerationAgent: {model} weight NOT updated")

if __name__ == "__main__":
    verify_changes()
