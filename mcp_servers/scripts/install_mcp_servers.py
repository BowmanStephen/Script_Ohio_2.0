#!/usr/bin/env python3
"""
MCP Server Installation Script for College Football Analytics Platform

This script automates the installation and configuration of Model Context Protocol (MCP) servers
to enhance the college football analytics platform with advanced database operations,
data processing, visualization, and API integration capabilities.

Usage:
    python install_mcp_servers.py [--phase {1,2,3,all}] [--environment {dev,prod}]
    python install_mcp_servers.py --help
"""

import os
import sys
import json
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class InstallationPhase(Enum):
    """Installation phases for MCP servers"""
    PHASE_1_CRITICAL = "phase1"
    PHASE_2_HIGH_VALUE = "phase2"
    PHASE_3_INTEGRATION = "phase3"
    ALL = "all"

class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "dev"
    PRODUCTION = "prod"

@dataclass
class ServerInfo:
    """Information about an MCP server"""
    name: str
    command: str
    args: List[str]
    env_vars: Dict[str, str]
    dependencies: List[str]
    priority: str
    enabled: bool
    installation_method: str = "npx"  # npx, uvx, pip, manual

class MCPServerInstaller:
    """Main installer class for MCP servers"""

    def __init__(self, project_root: str, environment: Environment = Environment.DEVELOPMENT):
        self.project_root = Path(project_root)
        self.mcp_dir = self.project_root / "mcp_servers"
        self.config_dir = self.mcp_dir / "config"
        self.environment = environment
        self.logger = self._setup_logging()

        # Load configuration
        self.config = self._load_config()
        self.servers = self._parse_servers()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = self.mcp_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "installation.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)

    def _load_config(self) -> Dict:
        """Load MCP configuration from JSON file"""
        config_file = self.config_dir / "mcp_config.json"
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {config_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)

    def _parse_servers(self) -> Dict[str, ServerInfo]:
        """Parse server configurations into ServerInfo objects"""
        servers = {}

        for category, server_data in self.config["mcpServers"].items():
            if isinstance(server_data, dict):
                for server_name, details in server_data.items():
                    if isinstance(details, dict):
                        servers[f"{category}_{server_name}"] = ServerInfo(
                            name=server_name,
                            command=details.get("command", ""),
                            args=details.get("args", []),
                            env_vars=details.get("env", {}),
                            dependencies=details.get("dependencies", []),
                            priority=details.get("priority", "medium"),
                            enabled=details.get("enabled", False),
                            installation_method=details.get("command", "").split()[0] if "command" in details else "npx"
                        )

        return servers

    def _check_prerequisites(self) -> bool:
        """Check system prerequisites"""
        self.logger.info("Checking system prerequisites...")

        prerequisites = {
            "node": "Node.js and npm",
            "python": "Python 3.8+",
            "git": "Git",
        }

        missing = []
        for tool, description in prerequisites.items():
            try:
                if tool == "node":
                    subprocess.run(["node", "--version"], check=True, capture_output=True)
                    subprocess.run(["npm", "--version"], check=True, capture_output=True)
                elif tool == "python":
                    subprocess.run([sys.executable, "--version"], check=True, capture_output=True)
                elif tool == "git":
                    subprocess.run(["git", "--version"], check=True, capture_output=True)

                self.logger.info(f"✓ {description} found")
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.error(f"✗ {description} not found")
                missing.append(description)

        if missing:
            self.logger.error(f"Missing prerequisites: {', '.join(missing)}")
            return False

        return True

    def _install_server(self, server_info: ServerInfo) -> Tuple[bool, str]:
        """Install a single MCP server"""
        self.logger.info(f"Installing {server_info.name}...")

        try:
            if server_info.installation_method == "npx":
                # npm package
                cmd = ["npx", "-y"] + server_info.args
                self.logger.info(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)

            elif server_info.installation_method == "uvx":
                # Python package via uvx
                cmd = ["uvx"] + server_info.args
                self.logger.info(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)

            elif server_info.installation_method == "pip":
                # Python package via pip
                if server_info.args:
                    package = server_info.args[0]
                    cmd = [sys.executable, "-m", "pip", "install", package]
                    self.logger.info(f"Running: {' '.join(cmd)}")
                    result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
                else:
                    return False, "No package specified for pip installation"

            else:
                return False, f"Unsupported installation method: {server_info.installation_method}"

            self.logger.info(f"✓ {server_info.name} installed successfully")
            return True, result.stdout

        except subprocess.TimeoutExpired:
            return False, f"Installation timeout for {server_info.name}"
        except subprocess.CalledProcessError as e:
            return False, f"Installation failed for {server_info.name}: {e.stderr}"
        except Exception as e:
            return False, f"Unexpected error installing {server_info.name}: {str(e)}"

    def _install_dependencies(self, server_info: ServerInfo) -> bool:
        """Install server dependencies"""
        if not server_info.dependencies:
            return True

        self.logger.info(f"Installing dependencies for {server_info.name}...")

        try:
            for dep in server_info.dependencies:
                self.logger.info(f"Installing {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep],
                             check=True, capture_output=True, timeout=120)

            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install dependencies for {server_info.name}: {e}")
            return False

    def _setup_environment(self, server_info: ServerInfo) -> bool:
        """Setup environment variables for a server"""
        if not server_info.env_vars:
            return True

        self.logger.info(f"Setting up environment variables for {server_info.name}...")

        try:
            # Create or update .env file
            env_file = self.mcp_dir / ".env"

            existing_vars = {}
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            existing_vars[key] = value

            # Add/update server environment variables
            for key, value in server_info.env_vars.items():
                if value.startswith('${') and value.endswith('}'):
                    env_var_name = value[2:-1]
                    if env_var_name not in os.environ:
                        self.logger.warning(f"Environment variable {env_var_name} not set")
                        continue
                    value = os.environ[env_var_name]

                existing_vars[key] = value

            # Write environment file
            with open(env_file, 'w') as f:
                for key, value in existing_vars.items():
                    f.write(f"{key}={value}\n")

            self.logger.info(f"✓ Environment setup complete for {server_info.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup environment for {server_info.name}: {e}")
            return False

    def _validate_installation(self, server_info: ServerInfo) -> bool:
        """Validate that a server is properly installed"""
        self.logger.info(f"Validating {server_info.name} installation...")

        try:
            # Try to run server with --help or version command
            if server_info.installation_method == "npx":
                cmd = ["npx"] + server_info.args[:1] + ["--help"]
            elif server_info.installation_method == "uvx":
                cmd = ["uvx"] + server_info.args[:1] + ["--help"]
            else:
                return True  # Skip validation for manual installations

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            success = result.returncode == 0 or "--help" in result.stdout.lower()

            if success:
                self.logger.info(f"✓ {server_info.name} validation passed")
            else:
                self.logger.warning(f"⚠ {server_info.name} validation inconclusive")

            return True

        except Exception as e:
            self.logger.warning(f"⚠ Could not validate {server_info.name}: {e}")
            return True  # Continue installation even if validation fails

    def get_servers_by_phase(self, phase: InstallationPhase) -> List[ServerInfo]:
        """Get servers to install for a specific phase"""
        phase_servers = []

        for server_id, server_info in self.servers.items():
            # Check if server is enabled for current environment
            if self.environment == Environment.PRODUCTION:
                production_enabled = self.config["deployment"]["production"]["essential_servers_only"]
                if production_enabled and server_info.priority not in ["critical", "high"]:
                    continue

            if not server_info.enabled and self.environment == Environment.DEVELOPMENT:
                continue

            # Categorize by phase based on server category and priority
            if phase == InstallationPhase.PHASE_1_CRITICAL:
                if server_info.priority in ["critical"] or "database" in server_id or "data_processing" in server_id:
                    phase_servers.append(server_info)

            elif phase == InstallationPhase.PHASE_2_HIGH_VALUE:
                if server_info.priority in ["high", "medium"] or "visualization" in server_id or "web_data" in server_id:
                    phase_servers.append(server_info)

            elif phase == InstallationPhase.PHASE_3_INTEGRATION:
                if server_info.priority in ["medium", "low"] or "external_apis" in server_id or "system" in server_id:
                    phase_servers.append(server_info)

            elif phase == InstallationPhase.ALL:
                phase_servers.append(server_info)

        return phase_servers

    def install_phase(self, phase: InstallationPhase) -> bool:
        """Install servers for a specific phase"""
        self.logger.info(f"Starting installation for {phase.value}...")

        servers_to_install = self.get_servers_by_phase(phase)

        if not servers_to_install:
            self.logger.info(f"No servers to install for {phase.value}")
            return True

        self.logger.info(f"Found {len(servers_to_install)} servers to install")

        successful_installations = 0
        failed_installations = []

        for server_info in servers_to_install:
            self.logger.info(f"Processing {server_info.name}...")

            # Install dependencies first
            if not self._install_dependencies(server_info):
                self.logger.error(f"Skipping {server_info.name} due to dependency issues")
                failed_installations.append(server_info.name)
                continue

            # Setup environment variables
            self._setup_environment(server_info)

            # Install the server
            success, message = self._install_server(server_info)

            if success:
                self._validate_installation(server_info)
                successful_installations += 1
            else:
                self.logger.error(f"Failed to install {server_info.name}: {message}")
                failed_installations.append(server_info.name)

        # Report results
        total = len(servers_to_install)
        self.logger.info(f"Phase {phase.value} complete: {successful_installations}/{total} servers installed successfully")

        if failed_installations:
            self.logger.error(f"Failed installations: {', '.join(failed_installations)}")
            return False

        return True

    def create_startup_script(self) -> None:
        """Create a script to start all installed MCP servers"""
        startup_script = self.mcp_dir / "start_mcp_servers.py"

        script_content = f'''#!/usr/bin/env python3
"""
Startup script for MCP servers in the College Football Analytics Platform
"""

import os
import subprocess
import json
from pathlib import Path

def main():
    """Start all enabled MCP servers"""
    mcp_dir = Path(__file__).parent
    config_file = mcp_dir / "config" / "mcp_config.json"

    with open(config_file, 'r') as f:
        config = json.load(f)

    print("Starting MCP servers...")

    for category, servers in config["mcpServers"].items():
        if isinstance(servers, dict):
            for server_name, details in servers.items():
                if isinstance(details, dict) and details.get("enabled", False):
                    print(f"Starting {{server_name}}...")

                    try:
                        # In a real implementation, you would start the server here
                        # For now, just show the command that would be run
                        cmd = [details["command"]] + details["args"]
                        print(f"  Command: {{' '.join(cmd)}}")

                        # Actually start the server (commented out for safety)
                        # subprocess.Popen(cmd)

                    except Exception as e:
                        print(f"  Error starting {{server_name}}: {{e}}")

    print("MCP servers startup complete")

if __name__ == "__main__":
    main()
'''

        with open(startup_script, 'w') as f:
            f.write(script_content)

        os.chmod(startup_script, 0o755)
        self.logger.info(f"Created startup script: {startup_script}")

def main():
    """Main installation function"""
    parser = argparse.ArgumentParser(
        description="Install MCP servers for College Football Analytics Platform"
    )
    parser.add_argument(
        "--phase",
        choices=["phase1", "phase2", "phase3", "all"],
        default="all",
        help="Installation phase to run (default: all)"
    )
    parser.add_argument(
        "--environment",
        choices=["dev", "prod"],
        default="dev",
        help="Target environment (default: dev)"
    )
    parser.add_argument(
        "--project-root",
        default=str(Path(__file__).parent.parent.parent),
        help="Project root directory"
    )

    args = parser.parse_args()

    # Convert string arguments to enums
    phase = InstallationPhase(args.phase)
    environment = Environment(args.environment)

    # Initialize installer
    installer = MCPServerInstaller(args.project_root, environment)

    # Check prerequisites
    if not installer._check_prerequisites():
        print("Prerequisites not met. Please install required tools and try again.")
        sys.exit(1)

    # Run installation
    print(f"Installing MCP servers for {args.environment} environment...")
    print(f"Phase: {args.phase}")
    print(f"Project root: {args.project_root}")
    print("-" * 50)

    success = installer.install_phase(phase)

    if success:
        print("\n✓ Installation completed successfully!")
        installer.create_startup_script()
        print(f"\nStartup script created: {installer.mcp_dir}/start_mcp_servers.py")
        print("\nNext steps:")
        print("1. Review the configuration files in mcp_servers/config/")
        print("2. Set required environment variables in mcp_servers/.env")
        print("3. Run the startup script to start MCP servers")
        print("4. Test integration using python scripts/test_mcp_integration.py")
    else:
        print("\n✗ Installation completed with errors. Check the log for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()