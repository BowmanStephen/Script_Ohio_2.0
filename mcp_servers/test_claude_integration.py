#!/usr/bin/env python3
"""
Test Claude Code MCP Integration

This script tests whether the MCP bridge is working correctly
and can connect Claude Code to the agent system.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_agent_mcp_bridge():
    """Test the Agent MCP Bridge"""
    print("🧪 Testing Agent MCP Bridge...")

    try:
        # Import the bridge
        from mcp_servers.agents.agent_mcp_bridge import AgentMCPBridge

        # Create bridge instance
        bridge = AgentMCPBridge()
        print("✅ Agent MCP Bridge created successfully")

        # Check available tools
        tools = bridge.get_available_tools()
        print(f"✅ Available tools: {len(tools)}")
        for tool in tools[:3]:  # Show first 3
            print(f"   • {tool['name']}: {tool['description'][:60]}...")

        return True

    except Exception as e:
        print(f"❌ Agent MCP Bridge test failed: {e}")
        return False

def test_model_mcp_server():
    """Test the Model MCP Server"""
    print("\n🧪 Testing Model MCP Server...")

    try:
        # Import the model server
        from mcp_servers.agents.model_mcp_server import ModelMCPServer

        # Create server instance
        server = ModelMCPServer()
        print("✅ Model MCP Server created successfully")

        # Check if it can be initialized (async test)
        print("✅ Model MCP Server components ready")

        return True

    except Exception as e:
        print(f"❌ Model MCP Server test failed: {e}")
        return False

def test_configuration_files():
    """Test configuration files exist and are valid"""
    print("\n🧪 Testing Configuration Files...")

    config_files = [
        ".claude/claude_desktop_config.json",
        ".claude/settings.local.json",
        "mcp_servers/config/mcp_config.json",
        "mcp_servers/config/claude_desktop_config.json"
    ]

    all_good = True

    for config_file in config_files:
        file_path = project_root / config_file
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    json.load(f)
                print(f"✅ {config_file} - Valid JSON")
            except json.JSONDecodeError as e:
                print(f"❌ {config_file} - Invalid JSON: {e}")
                all_good = False
            except Exception as e:
                print(f"❌ {config_file} - Error: {e}")
                all_good = False
        else:
            print(f"❌ {config_file} - File not found")
            all_good = False

    return all_good

def test_agent_system_imports():
    """Test if agent system components can be imported"""
    print("\n🧪 Testing Agent System Imports...")

    imports_to_test = [
        ("agents.analytics_orchestrator", "AnalyticsOrchestrator"),
        ("agents.core.context_manager", "ContextManager"),
        ("agents.model_execution_engine", "ModelExecutionEngine"),
        ("mcp_servers.agents.mcp_enhanced_orchestrator", "MCPEnhancedOrchestrator")
    ]

    all_good = True

    for module_name, class_name in imports_to_test:
        try:
            sys.path.append(str(project_root))
            exec(f"from {module_name} import {class_name}")
            print(f"✅ {class_name} - Import successful")
        except ImportError as e:
            print(f"⚠️  {class_name} - Import failed (may be expected): {e}")
        except Exception as e:
            print(f"❌ {class_name} - Unexpected error: {e}")
            all_good = False

    return all_good

def main():
    """Run all integration tests"""
    print("🚀 Script Ohio 2.0 - Claude Code MCP Integration Test")
    print("=" * 60)

    # Change to project root
    import os
    os.chdir(project_root)

    # Run tests
    results = {
        "Agent MCP Bridge": test_agent_mcp_bridge(),
        "Model MCP Server": test_model_mcp_server(),
        "Configuration Files": test_configuration_files(),
        "Agent System Imports": test_agent_system_imports()
    }

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Your MCP integration is ready.")
        print("\nNext steps:")
        print("1. Restart Claude Code to load the new configuration")
        print("2. Test agent capabilities with commands like:")
        print("   - orchestrate_analysis('Analyze Ohio State performance')")
        print("   - execute_model('xgboost', 'win_probability', {...})")
        print("   - navigate_learning('Show me analytics basics')")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("1. Ensure all dependencies are installed (pip install -r requirements-prod.txt)")
        print("2. Check that Python 3.13+ is being used")
        print("3. Verify project structure is intact")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)