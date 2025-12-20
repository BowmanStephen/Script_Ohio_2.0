#!/usr/bin/env python3
"""
🧪 ScriptOhio System Capabilities Test

Honest assessment of what the autonomous system can actually do
with the existing codebase and available data.

Author: ScriptOhio AI System
Version: 1.0.0
"""

import json
import sys
import time
import os
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"🧪 {title}")
    print(f"{'='*70}")

def test_data_availability():
    """Test what data is actually available"""
    print_section("Data Availability Assessment")

    data_sources = [
        "data/processed/training/master_training_data_v2.csv",
        "model_pack/updated_training_data.csv",
        "data/training/weekly/training_data_2025.csv",
        "starter_pack/data/games.csv"
    ]

    available_data = {}

    for data_path in data_sources:
        if Path(data_path).exists():
            try:
                df = pd.read_csv(data_path)
                available_data[data_path] = {
                    "exists": True,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "size_mb": Path(data_path).stat().st_size / (1024*1024),
                    "sample_columns": list(df.columns)[:5]
                }
                print(f"✅ {data_path}")
                print(f"   Rows: {len(df):,}")
                print(f"   Columns: {len(df.columns)}")
                print(f"   Size: {Path(data_path).stat().st_size / (1024*1024):.1f} MB")
            except Exception as e:
                print(f"❌ {data_path} - Error reading: {e}")
                available_data[data_path] = {"exists": False, "error": str(e)}
        else:
            print(f"❌ {data_path} - Not found")
            available_data[data_path] = {"exists": False}

    return available_data

def test_cfbd_api():
    """Test CFBD API functionality"""
    print_section("CFBD API Test")

    try:
        # Set API key
        os.environ['CFBD_API_KEY'] = "3nSBeJV4ODZlJLxQZ/H0vWG3DRAfTSPU2PporK/5K+BJininva/bPx5G4iNjeOsb"

        from src.cfbd_client.unified_client import UnifiedCFBDClient

        client = UnifiedCFBDClient()

        print("🔗 Testing CFBD API Connection...")

        # Test basic API call
        try:
            games = client.get_games(year=2025, week=14)

            if games:
                print(f"✅ API Connection Successful")
                print(f"   Games Retrieved: {len(games)}")

                if len(games) > 0:
                    sample_game = games[0]
                    print(f"   Sample Game: {sample_game.get('home_team', 'N/A')} vs {sample_game.get('away_team', 'N/A')}")
                    print(f"   Season: {sample_game.get('season', 'N/A')}")
                    print(f"   Week: {sample_game.get('week', 'N/A')}")

                return {
                    "api_working": True,
                    "games_count": len(games),
                    "api_response_time": "success"
                }
            else:
                print("⚠️ API returned empty data")
                return {"api_working": True, "games_count": 0, "warning": "empty_data"}

        except Exception as e:
            print(f"❌ API Call Failed: {e}")
            return {"api_working": False, "error": str(e)}

    except ImportError as e:
        print(f"❌ CFBD Client Import Failed: {e}")
        return {"api_working": False, "error": f"Import failed: {e}"}

def test_model_availability():
    """Test what models are actually available"""
    print_section("Model Availability Test")

    model_paths = [
        "models/production/ridge_regression_2025_v2.joblib",
        "models/production/xgboost_classifier_2025_v2.pkl",
        "models/production/fastai_neural_net_2025_v2.pkl",
        "model_pack/ridge_model_2025.joblib",
        "model_pack/xgb_home_win_model_2025.pkl",
        "model_pack/fastai_home_win_model_2025.pkl"
    ]

    available_models = {}

    for model_path in model_paths:
        if Path(model_path).exists():
            try:
                size_mb = Path(model_path).stat().st_size / (1024*1024)
                available_models[model_path] = {
                    "exists": True,
                    "size_mb": size_mb
                }
                print(f"✅ {model_path} ({size_mb:.1f} MB)")
            except Exception as e:
                print(f"❌ {model_path} - Error: {e}")
                available_models[model_path] = {"exists": False, "error": str(e)}
        else:
            print(f"❌ {model_path} - Not found")
            available_models[model_path] = {"exists": False}

    return available_models

def test_autonomous_components():
    """Test autonomous system components"""
    print_section("Autonomous Components Test")

    components = {}

    # Test orchestration agent
    try:
        from agents.autonomous_orchestration_agent import autonomous_orchestration_agent
        status = autonomous_orchestration_agent.get_system_status()

        print("✅ Autonomous Orchestration Agent")
        print(f"   Health Score: {status.get('system_health_score', 0):.2f}")
        print(f"   Autonomy Level: {status.get('autonomy_level', 'Unknown')}")

        components["orchestration_agent"] = {
            "available": True,
            "health_score": status.get('system_health_score', 0),
            "autonomy_level": status.get('autonomy_level', 'unknown')
        }

    except Exception as e:
        print(f"❌ Orchestration Agent: {e}")
        components["orchestration_agent"] = {"available": False, "error": str(e)}

    # Test weekly analysis autonomator
    try:
        from agents.autonomous_workflows.weekly_analysis_autonomator import weekly_analysis_autonomator
        analysis_status = weekly_analysis_autonomator.get_analysis_status()

        print("✅ Weekly Analysis Autonomator")
        print(f"   Agent ID: {analysis_status.get('agent_id', 'N/A')}")
        print(f"   Analysis State: {analysis_status.get('analysis_state', 'Unknown')}")

        components["weekly_analysis_autonomator"] = {
            "available": True,
            "analysis_state": analysis_status.get('analysis_state', 'unknown')
        }

    except Exception as e:
        print(f"❌ Weekly Analysis Autonomator: {e}")
        components["weekly_analysis_autonomator"] = {"available": False, "error": str(e)}

    # Test model training autonomator
    try:
        from agents.autonomous_workflows.model_training_autonomator import model_training_autonomator
        training_status = model_training_autonomator.get_training_status()

        print("✅ Model Training Autonomator")
        print(f"   Agent ID: {training_status.get('agent_id', 'N/A')}")
        print(f"   Training State: {training_status.get('training_state', 'Unknown')}")

        components["model_training_autonomator"] = {
            "available": True,
            "training_state": training_status.get('training_state', 'unknown')
        }

    except Exception as e:
        print(f"❌ Model Training Autonomator: {e}")
        components["model_training_autonomator"] = {"available": False, "error": str(e)}

    return components

def test_actual_workflows():
    """Test actual workflow execution"""
    print_section("Actual Workflow Test")

    workflow_results = {}

    # Test data validation workflow
    try:
        from agents.autonomous_workflows.weekly_analysis_autonomator import weekly_analysis_autonomator

        print("🔄 Testing Data Validation Workflow...")

        result = weekly_analysis_autonomator._execute_action(
            "check_data_availability",
            {"season": 2025, "week": 14},
            {}
        )

        print("✅ Data Validation Workflow")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   Games Found: {result.get('games_count', 0)}")
        print(f"   Available: {result.get('available', False)}")

        workflow_results["data_validation"] = {
            "executed": True,
            "success": result.get('status') == 'success',
            "games_found": result.get('games_count', 0)
        }

    except Exception as e:
        print(f"❌ Data Validation Workflow: {e}")
        workflow_results["data_validation"] = {"executed": False, "error": str(e)}

    # Test resource optimization workflow
    try:
        from agents.optimization.autonomous_resource_optimizer import autonomous_resource_optimizer

        print("🔄 Testing Resource Optimization Workflow...")

        result = autonomous_resource_optimizer._execute_action(
            "run_optimization_cycle",
            {},
            {}
        )

        print("✅ Resource Optimization Workflow")
        print(f"   Status: {result.get('status', 'Unknown')}")
        optimizations = result.get('optimizations', [])
        print(f"   Optimizations: {len(optimizations)}")

        workflow_results["resource_optimization"] = {
            "executed": True,
            "success": result.get('status') == 'success',
            "optimizations_count": len(optimizations)
        }

    except Exception as e:
        print(f"❌ Resource Optimization Workflow: {e}")
        workflow_results["resource_optimization"] = {"executed": False, "error": str(e)}

    return workflow_results

def generate_honest_assessment():
    """Generate honest assessment of system capabilities"""
    print_section("🎯 Honest System Assessment")

    # Run all tests
    data_results = test_data_availability()
    cfbd_results = test_cfbd_api()
    model_results = test_model_availability()
    component_results = test_autonomous_components()
    workflow_results = test_actual_workflows()

    # Calculate capability scores
    capabilities = {
        "data_infrastructure": 0,
        "api_connectivity": 0,
        "model_availability": 0,
        "autonomous_framework": 0,
        "workflow_execution": 0
    }

    # Data infrastructure score
    data_available = sum(1 for d in data_results.values() if d.get("exists", False))
    capabilities["data_infrastructure"] = (data_available / len(data_results)) * 100

    # API connectivity score
    if cfbd_results.get("api_working"):
        capabilities["api_connectivity"] = 100 if cfbd_results.get("games_count", 0) > 0 else 50
    else:
        capabilities["api_connectivity"] = 0

    # Model availability score
    models_available = sum(1 for m in model_results.values() if m.get("exists", False))
    capabilities["model_availability"] = (models_available / len(model_results)) * 100

    # Autonomous framework score
    components_available = sum(1 for c in component_results.values() if c.get("available", False))
    capabilities["autonomous_framework"] = (components_available / len(component_results)) * 100

    # Workflow execution score
    workflows_executed = sum(1 for w in workflow_results.values() if w.get("executed", False))
    workflows_successful = sum(1 for w in workflow_results.values() if w.get("success", False))

    if workflows_executed > 0:
        capabilities["workflow_execution"] = (workflows_successful / workflows_executed) * 100
    else:
        capabilities["workflow_execution"] = 0

    # Calculate overall score
    overall_score = sum(capabilities.values()) / len(capabilities)

    # Determine grade
    if overall_score >= 90:
        grade = "A"
        assessment = "Excellent - System is production-ready"
    elif overall_score >= 80:
        grade = "B"
        assessment = "Good - System needs minor improvements"
    elif overall_score >= 70:
        grade = "C"
        assessment = "Fair - System needs significant work"
    else:
        grade = "D"
        assessment = "Poor - System needs major rework"

    print(f"📊 Capability Assessment:")
    print(f"   Data Infrastructure: {capabilities['data_infrastructure']:.0f}%")
    print(f"   API Connectivity: {capabilities['api_connectivity']:.0f}%")
    print(f"   Model Availability: {capabilities['model_availability']:.0f}%")
    print(f"   Autonomous Framework: {capabilities['autonomous_framework']:.0f}%")
    print(f"   Workflow Execution: {capabilities['workflow_execution']:.0f}%")
    print(f"   Overall Score: {overall_score:.1f}%")
    print(f"   Grade: {grade}")
    print(f"   Assessment: {assessment}")

    # What's actually working
    print(f"\n✅ What's Actually Working:")

    if capabilities["autonomous_framework"] > 0:
        print(f"   • Autonomous framework components ({capabilities['autonomous_framework']:.0f}%)")

    if cfbd_results.get("api_working"):
        print(f"   • CFBD API connectivity")
        if cfbd_results.get("games_count", 0) > 0:
            print(f"   • Real game data access ({cfbd_results['games_count']} games)")

    if capabilities["workflow_execution"] > 0:
        print(f"   • Workflow execution ({capabilities['workflow_execution']:.0f}%)")

    if capabilities["data_infrastructure"] > 0:
        print(f"   • Training data infrastructure ({capabilities['data_infrastructure']:.0f}%)")

    # What needs work
    print(f"\n⚠️ What Needs Work:")

    if capabilities["workflow_execution"] < 50:
        print(f"   • Workflow execution (currently {capabilities['workflow_execution']:.0f}%)")

    if capabilities["model_availability"] < 50:
        print(f"   • Model availability (currently {capabilities['model_availability']:.0f}%)")

    if not cfbd_results.get("api_working"):
        print(f"   • API connectivity (currently broken)")

    # Save assessment results
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capabilities": capabilities,
        "overall_score": overall_score,
        "grade": grade,
        "assessment": assessment,
        "data_results": data_results,
        "cfbd_results": cfbd_results,
        "model_results": model_results,
        "component_results": component_results,
        "workflow_results": workflow_results
    }

    results_file = Path("results/honest_system_assessment.json")
    results_file.parent.mkdir(exist_ok=True)

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Detailed results saved to: {results_file}")

    return results

if __name__ == "__main__":
    print("🏈 ScriptOhio Honest System Capabilities Assessment")
    print("This provides an honest evaluation of what the system can actually do.\n")

    results = generate_honest_assessment()

    print(f"\n🎯 Bottom Line: {results['assessment']} (Grade: {results['grade']}, Score: {results['overall_score']:.1f}%)")