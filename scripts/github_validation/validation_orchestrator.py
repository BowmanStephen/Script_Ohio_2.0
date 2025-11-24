"""
Validation Orchestrator

Coordinates all validation modules and aggregates results.
Supports parallel execution where possible.
"""

import logging
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from github_validation.repository_health import RepositoryHealthValidator
from github_validation.build_validation import BuildValidator
from github_validation.test_validation import TestValidator
from github_validation.code_quality import CodeQualityValidator
from github_validation.security_validation import SecurityValidator
from github_validation.performance_validation import PerformanceValidator
from github_operations.git_utils import GitUtils

logger = logging.getLogger(__name__)


class ValidationOrchestrator:
    """Orchestrates all validation modules"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize validation orchestrator"""
        self.config = config
        self.git_utils = GitUtils()
        
        # Initialize validators
        self.repository_health = RepositoryHealthValidator(config, self.git_utils)
        self.build_validator = BuildValidator(config)
        self.test_validator = TestValidator(config)
        self.code_quality = CodeQualityValidator(config)
        self.security_validator = SecurityValidator(config)
        self.performance_validator = PerformanceValidator(config)
    
    def run_validation(
        self,
        validation_type: str = 'all',
        validation_scope: str = 'full'
    ) -> Dict[str, Any]:
        """Run validation suite"""
        logger.info(f"Running validation: type={validation_type}, scope={validation_scope}")
        
        results = {
            'overall_success': True,
            'validation_type': validation_type,
            'validation_scope': validation_scope
        }
        
        # Determine which validations to run
        validations_to_run = self._determine_validations(validation_type)
        
        # Run validations
        if 'repository_health' in validations_to_run:
            results['repository_health'] = self.repository_health.validate()
            if not results['repository_health'].get('success', False):
                results['overall_success'] = False
        
        if 'build' in validations_to_run:
            results['build'] = self.build_validator.validate(scope=validation_scope)
            if not results['build'].get('success', False):
                results['overall_success'] = False
        
        if 'tests' in validations_to_run:
            results['tests'] = self.test_validator.validate(scope=validation_scope)
            if not results['tests'].get('success', False):
                results['overall_success'] = False
            # Add coverage to top level
            if 'coverage' in results['tests']:
                results['coverage'] = results['tests']['coverage']
        
        if 'code_quality' in validations_to_run:
            results['code_quality'] = self.code_quality.validate(scope=validation_scope)
            if not results['code_quality'].get('success', False):
                results['overall_success'] = False
        
        if 'security' in validations_to_run:
            results['security'] = self.security_validator.validate(scope=validation_scope)
            if not results['security'].get('success', False):
                results['overall_success'] = False
        
        if 'performance' in validations_to_run:
            results['performance'] = self.performance_validator.validate(scope=validation_scope)
            if not results['performance'].get('success', False):
                results['overall_success'] = False
        
        return results
    
    def _determine_validations(self, validation_type: str) -> list:
        """Determine which validations to run based on type"""
        if validation_type == 'all':
            return [
                'repository_health',
                'build',
                'tests',
                'code_quality',
                'security',
                'performance'
            ]
        elif validation_type == 'build':
            return ['repository_health', 'build']
        elif validation_type == 'tests':
            return ['repository_health', 'tests']
        elif validation_type == 'security':
            return ['repository_health', 'security']
        elif validation_type == 'performance':
            return ['repository_health', 'performance']
        else:
            return ['repository_health']
    
    def run_parallel_validations(
        self,
        validation_scope: str = 'full'
    ) -> Dict[str, Any]:
        """Run validations in parallel where possible"""
        logger.info("Running parallel validations...")
        
        results = {
            'overall_success': True,
            'validation_scope': validation_scope
        }
        
        # Validations that can run in parallel
        parallel_tasks = {
            'build': lambda: self.build_validator.validate(scope=validation_scope),
            'security': lambda: self.security_validator.validate(scope=validation_scope),
            'code_quality': lambda: self.code_quality.validate(scope=validation_scope),
        }
        
        # Run parallel validations
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(task): name
                for name, task in parallel_tasks.items()
            }
            
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                    if not results[name].get('success', False):
                        results['overall_success'] = False
                except Exception as e:
                    logger.error(f"Error in {name} validation: {e}")
                    results[name] = {
                        'success': False,
                        'error': str(e)
                    }
                    results['overall_success'] = False
        
        # Run sequential validations (dependencies)
        results['repository_health'] = self.repository_health.validate()
        if not results['repository_health'].get('success', False):
            results['overall_success'] = False
        
        results['tests'] = self.test_validator.validate(scope=validation_scope)
        if not results['tests'].get('success', False):
            results['overall_success'] = False
        if 'coverage' in results['tests']:
            results['coverage'] = results['tests']['coverage']
        
        results['performance'] = self.performance_validator.validate(scope=validation_scope)
        if not results['performance'].get('success', False):
            results['overall_success'] = False
        
        return results

