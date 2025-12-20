"""
Tests for Context Isolation Manager
"""

import pytest
from agents.core.context_isolation import ContextIsolationManager


class TestContextIsolationManager:
    """Test suite for ContextIsolationManager"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = ContextIsolationManager()

    def test_create_isolated_context(self):
        """Test creating isolated context"""
        context = self.manager.create_isolated_context("test_agent", {"task": "test"})

        assert context is not None
        assert context.context_id is not None
        assert context.subagent_id == "test_agent"
        assert context.isolated is True
        assert "task" in context.initial_context

    def test_handoff_context(self):
        """Test context handoff"""
        context_data = {"result": "test_result", "task": "test_task"}

        new_context = self.manager.handoff_context(
            "from_agent", "to_agent", context_data
        )

        assert new_context is not None
        assert new_context.subagent_id == "to_agent"
        assert new_context.isolated is True

    def test_archive_context(self):
        """Test archiving context"""
        context = self.manager.create_isolated_context("test_agent")
        context_id = context.context_id

        success = self.manager.archive_context(context_id, "test_reason")

        assert success is True
        assert context_id not in self.manager.active_contexts
        assert len(self.manager.archived_contexts) > 0

    def test_get_context(self):
        """Test getting context"""
        context = self.manager.create_isolated_context("test_agent")
        context_id = context.context_id

        retrieved = self.manager.get_context(context_id)

        assert retrieved is not None
        assert retrieved.context_id == context_id

    def test_compress_context(self):
        """Test context compression"""
        context = self.manager.create_isolated_context(
            "test_agent", {"objective": "test", "task": "test_task"}
        )

        compressed = self.manager.compress_context(context)

        assert compressed is not None
        assert "context_id" in compressed
        assert "essential_data" in compressed
