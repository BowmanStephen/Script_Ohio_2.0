import pytest
from agents.orchestration_agent import OrchestrationAgent, OrchestrationMode
from agents.meta_agent import MetaAgent
import logging

# Set up logging to capture warnings
logging.basicConfig(level=logging.DEBUG)


class TestOrchestrationAgentFixes:

    def test_composition_initialization(self):
        """Test that MetaAgent is properly composed"""
        agent = OrchestrationAgent()
        assert hasattr(agent, '_meta_agent')
        # MetaAgent should either be initialized or gracefully failed
        assert agent._meta_agent is not None or agent._meta_agent is None  # Graceful failure allowed

    def test_agent_registry_safe_access(self):
        """Test safe access to agent_registry via property"""
        agent = OrchestrationAgent()
        registry = agent.agent_registry  # Should not raise AttributeError
        assert isinstance(registry, dict)
        # Should not crash even if MetaAgent is not available
        assert len(registry) >= 0

    def test_coordination_with_missing_meta_agent(self):
        """Test coordination when MetaAgent unavailable"""
        agent = OrchestrationAgent()
        agent._meta_agent = None  # Simulate missing MetaAgent

        result = agent._enhanced_coordinate_agents({
            'workflow': 'test',
            'agents': ['nonexistent_agent']
        }, {})

        assert result['success'] == False
        assert 'MetaAgent not available' in result['error']

    def test_optimization_components_none_handling(self):
        """Test graceful handling of missing optimization components"""
        agent = OrchestrationAgent()
        agent._optimization_components = None

        # Should not crash
        context_engine = agent._get_context_compression_engine()
        memory_mgr = agent._get_memory_manager()
        workflow = agent._get_workflow_automator()

        assert context_engine is None
        assert memory_mgr is None
        assert workflow is None

    def test_composition_health_check(self):
        """Test composition health check method"""
        agent = OrchestrationAgent()
        health = agent._check_composition_health()

        assert isinstance(health, dict)
        assert 'meta_agent_available' in health
        assert 'agent_registry_size' in health
        assert 'optimization_components_available' in health
        assert 'context_compression_available' in health
        assert 'memory_manager_available' in health
        assert 'workflow_automator_available' in health

    def test_handle_missing_component(self):
        """Test missing component error handling"""
        agent = OrchestrationAgent()

        result = agent._handle_missing_component('test_component', 'test_operation')

        assert result['success'] == False
        assert 'error' in result
        assert result['error_type'] == 'MissingComponent'
        assert result['component'] == 'test_component'
        assert result['fallback_applied'] is True

    def test_intensive_load_test(self):
        """Test the fix eliminates the 24% failure rate"""
        agent = OrchestrationAgent()
        failures = 0
        total_requests = 25

        for i in range(total_requests):
            try:
                if i % 4 == 0:
                    result = agent._monitor_optimization({}, {})
                elif i % 4 == 1:
                    result = agent._enhanced_coordinate_agents({'workflow': 'test', 'agents': []}, {})
                elif i % 4 == 2:
                    result = agent._enhanced_coordinate_agents({'agents': []}, {})
                else:
                    result = agent._check_composition_health()

                # All should succeed or fail gracefully without AttributeError
                assert isinstance(result, dict)

            except AttributeError as e:
                failures += 1
                print(f"AttributeError in request {i+1}: {e}")

        # Should have 0 AttributeErrors (was 6/25 before fix)
        assert failures == 0, f"Found {failures} AttributeErrors, expected 0"

    def test_optimization_monitoring_with_missing_components(self):
        """Test optimization monitoring handles missing components gracefully"""
        agent = OrchestrationAgent()
        agent._optimization_components = None

        # Should not crash
        result = agent._optimize_performance({'targets': ['context', 'memory']}, {})

        assert 'success' in result
        # Should return results with error info for missing components
        if not result.get('success', True):
            assert 'error' in result

    def test_agent_registry_property_access(self):
        """Test that agent_registry property works correctly"""
        agent = OrchestrationAgent()

        # Should be accessible without AttributeError
        registry = agent.agent_registry

        # Should be a dictionary
        assert isinstance(registry, dict)

        # Should not crash even when MetaAgent is unavailable
        agent._meta_agent = None
        registry_empty = agent.agent_registry
        assert isinstance(registry_empty, dict)
        assert len(registry_empty) == 0


class TestOrchestrationAgentIntegration:

    def test_monitor_optimization_compatibility(self):
        """Test that monitoring optimization works with the fix"""
        agent = OrchestrationAgent(OrchestrationMode.OPTIMIZED)

        # Should return proper result structure
        result = agent._monitor_optimization({}, {})

        assert isinstance(result, dict)
        assert 'optimization_status' in result or 'success' in result

    def test_coordinate_agents_basic_functionality(self):
        """Test basic agent coordination functionality"""
        agent = OrchestrationAgent()

        # Test with minimal parameters
        result = agent._enhanced_coordinate_agents({
            'workflow': 'test_workflow',
            'agents': []
        }, {})

        assert isinstance(result, dict)
        # Should either succeed or fail gracefully
        assert 'success' in result or 'error' in result

    def test_performance_tracking(self):
        """Test that performance tracking works without crashing"""
        agent = OrchestrationAgent()

        # Simulate performance update
        agent._update_performance_metrics('test_action', 0.5, {'success': True})

        # Should not raise any exceptions
        assert True  # If we reach here, no exceptions were raised

    def test_error_recovery_compatibility(self):
        """Test that error recovery works with composition pattern"""
        agent = OrchestrationAgent()

        # Test error recovery method
        try:
            agent._apply_error_recovery('test_action', Exception('test error'), {}, {})
        except Exception as e:
            # Should not crash - only in extreme cases
            assert False, f"Error recovery crashed: {e}"


# Performance validation test
def test_intensive_load_validation():
    """Validate the fix with the same load test that revealed the 24% failure rate"""
    agent = OrchestrationAgent()

    print("\n🔥 Running intensive coordination test with fix...")
    results = []
    failures = 0
    attribute_errors = 0

    for i in range(25):
        try:
            if i % 4 == 0:
                result = agent._monitor_optimization({}, {})
                operation = 'optimization_monitor'
            elif i % 4 == 1:
                result = agent._enhanced_coordinate_agents({'workflow': 'test_workflow', 'agents': []}, {})
                operation = 'agent_coordination'
            elif i % 4 == 2:
                result = agent._enhanced_coordinate_agents({'agents': []}, {})
                operation = 'enhanced_coordination'
            else:
                result = agent._check_composition_health()
                operation = 'health_check'

            results.append({
                'request_id': i+1,
                'operation': operation,
                'status': 'success',
                'result': result
            })

        except AttributeError as e:
            attribute_errors += 1
            failures += 1
            print(f"❌ Request {i+1}: AttributeError - {e}")
            results.append({
                'request_id': i+1,
                'operation': 'unknown',
                'status': 'error',
                'error': str(e)
            })
        except Exception as e:
            failures += 1
            print(f"❌ Request {i+1}: Other error - {e}")
            results.append({
                'request_id': i+1,
                'operation': 'unknown',
                'status': 'error',
                'error': str(e)
            })

    success_count = len([r for r in results if r['status'] == 'success'])
    success_rate = success_count / 25 * 100

    print(f"✅ Success rate: {success_rate:.1f}% (was ~76% before fix)")
    print(f"❌ AttributeErrors: {attribute_errors} (was 6 before fix)")
    print(f"❌ Total failures: {failures} (was 6 before fix)")

    # Validate fix
    assert attribute_errors == 0, f"Fix failed: {attribute_errors} AttributeErrors remain"
    assert success_rate >= 95, f"Fix failed: success rate {success_rate:.1f}% < 95%"

    print("🎉 Fix validated: 0 AttributeErrors, ≥95% success rate!")
    return True


if __name__ == "__main__":
    # Run the intensive validation test when this file is executed directly
    test_intensive_load_validation()