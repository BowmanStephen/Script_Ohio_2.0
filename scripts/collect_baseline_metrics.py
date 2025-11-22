#!/usr/bin/env python3
"""
Collect Baseline Metrics for Consolidation Plan

Collects code complexity, LOC, test coverage, and performance baseline
before any consolidation changes are made.

Usage:
    python3 scripts/collect_baseline_metrics.py --output CONSOLIDATION_BASELINE_METRICS.json
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import ast
import os


def collect_loc(project_root: Path) -> Dict[str, Any]:
    """Collect lines of code metrics"""
    print("📊 Collecting lines of code...")
    
    metrics = {
        'total_lines': 0,
        'python_files': 0,
        'by_directory': {}
    }
    
    # Count Python files
    python_files = []
    for ext in ['*.py']:
        for file_path in project_root.rglob(ext):
            # Skip virtual environments and caches
            if any(skip in str(file_path) for skip in ['__pycache__', '.venv', 'venv', '.git']):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    line_count = len([l for l in lines if l.strip()])
                    
                    metrics['total_lines'] += line_count
                    metrics['python_files'] += 1
                    
                    # Count by directory
                    dir_name = str(file_path.parent.relative_to(project_root))
                    if dir_name not in metrics['by_directory']:
                        metrics['by_directory'][dir_name] = {'files': 0, 'lines': 0}
                    metrics['by_directory'][dir_name]['files'] += 1
                    metrics['by_directory'][dir_name]['lines'] += line_count
                    
                    python_files.append(str(file_path))
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
    
    metrics['python_file_list'] = python_files[:100]  # Sample first 100
    return metrics


def collect_cyclomatic_complexity(project_root: Path) -> Dict[str, Any]:
    """Collect cyclomatic complexity metrics"""
    print("🔍 Collecting cyclomatic complexity...")
    
    complexity_metrics = {
        'total_functions': 0,
        'total_classes': 0,
        'high_complexity_functions': [],  # Functions with complexity > 10
        'average_complexity': 0.0
    }
    
    complexities = []
    
    def calculate_complexity(node):
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, 
                                 ast.With, ast.AsyncFor, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    for py_file in project_root.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['__pycache__', '.venv', 'venv', '.git', 'node_modules']):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity_metrics['total_functions'] += 1
                        complexity = calculate_complexity(node)
                        complexities.append(complexity)
                        
                        if complexity > 10:
                            complexity_metrics['high_complexity_functions'].append({
                                'file': str(py_file.relative_to(project_root)),
                                'function': node.name,
                                'complexity': complexity,
                                'line': node.lineno
                            })
                    
                    elif isinstance(node, ast.ClassDef):
                        complexity_metrics['total_classes'] += 1
        except (SyntaxError, UnicodeDecodeError) as e:
            # Skip files with syntax errors or encoding issues
            pass
        except Exception as e:
            print(f"⚠️  Error analyzing {py_file}: {e}")
    
    if complexities:
        complexity_metrics['average_complexity'] = sum(complexities) / len(complexities)
        complexity_metrics['max_complexity'] = max(complexities)
        complexity_metrics['min_complexity'] = min(complexities)
    
    return complexity_metrics


def collect_test_coverage(project_root: Path) -> Dict[str, Any]:
    """Collect test coverage metrics"""
    print("🧪 Collecting test coverage...")
    
    coverage_metrics = {
        'test_files': 0,
        'test_functions': 0,
        'coverage_available': False,
        'coverage_percent': 0.0
    }
    
    # Count test files
    test_files = list(project_root.rglob('test_*.py'))
    test_files.extend(project_root.rglob('*_test.py'))
    test_files.extend((project_root / 'tests').rglob('*.py') if (project_root / 'tests').exists() else [])
    test_files.extend((project_root / 'agents' / 'tests').rglob('*.py') if (project_root / 'agents' / 'tests').exists() else [])
    
    coverage_metrics['test_files'] = len(set(test_files))
    
    # Try to get pytest coverage if available
    try:
        result = subprocess.run(
            ['python3', '-m', 'pytest', '--co', '-q'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            # Try to get actual coverage report
            coverage_result = subprocess.run(
                ['python3', '-m', 'pytest', '--cov=agents', '--cov=scripts', '--cov-report=json', '-q'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            if coverage_result.returncode == 0:
                try:
                    coverage_data = json.loads(coverage_result.stdout)
                    if 'totals' in coverage_data:
                        coverage_metrics['coverage_available'] = True
                        coverage_metrics['coverage_percent'] = coverage_data['totals'].get('percent_covered', 0.0)
                except json.JSONDecodeError:
                    pass
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  pytest not available or timed out, skipping coverage collection")
    
    return coverage_metrics


def collect_performance_baseline(project_root: Path) -> Dict[str, Any]:
    """Collect performance baseline metrics"""
    print("⏱️  Collecting performance baseline...")
    
    performance_metrics = {
        'test_runtime': 0.0,
        'import_time': 0.0,
        'agent_instantiation_time': 0.0,
        'orchestrator_startup_time': 0.0
    }
    
    # Test runtime
    try:
        start = time.time()
        result = subprocess.run(
            ['python3', '-m', 'pytest', 'tests/', 'agents/tests/', '-q', '--tb=no'],
            cwd=project_root,
            capture_output=True,
            timeout=300
        )
        performance_metrics['test_runtime'] = time.time() - start
        performance_metrics['test_exit_code'] = result.returncode
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Test execution timed out or pytest not available")
        performance_metrics['test_runtime'] = -1.0
    
    # Import time for key modules
    try:
        start = time.time()
        import sys
        sys.path.insert(0, str(project_root))
        from agents.analytics_orchestrator import AnalyticsOrchestrator
        performance_metrics['import_time'] = time.time() - start
        
        # Orchestrator startup time
        start = time.time()
        orchestrator = AnalyticsOrchestrator()
        performance_metrics['orchestrator_startup_time'] = time.time() - start
        performance_metrics['orchestrator_available'] = True
    except Exception as e:
        print(f"⚠️  Could not measure orchestrator performance: {e}")
        performance_metrics['orchestrator_available'] = False
    
    return performance_metrics


def collect_file_counts(project_root: Path) -> Dict[str, Any]:
    """Collect file count metrics"""
    print("📁 Collecting file counts...")
    
    file_counts = {
        'total_python_files': 0,
        'total_test_files': 0,
        'total_markdown_files': 0,
        'total_notebook_files': 0,
        'by_directory': {}
    }
    
    for py_file in project_root.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['__pycache__', '.venv', 'venv', '.git']):
            continue
        file_counts['total_python_files'] += 1
        
        if 'test' in py_file.name.lower():
            file_counts['total_test_files'] += 1
    
    for md_file in project_root.rglob('*.md'):
        if any(skip in str(md_file) for skip in ['.git', 'node_modules']):
            continue
        file_counts['total_markdown_files'] += 1
    
    for nb_file in project_root.rglob('*.ipynb'):
        if any(skip in str(nb_file) for skip in ['.git', 'node_modules']):
            continue
        file_counts['total_notebook_files'] += 1
    
    return file_counts


def main():
    parser = argparse.ArgumentParser(
        description='Collect baseline metrics for consolidation plan'
    )
    parser.add_argument(
        '--output', '-o',
        default='CONSOLIDATION_BASELINE_METRICS.json',
        help='Output file path for metrics JSON'
    )
    parser.add_argument(
        '--project-root',
        default='.',
        help='Project root directory (default: current directory)'
    )
    
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    
    if not project_root.exists():
        print(f"❌ Project root does not exist: {project_root}")
        sys.exit(1)
    
    print("🏈 Script Ohio 2.0 - Baseline Metrics Collection")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print()
    
    # Collect all metrics
    baseline_metrics = {
        'collection_timestamp': time.time(),
        'collection_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'project_root': str(project_root),
        'loc_metrics': collect_loc(project_root),
        'complexity_metrics': collect_cyclomatic_complexity(project_root),
        'coverage_metrics': collect_test_coverage(project_root),
        'performance_metrics': collect_performance_baseline(project_root),
        'file_counts': collect_file_counts(project_root)
    }
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(baseline_metrics, f, indent=2, default=str)
    
    print()
    print("=" * 60)
    print("✅ Baseline metrics collected successfully!")
    print(f"📄 Output: {output_path}")
    print()
    print("Summary:")
    print(f"  - Python files: {baseline_metrics['file_counts']['total_python_files']}")
    print(f"  - Total lines: {baseline_metrics['loc_metrics']['total_lines']:,}")
    print(f"  - Test files: {baseline_metrics['file_counts']['total_test_files']}")
    print(f"  - Functions: {baseline_metrics['complexity_metrics']['total_functions']}")
    print(f"  - Average complexity: {baseline_metrics['complexity_metrics']['average_complexity']:.2f}")
    if baseline_metrics['coverage_metrics']['coverage_available']:
        print(f"  - Test coverage: {baseline_metrics['coverage_metrics']['coverage_percent']:.1f}%")
    if baseline_metrics['performance_metrics']['test_runtime'] > 0:
        print(f"  - Test runtime: {baseline_metrics['performance_metrics']['test_runtime']:.2f}s")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

