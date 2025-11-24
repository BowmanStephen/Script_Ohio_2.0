"""
Performance Validation

Validates performance metrics:
- React bundle size analysis (244KB limit)
- Performance regression detection
"""

import subprocess
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PerformanceValidator:
    """Validates performance metrics"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize performance validator"""
        self.config = config
        self.project_root = Path.cwd()
        self.frontend_path = self.project_root / config['project_structure']['frontend_path']
        self.frontend_dist = self.project_root / config['project_structure']['frontend_dist']
        self.bundle_size_limit = config.get('bundle_size_limit_kb', 244) * 1024  # Convert to bytes
        self.timeout = config['validation_timeouts'].get('performance', 60)
    
    def validate(self, scope: str = 'full') -> Dict[str, Any]:
        """Run performance validation"""
        results = {
            'success': True,
            'frontend': {},
            'errors': []
        }
        
        if scope in ['full', 'frontend']:
            frontend_result = self._validate_frontend_performance()
            results['frontend'] = frontend_result
            if not frontend_result.get('success', False):
                results['success'] = False
                results['errors'].append('Frontend performance validation failed')
        
        # Python performance validation could be added here
        if scope == 'python':
            results['python'] = {
                'success': True,
                'message': 'Python performance validation not implemented'
            }
        
        return results
    
    def _validate_frontend_performance(self) -> Dict[str, Any]:
        """Validate React frontend performance"""
        logger.info("Validating React frontend performance...")
        
        if not self.frontend_dist.exists():
            return {
                'success': False,
                'error': f"Frontend dist directory does not exist: {self.frontend_dist}. Run build first."
            }
        
        # Analyze bundle sizes
        bundle_analysis = self._analyze_bundle_sizes()
        
        # Check if any bundle exceeds limit
        exceeded = [
            name for name, size in bundle_analysis['bundles'].items()
            if size > self.bundle_size_limit
        ]
        
        success = len(exceeded) == 0
        
        return {
            'success': success,
            'bundle_analysis': bundle_analysis,
            'limit_kb': self.bundle_size_limit / 1024,
            'exceeded_bundles': exceeded,
            'message': f"Bundle size: {bundle_analysis['total_size_kb']:.1f}KB "
                      f"({'within' if success else 'exceeds'} {self.bundle_size_limit / 1024:.1f}KB limit)"
        }
    
    def _analyze_bundle_sizes(self) -> Dict[str, Any]:
        """Analyze bundle file sizes"""
        bundles = {}
        total_size = 0
        
        # Find all JS and CSS files in dist
        for file_path in self.frontend_dist.rglob('*'):
            if file_path.is_file():
                size = file_path.stat().st_size
                total_size += size
                
                # Categorize by file type
                if file_path.suffix in ['.js', '.mjs']:
                    file_name = file_path.name
                    if file_name not in bundles or size > bundles[file_name]:
                        bundles[file_name] = size
                elif file_path.suffix == '.css':
                    file_name = file_path.name
                    if file_name not in bundles or size > bundles[file_name]:
                        bundles[file_name] = size
        
        # Sort bundles by size
        sorted_bundles = dict(sorted(bundles.items(), key=lambda x: x[1], reverse=True))
        
        return {
            'bundles': sorted_bundles,
            'total_size': total_size,
            'total_size_kb': total_size / 1024,
            'bundle_count': len(bundles),
            'largest_bundle': max(bundles.items(), key=lambda x: x[1])[0] if bundles else None,
            'largest_size_kb': (max(bundles.values()) / 1024) if bundles else 0
        }
    
    def _check_performance_regression(self) -> Dict[str, Any]:
        """Check for performance regressions (placeholder for future implementation)"""
        # This would compare current performance metrics with baseline
        # For now, return a placeholder
        return {
            'success': True,
            'message': 'Performance regression detection not yet implemented',
            'skipped': True
        }

