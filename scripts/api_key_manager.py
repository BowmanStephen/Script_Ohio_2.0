#!/usr/bin/env python3
"""
Comprehensive CFBD API Key Management System
Ensures API key is available across all contexts and provides validation
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class APIKeyManager:
    """Manages CFBD API key across multiple contexts and provides validation"""

    def __init__(self):
        self.project_dir = Path(
            "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"
        )
        # Read API key from environment variable - no hardcoding!
        self.api_key = os.environ.get("CFBD_API_KEY")
        self.env_file = self.project_dir / ".env"
        self.zshrc_file = Path.home() / ".zshrc"
        self.claude_settings = self.project_dir / ".claude" / "settings.json"

    def get_api_key_interactive(self) -> str:
        """Get API key from user input if not in environment"""
        if not self.api_key:
            print("🏈 CFBD API Key not found in environment variables")
            print("Get your free API key at: https://collegefootballdata.com/")
            self.api_key = input("Enter your CFBD API key: ").strip()
            if not self.api_key:
                print("❌ No API key provided")
                sys.exit(1)
            # Set in environment for this session
            os.environ["CFBD_API_KEY"] = self.api_key
        return self.api_key

    def ensure_api_key_everywhere(self) -> Dict[str, bool]:
        """Ensure API key is set in all necessary locations"""
        # Make sure we have an API key
        api_key = self.get_api_key_interactive()

        results = {}

        # 1. Environment variable
        results["environment"] = self._set_environment_variable(api_key)

        # 2. .env file
        results["env_file"] = self._update_env_file(api_key)

        # 3. Shell configuration
        results["shell_config"] = self._update_shell_config(api_key)

        # 4. Claude settings
        results["claude_settings"] = self._update_claude_settings(api_key)

        return results

    def _set_environment_variable(self, api_key: str) -> bool:
        """Set API key in current environment"""
        try:
            os.environ["CFBD_API_KEY"] = api_key
            os.environ["CFBD_API_TOKEN"] = api_key
            return True
        except Exception as e:
            print(f"Error setting environment variable: {e}")
            return False

    def _update_env_file(self, api_key: str) -> bool:
        """Update .env file with API key"""
        try:
            # Read existing .env file
            env_content = ""
            if self.env_file.exists():
                with open(self.env_file, "r") as f:
                    env_content = f.read()

            # Update or add CFBD_API_KEY
            lines = env_content.split("\n")
            key_updated = False

            for i, line in enumerate(lines):
                if line.startswith("CFBD_API_KEY="):
                    lines[i] = f"CFBD_API_KEY={api_key}"
                    key_updated = True
                elif line.startswith("CFBD_API_TOKEN="):
                    lines[i] = f"CFBD_API_TOKEN={api_key}"

            if not key_updated:
                lines.append(f"CFBD_API_KEY={api_key}")
                lines.append(f"CFBD_API_TOKEN={api_key}")

            # Write back to .env file
            with open(self.env_file, "w") as f:
                f.write("\n".join(lines))

            return True

        except Exception as e:
            print(f"Error updating .env file: {e}")
            return False

    def _update_shell_config(self, api_key: str) -> bool:
        """Update shell configuration (.zshrc)"""
        try:
            # Read existing .zshrc
            with open(self.zshrc_file, "r") as f:
                zshrc_content = f.read()

            lines = zshrc_content.split("\n")
            key_updated = False

            for i, line in enumerate(lines):
                if line.startswith("export CFBD_API_KEY="):
                    lines[i] = f"export CFBD_API_KEY='{api_key}'"
                    key_updated = True
                elif line.startswith("export CFBD_API_TOKEN="):
                    lines[i] = f"export CFBD_API_TOKEN='{api_key}'"

            if not key_updated:
                lines.append(f"export CFBD_API_KEY='{api_key}'")
                lines.append(f"export CFBD_API_TOKEN='{api_key}'")

            # Write back to .zshrc
            with open(self.zshrc_file, "w") as f:
                f.write("\n".join(lines))

            return True

        except Exception as e:
            print(f"Error updating shell config: {e}")
            return False

    def _update_claude_settings(self, api_key: str) -> bool:
        """Update Claude project settings"""
        try:
            claude_dir = self.claude_settings.parent
            claude_dir.mkdir(exist_ok=True)

            # Read or create settings.json
            settings = {}
            if self.claude_settings.exists():
                with open(self.claude_settings, "r") as f:
                    settings = json.load(f)

            # Update environment section
            if "environment" not in settings:
                settings["environment"] = {}

            settings["environment"]["CFBD_API_KEY"] = api_key
            settings["environment"]["CFBD_API_TOKEN"] = api_key

            # Write back to settings.json
            with open(self.claude_settings, "w") as f:
                json.dump(settings, f, indent=2)

            return True

        except Exception as e:
            print(f"Error updating Claude settings: {e}")
            return False

    def validate_api_key(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Validate API key by testing CFBD API connectivity"""
        if not api_key:
            api_key = os.environ.get("CFBD_API_KEY")

        if not api_key:
            return {
                "api_key_set": False,
                "api_key_matches": False,
                "api_connectivity": False,
                "response_code": None,
                "error_message": "No API key provided",
            }

        try:
            import requests

            # Test API connectivity
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                "https://api.collegefootballdata.com/games?year=2025&limit=1",
                headers=headers,
                timeout=10,
            )

            validation_result = {
                "api_key_set": bool(os.environ.get("CFBD_API_KEY")),
                "api_key_matches": os.environ.get("CFBD_API_KEY") == api_key,
                "api_connectivity": response.status_code == 200,
                "response_code": response.status_code,
                "error_message": None,
            }

            if response.status_code != 200:
                validation_result["error_message"] = response.text

            return validation_result

        except Exception as e:
            return {
                "api_key_set": bool(os.environ.get("CFBD_API_KEY")),
                "api_key_matches": os.environ.get("CFBD_API_KEY") == api_key,
                "api_connectivity": False,
                "response_code": None,
                "error_message": str(e),
            }

    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive API key status report"""
        # Make sure we have an API key first
        api_key = self.get_api_key_interactive()

        results = self.ensure_api_key_everywhere()
        validation = self.validate_api_key(api_key)

        return {
            "setup_results": results,
            "validation": validation,
            "api_key_preview": f"{api_key[:12]}...{api_key[-8:]}" if api_key else "No key",
            "locations_configured": sum(results.values()),
            "total_locations": len(results),
            "success_rate": f"{(sum(results.values()) / len(results) * 100):.1f}%",
        }


def main():
    """Main API key management function"""
    import argparse

    parser = argparse.ArgumentParser(description="CFBD API Key Management")
    parser.add_argument(
        "--validate-only", action="store_true", help="Only validate existing setup"
    )
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--check", action="store_true", help="Check if API key is set")

    args = parser.parse_args()

    manager = APIKeyManager()

    if args.check:
        # Simple check if API key is available
        api_key = os.environ.get("CFBD_API_KEY")
        if args.json:
            print(json.dumps({"api_key_set": bool(api_key)}))
        else:
            if api_key:
                print("✅ CFBD_API_KEY is set in environment")
            else:
                print("❌ CFBD_API_KEY not found in environment")
                print("Set it with: export CFBD_API_KEY='your-api-key-here'")
        return

    if args.validate_only:
        validation = manager.validate_api_key()
        if args.json:
            print(json.dumps(validation, indent=2))
        else:
            print("API Key Validation Results:")
            for key, value in validation.items():
                status = "✅" if value or key == "response_code" else "❌"
                print(f"  {status} {key}: {value}")
    else:
        status = manager.get_status_report()

        if args.json:
            print(json.dumps(status, indent=2))
        elif not args.quiet:
            print("🏈 CFBD API Key Management Status")
            print("=" * 40)
            print(f"API Key: {status['api_key_preview']}")
            print(
                f"Locations: {status['locations_configured']}/{status['total_locations']} configured"
            )
            print(f"Success Rate: {status['success_rate']}")
            print()

            print("Setup Results:")
            for location, success in status["setup_results"].items():
                status_icon = "✅" if success else "❌"
                print(f"  {status_icon} {location}")

            print()
            print("API Validation:")
            validation = status["validation"]
            for key, value in validation.items():
                if key == "error_message" and value is None:
                    continue
                status_icon = "✅" if value or key == "response_code" else "❌"
                print(f"  {status_icon} {key}: {value}")

        # Exit with error code if any setup failed
        failed_locations = [
            loc for loc, success in status["setup_results"].items() if not success
        ]
        if failed_locations:
            print(f"\n⚠️  Failed locations: {', '.join(failed_locations)}")
            sys.exit(1)
        elif not status["validation"]["api_connectivity"]:
            print(
                f"\n❌ API connectivity failed: {status['validation']['error_message']}"
            )
            sys.exit(1)
        else:
            if not args.quiet:
                print("\n🎉 API key setup complete and validated!")


if __name__ == "__main__":
    main()