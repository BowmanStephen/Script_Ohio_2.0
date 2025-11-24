"""
Repository Health Validation

Validates Git repository health including:
- Clean working directory
- Protected branch detection
- Secret detection in commits
- Remote connectivity
"""

import logging
from typing import Dict, Any
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from github_operations.git_utils import GitUtils

logger = logging.getLogger(__name__)


class RepositoryHealthValidator:
    """Validates repository health"""
    
    def __init__(self, config: Dict[str, Any], git_utils: GitUtils):
        """Initialize repository health validator"""
        self.config = config
        self.git_utils = git_utils
        self.protected_branches = config.get('protected_branches', [])
    
    def validate(self) -> Dict[str, Any]:
        """Run all repository health checks"""
        results = {
            'success': True,
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        # Check working directory
        clean_check = self._check_working_directory()
        results['checks']['working_directory'] = clean_check
        if not clean_check['success']:
            results['success'] = False
            results['errors'].append(clean_check.get('error', 'Working directory not clean'))
        
        # Check protected branch
        branch_check = self._check_protected_branch()
        results['checks']['protected_branch'] = branch_check
        if branch_check['is_protected']:
            results['warnings'].append(
                f"Pushing to protected branch: {branch_check['branch']}"
            )
        
        # Check for secrets
        secret_check = self._check_secrets()
        results['checks']['secrets'] = secret_check
        if secret_check['secrets_found']:
            results['warnings'].extend([
                f"Potential secret detected in commit {s['commit'][:8]}: {s['pattern']}"
                for s in secret_check['secrets']
            ])
        
        # Check remote connectivity
        remote_check = self._check_remote_connectivity()
        results['checks']['remote_connectivity'] = remote_check
        if not remote_check['success']:
            results['success'] = False
            results['errors'].append('Remote connectivity check failed')
        
        return results
    
    def _check_working_directory(self) -> Dict[str, Any]:
        """Check if working directory is clean"""
        try:
            is_clean = self.git_utils.is_working_directory_clean()
            if is_clean:
                return {
                    'success': True,
                    'message': 'Working directory is clean'
                }
            else:
                uncommitted = self.git_utils.get_uncommitted_files()
                return {
                    'success': False,
                    'message': 'Working directory has uncommitted changes',
                    'uncommitted_files': uncommitted[:10],  # Limit to first 10
                    'error': f'{len(uncommitted)} uncommitted file(s)'
                }
        except Exception as e:
            logger.error(f"Error checking working directory: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_protected_branch(self) -> Dict[str, Any]:
        """Check if current branch is protected"""
        try:
            branch = self.git_utils.get_current_branch()
            is_protected = self.git_utils.is_protected_branch(branch)
            
            return {
                'branch': branch,
                'is_protected': is_protected,
                'message': f"Branch '{branch}' is {'protected' if is_protected else 'not protected'}"
            }
        except Exception as e:
            logger.error(f"Error checking protected branch: {e}")
            return {
                'branch': 'unknown',
                'is_protected': False,
                'error': str(e)
            }
    
    def _check_secrets(self) -> Dict[str, Any]:
        """Check for secrets in recent commits"""
        try:
            secrets = self.git_utils.detect_secrets_in_commits(count=5)
            return {
                'secrets_found': len(secrets) > 0,
                'secrets': secrets,
                'message': f"Found {len(secrets)} potential secret(s) in recent commits"
            }
        except Exception as e:
            logger.error(f"Error checking for secrets: {e}")
            return {
                'secrets_found': False,
                'secrets': [],
                'error': str(e)
            }
    
    def _check_remote_connectivity(self) -> Dict[str, Any]:
        """Check remote repository connectivity"""
        try:
            remote_url = self.git_utils.get_remote_url('origin')
            if not remote_url:
                return {
                    'success': False,
                    'error': 'No remote origin configured'
                }
            
            is_accessible = self.git_utils.check_remote_connectivity('origin')
            return {
                'success': is_accessible,
                'remote_url': remote_url,
                'message': f"Remote '{remote_url}' is {'accessible' if is_accessible else 'not accessible'}"
            }
        except Exception as e:
            logger.error(f"Error checking remote connectivity: {e}")
            return {
                'success': False,
                'error': str(e)
            }

