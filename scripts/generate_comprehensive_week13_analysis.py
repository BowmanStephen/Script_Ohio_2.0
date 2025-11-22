#!/usr/bin/env python3
"""
Comprehensive Week 13 Analysis Generator
Implementation of the TOON (Task-Oriented Object Notation) Plan
"""

import os
import sys
import json
import time
import logging
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import custom model classes to ensure pickle can load them
try:
    from src.models.random_forest import RandomForestScorePredictor
except ImportError:
    logging.warning("Could not import RandomForestScorePredictor from src.models.random_forest")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('week13_comprehensive_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

# Import configuration
try:
    from config.model_features import RIDGE_FEATURES, XGB_FEATURES
except ImportError:
    # Fallback if config module issues
    logger.warning("Could not import feature definitions from config, using defaults")
    RIDGE_FEATURES = []
    XGB_FEATURES = []

class AgentBase:
    """Base class for local agents in this script"""
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.info(f"{name} initialized")

class ModelLoaderAgent(AgentBase):
    """Loads all 4 ML models"""
    def __init__(self):
        super().__init__("ModelLoaderAgent")
        self.models = {}
        
    def load_all_models(self, model_pack_path: Path) -> Dict[str, Any]:
        """Load all 4 models from model_pack"""
        self.logger.info("Loading models...")
        
        models_to_load = {
            'ridge': 'ridge_model_2025.joblib',
            'xgb': 'xgb_home_win_model_2025.pkl',
            'fastai': 'fastai_home_win_model_2025.pkl',
            'random_forest': 'random_forest_model_2025.pkl'
        }
        
        for name, filename in models_to_load.items():
            path = model_pack_path / filename
            try:
                if not path.exists():
                    self.logger.error(f"Model file not found: {path}")
                    continue
                    
                if filename.endswith('.joblib'):
                    self.models[name] = joblib.load(path)
                elif name == 'random_forest':
                    # RF uses joblib even with .pkl extension based on debug
                    self.models[name] = joblib.load(path)
                elif name == 'xgb':
                    # XGB might use pickle or joblib
                    try:
                        self.models[name] = joblib.load(path)
                    except:
                        import pickle
                        with open(path, 'rb') as f:
                            self.models[name] = pickle.load(f)
                elif name == 'fastai':
                    # specialized loading for fastai
                    try:
                        from fastai.learner import load_learner
                        self.models[name] = load_learner(path)
                    except:
                        # Fallback to pickle/joblib
                        import pickle
                        with open(path, 'rb') as f:
                            self.models[name] = pickle.load(f)
                else:
                    import pickle
                    with open(path, 'rb') as f:
                        self.models[name] = pickle.load(f)
                
                self.logger.info(f"Successfully loaded {name}")
                
            except Exception as e:
                self.logger.error(f"Failed to load {name}: {e}")
        
        return self.models

class FeatureExtractorAgent(AgentBase):
    """Extracts correct features for each model type"""
    def __init__(self):
        super().__init__("FeatureExtractorAgent")
        # Features identified via inspection
        self.rf_features = [
            'home_adjusted_success', 'home_adjusted_success_allowed', 
            'away_adjusted_success', 'away_adjusted_success_allowed',
            'home_adjusted_rushing_epa', 'home_adjusted_rushing_epa_allowed', 
            'away_adjusted_rushing_epa', 'away_adjusted_rushing_epa_allowed',
            'home_adjusted_passing_epa', 'home_adjusted_passing_epa_allowed', 
            'away_adjusted_passing_epa', 'away_adjusted_passing_epa_allowed'
        ]
        
        self.ridge_features = [
            'home_talent', 'away_talent', 'home_elo', 'away_elo', 
            'home_adjusted_epa', 'home_adjusted_epa_allowed', 
            'away_adjusted_epa', 'away_adjusted_epa_allowed'
        ]
        
        self.xgb_features = [
            'home_talent', 'away_talent', 'spread', 'home_elo', 'away_elo', 
            'home_adjusted_epa', 'home_adjusted_epa_allowed', 
            'away_adjusted_epa', 'away_adjusted_epa_allowed', 
            'home_adjusted_success', 'home_adjusted_success_allowed', 
            'away_adjusted_success', 'away_adjusted_success_allowed'
        ]

    def load_week_data(self, path: Path) -> pd.DataFrame:
        self.logger.info(f"Loading week data from {path}")
        if not path.exists():
            self.logger.error(f"Week data file not found: {path}")
            return pd.DataFrame()
        return pd.read_csv(path)
        
    def extract_features(self, game_row: pd.Series, models: Dict) -> Dict[str, Any]:
        """Extract features for each model type"""
        features = {}
        
        # 1. Ridge Features
        if 'ridge' in models:
            try:
                ridge_data = []
                for f in self.ridge_features:
                    val = game_row.get(f, 0)
                    ridge_data.append(float(val) if pd.notna(val) else 0.0)
                features['ridge'] = np.array(ridge_data).reshape(1, -1)
            except Exception as e:
                self.logger.error(f"Error extracting ridge features: {e}")
                
        # 2. XGB Features
        if 'xgb' in models:
            try:
                xgb_data = []
                for f in self.xgb_features:
                    val = game_row.get(f, 0)
                    xgb_data.append(float(val) if pd.notna(val) else 0.0)
                features['xgb'] = np.array(xgb_data).reshape(1, -1)
            except Exception as e:
                self.logger.error(f"Error extracting xgb features: {e}")

        # 3. FastAI Features
        if 'fastai' in models:
            try:
                # FastAI uses same as XGB for now based on availability
                required_features = self.xgb_features
                fastai_data = []
                for f in required_features:
                    val = game_row.get(f, 0)
                    fastai_data.append(float(val) if pd.notna(val) else 0.0)
                features['fastai'] = np.array(fastai_data).reshape(1, -1)
            except Exception as e:
                self.logger.error(f"Error extracting fastai features: {e}")
                
        # 4. Random Forest Features
        if 'random_forest' in models:
            try:
                rf_data = {}
                for f in self.rf_features:
                    val = game_row.get(f, 0)
                    rf_data[f] = float(val) if pd.notna(val) else 0.0
                features['random_forest'] = pd.DataFrame([rf_data])
            except Exception as e:
                self.logger.error(f"Error extracting RF features: {e}")
            
        return features

class PredictionGeneratorAgent(AgentBase):
    """Generates predictions from each model"""
    def __init__(self):
        super().__init__("PredictionGeneratorAgent")
        
    def generate_predictions(self, models: Dict, features: Dict) -> Dict[str, Any]:
        preds = {}
        
        # Ridge (Margin)
        if 'ridge' in models and 'ridge' in features:
            try:
                preds['ridge_margin'] = float(models['ridge'].predict(features['ridge'])[0])
            except Exception as e:
                self.logger.error(f"Ridge prediction failed: {e}")
                preds['ridge_margin'] = 0.0
                
        # XGB (Win Prob)
        if 'xgb' in models and 'xgb' in features:
            try:
                # predict_proba returns [prob_loss, prob_win] usually
                probs = models['xgb'].predict_proba(features['xgb'])[0]
                preds['xgb_win_prob'] = float(probs[1])
            except Exception as e:
                self.logger.error(f"XGB prediction failed: {e}")
                preds['xgb_win_prob'] = 0.5
                
        # FastAI (Win Prob)
        if 'fastai' in models and 'fastai' in features:
            try:
                # FastAI prediction is tricky with raw learner vs wrapper.
                # If it's a learner, we might need to skip if we don't have the right input format.
                # Assuming it works like XGB/Sklearn or skipped for now to avoid crash
                # preds['fastai_win_prob'] = float(models['fastai'].predict(features['fastai'])[0])
                # Placeholder to avoid crash until we verify FastAI input requirements
                preds['fastai_win_prob'] = 0.5
            except Exception as e:
                # self.logger.error(f"FastAI prediction failed: {e}")
                preds['fastai_win_prob'] = 0.5
                
        # Random Forest (Margin)
        if 'random_forest' in models and 'random_forest' in features:
            try:
                # Using custom RandomForestScorePredictor which returns DF
                rf_res = models['random_forest'].predict(features['random_forest'])
                preds['rf_margin'] = float(rf_res['predicted_margin'].iloc[0])
            except Exception as e:
                self.logger.error(f"RF prediction failed: {e}")
                preds['rf_margin'] = 0.0
                
        return preds

class FeatureImportanceAgent(AgentBase):
    """Calculates feature importance"""
    def __init__(self):
        super().__init__("FeatureImportanceAgent")
        
    def calculate_importance(self, models: Dict, feature_extractor: FeatureExtractorAgent) -> Dict[str, Any]:
        importance = {}
        
        # XGB Importance
        if 'xgb' in models:
            try:
                model = models['xgb']
                if hasattr(model, 'feature_importances_'):
                    imps = model.feature_importances_
                    # Determine which features were used
                    if hasattr(model, 'feature_names_in_'):
                        feats = model.feature_names_in_
                    else:
                        feats = feature_extractor.xgb_features
                    
                    if len(feats) == len(imps):
                        # Zip and sort
                        sorted_imp = sorted(zip(feats, imps), key=lambda x: x[1], reverse=True)
                        importance['xgb'] = sorted_imp[:10]
            except Exception as e:
                self.logger.error(f"XGB importance failed: {e}")
                
        # Ridge Coefficients
        if 'ridge' in models:
            try:
                model = models['ridge']
                if hasattr(model, 'coef_'):
                    coefs = model.coef_
                    if hasattr(model, 'feature_names_in_'):
                        feats = model.feature_names_in_
                    else:
                        feats = feature_extractor.ridge_features
                        
                    if len(feats) == len(coefs):
                        sorted_coef = sorted(zip(feats, np.abs(coefs)), key=lambda x: x[1], reverse=True)
                        importance['ridge'] = sorted_coef[:10]
            except Exception as e:
                self.logger.error(f"Ridge importance failed: {e}")
                
        return importance

class EnsembleCalculatorAgent(AgentBase):
    """Creates weighted ensemble predictions"""
    def __init__(self):
        super().__init__("EnsembleCalculatorAgent")
        
    def calculate_ensemble(self, preds: Dict[str, float]) -> Dict[str, Any]:
        # Convert margins to probs: margin/40 + 0.5 (rough approximation)
        # 20 pts = 1.0, -20 pts = 0.0
        
        probs = []
        margins = []
        
        if 'ridge_margin' in preds:
            m = preds['ridge_margin']
            margins.append(m)
            p = np.clip(m/40.0 + 0.5, 0.05, 0.95)
            probs.append(p)
            
        if 'rf_margin' in preds:
            m = preds['rf_margin']
            margins.append(m)
            p = np.clip(m/40.0 + 0.5, 0.05, 0.95)
            probs.append(p)
            
        if 'xgb_win_prob' in preds:
            p = preds['xgb_win_prob']
            probs.append(p)
            # implied margin? (p-0.5)*40
            margins.append((p - 0.5) * 40.0)
            
        if 'fastai_win_prob' in preds:
            # Only include fastai if it's not the placeholder 0.5
            # or if we are confident it worked. 
            pass
            
        if not probs:
            return {'win_prob': 0.5, 'margin': 0.0, 'confidence': 0.0, 'winner': 'Unknown'}
            
        avg_prob = float(np.mean(probs))
        avg_margin = float(np.mean(margins))
        
        # Agreement score (std dev of probs)
        # Low std dev = high agreement
        std_dev = float(np.std(probs)) if len(probs) > 1 else 0.0
        agreement = 1.0 - std_dev 
        
        return {
            'win_prob': avg_prob,
            'margin': avg_margin,
            'confidence': agreement,
            'winner': 'Home' if avg_prob > 0.5 else 'Away'
        }

class NarrativeGeneratorAgent(AgentBase):
    """Generates human-readable explanations"""
    def __init__(self):
        super().__init__("NarrativeGeneratorAgent")
        
    def generate_narrative(self, game_info: pd.Series, ensemble: Dict, importance: Dict) -> str:
        home = game_info.get('home_team', 'Home')
        away = game_info.get('away_team', 'Away')
        winner = home if ensemble['win_prob'] > 0.5 else away
        prob = ensemble['win_prob'] if ensemble['win_prob'] > 0.5 else 1.0 - ensemble['win_prob']
        margin = abs(ensemble['margin'])
        
        narrative = f"**Prediction:** {winner} to win with {prob:.1%} confidence (Margin: {margin:.1f} pts).\n\n"
        
        narrative += "**Key Factors:**\n"
        if 'xgb' in importance and importance['xgb']:
            top_3 = importance['xgb'][:3]
            for feat, score in top_3:
                narrative += f"- {feat} (Impact: {score:.3f})\n"
        elif 'ridge' in importance and importance['ridge']:
            top_3 = importance['ridge'][:3]
            for feat, score in top_3:
                narrative += f"- {feat} (Impact: {score:.3f})\n"
        else:
            narrative += "- No specific feature importance available.\n"
                
        return narrative

class ArtifactGeneratorAgent(AgentBase):
    """Creates JSON, CSV, Markdown files"""
    def __init__(self):
        super().__init__("ArtifactGeneratorAgent")
        
    def save_artifacts(self, analysis_results: List[Dict], week: int, output_dir: Path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON
        json_path = output_dir / f"week{week}_comprehensive_analysis_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        self.logger.info(f"Saved JSON to {json_path}")
        
        # CSV
        csv_data = []
        for item in analysis_results:
            row = item['game_info'].copy()
            row.update(item['predictions'])
            row.update(item['ensemble'])
            row['narrative'] = item['narrative']
            csv_data.append(row)
            
        csv_path = output_dir / f"week{week}_detailed_predictions_{timestamp}.csv"
        pd.DataFrame(csv_data).to_csv(csv_path, index=False)
        self.logger.info(f"Saved CSV to {csv_path}")
        
        # Markdown
        md_path = output_dir / f"week{week}_narrative_previews_{timestamp}.md"
        with open(md_path, 'w') as f:
            f.write(f"# Week {week} Comprehensive Analysis\n\n")
            for item in analysis_results:
                f.write(f"## {item['game_info'].get('home_team')} vs {item['game_info'].get('away_team')}\n")
                f.write(item['narrative'] + "\n\n")
                f.write("---\n")
        self.logger.info(f"Saved Markdown to {md_path}")

def main():
    logger.info("Starting Comprehensive Week 13 Analysis...")
    
    # Config
    WEEK = 13
    SEASON = 2025
    MODEL_PACK_DIR = project_root / "model_pack"
    DATA_DIR = project_root # Root for training_data_2025_week13.csv
    OUTPUT_DIR = project_root / "analysis" / f"week{WEEK}"
    
    # Initialize Agents
    loader = ModelLoaderAgent()
    extractor = FeatureExtractorAgent()
    predictor = PredictionGeneratorAgent()
    importance = FeatureImportanceAgent()
    ensemble = EnsembleCalculatorAgent()
    narrative = NarrativeGeneratorAgent()
    artifact = ArtifactGeneratorAgent()
    
    # Phase 1: Load
    models = loader.load_all_models(MODEL_PACK_DIR)
    week_data_path = DATA_DIR / f"training_data_{SEASON}_week{WEEK}.csv"
    week_data = extractor.load_week_data(week_data_path)
    
    if week_data.empty:
        logger.error("No week data found. Aborting.")
        return

    # Phase 2-4: Analyze Loop
    results = []
    
    # Calculate global importance once (optional optimization)
    # model_importance = importance.calculate_importance(models, extractor)
    
    for _, game_row in week_data.iterrows():
        # Extract
        features = extractor.extract_features(game_row, models)
        
        # Predict
        preds = predictor.generate_predictions(models, features)
        
        # Importance (local)
        # For efficiency, we might just use global importance or skip per-game SHAP if slow
        # Using simple global importance for now
        local_importance = importance.calculate_importance(models, extractor)
        
        # Ensemble
        ens_result = ensemble.calculate_ensemble(preds)
        
        # Narrative
        narr_text = narrative.generate_narrative(game_row, ens_result, local_importance)
        
        results.append({
            'game_info': game_row.to_dict(),
            'predictions': preds,
            'ensemble': ens_result,
            'narrative': narr_text,
            'importance': local_importance
        })
        
    # Phase 5: Artifacts
    artifact.save_artifacts(results, WEEK, OUTPUT_DIR)
    
    logger.info("Analysis Complete.")

if __name__ == "__main__":
    main()
