#!/usr/bin/env python3
"""
Automated Model Retraining Pipeline

Orchestrates the complete model retraining workflow:
1. Fetch latest data
2. Calculate features
3. Train all models
4. Validate performance
5. Archive old models
6. Update model registry

Supports scheduling (weekly/monthly) and notifications.

Author: Model Pack Improvement Plan
Created: 2025-11-19
"""

import argparse
import logging
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_retraining.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AutomatedRetrainingPipeline:
    """Automated pipeline for model retraining"""
    
    def __init__(self, archive_old_models: bool = True, skip_data_acquisition: bool = False):
        """
        Initialize the retraining pipeline.
        
        Args:
            archive_old_models: If True, archive old models before training
            skip_data_acquisition: If True, skip data acquisition step
        """
        self.archive_old_models = archive_old_models
        self.skip_data_acquisition = skip_data_acquisition
        self.model_pack_dir = Path(__file__).parent.parent
        self.archive_dir = self.model_pack_dir / "archived_models" / datetime.now().strftime("%Y%m%d")
        self.results = {
            'start_time': datetime.now().isoformat(),
            'steps_completed': [],
            'steps_failed': [],
            'models_trained': [],
            'performance_metrics': {},
            'errors': []
        }
        
        # Import configuration
        try:
            from model_pack.config.data_config import get_data_config
            self.config = get_data_config()
            self.current_season = self.config.get_season()
        except ImportError:
            logger.error("Could not import configuration system")
            raise
    
    def archive_existing_models(self):
        """Archive existing models before retraining"""
        if not self.archive_old_models:
            logger.info("Skipping model archiving (disabled)")
            return
        
        logger.info("Archiving existing models...")
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        model_files = [
            f'ridge_model_{self.current_season}.joblib',
            f'xgb_home_win_model_{self.current_season}.pkl',
            f'fastai_home_win_model_{self.current_season}.pkl',
        ]
        
        archived_count = 0
        for model_file in model_files:
            model_path = self.model_pack_dir / model_file
            if model_path.exists():
                archive_path = self.archive_dir / model_file
                shutil.copy2(model_path, archive_path)
                logger.info(f"Archived {model_file} to {archive_path}")
                archived_count += 1
        
        logger.info(f"Archived {archived_count} model files")
        self.results['steps_completed'].append('archive_models')
    
    def fetch_latest_data(self):
        """Fetch latest data from CFBD API"""
        if self.skip_data_acquisition:
            logger.info("Skipping data acquisition (disabled)")
            self.results['steps_completed'].append('data_acquisition_skipped')
            return
        
        logger.info("Fetching latest data...")
        try:
            from model_pack.data_acquisition_agent import UnifiedDataAcquisitionAgent
            
            agent = UnifiedDataAcquisitionAgent()
            success = agent.run_complete_acquisition()
            
            if success:
                logger.info("Data acquisition completed successfully")
                self.results['steps_completed'].append('data_acquisition')
            else:
                logger.error("Data acquisition failed")
                self.results['steps_failed'].append('data_acquisition')
                self.results['errors'].append("Data acquisition returned False")
        except Exception as e:
            logger.error(f"Data acquisition error: {e}")
            self.results['steps_failed'].append('data_acquisition')
            self.results['errors'].append(f"Data acquisition error: {str(e)}")
            raise
    
    def calculate_features(self):
        """Calculate advanced features"""
        logger.info("Calculating advanced features...")
        try:
            from model_pack.metrics_calculation_agent import MetricsCalculationAgent
            
            agent = MetricsCalculationAgent()
            agent.execute_complete_pipeline()
            
            logger.info("Feature calculation completed successfully")
            self.results['steps_completed'].append('feature_calculation')
        except Exception as e:
            logger.error(f"Feature calculation error: {e}")
            self.results['steps_failed'].append('feature_calculation')
            self.results['errors'].append(f"Feature calculation error: {str(e)}")
            raise
    
    def train_models(self):
        """Train all ML models"""
        logger.info("Training all models...")
        try:
            from model_pack.model_training_agent import ModelTrainingAgent
            
            agent = ModelTrainingAgent()
            agent.run_complete_training_pipeline()
            
            # Extract performance metrics
            self.results['performance_metrics'] = agent.performance_metrics
            self.results['models_trained'] = list(agent.models.keys())
            
            logger.info("Model training completed successfully")
            self.results['steps_completed'].append('model_training')
        except Exception as e:
            logger.error(f"Model training error: {e}")
            self.results['steps_failed'].append('model_training')
            self.results['errors'].append(f"Model training error: {str(e)}")
            raise
    
    def validate_performance(self):
        """Validate model performance against thresholds"""
        logger.info("Validating model performance...")
        
        thresholds = {
            'ridge': {'mae_max': 15.0, 'r2_min': 0.3},
            'xgboost': {'accuracy_min': 0.55, 'auc_min': 0.6},
            'fastai': {'accuracy_min': 0.55, 'auc_min': 0.6},
        }
        
        validation_results = {}
        all_passed = True
        
        for model_name, metrics in self.results['performance_metrics'].items():
            if model_name not in thresholds:
                continue
            
            threshold = thresholds[model_name]
            model_passed = True
            model_issues = []
            
            if model_name == 'ridge':
                if metrics.get('mae', float('inf')) > threshold['mae_max']:
                    model_passed = False
                    model_issues.append(f"MAE {metrics.get('mae', 0):.2f} > {threshold['mae_max']}")
                if metrics.get('r2', -1) < threshold['r2_min']:
                    model_passed = False
                    model_issues.append(f"R² {metrics.get('r2', 0):.3f} < {threshold['r2_min']}")
            else:
                if metrics.get('accuracy', 0) < threshold['accuracy_min']:
                    model_passed = False
                    model_issues.append(f"Accuracy {metrics.get('accuracy', 0):.3f} < {threshold['accuracy_min']}")
                if metrics.get('auc', 0) < threshold['auc_min']:
                    model_passed = False
                    model_issues.append(f"AUC {metrics.get('auc', 0):.3f} < {threshold['auc_min']}")
            
            validation_results[model_name] = {
                'passed': model_passed,
                'issues': model_issues
            }
            
            if not model_passed:
                all_passed = False
                logger.warning(f"{model_name} validation failed: {', '.join(model_issues)}")
            else:
                logger.info(f"{model_name} validation passed")
        
        self.results['validation_results'] = validation_results
        self.results['validation_passed'] = all_passed
        
        if all_passed:
            self.results['steps_completed'].append('performance_validation')
        else:
            self.results['steps_failed'].append('performance_validation')
        
        return all_passed
    
    def update_model_registry(self):
        """Update model registry with new model information"""
        logger.info("Updating model registry...")
        
        registry_path = self.model_pack_dir / "model_registry.json"
        
        registry_data = {
            'last_updated': datetime.now().isoformat(),
            'season': self.current_season,
            'models': {}
        }
        
        for model_name in self.results['models_trained']:
            metrics = self.results['performance_metrics'].get(model_name, {})
            registry_data['models'][model_name] = {
                'filename': f'{model_name}_model_{self.current_season}',
                'metrics': metrics,
                'trained_at': datetime.now().isoformat()
            }
        
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f, indent=2)
        
        logger.info(f"Model registry updated: {registry_path}")
        self.results['steps_completed'].append('registry_update')
    
    def send_notification(self, success: bool):
        """
        Send notification about retraining completion.
        
        Args:
            success: True if retraining succeeded, False otherwise
        """
        # Placeholder for notification system
        # Could integrate with email, Slack, etc.
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"Retraining pipeline {status}")
        
        if not success:
            logger.error(f"Errors encountered: {self.results['errors']}")
    
    def run_pipeline(self) -> bool:
        """
        Execute the complete retraining pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info(f"STARTING AUTOMATED MODEL RETRAINING - {self.current_season}")
        logger.info("=" * 60)
        
        try:
            # Step 1: Archive old models
            if self.archive_old_models:
                self.archive_existing_models()
            
            # Step 2: Fetch latest data
            if not self.skip_data_acquisition:
                self.fetch_latest_data()
            
            # Step 3: Calculate features
            self.calculate_features()
            
            # Step 4: Train models
            self.train_models()
            
            # Step 5: Validate performance
            validation_passed = self.validate_performance()
            
            # Step 6: Update registry
            self.update_model_registry()
            
            # Step 7: Send notification
            success = validation_passed and len(self.results['steps_failed']) == 0
            self.results['end_time'] = datetime.now().isoformat()
            self.results['success'] = success
            self.results['duration_seconds'] = (
                datetime.fromisoformat(self.results['end_time']) -
                datetime.fromisoformat(self.results['start_time'])
            ).total_seconds()
            
            self.send_notification(success)
            
            # Save results
            results_path = self.model_pack_dir / f"retraining_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            logger.info("=" * 60)
            logger.info(f"RETRAINING PIPELINE {'COMPLETED SUCCESSFULLY' if success else 'COMPLETED WITH ERRORS'}")
            logger.info("=" * 60)
            
            return success
            
        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}")
            self.results['end_time'] = datetime.now().isoformat()
            self.results['success'] = False
            self.results['errors'].append(f"Pipeline error: {str(e)}")
            self.send_notification(False)
            return False


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Automated Model Retraining Pipeline")
    parser.add_argument("--skip-acquisition", action="store_true",
                       help="Skip data acquisition step")
    parser.add_argument("--no-archive", action="store_true",
                       help="Don't archive old models")
    parser.add_argument("--schedule", choices=['weekly', 'monthly'],
                       help="Schedule for automated retraining (not implemented)")
    
    args = parser.parse_args()
    
    pipeline = AutomatedRetrainingPipeline(
        archive_old_models=not args.no_archive,
        skip_data_acquisition=args.skip_acquisition
    )
    
    success = pipeline.run_pipeline()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

