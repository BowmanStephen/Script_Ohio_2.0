#!/usr/bin/env python3
"""
Router Instrumentation Analysis Script

Parses instrumentation logs from RequestRouter and AnalyticsOrchestrator
to validate simplification assumptions before removing router complexity.

Usage:
    python scripts/analyze_router_instrumentation.py [--log-file LOG_FILE] [--output OUTPUT_FILE]
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime


class RouterInstrumentationAnalyzer:
    """Analyzes router instrumentation logs and generates threshold-based reports"""
    
    def __init__(self, log_file: str = "logs/app.log"):
        self.log_file = Path(log_file)
        self.metrics = {
            'submit_count': 0,
            'process_count': 0,
            'permission_denials': 0,
            'permission_grants': 0,
            'agent_not_found_count': 0,
            'priority_sorts': 0,
            'errors_caught': 0,
            'status_retrieved_count': 0,
            'router_calls': 0,
            'queue_sizes_at_submit': [],
            'queue_sizes_at_process': [],
            'router_overhead_ms': [],
            'orchestrator_requests': []
        }
        
        # Decision thresholds
        self.thresholds = {
            'permission_denials_threshold': 0,
            'priority_sorts_threshold': 0,
            'queue_always_zero': True,
            'router_overhead_threshold_ms': 5.0,
            'agent_not_found_threshold': 0,
            'errors_caught_threshold': 0
        }
        
        # Log patterns
        self.patterns = {
            'router_audit': re.compile(r'\[ROUTER_AUDIT\]'),
            'orchestrator_audit': re.compile(r'\[ORCHESTRATOR_AUDIT\]'),
            'submit': re.compile(r'SUBMIT:\s+request_id=(\S+)\s+queue_size=(\d+)\s+priority=(\d+)'),
            'process_start': re.compile(r'PROCESS_START:\s+queue_size=(\d+)'),
            'permission_denied': re.compile(r'PERMISSION_DENIED:\s+request_id=(\S+)\s+agent_type=(\S+)'),
            'permission_granted': re.compile(r'PERMISSION_GRANTED:\s+request_id=(\S+)\s+agent_type=(\S+)'),
            'agent_not_found': re.compile(r'AGENT_NOT_FOUND:\s+request_id=(\S+)\s+agent_type=(\S+)'),
            'priority_sort': re.compile(r'PRIORITY_SORT:\s+queue_size=(\d+)'),
            'error_caught': re.compile(r'ERROR_CAUGHT:\s+request_id=(\S+)\s+error=(.+)'),
            'status_retrieved': re.compile(r'STATUS_RETRIEVED:\s+request_id=(\S+)'),
            'router_call': re.compile(r'ROUTER_CALL:\s+request_id=(\S+)(?:\s+agent_count=(\d+))?(?:\s+action=(\S+))?(?:\s+router_overhead_ms=([\d.]+))?(?:\s+total_time_ms=([\d.]+))?(?:\s+successful_agents=(\d+))?(?:\s+failed_agents=(\d+))?'),
            'overhead': re.compile(r'overhead_ms=([\d.]+)')
        }
    
    def parse_log_file(self) -> None:
        """Parse the log file and extract metrics"""
        if not self.log_file.exists():
            print(f"Warning: Log file {self.log_file} does not exist")
            return
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                self._parse_line(line)
    
    def _parse_line(self, line: str) -> None:
        """Parse a single log line"""
        # Check for router audit
        if self.patterns['router_audit'].search(line):
            # Submit pattern
            match = self.patterns['submit'].search(line)
            if match:
                self.metrics['submit_count'] += 1
                queue_size = int(match.group(2))
                self.metrics['queue_sizes_at_submit'].append(queue_size)
            
            # Process start pattern
            match = self.patterns['process_start'].search(line)
            if match:
                self.metrics['process_count'] += 1
                queue_size = int(match.group(1))
                self.metrics['queue_sizes_at_process'].append(queue_size)
            
            # Permission denied
            if self.patterns['permission_denied'].search(line):
                self.metrics['permission_denials'] += 1
            
            # Permission granted
            if self.patterns['permission_granted'].search(line):
                self.metrics['permission_grants'] += 1
            
            # Agent not found
            if self.patterns['agent_not_found'].search(line):
                self.metrics['agent_not_found_count'] += 1
            
            # Priority sort
            if self.patterns['priority_sort'].search(line):
                self.metrics['priority_sorts'] += 1
            
            # Error caught
            if self.patterns['error_caught'].search(line):
                self.metrics['errors_caught'] += 1
            
            # Status retrieved
            if self.patterns['status_retrieved'].search(line):
                self.metrics['status_retrieved_count'] += 1
            
            # Overhead extraction
            match = self.patterns['overhead'].search(line)
            if match:
                overhead = float(match.group(1))
                self.metrics['router_overhead_ms'].append(overhead)
        
        # Check for orchestrator audit
        if self.patterns['orchestrator_audit'].search(line):
            match = self.patterns['router_call'].search(line)
            if match:
                self.metrics['router_calls'] += 1
                request_id = match.group(1)
                
                # Extract additional fields if present
                call_data = {'request_id': request_id}
                if match.group(2):  # agent_count
                    call_data['agent_count'] = int(match.group(2))
                if match.group(3):  # action
                    call_data['action'] = match.group(3)
                if match.group(4):  # router_overhead_ms
                    call_data['router_overhead_ms'] = float(match.group(4))
                if match.group(5):  # total_time_ms
                    call_data['total_time_ms'] = float(match.group(5))
                if match.group(6):  # successful_agents
                    call_data['successful_agents'] = int(match.group(6))
                if match.group(7):  # failed_agents
                    call_data['failed_agents'] = int(match.group(7))
                
                self.metrics['orchestrator_requests'].append(call_data)
    
    def evaluate_thresholds(self) -> Dict[str, Any]:
        """Evaluate metrics against decision thresholds"""
        results = {}
        
        # Permission denials threshold
        results['permission_denials'] = {
            'metric': self.metrics['permission_denials'],
            'threshold': self.thresholds['permission_denials_threshold'],
            'pass': self.metrics['permission_denials'] <= self.thresholds['permission_denials_threshold'],
            'message': f"Permission denials: {self.metrics['permission_denials']} (threshold: {self.thresholds['permission_denials_threshold']})"
        }
        
        # Priority sorts threshold
        results['priority_sorts'] = {
            'metric': self.metrics['priority_sorts'],
            'threshold': self.thresholds['priority_sorts_threshold'],
            'pass': self.metrics['priority_sorts'] <= self.thresholds['priority_sorts_threshold'],
            'message': f"Priority sorts: {self.metrics['priority_sorts']} (threshold: {self.thresholds['priority_sorts_threshold']})"
        }
        
        # Queue always zero
        max_queue_submit = max(self.metrics['queue_sizes_at_submit']) if self.metrics['queue_sizes_at_submit'] else 0
        max_queue_process = max(self.metrics['queue_sizes_at_process']) if self.metrics['queue_sizes_at_process'] else 0
        max_queue = max(max_queue_submit, max_queue_process)
        results['queue_always_zero'] = {
            'metric': max_queue,
            'threshold': 0 if self.thresholds['queue_always_zero'] else None,
            'pass': max_queue == 0 if self.thresholds['queue_always_zero'] else True,
            'message': f"Max queue size: {max_queue} (expecting: 0)"
        }
        
        # Router overhead threshold
        avg_overhead = (
            sum(self.metrics['router_overhead_ms']) / len(self.metrics['router_overhead_ms'])
            if self.metrics['router_overhead_ms'] else 0.0
        )
        max_overhead = max(self.metrics['router_overhead_ms']) if self.metrics['router_overhead_ms'] else 0.0
        results['router_overhead'] = {
            'metric_avg': avg_overhead,
            'metric_max': max_overhead,
            'threshold': self.thresholds['router_overhead_threshold_ms'],
            'pass': avg_overhead <= self.thresholds['router_overhead_threshold_ms'],
            'message': f"Average router overhead: {avg_overhead:.2f}ms, Max: {max_overhead:.2f}ms (threshold: {self.thresholds['router_overhead_threshold_ms']}ms)"
        }
        
        # Agent not found threshold
        results['agent_not_found'] = {
            'metric': self.metrics['agent_not_found_count'],
            'threshold': self.thresholds['agent_not_found_threshold'],
            'pass': self.metrics['agent_not_found_count'] <= self.thresholds['agent_not_found_threshold'],
            'message': f"Agent not found count: {self.metrics['agent_not_found_count']} (threshold: {self.thresholds['agent_not_found_threshold']})"
        }
        
        # Errors caught threshold
        results['errors_caught'] = {
            'metric': self.metrics['errors_caught'],
            'threshold': self.thresholds['errors_caught_threshold'],
            'pass': self.metrics['errors_caught'] <= self.thresholds['errors_caught_threshold'],
            'message': f"Errors caught: {self.metrics['errors_caught']} (threshold: {self.thresholds['errors_caught_threshold']})"
        }
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        threshold_results = self.evaluate_thresholds()
        
        # Calculate statistics
        avg_queue_submit = (
            sum(self.metrics['queue_sizes_at_submit']) / len(self.metrics['queue_sizes_at_submit'])
            if self.metrics['queue_sizes_at_submit'] else 0.0
        )
        avg_queue_process = (
            sum(self.metrics['queue_sizes_at_process']) / len(self.metrics['queue_sizes_at_process'])
            if self.metrics['queue_sizes_at_process'] else 0.0
        )
        avg_overhead = (
            sum(self.metrics['router_overhead_ms']) / len(self.metrics['router_overhead_ms'])
            if self.metrics['router_overhead_ms'] else 0.0
        )
        
        # Overall pass/fail
        all_pass = all(result['pass'] for result in threshold_results.values())
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'log_file': str(self.log_file),
            'summary': {
                'all_thresholds_passed': all_pass,
                'total_submits': self.metrics['submit_count'],
                'total_processes': self.metrics['process_count'],
                'total_router_calls': self.metrics['router_calls'],
            },
            'metrics': {
                'submit_count': self.metrics['submit_count'],
                'process_count': self.metrics['process_count'],
                'permission_denials': self.metrics['permission_denials'],
                'permission_grants': self.metrics['permission_grants'],
                'agent_not_found_count': self.metrics['agent_not_found_count'],
                'priority_sorts': self.metrics['priority_sorts'],
                'errors_caught': self.metrics['errors_caught'],
                'status_retrieved_count': self.metrics['status_retrieved_count'],
                'router_calls': self.metrics['router_calls'],
                'average_queue_size_at_submit': round(avg_queue_submit, 2),
                'average_queue_size_at_process': round(avg_queue_process, 2),
                'max_queue_size': max(
                    max(self.metrics['queue_sizes_at_submit']) if self.metrics['queue_sizes_at_submit'] else 0,
                    max(self.metrics['queue_sizes_at_process']) if self.metrics['queue_sizes_at_process'] else 0
                ),
                'average_router_overhead_ms': round(avg_overhead, 2),
                'max_router_overhead_ms': round(
                    max(self.metrics['router_overhead_ms']) if self.metrics['router_overhead_ms'] else 0.0,
                    2
                )
            },
            'threshold_evaluation': threshold_results,
            'recommendation': (
                "✅ All thresholds passed. Router simplification is SAFE to proceed."
                if all_pass
                else "❌ Some thresholds failed. Review metrics before simplifying router."
            )
        }
        
        return report
    
    def print_human_readable_summary(self, report: Dict[str, Any]) -> None:
        """Print human-readable summary of the report"""
        print("\n" + "="*80)
        print("ROUTER INSTRUMENTATION ANALYSIS REPORT")
        print("="*80)
        print(f"\nLog File: {report['log_file']}")
        print(f"Analysis Time: {report['timestamp']}")
        
        print("\n" + "-"*80)
        print("SUMMARY")
        print("-"*80)
        print(f"All Thresholds Passed: {'✅ YES' if report['summary']['all_thresholds_passed'] else '❌ NO'}")
        print(f"Total Submits: {report['summary']['total_submits']}")
        print(f"Total Processes: {report['summary']['total_processes']}")
        print(f"Total Router Calls: {report['summary']['total_router_calls']}")
        
        print("\n" + "-"*80)
        print("METRICS")
        print("-"*80)
        metrics = report['metrics']
        print(f"Submit Count: {metrics['submit_count']}")
        print(f"Process Count: {metrics['process_count']}")
        print(f"Permission Denials: {metrics['permission_denials']}")
        print(f"Permission Grants: {metrics['permission_grants']}")
        print(f"Agent Not Found: {metrics['agent_not_found_count']}")
        print(f"Priority Sorts: {metrics['priority_sorts']}")
        print(f"Errors Caught: {metrics['errors_caught']}")
        print(f"Status Queries: {metrics['status_retrieved_count']}")
        print(f"Average Queue Size (Submit): {metrics['average_queue_size_at_submit']}")
        print(f"Average Queue Size (Process): {metrics['average_queue_size_at_process']}")
        print(f"Max Queue Size: {metrics['max_queue_size']}")
        print(f"Average Router Overhead: {metrics['average_router_overhead_ms']}ms")
        print(f"Max Router Overhead: {metrics['max_router_overhead_ms']}ms")
        
        print("\n" + "-"*80)
        print("THRESHOLD EVALUATION")
        print("-"*80)
        for name, result in report['threshold_evaluation'].items():
            status = "✅ PASS" if result['pass'] else "❌ FAIL"
            print(f"{status} - {result['message']}")
        
        print("\n" + "-"*80)
        print("RECOMMENDATION")
        print("-"*80)
        print(report['recommendation'])
        print("="*80 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze router instrumentation logs"
    )
    parser.add_argument(
        '--log-file',
        default='logs/app.log',
        help='Path to log file to analyze (default: logs/app.log)'
    )
    parser.add_argument(
        '--output',
        help='Output JSON report file (default: print to stdout)'
    )
    parser.add_argument(
        '--human-readable',
        action='store_true',
        help='Print human-readable summary'
    )
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = RouterInstrumentationAnalyzer(log_file=args.log_file)
    
    # Parse log file
    print(f"Parsing log file: {args.log_file}")
    analyzer.parse_log_file()
    
    # Generate report
    report = analyzer.generate_report()
    
    # Print human-readable summary
    if args.human_readable or not args.output:
        analyzer.print_human_readable_summary(report)
    
    # Output JSON report
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"JSON report written to: {output_path}")
    else:
        # Print JSON to stdout if no output file specified
        print("\nJSON Report:")
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

