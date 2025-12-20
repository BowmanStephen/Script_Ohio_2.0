#!/usr/bin/env python3
"""
Simple Commit Orchestrator - Direct Git-based Approach

A simplified version that uses basic git commands directly to commit the 365 files.
This bypasses the complex agent system and uses the proven git operations approach.

Usage:
    python3 scripts/simple_commit_orchestrator.py --mode=auto
"""

import argparse
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleGitOrchestrator:
    """Simple orchestrator using direct git commands"""

    def __init__(self):
        self.start_time = time.time()
        self.repo_root = Path.cwd()
        self.execution_id = f"simple_commit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Track execution state
        self.state = {
            'execution_id': self.execution_id,
            'start_time': datetime.now().isoformat(),
            'files_committed': 0,
            'commits_created': 0,
            'status': 'ready'
        }

    def get_git_files(self) -> List[str]:
        """Get list of all modified and untracked files"""
        try:
            # Get modified files
            modified_result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )

            # Get untracked files
            untracked_result = subprocess.run(
                ['git', 'ls-files', '--others', '--exclude-standard'],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )

            # Get staged files
            staged_result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )

            files = []
            for result in [modified_result, untracked_result, staged_result]:
                if result.returncode == 0:
                    files.extend(result.stdout.strip().split('\n'))

            # Filter out empty strings and deduplicate
            files = list(set(f.strip() for f in files if f.strip()))

            return sorted(files)

        except Exception as e:
            logger.error(f"Error getting git files: {e}")
            return []

    def create_commit_batches(self, files: List[str], max_files_per_commit: int = 50) -> List[List[str]]:
        """Create optimal commit batches"""
        batches = []

        # Group by directory for logical commits
        directories = {}
        for file_path in files:
            dir_name = Path(file_path).parent
            if dir_name == Path('.'):
                dir_name = 'root'
            if dir_name not in directories:
                directories[dir_name] = []
            directories[dir_name].append(file_path)

        # Create batches
        current_batch = []
        current_batch_size = 0

        # Sort directories by priority (core directories first)
        priority_dirs = ['agents', 'src', 'scripts', 'web_app', 'model_pack', 'starter_pack', 'docs']

        # Process priority directories first
        for dir_name in priority_dirs:
            if dir_name in directories:
                for file_path in directories[dir_name]:
                    current_batch.append(file_path)
                    current_batch_size += 1

                    if current_batch_size >= max_files_per_commit:
                        batches.append(current_batch.copy())
                        current_batch.clear()
                        current_batch_size = 0

                del directories[dir_name]

        # Process remaining directories
        for dir_name, dir_files in directories.items():
            for file_path in dir_files:
                current_batch.append(file_path)
                current_batch_size += 1

                if current_batch_size >= max_files_per_commit:
                    batches.append(current_batch.copy())
                    current_batch.clear()
                    current_batch_size = 0

        # Add final batch if not empty
        if current_batch:
            batches.append(current_batch)

        return batches

    def create_backup_tag(self) -> str:
        """Create a backup tag before starting commits"""
        tag_name = f"backup_before_commit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            subprocess.run(['git', 'tag', tag_name], check=True, cwd=self.repo_root)
            logger.info(f"Created backup tag: {tag_name}")
            return tag_name
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to create backup tag: {e}")
            return ""

    def stage_files(self, files: List[str]) -> bool:
        """Stage files for commit"""
        try:
            if files:
                subprocess.run(['git', 'add'] + files, check=True, cwd=self.repo_root)
                logger.info(f"Staged {len(files)} files")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stage files: {e}")
            return False

    def create_commit(self, batch: List[str], batch_number: int, total_batches: int) -> bool:
        """Create a commit for the given batch"""
        try:
            # Determine commit message based on batch content
            if batch_number == 1:
                prefix = "🎯 MAJOR MILESTONE: Agent Architecture Implementation"
            elif batch_number == total_batches:
                prefix = "🏁 FINAL MILESTONE: Complete System Upgrade"
            else:
                prefix = f"📦 BATCH {batch_number}/{total_batches}: Infrastructure Components"

            # Get directory summary for commit message
            dirs = set(Path(f).parent for f in batch[:5])  # First 5 files
            dir_summary = ", ".join(str(d) for d in sorted(dirs))

            commit_message = f"""{prefix}

Implement comprehensive {batch_number//total_batches*100:.0f}% of architectural upgrade:

{f"📂 Components: {dir_summary}" if dir_summary else "📁 Multiple file updates"}

{f"📊 Files in this batch: {len(batch)}"}

Total progress: {batch_number}/{total_batches} batches

🤖 Generated with Claude Code automated commit orchestrator
Co-Authored-By: Claude <noreply@anthropic.com>"""

            # Create commit
            subprocess.run(['git', 'commit', '-m', commit_message], check=True, cwd=self.repo_root)
            logger.info(f"✅ Created commit {batch_number}/{total_batches}: {len(batch)} files")

            self.state['files_committed'] += len(batch)
            self.state['commits_created'] += 1

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create commit: {e}")
            return False

    def push_commits(self) -> bool:
        """Push all commits to remote"""
        try:
            logger.info("Pushing commits to remote...")
            subprocess.run(['git', 'push', 'origin', 'HEAD'], check=True, cwd=self.repo_root)
            logger.info("✅ Successfully pushed commits to remote")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push commits: {e}")
            return False

    def execute_commit(self, mode: str = 'auto') -> Dict[str, Any]:
        """Execute the complete commit workflow"""
        logger.info(f"🚀 Starting Simple Commit Orchestrator - Mode: {mode}")
        logger.info(f"   Execution ID: {self.execution_id}")
        logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Phase 1: Get files and create batches
            logger.info("🔍 Analyzing repository changes...")
            files = self.get_git_files()

            if not files:
                logger.warning("No files to commit!")
                return {
                    'success': True,
                    'message': 'No files to commit',
                    'files_committed': 0,
                    'execution_time': 0
                }

            logger.info(f"📊 Found {len(files)} files to commit")

            batches = self.create_commit_batches(files)
            logger.info(f"📦 Created {len(batches)} commit batches")

            # Phase 2: Create backup
            backup_tag = self.create_backup_tag()

            # Phase 3: Execute commits
            logger.info("💾 Starting commit process...")
            self.state['status'] = 'committing'

            for i, batch in enumerate(batches, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"📦 BATCH {i}/{len(batches)}: Processing {len(batch)} files")

                # Interactive mode approval
                if mode == 'interactive':
                    if not self.get_batch_approval(batch, i, len(batches)):
                        logger.info("User cancelled - stopping commit process")
                        return {
                            'success': False,
                            'message': 'User cancelled',
                            'files_committed': self.state['files_committed'],
                            'execution_time': time.time() - self.start_time
                        }

                # Stage and commit
                if not self.stage_files(batch):
                    return {
                        'success': False,
                        'message': f'Failed to stage batch {i}',
                        'files_committed': self.state['files_committed'],
                        'execution_time': time.time() - self.start_time
                    }

                if not self.create_commit(batch, i, len(batches)):
                    return {
                        'success': False,
                        'message': f'Failed to create commit batch {i}',
                        'files_committed': self.state['files_committed'],
                        'execution_time': time.time() - self.start_time
                    }

                # Add delay between commits
                if i < len(batches):
                    logger.info("⏳ Waiting 5 seconds before next batch...")
                    time.sleep(5)

            # Phase 4: Push to remote
            logger.info("\n🚀 Pushing to remote repository...")
            if not self.push_commits():
                return {
                    'success': False,
                    'message': 'Failed to push commits',
                    'files_committed': self.state['files_committed'],
                    'execution_time': time.time() - self.start_time
                }

            # Complete successfully
            execution_time = time.time() - self.start_time
            self.state['status'] = 'completed'

            logger.info(f"\n🎉 COMMIT PROCESS COMPLETED SUCCESSFULLY!")
            logger.info(f"   Execution time: {execution_time:.1f} seconds")
            logger.info(f"   Files committed: {self.state['files_committed']}/{len(files)}")
            logger.info(f"   Commits created: {self.state['commits_created']}")
            logger.info(f"   Batches processed: {len(batches)}")
            if backup_tag:
                logger.info(f"   Backup tag: {backup_tag}")

            return {
                'success': True,
                'execution_id': self.execution_id,
                'execution_time': execution_time,
                'files_committed': self.state['files_committed'],
                'total_files': len(files),
                'commits_created': self.state['commits_created'],
                'batches_processed': len(batches),
                'backup_tag': backup_tag
            }

        except Exception as e:
            logger.error(f"Unexpected error during commit execution: {e}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'files_committed': self.state['files_committed'],
                'execution_time': time.time() - self.start_time
            }

    def get_batch_approval(self, batch: List[str], batch_number: int, total_batches: int) -> bool:
        """Get user approval for a batch in interactive mode"""

        print(f"\n{'='*60}")
        print(f"📦 BATCH {batch_number}/{total_batches}")
        print(f"📁 Files: {len(batch)}")
        print(f"📋 Sample files:")

        # Show sample files from the batch
        for file_path in batch[:5]:
            print(f"   - {file_path}")
        if len(batch) > 5:
            print(f"   ... and {len(batch) - 5} more files")

        while True:
            response = input(f"\nProceed with batch {batch_number}? [y/n/d] ").strip().lower()

            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            elif response in ['d', 'details']:
                print(f"\n📋 All files in batch {batch_number}:")
                for i, file_path in enumerate(batch, 1):
                    print(f"   {i:2d}. {file_path}")
            else:
                print("Please enter 'y' (yes), 'n' (no), or 'd' (details)")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Simple Commit Orchestrator - Direct Git-based file commit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 scripts/simple_commit_orchestrator.py --mode=auto
    python3 scripts/simple_commit_orchestrator.py --mode=interactive
        """
    )

    parser.add_argument(
        '--mode',
        choices=['auto', 'interactive'],
        default='auto',
        help='Execution mode (auto=fully automated, interactive=approval prompts)'
    )

    args = parser.parse_args()

    # Create and run orchestrator
    try:
        orchestrator = SimpleGitOrchestrator()
        result = orchestrator.execute_commit(args.mode)

        if result['success']:
            print("\n" + "="*60)
            print("🎉 AUTOMATED COMMIT COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"   Execution ID: {result.get('execution_id', 'unknown')}")
            print(f"   Execution Time: {result.get('execution_time', 0):.1f} seconds")
            print(f"   Files Committed: {result.get('files_committed', 0)}/{result.get('total_files', 0)}")
            print(f"   Commits Created: {result.get('commits_created', 0)}")
            print(f"   Batches Processed: {result.get('batches_processed', 0)}")
            if result.get('backup_tag'):
                print(f"   Backup Tag: {result['backup_tag']}")
            print("\n✅ All changes have been committed and pushed to the remote repository!")
        else:
            print("\n" + "="*60)
            print("❌ AUTOMATED COMMIT FAILED!")
            print("="*60)
            print(f"   Error: {result.get('message', 'Unknown error')}")
            print(f"   Files Attempted: {result.get('files_committed', 0)}")
            print(f"   Execution Time: {result.get('execution_time', 0):.1f} seconds")
            print("\n🔧 Troubleshooting:")
            print("   Check the error messages above")
            print("   Verify git repository status")
            print("   Check remote repository access")

    except KeyboardInterrupt:
        print("\n\n⚠️  COMMIT PROCESS INTERRUPTED BY USER")
        print("Some files may have been committed. Check git status to see current state.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())