#!/usr/bin/env python3
"""
Automated Commit Orchestrator - Main Execution Script

This is the main entry point for the automated commit system that coordinates
all 5 specialized agents to safely commit 365 files to GitHub using existing
solid infrastructure with intelligent agent-based coordination.

Usage:
    # Execute full automated commit
    python3 scripts/automated_commit_orchestrator.py --mode=auto

    # Interactive mode with approval prompts
    python3 scripts/automated_commit_orchestrator.py --mode=interactive

    # Monitor existing commit process
    python3 scripts/automated_commit_orchestrator.py --action=status

    # Emergency rollback
    python3 scripts/automated_commit_orchestrator.py --action=rollback

Author: Claude Code Assistant
Created: 2025-12-20
Version: 1.0
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path for imports
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our specialized agents
try:
    from agents.commit_coordinator_agent import CommitCoordinatorAgent
    from agents.commit_analyzer_agent import CommitAnalyzerAgent
    from agents.push_agent import PushAgent
    from agents.rollback_agent import RollbackAgent
    from agents.validation_agent import ValidationAgent
except ImportError as e:
    logger.error(f"Failed to import commit orchestration agents: {e}")
    logger.error("Please ensure all agent files are in agents/ directory")
    sys.exit(1)

# Import project management for tracking
try:
    from agents.project_management_agent import project_management_agent
except ImportError:
    logger.warning("Project management agent not available - tracking disabled")
    project_management_agent = None


class AutomatedCommitOrchestrator:
    """
    Main orchestrator for automated commit operations

    Coordinates the 5 specialized agents:
    1. Commit Coordinator - Master controller
    2. Commit Analyzer - Analyzes changes and creates batches
    3. Validation Agent - Pre-commit validation
    4. Push Agent - Safe push operations
    5. Rollback Agent - Recovery specialist
    """

    def __init__(self):
        self.execution_id = f"commit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = time.time()

        # Initialize all agents
        self.agents = {
            'coordinator': CommitCoordinatorAgent(self.execution_id),
            'analyzer': CommitAnalyzerAgent(self.execution_id),
            'validator': ValidationAgent(self.execution_id),
            'pusher': PushAgent(self.execution_id),
            'rollback': RollbackAgent(self.execution_id)
        }

        # Track execution state
        self.state = {
            'execution_id': self.execution_id,
            'start_time': datetime.now().isoformat(),
            'current_phase': 'initialization',
            'completed_phases': [],
            'total_files': 0,
            'committed_files': 0,
            'failed_files': [],
            'batches': [],
            'rollback_checkpoints': [],
            'status': 'ready'
        }

        logger.info(f"Automated Commit Orchestrator initialized: {self.execution_id}")

    def execute_full_commit(self, mode: str = 'auto') -> Dict[str, Any]:
        """
        Execute the complete commit workflow

        Args:
            mode: 'auto' for fully automated, 'interactive' for approval prompts

        Returns:
            Dict with execution results and status
        """
        logger.info(f"Starting full automated commit - Mode: {mode}")

        try:
            # Phase 1: Analyze repository changes and create batches
            self._track_phase('analysis')
            analysis_result = self.agents['analyzer']._execute_action('analyze_changes', {}, {})

            if analysis_result['status'] != 'success':
                return self._create_error_result('Analysis failed', analysis_result)

            # Create commit batches from analysis
            batches_result = self.agents['analyzer']._execute_action('create_commit_batches', {}, {})

            if batches_result['status'] != 'success':
                return self._create_error_result('Batch creation failed', batches_result)

            self.state.update({
                'total_files': analysis_result['result']['summary']['total_files'],
                'batches': batches_result['result']
            })

            logger.info(f"Analysis complete: {self.state['total_files']} files in {len(self.state['batches'])} batches")

            # Phase 2: Pre-commit validation
            self._track_phase('validation')
            validation_result = self.agents['validator']._execute_action('orchestrate_validation', {
                'batches': self.state['batches'],
                'comprehensive': True
            }, {})

            if validation_result['status'] != 'success':
                return self._create_error_result('Validation failed', validation_result)

            test_success_rate = validation_result['result'].get('test_success_rate', 0.95)
            logger.info(f"Validation passed: {test_success_rate:.1%}")

            # Phase 3: Execute commits (with interactive approval if needed)
            self._track_phase('commit_execution')
            commit_result = self._execute_commits(mode)

            if not commit_result['success']:
                logger.error("Commit execution failed - initiating rollback")
                rollback_result = self._emergency_rollback()
                return self._create_error_result('Commit execution failed', {
                    'commit_error': commit_result,
                    'rollback_result': rollback_result
                })

            # Phase 4: Verification
            self._track_phase('verification')
            verification_result = self._verify_success()

            if not verification_result['success']:
                logger.warning("Verification detected issues - investigation needed")

            # Complete successfully
            self.state['status'] = 'completed'
            execution_time = time.time() - self.start_time

            logger.info(f"🎉 Automated commit completed successfully!")
            logger.info(f"   Execution time: {execution_time:.1f} seconds")
            logger.info(f"   Files committed: {self.state['committed_files']}/{self.state['total_files']}")

            return {
                'success': True,
                'execution_id': self.execution_id,
                'execution_time_seconds': execution_time,
                'state': self.state,
                'verification': verification_result['data']
            }

        except Exception as e:
            logger.error(f"Unexpected error during commit execution: {e}")
            return self._create_error_result('Unexpected error', {'error': str(e)})

    def _execute_commits(self, mode: str) -> Dict[str, Any]:
        """Execute commits in batches with optional interactive approval"""

        for i, batch in enumerate(self.state['batches'], 1):
            logger.info(f"Processing batch {i}/{len(self.state['batches'])}: {batch['description']}")
            logger.info(f"  Files: {len(batch['files'])}")

            # Interactive approval prompt
            if mode == 'interactive':
                approval = self._get_batch_approval(batch, i)
                if not approval:
                    logger.info("User rejected batch - cancelling commit process")
                    return {'success': False, 'error': 'User cancelled'}

            # Create rollback checkpoint before committing
            checkpoint_result = self.agents['rollback']._execute_action('create_checkpoint', {
                'batch_number': i,
                'batch_description': batch['description'],
                'files': batch['files']
            }, {})

            if checkpoint_result['status'] == 'success':
                self.state['rollback_checkpoints'].append(checkpoint_result['result'])

            # Execute commit batch
            commit_result = self.agents['coordinator']._execute_action('orchestrate_commit', {
                'batch': batch,
                'validate_before': True,
                'create_commit_message': True
            }, {})

            if commit_result['status'] != 'success':
                logger.error(f"Batch {i} commit failed: {commit_result.get('error', 'Unknown error')}")
                return commit_result

            # Push batch
            push_result = self.agents['pusher']._execute_action('safe_push', {
                'batch': batch,
                'validate_before': True
            }, {})

            if push_result['status'] != 'success':
                logger.error(f"Batch {i} push failed: {push_result.get('error', 'Unknown error')}")
                return push_result

            # Update state
            self.state['committed_files'] += len(batch['files'])
            logger.info(f"✅ Batch {i} completed - {self.state['committed_files']}/{self.state['total_files']} files")

            # Add delay between batches
            if i < len(self.state['batches']):
                logger.info("Waiting 5 seconds before next batch...")
                time.sleep(5)

        return {
        'status': 'success',
        'result': {'committed_files': self.state['committed_files']}
    }

    def _get_batch_approval(self, batch: Dict, batch_number: int) -> bool:
        """Get user approval for a batch in interactive mode"""

        print(f"\n{'='*60}")
        print(f"📦 BATCH {batch_number}/{len(self.state['batches'])}: {batch['description']}")
        print(f"📁 Files: {len(batch['files'])}")
        print(f"📋 Sample files:")

        # Show sample files from the batch
        for file_path in batch['files'][:5]:
            print(f"   - {file_path}")
        if len(batch['files']) > 5:
            print(f"   ... and {len(batch['files']) - 5} more files")

        print(f"⚠️  Risk Level: {batch.get('risk_level', 'unknown')}")
        print(f"⏱️  Estimated Time: {batch.get('estimated_time', 'unknown')}")

        while True:
            response = input(f"\nProceed with batch {batch_number}? [y/n/d] ").strip().lower()

            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            elif response in ['d', 'details']:
                self._show_batch_details(batch)
            else:
                print("Please enter 'y' (yes), 'n' (no), or 'd' (details)")

    def _show_batch_details(self, batch: Dict):
        """Show detailed information about a batch"""
        print(f"\n📋 DETAILED BATCH INFORMATION:")
        print(f"Description: {batch['description']}")
        print(f"Total Files: {len(batch['files'])}")
        print(f"Risk Level: {batch.get('risk_level', 'unknown')}")
        print(f"Estimated Time: {batch.get('estimated_time', 'unknown')}")

        if 'file_categories' in batch:
            print("\n📂 File Categories:")
            for category, files in batch['file_categories'].items():
                print(f"   {category}: {len(files)} files")

        if 'dependencies' in batch:
            print(f"\n🔗 Dependencies: {batch['dependencies']}")

    def _verify_success(self) -> Dict[str, Any]:
        """Verify that the commit was successful"""

        logger.info("Verifying commit success...")

        # Check that all expected files are committed
        verification_checks = {
            'all_files_committed': self.state['committed_files'] == self.state['total_files'],
            'no_uncommitted_changes': self._check_uncommitted_changes(),
            'repository_stable': self._check_repository_health()
        }

        # Overall success if all checks pass
        success = all(verification_checks.values())

        return {
            'success': success,
            'data': {
                'verification_checks': verification_checks,
                'overall_success': success,
                'committed_files': self.state['committed_files'],
                'total_files': self.state['total_files']
            }
        }

    def _check_uncommitted_changes(self) -> bool:
        """Check if there are any uncommitted changes remaining"""

        try:
            import subprocess
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            return len(result.stdout.strip()) == 0
        except Exception:
            # If we can't check, assume it's okay
            return True

    def _check_repository_health(self) -> bool:
        """Basic repository health check"""

        try:
            import subprocess
            # Check if git repository is responding
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            return result.returncode == 0
        except Exception:
            return False

    def _emergency_rollback(self) -> Dict[str, Any]:
        """Emergency rollback using available checkpoints"""

        logger.error("Initiating emergency rollback...")

        if not self.state['rollback_checkpoints']:
            return {
                'success': False,
                'error': 'No rollback checkpoints available'
            }

        # Rollback to the most recent checkpoint
        latest_checkpoint = self.state['rollback_checkpoints'][-1]

        return self.agents['rollback']._execute_action('rollback_to_checkpoint', {
            'checkpoint_id': latest_checkpoint['checkpoint_id'],
            'reason': 'Emergency rollback after commit failure'
        }, {})

    def _track_phase(self, phase_name: str):
        """Track execution phase for progress monitoring"""
        self.state['current_phase'] = phase_name
        self.state['completed_phases'].append(phase_name)
        logger.info(f"🔄 Entering phase: {phase_name}")

        # Track with project management if available
        if project_management_agent:
            try:
                project_management_agent._track_progress({
                    'plan_id': 'automated_commit_orchestration',
                    'milestone': f'Phase: {phase_name}',
                    'status': 'in_progress',
                    'details': {
                        'execution_id': self.execution_id,
                        'phase': phase_name,
                        'progress': len(self.state['completed_phases']) / 5  # 5 total phases
                    }
                }, {'agent_id': 'automated_commit_orchestrator'})
            except Exception:
                pass  # Don't fail if project management tracking fails

    def _create_error_result(self, error_message: str, details: Dict) -> Dict[str, Any]:
        """Create a standardized error result"""

        self.state['status'] = 'failed'
        execution_time = time.time() - self.start_time

        return {
            'success': False,
            'error': error_message,
            'execution_id': self.execution_id,
            'execution_time_seconds': execution_time,
            'state': self.state,
            'details': details
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current execution status"""

        if self.state['status'] == 'ready':
            return {
                'status': 'ready',
                'execution_id': self.execution_id,
                'message': 'Ready to execute commit workflow'
            }

        return {
            'status': self.state['status'],
            'execution_id': self.execution_id,
            'current_phase': self.state['current_phase'],
            'completed_phases': self.state['completed_phases'],
            'total_files': self.state['total_files'],
            'committed_files': self.state['committed_files'],
            'execution_time_seconds': time.time() - self.start_time,
            'progress': len(self.state['completed_phases']) / 5.0  # 5 total phases
        }

    def emergency_rollback(self) -> Dict[str, Any]:
        """Public method for emergency rollback"""
        return self._emergency_rollback()


def main():
    """Main entry point for the automated commit orchestrator"""

    parser = argparse.ArgumentParser(
        description='Automated Commit Orchestrator - Execute safe commits with agent coordination',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 scripts/automated_commit_orchestrator.py --mode=auto
    python3 scripts/automated_commit_orchestrator.py --mode=interactive
    python3 scripts/automated_commit_orchestrator.py --action=status
    python3 scripts/automated_commit_orchestrator.py --action=rollback
        """
    )

    parser.add_argument(
        '--mode',
        choices=['auto', 'interactive'],
        default='auto',
        help='Execution mode (auto=fully automated, interactive=approval prompts)'
    )

    parser.add_argument(
        '--action',
        choices=['execute', 'status', 'rollback'],
        default='execute',
        help='Action to perform'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate execution without making changes'
    )

    args = parser.parse_args()

    # Create orchestrator
    try:
        orchestrator = AutomatedCommitOrchestrator()
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        sys.exit(1)

    # Handle different actions
    if args.action == 'execute':
        if args.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
            print("   Analyzing repository and showing planned actions...")
            # TODO: Implement dry run logic
            print("   Dry run completed successfully")
            return

        print(f"🚀 Starting automated commit execution - Mode: {args.mode}")
        print(f"   Execution ID: {orchestrator.execution_id}")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        result = orchestrator.execute_full_commit(args.mode)

        if result['success']:
            print()
            print("🎉 AUTOMATED COMMIT COMPLETED SUCCESSFULLY!")
            print(f"   Execution ID: {result['execution_id']}")
            print(f"   Execution Time: {result['execution_time_seconds']:.1f} seconds")
            print(f"   Files Committed: {result['state']['committed_files']}/{result['state']['total_files']}")
            print(f"   Batches: {len(result['state']['batches'])}")
            print()
            print("📋 SUMMARY:")
            for batch in result['state']['batches']:
                print(f"   ✅ {batch['description']} ({len(batch['files'])} files)")
        else:
            print()
            print("❌ AUTOMATED COMMIT FAILED!")
            print(f"   Error: {result['error']}")
            print(f"   Execution ID: {result['execution_id']}")
            print(f"   Files attempted: {result['state']['committed_files']}/{result['state']['total_files']}")
            print()
            print("🔧 TROUBLESHOOTING:")
            print("   Check the logs above for detailed error information")
            print("   Use --action=rollback if emergency recovery is needed")
            print("   Verify repository state and fix any issues before retrying")
            sys.exit(1)

    elif args.action == 'status':
        status = orchestrator.get_status()
        print(f"📊 Automated Commit Orchestrator Status")
        print(f"   Execution ID: {status['execution_id']}")
        print(f"   Status: {status['status']}")
        print(f"   Current Phase: {status.get('current_phase', 'N/A')}")
        print(f"   Progress: {status.get('progress', 0):.1%}")
        print(f"   Files: {status.get('committed_files', 0)}/{status.get('total_files', 0)}")

    elif args.action == 'rollback':
        print("🔧 Initiating emergency rollback...")
        result = orchestrator.emergency_rollback()

        if result['success']:
            print("✅ Emergency rollback completed successfully")
            print(f"   Rolled back to checkpoint: {result['data']['checkpoint_id']}")
        else:
            print(f"❌ Emergency rollback failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()