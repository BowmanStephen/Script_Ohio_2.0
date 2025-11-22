#!/usr/bin/env python3
"""
Performance benchmark suite for Week 13 system.
Tests response times, memory usage, and throughput under load.
"""

import pytest
import sys
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.week13_consolidation_agent import Week13ConsolidationAgent
from agents.legacy_creation_agent import LegacyCreationAgent
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

@dataclass
class PerformanceMetrics:
    """Performance metrics container"""
    execution_time: float
    memory_usage_mb: float
    cpu_percent: float
    success: bool
    error_message: str = ""

class Week13PerformanceBenchmark:
    """Performance benchmark suite for Week 13 system"""

    def __init__(self):
        self.consolidation_agent = Week13ConsolidationAgent("perf_consolidation")
        self.legacy_agent = LegacyCreationAgent("perf_legacy")
        self.orchestrator = AnalyticsOrchestrator()
        self.results: List[PerformanceMetrics] = []

    def measure_performance(self, func, *args, **kwargs) -> PerformanceMetrics:
        """Measure performance of a function call"""
        process = psutil.Process()

        # Record initial metrics
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()

        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Record final metrics
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            final_cpu = process.cpu_percent()

            return PerformanceMetrics(
                execution_time=execution_time,
                memory_usage_mb=final_memory - initial_memory,
                cpu_percent=final_cpu - initial_cpu,
                success=True
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return PerformanceMetrics(
                execution_time=execution_time,
                memory_usage_mb=0,
                cpu_percent=0,
                success=False,
                error_message=str(e)
            )

    def test_consolidation_performance(self):
        """Benchmark consolidation agent performance"""
        print("⚡ Benchmarking Consolidation Performance...")

        # Single operation benchmark
        metrics = self.measure_performance(
            self.consolidation_agent._execute_action,
            "asset_discovery",
            {"test_mode": True},
            {"user_id": "perf_test"}
        )

        print(f"   Single execution: {metrics.execution_time:.3f}s")
        print(f"   Memory usage: {metrics.memory_usage_mb:.2f}MB")
        assert metrics.success, f"Consolidation failed: {metrics.error_message}"
        assert metrics.execution_time < 2.0, f"Too slow: {metrics.execution_time:.3f}s"

        # Concurrent execution benchmark
        print("   Testing concurrent execution...")
        concurrent_metrics = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(
                    self.measure_performance,
                    self.consolidation_agent._execute_action,
                    "asset_discovery",
                    {"test_mode": True},
                    {"user_id": f"perf_test_{i}"}
                )
                for i in range(10)
            ]

            for future in as_completed(futures):
                metrics = future.result()
                concurrent_metrics.append(metrics)

        avg_time = sum(m.execution_time for m in concurrent_metrics) / len(concurrent_metrics)
        success_rate = sum(1 for m in concurrent_metrics if m.success) / len(concurrent_metrics)

        print(f"   Concurrent avg: {avg_time:.3f}s")
        print(f"   Success rate: {success_rate:.1%}")

        assert success_rate >= 0.9, f"Low success rate: {success_rate:.1%}"
        assert avg_time < 3.0, f"Concurrent operations too slow: {avg_time:.3f}s"

    def test_legacy_performance(self):
        """Benchmark legacy agent performance"""
        print("⚡ Benchmarking Legacy Performance...")

        # Single operation benchmark
        metrics = self.measure_performance(
            self.legacy_agent._execute_action,
            "template_extraction",
            {"test_mode": True, "max_templates": 3},
            {"user_id": "perf_test"}
        )

        print(f"   Single execution: {metrics.execution_time:.3f}s")
        print(f"   Memory usage: {metrics.memory_usage_mb:.2f}MB")
        assert metrics.success, f"Legacy failed: {metrics.error_message}"
        assert metrics.execution_time < 2.0, f"Too slow: {metrics.execution_time:.3f}s"

        # Batch operations benchmark
        print("   Testing batch operations...")
        batch_times = []

        for i in range(5):
            metrics = self.measure_performance(
                self.legacy_agent._execute_action,
                "template_extraction",
                {"test_mode": True, "max_templates": 2},
                {"user_id": f"perf_test_{i}"}
            )
            batch_times.append(metrics.execution_time)
            assert metrics.success, f"Batch operation {i} failed: {metrics.error_message}"

        avg_batch_time = sum(batch_times) / len(batch_times)
        print(f"   Batch avg: {avg_batch_time:.3f}s")
        assert avg_batch_time < 2.5, f"Batch operations too slow: {avg_batch_time:.3f}s"

    def test_orchestrator_throughput(self):
        """Test orchestrator throughput under load"""
        print("⚡ Benchmarking Orchestrator Throughput...")

        requests = [
            AnalyticsRequest(
                user_id=f"perf_user_{i}",
                query=f"Consolidate Week {i % 2 + 13} analytics" if i % 2 == 0 else "Extract templates from Week 13",
                request_type="analysis",
                parameters={},
                user_context={}
            )
            for i in range(20)
        ]

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(self.orchestrator.process_analytics_request, req)
                for req in requests
            ]

            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        total_time = time.time() - start_time
        throughput = len(requests) / total_time
        success_rate = sum(1 for r in results if r.status in ["success", "partial_success"]) / len(results)
        avg_response_time = sum(r.execution_time for r in results) / len(results)

        print(f"   Total requests: {len(requests)}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Throughput: {throughput:.1f} req/s")
        print(f"   Success rate: {success_rate:.1%}")
        print(f"   Avg response time: {avg_response_time:.3f}s")

        assert success_rate >= 0.8, f"Low success rate: {success_rate:.1%}"
        assert throughput >= 2.0, f"Low throughput: {throughput:.1f} req/s"
        assert avg_response_time < 3.0, f"High avg response time: {avg_response_time:.3f}s"

    def test_memory_efficiency(self):
        """Test memory usage and efficiency"""
        print("⚡ Testing Memory Efficiency...")

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform multiple operations
        operations = 0
        while operations < 50:
            # Consolidation operation
            result = self.consolidation_agent._execute_action(
                "asset_discovery",
                {"test_mode": True},
                {"user_id": f"memory_test_{operations}"}
            )

            if result["status"] == "success":
                operations += 1

            # Check memory every 10 operations
            if operations % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory

                print(f"   Operations: {operations}, Memory increase: {memory_increase:.1f}MB")

                # Memory shouldn't grow excessively
                assert memory_increase < 100, f"Memory leak detected: {memory_increase:.1f}MB increase"

    def test_stress_load(self):
        """Test system under stress load"""
        print("⚡ Stress Load Testing...")

        def stress_worker(worker_id: int, operations: int) -> List[PerformanceMetrics]:
            """Stress test worker function"""
            results = []

            for i in range(operations):
                # Alternate between consolidation and legacy
                if i % 2 == 0:
                    metrics = self.measure_performance(
                        self.consolidation_agent._execute_action,
                        "asset_discovery",
                        {"test_mode": True},
                        {"user_id": f"stress_user_{worker_id}_{i}"}
                    )
                else:
                    metrics = self.measure_performance(
                        self.legacy_agent._execute_action,
                        "template_extraction",
                        {"test_mode": True, "max_templates": 2},
                        {"user_id": f"stress_user_{worker_id}_{i}"}
                    )

                results.append(metrics)

                # Small delay to prevent overwhelming
                time.sleep(0.01)

            return results

        # Launch stress workers
        num_workers = 8
        operations_per_worker = 10

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(stress_worker, i, operations_per_worker)
                for i in range(num_workers)
            ]

            all_results = []
            for future in as_completed(futures):
                worker_results = future.result()
                all_results.extend(worker_results)

        total_time = time.time() - start_time
        total_operations = len(all_results)
        success_rate = sum(1 for r in all_results if r.success) / len(all_results)
        avg_time = sum(r.execution_time for r in all_results) / len(all_results)

        print(f"   Stress test completed:")
        print(f"   - Total operations: {total_operations}")
        print(f"   - Total time: {total_time:.2f}s")
        print(f"   - Operations/sec: {total_operations/total_time:.1f}")
        print(f"   - Success rate: {success_rate:.1%}")
        print(f"   - Avg time per operation: {avg_time:.3f}s")

        assert success_rate >= 0.7, f"Stress test success rate too low: {success_rate:.1%}"
        assert avg_time < 5.0, f"Stress test operations too slow: {avg_time:.3f}s"

def run_performance_benchmark():
    """Run complete performance benchmark suite"""
    print("🚀 Starting Week 13 Performance Benchmark Suite")
    print("=" * 60)

    benchmark = Week13PerformanceBenchmark()

    try:
        # Run all benchmark tests
        benchmark.test_consolidation_performance()
        print()

        benchmark.test_legacy_performance()
        print()

        benchmark.test_orchestrator_throughput()
        print()

        benchmark.test_memory_efficiency()
        print()

        benchmark.test_stress_load()
        print()

        print("✅ All performance benchmarks completed successfully!")
        print("=" * 60)

        # Performance summary
        print("\n📊 Performance Summary:")
        print("   - Consolidation: <2s average response time")
        print("   - Legacy: <2s average response time")
        print("   - Orchestrator: >2 req/s throughput")
        print("   - Memory: <100MB increase under load")
        print("   - Stress: >70% success rate under load")

    except Exception as e:
        print(f"❌ Performance benchmark failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_performance_benchmark()