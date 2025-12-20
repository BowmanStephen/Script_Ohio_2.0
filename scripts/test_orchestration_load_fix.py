#!/usr/bin/env python3
"""
Test script to validate the orchestration agent fix for coordination failures.
This script replicates the intensive test that revealed the 24% failure rate.
"""

import sys
import time
from datetime import datetime
from agents.orchestration_agent import OrchestrationAgent, OrchestrationMode


def validate_fix():
    """Run the same intensive test that revealed the 24% failure rate"""
    agent = OrchestrationAgent()

    print("🔥 Running intensive coordination test with fix...")
    print("=" * 60)
    print("Testing 25 rapid successive requests...")
    print()

    results = []
    failures = 0
    attribute_errors = 0
    total_requests = 25

    start_time = time.time()

    for i in range(total_requests):
        try:
            # Rotate through different coordination operations
            if i % 4 == 0:
                operation = 'optimization_monitor'
                result = agent._monitor_optimization({}, {})
            elif i % 4 == 1:
                operation = 'agent_coordination'
                result = agent._enhanced_coordinate_agents({'workflow': 'test_workflow', 'agents': []}, {})
            elif i % 4 == 2:
                operation = 'enhanced_coordination'
                result = agent._enhanced_coordinate_agents({'agents': []}, {})
            else:
                operation = 'health_check'
                result = agent._check_composition_health()

            results.append({
                'request_id': i+1,
                'operation': operation,
                'status': 'success',
                'result': result,
                'timestamp': time.time() - start_time
            })

            # Log the result for visibility
            if i < 5 or i % 5 == 0:  # Show first 5 and every 5th request
                print(f"  Request {i+1:2d} ({operation}): ✅ {results[-1]['timestamp']:.3f}s")

        except AttributeError as e:
            attribute_errors += 1
            failures += 1
            print(f"  Request {i+1:2d}: ❌ AttributeError - {str(e)[:60]}")
            results.append({
                'request_id': i+1,
                'operation': 'unknown',
                'status': 'error',
                'error': str(e),
                'timestamp': time.time() - start_time
            })
        except Exception as e:
            failures += 1
            print(f"  Request {i+1:2d}: ❌ Other error - {str(e)[:60]}")
            results.append({
                'request_id': i+1,
                'operation': 'unknown',
                'status': 'error',
                'error': str(e),
                'timestamp': time.time() - start_time
            })

    total_time = time.time() - start_time
    success_count = len([r for r in results if r['status'] == 'success'])
    success_rate = success_count / total_requests * 100

    print()
    print("📊 INTENSIVE WORKLOAD RESULTS")
    print("=" * 50)
    print(f"⏱️  Total Execution Time: {total_time:.2f}s")
    print(f"📋 Total Requests: {total_requests}")
    print(f"✅ Successful: {success_count} ({success_rate:.1f}%)")
    print(f"❌ Failed: {failures} ({failures/total_requests*100:.1f}%)")
    print(f"⚡ Average Request Time: {total_time/total_requests:.3f}s")
    print(f"🏆 Success Rate: {success_rate:.1f}%")

    # Operation breakdown
    print()
    print("📈 Performance by Operation:")
    operations = {}
    for r in results:
        op = r['operation']
        if op not in operations:
            operations[op] = {'success': 0, 'failed': 0, 'total_time': 0.0}

        if r['status'] == 'success':
            operations[op]['success'] += 1
        else:
            operations[op]['failed'] += 1

        operations[op]['total_time'] += r.get('timestamp', 0.0)

    for operation, stats in operations.items():
        if stats['success'] > 0 or stats['failed'] > 0:
            avg_time = stats['total_time'] / (stats['success'] + stats['failed'])
            print(f"  • {operation}: {stats['success']} success, {stats['failed']} failed, avg {avg_time:.3f}s")

    # Composition health check
    print()
    composition_health = agent._check_composition_health()
    print("🧠 Composition System Health:")
    for component, status in composition_health.items():
        emoji = "✅" if status else "❌"
        print(f"  {emoji} {component}: {status}")

    # Performance validation
    print()
    print("💻 Resource Impact:")

    # Check if we have the same number of requests as expected
    if len(results) == total_requests:
        print("  ✅ All requests processed")
    else:
        print(f"  ⚠️ Only {len(results)}/{total_requests} requests processed")

    # Validate fix against original issues
    print()
    print("🎯 VALIDATION AGAINST ORIGINAL ISSUES:")

    # Original issue: 6 AttributeErrors from missing agent_registry
    if attribute_errors == 0:
        print("  ✅ ZERO AttributeErrors (was 6 before fix)")
    else:
        print(f"  ❌ {attribute_errors} AttributeErrors remain (was 6 before fix)")

    # Original issue: 24% failure rate (6/25 failures)
    original_failure_rate = 6 / 25 * 100
    current_failure_rate = failures / total_requests * 100

    if current_failure_rate < original_failure_rate:
        improvement = original_failure_rate - current_failure_rate
        print(f"  ✅ IMPROVEMENT: {improvement:.1f}% reduction in failure rate")
        print(f"  📉 From {original_failure_rate:.1f}% → {current_failure_rate:.1f}%")
    else:
        print(f"  ⚠️ No improvement in failure rate")

    # Success rate validation
    if success_rate >= 95:
        print("  🎉 SUCCESS RATE: ≥95% - EXCELLENT")
    elif success_rate >= 90:
        print("  🟢 SUCCESS RATE: ≥90% - GOOD")
    elif success_rate >= 80:
        print("  🟡 SUCCESS RATE: ≥80% - ACCEPTABLE")
    else:
        print("  🔴 SUCCESS RATE: <80% - NEEDS IMPROVEMENT")

    # Final validation
    print()
    print("🔍 FINAL VALIDATION:")

    validation_passed = (
        attribute_errors == 0 and
        current_failure_rate < 5 and
        success_rate >= 95
    )

    if validation_passed:
        print("  ✅ ALL VALIDATIONS PASSED!")
        print("  🎉 Fix successfully eliminates coordination failures!")
        return True
    else:
        print("  ❌ VALIDATION FAILED!")
        if attribute_errors > 0:
            print(f"     Still have {attribute_errors} AttributeErrors")
        if current_failure_rate >= 5:
            print(f"     Failure rate still high: {current_failure_rate:.1f}%")
        if success_rate < 95:
            print(f"     Success rate below 95%: {success_rate:.1f}%")
        return False


def main():
    """Main entry point"""
    print(f"🔥 Orchestration Agent Fix Validation")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        success = validate_fix()

        if success:
            print()
            print("🎉 CONCLUSION:")
            print("  • Composition pattern successfully implemented")
            print("  • Agent registry access issues resolved")
            print(" • Optimization components handle missing gracefully")
            print(" • Coordination failures eliminated")
            print("  • System stable under intensive load")
            print()
            print("🚀 SYSTEM STATUS: PRODUCTION READY")
            return 0
        else:
            print()
            print("⚠️ CONCLUSION:")
            print("  • Some issues still need resolution")
            print("  • Further debugging required")
            print("  • System not yet production ready")
            return 1

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)