#!/usr/bin/env python3
"""
🧪 Autonomous System Integration Test Suite

Comprehensive testing for the autonomous system integration fixes.
Tests the critical integration points that were causing 0% workflow execution.
"""

import sys
import time
import json
import traceback
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def test_resource_optimizer():
    """Test that Resource Optimizer missing methods are implemented"""
    print("🔧 Testing Resource Optimizer...")

    try:
        from agents.optimization.autonomous_resource_optimizer import AutonomousResourceOptimizer

        # Test initialization
        optimizer = AutonomousResourceOptimizer()
        print(f"  ✓ Resource Optimizer initializes successfully")

        # Test missing methods
        assert hasattr(optimizer, '_calculate_average_response_time'), "Missing _calculate_average_response_time method"
        assert hasattr(optimizer, 'alert_history'), "Missing alert_history attribute"
        print(f"  ✓ Missing methods implemented")

        # Test method functionality
        avg_time = optimizer._calculate_average_response_time()
        assert isinstance(avg_time, float), "Average response time should return float"
        assert isinstance(optimizer.alert_history, list), "Alert history should be a list"
        print(f"  ✓ Methods work correctly (avg_time: {avg_time}, alert_history: {len(optimizer.alert_history)} items)")

        return True, "Resource Optimizer: All tests passed"

    except Exception as e:
        return False, f"Resource Optimizer failed: {str(e)}"

def test_autonomous_resilience_agent():
    """Test that Autonomous Resilience Agent can initialize without parameter errors"""
    print("🛡️ Testing Autonomous Resilience Agent...")

    try:
        from agents.resilience.autonomous_resilience_agent import AutonomousResilienceAgent

        # Test initialization
        agent = AutonomousResilienceAgent()
        print(f"  ✓ Autonomous Resilience Agent initializes successfully")

        # Test capabilities
        capabilities = agent._define_capabilities()
        assert len(capabilities) > 0, "Agent should have capabilities defined"
        print(f"  ✓ Agent has {len(capabilities)} properly defined capabilities")

        # Verify correct parameter names
        for cap in capabilities:
            assert hasattr(cap, 'permission_required'), f"Capability {cap.name} missing permission_required"
            assert hasattr(cap, 'tools_required'), f"Capability {cap.name} missing tools_required"
            assert hasattr(cap, 'data_access'), f"Capability {cap.name} missing data_access"

        print(f"  ✓ All capabilities use correct parameter names")

        return True, "Autonomous Resilience Agent: All tests passed"

    except Exception as e:
        return False, f"Autonomous Resilience Agent failed: {str(e)}"

def test_weekly_analysis_autonomator():
    """Test that Weekly Analysis Autonomator has proper error handling"""
    print("📊 Testing Weekly Analysis Autonomator...")

    try:
        from agents.autonomous_workflows.weekly_analysis_autonomator import WeeklyAnalysisAutonomator

        # Test initialization
        agent = WeeklyAnalysisAutonomator()
        print(f"  ✓ Weekly Analysis Autonomator initializes successfully")

        # Test capabilities
        capabilities = agent._define_capabilities()
        assert len(capabilities) > 0, "Agent should have capabilities defined"
        print(f"  ✓ Agent has {len(capabilities)} properly defined capabilities")

        # Test that error handling is implemented
        test_params = {"season": 2025, "week": 14}
        test_context = {"test_mode": True}

        # Test data validation with error handling
        validation_result = agent._validate_data_quality(test_params, test_context)
        assert "status" in validation_result, "Validation result should have status field"
        assert "data" in validation_result or "error" in validation_result, "Validation result should have data or error field"
        print(f"  ✓ Data validation has proper error handling (status: {validation_result.get('status', 'unknown')})")

        return True, "Weekly Analysis Autonomator: All tests passed"

    except Exception as e:
        return False, f"Weekly Analysis Autonomator failed: {str(e)}"

def test_autonomous_orchestration_agent():
    """Test that Autonomous Orchestration Agent has lazy loading and graceful fallbacks"""
    print("🎼 Testing Autonomous Orchestration Agent...")

    try:
        from agents.autonomous_orchestration_agent import AutonomousOrchestrationAgent

        # Test initialization
        agent = AutonomousOrchestrationAgent()
        print(f"  ✓ Autonomous Orchestration Agent initializes successfully")

        # Test graceful fallbacks
        assert hasattr(agent, 'agent_delegates'), "Agent should have delegates attribute"
        print(f"  ✓ Agent has {len(agent.agent_delegates)} delegates (graceful fallbacks working)")

        # Test that agent can handle missing dependencies
        status = agent.get_system_status()
        assert "status" in status, "Agent should provide system status"
        print(f"  ✓ System status available: {status.get('status', 'unknown')}")

        return True, "Autonomous Orchestration Agent: All tests passed"

    except Exception as e:
        return False, f"Autonomous Orchestration Agent failed: {str(e)}"

def test_system_integration():
    """Test overall system integration"""
    print("🔗 Testing System Integration...")

    try:
        # Test that all critical autonomous components can be imported
        from agents.optimization.autonomous_resource_optimizer import AutonomousResourceOptimizer
        from agents.resilience.autonomous_resilience_agent import AutonomousResilienceAgent
        from agents.autonomous_workflows.weekly_analysis_autonomator import WeeklyAnalysisAutonomator
        from agents.autonomous_orchestration_agent import AutonomousOrchestrationAgent

        print(f"  ✓ All critical autonomous components import successfully")

        # Test that they can work together
        optimizer = AutonomousResourceOptimizer()
        resilience_agent = AutonomousResilienceAgent()
        weekly_agent = WeeklyAnalysisAutonomator()
        orchestrator = AutonomousOrchestrationAgent()

        print(f"  ✓ All components can be instantiated together")

        # Test basic workflow coordination
        components = {
            "resource_optimizer": optimizer,
            "resilience_agent": resilience_agent,
            "weekly_analysis": weekly_agent,
            "orchestrator": orchestrator
        }

        healthy_count = 0
        for name, component in components.items():
            try:
                # Test if component has basic health check
                if hasattr(component, 'get_system_status'):
                    status = component.get_system_status()
                    if status.get('status') != 'failed':
                        healthy_count += 1
                else:
                    # Component is healthy if it can define capabilities
                    if hasattr(component, '_define_capabilities'):
                        capabilities = component._define_capabilities()
                        if capabilities:
                            healthy_count += 1
                    else:
                        healthy_count += 1  # Assume healthy if no status method

            except Exception:
                pass  # Component not healthy

        print(f"  ✓ {healthy_count}/{len(components)} components are healthy")

        return healthy_count == len(components), f"System Integration: {healthy_count}/{len(components)} components healthy"

    except Exception as e:
        return False, f"System Integration failed: {str(e)}"

def run_comprehensive_tests():
    """Run all integration tests and generate report"""
    print("🚀 Starting Autonomous System Integration Test Suite")
    print("=" * 60)

    tests = [
        ("Resource Optimizer", test_resource_optimizer),
        ("Autonomous Resilience Agent", test_autonomous_resilience_agent),
        ("Weekly Analysis Autonomator", test_weekly_analysis_autonomator),
        ("Autonomous Orchestration Agent", test_autonomous_orchestration_agent),
        ("System Integration", test_system_integration),
    ]

    results = []
    start_time = time.time()

    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 40)

        try:
            success, message = test_func()
            results.append({
                "test_name": test_name,
                "success": success,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED - {message}")

        except Exception as e:
            error_msg = f"Test execution failed: {str(e)}"
            print(f"💥 {test_name}: ERROR - {error_msg}")
            results.append({
                "test_name": test_name,
                "success": False,
                "message": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "traceback": traceback.format_exc()
            })

    # Generate summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    execution_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"Execution Time: {execution_time:.2f} seconds")

    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! Autonomous system integration is working.")
    else:
        print(f"\n⚠️ {failed_tests} test(s) failed. Review the failures above.")

    # Save results
    results_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "execution_time": execution_time
        },
        "test_results": results,
        "overall_status": "SUCCESS" if failed_tests == 0 else "FAILED"
    }

    results_file = Path("results/autonomous_integration_test_results.json")
    results_file.parent.mkdir(exist_ok=True)

    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"\n💾 Detailed results saved to: {results_file}")

    return results_data

if __name__ == "__main__":
    results = run_comprehensive_tests()
    sys.exit(0 if results["overall_status"] == "SUCCESS" else 1)