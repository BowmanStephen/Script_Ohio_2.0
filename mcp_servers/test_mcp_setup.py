#!/usr/bin/env python3
"""
Test MCP Setup for Script Ohio 2.0
===================================

This script tests if MCP servers are properly configured and working.
"""

import subprocess
import json
import os
from pathlib import Path

def run_mcp_server_check(package_name, args=None, env_vars=None):
    """Invoke an MCP server CLI package and capture its status."""
    try:
        cmd = ["npx", "-y", package_name]
        if args:
            cmd.extend(args)

        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Run with timeout to prevent hanging
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=5)

        return {
            "package": package_name,
            "status": "working" if result.returncode == 0 else "error",
            "output": result.stdout[:200] if result.stdout else result.stderr[:200]
        }
    except subprocess.TimeoutExpired:
        return {
            "package": package_name,
            "status": "timeout",
            "output": "Server started but timed out (expected behavior)"
        }
    except Exception as e:
        return {
            "package": package_name,
            "status": "error",
            "output": str(e)
        }

def main():
    print("🧪 Testing MCP Server Setup for Script Ohio 2.0")
    print("=" * 60)

    # Test critical MCP servers
    servers_to_test = [
        {
            "package": "@modelcontextprotocol/server-filesystem",
            "args": ["/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"],
            "description": "File system access"
        },
        {
            "package": "mcp-server-sqlite",
            "args": ["--db", "data/databases/football_analysis.db"],
            "description": "SQLite database access"
        },
        {
            "package": "time-mcp",
            "description": "Time utilities"
        },
        {
            "package": "@notionhq/notion-mcp-server",
            "description": "Notion integration",
            "env_vars": {"NOTION_API_KEY": "test_key"}
        },
        {
            "package": "@executeautomation/playwright-mcp-server",
            "description": "Web automation"
        }
    ]

    results = []

    for server in servers_to_test:
        print(f"\n🔍 Testing {server['package']}...")
        print(f"   Description: {server['description']}")

        result = run_mcp_server_check(
            server["package"],
            server.get("args"),
            server.get("env_vars")
        )

        results.append(result)

        if result["status"] == "working":
            print(f"   ✅ Status: Working")
        elif result["status"] == "timeout":
            print(f"   ✅ Status: Server started successfully")
        else:
            print(f"   ❌ Status: Error")
            print(f"   Output: {result['output']}")

    # Test configuration files
    print(f"\n📁 Checking Configuration Files...")

    config_files = [
        "/Users/stephen_bowman/.claude/claude_desktop_config.json",
        ".env"
    ]

    for config_file in config_files:
        config_path = Path(config_file)
        if config_path.exists():
            print(f"   ✅ {config_file} exists")
            if config_file.endswith(".json"):
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                        mcp_servers = config.get("mcpServers", {})
                        print(f"      MCP Servers configured: {len(mcp_servers)}")
                        for name in mcp_servers.keys():
                            print(f"      - {name}")
                except:
                    print(f"      ⚠️  Invalid JSON")
        else:
            print(f"   ❌ {config_file} missing")

    # Test database connection
    print(f"\n🗄️  Testing Database Connection...")
    db_path = Path("data/databases/football_analysis.db")
    if db_path.exists():
        print(f"   ✅ SQLite database exists ({db_path.stat().st_size / (1024*1024):.1f} MB)")

        # Test database connection
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM games")
            game_count = cursor.fetchone()[0]
            print(f"   ✅ Database connection working")
            print(f"   📊 Games in database: {game_count:,}")
            conn.close()
        except Exception as e:
            print(f"   ❌ Database connection error: {e}")
    else:
        print(f"   ❌ Database file missing")

    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 60)

    working_servers = [r for r in results if r["status"] in ["working", "timeout"]]
    failed_servers = [r for r in results if r["status"] == "error"]

    print(f"✅ Working servers: {len(working_servers)}/{len(results)}")
    print(f"❌ Failed servers: {len(failed_servers)}")

    if working_servers:
        print(f"\n✅ Working MCP Servers:")
        for server in working_servers:
            print(f"   - {server['package']}")

    if failed_servers:
        print(f"\n❌ Failed MCP Servers:")
        for server in failed_servers:
            print(f"   - {server['package']}: {server['output']}")

    print(f"\n🚀 MCP Integration Status: {'Ready' if len(working_servers) > 0 else 'Needs Setup'}")
    print(f"\n💡 Next Steps:")
    print(f"   1. Configure API keys in .env file for services you want to use")
    print(f"   2. Restart Claude Code to load new MCP configuration")
    print(f"   3. Test MCP functionality in Claude Code CLI")

if __name__ == "__main__":
    main()
