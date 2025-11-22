#!/usr/bin/env python3
"""
MCP Server Startup Script for Script Ohio 2.0
============================================

This script starts all configured MCP servers for the college football analytics platform.
It handles server initialization, health checks, and graceful shutdown.

Usage:
    python start_mcp_servers.py [--servers all|database|processing|visualization] [--debug]
"""

import os
import sys
import json
import time
import signal
import logging
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

class MCPServerManager:
    """Manages startup and shutdown of MCP servers"""

    def __init__(self, config_path: str = "config/mcp_config.json"):
        self.config_path = Path(config_path)
        self.servers: Dict[str, subprocess.Popen] = {}
        self.server_configs: Dict[str, Any] = {}
        self.setup_logging()
        self.load_config()

    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"mcp_servers_{timestamp}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("MCPServerManager")

    def load_config(self):
        """Load MCP server configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.server_configs = config.get('mcpServers', {})
                self.global_config = config.get('global', {})
                self.logger.info(f"Loaded configuration for {len(self.server_configs)} servers")
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration: {e}")
            sys.exit(1)

    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met"""
        self.logger.info("Checking prerequisites...")

        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"Node.js version: {result.stdout.strip()}")
            else:
                self.logger.error("Node.js not found. Please install Node.js.")
                return False
        except FileNotFoundError:
            self.logger.error("Node.js not found. Please install Node.js.")
            return False

        # Check NPM
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"NPM version: {result.stdout.strip()}")
            else:
                self.logger.error("NPM not found. Please install NPM.")
                return False
        except FileNotFoundError:
            self.logger.error("NPM not found. Please install NPM.")
            return False

        # Check Python dependencies
        required_packages = ['pandas', 'numpy', 'scipy']
        for package in required_packages:
            try:
                __import__(package)
                self.logger.info(f"✅ Python package {package} found")
            except ImportError:
                self.logger.error(f"❌ Python package {package} not found. Install with: pip install {package}")
                return False

        # Check if MCP packages are installed
        mcp_packages = [
            '@modelcontextprotocol/server-postgres',
            'mcp-server-sqlite',
            '@mcp-toolbox/databases',
            'mcp-server-pandas',
            '@modelcontextprotocol/server-csv-editor',
            '@modelcontextprotocol/server-echarts',
            'mcp-server-datawrapper',
            '@modelcontextprotocol/server-quickchart',
            '@modelcontextprotocol/server-filesystem',
            '@modelcontextprotocol/server-memory',
            '@modelcontextprotocol/server-fetch',
            '@modelcontextprotocol/server-github'
        ]

        missing_packages = []
        for package in mcp_packages:
            try:
                result = subprocess.run(['npm', 'list', '-g', package], capture_output=True, text=True)
                if result.returncode == 0:
                    self.logger.info(f"✅ MCP package {package} installed")
                else:
                    missing_packages.append(package)
            except:
                missing_packages.append(package)

        if missing_packages:
            self.logger.warning(f"⚠️  Missing MCP packages: {missing_packages}")
            self.logger.info("Install missing packages with: npm install -g " + " ".join(missing_packages))

        return True

    def start_server(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Start a single MCP server"""
        try:
            cmd = server_config.get('command', [])
            if not cmd:
                self.logger.warning(f"No command specified for server {server_name}")
                return False

            # Add environment variables
            env = os.environ.copy()
            env_vars = server_config.get('env', {})
            for key, value in env_vars.items():
                env[key] = value

            self.logger.info(f"Starting server: {server_name}")
            self.logger.debug(f"Command: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.servers[server_name] = process

            # Wait a moment and check if process is still running
            time.sleep(2)
            if process.poll() is None:
                self.logger.info(f"✅ Server {server_name} started successfully (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                self.logger.error(f"❌ Server {server_name} failed to start")
                self.logger.error(f"STDOUT: {stdout}")
                self.logger.error(f"STDERR: {stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to start server {server_name}: {e}")
            return False

    def start_servers(self, server_filter: str = "all"):
        """Start MCP servers based on filter"""
        if not self.check_prerequisites():
            self.logger.error("Prerequisites not met. Exiting.")
            return False

        # Define server categories
        categories = {
            "database": ["mcp-postgres", "mcp-sqlite", "mcp-databases"],
            "processing": ["mcp-pandas", "mcp-csv-editor"],
            "visualization": ["mcp-echarts", "mcp-datawrapper", "mcp-quickchart"],
            "system": ["mcp-filesystem", "mcp-memory"],
            "web": ["mcp-fetch", "mcp-github"]
        }

        servers_to_start = []
        if server_filter == "all":
            servers_to_start = list(self.server_configs.keys())
        elif server_filter in categories:
            servers_to_start = [s for s in categories[server_filter] if s in self.server_configs]
        else:
            # Assume it's a specific server name
            servers_to_start = [server_filter] if server_filter in self.server_configs else []

        self.logger.info(f"Starting {len(servers_to_start)} servers: {servers_to_start}")

        success_count = 0
        for server_name in servers_to_start:
            if server_name in self.server_configs:
                if self.start_server(server_name, self.server_configs[server_name]):
                    success_count += 1
            else:
                self.logger.warning(f"Server configuration not found: {server_name}")

        self.logger.info(f"Successfully started {success_count}/{len(servers_to_start)} servers")
        return success_count > 0

    def stop_servers(self):
        """Gracefully stop all running servers"""
        self.logger.info("Stopping MCP servers...")

        for server_name, process in self.servers.items():
            try:
                if process.poll() is None:  # Process is still running
                    self.logger.info(f"Stopping server: {server_name}")
                    process.terminate()

                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                        self.logger.info(f"✅ Server {server_name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        self.logger.warning(f"Force killing server: {server_name}")
                        process.kill()
                        process.wait()
                        self.logger.info(f"✅ Server {server_name} force killed")

            except Exception as e:
                self.logger.error(f"Error stopping server {server_name}: {e}")

        self.servers.clear()

    def monitor_servers(self):
        """Monitor running servers and restart if needed"""
        self.logger.info("Starting server monitoring...")

        try:
            while True:
                time.sleep(30)  # Check every 30 seconds

                for server_name, process in list(self.servers.items()):
                    if process.poll() is not None:  # Process has died
                        self.logger.warning(f"Server {server_name} has died, attempting restart...")
                        stdout, stderr = process.communicate()
                        self.logger.debug(f"Process output: {stdout}")
                        self.logger.debug(f"Process error: {stderr}")

                        # Restart the server
                        if server_name in self.server_configs:
                            if self.start_server(server_name, self.server_configs[server_name]):
                                self.logger.info(f"✅ Server {server_name} restarted successfully")
                            else:
                                self.logger.error(f"❌ Failed to restart server {server_name}")

        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")

    def print_status(self):
        """Print status of all servers"""
        print("\n" + "="*60)
        print("MCP SERVER STATUS")
        print("="*60)

        for server_name, process in self.servers.items():
            if process.poll() is None:
                print(f"✅ {server_name:20} | RUNNING  | PID: {process.pid}")
            else:
                print(f"❌ {server_name:20} | STOPPED  | Exit code: {process.returncode}")

        print("="*60)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal, stopping servers...")
    if 'manager' in globals():
        manager.stop_servers()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Start MCP servers for Script Ohio 2.0")
    parser.add_argument(
        "--servers",
        choices=["all", "database", "processing", "visualization", "system", "web"],
        default="all",
        help="Which servers to start (default: all)"
    )
    parser.add_argument("--monitor", action="store_true", help="Monitor servers and restart if needed")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--status", action="store_true", help="Show server status and exit")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    global manager
    manager = MCPServerManager()

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.status:
        manager.print_status()
        return

    # Start servers
    if manager.start_servers(args.servers):
        print(f"\n🚀 MCP servers started successfully!")

        if args.monitor:
            manager.monitor_servers()
        else:
            manager.print_status()
            print("\nPress Ctrl+C to stop servers...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    else:
        print("\n❌ Failed to start MCP servers")
        sys.exit(1)

    # Cleanup
    manager.stop_servers()

if __name__ == "__main__":
    main()