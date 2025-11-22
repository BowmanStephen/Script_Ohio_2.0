#!/usr/bin/env python3
"""
🔴 MASTER ADMIN SYSTEM AUDIT

Script Ohio 2.0 - Final System Verification

Purpose: Comprehensive system audit to ensure everything is ready for predictions
"""

import pandas as pd
import numpy as np
import os
import json
from pathlib import Path
from datetime import datetime
import sys
import subprocess

class SystemAuditor:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "sections": {},
            "overall_status": "UNKNOWN",
            "issues": [],
            "recommendations": []
        }
    
    def log(self, message, level="INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
            "DATA": "📊"
        }.get(level, "→ ")
        print(f"{prefix} [{timestamp}] {message}")

    def _load_model_file(self, full_path: Path):
        """Load a model file using the appropriate serialization helper."""
        name = full_path.name.lower()
        if "fastai" in name:
            try:
                from fastai.learner import load_learner
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise ImportError(
                    "fastai is required to audit the neural network model. "
                    "Install it with `pip install fastai`."
                ) from exc
            load_learner(full_path)
            return

        if full_path.suffix == ".joblib":
            import joblib
            joblib.load(full_path)
            return

        import pickle
        with open(full_path, 'rb') as f:
            pickle.load(f)
    
    def audit_data_files(self):
        """Audit data files"""
        print("\n" + "="*80)
        print("1️⃣  AUDITING DATA FILES")
        print("="*80)
        
        files_to_check = {
            "Training Data": "model_pack/updated_training_data.csv",
            "Migrated 2025 Data": "model_pack/2025_starter_pack_migrated.csv",
            "Talent Data": "model_pack/2025_talent.csv",
        }
        
        all_ok = True
        results = {}
        
        for name, rel_path in files_to_check.items():
            full_path = self.project_root / rel_path
            if full_path.exists():
                size_mb = full_path.stat().st_size / (1024 * 1024)
                self.log(f"{name}: ✅ ({size_mb:.2f} MB)", "SUCCESS")
                results[name] = {"exists": True, "size_mb": size_mb}
            else:
                self.log(f"{name}: ❌ MISSING", "ERROR")
                results[name] = {"exists": False}
                all_ok = False
                self.audit_results["issues"].append(f"Missing file: {rel_path}")
        
        self.audit_results["sections"]["1. DATA FILES"] = "✅ PASS" if all_ok else "❌ FAIL"
        return all_ok
    
    def audit_training_data(self):
        """Audit training data structure"""
        print("\n" + "="*80)
        print("2️⃣  AUDITING TRAINING DATA")
        print("="*80)
        
        training_file = self.project_root / "model_pack/updated_training_data.csv"
        
        if not training_file.exists():
            self.log("Training data not found", "ERROR")
            self.audit_results["sections"]["2. TRAINING DATA"] = "❌ FAIL"
            return False
        
        try:
            df = pd.read_csv(training_file, nrows=100)
            
            # Check structure
            expected_cols = 88
            actual_cols = len(df.columns)
            
            if actual_cols == expected_cols:
                self.log(f"Column count: ✅ {actual_cols} (expected {expected_cols})", "SUCCESS")
            else:
                self.log(f"Column count: ⚠️  {actual_cols} (expected {expected_cols})", "WARNING")
            
            # Check critical columns
            critical_cols = ['season', 'week', 'home_team', 'away_team', 'home_points', 'away_points',
                           'home_elo', 'away_elo', 'home_talent', 'away_talent', 'game_key', 'conference_game']
            
            missing_critical = [col for col in critical_cols if col not in df.columns]
            if len(missing_critical) == 0:
                self.log("Critical columns: ✅ All present", "SUCCESS")
            else:
                self.log(f"Critical columns: ❌ Missing {missing_critical}", "ERROR")
                self.audit_results["issues"].append(f"Missing critical columns: {missing_critical}")
            
            # Check 2025 data
            df_full = pd.read_csv(training_file)
            df_2025 = df_full[df_full['season'] == 2025]
            
            if len(df_2025) >= 600:
                self.log(f"2025 data: ✅ {len(df_2025)} games", "SUCCESS")
            else:
                self.log(f"2025 data: ⚠️  {len(df_2025)} games (expected 600+)", "WARNING")
            
            self.audit_results["sections"]["2. TRAINING DATA"] = "✅ PASS"
            return True
            
        except Exception as e:
            self.log(f"ERROR auditing training data: {e}", "ERROR")
            self.audit_results["sections"]["2. TRAINING DATA"] = "❌ FAIL"
            return False
    
    def audit_models(self):
        """Audit model files"""
        print("\n" + "="*80)
        print("3️⃣  AUDITING MODELS")
        print("="*80)
        
        models = {
            "Ridge Regression": "model_pack/ridge_model_2025.joblib",
            "XGBoost": "model_pack/xgb_home_win_model_2025.pkl",
            "FastAI": "model_pack/fastai_home_win_model_2025.pkl",
        }
        
        all_ok = True
        
        for name, rel_path in models.items():
            full_path = self.project_root / rel_path
            if full_path.exists():
                try:
                    self._load_model_file(full_path)
                    self.log(f"{name}: ✅ Loadable", "SUCCESS")
                except Exception as e:
                    self.log(f"{name}: ❌ Cannot load ({str(e)[:30]})", "ERROR")
                    all_ok = False
                    self.audit_results["issues"].append(f"Model '{name}' cannot be loaded")
            else:
                self.log(f"{name}: ❌ MISSING", "ERROR")
                all_ok = False
                self.audit_results["issues"].append(f"Model file missing: {rel_path}")
        
        self.audit_results["sections"]["3. MODELS"] = "✅ PASS" if all_ok else "❌ FAIL"
        return all_ok
    
    def audit_agents(self):
        """Audit agent system"""
        print("\n" + "="*80)
        print("4️⃣  AUDITING AGENTS")
        print("="*80)
        
        agent_files = [
            "agents/core/agent_framework.py",
            "agents/analytics_orchestrator.py",
            "agents/model_execution_engine.py",
        ]
        
        all_ok = True
        
        for rel_path in agent_files:
            full_path = self.project_root / rel_path
            if full_path.exists():
                self.log(f"{Path(rel_path).name}: ✅", "SUCCESS")
            else:
                self.log(f"{Path(rel_path).name}: ❌ MISSING", "ERROR")
                all_ok = False
        
        self.audit_results["sections"]["4. AGENTS"] = "✅ PASS" if all_ok else "❌ FAIL"
        return all_ok
    
    def audit_notebooks(self):
        """Audit notebooks"""
        print("\n" + "="*80)
        print("5️⃣  AUDITING NOTEBOOKS")
        print("="*80)
        
        model_pack_notebooks = [
            "model_pack/01_linear_regression_margin.ipynb",
            "model_pack/03_xgboost_win_probability.ipynb",
            "model_pack/04_fastai_win_probability.ipynb",
        ]
        
        all_ok = True
        found = 0
        
        for rel_path in model_pack_notebooks:
            full_path = self.project_root / rel_path
            if full_path.exists():
                found += 1
                self.log(f"{Path(rel_path).name}: ✅", "SUCCESS")
            else:
                self.log(f"{Path(rel_path).name}: ❌ MISSING", "ERROR")
        
        if found >= 2:
            self.log(f"Notebooks: ✅ {found}/{len(model_pack_notebooks)} found", "SUCCESS")
        else:
            all_ok = False
        
        self.audit_results["sections"]["5. NOTEBOOKS"] = "✅ PASS" if all_ok else "❌ FAIL"
        return all_ok
    
    def audit_dependencies(self):
        """Audit dependencies"""
        print("\n" + "="*80)
        print("6️⃣  AUDITING DEPENDENCIES")
        print("="*80)
        
        required_packages = ['pandas', 'numpy', 'sklearn', 'xgboost', 'joblib']
        optional_packages = ['fastai', 'shap']
        
        all_ok = True
        
        for pkg in required_packages:
            try:
                __import__(pkg)
                self.log(f"{pkg}: ✅", "SUCCESS")
            except ImportError:
                self.log(f"{pkg}: ❌ MISSING", "ERROR")
                all_ok = False
                self.audit_results["issues"].append(f"Required package missing: {pkg}")
        
        for pkg in optional_packages:
            try:
                __import__(pkg)
                self.log(f"{pkg}: ✅ (optional)", "SUCCESS")
            except ImportError:
                self.log(f"{pkg}: ⚠️  Not installed (optional)", "WARNING")
        
        self.audit_results["sections"]["6. DEPENDENCIES"] = "✅ PASS" if all_ok else "❌ FAIL"
        return all_ok
    
    def audit_config(self):
        """Audit configuration"""
        print("\n" + "="*80)
        print("7️⃣  AUDITING CONFIG")
        print("="*80)
        
        config_files = [
            "AGENTS.md",
            ".cursorrules",
        ]
        
        all_ok = True
        
        for rel_path in config_files:
            full_path = self.project_root / rel_path
            if full_path.exists():
                self.log(f"{rel_path}: ✅", "SUCCESS")
            else:
                self.log(f"{rel_path}: ⚠️  Not found (optional)", "WARNING")
        
        self.audit_results["sections"]["7. CONFIG"] = "✅ PASS"
        return True
    
    def audit_week12_critical(self):
        """Critical Week 12 audit"""
        print("\n" + "="*80)
        print("8️⃣  CRITICAL: WEEK 12 AUDIT")
        print("="*80)
        
        training_file = self.project_root / "model_pack/updated_training_data.csv"
        
        if not training_file.exists():
            self.log("Training data not found", "ERROR")
            self.audit_results["sections"]["8. WEEK 12"] = "❌ FAIL"
            return False
        
        try:
            df = pd.read_csv(training_file)
            df_week12 = df[(df['season'] == 2025) & (df['week'] == 12)]
            
            if len(df_week12) >= 45:
                self.log(f"Week 12 games: ✅ {len(df_week12)}", "SUCCESS")
            else:
                self.log(f"Week 12 games: ❌ {len(df_week12)} (expected 45+)", "ERROR")
                self.audit_results["issues"].append(f"Week 12 has only {len(df_week12)} games")
                self.audit_results["sections"]["8. WEEK 12"] = "❌ FAIL"
                return False
            
            # Ohio State vs UCLA
            osu_ucla = df_week12[
                ((df_week12['home_team'].str.contains('Ohio|OSU', case=False, na=False)) &
                 (df_week12['away_team'].str.contains('UCLA', case=False, na=False))) |
                ((df_week12['away_team'].str.contains('Ohio|OSU', case=False, na=False)) &
                 (df_week12['home_team'].str.contains('UCLA', case=False, na=False)))
            ]
            
            if len(osu_ucla) > 0:
                self.log("✅ Ohio State vs UCLA: FOUND", "SUCCESS")
                game = osu_ucla.iloc[0]
                self.log(f"   Game ID: {game.get('id', 'N/A')}", "INFO")
                self.log(f"   Date: {game.get('start_date', 'N/A')}", "INFO")
            else:
                self.log("❌ Ohio State vs UCLA: NOT FOUND", "ERROR")
                self.audit_results["issues"].append("Ohio State vs UCLA not found in Week 12")
                self.audit_results["sections"]["8. WEEK 12"] = "❌ FAIL"
                return False
            
            self.audit_results["sections"]["8. WEEK 12"] = "✅ PASS"
            return True
            
        except Exception as e:
            self.log(f"ERROR auditing Week 12: {e}", "ERROR")
            self.audit_results["sections"]["8. WEEK 12"] = "❌ FAIL"
            return False
    
    def run_full_audit(self):
        """Run complete system audit"""
        print("\n" + "="*80)
        print("🔴 MASTER ADMIN SYSTEM AUDIT")
        print("Script Ohio 2.0 - College Football Analytics")
        print("="*80)
        
        # Run all audits
        results = {
            "data_files": self.audit_data_files(),
            "training_data": self.audit_training_data(),
            "models": self.audit_models(),
            "agents": self.audit_agents(),
            "notebooks": self.audit_notebooks(),
            "dependencies": self.audit_dependencies(),
            "config": self.audit_config(),
            "week12": self.audit_week12_critical(),
        }
        
        # Calculate overall status
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        if passed == total:
            self.audit_results["overall_status"] = "OPERATIONAL"
        elif passed >= 6:
            self.audit_results["overall_status"] = "MOSTLY_OPERATIONAL"
        else:
            self.audit_results["overall_status"] = "ISSUES_DETECTED"
        
        # Save report
        report_file = self.project_root / "project_management" / "AUDIT_RESULTS.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        # Final summary
        print("\n" + "="*80)
        print("📊 AUDIT SUMMARY")
        print("="*80)
        print(f"\nResults: {passed}/{total} sections passed")
        
        for section, status in self.audit_results["sections"].items():
            print(f"  {status} {section}")
        
        if len(self.audit_results["issues"]) > 0:
            print(f"\n⚠️  Issues ({len(self.audit_results['issues'])}):")
            for issue in self.audit_results["issues"]:
                print(f"  • {issue}")
        
        print("\n" + "="*80)
        if self.audit_results["overall_status"] == "OPERATIONAL":
            print("🟢 SYSTEM STATUS: OPERATIONAL")
            print("\n✅ All systems optimal - READY FOR PREDICTIONS")
        elif self.audit_results["overall_status"] == "MOSTLY_OPERATIONAL":
            print("🟡 SYSTEM STATUS: MOSTLY OPERATIONAL")
            print(f"\n⚠️  {total - passed} section(s) need attention")
            print("✅ System functional with minor issues")
        else:
            print("🔴 SYSTEM STATUS: ISSUES DETECTED")
            print(f"\n❌ {total - passed} critical section(s) failed")
            print("⚠️  Requires attention before deployment")
        print("="*80)
        
        self.log(f"\n✅ Report saved: {report_file}", "SUCCESS")
        
        return self.audit_results


if __name__ == "__main__":
    # Get project root
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = Path(__file__).parent
    
    print(f"\n🔍 Using project root: {project_root}\n")
    
    auditor = SystemAuditor(project_root)
    results = auditor.run_full_audit()
    
    sys.exit(0 if results["overall_status"] == "OPERATIONAL" else 1)

