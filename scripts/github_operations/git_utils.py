"""
Git Utility Functions

Helper functions for Git operations including:
- Repository status checks
- Branch information
- Commit information
- Remote operations
"""

import subprocess
import re
from pathlib import Path
from typing import Dict, Any, Optional, List


class GitUtils:
    """Utility class for Git operations"""
    
    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize Git utilities"""
        if repo_path is None:
            # Find git root from current directory
            repo_path = self._find_git_root()
        self.repo_path = repo_path
    
    def _find_git_root(self) -> Path:
        """Find the git repository root"""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        return Path.cwd()
    
    def _run_git(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command"""
        cmd = ['git'] + args
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=check
        )
        return result
    
    def get_current_branch(self) -> str:
        """Get current branch name"""
        result = self._run_git(['rev-parse', '--abbrev-ref', 'HEAD'])
        return result.stdout.strip()
    
    def get_current_commit(self) -> str:
        """Get current commit hash"""
        result = self._run_git(['rev-parse', 'HEAD'])
        return result.stdout.strip()
    
    def is_working_directory_clean(self) -> bool:
        """Check if working directory is clean"""
        result = self._run_git(['status', '--porcelain'], check=False)
        return result.stdout.strip() == ''
    
    def get_uncommitted_files(self) -> List[str]:
        """Get list of uncommitted files"""
        result = self._run_git(['status', '--porcelain'], check=False)
        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                # Format: " M file.py" or "?? file.py"
                files.append(line[3:].strip())
        return files
    
    def is_protected_branch(self, branch: Optional[str] = None) -> bool:
        """Check if branch is protected"""
        if branch is None:
            branch = self.get_current_branch()
        
        protected = ['main', 'master', 'develop', 'production']
        return branch in protected
    
    def get_remote_url(self, remote: str = 'origin') -> Optional[str]:
        """Get remote URL"""
        try:
            result = self._run_git(['remote', 'get-url', remote], check=False)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def check_remote_connectivity(self, remote: str = 'origin') -> bool:
        """Check if remote is accessible"""
        try:
            result = self._run_git(['ls-remote', remote], check=False)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_recent_commits(self, count: int = 5) -> List[Dict[str, str]]:
        """Get recent commit information"""
        result = self._run_git([
            'log',
            f'-{count}',
            '--format=%H|%s|%an|%ae',
            '--no-decorate'
        ])
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 2:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1],
                        'author': parts[2] if len(parts) > 2 else '',
                        'email': parts[3] if len(parts) > 3 else ''
                    })
        return commits
    
    def detect_secrets_in_commits(self, count: int = 5) -> List[Dict[str, Any]]:
        """Detect potential secrets in recent commit messages"""
        commits = self.get_recent_commits(count)
        secrets_found = []
        
        # Common secret patterns
        patterns = {
            'api_key': re.compile(r'(?i)(api[_-]?key|apikey)\s*[:=]\s*[\w\-]+', re.IGNORECASE),
            'password': re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*\S+', re.IGNORECASE),
            'token': re.compile(r'(?i)(token|bearer)\s*[:=]\s*[\w\-\.]+', re.IGNORECASE),
            'secret': re.compile(r'(?i)(secret|secret[_-]?key)\s*[:=]\s*\S+', re.IGNORECASE),
            'private_key': re.compile(r'(?i)(private[_-]?key|privkey)\s*[:=]\s*[\w\-]+', re.IGNORECASE),
        }
        
        for commit in commits:
            message = commit['message']
            for pattern_name, pattern in patterns.items():
                if pattern.search(message):
                    secrets_found.append({
                        'commit': commit['hash'],
                        'message': message,
                        'pattern': pattern_name,
                        'severity': 'high' if pattern_name in ['private_key', 'secret'] else 'medium'
                    })
        
        return secrets_found
    
    def get_branch_info(self, branch: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive branch information"""
        if branch is None:
            branch = self.get_current_branch()
        
        info = {
            'name': branch,
            'commit': self.get_current_commit(),
            'is_protected': self.is_protected_branch(branch),
            'is_clean': self.is_working_directory_clean()
        }
        
        # Check if branch exists on remote
        try:
            result = self._run_git(['ls-remote', '--heads', 'origin', branch], check=False)
            info['exists_on_remote'] = result.returncode == 0 and branch in result.stdout
        except Exception:
            info['exists_on_remote'] = False
        
        return info

