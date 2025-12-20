#!/usr/bin/env python3
"""
🚀 ScriptOhio Autonomous Orchestration Demo

Demonstrates the autonomous code orchestration system capabilities:
- Trigger monitoring and response
- Self-managing workflow execution
- Error recovery and self-healing
- Resource optimization
- Performance monitoring
"""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.autonomous_orchestration_agent import autonomous_orchestration_agent
from agents.autonomous_workflows.weekly_analysis_autonomator import weekly_analysis_autonomator
from agents.core.trigger_system import trigger_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Print a formatted subsection header"""
    print(f"\n--- {title} ---")


def demo_system_status():
    """Demo: Show autonomous orchestration system status"""
    print_section("System Status Overview")

    # Get autonomous orchestration agent status
    status = autonomous_orchestration_agent.get_system_status()
    print("🤖 Autonomous Orchestration Agent Status:")
    print(json.dumps(status, indent=2, default=str))

    # Get weekly analysis autonomator status
    analysis_status = weekly_analysis_autonomator.get_analysis_status()
    print("\n📊 Weekly Analysis Autonomator Status:")
    print(json.dumps(analysis_status, indent=2, default=str))

    # Get trigger registry stats
    trigger_stats = trigger_registry.get_trigger_stats()
    print("\n⚡ Trigger Registry Statistics:")
    print(json.dumps(trigger_stats, indent=2))


def demo_trigger_monitoring():
    """Demo: Monitor and respond to triggers"""
    print_section("Trigger Monitoring Demo")

    print_subsection("Checking for active triggers...")
    triggered_events = trigger_registry.check_triggers()

    if triggered_events:
        print(f"🎯 Found {len(triggered_events)} triggered events:")
        for event in triggered_events:
            print(f"  - {event.event_id}: {event.data['workflow']}")
    else:
        print("✅ No triggers currently activated")

    print_subsection("Creating ScriptOhio default triggers...")
    success = trigger_registry.create_script_ohio_triggers()
    if success:
        print("✅ Default ScriptOhio triggers created successfully")
    else:
        print("⚠️ Some triggers may already exist")

    # Show updated trigger stats
    updated_stats = trigger_registry.get_trigger_stats()
    print(f"\n📈 Updated Trigger Registry: {updated_stats['total_triggers']} total triggers")
    for trigger_type, count in updated_stats['by_type'].items():
        print(f"  - {trigger_type}: {count}")


def demo_autonomous_workflow():
    """Demo: Run autonomous workflow execution"""
    print_section("Autonomous Workflow Execution Demo")

    # Create a sample autonomous task
    print_subsection("Creating autonomous workflow task...")

    # Get current season and week
    current_time = datetime.now(timezone.utc)
    season = current_time.year if current_time.month >= 8 else current_time.year - 1
    week = min(18, max(1, (current_time - datetime(season, 9, 1, tzinfo=timezone.utc)).days // 7 + 1))

    # Test data availability check
    print(f"\n🔍 Testing data availability for Season {season}, Week {week}...")

    result = weekly_analysis_autonomator._execute_action(
        "check_data_availability",
        {"season": season, "week": week},
        {}
    )

    print("📋 Data Availability Check Results:")
    print(json.dumps(result, indent=2, default=str))

    if result.get("success"):
        print("\n✅ Data available - proceeding with quality validation...")

        # Test data quality validation
        quality_result = weekly_analysis_autonomator._execute_action(
            "validate_data_quality",
            {"season": season, "week": week},
            {}
        )

        print("📊 Data Quality Validation Results:")
        print(json.dumps(quality_result, indent=2, default=str))


def demo_task_queue_management():
    """Demo: Task queue management"""
    print_section("Task Queue Management Demo")

    # Get current queue status
    print_subsection("Current task queue status...")
    queue_status = autonomous_orchestration_agent._execute_action(
        "manage_task_queue",
        {"operation": "status"},
        {}
    )

    print("📋 Task Queue Status:")
    print(json.dumps(queue_status, indent=2, default=str))

    # Show queue statistics
    if queue_status.get("success"):
        queue_info = queue_status
        print(f"\n📊 Queue Statistics:")
        print(f"  - Total tasks: {queue_info['queue_size']}")
        print(f"  - Pending: {queue_info['pending_tasks']}")
        print(f"  - Running: {queue_info['running_tasks']}")
        print(f"  - Retrying: {queue_info['retrying_tasks']}")

        if queue_info.get('tasks_by_type'):
            print(f"  - Tasks by type:")
            for task_type, count in queue_info['tasks_by_type'].items():
                print(f"    * {task_type}: {count}")


def demo_self_healing():
    """Demo: Self-healing capabilities"""
    print_section("Self-Healing Demo")

    print_subsection("Simulating error scenarios...")

    # Test healing with different error types
    error_scenarios = [
        {
            "error": "Network timeout occurred while fetching CFBD data",
            "action": "check_data_availability"
        },
        {
            "error": "Permission denied accessing model files",
            "action": "run_predictions"
        },
        {
            "error": "Data format validation failed",
            "action": "validate_data_quality"
        }
    ]

    for i, scenario in enumerate(error_scenarios, 1):
        print(f"\n🔧 Scenario {i}: {scenario['error']}")

        heal_result = weekly_analysis_autonomator._execute_action(
            "heal_analysis",
            scenario,
            {}
        )

        print(f"🩹 Healing Result:")
        print(json.dumps(heal_result, indent=2, default=str))


def demo_resource_optimization():
    """Demo: Resource optimization"""
    print_section("Resource Optimization Demo")

    print_subsection("Running resource optimization...")

    optimization_result = autonomous_orchestration_agent._execute_action(
        "optimize_resources",
        {},
        {}
    )

    print("⚡ Resource Optimization Results:")
    print(json.dumps(optimization_result, indent=2, default=str))

    # Show system metrics
    print_subsection("Current system metrics...")
    metrics = autonomous_orchestration_agent.system_metrics

    print("📊 System Metrics:")
    print(f"  - Active tasks: {metrics.active_tasks}")
    print(f"  - Completed tasks: {metrics.completed_tasks}")
    print(f"  - Failed tasks: {metrics.failed_tasks}")
    print(f"  - Average response time: {metrics.average_response_time:.2f}s")
    print(f"  - System health score: {metrics.system_health_score:.2f}")

    if metrics.resource_usage:
        print(f"  - Resource usage: {metrics.resource_usage}")


def demo_autonomous_cycle():
    """Demo: Complete autonomous cycle"""
    print_section("Complete Autonomous Cycle Demo")

    print_subsection("Running full autonomous orchestration cycle...")

    cycle_result = autonomous_orchestration_agent._execute_action(
        "run_autonomous_cycle",
        {"max_executions": 2},  # Limit for demo
        {}
    )

    print("🔄 Autonomous Cycle Results:")
    print(json.dumps(cycle_result, indent=2, default=str))

    if cycle_result.get("success"):
        cycle_data = cycle_result.get("cycle_results", {})

        print("\n📈 Cycle Summary:")
        if "trigger_monitoring" in cycle_data:
            trigger_data = cycle_data["trigger_monitoring"]
            print(f"  - Triggers checked: {trigger_data.get('triggers_checked', 0)}")
            print(f"  - Tasks created: {trigger_data.get('tasks_created', 0)}")

        if "task_execution" in cycle_data:
            task_data = cycle_data["task_execution"]
            print(f"  - Tasks executed: {task_data.get('execution_count', 0)}")
            if task_data.get("executed_tasks"):
                print(f"  - Executed task IDs: {task_data['executed_tasks']}")

        if "self_healing" in cycle_data:
            heal_data = cycle_data["self_healing"]
            print(f"  - Healing actions: {heal_data.get('healing_actions', [])}")

        if "resource_optimization" in cycle_data:
            opt_data = cycle_data["resource_optimization"]
            print(f"  - Optimizations: {opt_data.get('optimizations', [])}")


def demo_performance_monitoring():
    """Demo: Performance monitoring and metrics"""
    print_section("Performance Monitoring Demo")

    print_subsection("Collecting performance metrics...")

    # Get autonomous orchestration agent metrics
    system_status = autonomous_orchestration_agent.get_system_status()

    print("📊 Performance Metrics:")
    print(f"  - Autonomy Level: {system_status['autonomy_level']}")
    print(f"  - System Health Score: {system_status['system_health_score']:.3f}")
    print(f"  - Active Tasks: {system_status['active_tasks']}")
    print(f"  - Completed Today: {system_status['completed_tasks']}")
    print(f"  - Failed Today: {system_status['failed_tasks']}")
    print(f"  - Average Response Time: {system_status['average_response_time']:.2f}s")

    if system_status.get('resource_usage'):
        print(f"  - Resource Usage:")
        for resource, usage in system_status['resource_usage'].items():
            print(f"    * {resource}: {usage}%")

    # Get state manager metrics
    print_subsection("State manager metrics...")
    try:
        from agents.core.state_manager import state_manager
        state_metrics = state_manager.get_metrics()

        print("💾 State Manager Metrics:")
        print(f"  - Total Snapshots: {state_metrics['total_snapshots']}")
        print(f"  - Active Snapshots: {state_metrics['active_snapshots']}")
        print(f"  - Cache Hit Rate: {state_metrics['cache_hit_rate']:.3f}")
        print(f"  - Snapshots Created: {state_metrics['snapshots_created']}")
        print(f"  - Snapshots Restored: {state_metrics['snapshots_restored']}")

    except Exception as e:
        print(f"⚠️ Could not retrieve state manager metrics: {e}")


def interactive_menu():
    """Interactive demo menu"""
    while True:
        print_section("Autonomous Orchestration Demo Menu")
        print("Choose a demo to run:")
        print("1. System Status Overview")
        print("2. Trigger Monitoring")
        print("3. Autonomous Workflow Execution")
        print("4. Task Queue Management")
        print("5. Self-Healing Demo")
        print("6. Resource Optimization")
        print("7. Complete Autonomous Cycle")
        print("8. Performance Monitoring")
        print("9. Run All Demos")
        print("0. Exit")

        choice = input("\nEnter your choice (0-9): ").strip()

        if choice == "0":
            print("\n👋 Exiting demo...")
            break
        elif choice == "1":
            demo_system_status()
        elif choice == "2":
            demo_trigger_monitoring()
        elif choice == "3":
            demo_autonomous_workflow()
        elif choice == "4":
            demo_task_queue_management()
        elif choice == "5":
            demo_self_healing()
        elif choice == "6":
            demo_resource_optimization()
        elif choice == "7":
            demo_autonomous_cycle()
        elif choice == "8":
            demo_performance_monitoring()
        elif choice == "9":
            run_all_demos()
        else:
            print("\n❌ Invalid choice. Please enter a number between 0-9.")

        if choice != "0":
            input("\nPress Enter to continue...")


def run_all_demos():
    """Run all demo functions"""
    demos = [
        ("System Status", demo_system_status),
        ("Trigger Monitoring", demo_trigger_monitoring),
        ("Autonomous Workflow", demo_autonomous_workflow),
        ("Task Queue Management", demo_task_queue_management),
        ("Self-Healing", demo_self_healing),
        ("Resource Optimization", demo_resource_optimization),
        ("Autonomous Cycle", demo_autonomous_cycle),
        ("Performance Monitoring", demo_performance_monitoring),
    ]

    for name, demo_func in demos:
        try:
            demo_func()
            time.sleep(2)  # Brief pause between demos
        except Exception as e:
            logger.error(f"Error in {name} demo: {e}")
            continue

    print_section("Demo Complete")
    print("🎉 All demos completed! The ScriptOhio Autonomous Orchestration System is ready.")


def main():
    """Main demo entry point"""
    print_section("🏈 ScriptOhio Autonomous Orchestration System Demo")
    print("Welcome to the autonomous code orchestration demonstration!")
    print("This system can self-manage workflows, heal from errors, and optimize resources.")

    # Check if running with arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--all":
            run_all_demos()
        elif arg == "--status":
            demo_system_status()
        elif arg == "--interactive":
            interactive_menu()
        else:
            print(f"Unknown argument: {arg}")
            print("Usage: python demo_autonomous_orchestration.py [--all|--status|--interactive]")
    else:
        # Default: run interactive menu
        interactive_menu()


if __name__ == "__main__":
    main()