#!/usr/bin/env python3
"""
Comprehensive CFBD API Key Management System
Ensures API key is available across all contexts and provides validation
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

class APIKeyManager:
    """Manages CFBD API key across multiple contexts and provides validation"""

    def __init__(self):
        self.project_dir = Path("/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0")
        self.api_key = "3nSBeJV4ODZlJLxQZ/H0vWG3DRAfTSPU2PporK/5K+BJininva/bPx5G4iNjeOsb"
        self.env_file = self.project_dir / ".env"
        self.zshrc_file = Path.home() / ".zshrc"
        self.claude_settings = self.project_dir / ".claude" / "settings.json"

    def ensure_api_key_everywhere(self) -> Dict[str, bool]:
        """Ensure API key is set in all necessary locations"""
        results = {}

        # 1. Environment variable
        results['environment'] = self._set_environment_variable()

        # 2. .env file
        results['env_file'] = self._update_env_file()

        # 3. Shell configuration
        results['shell_config'] = self._update_shell_config()

        # 4. Claude settings
        results['claude_settings'] = self._update_claude_settings()

        return results

    def _set_environment_variable(self) -> bool:
        """Set API key in current environment"""
        try:
            os.environ['CFBD_API_KEY'] = self.api_key
            os.environ['CFBD_API_TOKEN'] = self.api_key
            return True
        except Exception as e:
            print(f"Error setting environment variable: {e}")
            return False

    def _update_env_file(self) -> bool:
        """Update .env file with API key"""
        try:
            # Read existing .env file
            env_content = ""
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    env_content = f.read()

            # Update or add CFBD_API_KEY
            lines = env_content.split('\n')
            key_updated = False

            for i, line in enumerate(lines):
                if line.startswith('CFBD_API_KEY='):
                    lines[i] = f'CFBD_API_KEY={self.api_key}'
                    key_updated = True
                elif line.startswith('CFBD_API_TOKEN='):
                    lines[i] = f'CFBD_API_TOKEN={self.api_key}'

            if not key_updated:
                lines.append(f'CFBD_API_KEY={self.api_key}')
                lines.append(f'CFBD_API_TOKEN={self.api_key}')

            # Write back to .env file
            with open(self.env_file, 'w') as f:
                f.write('\n'.join(lines))

            return True

        except Exception as e:
            print(f"Error updating .env file: {e}")
            return False

    def _update_shell_config(self) -> bool:
        """Update shell configuration (.zshrc)"""
        try:
            # Read existing .zshrc
            with open(self.zshrc_file, 'r') as f:
                zshrc_content = f.read()

            lines = zshrc_content.split('\n')
            key_updated = False

            for i, line in enumerate(lines):
                if line.startswith('export CFBD_API_KEY='):
                    lines[i] = f'export CFBD_API_KEY=\'{self.api_key}\''
                    key_updated = True
                elif line.startswith('export CFBD_API_TOKEN='):
                    lines[i] = f'export CFBD_API_TOKEN=\'{self.api_key}\''

            if not key_updated:
                lines.append(f'export CFBD_API_KEY=\'{self.api_key}\'')
                lines.append(f'export CFBD_API_TOKEN=\'{self.api_key}\'')

            # Write back to .zshrc
            with open(self.zshrc_file, 'w') as f:
                f.write('\n'.join(lines))

            return True

        except Exception as e:
            print(f"Error updating shell config: {e}")
            return False

    def _update_claude_settings(self) -> bool:
        """Update Claude project settings"""
        try:
            claude_dir = self.claude_settings.parent
            claude_dir.mkdir(exist_ok=True)

            # Read or create settings.json
            settings = {}
            if self.claude_settings.exists():
                with open(self.claude_settings, 'r') as f:
                    settings = json.load(f)

            # Update environment section
            if 'environment' not in settings:
                settings['environment'] = {}

            settings['environment']['CFBD_API_KEY'] = self.api_key
            settings['environment']['CFBD_API_TOKEN'] = self.api_key

            # Write back to settings.json
            with open(self.claude_settings, 'w') as f:
                json.dump(settings, f, indent=2)

            return True

        except Exception as e:
            print(f"Error updating Claude settings: {e}")
            return False

    def validate_api_key(self) -> Dict[str, Any]:
        """Validate API key by testing CFBD API connectivity"""
        try:
            import requests

            # Test API connectivity
            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = requests.get(
                'https://api.collegefootballdata.com/games?year=2025&limit=1',
                headers=headers,
                timeout=10
            )

            validation_result = {
                'api_key_set': bool(os.environ.get('CFBD_API_KEY')),
                'api_key_matches': os.environ.get('CFBD_API_KEY') == self.api_key,
                'api_connectivity': response.status_code == 200,
                'response_code': response.status_code,
                'error_message': None
            }

            if response.status_code != 200:
                validation_result['error_message'] = response.text

            return validation_result

        except Exception as e:
            return {
                'api_key_set': bool(os.environ.get('CFBD_API_KEY')),
                'api_key_matches': os.environ.get('CFBD_API_KEY') == self.api_key,
                'api_connectivity': False,
                'response_code': None,
                'error_message': str(e)
            }

    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive API key status report"""
        results = self.ensure_api_key_everywhere()
        validation = self.validate_api_key()

        return {
            'setup_results': results,
            'validation': validation,
            'api_key_preview': f'{self.api_key[:12]}...{self.api_key[-8:]}',
            'locations_configured': sum(results.values()),
            'total_locations': len(results),
            'success_rate': f"{(sum(results.values()) / len(results) * 100):.1f}%"
        }

def main():
    """Main API key management function"""
    import argparse

    parser = argparse.ArgumentParser(description='CFBD API Key Management')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate existing setup')
    parser.add_argument('--quiet', action='store_true',
                       help='Minimal output')
    parser.add_argument('--json', action='store_true',
                       help='JSON output')

    args = parser.parse_args()

    manager = APIKeyManager()

    if args.validate_only:
        validation = manager.validate_api_key()
        if args.json:
            print(json.dumps(validation, indent=2))
        else:
            print("API Key Validation Results:")
            for key, value in validation.items():
                status = "✅" if value or key == 'response_code' else "❌"
                print(f"  {status} {key}: {value}")
    else:
        status = manager.get_status_report()

        if args.json:
            print(json.dumps(status, indent=2))
        elif not args.quiet:
            print("🏈 CFBD API Key Management Status")
            print("=" * 40)
            print(f"API Key: {status['api_key_preview']}")
            print(f"Locations: {status['locations_configured']}/{status['total_locations']} configured")
            print(f"Success Rate: {status['success_rate']}")
            print()

            print("Setup Results:")
            for location, success in status['setup_results'].items():
                status_icon = "✅" if success else "❌"
                print(f"  {status_icon} {location}")

            print()
            print("API Validation:")
            validation = status['validation']
            for key, value in validation.items():
                if key == 'error_message' and value is None:
                    continue
                status_icon = "✅" if value or key == 'response_code' else "❌"
                print(f"  {status_icon} {key}: {value}")

        # Exit with error code if any setup failed
        failed_locations = [loc for loc, success in status['setup_results'].items() if not success]
        if failed_locations:
            print(f"\n⚠️  Failed locations: {', '.join(failed_locations)}")
            sys.exit(1)
        elif not status['validation']['api_connectivity']:
            print(f"\n❌ API connectivity failed: {status['validation']['error_message']}")
            sys.exit(1)
        else:
            if not args.quiet:
                print("\n🎉 API key setup complete and validated!")

if __name__ == "__main__":
    main()