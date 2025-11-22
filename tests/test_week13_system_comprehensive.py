#!/usr/bin/env python3
"""
Comprehensive test suite for Week 13 consolidation and legacy system.
Validates all functionality, performance, and integration requirements.
"""

import pytest
import sys
import time
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.week13_consolidation_agent import Week13ConsolidationAgent
from agents.legacy_creation_agent import LegacyCreationAgent
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest, AnalyticsResponse

class TestWeek13System:
    """Comprehensive test suite for Week 13 consolidation and legacy system"""

    @pytest.fixture
    def consolidation_agent(self):
        """Create Week 13 consolidation agent for testing"""
        return Week13ConsolidationAgent("test_consolidation_001")

    @pytest.fixture
    def legacy_agent(self):
        """Create Legacy Creation agent for testing"""
        return LegacyCreationAgent("test_legacy_001")

    @pytest.fixture
    def orchestrator(self):
        """Create Analytics Orchestrator for testing"""
        return AnalyticsOrchestrator()

    def test_consolidation_agent_creation(self, consolidation_agent):
        """Test Week 13 consolidation agent creation and capabilities"""
        print("🧪 Testing Week 13 Consolidation Agent Creation...")

        # Verify agent creation
        assert consolidation_agent is not None
        assert consolidation_agent.agent_id == "test_consolidation_001"
        assert "Week 13" in consolidation_agent.name
        assert consolidation_agent.permission_level.value >= 2

        # Verify capabilities
        capabilities = consolidation_agent.capabilities
        assert len(capabilities) >= 3

        capability_names = [cap.name for cap in capabilities]
        assert "full_consolidation" in capability_names
        assert "asset_discovery" in capability_names
        assert "quality_validation" in capability_names

        print(f"✅ Consolidation agent has {len(capabilities)} capabilities")

    def test_legacy_agent_creation(self, legacy_agent):
        """Test Legacy Creation agent creation and capabilities"""
        print("🧪 Testing Legacy Creation Agent Creation...")

        # Verify agent creation
        assert legacy_agent is not None
        assert legacy_agent.agent_id == "test_legacy_001"
        assert "Legacy" in legacy_agent.name
        assert legacy_agent.permission_level.value >= 2

        # Verify capabilities
        capabilities = legacy_agent.capabilities
        assert len(capabilities) >= 3

        capability_names = [cap.name for cap in capabilities]
        assert "template_extraction" in capability_names
        assert "automated_documentation" in capability_names
        assert "best_practices_capture" in capability_names

        print(f"✅ Legacy agent has {len(capabilities)} capabilities")

    def test_consolidation_asset_discovery(self, consolidation_agent):
        """Test Week 13 asset discovery functionality"""
        print("🧪 Testing Week 13 Asset Discovery...")

        start_time = time.time()

        # Execute asset discovery
        result = consolidation_agent._execute_action(
            "asset_discovery",
            {"test_mode": True},
            {"user_id": "test_user"}
        )

        execution_time = time.time() - start_time

        # Validate results
        assert result["status"] == "success"
        assert "data" in result
        assert execution_time < 2.0, f"Asset discovery took {execution_time:.2f}s (target: <2s)"

        week13_assets = result["data"]["discovered_assets"]
        assert len(week13_assets) >= 10, "Should find at least 10 Week 13 assets"

        asset_summary = result["data"]
        assert asset_summary["total_count"] >= 10
        assert "analysis" in asset_summary["asset_types"]
        assert "data" in asset_summary["asset_types"]

        print(f"✅ Discovered {asset_summary['total_count']} Week 13 assets in {execution_time:.2f}s")

    def test_legacy_template_extraction(self, legacy_agent):
        """Test Legacy template extraction functionality"""
        print("🧪 Testing Legacy Template Extraction...")

        start_time = time.time()

        # Execute template extraction
        result = legacy_agent._execute_action(
            "template_extraction",
            {"test_mode": True, "max_templates": 5},
            {"user_id": "test_user"}
        )

        execution_time = time.time() - start_time

        # Validate results
        assert result["status"] == "success"
        assert "data" in result
        assert execution_time < 2.0, f"Template extraction took {execution_time:.2f}s (target: <2s)"

        templates = result["data"]["templates"]
        assert len(templates) >= 1, "Should extract at least 1 template"

        extraction_summary = result["data"]
        assert extraction_summary["total_count"] >= 1
        assert "data_pipeline" in extraction_summary["template_types"]

        print(f"✅ Extracted {extraction_summary['total_count']} templates in {execution_time:.2f}s")

    def test_orchestrator_week13_routing(self, orchestrator):
        """Test Analytics Orchestrator Week 13 routing"""
        print("🧪 Testing Analytics Orchestrator Week 13 Routing...")

        # Test Week 13 consolidation routing
        consolidation_request = AnalyticsRequest(
            user_id="test_user",
            query="Please consolidate all Week 13 analytics work",
            query_type="analysis",
            parameters={},
            context_hints={}
        )

        start_time = time.time()
        response = orchestrator.process_analytics_request(consolidation_request)
        execution_time = time.time() - start_time

        # Validate routing
        assert response.status in ["success", "partial_success"], f"Routing failed: {response.error_message}"
        assert execution_time < 2.0, f"Routing took {execution_time:.2f}s (target: <2s)"
        assert response.metadata.get("agent_type") == "week13_consolidation", "Incorrect routing"

        print(f"✅ Week 13 consolidation routing successful in {execution_time:.2f}s")

        # Test Week 13 legacy routing
        legacy_request = AnalyticsRequest(
            user_id="test_user",
            query="Create templates from Week 13 work for future weeks",
            query_type="analysis",
            parameters={},
            context_hints={}
        )

        start_time = time.time()
        response = orchestrator.process_analytics_request(legacy_request)
        execution_time = time.time() - start_time

        # Validate routing
        assert response.status in ["success", "partial_success"], f"Legacy routing failed: {response.error_message}"
        assert execution_time < 2.0, f"Legacy routing took {execution_time:.2f}s (target: <2s)"

        print(f"✅ Week 13 legacy routing successful in {execution_time:.2f}s")

    def test_performance_requirements(self, consolidation_agent, legacy_agent):
        """Test system performance requirements"""
        print("🧪 Testing Performance Requirements...")

        # Test consolidation performance
        consolidation_times = []
        for i in range(3):
            start_time = time.time()
            result = consolidation_agent._execute_action(
                "asset_discovery",
                {"test_mode": True},
                {"user_id": "test_user"}
            )
            consolidation_times.append(time.time() - start_time)
            assert result["status"] == "success"

        avg_consolidation_time = sum(consolidation_times) / len(consolidation_times)
        assert avg_consolidation_time < 2.0, f"Average consolidation time: {avg_consolidation_time:.2f}s (target: <2s)"

        # Test legacy performance
        legacy_times = []
        for i in range(3):
            start_time = time.time()
            result = legacy_agent._execute_action(
                "template_extraction",
                {"test_mode": True, "max_templates": 3},
                {"user_id": "test_user"}
            )
            legacy_times.append(time.time() - start_time)
            assert result["status"] == "success"

        avg_legacy_time = sum(legacy_times) / len(legacy_times)
        assert avg_legacy_time < 2.0, f"Average legacy time: {avg_legacy_time:.2f}s (target: <2s)"

        print(f"✅ Performance requirements met:")
        print(f"   - Consolidation: {avg_consolidation_time:.2f}s average")
        print(f"   - Legacy: {avg_legacy_time:.2f}s average")

    def test_integration_workflow(self, orchestrator):
        """Test complete Week 13 integration workflow"""
        print("🧪 Testing Complete Integration Workflow...")

        workflow_start_time = time.time()

        # Step 1: Consolidate Week 13 assets
        consolidation_request = AnalyticsRequest(
            user_id="test_user",
            query="Show me all Week 13 analytics and consolidate them",
            query_type="analysis",
            parameters={},
            context_hints={}
        )

        consolidation_response = orchestrator.process_analytics_request(consolidation_request)
        assert consolidation_response.status in ["success", "partial_success"]

        # Step 2: Extract templates from consolidated work
        legacy_request = AnalyticsRequest(
            user_id="test_user",
            query="Based on Week 13 work, create templates for future weeks",
            query_type="analysis",
            parameters={},
            context_hints={}
        )

        legacy_response = orchestrator.process_analytics_request(legacy_request)
        assert legacy_response.status in ["success", "partial_success"]

        workflow_time = time.time() - workflow_start_time
        assert workflow_time < 5.0, f"Complete workflow took {workflow_time:.2f}s (target: <5s)"

        print(f"✅ Complete workflow successful in {workflow_time:.2f}s")

    def test_error_handling(self, consolidation_agent, legacy_agent):
        """Test error handling and recovery"""
        print("🧪 Testing Error Handling...")

        # Test consolidation error handling
        result = consolidation_agent._execute_action(
            "invalid_action",
            {"test_mode": True},
            {"user_id": "test_user"}
        )

        assert result["status"] == "error"
        assert "error_message" in result

        # Test legacy error handling
        result = legacy_agent._execute_action(
            "invalid_action",
            {"test_mode": True},
            {"user_id": "test_user"}
        )

        assert result["status"] == "error"
        assert "error_message" in result

        print("✅ Error handling working correctly")

    def test_data_quality_validation(self, consolidation_agent):
        """Test data quality and validation"""
        print("🧪 Testing Data Quality Validation...")

        start_time = time.time()

        # Execute quality validation
        result = consolidation_agent._execute_action(
            "quality_validation",
            {"test_mode": True},
            {"user_id": "test_user"}
        )

        execution_time = time.time() - start_time

        # Validate results
        assert result["status"] == "success"
        assert "validation_report" in result
        assert execution_time < 2.0, f"Quality validation took {execution_time:.2f}s (target: <2s)"

        validation_report = result["validation_report"]
        assert "assets_validated" in validation_report
        assert "quality_score" in validation_report

        print(f"✅ Validated {validation_report['assets_validated']} assets in {execution_time:.2f}s")

if __name__ == "__main__":
    print("🚀 Starting Week 13 System Comprehensive Testing")
    print("=" * 60)

    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])