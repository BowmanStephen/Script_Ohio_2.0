"""
Build Validation

Validates builds for both Python and React frontend:
- Python syntax validation
- React build validation
"""

import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class BuildValidator:
    """Validates build processes"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize build validator"""
        self.config = config
        self.project_root = Path.cwd()
        self.frontend_path = self.project_root / config['project_structure']['frontend_path']
        self.frontend_dist = self.project_root / config['project_structure']['frontend_dist']
        self.timeout = config['validation_timeouts'].get('build', 300)
    
    def validate(self, scope: str = 'full') -> Dict[str, Any]:
        """Run build validation"""
        results = {
            'success': True,
            'python': {},
            'frontend': {},
            'errors': []
        }
        
        if scope in ['full', 'python']:
            python_result = self._validate_python_build()
            results['python'] = python_result
            if not python_result.get('success', False):
                results['success'] = False
                results['errors'].append('Python build validation failed')
        
        if scope in ['full', 'frontend']:
            frontend_result = self._validate_frontend_build()
            results['frontend'] = frontend_result
            if not frontend_result.get('success', False):
                results['success'] = False
                results['errors'].append('Frontend build validation failed')
        
        return results
    
    def _validate_python_build(self) -> Dict[str, Any]:
        """Validate Python syntax"""
        logger.info("Validating Python syntax...")
        
        python_paths = self.config['project_structure']['python_paths']
        invalid_files = []
        total_files = 0
        
        for path_str in python_paths:
            path = self.project_root / path_str
            if not path.exists():
                continue
            
            for py_file in path.rglob('*.py'):
                # Skip common exclusions
                if any(skip in str(py_file) for skip in [
                    '__pycache__', '.venv', 'venv', '.git', 'node_modules',
                    'dist', 'build', '.pytest_cache'
                ]):
                    continue
                
                total_files += 1
                try:
                    result = subprocess.run(
                        ['python3', '-m', 'py_compile', str(py_file)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode != 0:
                        invalid_files.append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'error': result.stderr
                        })
                except subprocess.TimeoutExpired:
                    invalid_files.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'error': 'Timeout during compilation'
                    })
                except Exception as e:
                    invalid_files.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'error': str(e)
                    })
        
        success = len(invalid_files) == 0
        return {
            'success': success,
            'total_files': total_files,
            'invalid_files': len(invalid_files),
            'errors': invalid_files[:10],  # Limit to first 10
            'message': f"Python syntax: {total_files - len(invalid_files)}/{total_files} files valid"
        }
    
    def _validate_frontend_build(self) -> Dict[str, Any]:
        """Validate React frontend build"""
        logger.info("Validating React frontend build...")
        
        if not self.frontend_path.exists():
            return {
                'success': False,
                'error': f"Frontend path does not exist: {self.frontend_path}"
            }
        
        # Check if node_modules exists
        node_modules = self.frontend_path / 'node_modules'
        if not node_modules.exists():
            return {
                'success': False,
                'error': 'node_modules not found. Run npm install first.'
            }
        
        # Clean previous build
        if self.frontend_dist.exists():
            import shutil
            shutil.rmtree(self.frontend_dist)
        
        # Run build
        try:
            result = subprocess.run(
                ['npm', 'run', 'build'],
                cwd=self.frontend_path,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': 'Build failed',
                    'stderr': result.stderr[-500:] if result.stderr else '',  # Last 500 chars
                    'stdout': result.stdout[-500:] if result.stdout else ''
                }
            
            # Verify dist directory was created
            if not self.frontend_dist.exists():
                return {
                    'success': False,
                    'error': 'Build completed but dist directory not found'
                }
            
            # Check for build artifacts
            dist_files = list(self.frontend_dist.rglob('*'))
            js_files = [f for f in dist_files if f.suffix in ['.js', '.mjs']]
            css_files = [f for f in dist_files if f.suffix == '.css']
            
            return {
                'success': True,
                'dist_path': str(self.frontend_dist),
                'js_files': len(js_files),
                'css_files': len(css_files),
                'total_files': len(dist_files),
                'message': f"Build successful: {len(js_files)} JS, {len(css_files)} CSS files"
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Build timeout after {self.timeout} seconds'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'npm not found. Install Node.js and npm first.'
            }
        except Exception as e:
            logger.error(f"Error validating frontend build: {e}")
            return {
                'success': False,
                'error': str(e)
            }

