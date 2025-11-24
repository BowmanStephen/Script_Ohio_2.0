"""
Rollback Operations

Safe rollback operations with backup branch creation
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .git_utils import GitUtils

logger = logging.getLogger(__name__)


class RollbackOperations:
    """Handles safe rollback operations"""
    
    def __init__(self, config: Dict[str, Any], git_utils: GitUtils):
        """Initialize rollback operations"""
        self.config = config
        self.git_utils = git_utils
    
    def safe_rollback(
        self,
        target_commit: Optional[str] = None,
        emergency_mode: bool = False,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """Perform safe rollback with backup"""
        logger.info(f"Starting rollback: commit={target_commit}, emergency={emergency_mode}")
        
        result = {
            'success': False,
            'target_commit': target_commit,
            'emergency_mode': emergency_mode,
            'timestamp': datetime.now().isoformat()
        }
        
        # Get current branch and commit
        current_branch = self.git_utils.get_current_branch()
        current_commit = self.git_utils.get_current_commit()
        result['current_branch'] = current_branch
        result['current_commit'] = current_commit
        
        # Determine target commit
        if target_commit is None:
            # Rollback to previous commit
            try:
                result_prev = self.git_utils._run_git(['log', '-1', '--format=%H', 'HEAD~1'], check=False)
                if result_prev.returncode == 0:
                    target_commit = result_prev.stdout.strip()
                else:
                    result['error'] = 'No previous commit found'
                    return result
            except Exception as e:
                result['error'] = f"Error finding previous commit: {e}"
                return result
        
        result['target_commit'] = target_commit
        
        # Ensure target_commit is set (should not be None at this point)
        if target_commit is None:
            result['error'] = 'Target commit is required'
            return result
        
        # Create backup branch if requested
        backup_branch = None
        if create_backup:
            backup_branch = self._create_backup_branch(current_branch, current_commit)
            result['backup_branch'] = backup_branch
            if not backup_branch:
                if not emergency_mode:
                    result['error'] = 'Failed to create backup branch. Use --emergency to skip.'
                    return result
                logger.warning("Backup creation failed, continuing in emergency mode")
        
        # Perform rollback
        try:
            rollback_result = self._execute_rollback(target_commit, emergency_mode)
            result.update(rollback_result)
            result['success'] = rollback_result.get('success', False)
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            result['error'] = str(e)
            result['success'] = False
            
            # If rollback failed and we have a backup, suggest recovery
            if backup_branch:
                result['recovery_suggestion'] = f"Recovery: git checkout {backup_branch}"
        
        return result
    
    def _create_backup_branch(
        self,
        current_branch: str,
        current_commit: str
    ) -> Optional[str]:
        """Create a backup branch before rollback"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_branch = f"backup_{current_branch}_{timestamp}"
        
        try:
            result = self.git_utils._run_git([
                'branch',
                backup_branch,
                current_commit
            ], check=False)
            
            if result.returncode == 0:
                logger.info(f"Created backup branch: {backup_branch}")
                return backup_branch
            else:
                logger.error(f"Failed to create backup branch: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error creating backup branch: {e}")
            return None
    
    def _execute_rollback(
        self,
        target_commit: str,
        emergency_mode: bool
    ) -> Dict[str, Any]:
        """Execute the actual rollback"""
        try:
            # Reset to target commit
            reset_result = self.git_utils._run_git([
                'reset',
                '--hard',
                target_commit
            ], check=False)
            
            if reset_result.returncode != 0:
                return {
                    'success': False,
                    'error': f"Reset failed: {reset_result.stderr}"
                }
            
            # If not emergency mode, verify the commit exists
            if not emergency_mode:
                verify_result = self.git_utils._run_git([
                    'rev-parse',
                    '--verify',
                    f'{target_commit}^{{commit}}'
                ], check=False)
                
                if verify_result.returncode != 0:
                    return {
                        'success': False,
                        'error': f"Invalid commit: {target_commit}"
                    }
            
            return {
                'success': True,
                'message': f"Successfully rolled back to {target_commit[:8]}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

