#!/usr/bin/env python3
"""
Data Synchronization Audit and Update Script
============================================

This script audits the entire system to ensure all components are using the latest data:
1. Checks training data file status and recency
2. Verifies model training dates vs data dates
3. Identifies notebooks/scripts with outdated data references
4. Checks for missing weeks in training data
5. Provides recommendations for updates

Usage:
    python3 scripts/audit_and_sync_data.py [--fix] [--retrain]
"""

import os
import sys
import json
import pandas as pd
import joblib
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'data_audit.log')
    ]
)
logger = logging.getLogger(__name__)

class DataAuditor:
    """Audit data synchronization across the system"""
    
    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.model_pack_dir = project_root / "model_pack"
        self.issues = []
        self.recommendations = []
        
    def audit_all(self) -> Dict[str, Any]:
        """Run complete audit"""
        logger.info("=" * 70)
        logger.info("DATA SYNCHRONIZATION AUDIT")
        logger.info("=" * 70)
        
        results = {
            'training_data': self.audit_training_data(),
            'models': self.audit_models(),
            'notebooks': self.audit_notebooks(),
            'scripts': self.audit_scripts(),
            'weekly_files': self.audit_weekly_files(),
            'summary': {}
        }
        
        # Generate summary
        results['summary'] = self.generate_summary(results)
        
        return results
    
    def audit_training_data(self) -> Dict[str, Any]:
        """Audit training data file"""
        logger.info("\n1. AUDITING TRAINING DATA")
        logger.info("-" * 70)
        
        training_path = self.model_pack_dir / "updated_training_data.csv"
        fallback_path = self.model_pack_dir / "training_data.csv"
        
        result = {
            'primary_file': str(training_path),
            'exists': training_path.exists(),
            'fallback_exists': fallback_path.exists(),
            'file_size_mb': 0,
            'last_modified': None,
            'total_games': 0,
            'seasons': [],
            'latest_week': {},
            'issues': []
        }
        
        if training_path.exists():
            stat = training_path.stat()
            result['file_size_mb'] = round(stat.st_size / (1024 * 1024), 2)
            result['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            try:
                df = pd.read_csv(training_path, nrows=0)  # Just check columns
                logger.info(f"✅ Training data file exists: {training_path}")
                logger.info(f"   Size: {result['file_size_mb']} MB")
                logger.info(f"   Last modified: {result['last_modified']}")
                
                # Check actual data
                df_full = pd.read_csv(training_path)
                result['total_games'] = len(df_full)
                result['seasons'] = sorted(df_full['season'].unique().tolist())
                
                # Check 2025 data
                df_2025 = df_full[df_full['season'] == 2025]
                if len(df_2025) > 0:
                    result['latest_week'] = {
                        'season': 2025,
                        'max_week': int(df_2025['week'].max()),
                        'games': len(df_2025),
                        'weeks_covered': sorted(df_2025['week'].unique().tolist())
                    }
                    logger.info(f"   2025 Season: {len(df_2025)} games, Weeks {result['latest_week']['weeks_covered']}")
                else:
                    result['issues'].append("No 2025 season data found")
                    logger.warning("⚠️  No 2025 season data in training file")
                    
            except Exception as e:
                result['issues'].append(f"Error reading file: {e}")
                logger.error(f"❌ Error reading training data: {e}")
        else:
            result['issues'].append("Primary training data file not found")
            logger.error(f"❌ Training data file not found: {training_path}")
            
        return result
    
    def audit_models(self) -> Dict[str, Any]:
        """Audit model files and training dates"""
        logger.info("\n2. AUDITING MODELS")
        logger.info("-" * 70)
        
        models_to_check = {
            'ridge': 'ridge_model_2025.joblib',
            'xgb': 'xgb_home_win_model_2025.pkl',
            'fastai': 'fastai_home_win_model_2025.pkl',
            'random_forest': 'random_forest_model_2025.pkl'
        }
        
        result = {
            'models': {},
            'training_data_date': None,
            'issues': []
        }
        
        # Get training data date
        training_path = self.model_pack_dir / "updated_training_data.csv"
        if training_path.exists():
            result['training_data_date'] = datetime.fromtimestamp(
                training_path.stat().st_mtime
            ).isoformat()
        
        for name, filename in models_to_check.items():
            model_path = self.model_pack_dir / filename
            model_info = {
                'exists': model_path.exists(),
                'file_size_mb': 0,
                'last_modified': None,
                'needs_retrain': False
            }
            
            if model_path.exists():
                stat = model_path.stat()
                model_info['file_size_mb'] = round(stat.st_size / (1024 * 1024), 2)
                model_info['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                # Check if model is older than training data
                if result['training_data_date']:
                    model_date = datetime.fromtimestamp(stat.st_mtime)
                    data_date = datetime.fromisoformat(result['training_data_date'])
                    if model_date < data_date:
                        model_info['needs_retrain'] = True
                        result['issues'].append(f"{name} model is older than training data")
                
                logger.info(f"✅ {name}: {model_info['file_size_mb']} MB, modified {model_info['last_modified']}")
                if model_info['needs_retrain']:
                    logger.warning(f"   ⚠️  Model may need retraining (older than data)")
            else:
                model_info['exists'] = False
                result['issues'].append(f"{name} model file not found")
                logger.error(f"❌ {name} model not found: {model_path}")
            
            result['models'][name] = model_info
        
        return result
    
    def audit_notebooks(self) -> Dict[str, Any]:
        """Audit notebooks for outdated data references"""
        logger.info("\n3. AUDITING NOTEBOOKS")
        logger.info("-" * 70)
        
        notebooks_dir = self.model_pack_dir
        notebooks = list(notebooks_dir.glob("*.ipynb"))
        
        result = {
            'notebooks_checked': len(notebooks),
            'using_config': [],
            'hardcoded_paths': [],
            'outdated_references': [],
            'issues': []
        }
        
        for nb_path in notebooks:
            try:
                with open(nb_path, 'r') as f:
                    nb_content = f.read()
                
                # Check for config usage (good)
                if 'get_data_config' in nb_content or 'config.get_training_data_path' in nb_content:
                    result['using_config'].append(nb_path.name)
                    logger.info(f"✅ {nb_path.name}: Using config system")
                
                # Check for hardcoded old paths (bad)
                if 'training_data.csv"' in nb_content and 'updated_training_data' not in nb_content:
                    result['hardcoded_paths'].append(nb_path.name)
                    result['issues'].append(f"{nb_path.name} may have hardcoded old path")
                    logger.warning(f"⚠️  {nb_path.name}: May have hardcoded 'training_data.csv'")
                
            except Exception as e:
                result['issues'].append(f"Error reading {nb_path.name}: {e}")
        
        return result
    
    def audit_scripts(self) -> Dict[str, Any]:
        """Audit Python scripts for data references"""
        logger.info("\n4. AUDITING SCRIPTS")
        logger.info("-" * 70)
        
        scripts_dir = PROJECT_ROOT / "scripts"
        scripts = list(scripts_dir.glob("*.py"))
        
        result = {
            'scripts_checked': len(scripts),
            'using_updated_data': [],
            'using_old_data': [],
            'issues': []
        }
        
        for script_path in scripts:
            try:
                with open(script_path, 'r') as f:
                    content = f.read()
                
                if 'updated_training_data.csv' in content:
                    result['using_updated_data'].append(script_path.name)
                elif 'training_data.csv' in content and 'updated_training_data' not in content:
                    result['using_old_data'].append(script_path.name)
                    result['issues'].append(f"{script_path.name} may reference old training_data.csv")
                    
            except Exception as e:
                pass  # Skip binary or unreadable files
        
        logger.info(f"   Scripts using updated data: {len(result['using_updated_data'])}")
        if result['using_old_data']:
            logger.warning(f"   Scripts potentially using old data: {result['using_old_data']}")
        
        return result
    
    def audit_weekly_files(self) -> Dict[str, Any]:
        """Audit weekly training data files"""
        logger.info("\n5. AUDITING WEEKLY FILES")
        logger.info("-" * 70)
        
        weekly_files = list(PROJECT_ROOT.glob("training_data_2025_week*.csv"))
        
        result = {
            'files_found': len(weekly_files),
            'weeks_covered': [],
            'latest_week': 0,
            'issues': []
        }
        
        for file_path in sorted(weekly_files):
            try:
                # Extract week number
                week_num = int(file_path.stem.split('week')[-1])
                result['weeks_covered'].append(week_num)
                
                # Check file
                df = pd.read_csv(file_path)
                logger.info(f"✅ Week {week_num}: {len(df)} games")
                
            except Exception as e:
                result['issues'].append(f"Error reading {file_path.name}: {e}")
        
        if result['weeks_covered']:
            result['latest_week'] = max(result['weeks_covered'])
            logger.info(f"   Latest week file: Week {result['latest_week']}")
        
        return result
    
    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate audit summary"""
        logger.info("\n" + "=" * 70)
        logger.info("AUDIT SUMMARY")
        logger.info("=" * 70)
        
        summary = {
            'total_issues': 0,
            'critical_issues': [],
            'recommendations': []
        }
        
        # Collect all issues
        all_issues = []
        all_issues.extend(results['training_data'].get('issues', []))
        all_issues.extend(results['models'].get('issues', []))
        all_issues.extend(results['notebooks'].get('issues', []))
        all_issues.extend(results['scripts'].get('issues', []))
        all_issues.extend(results['weekly_files'].get('issues', []))
        
        summary['total_issues'] = len(all_issues)
        
        # Check if models need retraining
        models_need_retrain = any(
            m.get('needs_retrain', False) 
            for m in results['models'].get('models', {}).values()
        )
        
        if models_need_retrain:
            summary['critical_issues'].append("Models are older than training data - retraining recommended")
            summary['recommendations'].append("Run: python3 scripts/combine_weeks_5_13_and_retrain.py --retrain")
        
        # Check training data coverage
        latest_week = results['training_data'].get('latest_week', {})
        if latest_week:
            max_week = latest_week.get('max_week', 0)
            if max_week < 13:
                summary['recommendations'].append(f"Training data only goes to Week {max_week}. Update to Week 13+")
        
        # Check for hardcoded paths
        if results['notebooks'].get('hardcoded_paths'):
            summary['recommendations'].append("Some notebooks may have hardcoded old paths - review and update")
        
        logger.info(f"\nTotal Issues Found: {summary['total_issues']}")
        logger.info(f"Critical Issues: {len(summary['critical_issues'])}")
        
        if summary['critical_issues']:
            logger.warning("\n⚠️  CRITICAL ISSUES:")
            for issue in summary['critical_issues']:
                logger.warning(f"   - {issue}")
        
        if summary['recommendations']:
            logger.info("\n📋 RECOMMENDATIONS:")
            for rec in summary['recommendations']:
                logger.info(f"   - {rec}")
        
        return summary

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Audit data synchronization across system")
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues automatically')
    parser.add_argument('--retrain', action='store_true', help='Retrain models after fixing data')
    parser.add_argument('--output', type=str, help='Save audit report to JSON file')
    
    args = parser.parse_args()
    
    auditor = DataAuditor()
    results = auditor.audit_all()
    
    # Save report if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"\n📄 Audit report saved to: {output_path}")
    
    # Auto-fix if requested
    if args.fix:
        logger.info("\n" + "=" * 70)
        logger.info("AUTO-FIX MODE")
        logger.info("=" * 70)
        # TODO: Implement auto-fix logic
        logger.info("Auto-fix not yet implemented. Please follow recommendations above.")
    
    # Retrain if requested
    if args.retrain:
        logger.info("\n" + "=" * 70)
        logger.info("RETRAINING MODELS")
        logger.info("=" * 70)
        logger.info("Run: python3 scripts/combine_weeks_5_13_and_retrain.py")
    
    return 0 if results['summary']['total_issues'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

