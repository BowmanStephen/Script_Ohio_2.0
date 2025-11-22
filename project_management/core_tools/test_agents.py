#!/usr/bin/env python3
"""
Simple Test of Agent System
This script performs a quick test of the agent system without requiring interactive input.
"""

import os
import sys
import time

# Add the agents/core directory to the path (go up to project root first)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up three levels to Script_Ohio_2.0 root
agents_core_path = os.path.join(project_root, 'agents', 'core')
if os.path.exists(agents_core_path):
    sys.path.insert(0, agents_core_path)
    print(f"✓ Added agents/core to path: {agents_core_path}")

# Add agents directory for other modules
agents_path = os.path.join(project_root, 'agents')
if os.path.exists(agents_path):
    sys.path.insert(0, agents_path)
    print(f"✓ Added agents to path: {agents_path}")

try:
    from context_manager import ContextManager, UserRole
    from agent_framework import AgentFactory, RequestRouter, AgentRequest, PermissionLevel
    from analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest
    print("✓ All agent modules imported successfully!")

    def test_context_manager():
        """Quick test of Context Manager"""
        print("\n🧠 Testing Context Manager...")
        cm = ContextManager()

        # Test role detection
        test_context = {
            'notebooks': ['starter_pack/01_intro_to_data.ipynb'],
            'models': [],
            'query_type': 'learn about college football data'
        }

        role = cm.detect_user_role(test_context)
        print(f"  ✓ Detected role: {role.value}")

        # Test context loading
        context = cm.load_context_for_role(role, test_context)
        print(f"  ✓ Context loaded with {len(context)} components")

        # Get performance metrics
        metrics = cm.get_performance_metrics()
        print(f"  ✓ Cache entries: {metrics.get('cache_entries', 0)}")

        return True

    def test_agent_framework():
        """Quick test of Agent Framework"""
        print("\n🤖 Testing Agent Framework...")

        factory = AgentFactory()
        print("  ✓ Agent Factory initialized")

        router = RequestRouter(factory)
        print("  ✓ Request Router initialized")

        # Test creating a basic request
        test_request = AgentRequest(
            request_id="test_001",
            agent_type="test",
            action="test_action",
            parameters={},
            user_context={"role": "analyst"},
            timestamp=time.time(),
            priority=2
        )
        print(f"  ✓ Created test request: {test_request.request_id}")

        return True

    def test_analytics_orchestrator():
        """Quick test of Analytics Orchestrator"""
        print("\n🎯 Testing Analytics Orchestrator...")

        try:
            orchestrator = AnalyticsOrchestrator()
            print("  ✓ Analytics Orchestrator initialized")

            # Get system status
            status = orchestrator.get_system_status()
            print(f"  ✓ System status: {status['orchestrator']['status']}")

            # Test processing a simple request
            request = AnalyticsRequest(
                user_id="test_user",
                query="Test query",
                query_type="test",
                parameters={},
                context_hints={},
                priority=2
            )

            response = orchestrator.process_analytics_request(request)
            print(f"  ✓ Request processed with status: {response.status}")

            return True

        except Exception as e:
            print(f"  ⚠️  Analytics Orchestrator test failed: {e}")
            return False

    # Run all tests
    print("🚀 Starting Agent System Tests")
    print("=" * 50)

    tests = [
        ("Context Manager", test_context_manager),
        ("Agent Framework", test_agent_framework),
        ("Analytics Orchestrator", test_analytics_orchestrator)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} failed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your agent system is working correctly!")
    else:
        print("⚠️  Some tests failed. Check the agent implementations.")

except ImportError as e:
    print(f"❌ Error importing agent modules: {e}")
    print(f"Project root: {project_root}")
    print(f"Agents core path: {agents_core_path}")
    print(f"Agents path: {agents_path}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)