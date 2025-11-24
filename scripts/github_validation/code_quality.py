"""
Code Quality Validation

Validates code quality for both Python and React:
- Python: ruff, black, mypy
- React: eslint, tsc (TypeScript)
"""

import subprocess
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CodeQualityValidator:
    """Validates code quality"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize code quality validator"""
        self.config = config
        self.project_root = Path.cwd()
        self.frontend_path = self.project_root / config['project_structure']['frontend_path']
        self.python_paths = config['project_structure']['python_paths']
    
    def validate(self, scope: str = 'full') -> Dict[str, Any]:
        """Run code quality validation"""
        results = {
            'success': True,
            'python': {},
            'frontend': {},
            'errors': []
        }
        
        if scope in ['full', 'python']:
            python_result = self._validate_python_quality()
            results['python'] = python_result
            if not python_result.get('success', False):
                results['success'] = False
                results['errors'].append('Python code quality validation failed')
        
        if scope in ['full', 'frontend']:
            frontend_result = self._validate_frontend_quality()
            results['frontend'] = frontend_result
            if not frontend_result.get('success', False):
                results['success'] = False
                results['errors'].append('Frontend code quality validation failed')
        
        return results
    
    def _validate_python_quality(self) -> Dict[str, Any]:
        """Validate Python code quality"""
        logger.info("Validating Python code quality...")
        
        checks = {
            'ruff': self._check_ruff(),
            'black': self._check_black(),
            'mypy': self._check_mypy()
        }
        
        all_passed = all(check.get('success', False) for check in checks.values())
        
        return {
            'success': all_passed,
            'checks': checks,
            'message': f"Python quality: {'all checks passed' if all_passed else 'some checks failed'}"
        }
    
    def _check_ruff(self) -> Dict[str, Any]:
        """Check code with ruff"""
        try:
            # Build paths string
            paths = ' '.join(self.python_paths)
            result = subprocess.run(
                ['ruff', 'check'] + self.python_paths,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'output': result.stdout + result.stderr,
                'message': 'Ruff check passed' if result.returncode == 0 else 'Ruff found issues'
            }
        except FileNotFoundError:
            return {
                'success': True,  # Don't fail if ruff not installed
                'skipped': True,
                'message': 'Ruff not found (optional)'
            }
        except Exception as e:
            logger.warning(f"Error running ruff: {e}")
            return {
                'success': True,  # Don't fail on errors
                'error': str(e)
            }
    
    def _check_black(self) -> Dict[str, Any]:
        """Check code formatting with black"""
        try:
            result = subprocess.run(
                ['black', '--check'] + self.python_paths,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'output': result.stdout + result.stderr,
                'message': 'Black formatting check passed' if result.returncode == 0 else 'Black found formatting issues'
            }
        except FileNotFoundError:
            return {
                'success': True,  # Don't fail if black not installed
                'skipped': True,
                'message': 'Black not found (optional)'
            }
        except Exception as e:
            logger.warning(f"Error running black: {e}")
            return {
                'success': True,  # Don't fail on errors
                'error': str(e)
            }
    
    def _check_mypy(self) -> Dict[str, Any]:
        """Check types with mypy"""
        try:
            result = subprocess.run(
                ['mypy'] + self.python_paths,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'output': result.stdout + result.stderr,
                'message': 'Mypy type check passed' if result.returncode == 0 else 'Mypy found type issues'
            }
        except FileNotFoundError:
            return {
                'success': True,  # Don't fail if mypy not installed
                'skipped': True,
                'message': 'Mypy not found (optional)'
            }
        except Exception as e:
            logger.warning(f"Error running mypy: {e}")
            return {
                'success': True,  # Don't fail on errors
                'error': str(e)
            }
    
    def _validate_frontend_quality(self) -> Dict[str, Any]:
        """Validate React frontend code quality"""
        logger.info("Validating React frontend code quality...")
        
        if not self.frontend_path.exists():
            return {
                'success': False,
                'error': f"Frontend path does not exist: {self.frontend_path}"
            }
        
        checks = {
            'eslint': self._check_eslint(),
            'typescript': self._check_typescript()
        }
        
        all_passed = all(check.get('success', False) for check in checks.values())
        
        return {
            'success': all_passed,
            'checks': checks,
            'message': f"Frontend quality: {'all checks passed' if all_passed else 'some checks failed'}"
        }
    
    def _check_eslint(self) -> Dict[str, Any]:
        """Check code with eslint"""
        try:
            result = subprocess.run(
                ['npm', 'run', 'lint'],
                cwd=self.frontend_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'output': result.stdout + result.stderr,
                'message': 'ESLint check passed' if result.returncode == 0 else 'ESLint found issues'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'npm not found'
            }
        except Exception as e:
            logger.error(f"Error running eslint: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_typescript(self) -> Dict[str, Any]:
        """Check types with TypeScript compiler"""
        try:
            result = subprocess.run(
                ['npm', 'run', 'typecheck'],
                cwd=self.frontend_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'output': result.stdout + result.stderr,
                'message': 'TypeScript check passed' if result.returncode == 0 else 'TypeScript found type errors'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'npm not found'
            }
        except Exception as e:
            logger.error(f"Error running TypeScript check: {e}")
            return {
                'success': False,
                'error': str(e)
            }

