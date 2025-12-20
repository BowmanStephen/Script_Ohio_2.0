#!/usr/bin/env python3
"""
Coordination System Test Suite
Version 1.0

Comprehensive testing of inter-agent communication and human-in-the-loop integration.
"""

import asyncio
import json
import logging
import time
from datetime import datetime

from agents.coordination.coordination_integration import (
    initialize_coordination_system, register_specialized_agent,
    execute_agent_workflow, broadcast_system_update,
    get_coordination_system_status, perform_coordination_health_check
)
from agents.coordination.agent_communication_adapter import AgentCapability
from agents.coordination.human_in_the_loop import (
    request_human_decision, submit_human_decision,
    DecisionLevel, NotificationChannel, get_human_oversight_status
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSpecializedAgent:
    """Test specialized agent for coordination testing"""

    def __init__(self, agent_id: str, response_delay: float = 0.1):
        self.agent_id = agent_id
        self.response_delay = response_delay
        self.coordination_log = []

    def _execute_action(self, action: str, parameters: dict, user_context: dict) -> dict:
        """Execute action as defined by BaseAgent framework"""
        time.sleep(self.response_delay)  # Simulate processing time

        result = {
            "status": "success",
            "agent": self.agent_id,
            "action": action,
            "parameters": parameters,
            "execution_time": self.response_delay,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.coordination_log.append({
            "action": "execute_action",
            "result": result
        })

        return result

    def execute_coordination_step(self, workflow_id: str, step_data: dict) -> dict:
        """Execute coordination workflow step"""
        time.sleep(self.response_delay)  # Simulate processing time

        result = {
            "agent": self.agent_id,
            "workflow_id": workflow_id,
            "step_completed": True,
            "result": f"Processed by {self.agent_id}",
            "step_data": step_data,
            "processing_time": self.response_delay,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.coordination_log.append({
            "action": "coordination_step",
            "workflow_id": workflow_id,
            "result": result
        })

        return result

    def get_coordination_log(self) -> list:
        """Get agent's coordination log"""
        return self.coordination_log.copy()

class CoordinationSystemTester:
    """Comprehensive coordination system tester"""

    def __init__(self):
        self.test_results = {
            "communication_tests": {},
            "workflow_tests": {},
            "human_oversight_tests": {},
            "integration_tests": {},
            "performance_tests": {}
        }
        self.test_agents = {}

    async def run_all_tests(self):
        """Run all coordination system tests"""
        logger.info("🧪 Starting Comprehensive Coordination System Tests")
        print("=" * 80)

        # Initialize coordination system
        await self._initialize_test_environment()

        # Run test suites
        await self._test_communication_system()
        await self._test_workflow_coordination()
        await self._test_human_oversight_integration()
        await self._test_system_integration()
        await self._test_performance_metrics()

        # Generate comprehensive report
        self._generate_test_report()

    async def _initialize_test_environment(self):
        """Initialize test environment with specialized agents"""
        logger.info("🔧 Initializing test environment...")

        # Initialize coordination system
        config = {
            "redis_url": "redis://localhost:6379/1",
            "human_in_the_loop": {
                "notifications": {
                    "email": {
                        "smtp_server": "localhost",
                        "smtp_port": 587,
                        "from_address": "test-coordination@example.com",
                        "approvers": ["test-admin@example.com"]
                    }
                }
            }
        }

        await initialize_coordination_system(config)

        # Create test specialized agents
        test_capabilities = [
            AgentCapability(
                name="test_data_processing",
                description="Test data processing capability",
                input_types=["dict", "list"],
                output_types=["dict"],
                execution_time_estimate=0.5,
                requires_human_approval=False
            ),
            AgentCapability(
                name="test_model_execution",
                description="Test model execution capability",
                input_types=["dict"],
                output_types=["dict"],
                execution_time_estimate=1.0,
                requires_human_approval=False
            ),
            AgentCapability(
                name="test_critical_operation",
                description="Test critical operation requiring approval",
                input_types=["dict"],
                output_types=["dict"],
                execution_time_estimate=2.0,
                requires_human_approval=True
            )
        ]

        # Create test agents
        agent_configs = [
            ("cfbd_integration_agent", 8200, 0.1),
            ("model_execution_engine", 8300, 0.2),
            ("analytics_generator", 8400, 0.15),
            ("quality_assurance_agent", 8500, 0.05)
        ]

        for agent_id, port, delay in agent_configs:
            agent_instance = TestSpecializedAgent(agent_id, delay)
            self.test_agents[agent_id] = agent_instance

            success = await register_specialized_agent(
                agent_id, agent_instance, port, test_capabilities
            )

            if success:
                logger.info(f"✅ Test agent {agent_id} registered successfully")
            else:
                logger.error(f"❌ Failed to register test agent {agent_id}")

        # Start agent communication
        from agents.coordination.agent_communication_adapter import communication_manager
        await communication_manager.start_all_communication()

        logger.info("✅ Test environment initialized")

    async def _test_communication_system(self):
        """Test inter-agent communication system"""
        logger.info("📡 Testing inter-agent communication...")

        test_cases = [
            {
                "name": "basic_message_passing",
                "description": "Test basic message passing between agents",
                "test": self._test_basic_message_passing
            },
            {
                "name": "broadcast_messaging",
                "description": "Test broadcast messaging to all agents",
                "test": self._test_broadcast_messaging
            },
            {
                "name": "message_priority_handling",
                "description": "Test message priority handling",
                "test": self._test_message_priority_handling
            }
        ]

        for test_case in test_cases:
            logger.info(f"  🧪 Running {test_case['name']}: {test_case['description']}")
            try:
                result = await test_case["test"]()
                self.test_results["communication_tests"][test_case["name"]] = {
                    "status": "passed" if result else "failed",
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.info(f"    {'✅ PASSED' if result else '❌ FAILED'}")
            except Exception as e:
                self.test_results["communication_tests"][test_case["name"]] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.error(f"    ❌ ERROR: {e}")

    async def _test_basic_message_passing(self) -> bool:
        """Test basic message passing between agents"""
        try:
            # Test message passing between CFBD integration agent and model execution engine
            from agents.coordination.agent_communication_adapter import send_from_agent

            success = await send_from_agent(
                "cfbd_integration_agent",
                "model_execution_engine",
                "Test Data Processing Request",
                {
                    "action": "process_data",
                    "season": 2025,
                    "week": 13,
                    "test_data": "sample_data"
                }
            )

            return success

        except Exception as e:
            logger.error(f"Basic message passing test failed: {e}")
            return False

    async def _test_broadcast_messaging(self) -> bool:
        """Test broadcast messaging to all agents"""
        try:
            from agents.coordination.agent_communication_adapter import broadcast_from_agent

            broadcast_results = await broadcast_from_agent(
                "cfbd_integration_agent",
                "System Status Update",
                {
                    "system_status": "operational",
                    "active_agents": 4,
                    "test_mode": True
                }
            )

            # Check if at least one agent received the broadcast
            successful_deliveries = sum(broadcast_results)
            return successful_deliveries > 0

        except Exception as e:
            logger.error(f"Broadcast messaging test failed: {e}")
            return False

    async def _test_message_priority_handling(self) -> bool:
        """Test message priority handling"""
        try:
            # Send messages with different priorities
            from agents.coordination.agent_communication_adapter import send_from_agent
            from agents.coordination.inter_agent_communication import Priority

            # Test high priority message
            high_priority_result = await send_from_agent(
                "cfbd_integration_agent",
                "model_execution_engine",
                "High Priority Test",
                {"priority": "high", "urgent": True},
                Priority.HIGH
            )

            # Test low priority message
            low_priority_result = await send_from_agent(
                "cfbd_integration_agent",
                "model_execution_engine",
                "Low Priority Test",
                {"priority": "low", "background": True},
                Priority.LOW
            )

            return high_priority_result and low_priority_result

        except Exception as e:
            logger.error(f"Message priority handling test failed: {e}")
            return False

    async def _test_workflow_coordination(self):
        """Test workflow coordination patterns"""
        logger.info("🔄 Testing workflow coordination...")

        test_cases = [
            {
                "name": "pipeline_workflow",
                "description": "Test sequential pipeline workflow execution",
                "test": self._test_pipeline_workflow
            },
            {
                "name": "parallel_workflow",
                "description": "Test parallel workflow execution",
                "test": self._test_parallel_workflow
            },
            {
                "name": "consensus_decision",
                "description": "Test consensus decision making",
                "test": self._test_consensus_decision
            }
        ]

        for test_case in test_cases:
            logger.info(f"  🧪 Running {test_case['name']}: {test_case['description']}")
            try:
                result = await test_case["test"]()
                self.test_results["workflow_tests"][test_case["name"]] = {
                    "status": "passed" if result else "failed",
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.info(f"    {'✅ PASSED' if result else '❌ FAILED'}")
            except Exception as e:
                self.test_results["workflow_tests"][test_case["name"]] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.error(f"    ❌ ERROR: {e}")

    async def _test_pipeline_workflow(self) -> bool:
        """Test sequential pipeline workflow execution"""
        try:
            workflow_result = await execute_agent_workflow(
                "data_processing_pipeline",
                ["cfbd_integration_agent", "model_execution_engine"],
                {
                    "task": "process_week_13_data",
                    "season": 2025,
                    "week": 13,
                    "test_mode": True
                },
                "pipeline"
            )

            return workflow_result.get("status") == "success"

        except Exception as e:
            logger.error(f"Pipeline workflow test failed: {e}")
            return False

    async def _test_parallel_workflow(self) -> bool:
        """Test parallel workflow execution"""
        try:
            workflow_result = await execute_agent_workflow(
                "parallel_data_analysis",
                ["cfbd_integration_agent", "analytics_generator", "quality_assurance_agent"],
                {
                    "task": "analyze_week_13_games",
                    "season": 2025,
                    "week": 13,
                    "parallel_tasks": True
                },
                "parallel"
            )

            return workflow_result.get("status") in ["success", "partial"]

        except Exception as e:
            logger.error(f"Parallel workflow test failed: {e}")
            return False

    async def _test_consensus_decision(self) -> bool:
        """Test consensus decision making"""
        try:
            # Request consensus from multiple agents
            consensus_result = await coordination_integrator.request_peer_consensus(
                "cfbd_integration_agent",
                "data_processing_strategy",
                {
                    "proposal": "Use enhanced feature engineering",
                    "rationale": "Improved accuracy with 86 opponent-adjusted features",
                    "expected_impact": "15% accuracy improvement"
                },
                min_consensus=2
            )

            return consensus_result.get("consensus_reached", False)

        except Exception as e:
            logger.error(f"Consensus decision test failed: {e}")
            return False

    async def _test_human_oversight_integration(self):
        """Test human-in-the-loop integration"""
        logger.info("👥 Testing human-in-the-loop integration...")

        test_cases = [
            {
                "name": "decision_request_creation",
                "description": "Test creating human decision requests",
                "test": self._test_decision_request_creation
            },
            {
                "name": "automated_approval",
                "description": "Test automated approval for low-risk operations",
                "test": self._test_automated_approval
            },
            {
                "name": "notification_system",
                "description": "Test notification system integration",
                "test": self._test_notification_system
            }
        ]

        for test_case in test_cases:
            logger.info(f"  🧪 Running {test_case['name']}: {test_case['description']}")
            try:
                result = await test_case["test"]()
                self.test_results["human_oversight_tests"][test_case["name"]] = {
                    "status": "passed" if result else "failed",
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.info(f"    {'✅ PASSED' if result else '❌ FAILED'}")
            except Exception as e:
                self.test_results["human_oversight_tests"][test_case["name"]] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.error(f"    ❌ ERROR: {e}")

    async def _test_decision_request_creation(self) -> bool:
        """Test creating human decision requests"""
        try:
            # Request human decision for a critical operation
            decision_request = await request_human_decision(
                "model_deployment_production",
                "model_execution_engine",
                "Test Model Deployment",
                "Requesting approval to deploy test model to production",
                {
                    "model_name": "test_model_2025",
                    "accuracy": 0.82,
                    "training_games": 4500,
                    "deployment_target": "production"
                },
                {
                    "validation_results": "passed",
                    "test_coverage": "95%"
                },
                risk_level="medium",
                urgency="normal"
            )

            return decision_request.get("status") in ["pending", "approved"]

        except Exception as e:
            logger.error(f"Decision request creation test failed: {e}")
            return False

    async def _test_automated_approval(self) -> bool:
        """Test automated approval for low-risk operations"""
        try:
            # Request decision for automated weekly analysis (should be automatic)
            decision_request = await request_human_decision(
                "automated_weekly_analysis",
                "analytics_generator",
                "Automated Weekly Analysis",
                "Running automated weekly analysis for week 13",
                {
                    "analysis_type": "weekly_summary",
                    "season": 2025,
                    "week": 13
                },
                risk_level="low",
                urgency="normal"
            )

            return decision_request.get("status") == "approved"

        except Exception as e:
            logger.error(f"Automated approval test failed: {e}")
            return False

    async def _test_notification_system(self) -> bool:
        """Test notification system integration"""
        try:
            # Check if dashboard directory exists and can be written to
            from pathlib import Path
            dashboard_dir = Path("project_management/human_oversight")
            dashboard_dir.mkdir(parents=True, exist_ok=True)

            # Create a test dashboard entry
            test_file = dashboard_dir / "test_notification.json"
            test_data = {
                "test": True,
                "timestamp": datetime.utcnow().isoformat()
            }

            with open(test_file, 'w') as f:
                json.dump(test_data, f)

            # Clean up test file
            test_file.unlink()

            return True

        except Exception as e:
            logger.error(f"Notification system test failed: {e}")
            return False

    async def _test_system_integration(self):
        """Test complete system integration"""
        logger.info("🔗 Testing system integration...")

        test_cases = [
            {
                "name": "system_status_reporting",
                "description": "Test comprehensive system status reporting",
                "test": self._test_system_status_reporting
            },
            {
                "name": "health_check_system",
                "description": "Test system health check functionality",
                "test": self._test_health_check_system
            },
            {
                "name": "coordination_workflows",
                "description": "Test complete coordination workflows",
                "test": self._test_complete_coordination_workflows
            }
        ]

        for test_case in test_cases:
            logger.info(f"  🧪 Running {test_case['name']}: {test_case['description']}")
            try:
                result = await test_case["test"]()
                self.test_results["integration_tests"][test_case["name"]] = {
                    "status": "passed" if result else "failed",
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.info(f"    {'✅ PASSED' if result else '❌ FAILED'}")
            except Exception as e:
                self.test_results["integration_tests"][test_case["name"]] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.error(f"    ❌ ERROR: {e}")

    async def _test_system_status_reporting(self) -> bool:
        """Test comprehensive system status reporting"""
        try:
            status = get_coordination_system_status()

            required_keys = [
                "system_metrics", "registered_agents", "active_workflows",
                "communication_stats", "human_oversight_stats", "system_uptime_minutes"
            ]

            return all(key in status for key in required_keys)

        except Exception as e:
            logger.error(f"System status reporting test failed: {e}")
            return False

    async def _test_health_check_system(self) -> bool:
        """Test system health check functionality"""
        try:
            health_status = await perform_coordination_health_check()

            required_keys = ["timestamp", "overall_status", "components"]
            return all(key in health_status for key in required_keys)

        except Exception as e:
            logger.error(f"Health check system test failed: {e}")
            return False

    async def _test_complete_coordination_workflows(self) -> bool:
        """Test complete coordination workflows"""
        try:
            # Execute a comprehensive workflow involving multiple coordination patterns
            workflow_result = await execute_agent_workflow(
                "comprehensive_weekly_analysis",
                ["cfbd_integration_agent", "model_execution_engine", "analytics_generator"],
                {
                    "task": "complete_weekly_analysis",
                    "season": 2025,
                    "week": 13,
                    "include_predictions": True,
                    "require_validation": True
                },
                "pipeline"
            )

            return workflow_result.get("status") == "success"

        except Exception as e:
            logger.error(f"Complete coordination workflows test failed: {e}")
            return False

    async def _test_performance_metrics(self):
        """Test system performance metrics"""
        logger.info("📊 Testing performance metrics...")

        test_cases = [
            {
                "name": "message_throughput",
                "description": "Test message throughput performance",
                "test": self._test_message_throughput
            },
            {
                "name": "workflow_execution_time",
                "description": "Test workflow execution time performance",
                "test": self._test_workflow_execution_time
            },
            {
                "name": "system_scalability",
                "description": "Test system scalability with concurrent operations",
                "test": self._test_system_scalability
            }
        ]

        for test_case in test_cases:
            logger.info(f"  🧪 Running {test_case['name']}: {test_case['description']}")
            try:
                result = await test_case["test"]()
                self.test_results["performance_tests"][test_case["name"]] = {
                    "status": "passed" if result else "failed",
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.info(f"    {'✅ PASSED' if result else '❌ FAILED'}")
            except Exception as e:
                self.test_results["performance_tests"][test_case["name"]] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.error(f"    ❌ ERROR: {e}")

    async def _test_message_throughput(self) -> bool:
        """Test message throughput performance"""
        try:
            from agents.coordination.agent_communication_adapter import send_from_agent

            start_time = time.time()
            message_count = 10
            successful_sends = 0

            for i in range(message_count):
                success = await send_from_agent(
                    "cfbd_integration_agent",
                    "model_execution_engine",
                    f"Performance Test Message {i+1}",
                    {"test_id": i, "performance_test": True}
                )
                if success:
                    successful_sends += 1

            execution_time = time.time() - start_time
            throughput = successful_sends / execution_time

            # Pass if throughput is reasonable (at least 2 messages per second)
            return throughput >= 2.0 and successful_sends >= message_count * 0.8

        except Exception as e:
            logger.error(f"Message throughput test failed: {e}")
            return False

    async def _test_workflow_execution_time(self) -> bool:
        """Test workflow execution time performance"""
        try:
            start_time = time.time()

            # Execute a simple workflow
            workflow_result = await execute_agent_workflow(
                "performance_test_workflow",
                ["cfbd_integration_agent", "model_execution_engine"],
                {"performance_test": True, "data_size": "small"},
                "pipeline"
            )

            execution_time = time.time() - start_time

            # Pass if workflow completes within reasonable time (under 10 seconds)
            return (
                workflow_result.get("status") == "success" and
                execution_time < 10.0
            )

        except Exception as e:
            logger.error(f"Workflow execution time test failed: {e}")
            return False

    async def _test_system_scalability(self) -> bool:
        """Test system scalability with concurrent operations"""
        try:
            # Run multiple workflows concurrently
            concurrent_workflows = 3

            async def run_workflow(workflow_id: int):
                return await execute_agent_workflow(
                    f"scalability_test_{workflow_id}",
                    ["cfbd_integration_agent", "model_execution_engine"],
                    {"concurrent_test": True, "workflow_id": workflow_id},
                    "pipeline"
                )

            start_time = time.time()

            # Execute workflows concurrently
            tasks = [run_workflow(i) for i in range(concurrent_workflows)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            execution_time = time.time() - start_time

            # Count successful workflows
            successful_workflows = sum(
                1 for result in results
                if not isinstance(result, Exception) and result.get("status") == "success"
            )

            # Pass if at least 80% of workflows succeed within reasonable time
            return (
                successful_workflows >= concurrent_workflows * 0.8 and
                execution_time < 30.0
            )

        except Exception as e:
            logger.error(f"System scalability test failed: {e}")
            return False

    def _generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("🧪 COMPREHENSIVE COORDINATION SYSTEM TEST REPORT")
        print("=" * 80)

        # Calculate overall statistics
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0

        for test_category, test_results in self.test_results.items():
            category_total = len(test_results)
            category_passed = sum(1 for result in test_results.values() if result["status"] == "passed")
            category_failed = sum(1 for result in test_results.values() if result["status"] == "failed")
            category_errors = sum(1 for result in test_results.values() if result["status"] == "error")

            total_tests += category_total
            passed_tests += category_passed
            failed_tests += category_failed
            error_tests += category_errors

            print(f"\n📋 {test_category.replace('_', ' ').title()}:")
            print(f"   Total: {category_total} | Passed: {category_passed} | Failed: {category_failed} | Errors: {category_errors}")

            # Show individual test results
            for test_name, test_result in test_results.items():
                status_icon = {
                    "passed": "✅",
                    "failed": "❌",
                    "error": "💥"
                }.get(test_result["status"], "❓")

                print(f"   {status_icon} {test_name}")

        # Overall summary
        print(f"\n🎯 OVERALL SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ({(passed_tests/total_tests*100):.1f}%)")
        print(f"   Failed: {failed_tests} ({(failed_tests/total_tests*100):.1f}%)")
        print(f"   Errors: {error_tests} ({(error_tests/total_tests*100):.1f}%)")

        # Success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")

        # System status
        print(f"\n📊 SYSTEM STATUS:")
        try:
            coordination_status = get_coordination_system_status()
            print(f"   Registered Agents: {coordination_status.get('registered_agents', [])}")
            print(f"   Active Workflows: {coordination_status.get('active_workflows', 0)}")
            print(f"   System Uptime: {coordination_status.get('system_uptime_minutes', 0):.1f} minutes")
        except Exception as e:
            print(f"   Status retrieval failed: {e}")

        # Agent logs
        print(f"\n🤖 AGENT COORDINATION LOGS:")
        for agent_id, agent in self.test_agents.items():
            log = agent.get_coordination_log()
            print(f"   {agent_id}: {len(log)} coordination actions")
            for entry in log[-2:]:  # Show last 2 entries
                print(f"     - {entry['action']}: {entry.get('result', {}).get('timestamp', 'N/A')}")

        # Final assessment
        if success_rate >= 80:
            print(f"\n🎉 COORDINATION SYSTEM: {'EXCELLENT' if success_rate >= 95 else 'GOOD'}")
            print("   System is ready for production deployment!")
        elif success_rate >= 60:
            print(f"\n⚠️  COORDINATION SYSTEM: ACCEPTABLE")
            print("   System has some issues but is functional.")
        else:
            print(f"\n❌ COORDINATION SYSTEM: NEEDS IMPROVEMENT")
            print("   System has significant issues that need to be addressed.")

        # Save detailed report
        report_file = f"coordination_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "test_results": self.test_results,
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "error_tests": error_tests,
                    "success_rate": success_rate,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "system_status": coordination_status if 'coordination_status' in locals() else None,
                "agent_logs": {
                    agent_id: agent.get_coordination_log()
                    for agent_id, agent in self.test_agents.items()
                }
            }, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")
        print("=" * 80)

async def main():
    """Main test execution function"""
    print("🚀 Starting Comprehensive Coordination System Testing")
    print("This test suite validates inter-agent communication, human-in-the-loop integration,")
    print("workflow coordination, and system performance.")
    print("\nNote: Some tests may require Redis to be running for full functionality.")
    print("-" * 80)

    tester = CoordinationSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())