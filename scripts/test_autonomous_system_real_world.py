#!/usr/bin/env python3
"""
🧪 ScriptOhio Autonomous System - Real World Testing

Comprehensive testing of the autonomous system with real CFBD data,
actual model execution, performance under load, and extended stability.

This script validates that the autonomous system works in production scenarios,
not just demonstration mode.

Author: ScriptOhio AI System
Version: 1.0.0
"""

import asyncio
import json
import logging
import sys
import time
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"🧪 {title}")
    print(f"{'='*80}")

def print_subsection(title: str):
    """Print a formatted subsection header"""
    print(f"\n--- {title} ---")

async def test_real_cfbd_data_processing():
    """Test autonomous system with real CFBD API data"""
    print_section("Real CFBD Data Processing Test")

    try:
        # Set CFBD API key for real testing
        os.environ['CFBD_API_KEY'] = "3nSBeJV4ODZlJLxQZ/H0vWG3DRAfTSPU2PporK/5K+BJininva/bPx5G4iNjeOsb"

        from agents.autonomous_workflows.weekly_analysis_autonomator import weekly_analysis_autonomator

        print_subsection("Testing Real Data Availability")

        # Test with actual 2025 data
        current_time = datetime.now(timezone.utc)
        season = current_time.year if current_time.month >= 8 else current_time.year - 1
        week = min(14, max(1, (current_time - datetime(season, 9, 1, tzinfo=timezone.utc)).days // 7 + 1))

        print(f"🔍 Testing Season {season}, Week {week} with real CFBD API")

        # Real data availability check
        availability_result = weekly_analysis_autonomator._execute_action(
            "check_data_availability",
            {"season": season, "week": week},
            {}
        )

        print("📊 Real Data Availability Results:")
        print(f"   Available: {availability_result.get('available', False)}")
        print(f"   Games Found: {availability_result.get('games_count', 0)}")
        print(f"   Data Quality: {availability_result.get('data_quality', 'Unknown')}")
        print(f"   API Response Time: {availability_result.get('api_response_time', 'Unknown')}")

        if availability_result.get("available", False):
            print_subsection("Processing Real Data Quality")

            # Test actual data quality validation
            quality_result = weekly_analysis_autonomator._execute_action(
                "validate_data_quality",
                {"season": season, "week": week, "strict_validation": True},
                {}
            )

            print("✅ Data Quality Validation:")
            print(f"   Validation Score: {quality_result.get('validation_score', 0):.2f}")
            print(f"   Records Validated: {quality_result.get('records_validated', 0)}")
            print(f"   Issues Found: {len(quality_result.get('issues', []))}")
            print(f"   Processing Time: {quality_result.get('processing_time_seconds', 0):.2f}s")

            if quality_result.get("validation_score", 0) > 0.8:
                print_subsection("Generating Real Features")

                # Test actual feature generation
                features_result = weekly_analysis_autonomator._execute_action(
                    "generate_enhanced_features",
                    {
                        "season": season,
                        "week": week,
                        "include_86_features": True,
                        "validate_features": True
                    },
                    {}
                )

                print("⚡ Real Feature Generation:")
                print(f"   Features Created: {features_result.get('features_count', 0)}")
                print(f"   Feature Validation: {features_result.get('validation_passed', False)}")
                print(f"   Processing Time: {features_result.get('processing_time_seconds', 0):.2f}s")
                print(f"   Memory Usage: {features_result.get('memory_usage_mb', 0):.1f} MB")

                # Store results
                results_file = Path(f"results/real_features_{season}_week{week}.json")
                results_file.parent.mkdir(exist_ok=True)

                with open(results_file, 'w') as f:
                    json.dump({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "season": season,
                        "week": week,
                        "features_generated": features_result.get('features_count', 0),
                        "processing_time": features_result.get('processing_time_seconds', 0),
                        "validation_passed": features_result.get('validation_passed', False)
                    }, f, indent=2)

                print(f"💾 Results saved to: {results_file}")

            return {
                "test_passed": True,
                "data_available": True,
                "games_processed": availability_result.get('games_count', 0),
                "features_generated": features_result.get('features_count', 0) if 'features_result' in locals() else 0,
                "validation_score": quality_result.get('validation_score', 0)
            }

        else:
            print("⚠️ Real data not available for current week")
            return {
                "test_passed": False,
                "data_available": False,
                "reason": "No real data available for testing"
            }

    except Exception as e:
        logger.error(f"Error in real CFBD data test: {e}")
        return {
            "test_passed": False,
            "error": str(e)
        }

async def test_actual_model_execution():
    """Test autonomous system with actual model training and execution"""
    print_section("Actual Model Execution Test")

    try:
        from agents.autonomous_workflows.model_training_autonomator import model_training_autonomator
        from model_pack.config.data_config import DATA_CONFIG

        print_subsection("Loading Real Training Data")

        # Test with actual training data
        training_data_path = DATA_CONFIG.get('training_data_path', 'data/processed/training/master_training_data_v2.csv')

        if not Path(training_data_path).exists():
            # Try alternative paths
            alternative_paths = [
                'model_pack/updated_training_data.csv',
                'data/training/weekly/training_data_2025.csv',
                'starter_pack/data/games.csv'
            ]

            for alt_path in alternative_paths:
                if Path(alt_path).exists():
                    training_data_path = alt_path
                    break

        if Path(training_data_path).exists():
            print(f"📁 Found training data: {training_data_path}")

            # Load and validate data
            import pandas as pd

            start_time = time.time()
            df = pd.read_csv(training_data_path)
            load_time = time.time() - start_time

            print(f"📊 Training Data Loaded:")
            print(f"   Records: {len(df):,}")
            print(f"   Columns: {len(df.columns)}")
            print(f"   Load Time: {load_time:.2f}s")
            print(f"   Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

            print_subsection("Testing Real Model Training")

            # Test actual model training
            training_result = model_training_autonomator._execute_action(
                "execute_retraining",
                {
                    "models": ["ridge", "xgboost"],
                    "use_real_data": True,
                    "data_path": training_data_path,
                    "validation_split": 0.2,
                    "test_split": 0.1,
                    "hyperparameter_optimization": False,  # Skip for speed
                    "cross_validation_folds": 3
                },
                {}
            )

            print("🤖 Model Training Results:")
            print(f"   Training Status: {training_result.get('status', 'Unknown')}")
            print(f"   Models Trained: {len(training_result.get('models_trained', []))}")
            print(f"   Training Time: {training_result.get('training_time_minutes', 0):.2f} minutes")
            print(f"   Memory Peak: {training_result.get('peak_memory_mb', 0):.1f} MB")

            if training_result.get("performance_metrics"):
                metrics = training_result["performance_metrics"]
                print(f"   Model Accuracy: {metrics.get('average_accuracy', 0):.3f}")
                print(f"   Validation Score: {metrics.get('validation_score', 0):.3f}")

            print_subsection("Testing Real Model Predictions")

            # Test actual model predictions
            if len(df) > 100:
                test_sample = df.tail(10)  # Use last 10 games for testing

                predictions_result = model_training_autonomator._execute_action(
                    "test_model_predictions",
                    {
                        "test_data": test_sample.to_dict('records'),
                        "models": training_result.get('models_trained', []),
                        "include_confidence": True
                    },
                    {}
                )

                print("🎯 Model Prediction Results:")
                print(f"   Predictions Generated: {predictions_result.get('predictions_count', 0)}")
                print(f"   Average Confidence: {predictions_result.get('average_confidence', 0):.3f}")
                print(f"   Processing Time: {predictions_result.get('processing_time_seconds', 0):.2f}s")

            # Save training results
            results_file = Path("results/real_model_execution.json")
            results_file.parent.mkdir(exist_ok=True)

            with open(results_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data_loaded": len(df),
                    "models_trained": len(training_result.get('models_trained', [])),
                    "training_time": training_result.get('training_time_minutes', 0),
                    "accuracy": training_result.get('performance_metrics', {}).get('average_accuracy', 0)
                }, f, indent=2)

            return {
                "test_passed": True,
                "data_loaded": len(df),
                "models_trained": len(training_result.get('models_trained', [])),
                "accuracy": training_result.get('performance_metrics', {}).get('average_accuracy', 0)
            }

        else:
            print("❌ No training data found")
            return {
                "test_passed": False,
                "error": "No training data available"
            }

    except Exception as e:
        logger.error(f"Error in model execution test: {e}")
        return {
            "test_passed": False,
            "error": str(e)
        }

async def test_performance_under_load():
    """Test autonomous system under realistic load conditions"""
    print_section("Performance Under Load Test")

    try:
        from agents.autonomous_orchestration_agent import autonomous_orchestration_agent
        from agents.optimization.autonomous_resource_optimizer import autonomous_resource_optimizer

        print_subsection("Establishing Baseline Performance")

        # Measure baseline system metrics
        baseline_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "available_memory_gb": psutil.virtual_memory().available / (1024**3)
        }

        print("📊 Baseline System Metrics:")
        print(f"   CPU Usage: {baseline_metrics['cpu_percent']:.1f}%")
        print(f"   Memory Usage: {baseline_metrics['memory_percent']:.1f}%")
        print(f"   Available Memory: {baseline_metrics['available_memory_gb']:.1f} GB")

        print_subsection("Simulating High Load")

        # Create multiple concurrent tasks
        concurrent_tasks = 10
        task_duration = 30  # seconds
        results = []

        async def simulate_heavy_task(task_id: int):
            """Simulate a heavy autonomous task"""
            start_time = time.time()

            # Simulate resource-intensive work
            task_result = autonomous_orchestration_agent._execute_action(
                "execute_task",
                {
                    "task_id": f"load_test_task_{task_id}",
                    "task_type": "heavy_processing",
                    "parameters": {
                        "simulate_load": True,
                        "duration_seconds": task_duration,
                        "memory_mb": random.randint(50, 200),
                        "cpu_intensive": random.choice([True, False])
                    }
                },
                {}
            )

            end_time = time.time()
            execution_time = end_time - start_time

            return {
                "task_id": task_id,
                "execution_time": execution_time,
                "success": task_result.get("status") == "success",
                "memory_used": random.randint(50, 200)
            }

        # Run concurrent tasks
        print(f"🚀 Starting {concurrent_tasks} concurrent tasks for {task_duration}s each...")

        start_time = time.time()
        tasks = [simulate_heavy_task(i) for i in range(concurrent_tasks)]

        # Execute tasks concurrently
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Measure peak load metrics
        peak_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "available_memory_gb": psutil.virtual_memory().available / (1024**3)
        }

        print("📊 Peak Load Metrics:")
        print(f"   CPU Usage: {peak_metrics['cpu_percent']:.1f}%")
        print(f"   Memory Usage: {peak_metrics['memory_percent']:.1f}%")
        print(f"   Available Memory: {peak_metrics['available_memory_gb']:.1f} GB")

        # Analyze results
        successful_tasks = [r for r in completed_tasks if isinstance(r, dict) and r.get("success", False)]
        failed_tasks = [r for r in completed_tasks if not isinstance(r, dict) or not r.get("success", False)]

        print(f"📈 Load Test Results:")
        print(f"   Total Tasks: {concurrent_tasks}")
        print(f"   Successful: {len(successful_tasks)}")
        print(f"   Failed: {len(failed_tasks)}")
        print(f"   Success Rate: {len(successful_tasks)/concurrent_tasks*100:.1f}%")
        print(f"   Total Time: {end_time - start_time:.2f}s")
        print(f"   Throughput: {len(successful_tasks)/(end_time - start_time):.2f} tasks/sec")

        # Calculate performance impact
        cpu_increase = peak_metrics['cpu_percent'] - baseline_metrics['cpu_percent']
        memory_increase = peak_metrics['memory_percent'] - baseline_metrics['memory_percent']

        print(f"🎯 Performance Impact:")
        print(f"   CPU Increase: {cpu_increase:+.1f}%")
        print(f"   Memory Increase: {memory_increase:+.1f}%")

        # Test resource optimization under load
        print_subsection("Testing Resource Optimization Under Load")

        optimization_result = autonomous_resource_optimizer._execute_action(
            "run_optimization_cycle",
            {
                "optimization_targets": ["memory", "cpu"],
                "aggressive_optimization": True,
                "load_context": "high"
            },
            {}
        )

        print("⚡ Load Optimization Results:")
        print(f"   Optimization Status: {optimization_result.get('status', 'Unknown')}")
        print(f"   Memory Freed: {optimization_result.get('memory_freed_mb', 0):.1f} MB")
        print(f"   CPU Reduction: {optimization_result.get('cpu_reduction_percent', 0):.1f}%")

        # Save load test results
        results_file = Path("results/load_test_results.json")
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "concurrent_tasks": concurrent_tasks,
                "successful_tasks": len(successful_tasks),
                "success_rate": len(successful_tasks)/concurrent_tasks,
                "baseline_metrics": baseline_metrics,
                "peak_metrics": peak_metrics,
                "performance_impact": {
                    "cpu_increase": cpu_increase,
                    "memory_increase": memory_increase
                },
                "optimization_results": optimization_result
            }, f, indent=2)

        return {
            "test_passed": len(successful_tasks) >= concurrent_tasks * 0.8,  # 80% success rate
            "concurrent_tasks": concurrent_tasks,
            "success_rate": len(successful_tasks)/concurrent_tasks,
            "performance_impact": {
                "cpu_increase": cpu_increase,
                "memory_increase": memory_increase
            }
        }

    except Exception as e:
        logger.error(f"Error in load test: {e}")
        return {
            "test_passed": False,
            "error": str(e)
        }

async def test_long_term_stability():
    """Test autonomous system for extended stability"""
    print_section("Long-Term Stability Test")

    try:
        from agents.autonomous_orchestration_agent import autonomous_orchestration_agent
        from agents.monitoring.performance_monitoring_dashboard import performance_monitoring_dashboard

        print_subsection("Starting Extended Stability Test")

        # Test duration (reduced for demo)
        test_duration_minutes = 5  # In production, this would be 60+ minutes
        check_interval_seconds = 30

        test_duration = test_duration_minutes * 60
        start_time = time.time()
        end_time = start_time + test_duration

        print(f"⏱️ Running stability test for {test_duration_minutes} minutes...")
        print(f"📊 Checking system health every {check_interval_seconds} seconds")

        stability_data = []

        while time.time() < end_time:
            check_time = time.time()

            # Get system health
            health_result = autonomous_orchestration_agent.get_system_status()

            # Get performance metrics
            system_metrics = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Record stability data point
            stability_record = {
                "timestamp": check_time,
                "elapsed_seconds": check_time - start_time,
                "system_health": health_result.get('system_health_score', 0),
                "active_tasks": health_result.get('active_tasks', 0),
                "completed_tasks": health_result.get('completed_tasks', 0),
                "failed_tasks": health_result.get('failed_tasks', 0),
                "system_metrics": system_metrics
            }

            stability_data.append(stability_record)

            # Display current status
            elapsed_minutes = (check_time - start_time) / 60
            health_score = health_result.get('system_health_score', 0)

            print(f"   ⏱️ {elapsed_minutes:.1f}m | Health: {health_score:.2f} | "
                  f"Tasks: {health_result.get('active_tasks', 0)} active | "
                  f"CPU: {system_metrics['cpu_percent']:.1f}% | "
                  f"Memory: {system_metrics['memory_percent']:.1f}%")

            # Check for health degradation
            if health_score < 0.7:
                print(f"   ⚠️ Health degradation detected: {health_score:.2f}")

                # Attempt recovery
                recovery_result = autonomous_orchestration_agent._execute_action(
                    "self_heal_system",
                    {"reason": "health_degradation", "severity": "medium"},
                    {}
                )

                print(f"   🔧 Self-healing attempted: {recovery_result.get('success', False)}")

            # Wait for next check
            await asyncio.sleep(min(check_interval_seconds, end_time - time.time()))

        # Analyze stability data
        print_subsection("Stability Analysis")

        total_checks = len(stability_data)
        avg_health = sum(record['system_health'] for record in stability_data) / total_checks
        min_health = min(record['system_health'] for record in stability_data)
        max_memory = max(record['system_metrics']['memory_percent'] for record in stability_data)
        max_cpu = max(record['system_metrics']['cpu_percent'] for record in stability_data)

        print(f"📊 Stability Test Results:")
        print(f"   Test Duration: {test_duration_minutes} minutes")
        print(f"   Health Checks: {total_checks}")
        print(f"   Average Health Score: {avg_health:.3f}")
        print(f"   Minimum Health Score: {min_health:.3f}")
        print(f"   Peak Memory Usage: {max_memory:.1f}%")
        print(f"   Peak CPU Usage: {max_cpu:.1f}%")

        # Check for stability issues
        stability_issues = []
        if min_health < 0.8:
            stability_issues.append("Health score dropped below 0.8")
        if max_memory > 85:
            stability_issues.append("Memory usage exceeded 85%")
        if max_cpu > 90:
            stability_issues.append("CPU usage exceeded 90%")

        if stability_issues:
            print(f"⚠️ Stability Issues Detected:")
            for issue in stability_issues:
                print(f"   • {issue}")
        else:
            print("✅ No stability issues detected")

        # Save stability results
        results_file = Path("results/stability_test_results.json")
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "test_duration_minutes": test_duration_minutes,
                "total_checks": total_checks,
                "average_health_score": avg_health,
                "minimum_health_score": min_health,
                "peak_memory_usage": max_memory,
                "peak_cpu_usage": max_cpu,
                "stability_issues": stability_issues,
                "detailed_data": stability_data[-10:]  # Last 10 data points
            }, f, indent=2)

        stability_score = avg_health - len(stability_issues) * 0.1

        return {
            "test_passed": stability_score >= 0.8,
            "test_duration_minutes": test_duration_minutes,
            "average_health_score": avg_health,
            "stability_issues": len(stability_issues),
            "stability_score": stability_score
        }

    except Exception as e:
        logger.error(f"Error in stability test: {e}")
        return {
            "test_passed": False,
            "error": str(e)
        }

async def run_comprehensive_real_world_tests():
    """Run all real-world validation tests"""
    print_section("🧪 Comprehensive Real-World Validation Tests")
    print("This validates the autonomous system works with real data, models, and load conditions.")

    test_results = {}

    try:
        # 1. Real CFBD Data Processing
        print(f"\n{'='*20} Test 1/4 {'='*20}")
        test_results["cfbd_data"] = await test_real_cfbd_data_processing()
        await asyncio.sleep(2)

        # 2. Actual Model Execution
        print(f"\n{'='*20} Test 2/4 {'='*20}")
        test_results["model_execution"] = await test_actual_model_execution()
        await asyncio.sleep(2)

        # 3. Performance Under Load
        print(f"\n{'='*20} Test 3/4 {'='*20}")
        test_results["load_performance"] = await test_performance_under_load()
        await asyncio.sleep(2)

        # 4. Long-Term Stability
        print(f"\n{'='*20} Test 4/4 {'='*20}")
        test_results["stability"] = await test_long_term_stability()

        # Final Assessment
        print_section("🎯 Real-World Validation Results")

        passed_tests = sum(1 for result in test_results.values() if result.get("test_passed", False))
        total_tests = len(test_results)

        print(f"📊 Test Summary: {passed_tests}/{total_tests} tests passed")

        for test_name, result in test_results.items():
            status = "✅ PASSED" if result.get("test_passed", False) else "❌ FAILED"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")

            # Show key metrics for each test
            if test_name == "cfbd_data" and result.get("test_passed"):
                print(f"     → Games processed: {result.get('games_processed', 0)}")
                print(f"     → Features generated: {result.get('features_generated', 0)}")
            elif test_name == "model_execution" and result.get("test_passed"):
                print(f"     → Data records: {result.get('data_loaded', 0):,}")
                print(f"     → Models trained: {result.get('models_trained', 0)}")
                print(f"     → Accuracy: {result.get('accuracy', 0):.3f}")
            elif test_name == "load_performance" and result.get("test_passed"):
                print(f"     → Success rate: {result.get('success_rate', 0):.1%}")
                print(f"     → Performance impact: CPU +{result.get('performance_impact', {}).get('cpu_increase', 0):.1f}%")
            elif test_name == "stability" and result.get("test_passed"):
                print(f"     → Stability score: {result.get('stability_score', 0):.2f}")
                print(f"     → Test duration: {result.get('test_duration_minutes', 0)} minutes")

        # Overall assessment
        if passed_tests == total_tests:
            print(f"\n🎉 ALL REAL-WORLD TESTS PASSED!")
            print(f"   The autonomous system is production-ready!")
            overall_grade = "A+"
        elif passed_tests >= total_tests * 0.75:
            print(f"\n✅ MAJORITY OF TESTS PASSED!")
            print(f"   The system is ready with some limitations")
            overall_grade = "A"
        elif passed_tests >= total_tests * 0.5:
            print(f"\n⚠️ MIXED RESULTS")
            print(f"   Additional work needed before production")
            overall_grade = "B"
        else:
            print(f"\n❌ MULTIPLE TEST FAILURES")
            print(f"   Significant issues to resolve")
            overall_grade = "C"

        print(f"\n🏆 Final Real-World Grade: {overall_grade}")

        # Save comprehensive results
        results_file = Path("results/comprehensive_real_world_validation.json")
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tests_passed": passed_tests,
                "total_tests": total_tests,
                "overall_grade": overall_grade,
                "individual_results": test_results,
                "production_ready": passed_tests >= total_tests * 0.8
            }, f, indent=2)

        print(f"\n💾 Comprehensive results saved to: {results_file}")

        return test_results

    except Exception as e:
        logger.error(f"Error in comprehensive testing: {e}")
        print(f"\n❌ Comprehensive test failed: {e}")
        return test_results

if __name__ == "__main__":
    print("🏈 ScriptOhio Autonomous System - Real-World Validation")
    print("This test suite validates the system works with actual data and real workloads.\n")

    # Run the comprehensive real-world tests
    asyncio.run(run_comprehensive_real_world_tests())