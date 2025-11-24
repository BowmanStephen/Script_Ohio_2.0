#!/usr/bin/env python3
"""
GitHub Safe Operations CLI

Performs safe Git/GitHub operations with comprehensive validation including:
- Repository health checks
- Build validation (Python + React)
- Test validation with coverage thresholds
- Code quality checks
- Security vulnerability scanning
- Performance validation
- Safe push with rollback capabilities

Usage:
    python3 scripts/github_cmd.py push [OPTIONS]
    python3 scripts/github_cmd.py validate [OPTIONS]
    python3 scripts/github_cmd.py rollback [OPTIONS]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from github_validation.validation_orchestrator import ValidationOrchestrator
from github_operations.push_operations import PushOperations
from github_operations.rollback_operations import RollbackOperations
from github_operations.git_utils import GitUtils


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    if config_path is None:
        config_path = Path(__file__).parent / "github_config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)


def cmd_push(args: argparse.Namespace) -> int:
    """Handle push command"""
    config = load_config()
    git_utils = GitUtils()
    push_ops = PushOperations(config, git_utils)
    
    # Determine validation scope
    validation_scope = "full"
    if args.python_only:
        validation_scope = "python"
    elif args.frontend_only:
        validation_scope = "frontend"
    
    # Execute push with validation
    try:
        result = push_ops.safe_push(
            branch=args.branch,
            remote=args.remote,
            skip_validation=args.skip_tests,
            dry_run=args.dry_run,
            force_with_lease=args.force_with_lease,
            validation_scope=validation_scope
        )
        
        if result['success']:
            print("\n✅ Push completed successfully")
            if 'validation_results' in result:
                print_validation_summary(result['validation_results'])
            return 0
        else:
            print(f"\n❌ Push failed: {result.get('error', 'Unknown error')}")
            if 'validation_results' in result:
                print_validation_summary(result['validation_results'])
            return 1
    except Exception as e:
        print(f"\n❌ Fatal error during push: {e}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Handle validate command"""
    config = load_config()
    orchestrator = ValidationOrchestrator(config)
    
    # Determine validation scope
    validation_scope = "full"
    if args.python_only:
        validation_scope = "python"
    elif args.frontend_only:
        validation_scope = "frontend"
    
    # Determine validation type
    validation_type = "all"
    if args.build_only:
        validation_type = "build"
    elif args.tests_only:
        validation_type = "tests"
    elif args.security_only:
        validation_type = "security"
    elif args.performance_only:
        validation_type = "performance"
    
    try:
        results = orchestrator.run_validation(
            validation_type=validation_type,
            validation_scope=validation_scope
        )
        
        print_validation_summary(results)
        
        if results['overall_success']:
            print("\n✅ All validations passed")
            return 0
        else:
            print("\n❌ Some validations failed")
            return 1
    except Exception as e:
        print(f"\n❌ Fatal error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_rollback(args: argparse.Namespace) -> int:
    """Handle rollback command"""
    config = load_config()
    git_utils = GitUtils()
    rollback_ops = RollbackOperations(config, git_utils)
    
    try:
        result = rollback_ops.safe_rollback(
            target_commit=args.commit,
            emergency_mode=args.emergency,
            create_backup=not args.no_backup
        )
        
        if result['success']:
            print("\n✅ Rollback completed successfully")
            if 'backup_branch' in result:
                print(f"   Backup branch created: {result['backup_branch']}")
            return 0
        else:
            print(f"\n❌ Rollback failed: {result.get('error', 'Unknown error')}")
            return 1
    except Exception as e:
        print(f"\n❌ Fatal error during rollback: {e}")
        import traceback
        traceback.print_exc()
        return 1


def print_validation_summary(results: Dict[str, Any]) -> None:
    """Print formatted validation summary"""
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    categories = [
        ('repository_health', 'Repository Health'),
        ('build', 'Build Validation'),
        ('tests', 'Test Validation'),
        ('code_quality', 'Code Quality'),
        ('security', 'Security'),
        ('performance', 'Performance')
    ]
    
    for key, label in categories:
        if key in results:
            status = "✅ PASS" if results[key].get('success', False) else "❌ FAIL"
            print(f"{label:.<50} {status}")
            if not results[key].get('success', False) and 'error' in results[key]:
                print(f"  Error: {results[key]['error']}")
    
    if 'coverage' in results.get('tests', {}):
        coverage = results['tests']['coverage']
        threshold = results['tests'].get('threshold', 90)
        status = "✅" if coverage >= threshold else "❌"
        print(f"\nTest Coverage: {coverage:.1f}% (threshold: {threshold}%) {status}")
    
    print("=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="GitHub Safe Operations CLI - Safe Git operations with comprehensive validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate before pushing
  python3 scripts/github_cmd.py validate
  
  # Push with full validation
  python3 scripts/github_cmd.py push
  
  # Push Python-only validation
  python3 scripts/github_cmd.py push --python-only
  
  # Rollback to previous commit
  python3 scripts/github_cmd.py rollback
  
  # Rollback to specific commit
  python3 scripts/github_cmd.py rollback --commit abc123
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Push command
    push_parser = subparsers.add_parser('push', help='Push with validation')
    push_parser.add_argument('--branch', type=str, help='Target branch (default: current)')
    push_parser.add_argument('--remote', type=str, default='origin', help='Remote name (default: origin)')
    push_parser.add_argument('--skip-tests', action='store_true', help='Skip validation (dangerous)')
    push_parser.add_argument('--dry-run', action='store_true', help='Preview without executing')
    push_parser.add_argument('--force-with-lease', action='store_true', help='Force push with lease')
    push_parser.add_argument('--python-only', action='store_true', help='Validate Python only')
    push_parser.add_argument('--frontend-only', action='store_true', help='Validate frontend only')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Run validation checks')
    validate_parser.add_argument('--build-only', action='store_true', help='Build validation only')
    validate_parser.add_argument('--tests-only', action='store_true', help='Test validation only')
    validate_parser.add_argument('--security-only', action='store_true', help='Security validation only')
    validate_parser.add_argument('--performance-only', action='store_true', help='Performance validation only')
    validate_parser.add_argument('--python-only', action='store_true', help='Python validation only')
    validate_parser.add_argument('--frontend-only', action='store_true', help='Frontend validation only')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback last push')
    rollback_parser.add_argument('--commit', type=str, help='Rollback to specific commit')
    rollback_parser.add_argument('--emergency', action='store_true', help='Emergency rollback mode')
    rollback_parser.add_argument('--no-backup', action='store_true', help='Skip backup branch creation')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command handler
    if args.command == 'push':
        return cmd_push(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'rollback':
        return cmd_rollback(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())

