"""
🏛️ SUPER ORCHESTRATOR - Unified Agent Orchestration

Replaces 4+ orchestrators with a single, high-performance orchestrator.
Consolidates all orchestration capabilities with intelligent routing
and direct agent execution.

Performance Targets:
- Agent Loading: <50ms (vs 253ms current)
- Memory Footprint: <50MB (vs 105MB+ current)
- Request Routing: <10ms (vs complex factory chain)
- Response Time: <100ms total
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
from pathlib import Path
import sys

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

logger = logging.getLogger(__name__)

class RequestType(Enum):
    """Request types for intelligent routing"""
    ANALYSIS = "analysis"
    PREDICTION = "prediction"
    LEARNING = "learning"
    DATA = "data"
    VALIDATION = "validation"
    INSIGHT = "insight"
    PERFORMANCE = "performance"
    WEEKLY = "weekly"

@dataclass
class AnalyticsRequest:
    """Simplified request structure"""
    user_id: str
    query: str
    request_type: RequestType
    parameters: Dict[str, Any]
    context: Dict[str, Any]
    priority: int = 1
    session_id: Optional[str] = None

@dataclass
class AnalyticsResponse:
    """Simplified response structure"""
    status: str
    data: Any
    metadata: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None

class ModelPool:
    """Shared model pool to prevent duplicate loading"""

    def __init__(self):
        self._models = {}
        self._load_times = {}
        logger.info("ModelPool initialized")

    def get_model(self, model_name: str):
        """Get model with lazy loading and caching"""
        if model_name not in self._models:
            start_time = time.time()
            try:
                # Import and load model only when needed
                from src.models.execution.engine import ModelExecutionEngine
                engine = ModelExecutionEngine()

                if hasattr(engine, f'_{model_name}'):
                    self._models[model_name] = getattr(engine, f'_{model_name}')
                else:
                    # Try to load from model_pack
                    import joblib
                    import pickle
                    model_path = f"model_pack/{model_name}.joblib"
                    if not Path(model_path).exists():
                        model_path = f"model_pack/{model_name}.pkl"

                    if Path(model_path).exists():
                        if model_path.endswith('.joblib'):
                            self._models[model_name] = joblib.load(model_path)
                        else:
                            with open(model_path, 'rb') as f:
                                self._models[model_name] = pickle.load(f)
                    else:
                        raise FileNotFoundError(f"Model {model_name} not found")

                load_time = time.time() - start_time
                self._load_times[model_name] = load_time
                logger.info(f"Loaded model {model_name} in {load_time:.3f}s")

            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {str(e)}")
                raise

        return self._models[model_name]

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get model pool memory statistics"""
        return {
            "loaded_models": list(self._models.keys()),
            "model_count": len(self._models),
            "load_times": self._load_times
        }

class SuperOrchestrator(BaseAgent):
    """
    🏛️ Super Orchestrator - Unified High-Performance Orchestration

    Replaces multiple orchestrators with a single, efficient orchestrator
    that provides intelligent routing, direct execution, and comprehensive monitoring.
    """

    def __init__(self, agent_id: str = "super_orchestrator"):
        super().__init__(
            agent_id=agent_id,
            name="Super Orchestrator",
            permission_level=PermissionLevel.ADMIN
        )

        # Performance optimizations
        self.model_pool = ModelPool()
        self._agent_cache = {}
        self._response_cache = {}
        self._performance_metrics = {
            "total_requests": 0,
            "avg_response_time": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

        # Direct agent references (no factory pattern)
        self._core_agents = {}
        self._initialize_agents()

        logger.info(f"SuperOrchestrator initialized with {len(self._core_agents)} agents")

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define super orchestrator capabilities"""
        return [
            AgentCapability(
                name="unified_orchestration",
                description="All orchestration capabilities in single agent",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["routing", "caching", "monitoring"],
                data_access=["all"],
                execution_time_estimate=0.05  # 50ms target
            ),
            AgentCapability(
                name="intelligent_routing",
                description="Smart request routing to optimal agent",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["routing", "optimization"],
                data_access=["all"],
                execution_time_estimate=0.01  # 10ms routing
            ),
            AgentCapability(
                name="performance_monitoring",
                description="Real-time performance tracking and optimization",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["monitoring", "metrics"],
                data_access=["performance"],
                execution_time_estimate=0.001
            ),
            AgentCapability(
                name="legacy_compatibility",
                description="Compatibility with existing agent interfaces",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["compatibility", "translation"],
                data_access=["all"],
                execution_time_estimate=0.02
            )
        ]

    def _initialize_agents(self):
        """Initialize core agents with lazy loading"""
        try:
            # Import agent classes
            from agents.learning_navigator_agent import LearningNavigatorAgent
            from agents.insight_generator_agent import InsightGeneratorAgent
            from agents.weekly_prediction_generation_agent import WeeklyPredictionGenerationAgent
            from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
            from agents.quality_assurance_agent import QualityAssuranceAgent
            from agents.performance_monitor_agent import PerformanceMonitorAgent

            # Store classes for lazy instantiation
            self._agent_classes = {
                "learning": LearningNavigatorAgent,
                "insight": InsightGeneratorAgent,
                "prediction": WeeklyPredictionGenerationAgent,
                "matchup": WeeklyMatchupAnalysisAgent,
                "quality": QualityAssuranceAgent,
                "performance": PerformanceMonitorAgent
            }

            logger.info(f"Agent classes loaded: {list(self._agent_classes.keys())}")

        except Exception as e:
            logger.error(f"Failed to load agent classes: {str(e)}")
            self._agent_classes = {}

    def _get_agent(self, agent_type: str):
        """Get agent instance with caching"""
        if agent_type not in self._agent_cache:
            if agent_type in self._agent_classes:
                try:
                    agent = self._agent_classes[agent_type](f"{agent_type}_instance")
                    self._agent_cache[agent_type] = agent
                    logger.info(f"Created {agent_type} agent")
                except Exception as e:
                    logger.error(f"Failed to create {agent_type} agent: {str(e)}")
                    return None
            else:
                logger.warning(f"Unknown agent type: {agent_type}")
                return None

        return self._agent_cache[agent_type]

    def _route_request(self, request: AnalyticsRequest) -> Optional[str]:
        """Intelligent request routing - 10ms target"""
        route_map = {
            RequestType.LEARNING: "learning",
            RequestType.INSIGHT: "insight",
            RequestType.PREDICTION: "prediction",
            RequestType.WEEKLY: "prediction",  # Weekly predictions
            RequestType.ANALYSIS: "insight",   # Analysis -> insights
            RequestType.VALIDATION: "quality",
            RequestType.PERFORMANCE: "performance",
            RequestType.DATA: "prediction"     # Data access through prediction agent
        }

        agent_type = route_map.get(request.request_type)
        if agent_type:
            logger.debug(f"Routed {request.request_type.value} to {agent_type}")

        return agent_type

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute super orchestrator actions"""
        try:
            if action == "process_request":
                return self._process_request(parameters, user_context)
            elif action == "get_performance_metrics":
                return self._get_performance_metrics()
            elif action == "clear_cache":
                return self._clear_cache()
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "execution_time": 0
            }

    def _process_request(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process analytics request with performance tracking"""
        start_time = time.time()

        try:
            # Create request object
            request = AnalyticsRequest(
                user_id=user_context.get("user_id", "anonymous"),
                query=parameters.get("query", ""),
                request_type=RequestType(parameters.get("request_type", "analysis")),
                parameters=parameters,
                context=user_context
            )

            # Check cache first
            cache_key = f"{request.query}:{request.request_type.value}"
            if cache_key in self._response_cache:
                self._performance_metrics["cache_hits"] += 1
                cached_response = self._response_cache[cache_key]
                cached_response["metadata"]["from_cache"] = True
                cached_response["execution_time"] = time.time() - start_time
                return cached_response

            self._performance_metrics["cache_misses"] += 1

            # Route to appropriate agent
            agent_type = self._route_request(request)
            if not agent_type:
                return AnalyticsResponse(
                    status="error",
                    data=None,
                    metadata={"error": "No suitable agent found"},
                    execution_time=time.time() - start_time,
                    error_message="Request routing failed"
                ).__dict__

            # Get agent and execute
            agent = self._get_agent(agent_type)
            if not agent:
                return AnalyticsResponse(
                    status="error",
                    data=None,
                    metadata={"error": f"Failed to initialize {agent_type} agent"},
                    execution_time=time.time() - start_time,
                    error_message="Agent initialization failed"
                ).__dict__

            # Execute request on agent
            try:
                if hasattr(agent, 'process_request'):
                    result = agent.process_request(request.query, request.parameters, request.context)
                elif hasattr(agent, '_execute_action'):
                    result = agent._execute_action('handle_request', request.parameters, request.context)
                else:
                    # Fallback to main capability
                    result = agent._execute_action(request.request_type.value, request.parameters, request.context)

                # Create response
                response = AnalyticsResponse(
                    status="success",
                    data=result.get("data", result),
                    metadata={
                        "agent_used": agent_type,
                        "request_type": request.request_type.value,
                        "performance": self.model_pool.get_memory_usage()
                    },
                    execution_time=time.time() - start_time
                ).__dict__

            except Exception as e:
                logger.error(f"Agent execution failed: {str(e)}")
                response = AnalyticsResponse(
                    status="error",
                    data=None,
                    metadata={"agent_used": agent_type, "error_type": "agent_execution"},
                    execution_time=time.time() - start_time,
                    error_message=str(e)
                ).__dict__

            # Cache successful responses
            if response["status"] == "success":
                self._response_cache[cache_key] = response

            # Update metrics
            self._performance_metrics["total_requests"] += 1
            self._performance_metrics["avg_response_time"] = (
                (self._performance_metrics["avg_response_time"] * (self._performance_metrics["total_requests"] - 1) +
                 response["execution_time"]) / self._performance_metrics["total_requests"]
            )

            return response

        except Exception as e:
            logger.error(f"Request processing failed: {str(e)}")
            return AnalyticsResponse(
                status="error",
                data=None,
                metadata={"error_type": "orchestration_failure"},
                execution_time=time.time() - start_time,
                error_message=str(e)
            ).__dict__

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            "orchestrator_metrics": self._performance_metrics,
            "model_pool_metrics": self.model_pool.get_memory_usage(),
            "agent_cache_size": len(self._agent_cache),
            "response_cache_size": len(self._response_cache),
            "cache_hit_rate": (
                self._performance_metrics["cache_hits"] /
                max(1, self._performance_metrics["cache_hits"] + self._performance_metrics["cache_misses"])
            ) if self._performance_metrics["cache_hits"] + self._performance_metrics["cache_misses"] > 0 else 0
        }

    def _clear_cache(self) -> Dict[str, Any]:
        """Clear all caches"""
        self._response_cache.clear()
        self._agent_cache.clear()

        # Note: Model pool not cleared to maintain performance

        return {
            "status": "success",
            "message": "Caches cleared",
            "timestamp": time.time()
        }

    # Legacy compatibility methods
    def process_analytics_request(self, user_id: str, query: str, request_type: str,
                                 parameters: Dict[str, Any], context: Dict[str, Any]) -> AnalyticsResponse:
        """Legacy compatibility method"""
        request = AnalyticsRequest(
            user_id=user_id,
            query=query,
            request_type=RequestType(request_type),
            parameters=parameters,
            context=context
        )

        result = self._process_request({
            "query": query,
            "request_type": request_type,
            "parameters": parameters
        }, {"user_id": user_id})

        return AnalyticsResponse(**result)

# Factory function for easy instantiation
def create_super_orchestrator(agent_id: str = "super_orchestrator") -> SuperOrchestrator:
    """Create and return SuperOrchestrator instance"""
    return SuperOrchestrator(agent_id)

# Quick test function
def test_super_orchestrator():
    """Test SuperOrchestrator functionality"""
    print("🧪 Testing SuperOrchestrator...")

    try:
        orchestrator = create_super_orchestrator()
        print("✅ SuperOrchestrator created successfully")

        # Test performance metrics
        metrics = orchestrator._get_performance_metrics()
        print(f"📊 Performance metrics: {metrics}")

        # Test simple request
        response = orchestrator.process_analytics_request(
            user_id="test_user",
            query="test request",
            request_type="analysis",
            parameters={"test": True},
            context={}
        )
        print(f"📝 Response: {response}")

        print("✅ SuperOrchestrator test completed successfully")

    except Exception as e:
        print(f"❌ SuperOrchestrator test failed: {str(e)}")

if __name__ == "__main__":
    test_super_orchestrator()