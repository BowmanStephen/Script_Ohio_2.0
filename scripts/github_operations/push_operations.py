"""
Push Operations

Safe push operations with comprehensive validation
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from github_operations.git_utils import GitUtils
from github_validation.validation_orchestrator import ValidationOrchestrator

logger = logging.getLogger(__name__)


class PushOperations:
    """Handles safe push operations"""
    
    def __init__(self, config: Dict[str, Any], git_utils: GitUtils):
        """Initialize push operations"""
        self.config = config
        self.git_utils = git_utils
        self.validation_orchestrator = ValidationOrchestrator(config)
    
    def safe_push(
        self,
        branch: Optional[str] = None,
        remote: str = 'origin',
        skip_validation: bool = False,
        dry_run: bool = False,
        force_with_lease: bool = False,
        validation_scope: str = 'full'
    ) -> Dict[str, Any]:
        """Perform safe push with validation"""
        logger.info(f"Starting safe push: branch={branch}, remote={remote}, dry_run={dry_run}")
        
        result = {
            'success': False,
            'branch': branch or self.git_utils.get_current_branch(),
            'remote': remote,
            'dry_run': dry_run,
            'timestamp': datetime.now().isoformat()
        }
        
        # Get branch info
        branch_info = self.git_utils.get_branch_info(branch)
        result['branch_info'] = branch_info
        
        # Run validation unless skipped
        if not skip_validation:
            logger.info("Running pre-push validation...")
            validation_results = self.validation_orchestrator.run_validation(
                validation_type='all',
                validation_scope=validation_scope
            )
            result['validation_results'] = validation_results
            
            if not validation_results.get('overall_success', False):
                result['error'] = 'Validation failed. Push aborted.'
                result['success'] = False
                return result
        else:
            logger.warning("Validation skipped (dangerous!)")
            result['validation_skipped'] = True
        
        # Dry run - don't actually push
        if dry_run:
            logger.info("Dry run mode - push not executed")
            result['success'] = True
            result['message'] = 'Dry run completed successfully'
            return result
        
        # Perform push
        try:
            push_result = self._execute_push(
                branch=branch or self.git_utils.get_current_branch(),
                remote=remote,
                force_with_lease=force_with_lease
            )
            
            result.update(push_result)
            result['success'] = push_result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error during push: {e}")
            result['error'] = str(e)
            result['success'] = False
        
        return result
    
    def _execute_push(
        self,
        branch: str,
        remote: str,
        force_with_lease: bool = False
    ) -> Dict[str, Any]:
        """Execute the actual git push"""
        import subprocess
        
        push_args = ['push', remote, branch]
        if force_with_lease:
            push_args.insert(1, '--force-with-lease')
        
        try:
            result = subprocess.run(
                ['git'] + push_args,
                cwd=self.git_utils.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                'success': True,
                'message': f"Successfully pushed {branch} to {remote}",
                'output': result.stdout
            }
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f"Push failed: {e.stderr}",
                'exit_code': e.returncode
            }

