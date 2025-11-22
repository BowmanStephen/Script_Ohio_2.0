#!/usr/bin/env python3
"""
Agent System Demonstration

This script demonstrates the complete agent architecture for Script Ohio 2.0,
showing how the Context Manager, Agent Framework, and Analytics Orchestrator work together.

Author: Claude Code Assistant
Created: 2025-11-07
Version: 1.0
"""

import os
import sys
import json
import time
from pathlib import Path

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

# Add current directory to path for relative imports
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

try:
    from context_manager import ContextManager, UserRole
    from agent_framework import AgentFactory, RequestRouter, AgentRequest, PermissionLevel
    from analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest
except ImportError as e:
    print(f"❌ Error importing agent modules: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(__file__)}")
    print(f"Project root: {project_root}")
    print(f"Looking for modules in: {agents_core_path}")
    print(f"Files in agents/core directory: {os.listdir(agents_core_path) if os.path.exists(agents_core_path) else 'Directory not found'}")
    print(f"Looking for agents in: {agents_path}")
    print(f"Files in agents directory: {os.listdir(agents_path) if os.path.exists(agents_path) else 'Directory not found'}")
    print("\n💡 Tip: Make sure you're running this from the correct directory structure")
    sys.exit(1)

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n--- {title} ---")

def demo_context_manager():
    """Demonstrate the Context Manager functionality (deprecated)"""
    print_header("CONTEXT MANAGER DEMONSTRATION")
    print("⚠️  WARNING: ContextManager is deprecated and will be removed on 2025-12-19")
    print("   Use direct agent instantiation instead (see WeeklyAnalysisOrchestrator pattern)")
    return

    # Initialize Context Manager (deprecated)
    cm = ContextManager()

    print_section("User Role Detection")

    # Test different user contexts
    test_contexts = [
        {
            'name': 'Beginner Analyst',
            'context': {
                'notebooks': ['starter_pack/01_intro_to_data.ipynb'],
                'models': [],
                'query_type': 'learn about college football data'
            }
        },
        {
            'name': 'Data Scientist',
            'context': {
                'notebooks': ['model_pack/06_shap_interpretability.ipynb'],
                'models': ['xgb_home_win_model_2025.pkl', 'fastai_home_win_model_2025.pkl'],
                'query_type': 'advanced feature engineering and model optimization'
            }
        },
        {
            'name': 'Production User',
            'context': {
                'models': ['ridge_model_2025.joblib'],
                'query_type': 'predict game outcomes for production use'
            }
        }
    ]

    for test_case in test_contexts:
        role = cm.detect_user_role(test_case['context'])
        print(f"  {test_case['name']}: {role.value}")

    print_section("Context Loading for Different Roles")

    # Demonstrate context loading for each role
    for role in UserRole:
        print(f"\n  {role.value.upper()} Role Context:")
        context = cm.load_context_for_role(role, test_contexts[0]['context'])

        summary = cm.get_context_summary(role)
        print(f"    Token Budget: {summary['token_budget']:,} tokens")
        print(f"    Data Scope: {summary['data_scope']}")
        print(f"    Notebooks Available: {summary['notebook_count']}")
        print(f"    Models Available: {summary['model_count']}")
        print(f"    Focus Areas: {', '.join(summary['focus_areas'])}")

    print_section("Context Performance Metrics")
    metrics = cm.get_performance_metrics()
    # Convert to JSON-serializable format
    json_metrics = {}
    for key, value in metrics.items():
        if isinstance(value, dict):
            json_metrics[key] = {str(k): v for k, v in value.items()}
        else:
            json_metrics[key] = value
    print(json.dumps(json_metrics, indent=2))

def demo_agent_framework():
    """Demonstrate the Agent Framework functionality"""
    print_header("AGENT FRAMEWORK DEMONSTRATION")

    try:
        # Import the learning navigator agent
        from agent_framework import LearningNavigatorAgent

        print_section("Agent Factory and Registration")

        # Initialize agent factory
        factory = AgentFactory()
        factory.register_agent_class(LearningNavigatorAgent, "learning_navigator")
        print("  ✓ Learning Navigator agent registered")

        # Create agent instances
        learning_agent = factory.create_agent("learning_navigator", "demo_learning_nav")
        print("  ✓ Learning Navigator agent instance created")

        print_section("Agent Capabilities")

        agent_status = learning_agent.get_status()
        for capability in agent_status['capabilities']:
            print(f"  • {capability['name']}: {capability['description']}")
            print(f"    Permission Required: Level {capability['permission_required']}")
            print(f"    Est. Execution Time: {capability['execution_time_estimate']}s")

        print_section("Agent Request Processing")

        # Create a test request
        test_request = AgentRequest(
            request_id="demo_001",
            agent_type="learning_navigator",
            action="guide_learning_path",
            parameters={"current_notebook": "start"},
            user_context={"role": "analyst", "skill_level": "beginner"},
            timestamp=time.time(),
            priority=2
        )

        print(f"  Processing request: {test_request.action}")
        response = learning_agent.execute_request(test_request, PermissionLevel.READ_EXECUTE)

        print(f"  Status: {response.status.value}")
        print(f"  Execution Time: {response.execution_time:.3f}s")
        if response.result:
            print(f"  Result: {json.dumps(response.result, indent=4)}")

        print_section("Agent Performance Metrics")
        final_status = learning_agent.get_status()
        print(json.dumps(final_status['performance_metrics'], indent=2))

    except ImportError as e:
        print(f"  ❌ Error: {e}")
        print("  Agent framework not fully available for demonstration")

def demo_analytics_orchestrator():
    """Demonstrate the Analytics Orchestrator functionality"""
    print_header("ANALYTICS ORCHESTRATOR DEMONSTRATION")

    try:
        # Initialize orchestrator
        orchestrator = AnalyticsOrchestrator()
        print("  ✓ Analytics Orchestrator initialized")

        print_section("System Status Check")
        system_status = orchestrator.get_system_status()
        print(f"  Orchestrator Status: {system_status['orchestrator']['status']}")
        print(f"  Context Manager Cache Entries: {system_status['context_manager']['cache_entries']}")
        print(f"  Active Agents: {system_status['agent_factory']['active_agents']}")
        print(f"  Total Interactions: {system_status['sessions']['total_interactions']}")

        print_section("Processing Analytics Requests")

        # Test different types of requests
        test_requests = [
            {
                'name': 'Learning Request',
                'request': AnalyticsRequest(
                    user_id="demo_user_001",
                    query="I want to learn about college football analytics",
                    query_type="learning",
                    parameters={},
                    context_hints={
                        'skill_level': 'beginner',
                        'interests': ['data_analysis', 'sports']
                    },
                    priority=2
                )
            },
            {
                'name': 'Data Exploration Request',
                'request': AnalyticsRequest(
                    user_id="demo_user_001",
                    query="Show me the dataset structure",
                    query_type="data_exploration",
                    parameters={},
                    context_hints={
                        'focus_areas': ['data_structure', 'features']
                    },
                    priority=2
                )
            },
            {
                'name': 'Advanced Analysis Request',
                'request': AnalyticsRequest(
                    user_id="demo_user_002",
                    query="Analyze team performance using advanced metrics",
                    query_type="analysis",
                    parameters={
                        'analysis_type': 'performance',
                        'focus_areas': ['efficiency', 'explosiveness']
                    },
                    context_hints={
                        'skill_level': 'advanced'
                    },
                    priority=3
                )
            }
        ]

        for test_case in test_requests:
            print(f"\n  Processing: {test_case['name']}")
            print(f"  Query: {test_case['request'].query}")

            start_time = time.time()
            response = orchestrator.process_analytics_request(test_case['request'])
            execution_time = time.time() - start_time

            print(f"  Status: {response.status}")
            print(f"  Execution Time: {execution_time:.3f}s")
            print(f"  Insights Count: {len(response.insights)}")
            print(f"  Visualizations Count: {len(response.visualizations)}")

            if response.insights:
                print("  Key Insights:")
                for insight in response.insights[:3]:  # Show first 3 insights
                    print(f"    • {insight}")

            if response.visualizations:
                print("  Visualizations:")
                for viz in response.visualizations:
                    print(f"    • {viz['type']}: {viz['title']}")

        print_section("Session Management")

        # Start a session
        session_id = orchestrator.start_session("demo_user_003", {"role": "analyst"})
        print(f"  Started session: {session_id}")

        # End the session
        session_summary = orchestrator.end_session(session_id)
        print(f"  Session Duration: {session_summary['duration']:.2f} seconds")

        print_section("Performance Summary")
        session_summary = orchestrator.get_session_summary()
        print(json.dumps(session_summary, indent=2))

    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()

def demo_integration():
    """Demonstrate the complete integrated system"""
    print_header("COMPLETE INTEGRATED SYSTEM DEMONSTRATION")

    try:
        # Initialize the complete system
        orchestrator = AnalyticsOrchestrator()
        print("  ✓ Complete system initialized")

        print_section("Interactive Analytics Session")

        # Simulate an interactive session
        user_id = "demo_session_user"
        session_id = orchestrator.start_session(user_id, {
            "role": "data_scientist",
            "skill_level": "intermediate",
            "interests": ["modeling", "predictions"]
        })

        print(f"  Started session: {session_id}")

        # Simulate a series of requests
        conversation_flow = [
            "I'm new to college football analytics, where should I start?",
            "Show me how to build team rankings using EPA",
            "I want to understand how to predict game outcomes",
            "What are the most important features for predicting wins?",
            "Can you help me analyze team efficiency metrics?"
        ]

        for i, query in enumerate(conversation_flow, 1):
            print(f"\n  Query {i}: {query}")

            request = AnalyticsRequest(
                user_id=user_id,
                query=query,
                query_type="learning" if i <= 2 else "analysis",
                parameters={},
                context_hints={
                    "conversation_turn": i,
                    "previous_queries": conversation_flow[:i-1]
                },
                priority=2
            )

            response = orchestrator.process_analytics_request(request)

            print(f"  Response: {response.status}")
            if response.insights:
                print(f"  Top Insight: {response.insights[0]}")
            print(f"  Agents Used: {response.metadata.get('agents_used', [])}")

        # End session
        session_summary = orchestrator.end_session(session_id)
        print(f"\n  Session Complete:")
        print(f"    Duration: {session_summary['duration']:.2f} seconds")
        print(f"    Interactions: {len(session_summary.get('interactions', []))}")

        print_section("Final System Performance")
        final_metrics = orchestrator.get_system_status()

        print(f"  Total Requests Processed: {final_metrics['orchestrator']['performance_metrics']['total_requests']}")
        print(f"  Success Rate: {final_metrics['orchestrator']['performance_metrics']['successful_requests'] / max(1, final_metrics['orchestrator']['performance_metrics']['total_requests']) * 100:.1f}%")
        print(f"  Average Response Time: {final_metrics['orchestrator']['performance_metrics']['average_response_time']:.3f}s")
        print(f"  Cache Hit Rate: {final_metrics['orchestrator']['performance_metrics']['cache_hit_rate']:.1f}%")

    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main demonstration function"""
    print_header("🏈 SCRIPT OHIO 2.0 - AGENT SYSTEM DEMONSTRATION")
    print("This demonstration showcases the intelligent agent architecture")
    print("that transforms college football analytics into a personalized,")
    print("automated experience.\n")

    print("Select which component to demonstrate:")
    print("1. Context Manager")
    print("2. Agent Framework")
    print("3. Analytics Orchestrator")
    print("4. Complete Integrated System")
    print("5. Run All Demonstrations")

    try:
        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == "1":
            demo_context_manager()
        elif choice == "2":
            demo_agent_framework()
        elif choice == "3":
            demo_analytics_orchestrator()
        elif choice == "4":
            demo_integration()
        elif choice == "5":
            demo_context_manager()
            demo_agent_framework()
            demo_analytics_orchestrator()
            demo_integration()
        else:
            print("Invalid choice. Running complete demonstration...")
            demo_integration()

    except KeyboardInterrupt:
        print("\n\nDemonstration interrupted by user.")
    except Exception as e:
        print(f"\n\nAn error occurred during demonstration: {e}")
        import traceback
        traceback.print_exc()

    print_header("DEMONSTRATION COMPLETE")
    print("Thank you for exploring the Script Ohio 2.0 agent architecture!")
    print("\nNext Steps:")
    print("1. Review the agent implementations in the /agents directory")
    print("2. Customize agent capabilities for your specific use cases")
    print("3. Extend the system with additional specialized agents")
    print("4. Integrate with your existing Jupyter notebooks and models")

if __name__ == "__main__":
    main()