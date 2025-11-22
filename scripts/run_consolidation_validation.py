#!/usr/bin/env python3
"""
Consolidation Validation Script

Runs comprehensive validation for consolidation plan:
- Syntax validation via py_compile
- Test execution via pytest
- Import validation
- Performance comparison

Usage:
    python3 scripts/run_consolidation_validation.py [--baseline BASELINE.json] [--output OUTPUT.json]
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional


def run_syntax_validation(project_root: Path) -> Dict[str, Any]:
    """Run syntax validation on all Python files"""
    print("🔍 Running syntax validation...")
    
    results = {
        'total_files': 0,
        'valid_files': 0,
        'invalid_files': [],
        'errors': []
    }
    
    python_files = []
    for py_file in project_root.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['__pycache__', '.venv', 'venv', '.git', 'node_modules']):
            continue
        python_files.append(py_file)
    
    results['total_files'] = len(python_files)
    
    for py_file in python_files:
        try:
            result = subprocess.run(
                ['python3', '-m', 'py_compile', str(py_file)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                results['valid_files'] += 1
            else:
                results['invalid_files'].append(str(py_file.relative_to(project_root)))
                results['errors'].append({
                    'file': str(py_file.relative_to(project_root)),
                    'error': result.stderr
                })
        except subprocess.TimeoutExpired:
            results['invalid_files'].append(str(py_file.relative_to(project_root)))
            results['errors'].append({
                'file': str(py_file.relative_to(project_root)),
                'error': 'Timeout during compilation'
            })
        except Exception as e:
            results['invalid_files'].append(str(py_file.relative_to(project_root)))
            results['errors'].append({
                'file': str(py_file.relative_to(project_root)),
                'error': str(e)
            })
    
    return results


def run_test_execution(project_root: Path) -> Dict[str, Any]:
    """Run test suite via pytest"""
    print("🧪 Running test suite...")
    
    results = {
        'success': False,
        'test_count': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'execution_time': 0.0,
        'errors': []
    }
    
    try:
        start_time = time.time()
        result = subprocess.run(
            ['python3', '-m', 'pytest', 'tests/', 'agents/tests/', '-v', '--tb=short', '--no-header'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=600
        )
        results['execution_time'] = time.time() - start_time
        results['success'] = result.returncode == 0
        results['exit_code'] = result.returncode
        
        # Parse pytest output (basic parsing)
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if ' passed' in line or ' failed' in line or ' skipped' in line:
                # Try to extract counts
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        if 'passed' in line.lower():
                            results['passed'] = int(part)
                        elif 'failed' in line.lower():
                            results['failed'] = int(part)
                        elif 'skipped' in line.lower():
                            results['skipped'] = int(part)
        
        results['test_count'] = results['passed'] + results['failed'] + results['skipped']
        
        if result.stderr:
            results['errors'].append(result.stderr)
    except subprocess.TimeoutExpired:
        results['errors'].append('Test execution timed out after 600 seconds')
    except FileNotFoundError:
        results['errors'].append('pytest not found - install with: pip install pytest')
    except Exception as e:
        results['errors'].append(f'Test execution error: {str(e)}')
    
    return results


def run_import_validation(project_root: Path) -> Dict[str, Any]:
    """Validate critical imports"""
    print("📦 Validating critical imports...")
    
    results = {
        'total_imports': 0,
        'successful_imports': 0,
        'failed_imports': [],
        'errors': []
    }
    
    critical_imports = [
        'agents.analytics_orchestrator',
        'agents.core.agent_framework',
        'agents.learning_navigator_agent',
        'src.models.execution.engine',
        'agents.insight_generator_agent',
    ]
    
    results['total_imports'] = len(critical_imports)
    
    for module_name in critical_imports:
        try:
            result = subprocess.run(
                ['python3', '-c', f'import sys; sys.path.insert(0, "."); import {module_name}'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                results['successful_imports'] += 1
            else:
                results['failed_imports'].append(module_name)
                results['errors'].append({
                    'module': module_name,
                    'error': result.stderr
                })
        except Exception as e:
            results['failed_imports'].append(module_name)
            results['errors'].append({
                'module': module_name,
                'error': str(e)
            })
    
    return results


def compare_performance(baseline_file: Optional[Path], current_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Compare current performance to baseline"""
    print("⏱️  Comparing performance to baseline...")
    
    comparison = {
        'baseline_available': False,
        'regressions': [],
        'improvements': [],
        'unchanged': []
    }
    
    if not baseline_file or not baseline_file.exists():
        comparison['message'] = 'No baseline file provided - skipping comparison'
        return comparison
    
    try:
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)
        
        comparison['baseline_available'] = True
        baseline_perf = baseline.get('performance_metrics', {})
        current_perf = current_metrics.get('performance_metrics', {})
        
        # Compare test runtime
        if 'test_runtime' in baseline_perf and 'test_runtime' in current_perf:
            baseline_time = baseline_perf['test_runtime']
            current_time = current_perf['test_runtime']
            if current_time > 0 and baseline_time > 0:
                if current_time > baseline_time * 1.1:  # 10% threshold
                    comparison['regressions'].append({
                        'metric': 'test_runtime',
                        'baseline': baseline_time,
                        'current': current_time,
                        'increase_percent': ((current_time - baseline_time) / baseline_time) * 100
                    })
                elif current_time < baseline_time * 0.9:
                    comparison['improvements'].append({
                        'metric': 'test_runtime',
                        'baseline': baseline_time,
                        'current': current_time,
                        'decrease_percent': ((baseline_time - current_time) / baseline_time) * 100
                    })
                else:
                    comparison['unchanged'].append('test_runtime')
    except Exception as e:
        comparison['error'] = f'Error comparing to baseline: {str(e)}'
    
    return comparison


def main():
    parser = argparse.ArgumentParser(
        description='Run consolidation validation'
    )
    parser.add_argument(
        '--baseline',
        help='Path to baseline metrics JSON file for comparison'
    )
    parser.add_argument(
        '--output', '-o',
        default='CONSOLIDATION_VALIDATION_REPORT.json',
        help='Output file for validation report'
    )
    parser.add_argument(
        '--project-root',
        default='.',
        help='Project root directory'
    )
    
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    
    print("🏈 Script Ohio 2.0 - Consolidation Validation")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print()
    
    # Run validations
    validation_results = {
        'validation_timestamp': time.time(),
        'validation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'project_root': str(project_root),
        'syntax_validation': run_syntax_validation(project_root),
        'test_execution': run_test_execution(project_root),
        'import_validation': run_import_validation(project_root)
    }
    
    # Performance comparison if baseline provided
    if args.baseline:
        baseline_path = Path(args.baseline)
        validation_results['performance_comparison'] = compare_performance(
            baseline_path,
            validation_results
        )
    
    # Calculate overall status
    syntax_ok = validation_results['syntax_validation']['invalid_files'] == []
    tests_ok = validation_results['test_execution']['success']
    imports_ok = validation_results['import_validation']['failed_imports'] == []
    
    validation_results['overall_status'] = 'pass' if (syntax_ok and tests_ok and imports_ok) else 'fail'
    validation_results['summary'] = {
        'syntax_valid': syntax_ok,
        'tests_passing': tests_ok,
        'imports_valid': imports_ok,
        'total_issues': (
            len(validation_results['syntax_validation']['invalid_files']) +
            validation_results['test_execution']['failed'] +
            len(validation_results['import_validation']['failed_imports'])
        )
    }
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    print()
    print("=" * 60)
    print("✅ Validation complete!")
    print(f"📄 Report: {output_path}")
    print()
    print("Summary:")
    print(f"  - Syntax: {'✅ PASS' if syntax_ok else '❌ FAIL'} ({validation_results['syntax_validation']['valid_files']}/{validation_results['syntax_validation']['total_files']} files)")
    print(f"  - Tests: {'✅ PASS' if tests_ok else '❌ FAIL'} ({validation_results['test_execution']['passed']} passed, {validation_results['test_execution']['failed']} failed)")
    print(f"  - Imports: {'✅ PASS' if imports_ok else '❌ FAIL'} ({validation_results['import_validation']['successful_imports']}/{validation_results['import_validation']['total_imports']} modules)")
    print(f"  - Overall: {'✅ PASS' if validation_results['overall_status'] == 'pass' else '❌ FAIL'}")
    
    return 0 if validation_results['overall_status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())

