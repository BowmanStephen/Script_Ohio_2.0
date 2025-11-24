"""
Test Validation

Validates test execution and coverage:
- Python pytest with coverage (90% threshold)
- React test execution with coverage
"""

import subprocess
import logging
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TestValidator:
    """Validates test execution and coverage"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize test validator"""
        self.config = config
        self.project_root = Path.cwd()
        self.frontend_path = self.project_root / config['project_structure']['frontend_path']
        self.coverage_threshold = config.get('coverage_threshold', 90)
        self.timeout = config['validation_timeouts'].get('tests', 600)
    
    def validate(self, scope: str = 'full') -> Dict[str, Any]:
        """Run test validation"""
        results = {
            'success': True,
            'python': {},
            'frontend': {},
            'coverage': 0.0,
            'threshold': self.coverage_threshold,
            'errors': []
        }
        
        if scope in ['full', 'python']:
            python_result = self._validate_python_tests()
            results['python'] = python_result
            if not python_result.get('success', False):
                results['success'] = False
                results['errors'].append('Python test validation failed')
            if 'coverage' in python_result:
                results['coverage'] = python_result['coverage']
        
        if scope in ['full', 'frontend']:
            frontend_result = self._validate_frontend_tests()
            results['frontend'] = frontend_result
            if not frontend_result.get('success', False):
                results['success'] = False
                results['errors'].append('Frontend test validation failed')
            # Combine coverage if both run
            if 'coverage' in frontend_result and results['coverage'] > 0:
                results['coverage'] = (results['coverage'] + frontend_result['coverage']) / 2
            elif 'coverage' in frontend_result:
                results['coverage'] = frontend_result['coverage']
        
        # Check coverage threshold
        if results['coverage'] < self.coverage_threshold:
            results['success'] = False
            results['errors'].append(
                f"Coverage {results['coverage']:.1f}% below threshold {self.coverage_threshold}%"
            )
        
        return results
    
    def _validate_python_tests(self) -> Dict[str, Any]:
        """Validate Python tests with pytest"""
        logger.info("Running Python tests with coverage...")
        
        try:
            # Run pytest with coverage
            result = subprocess.run(
                [
                    'python3', '-m', 'pytest',
                    'tests/', 'agents/tests/',
                    '--cov=agents',
                    '--cov=src',
                    '--cov-report=xml',
                    '--cov-report=term',
                    '--junit-xml=test-results.xml',
                    '-v',
                    '--tb=short'
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Parse coverage from XML
            coverage = self._parse_coverage_xml()
            
            # Parse test results
            test_results = self._parse_junit_xml()
            
            success = result.returncode == 0 and coverage >= self.coverage_threshold
            
            return {
                'success': success,
                'exit_code': result.returncode,
                'coverage': coverage,
                'threshold': self.coverage_threshold,
                'tests_run': test_results.get('tests', 0),
                'tests_passed': test_results.get('passed', 0),
                'tests_failed': test_results.get('failed', 0),
                'tests_skipped': test_results.get('skipped', 0),
                'message': f"Tests: {test_results.get('passed', 0)}/{test_results.get('tests', 0)} passed, "
                          f"Coverage: {coverage:.1f}%"
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Test timeout after {self.timeout} seconds'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'pytest not found. Install requirements-dev.txt first.'
            }
        except Exception as e:
            logger.error(f"Error validating Python tests: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_coverage_xml(self) -> float:
        """Parse coverage from coverage.xml"""
        coverage_file = self.project_root / 'coverage.xml'
        if not coverage_file.exists():
            return 0.0
        
        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            # Coverage XML format: <coverage line-rate="0.85">
            line_rate = float(root.get('line-rate', 0))
            return line_rate * 100
        except Exception as e:
            logger.warning(f"Could not parse coverage.xml: {e}")
            return 0.0
    
    def _parse_junit_xml(self) -> Dict[str, int]:
        """Parse test results from JUnit XML"""
        junit_file = self.project_root / 'test-results.xml'
        if not junit_file.exists():
            return {'tests': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
        
        try:
            tree = ET.parse(junit_file)
            root = tree.getroot()
            return {
                'tests': int(root.get('tests', 0)),
                'passed': int(root.get('tests', 0)) - int(root.get('failures', 0)) - int(root.get('errors', 0)),
                'failed': int(root.get('failures', 0)) + int(root.get('errors', 0)),
                'skipped': int(root.get('skipped', 0))
            }
        except Exception as e:
            logger.warning(f"Could not parse test-results.xml: {e}")
            return {'tests': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
    
    def _validate_frontend_tests(self) -> Dict[str, Any]:
        """Validate React frontend tests"""
        logger.info("Running React frontend tests...")
        
        if not self.frontend_path.exists():
            return {
                'success': False,
                'error': f"Frontend path does not exist: {self.frontend_path}"
            }
        
        try:
            # Run tests with coverage
            result = subprocess.run(
                ['npm', 'run', 'test'],
                cwd=self.frontend_path,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Try to parse coverage from output or coverage files
            coverage = self._parse_frontend_coverage()
            
            success = result.returncode == 0
            
            return {
                'success': success,
                'exit_code': result.returncode,
                'coverage': coverage,
                'message': f"Frontend tests: {'passed' if success else 'failed'}, Coverage: {coverage:.1f}%"
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Test timeout after {self.timeout} seconds'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'npm not found. Install Node.js and npm first.'
            }
        except Exception as e:
            logger.error(f"Error validating frontend tests: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_frontend_coverage(self) -> float:
        """Parse frontend coverage from coverage files"""
        coverage_dir = self.frontend_path / 'coverage'
        if not coverage_dir.exists():
            return 0.0
        
        # Look for coverage-summary.json
        summary_file = coverage_dir / 'coverage-summary.json'
        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    data = json.load(f)
                    # Get total coverage
                    total = data.get('total', {})
                    lines = total.get('lines', {})
                    pct = lines.get('pct', 0)
                    return float(pct)
            except Exception as e:
                logger.warning(f"Could not parse coverage-summary.json: {e}")
        
        return 0.0

