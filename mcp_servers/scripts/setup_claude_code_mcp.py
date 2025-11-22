#!/usr/bin/env python3
"""
Claude Code MCP Setup Script

This script configures MCP servers for use with Claude Code CLI, ensuring all the
enhanced analytics capabilities are available directly in your Claude Code sessions.

Usage:
    python setup_claude_code_mcp.py [--install] [--validate] [--help]
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import logging

class ClaudeCodeMCPSetup:
    """Setup and configure MCP servers for Claude Code CLI"""

    def __init__(self, project_root: str = None):
        """Initialize the setup process"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)

        self.mcp_dir = self.project_root / "mcp_servers"
        self.config_dir = self.mcp_dir / "config"

        # Claude Code configuration paths
        self.claude_config_dir = Path.home() / ".claude"
        self.claude_config_file = self.claude_config_dir / "claude_desktop_config.json"

        # Setup logging
        self.logger = self._setup_logging()

        self.logger.info("Claude Code MCP Setup initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the setup process"""
        log_dir = self.mcp_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - Claude-Setup - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "claude_setup.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)

    def validate_prerequisites(self) -> bool:
        """Validate that prerequisites are met"""
        self.logger.info("Validating prerequisites...")

        prerequisites = {
            "node": "Node.js",
            "python": "Python 3.8+",
            "claude_code": "Claude Code CLI"
        }

        all_good = True

        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"✓ {result.stdout.strip()}")
            else:
                self.logger.error("✗ Node.js not found")
                all_good = False
        except FileNotFoundError:
            self.logger.error("✗ Node.js not found")
            all_good = False

        # Check Python
        try:
            result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"✓ {result.stdout.strip()}")
            else:
                self.logger.error("✗ Python not found")
                all_good = False
        except Exception as e:
            self.logger.error(f"✗ Python error: {e}")
            all_good = False

        # Check Claude Code CLI
        try:
            result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"✓ Claude Code CLI {result.stdout.strip()}")
            else:
                self.logger.warning("⚠ Claude Code CLI not found or not in PATH")
                all_good = False
        except FileNotFoundError:
            self.logger.warning("⚠ Claude Code CLI not found or not in PATH")
            all_good = False

        return all_good

    def create_claude_config_directory(self) -> bool:
        """Create Claude configuration directory"""
        try:
            self.claude_config_dir.mkdir(exist_ok=True)
            self.logger.info(f"✓ Claude config directory: {self.claude_config_dir}")
            return True
        except Exception as e:
            self.logger.error(f"✗ Failed to create Claude config directory: {e}")
            return False

    def generate_claude_config(self) -> Dict:
        """Generate Claude configuration with MCP servers"""
        self.logger.info("Generating Claude configuration...")

        # Load MCP configuration
        mcp_config_file = self.config_dir / "mcp_config.json"
        if not mcp_config_file.exists():
            self.logger.error(f"MCP configuration file not found: {mcp_config_file}")
            return {}

        try:
            with open(mcp_config_file, 'r') as f:
                mcp_config = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load MCP configuration: {e}")
            return {}

        # Convert MCP configuration to Claude format
        claude_config = {
            "mcpServers": {},
            "systemPrompts": [
                "You are an expert college football analyst with access to advanced analytics tools including database queries, data processing, and visualization capabilities.",
                "When analyzing football data, always consider context like opponent strength, injuries, weather conditions, and historical performance.",
                "Use database tools to query game results, team statistics, and player performance data.",
                "Leverage data processing tools to clean, transform, and analyze football datasets.",
                "Create visualizations using chart generation tools to present insights effectively.",
                "Store important analysis results in memory for future reference and context building.",
                "When working with the College Football Analytics Platform, you have access to:",
                "  - Historical game data (1869-present)",
                "  - Current season data with real-time updates",
                "  - Advanced metrics (EPA, success rates, explosiveness)",
                "  - Machine learning models for predictions",
                "  - Educational notebooks and tutorials",
                "Always provide actionable insights and back up your analysis with data."
            ]
        }

        # Add enabled MCP servers
        for category, servers in mcp_config.get("mcpServers", {}).items():
            if isinstance(servers, dict):
                for server_name, server_config in servers.items():
                    if isinstance(server_config, dict) and server_config.get("enabled", False):
                        # Create Claude-friendly server name
                        claude_server_name = f"{category}_{server_name}"

                        # Build server configuration
                        server_entry = {
                            "command": server_config.get("command", ""),
                            "args": server_config.get("args", [])
                        }

                        # Add environment variables if present
                        if server_config.get("env"):
                            server_entry["env"] = server_config["env"]

                        # Add description
                        description = server_config.get("description", f"{claude_server_name} MCP server")
                        server_entry["description"] = description

                        claude_config["mcpServers"][claude_server_name] = server_entry

        self.logger.info(f"Generated configuration with {len(claude_config['mcpServers'])} MCP servers")
        return claude_config

    def install_claude_config(self, config: Dict) -> bool:
        """Install Claude configuration"""
        try:
            # Backup existing configuration
            if self.claude_config_file.exists():
                backup_file = self.claude_config_file.with_suffix('.json.backup')
                shutil.copy2(self.claude_config_file, backup_file)
                self.logger.info(f"✓ Backed up existing configuration to {backup_file}")

            # Write new configuration
            with open(self.claude_config_file, 'w') as f:
                json.dump(config, f, indent=2)

            self.logger.info(f"✓ Claude configuration installed: {self.claude_config_file}")
            return True

        except Exception as e:
            self.logger.error(f"✗ Failed to install Claude configuration: {e}")
            return False

    def create_environment_file(self) -> bool:
        """Create environment file with required variables"""
        env_file = self.mcp_dir / ".env"

        env_content = """# Claude Code MCP Environment Variables
# Fill in your actual values for the variables below

# Database Configuration
POSTGRES_PASSWORD=your_postgres_password_here
POSTGRES_USER=postgres
POSTGRES_DB=college_football

# External API Keys (Optional but recommended)
GITHUB_TOKEN=your_github_personal_access_token_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Google Integration (Optional)
GOOGLE_CREDS_FILE=/path/to/your/google_credentials.json

# Claude Code Settings
MCP_LOG_LEVEL=info
MCP_TIMEOUT=30000
MCP_CACHE_DURATION=3600
"""

        try:
            with open(env_file, 'w') as f:
                f.write(env_content)

            self.logger.info(f"✓ Environment file created: {env_file}")
            self.logger.info("⚠ Please edit the .env file with your actual credentials")
            return True

        except Exception as e:
            self.logger.error(f"✗ Failed to create environment file: {e}")
            return False

    def install_mcp_servers(self) -> bool:
        """Install required MCP servers"""
        self.logger.info("Installing MCP servers...")

        # Run the installation script
        install_script = self.mcp_dir / "scripts" / "install_mcp_servers.py"

        if not install_script.exists():
            self.logger.error(f"Installation script not found: {install_script}")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(install_script), "--phase", "phase1"],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            if result.returncode == 0:
                self.logger.info("✓ Phase 1 MCP servers installed successfully")
                return True
            else:
                self.logger.error(f"✗ MCP server installation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("✗ MCP server installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"✗ Error during MCP server installation: {e}")
            return False

    def validate_setup(self) -> Dict[str, bool]:
        """Validate the setup and report status"""
        self.logger.info("Validating Claude Code MCP setup...")

        validation_results = {}

        # Check configuration file exists
        validation_results["config_exists"] = self.claude_config_file.exists()

        # Check configuration is valid JSON
        if validation_results["config_exists"]:
            try:
                with open(self.claude_config_file, 'r') as f:
                    json.load(f)
                validation_results["config_valid"] = True
            except:
                validation_results["config_valid"] = False
        else:
            validation_results["config_valid"] = False

        # Check environment file exists
        env_file = self.mcp_dir / ".env"
        validation_results["env_file_exists"] = env_file.exists()

        # Check for placeholder values in environment file
        if validation_results["env_file_exists"]:
            try:
                with open(env_file, 'r') as f:
                    env_content = f.read()

                # Check if placeholder values are still present
                placeholders_found = any(placeholder in env_content for placeholder in [
                    "your_postgres_password_here",
                    "your_github_personal_access_token_here",
                    "your_firecrawl_api_key_here"
                ])
                validation_results["env_configured"] = not placeholders_found
            except:
                validation_results["env_configured"] = False
        else:
            validation_results["env_configured"] = False

        # Test some MCP server connectivity
        validation_results["mcp_connectivity"] = self._test_mcp_connectivity()

        # Check Claude Code can access configuration
        validation_results["claude_access"] = self._test_claude_access()

        return validation_results

    def _test_mcp_connectivity(self) -> bool:
        """Test basic MCP server connectivity"""
        try:
            # Try to run a simple connectivity test
            test_script = self.mcp_dir / "scripts" / "test_mcp_integration.py"
            if test_script.exists():
                result = subprocess.run(
                    [sys.executable, str(test_script), "--category", "system"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return result.returncode == 0
            return False
        except:
            return False

    def _test_claude_access(self) -> bool:
        """Test if Claude Code can access the configuration"""
        try:
            # Try to run Claude Code with a simple command
            result = subprocess.run(
                ["claude", "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except:
            return False

    def print_setup_status(self, validation_results: Dict[str, bool]):
        """Print setup status with clear indicators"""
        print("\n" + "="*60)
        print("CLAUDE CODE MCP SETUP STATUS")
        print("="*60)

        status_items = [
            ("Configuration File", validation_results["config_exists"],
             "✅ Created" if validation_results["config_exists"] else "❌ Missing"),
            ("Configuration Valid", validation_results["config_valid"],
             "✅ Valid JSON" if validation_results["config_valid"] else "❌ Invalid JSON"),
            ("Environment File", validation_results["env_file_exists"],
             "✅ Created" if validation_results["env_file_exists"] else "❌ Missing"),
            ("Environment Configured", validation_results["env_configured"],
             "✅ Configured" if validation_results["env_configured"] else "⚠️ Needs configuration"),
            ("MCP Connectivity", validation_results["mcp_connectivity"],
             "✅ Connected" if validation_results["mcp_connectivity"] else "❌ Not connected"),
            ("Claude Code Access", validation_results["claude_access"],
             "✅ Available" if validation_results["claude_access"] else "❌ Not found")
        ]

        for name, status, indicator in status_items:
            print(f"{indicator:<25} {name}")

        print("\n" + "="*60)

        # Overall status
        all_critical = all([
            validation_results["config_exists"],
            validation_results["config_valid"],
            validation_results["env_file_exists"],
            validation_results["claude_access"]
        ])

        if all_critical:
            print("🎉 SETUP COMPLETE! Your MCP servers are ready for Claude Code.")
        else:
            print("⚠️  SETUP INCOMPLETE. Please address the issues above.")

        print("\nNext Steps:")
        print("1. Restart Claude Code to load the new configuration")
        print("2. Test the MCP servers with: 'claude --help'")
        print("3. Start using enhanced analytics capabilities in Claude Code")

    def create_usage_examples(self) -> bool:
        """Create usage examples file"""
        examples_file = self.mcp_dir / "docs" / "CLAUDE_CODE_USAGE_EXAMPLES.md"

        content = """# Claude Code MCP Usage Examples

This document provides examples of how to use the enhanced MCP capabilities with Claude Code for college football analytics.

## Database Operations

### Query Team Performance
```
Using the database tools, show me the top 10 teams by points scored in the 2025 season.
```

### Analyze Head-to-Head Records
```
Query the database for all games between Ohio State and Michigan since 2010, and show me their win-loss record.
```

## Data Processing

### Advanced Metrics Calculation
```
Process the game data to calculate EPA (Expected Points Added) for each team's offensive plays this season.
```

### Data Cleaning and Validation
```
Clean the current season data by removing duplicate games and validating score ranges.
```

## Visualization

### Create Performance Charts
```
Generate a bar chart showing the top 15 teams by scoring average this season.
```

### Season Trends Visualization
```
Create a line chart showing the scoring trends for the Big Ten conference over the last 5 seasons.
```

## Advanced Analytics

### Machine Learning Predictions
```
Using the historical data, create a prediction model for this week's games and show me the most confident predictions.
```

### Statistical Analysis
```
Perform a regression analysis on team performance metrics to identify key factors for winning games.
```

## Memory and Context

### Store Insights
```
Remember that Ohio State's offense has been averaging 45 points per game over their last 5 games.
```

### Retrieve Stored Analysis
```
What insights have we stored about the Big Ten championship race?
```

## File Operations

### Analyze Notebooks
```
Review the model_pack notebooks and summarize which machine learning techniques perform best for game predictions.
```

### Export Analysis Results
```
Save our team performance analysis to a CSV file for external reporting.
```

## Integration Examples

### Multi-Step Analysis
```
1. Query the database for all games from week 10 of the 2025 season
2. Process this data to calculate team efficiency metrics
3. Create visualizations comparing offensive vs defensive performance
4. Store the key findings in memory for future reference
```

### Real-time Updates
```
Using web scraping, find any recent injury reports or news that might affect this week's games, and update our predictions accordingly.
```

## Best Practices

1. **Always cite your data sources** when providing statistics
2. **Consider context** like weather conditions, injuries, and travel
3. **Use multiple data sources** for comprehensive analysis
4. **Store important insights** in memory for building context over time
5. **Create visualizations** to make complex data more understandable
6. **Validate your findings** with historical data when possible

## Troubleshooting

If MCP servers aren't responding:
1. Check that the configuration file is properly set up
2. Ensure all environment variables are configured
3. Restart Claude Code to reload the configuration
4. Run the test script: `python scripts/test_mcp_integration.py`

For more help, check the documentation in the `docs/` directory.
"""

        try:
            examples_file.parent.mkdir(exist_ok=True)
            with open(examples_file, 'w') as f:
                f.write(content)
            self.logger.info(f"✓ Usage examples created: {examples_file}")
            return True
        except Exception as e:
            self.logger.error(f"✗ Failed to create usage examples: {e}")
            return False

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(
        description="Setup MCP servers for Claude Code CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_claude_code_mcp.py --install    # Full installation
  python setup_claude_code_mcp.py --validate   # Validate existing setup
  python setup_claude_code_mcp.py              # Default: validate setup
        """
    )

    parser.add_argument(
        "--install",
        action="store_true",
        help="Install and configure MCP servers for Claude Code"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate existing Claude Code MCP setup"
    )
    parser.add_argument(
        "--project-root",
        help="Project root directory (default: auto-detect)"
    )

    args = parser.parse_args()

    # Initialize setup
    setup = ClaudeCodeMCPSetup(args.project_root)

    print("🔧 Claude Code MCP Setup")
    print("="*40)

    # Validate prerequisites
    if not setup.validate_prerequisites():
        print("\n❌ Prerequisites not met. Please install required software:")
        print("- Node.js (v16+)")
        print("- Python (v3.8+)")
        print("- Claude Code CLI")
        return 1

    if args.install:
        print("\n📦 Installing MCP servers...")

        # Create configuration directory
        if not setup.create_claude_config_directory():
            return 1

        # Install MCP servers
        if not setup.install_mcp_servers():
            print("⚠️  Some MCP servers failed to install. Continuing with setup...")

        # Generate and install Claude configuration
        claude_config = setup.generate_claude_config()
        if not claude_config:
            print("❌ Failed to generate Claude configuration")
            return 1

        if not setup.install_claude_config(claude_config):
            print("❌ Failed to install Claude configuration")
            return 1

        # Create environment file
        setup.create_environment_file()

        # Create usage examples
        setup.create_usage_examples()

        print("\n✅ Installation completed!")

    # Validate setup
    print("\n🔍 Validating setup...")
    validation_results = setup.validate_setup()
    setup.print_setup_status(validation_results)

    # Return success if critical components are working
    all_critical = all([
        validation_results["config_exists"],
        validation_results["config_valid"],
        validation_results["env_file_exists"],
        validation_results["claude_access"]
    ])

    return 0 if all_critical else 1

if __name__ == "__main__":
    sys.exit(main())