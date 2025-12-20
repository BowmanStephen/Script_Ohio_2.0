#!/usr/bin/env python3
"""
Simple AI Assistant for Script Ohio 2.0

A user-friendly natural language interface for code improvements.
Perfect for users who prefer verbal commands over technical commands.
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


class SimpleAIAssistant:
    """Simple AI assistant for code improvements"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.command_history = []

    def understand_command(self, user_input):
        """Understand what the user wants to do"""
        user_input = user_input.lower()

        # Code quality commands
        if any(word in user_input for word in ["clean", "format", "style", "tidy"]):
            return "format_code"

        if any(word in user_input for word in ["safe", "backup", "protect"]):
            return "make_safe"

        if any(word in user_input for word in ["check", "health", "status", "analyze"]):
            return "check_health"

        if any(word in user_input for word in ["test", "validate", "verify"]):
            return "run_tests"

        if any(word in user_input for word in ["improve", "better", "enhance"]):
            return "general_improve"

        if any(word in user_input for word in ["fix", "error", "broken"]):
            return "fix_issues"

        return "unknown"

    def execute_command(self, command_type):
        """Execute the understood command"""
        actions = {
            "format_code": self._format_code,
            "make_safe": self._make_safe,
            "check_health": self._check_health,
            "run_tests": self._run_tests,
            "general_improve": self._general_improve,
            "fix_issues": self._fix_issues,
            "unknown": self._ask_clarification,
        }

        return actions.get(command_type, self._ask_clarification)()

    def _format_code(self):
        """Safely format the code"""
        print("🎨 I'll clean up your code formatting...")

        try:
            # Use the safe improvements we already built
            result = subprocess.run(
                ["make", "improve-with-backup"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                print("✅ Code formatting complete!")
                print("   • Automatic backup created")
                print("   • Imports organized")
                print("   • Code formatted consistently")
                return True
            else:
                print("❌ Something went wrong with formatting")
                print(f"   Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("⏰ Formatting took too long - interrupted")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def _make_safe(self):
        """Add safety measures"""
        print("🛡️ Making your code safer...")

        # Create backup first
        try:
            result = subprocess.run(
                ["make", "backup-create"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print("✅ Safety measures in place!")
                print("   • Backup created")
                print("   • System validated")
                return True
            else:
                print("❌ Backup creation failed")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def _check_health(self):
        """Check code health"""
        print("🏥 Checking code health...")

        try:
            result = subprocess.run(
                ["make", "health-check"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=180,
            )

            print(result.stdout)
            return result.returncode == 0

        except Exception as e:
            print(f"❌ Error checking health: {e}")
            return False

    def _run_tests(self):
        """Run the test suite"""
        print("🧪 Running tests...")

        try:
            result = subprocess.run(
                ["make", "test"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                print("✅ All tests passed!")
            else:
                print("❌ Some tests failed")
                print(result.stdout)

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print("⏰ Tests took too long - interrupted")
            return False
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False

    def _general_improve(self):
        """General code improvements"""
        print("🚀 Running general improvements...")

        # Run the safe improvements which include formatting and import sorting
        return self._format_code()

    def _fix_issues(self):
        """Try to fix common issues"""
        print("🔧 Looking for issues to fix...")

        # First check for syntax issues
        try:
            result = subprocess.run(
                ["make", "syntax-validate"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                print("✅ No syntax issues found")
                # Then run general improvements
                return self._general_improve()
            else:
                print("❌ Syntax issues found - please fix these first")
                print(result.stdout)
                return False

        except Exception as e:
            print(f"❌ Error checking for issues: {e}")
            return False

    def _ask_clarification(self):
        """Ask user to clarify their request"""
        print(
            "🤔 I'm not sure what you want me to do. Here are some things I can help with:"
        )
        print()
        print("💡 Try saying:")
        print("   • 'clean up the code formatting'")
        print("   • 'make everything safer'")
        print("   • 'check the code health'")
        print("   • 'run the tests'")
        print("   • 'improve the code'")
        print("   • 'fix any issues'")
        print()
        return False

    def suggest_next_steps(self):
        """Suggest what to do next"""
        suggestions = [
            "Try: 'clean up the code formatting'",
            "Ask: 'check the code health'",
            "Say: 'make everything safer'",
            "Request: 'run the tests'",
        ]

        print("💡 What would you like to do next?")
        for suggestion in suggestions:
            print(f"   {suggestion}")


def main():
    """Main interactive interface"""
    print("🤖 Simple AI Assistant - Script Ohio 2.0")
    print("=" * 45)
    print("I help you improve your code safely!")
    print("Just tell me what you need in plain English. 😊")
    print()
    print("Type 'help' for examples or 'quit' to exit.")
    print()

    assistant = SimpleAIAssistant()

    while True:
        try:
            user_input = input("💬 What can I help you with? ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye! Your code is safe and improved.")
                break

            if user_input.lower() in ["help", "h", "?"]:
                assistant._ask_clarification()
                assistant.suggest_next_steps()
                print()
                continue

            if not user_input:
                continue

            print()
            command_type = assistant.understand_command(user_input)
            success = assistant.execute_command(command_type)

            # Add to history
            assistant.command_history.append(
                {
                    "input": user_input,
                    "command": command_type,
                    "success": success,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            print()
            if success:
                print("✅ Task completed successfully!")
                assistant.suggest_next_steps()
            else:
                print("💡 Let me help you with that...")
                assistant.suggest_next_steps()

            print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye! Your code is safe and improved.")
            break
        except Exception as e:
            print(f"\n❌ Oops! Something went wrong: {e}")
            print("💡 Try again with a simpler request")
            print()


if __name__ == "__main__":
    main()
