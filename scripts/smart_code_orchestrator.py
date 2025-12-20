#!/usr/bin/env python3
"""
Smart Code Orchestrator for Script Ohio 2.0

Intelligent automation system that responds to natural language commands
and safely executes code improvements using agent-based workflows.
"""

import os
import sys
import json
import time
import traceback
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class ImprovementRequest:
    """Natural language improvement request"""

    command: str
    intent: str
    scope: str
    confidence: float
    suggested_actions: List[str]


class SmartCodeOrchestrator:
    """Intelligent code improvement orchestrator"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.command_patterns = self._load_command_patterns()
        self.improvement_history = []
        self.performance_metrics = {
            "total_requests": 0,
            "successful_improvements": 0,
            "avg_execution_time": 0,
            "user_satisfaction": 0.0,
        }

    def _load_command_patterns(self) -> Dict[str, Dict]:
        """Load natural language command patterns"""
        return {
            # Code Quality Commands
            "clean_up_code": {
                "keywords": ["clean", "cleanup", "tidy", "organize", "format", "style"],
                "intent": "improve_code_quality",
                "actions": ["format", "sort_imports", "remove_unused_imports"],
                "confidence_threshold": 0.7,
            },
            "fix_syntax": {
                "keywords": ["fix", "broken", "syntax", "error", "not working"],
                "intent": "fix_syntax_issues",
                "actions": ["validate_syntax", "apply_fixes"],
                "confidence_threshold": 0.8,
            },
            "improve_structure": {
                "keywords": ["structure", "organize", "refactor", "better"],
                "intent": "improve_code_structure",
                "actions": ["analyze_structure", "suggest_refactors"],
                "confidence_threshold": 0.6,
            },
            # Safety & Testing Commands
            "make_safe": {
                "keywords": ["safe", "backup", "protect", "secure"],
                "intent": "enhance_safety",
                "actions": ["create_backup", "add_safety_checks", "validate"],
                "confidence_threshold": 0.7,
            },
            "test_code": {
                "keywords": ["test", "check", "validate", "verify"],
                "intent": "run_tests",
                "actions": ["run_tests", "generate_coverage", "fix_test_issues"],
                "confidence_threshold": 0.8,
            },
            # Performance Commands
            "speed_up": {
                "keywords": ["fast", "slow", "performance", "optimize", "speed"],
                "intent": "improve_performance",
                "actions": ["profile_code", "optimize_bottlenecks"],
                "confidence_threshold": 0.6,
            },
            # Documentation Commands
            "document": {
                "keywords": ["docs", "documentation", "explain", "comments"],
                "intent": "improve_documentation",
                "actions": ["add_docs", "improve_comments", "generate_readme"],
                "confidence_threshold": 0.7,
            },
            # General Commands
            "improve": {
                "keywords": ["improve", "better", "enhance", "upgrade"],
                "intent": "general_improvement",
                "actions": [
                    "analyze",
                    "suggest_improvements",
                    "apply_safe_improvements",
                ],
                "confidence_threshold": 0.5,
            },
            "check": {
                "keywords": ["check", "status", "health", "analyze"],
                "intent": "analyze_status",
                "actions": ["health_check", "generate_report"],
                "confidence_threshold": 0.8,
            },
        }

    def parse_natural_command(self, command: str) -> ImprovementRequest:
        """Parse natural language command into structured request"""
        command_lower = command.lower()
        words = command_lower.split()

        best_match = None
        best_confidence = 0.0

        for pattern_name, pattern_data in self.command_patterns.items():
            confidence = self._calculate_confidence(words, pattern_data["keywords"])
            if (
                confidence > best_confidence
                and confidence >= pattern_data["confidence_threshold"]
            ):
                best_confidence = confidence
                best_match = pattern_name

        if best_match:
            pattern = self.command_patterns[best_match]
            return ImprovementRequest(
                command=command,
                intent=pattern["intent"],
                scope=self._extract_scope(command),
                confidence=best_confidence,
                suggested_actions=pattern["actions"],
            )
        else:
            # Fallback to general analysis
            return ImprovementRequest(
                command=command,
                intent="analyze_request",
                scope="general",
                confidence=0.3,
                suggested_actions=["analyze", "ask_clarification"],
            )

    def _calculate_confidence(self, words: List[str], keywords: List[str]) -> float:
        """Calculate confidence score for command matching"""
        matches = sum(
            1 for word in words if any(keyword in word for keyword in keywords)
        )
        return min(matches / len(words) if words else 0, 1.0)

    def _extract_scope(self, command: str) -> str:
        """Extract scope from command (specific files, directories, etc.)"""
        # Look for file paths, directories, or specific components
        import re

        # File paths
        file_patterns = re.findall(r"[\w\-\.\/]+\.py", command)
        if file_patterns:
            return f"files:{','.join(file_patterns)}"

        # Directories
        dir_patterns = re.findall(r"[\w\-\/]+\/", command)
        if dir_patterns:
            return f"dirs:{','.join(dir_patterns[:-1])}"  # Remove trailing slash

        # Components
        components = ["agents", "src", "scripts", "tests", "web_app", "model_pack"]
        for component in components:
            if component in command.lower():
                return f"component:{component}"

        return "project"

    def execute_request(self, request: ImprovementRequest) -> Dict[str, Any]:
        """Execute the improvement request using smart automation"""
        start_time = time.time()

        execution_result = {
            "request": request.command,
            "intent": request.intent,
            "confidence": request.confidence,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "actions_taken": [],
            "results": {},
            "execution_time": 0,
            "user_feedback": "",
        }

        try:
            if request.confidence < 0.5:
                # Low confidence - ask for clarification
                execution_result["results"]["clarification_needed"] = True
                execution_result["user_feedback"] = (
                    self._generate_clarification_question(request)
                )
            else:
                # High confidence - execute actions
                for action in request.suggested_actions:
                    action_result = self._execute_action(action, request)
                    execution_result["actions_taken"].append(action)
                    execution_result["results"][action] = action_result

                execution_result["success"] = True

            execution_time = time.time() - start_time
            execution_result["execution_time"] = execution_time

            # Update metrics
            self._update_metrics(execution_result)

            # Add to history
            self.improvement_history.append(execution_result)

        except Exception as e:
            execution_result["error"] = str(e)
            execution_result["success"] = False
            execution_result["traceback"] = traceback.format_exc()
            print(f"DEBUG: Exception occurred: {e}")
            print(f"DEBUG: Traceback: {traceback.format_exc()}")

        return execution_result

    def _execute_action(
        self, action: str, request: ImprovementRequest
    ) -> Dict[str, Any]:
        """Execute a specific action using the safety system"""
        action_map = {
            "format": self._safe_format_code,
            "sort_imports": self._safe_sort_imports,
            "validate_syntax": self._validate_syntax,
            "create_backup": self._create_backup,
            "health_check": self._run_health_check,
            "run_tests": self._run_tests,
            "analyze": self._analyze_code,
            "apply_safe_improvements": self._apply_safe_improvements,
            "generate_report": self._generate_report,
        }

        if action in action_map:
            return action_map[action](request)
        else:
            # Try to run unknown actions as Makefile targets
            return self._run_makefile_target(action, request)

    def _safe_format_code(self, request: ImprovementRequest) -> Dict[str, Any]:
        """Safely format code using the Makefile target"""
        try:
            result = subprocess.run(
                ["make", "format"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "files_changed": self._count_changed_files(result.stdout),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _safe_sort_imports(self, request: ImprovementRequest) -> Dict[str, Any]:
        """Safely sort imports using the Makefile target"""
        try:
            result = subprocess.run(
                ["make", "sort-imports"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "imports_fixed": (
                    result.stdout.count("fixed") if "fixed" in result.stdout else 0
                ),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _apply_safe_improvements(self, request: ImprovementRequest) -> Dict[str, Any]:
        """Apply all safe improvements using the enhanced Makefile target"""
        try:
            result = subprocess.run(
                ["make", "improve-with-backup"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
            )

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "backup_created": "backup" in result.stdout.lower(),
                "changes_applied": result.stdout.count("✅")
                + result.stdout.count("✨"),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _validate_syntax(self, request: ImprovementRequest) -> Dict[str, Any]:
        """Validate Python syntax"""
        try:
            result = subprocess.run(
                ["make", "syntax-validate"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "syntax_valid": "valid syntax" in result.stdout.lower(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _create_backup(self, request: ImprovementRequest) -> Dict[str, Any]:
        """Create backup using Makefile target"""
        try:
            result = subprocess.run(
                ["make", "backup-create"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "backup_created": "branch" in result.stdout.lower()
                or "commit" in result.stdout.lower(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _run_health_check(self, request: ImprovementRequest) -> Dict[str, Any]:
        """Run comprehensive health check"""
        try:
            result = subprocess.run(
                ["make", "health-check"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=180,
            )

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "health_score": self._extract_health_score(result.stdout),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _run_tests(self, request: ImprovementRequest) -> Dict[str, Any]:
        """Run test suite"""
        try:
            result = subprocess.run(
                ["make", "test"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,
            )

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "tests_run": self._extract_test_count(result.stdout),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _analyze_code(self, request: ImprovementRequest) -> Dict[str, Any]:
        """Analyze codebase and provide insights"""
        try:
            # Run comprehensive check for analysis
            result = subprocess.run(
                ["make", "comprehensive-check"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            analysis = {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "insights": self._extract_insights(result.stdout),
            }

            return analysis
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _generate_report(self, request: ImprovementRequest) -> Dict[str, Any]:
        """Generate detailed safety report"""
        try:
            result = subprocess.run(
                ["make", "safe-report"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "report_generated": "saved" in result.stdout.lower(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _count_changed_files(self, output: str) -> int:
        """Count number of files changed from output"""
        return output.count("reformatted") + output.count("fixed")

    def _extract_health_score(self, output: str) -> Dict[str, Any]:
        """Extract health score information from output"""
        score = {
            "syntax_valid": "valid syntax" in output.lower(),
            "critical_files_ok": "critical files present" in output.lower(),
            "data_valid": "data integrity validated" in output.lower(),
        }
        return score

    def _extract_test_count(self, output: str) -> int:
        """Extract number of tests run from output"""
        import re

        matches = re.findall(r"(\d+)\s+(?:tests? run|passed|failed)", output.lower())
        return int(matches[0]) if matches else 0

    def _extract_insights(self, output: str) -> Dict[str, Any]:
        """Extract insights from analysis output"""
        insights = {
            "syntax_issues": "syntax errors" in output.lower(),
            "missing_files": "missing" in output.lower(),
            "linting_issues": "issues" in output.lower() or "error" in output.lower(),
            "overall_health": "passed" in output.lower(),
        }
        return insights

    def _generate_clarification_question(self, request: ImprovementRequest) -> str:
        """Generate clarification question for low-confidence requests"""
        clarification_map = {
            "analyze_request": "I'd like to help! Could you tell me more specifically what you'd like to improve? For example: 'clean up the code formatting', 'make the code safer', or 'check for errors'?",
            "general_improvement": "I can help improve your code! Are you looking to: 1) Clean up formatting, 2) Fix any issues, 3) Add safety checks, or 4) Something else?",
        }

        base_question = clarification_map.get(
            request.intent, "Could you be more specific about what you'd like me to do?"
        )

        # Add scope-specific suggestions
        if request.scope != "project":
            base_question += f" I noticed you mentioned '{request.scope}' - should I focus on that specific area?"

        return base_question

    def _update_metrics(self, result: Dict[str, Any]):
        """Update performance metrics"""
        self.performance_metrics["total_requests"] += 1
        if result["success"]:
            self.performance_metrics["successful_improvements"] += 1

        # Update average execution time
        current_avg = self.performance_metrics["avg_execution_time"]
        new_time = result["execution_time"]
        total_requests = self.performance_metrics["total_requests"]
        self.performance_metrics["avg_execution_time"] = (
            current_avg * (total_requests - 1) + new_time
        ) / total_requests

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            "metrics": self.performance_metrics,
            "success_rate": (
                self.performance_metrics["successful_improvements"]
                / max(self.performance_metrics["total_requests"], 1)
            )
            * 100,
            "recent_requests": (
                self.improvement_history[-5:] if self.improvement_history else []
            ),
        }

    def suggest_next_actions(self) -> List[str]:
        """Suggest next actions based on current state"""
        suggestions = []

        # Check if there are recent improvements
        if not self.improvement_history:
            suggestions.append(
                "Start with a simple check: 'check the code health' or 'clean up the formatting'"
            )
        else:
            last_result = self.improvement_history[-1]
            if last_result.get("success"):
                suggestions.append("Great! Try: 'make the code safer' or 'run tests'")
            else:
                suggestions.append(
                    "Let's fix any issues: 'check for syntax errors' or 'analyze the code structure'"
                )

        # Add general suggestions
        suggestions.extend(
            [
                "Ask for a status update: 'how is the code doing?'",
                "Request specific improvements: 'improve the agents directory'",
                "Get help with safety: 'make sure everything is backed up'",
            ]
        )

        return suggestions[:4]  # Return top 4 suggestions

    def _run_makefile_target(self, target: str, request: ImprovementRequest) -> Dict[str, Any]:
        """Run unknown actions as Makefile targets"""
        try:
            # Convert action to makefile target format
            makefile_target = target.replace("_", "-")
            result = subprocess.run(
                ["make", makefile_target],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "makefile_target": makefile_target,
                "target_executed": True
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


def create_simple_interface():
    """Create a simple interactive interface for users"""
    print("🏈 Smart Code Orchestrator - Script Ohio 2.0")
    print("=" * 50)
    print(
        "I can help you improve your code safely! Just tell me what you need in plain English."
    )
    print()
    print("Examples of what you can say:")
    print("  • 'clean up the code formatting'")
    print("  • 'make everything safer'")
    print("  • 'check if there are any errors'")
    print("  • 'improve the agents directory'")
    print("  • 'run tests and fix issues'")
    print()
    print("Type 'help' for more examples or 'quit' to exit.")
    print()

    orchestrator = SmartCodeOrchestrator()

    while True:
        try:
            command = input("💬 What would you like me to do? ").strip()

            if command.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye! Your code is safe and sound.")
                break

            if command.lower() in ["help", "h", "?"]:
                print("\n📖 Available commands:")
                suggestions = orchestrator.suggest_next_actions()
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
                print()
                continue

            if not command:
                continue

            print(f"\n🔄 Processing: '{command}'...")

            # Parse and execute request
            request = orchestrator.parse_natural_command(command)
            result = orchestrator.execute_request(request)

            # Display results
            if result.get("clarification_needed"):
                print(f"❓ {result['user_feedback']}")
            else:
                print(
                    f"✅ {'Success!' if result['success'] else '❌ Something went wrong'}"
                )

                if result["success"]:
                    print(f"🎯 Intent: {result['intent'].replace('_', ' ').title()}")
                    print(f"⚡ Confidence: {result['confidence']:.1%}")
                    print(f"⏱️  Time: {result['execution_time']:.1f}s")

                    if result["actions_taken"]:
                        print(f"🔧 Actions: {', '.join(result['actions_taken'])}")

                    # Show key results
                    for action, action_result in result.get("results", {}).items():
                        if (
                            isinstance(action_result, dict)
                            and action_result.get("status") == "success"
                        ):
                            if action == "apply_safe_improvements":
                                changes = action_result.get("changes_applied", 0)
                                backup = action_result.get("backup_created", False)
                                print(
                                    f"   • {action}: {changes} improvements made, backup: {'✅' if backup else '❌'}"
                                )
                            elif action == "health_check":
                                health = action_result.get("health_score", {})
                                print(f"   • {action}: System health checked")
                            else:
                                print(f"   • {action}: ✅ Completed")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")

            # Show suggestions for next steps
            suggestions = orchestrator.suggest_next_actions()
            print(f"\n💡 Next, you could:")
            for suggestion in suggestions[:2]:
                print(f"   • {suggestion}")
            print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye! Your code is safe and sound.")
            break
        except Exception as e:
            print(f"\n❌ Oops! Something went wrong: {e}")
            print("💡 Try again with a simpler command like 'check code health'")


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="Smart Code Orchestrator")
    parser.add_argument("command", nargs="?", help="Command to execute")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run in interactive mode"
    )
    parser.add_argument(
        "--metrics", action="store_true", help="Show performance metrics"
    )

    args = parser.parse_args()

    orchestrator = SmartCodeOrchestrator()

    if args.metrics:
        metrics = orchestrator.get_metrics()
        print("📊 Smart Orchestrator Metrics")
        print("=" * 30)
        print(f"Total Requests: {metrics['metrics']['total_requests']}")
        print(f"Success Rate: {metrics['success_rate']:.1f}%")
        print(f"Avg Execution Time: {metrics['metrics']['avg_execution_time']:.1f}s")

        if metrics["recent_requests"]:
            print("\n📋 Recent Requests:")
            for req in metrics["recent_requests"]:
                status = "✅" if req["success"] else "❌"
                print(f"   {status} {req['request']}")

    elif args.interactive or not args.command:
        create_simple_interface()

    else:
        # Single command execution
        request = orchestrator.parse_natural_command(args.command)
        result = orchestrator.execute_request(request)

        print(f"🎯 Command: {args.command}")
        print(f"✅ {'Success' if result['success'] else 'Failed'}")
        print(f"⏱️  Time: {result['execution_time']:.1f}s")

        if not result["success"]:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
