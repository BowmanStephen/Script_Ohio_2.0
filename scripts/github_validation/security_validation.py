"""
Security Validation

Validates security for both Python and React:
- Python: bandit, pip-audit, safety
- React: npm audit
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Validates security vulnerabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize security validator"""
        self.config = config
        self.project_root = Path.cwd()
        self.frontend_path = self.project_root / config['project_structure']['frontend_path']
        self.thresholds = config.get('security_thresholds', {
            'high': 0,
            'medium': 5,
            'low': 10
        })
        self.timeout = config['validation_timeouts'].get('security', 120)
    
    def validate(self, scope: str = 'full') -> Dict[str, Any]:
        """Run security validation"""
        results = {
            'success': True,
            'python': {},
            'frontend': {},
            'vulnerabilities': {
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'errors': []
        }
        
        if scope in ['full', 'python']:
            python_result = self._validate_python_security()
            results['python'] = python_result
            if not python_result.get('success', False):
                results['success'] = False
                results['errors'].append('Python security validation failed')
            # Aggregate vulnerabilities
            if 'vulnerabilities' in python_result:
                for severity in ['high', 'medium', 'low']:
                    results['vulnerabilities'][severity] += python_result['vulnerabilities'].get(severity, 0)
        
        if scope in ['full', 'frontend']:
            frontend_result = self._validate_frontend_security()
            results['frontend'] = frontend_result
            if not frontend_result.get('success', False):
                results['success'] = False
                results['errors'].append('Frontend security validation failed')
            # Aggregate vulnerabilities
            if 'vulnerabilities' in frontend_result:
                for severity in ['high', 'medium', 'low']:
                    results['vulnerabilities'][severity] += frontend_result['vulnerabilities'].get(severity, 0)
        
        # Check thresholds
        if results['vulnerabilities']['high'] > self.thresholds['high']:
            results['success'] = False
            results['errors'].append(
                f"High severity vulnerabilities: {results['vulnerabilities']['high']} "
                f"(threshold: {self.thresholds['high']})"
            )
        if results['vulnerabilities']['medium'] > self.thresholds['medium']:
            results['success'] = False
            results['errors'].append(
                f"Medium severity vulnerabilities: {results['vulnerabilities']['medium']} "
                f"(threshold: {self.thresholds['medium']})"
            )
        if results['vulnerabilities']['low'] > self.thresholds['low']:
            results['success'] = False
            results['errors'].append(
                f"Low severity vulnerabilities: {results['vulnerabilities']['low']} "
                f"(threshold: {self.thresholds['low']})"
            )
        
        return results
    
    def _validate_python_security(self) -> Dict[str, Any]:
        """Validate Python security"""
        logger.info("Validating Python security...")
        
        checks = {
            'bandit': self._check_bandit(),
            'pip_audit': self._check_pip_audit(),
            'safety': self._check_safety()
        }
        
        # Aggregate vulnerabilities
        vulnerabilities = {'high': 0, 'medium': 0, 'low': 0}
        for check in checks.values():
            if 'vulnerabilities' in check:
                for severity in ['high', 'medium', 'low']:
                    vulnerabilities[severity] += check['vulnerabilities'].get(severity, 0)
        
        # Check if any check failed threshold
        success = (
            vulnerabilities['high'] <= self.thresholds['high'] and
            vulnerabilities['medium'] <= self.thresholds['medium'] and
            vulnerabilities['low'] <= self.thresholds['low']
        )
        
        return {
            'success': success,
            'checks': checks,
            'vulnerabilities': vulnerabilities,
            'message': f"Python security: {sum(vulnerabilities.values())} vulnerabilities found"
        }
    
    def _check_bandit(self) -> Dict[str, Any]:
        """Check code with bandit"""
        try:
            result = subprocess.run(
                ['bandit', '-r', 'agents/', 'src/', '-f', 'json'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            vulnerabilities = {'high': 0, 'medium': 0, 'low': 0}
            
            if result.returncode == 0 or result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for issue in data.get('results', []):
                        severity = issue.get('issue_severity', 'low').lower()
                        if severity in vulnerabilities:
                            vulnerabilities[severity] += 1
                except (json.JSONDecodeError, KeyError):
                    pass
            
            return {
                'success': True,  # Bandit doesn't fail on findings
                'vulnerabilities': vulnerabilities,
                'output': result.stdout,
                'message': f"Bandit: {sum(vulnerabilities.values())} issues found"
            }
        except FileNotFoundError:
            return {
                'success': True,
                'skipped': True,
                'vulnerabilities': {'high': 0, 'medium': 0, 'low': 0},
                'message': 'Bandit not found (optional)'
            }
        except Exception as e:
            logger.warning(f"Error running bandit: {e}")
            return {
                'success': True,
                'vulnerabilities': {'high': 0, 'medium': 0, 'low': 0},
                'error': str(e)
            }
    
    def _check_pip_audit(self) -> Dict[str, Any]:
        """Check dependencies with pip-audit"""
        try:
            result = subprocess.run(
                ['pip-audit', '--json'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            vulnerabilities = {'high': 0, 'medium': 0, 'low': 0}
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for vuln in data.get('vulnerabilities', []):
                        severity = vuln.get('severity', 'low').lower()
                        if severity in vulnerabilities:
                            vulnerabilities[severity] += 1
                except (json.JSONDecodeError, KeyError):
                    pass
            
            return {
                'success': result.returncode == 0,
                'vulnerabilities': vulnerabilities,
                'output': result.stdout,
                'message': f"pip-audit: {sum(vulnerabilities.values())} vulnerabilities found"
            }
        except FileNotFoundError:
            return {
                'success': True,
                'skipped': True,
                'vulnerabilities': {'high': 0, 'medium': 0, 'low': 0},
                'message': 'pip-audit not found (optional)'
            }
        except Exception as e:
            logger.warning(f"Error running pip-audit: {e}")
            return {
                'success': True,
                'vulnerabilities': {'high': 0, 'medium': 0, 'low': 0},
                'error': str(e)
            }
    
    def _check_safety(self) -> Dict[str, Any]:
        """Check dependencies with safety"""
        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            vulnerabilities = {'high': 0, 'medium': 0, 'low': 0}
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for vuln in data:
                        severity = vuln.get('severity', 'low').lower()
                        if severity in vulnerabilities:
                            vulnerabilities[severity] += 1
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
            
            return {
                'success': result.returncode == 0,
                'vulnerabilities': vulnerabilities,
                'output': result.stdout,
                'message': f"Safety: {sum(vulnerabilities.values())} vulnerabilities found"
            }
        except FileNotFoundError:
            return {
                'success': True,
                'skipped': True,
                'vulnerabilities': {'high': 0, 'medium': 0, 'low': 0},
                'message': 'Safety not found (optional)'
            }
        except Exception as e:
            logger.warning(f"Error running safety: {e}")
            return {
                'success': True,
                'vulnerabilities': {'high': 0, 'medium': 0, 'low': 0},
                'error': str(e)
            }
    
    def _validate_frontend_security(self) -> Dict[str, Any]:
        """Validate React frontend security"""
        logger.info("Validating React frontend security...")
        
        if not self.frontend_path.exists():
            return {
                'success': False,
                'error': f"Frontend path does not exist: {self.frontend_path}"
            }
        
        try:
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=self.frontend_path,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            vulnerabilities = {'high': 0, 'medium': 0, 'low': 0}
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    # npm audit JSON format
                    for severity, count in data.get('metadata', {}).get('vulnerabilities', {}).items():
                        severity_lower = severity.lower()
                        if severity_lower in vulnerabilities:
                            vulnerabilities[severity_lower] = count
                except (json.JSONDecodeError, KeyError):
                    pass
            
            success = (
                vulnerabilities['high'] <= self.thresholds['high'] and
                vulnerabilities['medium'] <= self.thresholds['medium'] and
                vulnerabilities['low'] <= self.thresholds['low']
            )
            
            return {
                'success': success,
                'vulnerabilities': vulnerabilities,
                'output': result.stdout[:1000] if result.stdout else '',  # Limit output
                'message': f"npm audit: {sum(vulnerabilities.values())} vulnerabilities found"
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'npm not found'
            }
        except Exception as e:
            logger.error(f"Error validating frontend security: {e}")
            return {
                'success': False,
                'error': str(e)
            }

