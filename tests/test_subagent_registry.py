"""
Tests for Subagent Registry
"""

import pytest
from agents.claude_code_subagent_registry import SubagentRegistry


class TestSubagentRegistry:
    """Test suite for SubagentRegistry"""

    def setup_method(self):
        """Set up test fixtures"""
        self.registry = SubagentRegistry()

    def test_registry_initialization(self):
        """Test registry initialization"""
        assert self.registry.agents_dir is not None
        assert isinstance(self.registry.subagents, dict)

    def test_list_subagents(self):
        """Test listing subagents"""
        subagents = self.registry.list_subagents()

        assert isinstance(subagents, list)
        assert len(subagents) > 0

    def test_get_subagent(self):
        """Test getting a subagent"""
        subagents = self.registry.list_subagents()
        if subagents:
            subagent = self.registry.get_subagent(subagents[0])

            assert subagent is not None
            assert subagent.name == subagents[0]

    def test_get_nonexistent_subagent(self):
        """Test getting a non-existent subagent"""
        subagent = self.registry.get_subagent("Nonexistent Agent")

        assert subagent is None

    def test_subagent_permissions(self):
        """Test subagent permission levels"""
        subagents = self.registry.list_subagents()
        if subagents:
            subagent = self.registry.get_subagent(subagents[0])

            assert subagent is not None
            perm_level = subagent.get_permission_level()
            assert perm_level is not None

    def test_reload(self):
        """Test reloading subagents"""
        initial_count = len(self.registry.subagents)
        self.registry.reload()

        # Should have same or more subagents after reload
        assert len(self.registry.subagents) >= initial_count
