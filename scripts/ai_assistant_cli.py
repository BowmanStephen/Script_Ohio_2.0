#!/usr/bin/env python3
"""
AI Assistant CLI Interface

Command-line interface for interacting with the AI Assistant agent
through natural language conversation.

Author: Claude Code Assistant
Created: 2025-12-18
Version: 1.0
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.ai_assistant_agent import AIAssistantAgent
from agents.core.agent_framework import PermissionLevel


class AIAssistantCLI:
    """Command-line interface for AI Assistant"""

    def __init__(self):
        self.agent = AIAssistantAgent("cli_ai_assistant")
        self.session_id = str(uuid.uuid4())
        self.running = True

        # Print welcome message
        self.print_welcome()

    def print_welcome(self):
        """Print welcome message and instructions"""
        print("=" * 70)
        print("🏈 SCRIPT OHIO 2.0 AI ASSISTANT")
        print("=" * 70)
        print("Welcome! I'm your conversational AI assistant for college football analytics.")
        print("I can help you with:")
        print("  📊 Data analysis and team statistics")
        print("  🏈 Game predictions and betting insights")
        print("  🤖 Task automation and report generation")
        print("  📚 Learning guidance and model explanations")
        print()
        print("Type 'help' for commands, 'quit' or 'exit' to end the conversation.")
        print("-" * 70)

    def process_input(self, user_input: str) -> Dict:
        """Process user input through AI Assistant"""
        if user_input.lower() in ['quit', 'exit', 'q']:
            self.running = False
            return {"type": "exit", "message": "Goodbye! 👋"}

        # Handle CLI commands
        if user_input.lower() == 'help':
            return self.show_help()
        elif user_input.lower() == 'status':
            return self.show_status()
        elif user_input.lower() == 'clear':
            return self.clear_conversation()
        elif user_input.lower().startswith('session'):
            return self.handle_session_command(user_input)
        else:
            # Process through AI Assistant
            return self.process_conversation(user_input)

    def show_help(self) -> Dict:
        """Show help information"""
        help_text = """
🤖 AI ASSISTANT COMMANDS:
  help                 Show this help message
  status              Show current session status
  clear               Clear conversation history
  session new         Start a new conversation session
  session info        Show current session information
  quit, exit, q       Exit the AI Assistant

💬 CONVERSATION EXAMPLES:
  "Hello, how are you?"
  "Analyze Ohio State's performance this season"
  "Predict the Ohio State vs Michigan game"
  "Compare top 25 team statistics"
  "Explain how your prediction models work"
  "Generate a weekly report"
  "Show me betting insights for this week"
        """
        return {"type": "help", "message": help_text.strip()}

    def show_status(self) -> Dict:
        """Show current session status"""
        # Get conversation info
        result = self.agent._execute_action("conversation_management", {
            "session_id": self.session_id,
            "action": "get"
        }, {})

        conversation = result["data"]["conversation"]
        context = result["data"]["context"]

        status_text = f"""
📊 SESSION STATUS:
  Session ID: {self.session_id[:8]}...
  Message Count: {len(conversation)}
  Context Keys: {list(context.keys()) if context else 'None'}
  Agent Status: {self.agent.agent_id} - {self.agent.agent_name}
        """.strip()

        return {"type": "status", "message": status_text}

    def clear_conversation(self) -> Dict:
        """Clear conversation history"""
        result = self.agent._execute_action("conversation_management", {
            "session_id": self.session_id,
            "action": "clear"
        }, {})

        if result["status"] == "success":
            return {"type": "clear", "message": "✅ Conversation history cleared"}
        else:
            return {"type": "error", "message": "❌ Failed to clear conversation"}

    def handle_session_command(self, command: str) -> Dict:
        """Handle session-related commands"""
        parts = command.strip().split()

        if len(parts) >= 2 and parts[1] == "new":
            # Start new session
            self.session_id = str(uuid.uuid4())
            return {
                "type": "session",
                "message": f"🆕 Started new conversation session (ID: {self.session_id[:8]}...)"
            }

        elif len(parts) >= 2 and parts[1] == "info":
            # Show session info
            return {
                "type": "session",
                "message": f"📍 Current session ID: {self.session_id}\n   Agent: {self.agent.agent_name}"
            }

        else:
            return {
                "type": "error",
                "message": "❌ Unknown session command. Use 'session new' or 'session info'"
            }

    def process_conversation(self, user_input: str) -> Dict:
        """Process conversation through AI Assistant"""
        try:
            result = self.agent._execute_action("natural_language_processing", {
                "message": user_input,
                "session_id": self.session_id
            }, {})

            if result["status"] == "success":
                data = result["data"]
                response = data["response"]
                intent = data["intent"]
                confidence = data["confidence"]
                suggestions = data.get("suggestions", [])

                # Format response with metadata
                formatted_response = f"{response}\n\n"
                formatted_response += f"🎯 Intent: {intent} (confidence: {confidence:.2f})\n"

                if suggestions:
                    formatted_response += "\n💡 Suggestions:\n"
                    for i, suggestion in enumerate(suggestions, 1):
                        formatted_response += f"  {i}. {suggestion}\n"

                return {
                    "type": "conversation",
                    "message": formatted_response.strip(),
                    "intent": intent,
                    "confidence": confidence,
                    "suggestions": suggestions
                }
            else:
                return {
                    "type": "error",
                    "message": f"❌ Error: {result.get('error', 'Unknown error')}"
                }

        except Exception as e:
            return {
                "type": "error",
                "message": f"❌ Unexpected error: {str(e)}"
            }

    def run_interactive(self):
        """Run interactive conversation"""
        print("You can start talking to me now! Type 'help' for commands.")
        print()

        while self.running:
            try:
                # Get user input
                user_input = input("🏈 You: ").strip()

                if not user_input:
                    continue

                # Process input
                result = self.process_input(user_input)

                # Print response
                print(f"\n🤖 Assistant: {result['message']}\n")

                if result["type"] == "exit":
                    break

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")

    def run_single_query(self, query: str) -> Dict:
        """Process a single query and return result"""
        result = self.process_input(query)
        return result


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Script Ohio 2.0 AI Assistant - Conversational interface for college football analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  python3 ai_assistant_cli.py                    # Interactive mode
  python3 ai_assistant_cli.py -q "Hello"         # Single query
  python3 ai_assistant_cli.py --query "Predict Ohio State vs Michigan"
  python3 ai_assistant_cli.py --session-id custom-session

CONVERSATION EXAMPLES:
  "Hello, how are you?"
  "Analyze Ohio State's performance this season"
  "Predict the Ohio State vs Michigan game"
  "Compare top 25 team statistics"
  "Explain how your prediction models work"
        """
    )

    parser.add_argument(
        "-q", "--query",
        type=str,
        help="Single query to process (non-interactive mode)"
    )

    parser.add_argument(
        "--session-id",
        type=str,
        help="Custom session ID (defaults to random UUID)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output response in JSON format"
    )

    parser.add_argument(
        "--no-welcome",
        action="store_true",
        help="Skip welcome message"
    )

    args = parser.parse_args()

    # Initialize CLI
    cli = AIAssistantCLI()

    # Set custom session ID if provided
    if args.session_id:
        cli.session_id = args.session_id

    # Skip welcome if requested
    if args.no_welcome:
        pass  # Welcome was already printed in __init__

    # Process single query or run interactive mode
    if args.query:
        result = cli.run_single_query(args.query)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"🤖 Assistant: {result['message']}")
    else:
        cli.run_interactive()


if __name__ == "__main__":
    main()