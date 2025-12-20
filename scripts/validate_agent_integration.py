#!/usr/bin/env python3
"""
Agent Integration Validation Script

Validates the successful integration and coordination of 15+ agents in the Super AI Agent Architecture.
This script provides comprehensive validation of the Phase 2 achievements.

Usage:
    python3 scripts/validate_agent_integration.py [--component all|registry|communication|load_balancing|workflows]
    python3 scripts/validate_agent_integration.py --detailed
    python3 scripts/validate_agent_integration.py --report

Author: Super AI Agent System
Created: 2025-12-18
"""

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Any, Dict, List


def validate_agent_registry() -> Dict[str, Any]:
    """Validate agent registry with Meta Agent"""
    print("📋 Validating Agent Registry...")

    try:
        from agents.meta_agent import meta_agent

        # Get registry
        registry = meta_agent._get_registry({}, {})
        agent_count = len(registry)

        # Check file-based registry
        import os

        registry_file = "agents/agent_registry.json"
        file_agents = 0

        if os.path.exists(registry_file):
            with open(registry_file, "r") as f:
                file_registry = json.load(f)
                file_agents = len(file_registry)

        # Calculate capacity usage
        capacity_usage = file_agents / 20 * 100

        success_metrics = {
            "meta_agent_accessible": True,
            "agent_count": agent_count,
            "file_agent_count": file_agents,
            "capacity_usage_percent": capacity_usage,
            "meets_15_agent_target": file_agents >= 15,
            "meets_10_agent_target": file_agents >= 10,
        }

        print(f"  ✅ Meta Agent accessible: {success_metrics['meta_agent_accessible']}")
        print(f"  📊 Registry agents: {success_metrics['agent_count']}")
        print(f"  📁 File agents: {success_metrics['file_agent_count']}")
        print(f"  📈 Capacity usage: {success_metrics['capacity_usage_percent']:.1f}%")
        print(
            f"  🎯 15+ agent target: {'✅ MET' if success_metrics['meets_15_agent_target'] else '❌ NOT MET'}"
        )

        return {
            "component": "agent_registry",
            "status": (
                "success"
                if success_metrics["meets_15_agent_target"]
                else "partial_success"
            ),
            "metrics": success_metrics,
        }

    except Exception as e:
        print(f"  ❌ Registry validation failed: {e}")
        return {"component": "agent_registry", "status": "error", "error": str(e)}


def validate_communication_protocols() -> Dict[str, Any]:
    """Validate communication protocols and TOON integration"""
    print("📡 Validating Communication Protocols...")

    try:
        from agents.coordination.agent_integration_specialist import (
            AgentIntegrationSpecialist,
        )
        from src.toon_format import decode, encode

        # Test TOON format
        test_data = {
            "agents": [
                {"id": "test_agent_1", "status": "active", "health": 0.9},
                {"id": "test_agent_2", "status": "active", "health": 0.8},
                {"id": "test_agent_3", "status": "active", "health": 0.85},
            ],
            "timestamp": datetime.now().isoformat(),
            "type": "coordination_test",
        }

        # Test compression
        toon_output = encode(test_data)
        decoded_output = decode(toon_output)

        json_length = len(str(test_data))
        toon_length = len(toon_output)
        compression_ratio = (json_length - toon_length) / json_length

        # Validate data integrity
        data_integrity = (
            len(decoded_output["agents"]) == len(test_data["agents"])
            and decoded_output["type"] == test_data["type"]
        )

        # Test integration specialist
        specialist = AgentIntegrationSpecialist()
        comm_result = specialist._execute_action(
            "establish_communication_protocols", {}, {}
        )

        success_metrics = {
            "toon_format_works": True,
            "compression_ratio": compression_ratio,
            "data_integrity": data_integrity,
            "compression_above_40_percent": compression_ratio > 0.40,
            "protocols_established": comm_result.get("communication_summary", {}).get(
                "protocols_established", 0
            ),
            "toon_integration_enabled": comm_result.get(
                "communication_summary", {}
            ).get("toon_integration_enabled", False),
            "message_routing_established": comm_result.get(
                "communication_summary", {}
            ).get("message_routing_established", False),
        }

        print(f"  ✅ TOON format works: {success_metrics['toon_format_works']}")
        print(f"  📊 Compression ratio: {success_metrics['compression_ratio']:.1%}")
        print(f"  🔒 Data integrity: {success_metrics['data_integrity']}")
        print(
            f"  📈 Compression >40%: {success_metrics['compression_above_40_percent']}"
        )
        print(f"  🔗 Protocols established: {success_metrics['protocols_established']}")
        print(f"  📝 TOON integration: {success_metrics['toon_integration_enabled']}")

        overall_success = (
            success_metrics["toon_format_works"]
            and success_metrics["data_integrity"]
            and success_metrics["compression_above_40_percent"]
            and success_metrics["toon_integration_enabled"]
        )

        return {
            "component": "communication_protocols",
            "status": "success" if overall_success else "partial_success",
            "metrics": success_metrics,
        }

    except Exception as e:
        print(f"  ❌ Communication validation failed: {e}")
        return {
            "component": "communication_protocols",
            "status": "error",
            "error": str(e),
        }


def validate_load_balancing() -> Dict[str, Any]:
    """Validate load balancing across agent ecosystem"""
    print("⚖️ Validating Load Balancing...")

    try:
        import psutil
        from agents.orchestration_agent import orchestration_agent

        # Get system metrics
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_usage_percent": (
                psutil.disk_usage("/").used / psutil.disk_usage("/").total
            )
            * 100,
        }

        # Test orchestration agent
        optimization_methods = [
            method for method in dir(orchestration_agent) if "optim" in method.lower()
        ]

        # Test optimization monitoring
        try:
            monitoring_result = orchestration_agent._monitor_optimization({}, {})
            monitoring_works = True
        except Exception as e:
            print(f"  ⚠️ Optimization monitoring issue: {e}")
            monitoring_works = False

        success_metrics = {
            "system_metrics_available": True,
            "cpu_usage": system_metrics["cpu_percent"],
            "memory_usage": system_metrics["memory_percent"],
            "system_resources_healthy": (
                system_metrics["cpu_percent"] < 80
                and system_metrics["memory_percent"] < 90
            ),
            "orchestration_agent_available": True,
            "optimization_methods_count": len(optimization_methods),
            "optimization_monitoring_works": monitoring_works,
            "load_balancing_ready": len(optimization_methods) > 0,
        }

        print(
            f"  ✅ System metrics available: {success_metrics['system_metrics_available']}"
        )
        print(f"  💻 CPU usage: {success_metrics['cpu_usage']:.1f}%")
        print(f"  🧠 Memory usage: {success_metrics['memory_usage']:.1f}%")
        print(f"  🏥 System healthy: {success_metrics['system_resources_healthy']}")
        print(
            f"  🤝 Orchestration agent: {success_metrics['orchestration_agent_available']}"
        )
        print(
            f"  ⚙️ Optimization methods: {success_metrics['optimization_methods_count']}"
        )
        print(
            f"  📊 Monitoring works: {success_metrics['optimization_monitoring_works']}"
        )

        overall_success = (
            success_metrics["system_metrics_available"]
            and success_metrics["system_resources_healthy"]
            and success_metrics["orchestration_agent_available"]
            and success_metrics["load_balancing_ready"]
        )

        return {
            "component": "load_balancing",
            "status": "success" if overall_success else "partial_success",
            "metrics": success_metrics,
        }

    except Exception as e:
        print(f"  ❌ Load balancing validation failed: {e}")
        return {"component": "load_balancing", "status": "error", "error": str(e)}


def validate_workflow_coordination() -> Dict[str, Any]:
    """Validate workflow coordination across agents"""
    print("🔄 Validating Workflow Coordination...")

    try:
        from agents.coordination.agent_integration_specialist import (
            AgentIntegrationSpecialist,
        )

        specialist = AgentIntegrationSpecialist()

        # Test workflow coordination
        workflow_result = specialist._execute_action(
            "coordinate_agent_workflows",
            {
                "workflow_types": ["analysis", "prediction", "monitoring"],
                "test_execution": True,
            },
            {},
        )

        wf_summary = workflow_result.get("workflow_summary", {})
        workflows = workflow_result.get("coordinated_workflows", [])

        # Analyze workflow success
        successful_workflows = len(
            [w for w in workflows if w.get("status") == "tested"]
        )
        parallel_workflows = len(
            [w for w in workflows if w.get("parallel_execution", False)]
        )

        success_metrics = {
            "workflow_coordination_works": workflow_result.get("status") == "success",
            "total_workflows": wf_summary.get("total_workflows", 0),
            "successful_executions": wf_summary.get("successful_executions", 0),
            "workflow_types_supported": len(
                wf_summary.get("workflow_types_requested", [])
            ),
            "parallel_execution_enabled": wf_summary.get(
                "parallel_execution_enabled", False
            ),
            "workflow_definitions_created": len(workflows),
            "test_execution_successful": successful_workflows > 0,
        }

        print(
            f"  ✅ Coordination works: {success_metrics['workflow_coordination_works']}"
        )
        print(f"  📊 Total workflows: {success_metrics['total_workflows']}")
        print(f"  ✅ Successful executions: {success_metrics['successful_executions']}")
        print(f"  🔄 Workflow types: {success_metrics['workflow_types_supported']}")
        print(
            f"  ⚡ Parallel execution: {success_metrics['parallel_execution_enabled']}"
        )
        print(
            f"  📝 Definitions created: {success_metrics['workflow_definitions_created']}"
        )

        overall_success = (
            success_metrics["workflow_coordination_works"]
            and success_metrics["total_workflows"] > 0
        )

        return {
            "component": "workflow_coordination",
            "status": "success" if overall_success else "partial_success",
            "metrics": success_metrics,
        }

    except Exception as e:
        print(f"  ❌ Workflow coordination validation failed: {e}")
        return {
            "component": "workflow_coordination",
            "status": "error",
            "error": str(e),
        }


def generate_integration_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comprehensive integration report"""

    # Calculate overall success
    success_count = sum(1 for r in results if r.get("status") == "success")
    partial_count = sum(1 for r in results if r.get("status") == "partial_success")
    error_count = sum(1 for r in results if r.get("status") == "error")
    total_count = len(results)

    # Calculate key metrics
    agent_registry_result = next(
        (r for r in results if r["component"] == "agent_registry"), {}
    )
    comm_result = next(
        (r for r in results if r["component"] == "communication_protocols"), {}
    )

    agents_registered = agent_registry_result.get("metrics", {}).get(
        "file_agent_count", 0
    )
    compression_ratio = comm_result.get("metrics", {}).get("compression_ratio", 0)

    # Determine overall grade
    success_rate = success_count / total_count if total_count > 0 else 0

    if success_rate >= 0.8 and agents_registered >= 15:
        overall_grade = "A+"
        status = "EXCELLENT"
    elif success_rate >= 0.7 and agents_registered >= 12:
        overall_grade = "A"
        status = "GOOD"
    elif success_rate >= 0.6 and agents_registered >= 10:
        overall_grade = "B"
        status = "SATISFACTORY"
    else:
        overall_grade = "C"
        status = "NEEDS_IMPROVEMENT"

    report = {
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 2: Agent Integration and Coordination",
        "overall_status": status,
        "overall_grade": overall_grade,
        "success_rate": success_rate,
        "component_results": {
            "successful": success_count,
            "partial_success": partial_count,
            "errors": error_count,
            "total": total_count,
        },
        "key_achievements": {
            "agents_registered": agents_registered,
            "target_15_agents": agents_registered >= 15,
            "target_10_agents": agents_registered >= 10,
            "compression_ratio": compression_ratio,
            "compression_above_40_percent": compression_ratio > 0.40,
            "capacity_usage_percent": (agents_registered / 20) * 100,
        },
        "detailed_results": results,
        "recommendations": generate_recommendations(
            results, success_rate, agents_registered
        ),
    }

    return report


def generate_recommendations(
    results: List[Dict[str, Any]], success_rate: float, agents_registered: int
) -> List[str]:
    """Generate recommendations based on validation results"""
    recommendations = []

    if success_rate >= 0.8 and agents_registered >= 15:
        recommendations.extend(
            [
                "🎉 EXCELLENT: Proceed to Phase 3: Advanced Performance Optimization",
                "📊 Monitor optimization benefits in production workflows",
                "🔧 Fine-tune load balancing parameters for maximum efficiency",
                "📝 Document integration patterns for future agent development",
            ]
        )
    elif agents_registered >= 10:
        recommendations.extend(
            [
                "⚠️ GOOD: Register 5+ more agents to reach 15+ target",
                "🔧 Fix any components showing errors before Phase 3",
                "📊 Test agent workflows with real data scenarios",
                "🏥 Establish comprehensive health monitoring",
            ]
        )
    else:
        recommendations.extend(
            [
                "❌ NEEDS WORK: Focus on registering 10+ minimum agents",
                "🔧 Debug integration issues in failed components",
                "📋 Review agent file formats and registry structure",
                "🔄 Re-run activation scripts to establish baseline",
            ]
        )

    # Component-specific recommendations
    for result in results:
        if result.get("status") == "error":
            component = result.get("component", "unknown")
            recommendations.append(
                f"🔧 Fix {component.replace('_', ' ').title()} component errors"
            )

    return recommendations


def main():
    """Main validation script"""
    parser = argparse.ArgumentParser(description="Validate Super AI Agent Integration")
    parser.add_argument(
        "--component",
        "-c",
        choices=["all", "registry", "communication", "load_balancing", "workflows"],
        default="all",
        help="Component to validate (default: all)",
    )
    parser.add_argument(
        "--detailed", "-d", action="store_true", help="Show detailed validation output"
    )
    parser.add_argument(
        "--report", "-r", action="store_true", help="Generate comprehensive report"
    )
    parser.add_argument("--output", "-o", help="Save report to JSON file")

    args = parser.parse_args()

    print("🔍 SUPER AI AGENT INTEGRATION VALIDATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Phase: Phase 2 - Agent Integration and Coordination")
    print(f"Component: {args.component}")
    print()

    start_time = time.time()
    results = []

    # Run validations based on component selection
    if args.component in ["all", "registry"]:
        results.append(validate_agent_registry())
        print()

    if args.component in ["all", "communication"]:
        results.append(validate_communication_protocols())
        print()

    if args.component in ["all", "load_balancing"]:
        results.append(validate_load_balancing())
        print()

    if args.component in ["all", "workflows"]:
        results.append(validate_workflow_coordination())
        print()

    execution_time = time.time() - start_time

    # Generate comprehensive report
    if args.component == "all" or args.report:
        print("=" * 60)
        print("📊 COMPREHENSIVE INTEGRATION REPORT")
        print("=" * 60)

        report = generate_integration_report(results)

        print(f"🎯 Overall Status: {report['overall_status']}")
        print(f"📈 Overall Grade: {report['overall_grade']}")
        print(f"✅ Success Rate: {report['success_rate']:.1%}")
        print(f"⏱️ Execution Time: {execution_time:.2f} seconds")

        print(f"\\n🏆 KEY ACHIEVEMENTS:")
        achievements = report["key_achievements"]
        print(f"  • Agents Registered: {achievements['agents_registered']}/20")
        print(
            f"  • 15+ Agent Target: {'✅ MET' if achievements['target_15_agents'] else '❌ NOT MET'}"
        )
        print(
            f"  • 10+ Agent Target: {'✅ MET' if achievements['target_10_agents'] else '❌ NOT MET'}"
        )
        print(f"  • Capacity Usage: {achievements['capacity_usage_percent']:.1f}%")
        print(f"  • Compression Ratio: {achievements['compression_ratio']:.1%}")
        print(
            f"  • Compression >40%: {'✅ MET' if achievements['compression_above_40_percent'] else '❌ NOT MET'}"
        )

        print(f"\\n📋 COMPONENT RESULTS:")
        comp_results = report["component_results"]
        print(f"  • Successful: {comp_results['successful']}")
        print(f"  • Partial Success: {comp_results['partial_success']}")
        print(f"  • Errors: {comp_results['errors']}")
        print(f"  • Total: {comp_results['total']}")

        print(f"\\n🎯 RECOMMENDATIONS:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")

        # Save report if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\\n📄 Report saved to: {args.output}")

    return report


if __name__ == "__main__":
    try:
        report = main()
        # Exit with appropriate code based on overall success
        if report.get("overall_grade") in ["A+", "A"]:
            sys.exit(0)  # Success
        elif report.get("overall_grade") in ["B"]:
            sys.exit(1)  # Partial success
        else:
            sys.exit(2)  # Needs work
    except KeyboardInterrupt:
        print("\\n⚠️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Validation failed: {e}")
        sys.exit(2)
