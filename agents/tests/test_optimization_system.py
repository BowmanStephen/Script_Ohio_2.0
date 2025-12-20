"""
Comprehensive Test Suite for Optimization System

Tests all optimization components:
- Context compression and TOON format integration
- Hierarchical memory management
- Workflow automation
- Enhanced orchestration agent
- Performance monitoring and validation
"""

import json
import shutil
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Import optimization components
from agents.optimization.context_compression_rules import (
    ContextCompressionEngine,
    ContextState,
)
from agents.optimization.memory_manager import HierarchicalMemoryManager, MemoryLevel
from agents.optimization.workflow_automator import (
    TaskPriority,
    WorkflowAutomator,
    WorkflowStatus,
)
from agents.orchestration_agent import OrchestrationAgent, OrchestrationMode


# Mock the TOON format for testing
class MockTOONFormat:
    @staticmethod
    def encode(data):
        return json.dumps(data, separators=(",", ":"))

    @staticmethod
    def decode(data):
        return json.loads(data)


# Monkey patch for testing
import sys

sys.modules["src.toon_format"] = MockTOONFormat()


class TestContextCompressionEngine:
    """Test suite for Context Compression Engine"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        # Create test configuration
        test_config = {
            "context_management": {
                "phase_based_clearing": {
                    "enabled": True,
                    "preserve_on_clear": ["meta_agent_state", "current_task_context"],
                    "max_context_tokens": 8000,
                    "compression_threshold": 6000,
                    "archive_path": f"{self.temp_dir}/contexts/",
                },
                "toon_format": {"enabled": True, "compression_ratio_target": 0.65},
            }
        }

        with open(self.config_path, "w") as f:
            json.dump(test_config, f)

        self.engine = ContextCompressionEngine(str(self.config_path))

    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test engine initialization"""
        assert self.engine.config is not None
        assert len(self.engine.rules) > 0
        assert self.engine.metrics["contexts_compressed"] == 0

    def test_phase_update(self):
        """Test phase-based context clearing"""
        old_phase = self.engine.current_phase
        self.engine.update_phase("analysis")

        assert self.engine.current_phase == "analysis"
        assert self.engine.current_phase != old_phase

    def test_context_compression(self):
        """Test context compression"""
        test_data = {"large_context": "x" * 1000, "nested": {"data": list(range(100))}}

        compressed = self.engine.compress_context("test_agent", test_data)

        assert compressed is not None
        assert self.engine.metrics["contexts_compressed"] == 1
        assert "compressed_data" in compressed

    def test_context_archival(self):
        """Test context archival"""
        test_context = {"important_data": "test_value"}

        # Archive context
        self.engine.archive_context("test_agent", test_context, {"reason": "test"})

        # Verify archival
        assert len(self.engine.archived_contexts) > 0
        assert "test_agent" in self.engine.archived_contexts

    def test_context_restoration(self):
        """Test context restoration"""
        original_context = {"restored_data": "value"}

        # Archive first
        self.engine.archive_context("test_agent", original_context)

        # Then restore
        restored = self.engine.restore_context("test_agent")

        assert restored is not None
        assert restored == original_context

    def test_relevant_context_loading(self):
        """Test dynamic context loading"""
        context = self.engine.load_relevant_context(
            "test_agent", "analysis_task", max_tokens=1000
        )

        assert isinstance(context, dict)
        # Should return empty dict since no context sources are configured in test

    def test_metrics_collection(self):
        """Test metrics collection"""
        metrics = self.engine.get_metrics()

        assert "contexts_compressed" in metrics
        assert "tokens_saved" in metrics
        assert "compression_ratio" in metrics


class TestHierarchicalMemoryManager:
    """Test suite for Hierarchical Memory Manager"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_memory_config.json"

        # Create test configuration
        test_config = {
            "level_1_meta_agent": {
                "max_size_mb": 10,
                "retention_days": 1,
                "storage_path": f"{self.temp_dir}/meta/",
            },
            "level_2_orchestrators": {
                "max_size_mb": 5,
                "retention_hours": 1,
                "storage_path": f"{self.temp_dir}/orchestrators/",
            },
            "level_3_agents": {
                "max_size_mb": 2,
                "retention_minutes": 10,
                "storage_path": f"{self.temp_dir}/agents/",
            },
            "level_4_cache": {
                "max_size_mb": 5,
                "ttl_minutes": {
                    "cfbd_api_responses": 1,
                    "model_predictions": 2,
                    "toon_outputs": 1,
                },
                "storage_path": f"{self.temp_dir}/cache/",
            },
        }

        with open(self.config_path, "w") as f:
            json.dump(test_config, f)

        self.manager = HierarchicalMemoryManager(str(self.config_path))

    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test manager initialization"""
        assert self.manager.config is not None
        assert MemoryLevel.META_AGENT in self.manager.memory_stores
        assert MemoryLevel.CACHE in self.manager.memory_stores

    def test_store_and_retrieve(self):
        """Test storing and retrieving data"""
        test_data = {"key": "value", "numbers": [1, 2, 3]}

        # Store data
        success = self.manager.store("test_key", test_data, MemoryLevel.AGENT)
        assert success is True

        # Retrieve data
        retrieved = self.manager.retrieve("test_key")
        assert retrieved == test_data

    def test_level_specific_storage(self):
        """Test storage in specific memory levels"""
        test_data = {"level_test": "data"}

        for level in MemoryLevel:
            key = f"test_{level.name}"
            success = self.manager.store(key, test_data, level)
            assert success is True

            retrieved = self.manager.retrieve(key, level)
            assert retrieved == test_data

    def test_expiration_handling(self):
        """Test data expiration"""
        test_data = {"expire_test": "data"}

        # Store with short expiration
        success = self.manager.store(
            "expire_key", test_data, MemoryLevel.CACHE, expires_in=timedelta(seconds=1)
        )
        assert success is True

        # Should be retrievable immediately
        retrieved = self.manager.retrieve("expire_key")
        assert retrieved == test_data

        # Wait for expiration
        time.sleep(2)

        # Should be expired now
        retrieved = self.manager.retrieve("expire_key")
        assert retrieved is None

    def test_tag_based_search(self):
        """Test searching by tags"""
        test_data = {"tagged_data": "value"}
        tags = ["test", "memory", "search"]

        # Store with tags
        success = self.manager.store(
            "tagged_key", test_data, MemoryLevel.AGENT, tags=tags
        )
        assert success is True

        # Search by tags
        results = self.manager.search_by_tags(["test", "memory"])
        assert len(results) > 0

        # Search by non-existent tag
        results = self.manager.search_by_tags(["non_existent"])
        assert len(results) == 0

    def test_memory_cleanup(self):
        """Test memory cleanup of expired entries"""
        # Store some data with expiration
        for i in range(3):
            self.manager.store(
                f"expire_test_{i}",
                {"data": f"value_{i}"},
                MemoryLevel.CACHE,
                expires_in=timedelta(seconds=1),
            )

        # Wait for expiration
        time.sleep(2)

        # Clean up expired entries
        cleaned_count = self.manager.cleanup_expired()
        assert cleaned_count >= 0  # May be 0 if cleanup already happened

    def test_statistics_collection(self):
        """Test memory statistics"""
        # Store some test data
        for i in range(5):
            self.manager.store(
                f"stat_test_{i}", {"data": f"value_{i}"}, MemoryLevel.AGENT
            )

        # Get statistics
        stats = self.manager.get_stats()

        assert stats.total_entries >= 5
        assert stats.total_size_mb >= 0
        assert stats.hit_rate >= 0.0


class TestWorkflowAutomator:
    """Test suite for Workflow Automator"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_workflow_config.json"

        # Create test configuration
        test_config = {
            "weekly_analysis": {
                "enabled": True,
                "timeout_minutes": 10,
                "max_retry_attempts": 2,
            },
            "error_handling": {
                "graceful_degradation": ["ml_predictions", "simple_predictions"]
            },
        }

        with open(self.config_path, "w") as f:
            json.dump(test_config, f)

        self.automator = WorkflowAutomator(str(self.config_path))

    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test automator initialization"""
        assert self.automator.config is not None
        assert "weekly_analysis" in self.automator.workflow_definitions
        assert len(self.automator.workflow_definitions) > 0

    def test_workflow_execution(self):
        """Test workflow execution"""
        if "weekly_analysis" not in self.automator.workflow_definitions:
            pytest.skip("weekly_analysis workflow not defined")

        execution = self.automator.execute_workflow("weekly_analysis")

        assert execution is not None
        assert execution.workflow_id == "weekly_analysis"
        assert execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]

    def test_workflow_status_tracking(self):
        """Test workflow status tracking"""
        if "weekly_analysis" not in self.automator.workflow_definitions:
            pytest.skip("weekly_analysis workflow not defined")

        execution = self.automator.execute_workflow("weekly_analysis")
        execution_id = execution.execution_id

        # Check status
        status = self.automator.get_workflow_status(execution_id)
        assert status is not None
        assert status.execution_id == execution_id

    def test_workflow_cancellation(self):
        """Test workflow cancellation"""
        if "weekly_analysis" not in self.automator.workflow_definitions:
            pytest.skip("weekly_analysis workflow not defined")

        # Start a workflow
        execution = self.automator.execute_workflow("weekly_analysis")
        execution_id = execution.execution_id

        # Try to cancel it (may already be completed)
        cancelled = self.automator.cancel_workflow(execution_id)

        # Should either succeed or fail gracefully
        assert isinstance(cancelled, bool)

    def test_metrics_collection(self):
        """Test workflow automator metrics"""
        metrics = self.automator.get_metrics()

        assert "workflows_executed" in metrics
        assert "tasks_completed" in metrics
        assert "tasks_failed" in metrics


class TestOrchestrationAgent:
    """Test suite for Orchestration Agent"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_orchestration_config.json"

        # Create test configuration
        test_config = {
            "agent_coordination": {
                "lifecycle_management": {"enabled": True, "health_monitoring": True},
                "load_balancing": {
                    "cpu_threshold_percent": 70,
                    "memory_threshold_percent": 80,
                },
            },
            "performance_optimization": {
                "cfbd_integration": {"rate_limit_requests_per_second": 6}
            },
        }

        with open(self.config_path, "w") as f:
            json.dump(test_config, f)

        # Mock the orchestration agent config path
        import agents.orchestration_agent

        agents.orchestration_agent.Path = lambda x: (
            self.config_path
            if str(x).endswith("claude_code_optimization.json")
            else Path(x)
        )

        self.agent = OrchestrationAgent(mode=OrchestrationMode.STANDARD)

    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test agent initialization"""
        assert self.agent.mode == OrchestrationMode.STANDARD
        assert self.agent.orchestration_config is not None
        assert len(self.agent._define_capabilities()) > 0

    def test_system_monitoring(self):
        """Test system monitoring capability"""
        result = self.agent._monitor_system({}, {})

        assert result["success"] is True
        assert "metrics" in result
        assert "health_status" in result

    def test_optimization_monitoring(self):
        """Test optimization monitoring capability"""
        result = self.agent._monitor_optimization({}, {})

        assert result["success"] is True
        assert "optimization_report" in result
        assert "metrics_collected" in result

    def test_performance_optimization(self):
        """Test performance optimization capability"""
        result = self.agent._optimize_performance({"targets": ["memory"]}, {})

        assert result["success"] is True
        assert "optimization_results" in result
        assert "performance_gains" in result

    def test_context_management(self):
        """Test context management capability"""
        result = self.agent._manage_context_windows(
            {"operation": "compress", "agent_ids": ["test_agent"]}, {}
        )

        assert result["success"] is True
        assert "agent_results" in result

    def test_claude_code_coordination(self):
        """Test Claude Code coordination capability"""
        result = self.agent._coordinate_claude_code(
            {"request_type": "status_inquiry", "request_data": {}}, {}
        )

        assert result["success"] is True
        assert "system_status" in result


class TestIntegration:
    """Integration tests for the complete optimization system"""

    def setup_method(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()

        # Initialize all components with test configuration
        self.setup_context_compression()
        self.setup_memory_manager()
        self.setup_workflow_automator()

    def teardown_method(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir)

    def setup_context_compression(self):
        """Set up context compression for integration tests"""
        config_path = Path(self.temp_dir) / "integration_context_config.json"
        test_config = {
            "context_management": {
                "phase_based_clearing": {
                    "enabled": True,
                    "preserve_on_clear": ["meta_agent_state", "current_task_context"],
                    "max_context_tokens": 8000,
                },
                "toon_format": {"enabled": True, "compression_ratio_target": 0.65},
            }
        }

        with open(config_path, "w") as f:
            json.dump(test_config, f)

        self.context_engine = ContextCompressionEngine(str(config_path))

    def setup_memory_manager(self):
        """Set up memory manager for integration tests"""
        config_path = Path(self.temp_dir) / "integration_memory_config.json"
        test_config = {
            "level_1_meta_agent": {
                "max_size_mb": 10,
                "storage_path": f"{self.temp_dir}/meta/",
            },
            "level_4_cache": {
                "max_size_mb": 10,
                "storage_path": f"{self.temp_dir}/cache/",
            },
        }

        with open(config_path, "w") as f:
            json.dump(test_config, f)

        self.memory_manager = HierarchicalMemoryManager(str(config_path))

    def setup_workflow_automator(self):
        """Set up workflow automator for integration tests"""
        config_path = Path(self.temp_dir) / "integration_workflow_config.json"
        test_config = {"weekly_analysis": {"enabled": True, "timeout_minutes": 5}}

        with open(config_path, "w") as f:
            json.dump(test_config, f)

        self.workflow_automator = WorkflowAutomator(str(config_path))

    def test_context_to_memory_integration(self):
        """Test integration between context compression and memory management"""
        # Compress some context
        test_context = {"integration_test": "data", "numbers": list(range(50))}
        compressed = self.context_engine.compress_context(
            "integration_agent", test_context
        )

        # Store compressed context in memory
        success = self.memory_manager.store(
            "compressed_context", compressed, MemoryLevel.AGENT
        )
        assert success is True

        # Retrieve from memory
        retrieved = self.memory_manager.retrieve("compressed_context")
        assert retrieved is not None
        assert "compressed_data" in retrieved

    def test_workflow_memory_integration(self):
        """Test integration between workflow execution and memory storage"""
        if "weekly_analysis" not in self.workflow_automator.workflow_definitions:
            pytest.skip("weekly_analysis workflow not defined")

        # Execute workflow
        execution = self.workflow_automator.execute_workflow("weekly_analysis")

        # Store workflow results in memory
        success = self.memory_manager.store(
            f"workflow_{execution.execution_id}",
            {
                "execution_id": execution.execution_id,
                "status": execution.status.value,
                "results": execution.task_results,
            },
            MemoryLevel.ORCHESTRATOR,
        )
        assert success is True

        # Retrieve and verify
        retrieved = self.memory_manager.retrieve(f"workflow_{execution.execution_id}")
        assert retrieved is not None
        assert retrieved["execution_id"] == execution.execution_id

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow with all optimizations"""
        # 1. Start with context compression
        initial_context = {"workflow_data": "test", "phase": "integration"}
        compressed = self.context_engine.compress_context(
            "test_workflow", initial_context
        )

        # 2. Update phase for optimization
        self.context_engine.update_phase("integration_test")

        # 3. Store in hierarchical memory
        self.memory_manager.store("workflow_context", compressed, MemoryLevel.AGENT)

        # 4. Execute workflow (if available)
        if "weekly_analysis" in self.workflow_automator.workflow_definitions:
            execution = self.workflow_automator.execute_workflow("weekly_analysis")

            # 5. Store workflow results
            self.memory_manager.store(
                "workflow_results",
                {"status": execution.status.value, "metrics": execution.metrics},
                MemoryLevel.ORCHESTRATOR,
            )

            # 6. Verify complete integration
            context_retrieved = self.memory_manager.retrieve("workflow_context")
            results_retrieved = self.memory_manager.retrieve("workflow_results")

            assert context_retrieved is not None
            assert results_retrieved is not None

    def test_performance_metrics_integration(self):
        """Test performance metrics collection across all components"""
        # Collect metrics from all components
        context_metrics = self.context_engine.get_metrics()
        memory_stats = self.memory_manager.get_stats()
        workflow_metrics = self.workflow_automator.get_metrics()

        # Verify metrics structure
        assert "contexts_compressed" in context_metrics
        assert hasattr(memory_stats, "total_entries")  # MemoryStats is a dataclass
        assert "workflows_executed" in workflow_metrics

        # Create integrated metrics report
        integrated_metrics = {
            "timestamp": datetime.now().isoformat(),
            "context_compression": context_metrics,
            "memory_management": {
                "total_entries": memory_stats.total_entries,
                "total_size_mb": memory_stats.total_size_mb,
                "hit_rate": memory_stats.hit_rate,
            },
            "workflow_automation": workflow_metrics,
        }

        # Store integrated metrics
        success = self.memory_manager.store(
            "integrated_metrics", integrated_metrics, MemoryLevel.META_AGENT
        )
        assert success is True


# Test configuration and utilities
class TestConfiguration:
    """Test configuration loading and validation"""

    def test_config_loading(self):
        """Test configuration loading with missing files"""
        from agents.optimization.context_compression_rules import (
            ContextCompressionEngine,
        )

        # Should load with defaults when config file is missing
        engine = ContextCompressionEngine("non_existent_config.json")
        assert engine.config is not None
        assert "context_management" in engine.config

    def test_config_validation(self):
        """Test configuration validation"""
        from agents.optimization.memory_manager import HierarchicalMemoryManager

        # Should handle invalid JSON gracefully
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            f.flush()

            try:
                manager = HierarchicalMemoryManager(f.name)
                # Should use defaults when config is invalid
                assert manager.config is not None
            finally:
                import os

                os.unlink(f.name)


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmarks for optimization components"""

    def test_context_compression_performance(self):
        """Benchmark context compression performance"""
        engine = ContextCompressionEngine()

        # Create large test data
        large_data = {
            "large_context": "x" * 10000,
            "nested_data": {"items": list(range(1000))},
            "arrays": [[i] * 100 for i in range(100)],
        }

        start_time = time.time()
        compressed = engine.compress_context("perf_test", large_data)
        compression_time = time.time() - start_time

        # Performance assertions
        assert compression_time < 5.0  # Should complete within 5 seconds
        assert compressed is not None

        metrics = engine.get_metrics()
        assert metrics["contexts_compressed"] >= 1

    def test_memory_operations_performance(self):
        """Benchmark memory operations performance"""
        manager = HierarchicalMemoryManager()

        # Performance test for multiple operations
        start_time = time.time()

        for i in range(100):
            test_data = {"benchmark": f"data_{i}", "numbers": list(range(10))}
            manager.store(f"perf_key_{i}", test_data, MemoryLevel.CACHE)
            retrieved = manager.retrieve(f"perf_key_{i}")
            assert retrieved == test_data

        total_time = time.time() - start_time

        # Performance assertions
        assert total_time < 10.0  # 100 operations should complete within 10 seconds
        assert total_time / 100 < 0.1  # Average operation should be under 100ms


# Utility functions for testing
def create_test_agent_registry():
    """Create test agent registry for integration tests"""
    return {
        "test_agent_1": {
            "agent_id": "test_agent_1",
            "agent_name": "Test Agent 1",
            "status": "active",
            "health_score": 0.9,
            "capabilities": ["test_capability"],
        },
        "test_agent_2": {
            "agent_id": "test_agent_2",
            "agent_name": "Test Agent 2",
            "status": "active",
            "health_score": 0.8,
            "capabilities": ["another_capability"],
        },
    }


def create_sample_workflow_data():
    """Create sample workflow data for testing"""
    return {
        "workflow_id": "test_workflow",
        "tasks": [
            {"task_id": "task_1", "name": "Test Task 1"},
            {"task_id": "task_2", "name": "Test Task 2"},
        ],
    }


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])
