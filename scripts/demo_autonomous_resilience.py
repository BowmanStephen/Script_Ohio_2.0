#!/usr/bin/env python3
"""
🛡️ ScriptOhio Autonomous Resilience System Demo

Demonstrates the circuit breaker patterns and intelligent error recovery
capabilities of the autonomous orchestration system.

Features:
- Circuit breaker protection for external services
- Intelligent error classification and recovery
- Emergency system recovery procedures
- Health monitoring and alerting
- Performance under failure conditions

Author: ScriptOhio AI System
Version: 1.0.0
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import random

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.resilience.autonomous_resilience_agent import autonomous_resilience_agent
from agents.resilience.autonomous_resilience_agent import CircuitState, ErrorCategory, ErrorSeverity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🛡️ {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Print a formatted subsection header"""
    print(f"\n--- {title} ---")


async def demo_circuit_breaker_protection():
    """Demo: Circuit breaker protection for external services"""
    print_section("Circuit Breaker Protection Demo")

    print_subsection("Testing normal operation")

    # Test successful call
    async def mock_successful_call():
        await asyncio.sleep(0.1)
        return {"status": "success", "data": "test_data"}

    try:
        result = await autonomous_resilience_agent._execute_action(
            "protect_call",
            {
                "service_name": "cfbd_api",
                "function": mock_successful_call,
                "args": []
            },
            {}
        )

        print("✅ Successful call protected by circuit breaker:")
        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print_subsection("Simulating service failures")

    # Mock failing function
    call_count = 0
    async def mock_failing_call():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)

        if call_count <= 3:
            raise Exception(f"Simulated API failure #{call_count}")
        else:
            return {"status": "recovered", "data": "recovered_data"}

    # Multiple calls to trigger circuit breaker
    for i in range(8):
        try:
            result = await autonomous_resilience_agent._execute_action(
                "protect_call",
                {
                    "service_name": "cfbd_api",
                    "function": mock_failing_call,
                    "args": []
                },
                {}
            )

            print(f"🔄 Call {i+1}: {result.get('status', 'unknown')}")

        except Exception as e:
            print(f"⚡ Call {i+1}: {str(e)[:50]}...")

        await asyncio.sleep(0.5)  # Brief delay between calls

    # Show circuit breaker status
    print_subsection("Circuit breaker status")
    for name, status in autonomous_resilience_agent.get_resilience_status()["circuit_breakers"].items():
        print(f"\n📊 {name}:")
        print(f"  State: {status['state']}")
        print(f"  Failures: {status['failure_count']}")
        print(f"  Successes: {status['success_count']}")
        print(f"  Total calls: {status['call_count']}")


async def demo_intelligent_error_classification():
    """Demo: Intelligent error classification and recovery"""
    print_section("Intelligent Error Classification Demo")

    # Test different error types
    error_scenarios = [
        {
            "name": "Network Timeout",
            "error": Exception("Connection timeout after 30 seconds"),
            "context": {"service": "cfbd_api", "critical_workflow": False}
        },
        {
            "name": "API Rate Limit",
            "error": Exception("HTTP 429: Too Many Requests"),
            "context": {"service": "cfbd_api", "recent_failures": 1}
        },
        {
            "name": "Data Corruption",
            "error": Exception("JSON decode error: Expecting ',' delimiter"),
            "context": {"service": "data_pipeline", "critical_workflow": True}
        },
        {
            "name": "Model Load Failure",
            "error": Exception("ModelLoadError: Could not load model file"),
            "context": {"service": "model_execution", "critical_workflow": True}
        },
        {
            "name": "Memory Exhaustion",
            "error": Exception("MemoryError: Unable to allocate array"),
            "context": {"service": "model_training", "critical_workflow": False}
        }
    ]

    for scenario in error_scenarios:
        print_subsection(f"Error: {scenario['name']}")

        result = await autonomous_resilience_agent._execute_action(
            "handle_error",
            {
                "error": scenario["error"],
                "context": scenario["context"],
                "attempt_recovery": True
            },
            {}
        )

        print(f"🔍 Classification:")
        print(f"  Category: {result['error_classification']['category']}")
        print(f"  Severity: {result['error_classification']['severity']}")
        print(f"  Error Type: {result['error_details']['type']}")

        if result.get("recovery_result"):
            recovery = result["recovery_result"]
            print(f"🔧 Recovery Attempt:")
            print(f"  Strategy: {recovery.get('strategy_used', 'N/A')}")
            print(f"  Success: {recovery.get('success', False)}")
            if recovery.get('success'):
                print(f"  Message: {recovery.get('message', 'N/A')}")
            else:
                print(f"  Error: {recovery.get('error', 'N/A')}")
                if recovery.get('fallback_available'):
                    print(f"  Fallback Available: ✅")
                if recovery.get('requires_intervention'):
                    print(f"  ⚠️ Requires Manual Intervention")

        await asyncio.sleep(1)  # Brief delay between scenarios


async def demo_system_health_monitoring():
    """Demo: Comprehensive system health monitoring"""
    print_section("System Health Monitoring Demo")

    print_subsection("Performing comprehensive health check")

    result = await autonomous_resilience_agent._execute_action(
        "monitor_system_health",
        {"comprehensive": True},
        {}
    )

    print("🏥 System Health Status:")
    print(f"  Overall Health: {result['health_status']}")
    print(f"  Timestamp: {result['timestamp']}")
    print(f"  Message: {result['message']}")

    print_subsection("Circuit Breaker Health")
    for name, status in result["circuit_breakers"].items():
        status_emoji = "🟢" if status["state"] == "closed" else "🔴" if status["state"] == "open" else "🟡"
        print(f"  {status_emoji} {name}: {status['state'].upper()}")

    print_subsection("System Resources")
    resources = result["system_resources"]
    if resources:
        cpu_emoji = "🟢" if resources.get("cpu_percent", 0) < 80 else "🟡" if resources.get("cpu_percent", 0) < 90 else "🔴"
        memory_emoji = "🟢" if resources.get("memory_percent", 0) < 80 else "🟡" if resources.get("memory_percent", 0) < 90 else "🔴"
        disk_emoji = "🟢" if resources.get("disk_percent", 0) < 90 else "🟡" if resources.get("disk_percent", 0) < 95 else "🔴"

        print(f"  {cpu_emoji} CPU: {resources.get('cpu_percent', 0):.1f}%")
        print(f"  {memory_emoji} Memory: {resources.get('memory_percent', 0):.1f}%")
        print(f"  {disk_emoji} Disk: {resources.get('disk_percent', 0):.1f}%")
        print(f"  💾 Available Memory: {resources.get('available_memory_gb', 0):.1f}GB")

    if result.get("issues"):
        print_subsection("Detected Issues")
        for issue in result["issues"]:
            print(f"  ⚠️ {issue}")

    if result.get("recommendations"):
        print_subsection("Recommendations")
        for rec in result["recommendations"]:
            print(f"  💡 {rec}")


async def demo_emergency_recovery():
    """Demo: Emergency system recovery procedures"""
    print_section("Emergency Recovery Demo")

    recovery_types = ["circuit_breakers", "resources", "memory", "full"]

    for recovery_type in recovery_types:
        print_subsection(f"Emergency Recovery: {recovery_type.upper()}")

        result = await autonomous_resilience_agent._execute_action(
            "emergency_recovery",
            {"recovery_type": recovery_type},
            {}
        )

        print(f"🚨 Recovery Status: {result['status']}")
        print(f"📝 Recovery Type: {result['recovery_type']}")

        if result.get("actions_taken"):
            print("🔧 Actions Taken:")
            for action in result["actions_taken"]:
                print(f"  ✓ {action}")

        print(f"💬 Message: {result['message']}")
        print(f"⏰ Timestamp: {result['timestamp']}")

        await asyncio.sleep(1)  # Brief delay between recovery types


async def demo_stress_testing():
    """Demo: Stress testing the resilience system"""
    print_section("Resilience System Stress Testing")

    print_subsection("Simulating high error rate conditions")

    # Simulate multiple concurrent errors
    error_tasks = []
    error_types = [
        Exception("Network timeout"),
        Exception("Rate limit exceeded"),
        Exception("Database connection failed"),
        Exception("File system permission denied"),
        Exception("Model prediction failed")
    ]

    start_time = time.time()

    # Create 20 concurrent error handling tasks
    for i in range(20):
        error = random.choice(error_types)
        task = autonomous_resilience_agent._execute_action(
            "handle_error",
            {
                "error": error,
                "context": {
                    "service": f"service_{i%5}",
                    "critical_workflow": i % 3 == 0,
                    "recent_failures": i
                },
                "attempt_recovery": True
            },
            {}
        )
        error_tasks.append(task)

    # Wait for all error handling to complete
    results = await asyncio.gather(*error_tasks, return_exceptions=True)

    end_time = time.time()
    duration = end_time - start_time

    print(f"⚡ Processed {len(results)} errors in {duration:.2f} seconds")
    print(f"📊 Average processing time: {duration/len(results)*1000:.1f}ms per error")

    # Analyze results
    successful_recoveries = sum(1 for r in results if isinstance(r, dict) and
                               r.get("recovery_result", {}).get("success", False))

    print(f"✅ Successful recoveries: {successful_recoveries}/{len(results)} ({successful_recoveries/len(results)*100:.1f}%)")

    # Show final error metrics
    status = autonomous_resilience_agent.get_resilience_status()
    print(f"\n📈 Final Error Metrics:")
    print(f"  Total Errors: {status['error_metrics']['total_errors']}")
    print(f"  Error Rate (24h): {status['error_metrics']['error_rate_24h']:.1%}")
    print(f"  Errors by Category: {status['error_metrics']['errors_by_category']}")
    print(f"  Errors by Severity: {status['error_metrics']['errors_by_severity']}")


async def demo_performance_under_load():
    """Demo: Performance testing under various load conditions"""
    print_section("Performance Under Load Demo")

    load_scenarios = [
        {"name": "Light Load", "concurrent_calls": 5, "success_rate": 0.9},
        {"name": "Medium Load", "concurrent_calls": 15, "success_rate": 0.7},
        {"name": "Heavy Load", "concurrent_calls": 30, "success_rate": 0.5}
    ]

    for scenario in load_scenarios:
        print_subsection(f"Testing {scenario['name']} ({scenario['concurrent_calls']} concurrent calls)")

        # Mock service with controlled success rate
        async def mock_service():
            await asyncio.sleep(0.1)
            if random.random() < scenario["success_rate"]:
                return {"status": "success", "data": f"data_{random.randint(1, 1000)}"}
            else:
                raise Exception("Random service failure for testing")

        # Create concurrent tasks
        tasks = []
        start_time = time.time()

        for i in range(scenario["concurrent_calls"]):
            task = autonomous_resilience_agent._execute_action(
                "protect_call",
                {
                    "service_name": "cfbd_api",
                    "function": mock_service,
                    "args": []
                },
                {}
            )
            tasks.append(task)

        # Wait for completion
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Analyze results
        successful_calls = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
        handled_errors = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "error_handled")
        total_time = end_time - start_time

        print(f"  📊 Results:")
        print(f"    Total calls: {scenario['concurrent_calls']}")
        print(f"    Successful: {successful_calls} ({successful_calls/scenario['concurrent_calls']*100:.1f}%)")
        print(f"    Error handled: {handled_errors} ({handled_errors/scenario['concurrent_calls']*100:.1f}%)")
        print(f"    Total time: {total_time:.2f}s")
        print(f"    Throughput: {scenario['concurrent_calls']/total_time:.1f} calls/sec")

        await asyncio.sleep(1)


async def interactive_resilience_menu():
    """Interactive resilience demo menu"""
    while True:
        print_section("🛡️ Autonomous Resilience System Demo Menu")
        print("Choose a demo to run:")
        print("1. Circuit Breaker Protection")
        print("2. Intelligent Error Classification")
        print("3. System Health Monitoring")
        print("4. Emergency Recovery Procedures")
        print("5. Stress Testing")
        print("6. Performance Under Load")
        print("7. Run All Demos")
        print("8. Show Resilience Status")
        print("0. Exit")

        choice = input("\nEnter your choice (0-8): ").strip()

        if choice == "0":
            print("\n👋 Exiting resilience demo...")
            break
        elif choice == "1":
            await demo_circuit_breaker_protection()
        elif choice == "2":
            await demo_intelligent_error_classification()
        elif choice == "3":
            await demo_system_health_monitoring()
        elif choice == "4":
            await demo_emergency_recovery()
        elif choice == "5":
            await demo_stress_testing()
        elif choice == "6":
            await demo_performance_under_load()
        elif choice == "7":
            await run_all_resilience_demos()
        elif choice == "8":
            show_resilience_status()
        else:
            print("\n❌ Invalid choice. Please enter a number between 0-8.")

        if choice != "0":
            input("\nPress Enter to continue...")


async def run_all_resilience_demos():
    """Run all resilience demonstration functions"""
    demos = [
        ("Circuit Breaker Protection", demo_circuit_breaker_protection),
        ("Intelligent Error Classification", demo_intelligent_error_classification),
        ("System Health Monitoring", demo_system_health_monitoring),
        ("Emergency Recovery", demo_emergency_recovery),
        ("Stress Testing", demo_stress_testing),
        ("Performance Under Load", demo_performance_under_load)
    ]

    for name, demo_func in demos:
        try:
            await demo_func()
            await asyncio.sleep(2)  # Brief pause between demos
        except Exception as e:
            logger.error(f"Error in {name} demo: {e}")
            continue

    print_section("Resilience Demo Complete")
    print("🎉 All resilience demos completed!")
    print("The ScriptOhio Autonomous Resilience System is ready to protect your workflows.")


def show_resilience_status():
    """Display current resilience system status"""
    print_section("Current Resilience System Status")

    status = autonomous_resilience_agent.get_resilience_status()

    print("📊 Error Metrics:")
    metrics = status["error_metrics"]
    print(f"  Total Errors: {metrics['total_errors']}")
    print(f"  Error Rate (24h): {metrics['error_rate_24h']:.1%}")
    print(f"  Last Error: {metrics['last_error_time'] or 'None'}")

    if metrics['errors_by_category']:
        print("  Errors by Category:")
        for category, count in metrics['errors_by_category'].items():
            print(f"    {category}: {count}")

    if metrics['errors_by_severity']:
        print("  Errors by Severity:")
        for severity, count in metrics['errors_by_severity'].items():
            print(f"    {severity}: {count}")

    print("\n⚡ Circuit Breakers:")
    for name, cb_status in status["circuit_breakers"].items():
        state_emoji = "🟢" if cb_status["state"] == "closed" else "🔴" if cb_status["state"] == "open" else "🟡"
        print(f"  {state_emoji} {name}: {cb_status['state'].upper()}")
        print(f"    Failures: {cb_status['failure_count']}, Calls: {cb_status['call_count']}")

    print("\n🔧 Recovery Engine:")
    recovery = status["recovery_engine"]
    print(f"  Active Recoveries: {recovery['active_recoveries']}")
    print(f"  Available Strategies: {recovery['available_strategies']}")

    print(f"\n🏥 Last Health Check: {status['last_health_check'] or 'Never'}")


async def main():
    """Main demo entry point"""
    print_section("🏈 ScriptOhio Autonomous Resilience System Demo")
    print("Welcome to the autonomous resilience demonstration!")
    print("This system protects your workflows with circuit breakers and intelligent error recovery.")

    # Check if running with arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--all":
            await run_all_resilience_demos()
        elif arg == "--status":
            show_resilience_status()
        elif arg == "--interactive":
            await interactive_resilience_menu()
        else:
            print(f"Unknown argument: {arg}")
            print("Usage: python demo_autonomous_resilience.py [--all|--status|--interactive]")
    else:
        # Default: run interactive menu
        await interactive_resilience_menu()


if __name__ == "__main__":
    asyncio.run(main())