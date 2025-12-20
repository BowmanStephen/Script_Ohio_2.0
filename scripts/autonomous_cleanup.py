#!/usr/bin/env python3
"""
Autonomous Cleanup CLI Interface

Command-line interface for the autonomous code cleanup system.
Provides comprehensive cleanup operations with safety validation and rollback capabilities.

Usage:
    python scripts/autonomous_cleanup.py --scope backup,cache --dry-run
    python scripts/autonomous_cleanup.py --auto --backup-point
    python scripts/autonomous_cleanup.py --rollback --point 2025-01-20_14-30
    python scripts/autonomous_cleanup.py --status

Author: Autonomous Code Orchestration System
Created: 2025-01-20
Version: 1.0
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.cleanup_orchestrator_agent import CleanupOrchestratorAgent
from agents.cleanup.validation_manager import ValidationManager
from agents.cleanup.state_manager import StateManager
from agents.cleanup.rollback_manager import RollbackManager


class AutonomousCleanupCLI:
    """Command-line interface for autonomous cleanup operations"""

    def __init__(self):
        self.orchestrator = CleanupOrchestratorAgent()
        self.validation_manager = ValidationManager()
        self.state_manager = StateManager()
        self.rollback_manager = RollbackManager()

    def run_cleanup(
        self,
        scopes: list,
        dry_run: bool = False,
        force: bool = False,
        auto: bool = False,
        backup_point: bool = False
    ) -> int:
        """Run cleanup operations"""

        print("🧹 Autonomous Cleanup System")
        print("=" * 50)
        print(f"Scopes: {', '.join(scopes)}")
        print(f"Dry run: {dry_run}")
        print(f"Force: {force}")
        print(f"Auto mode: {auto}")
        print()

        # Create state for this operation
        session_id = f"cleanup_{int(time.time())}"
        state = self.state_manager.create_state(
            session_id=session_id,
            operation_type="coordinate_cleanup",
            scopes=scopes,
            initial_state={
                "dry_run": dry_run,
                "force": force,
                "auto": auto,
                "backup_point": backup_point
            }
        )

        # Create backup point if requested
        if backup_point and not dry_run:
            print("📦 Creating backup point...")
            rollback_point = self.rollback_manager.create_rollback_point(
                session_id=session_id,
                description=f"Pre-cleanup backup for scopes: {', '.join(scopes)}",
                scopes=scopes
            )
            print(f"✅ Backup point created: {rollback_point.rollback_id}")
            print()

        # Pre-cleanup validation
        if not dry_run or force:
            print("🔍 Running pre-cleanup validation...")
            validation = self.validation_manager.run_pre_cleanup_validation(
                scope=scopes,
                force=force
            )

            if not validation["overall_passed"]:
                print("❌ Pre-cleanup validation failed!")
                print("Critical issues found:")
                for check_name, result in validation["critical_results"].items():
                    if not result["passed"]:
                        print(f"  - {check_name}: {result['message']}")

                if not force:
                    print("\n💡 Use --force to override validation warnings")
                    return 1
            else:
                print("✅ Pre-cleanup validation passed")

            if validation["warning_results"]:
                print("⚠️  Warnings:")
                for check_name, result in validation["warning_results"].items():
                    if not result["passed"]:
                        print(f"  - {check_name}: {result['message']}")
            print()

        # Analyze scope
        print("📊 Analyzing cleanup scope...")
        analysis = self.orchestrator._analyze_scope({"scopes": scopes}, {})
        print(f"Estimated files: {analysis['total_estimated_files']}")
        print(f"Estimated space to free: {analysis['total_estimated_space_mb']:.1f}MB")
        print()

        # Execute cleanup
        print("🚀 Starting cleanup operations...")
        start_time = time.time()

        try:
            # Update state
            self.state_manager.update_state(
                session_id=session_id,
                status="running"
            )

            # Execute cleanup
            result = self.orchestrator._coordinate_cleanup(
                {
                    "scopes": scopes,
                    "dry_run": dry_run,
                    "force": force
                },
                {"user_id": "cli"}
            )

            execution_time = time.time() - start_time

            # Update state with results
            self.state_manager.update_state(
                session_id=session_id,
                files_processed=result["total_files_processed"],
                space_freed_mb=result["total_space_freed_mb"],
                status="completed"
            )

            # Display results
            print("\n📈 Cleanup Results:")
            print(f"Files processed: {result['total_files_processed']}")
            print(f"Space freed: {result['total_space_freed_mb']:.1f}MB")
            print(f"Execution time: {execution_time:.1f} seconds")
            print(f"Errors: {len(result['errors'])}")
            print(f"Warnings: {len(result['warnings'])}")

            if result["errors"]:
                print("\n❌ Errors encountered:")
                for error in result["errors"]:
                    print(f"  - {error}")

            if result["warnings"]:
                print("\n⚠️  Warnings:")
                for warning in result["warnings"]:
                    print(f"  - {warning}")

            # Show scope-specific results
            for scope, scope_result in result["scopes_processed"].items():
                print(f"\n📂 {scope.title()} Cleanup:")
                print(f"  Files: {scope_result['files_processed']}")
                if scope_result.get("space_freed_mb", 0) > 0:
                    print(f"  Space freed: {scope_result['space_freed_mb']:.1f}MB")

                # Show additional details based on scope
                if scope == "backup" and "categories" in scope_result:
                    print(f"  Categories: {scope_result['categories']}")
                elif scope == "cache" and "directories_removed" in scope_result:
                    print(f"  Directories removed: {scope_result['directories_removed']}")
                elif scope == "legacy" and "files_found" in scope_result:
                    print(f"  Legacy files found: {len(scope_result['files_found'])}")

            # Post-cleanup validation
            if not dry_run:
                print("\n🔍 Running post-cleanup validation...")
                post_validation = self.validation_manager.run_post_cleanup_validation(result)

                if post_validation["overall_passed"]:
                    print("✅ Post-cleanup validation passed")
                else:
                    print("⚠️  Post-cleanup validation found issues:")
                    for check_name, check_result in post_validation["system_integrity"].items():
                        if not check_result["passed"]:
                            print(f"  - {check_name}: {check_result['message']}")

                # Show performance impact
                if "performance_impact" in post_validation:
                    impact = post_validation["performance_impact"]
                    print(f"\n📊 Performance Impact: {impact.get('performance_rating', 'unknown')}")
                    if "disk_space_freed_mb" in impact:
                        print(f"  Disk space freed: {impact['disk_space_freed_mb']:.1f}MB")

            # Complete state
            self.state_manager.complete_state(
                session_id=session_id,
                success=len(result["errors"]) == 0,
                final_summary={
                    "files_processed": result["total_files_processed"],
                    "space_freed_mb": result["total_space_freed_mb"],
                    "execution_time": execution_time,
                    "errors_count": len(result["errors"]),
                    "warnings_count": len(result["warnings"])
                }
            )

            return 0 if len(result["errors"]) == 0 else 1

        except KeyboardInterrupt:
            print("\n⚠️  Cleanup interrupted by user")
            self.state_manager.update_state(
                session_id=session_id,
                status="interrupted"
            )
            return 130
        except Exception as e:
            print(f"\n❌ Cleanup failed: {str(e)}")
            self.state_manager.add_error(
                session_id=session_id,
                error_message=str(e),
                error_context={"exception_type": type(e).__name__}
            )
            self.state_manager.complete_state(
                session_id=session_id,
                success=False
            )
            return 1

    def list_rollback_points(self, limit: int = 10) -> int:
        """List available rollback points"""

        print("📦 Available Rollback Points")
        print("=" * 50)

        rollbacks = self.rollback_manager.list_rollback_points(limit=limit)

        if not rollbacks:
            print("No rollback points available")
            return 0

        for i, rollback in enumerate(rollbacks, 1):
            created_date = datetime.fromisoformat(rollback["timestamp"])
            print(f"\n{i}. {rollback['rollback_id']}")
            print(f"   Session: {rollback['session_id']}")
            print(f"   Description: {rollback['description']}")
            print(f"   Created: {created_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Size: {rollback['size_mb']:.1f}MB")
            print(f"   Files: {rollback['file_count']}")

        return 0

    def restore_rollback(
        self,
        rollback_id: str,
        force: bool = False,
        dry_run: bool = False
    ) -> int:
        """Restore from rollback point"""

        print(f"🔄 Restoring from rollback point: {rollback_id}")
        print(f"Dry run: {dry_run}")
        print(f"Force: {force}")
        print()

        if dry_run:
            print("🔍 Planning restore operations...")

        result = self.rollback_manager.restore_rollback_point(
            rollback_id=rollback_id,
            force=force,
            dry_run=dry_run
        )

        if result["success"]:
            if dry_run:
                print("✅ Restore plan created successfully")
                print("\nPlanned operations:")
                for i, operation in enumerate(result["operations"], 1):
                    print(f"{i}. {operation['operation']}: {operation['description']}")
                    if "file_count" in operation:
                        print(f"   Files: {operation['file_count']}")
            else:
                print("✅ Restore completed successfully")
                print(f"Message: {result.get('message', 'No message')}")
        else:
            print(f"❌ Restore failed: {result.get('error', 'Unknown error')}")

            if "emergency_restore" in result:
                emergency = result["emergency_restore"]
                if emergency.get("success"):
                    print(f"🆘 Emergency restore successful: {emergency.get('backup_id')}")
                else:
                    print("🆘 Emergency restore also failed")

        return 0 if result["success"] else 1

    def show_status(self) -> int:
        """Show system status"""

        print("🔍 Autonomous Cleanup System Status")
        print("=" * 50)

        # Cleanup orchestrator status
        cleanup_status = self.orchestrator.get_cleanup_status()
        print(f"\n🧹 Cleanup Orchestrator:")
        print(f"  Session ID: {cleanup_status['session_id']}")
        print(f"  Phase: {cleanup_status.get('phase', 'unknown')}")
        print(f"  Status: {cleanup_status.get('status', 'unknown')}")
        print(f"  Emergency Stop: {cleanup_status.get('emergency_stop', False)}")
        print(f"  Rollback Points: {cleanup_status['rollback_points_count']}")
        print(f"  Files Processed: {cleanup_status['metrics']['files_processed']}")
        print(f"  Space Freed: {cleanup_status['metrics']['space_freed_mb']:.1f}MB")

        # Validation manager status
        validation_summary = self.validation_manager.get_validation_summary()
        print(f"\n🔍 Validation Manager:")
        print(f"  Total Validations: {validation_summary.get('total_validations', 0)}")
        print(f"  Passed: {validation_summary.get('passed_validations', 0)}")
        print(f"  Pass Rate: {validation_summary.get('pass_rate', 0):.1%}")
        if validation_summary.get("critical_checks_failing"):
            print(f"  Failing Checks: {', '.join(validation_summary['critical_checks_failing'])}")

        # State manager status
        state_metrics = self.state_manager.get_state_metrics()
        print(f"\n📊 State Manager:")
        print(f"  Active Sessions: {state_metrics['active_sessions']}")
        print(f"  Total Files Processed: {state_metrics['total_files_processed']}")
        print(f"  Total Space Freed: {state_metrics['total_space_freed_mb']:.1f}MB")
        print(f"  Total Errors: {state_metrics['total_errors']}")
        print(f"  Total Warnings: {state_metrics['total_warnings']}")

        # Rollback manager status
        rollback_status = self.rollback_manager.get_rollback_status()
        print(f"\n📦 Rollback Manager:")
        print(f"  Rollback Points: {rollback_status['rollback_points']}")
        print(f"  Total Size: {rollback_status['total_size_mb']:.1f}MB")
        print(f"  Directory: {rollback_status['backup_directory']}")
        print(f"  Status: {rollback_status['status']}")

        # Health check
        health_status = {
            "orchestrator": cleanup_status.get("status", "unknown") != "error",
            "validation": validation_summary.get("pass_rate", 0.0) > 0.8,
            "state": state_metrics["total_errors"] < 10,
            "rollback": rollback_status["status"] == "active"
        }

        overall_health = all(health_status.values())
        health_emoji = "✅" if overall_health else "⚠️"
        print(f"\n{health_emoji} Overall Health: {'Healthy' if overall_health else 'Issues Detected'}")

        if not overall_health:
            print("Component Issues:")
            for component, healthy in health_status.items():
                if not healthy:
                    print(f"  - {component.title()}: Unhealthy")

        return 0

    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old rollback points and state data"""

        print(f"🧹 Cleaning up old data (older than {days_to_keep} days)")

        # Clean old rollback points
        print("📦 Cleaning old rollback points...")
        rollback_cleaned = self.rollback_manager.cleanup_old_rollbacks(days_to_keep)
        print(f"  Removed {rollback_cleaned} rollback points")

        # Clean old states
        print("📊 Cleaning old state data...")
        state_cleaned = self.state_manager.cleanup_old_states(days_to_keep)
        print(f"  Removed {state_cleaned} state files")

        print("✅ Cleanup completed")
        return 0


def main():
    """Main CLI entry point"""

    parser = argparse.ArgumentParser(
        description="Autonomous Cleanup System - Safe and intelligent codebase cleanup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze what would be cleaned (dry run)
  python scripts/autonomous_cleanup.py --scope backup,cache --dry-run

  # Run cleanup with backup point
  python scripts/autonomous_cleanup.py --scope cache --backup-point

  # Full autonomous cleanup
  python scripts/autonomous_cleanup.py --auto --backup-point

  # List rollback points
  python scripts/autonomous_cleanup.py --list-rollback

  # Restore from rollback point
  python scripts/autonomous_cleanup.py --rollback rollback_1642690800000

  # Show system status
  python scripts/autonomous_cleanup.py --status

Available Scopes:
  backup    - Clean up backup files with intelligent retention
  cache     - Remove Python cache directories
  legacy    - Clean up post-migration legacy code
  tests     - Organize scattered test files
  docs      - Streamline documentation formats
        """
    )

    # Scope arguments
    parser.add_argument(
        "--scope",
        nargs="+",
        choices=["backup", "cache", "legacy", "tests", "docs"],
        help="Cleanup scopes to process"
    )

    # Mode arguments
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without making changes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip safety validations and force cleanup"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run in fully autonomous mode with all safety checks"
    )
    parser.add_argument(
        "--backup-point",
        action="store_true",
        help="Create rollback point before cleanup"
    )

    # Rollback arguments
    parser.add_argument(
        "--list-rollback",
        action="store_true",
        help="List available rollback points"
    )
    parser.add_argument(
        "--rollback",
        metavar="ROLLBACK_ID",
        help="Restore from specific rollback point"
    )
    parser.add_argument(
        "--restore-dry-run",
        action="store_true",
        help="Dry run rollback operations"
    )

    # Status and management
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status and metrics"
    )
    parser.add_argument(
        "--cleanup-old",
        type=int,
        metavar="DAYS",
        help="Clean up data older than specified days"
    )

    # Output options
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )

    args = parser.parse_args()
    cli = AutonomousCleanupCLI()

    # Handle different modes
    if args.list_rollback:
        return cli.list_rollback_points()

    elif args.rollback:
        return cli.restore_rollback(
            rollback_id=args.rollback,
            force=args.force,
            dry_run=args.restore_dry_run
        )

    elif args.status:
        return cli.show_status()

    elif args.cleanup_old:
        return cli.cleanup_old_data(days_to_keep=args.cleanup_old)

    elif args.scope:
        # Set default scopes if auto mode
        if args.auto and not args.scope:
            args.scope = ["backup", "cache", "legacy", "tests", "docs"]

        # Validate scope selection
        if not args.scope:
            print("❌ No cleanup scopes specified")
            parser.print_help()
            return 1

        # Set defaults for auto mode
        if args.auto:
            args.backup_point = True
            args.force = False

        return cli.run_cleanup(
            scopes=args.scope,
            dry_run=args.dry_run,
            force=args.force,
            auto=args.auto,
            backup_point=args.backup_point
        )

    else:
        print("❌ No action specified")
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())