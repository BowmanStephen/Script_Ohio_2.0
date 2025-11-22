#!/usr/bin/env python3
"""
Simplified Analytics Orchestrator - Based on WeeklyAnalysisOrchestrator Pattern

This is a simplified orchestrator that matches the pattern actually used in production.
It directly instantiates agents and calls execute_task() - no context/state/workflow complexity.

Author: Consolidation Plan Implementation
Created: 2025-11-19
Version: 2.0 (Simplified)
"""

import os
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path

from agents.core.agent_framework import (
    AgentFactory,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    PermissionLevel,
    RequestRouter,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalyticsRequest:
    """High-level analytics request from user"""
    user_id: str
    query: str
    query_type: str
    parameters: Dict[str, Any]
    context_hints: Dict[str, Any] = None
    request_id: str = None
    priority: int = 1
    timestamp: float = None

    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.context_hints is None:
            self.context_hints = {}

@dataclass
class AnalyticsResponse:
    """High-level analytics response to user"""
    request_id: str
    status: str
    results: Any
    insights: List[str]
    visualizations: List[Dict[str, Any]]
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

class SimplifiedAnalyticsOrchestrator:
    """
    Simplified orchestrator matching WeeklyAnalysisOrchestrator pattern.
    
    Features:
    - Direct agent instantiation (no factory complexity)
    - Simple execute_task() calls
    - No context/role management
    - No state persistence
    - No workflow automation
    """
    
    def __init__(self, base_path: str = None):
        """Initialize the simplified orchestrator"""
        self.base_path = base_path or os.getcwd()
        self.agent_factory = AgentFactory(base_path)
        self.request_router = RequestRouter(self.agent_factory)
        
        # Load available agents
        self._load_agents()
        
        # Simple session tracking (in-memory only)
        self.session_history = []
        
        # Performance tracking
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0
        }
        
        logger.info("Simplified Analytics Orchestrator initialized")
    
    def _load_agents(self):
        """Load and register all available agents"""
        try:
            from agents.learning_navigator_agent import LearningNavigatorAgent
            from src.models.execution.engine import ModelExecutionEngine
            from agents.insight_generator_agent import InsightGeneratorAgent
            from agents.conversational_ai_agent import ConversationalAIAgent
            
            self.agent_factory.register_agent_class(LearningNavigatorAgent, "learning_navigator")
            self.agent_factory.register_agent_class(ModelExecutionEngine, "model_engine")
            self.agent_factory.register_agent_class(InsightGeneratorAgent, "insight_generator")
            self.agent_factory.register_agent_class(ConversationalAIAgent, "conversational_ai")
            
            # Create default instances
            self.agent_factory.create_agent("learning_navigator", "default_learning_nav")
            self.agent_factory.create_agent("model_engine", "default_model_engine")
            self.agent_factory.create_agent("insight_generator", "default_insight_generator")
            self.agent_factory.create_agent("conversational_ai", "default_conversational_ai")
            
            logger.info("Loaded agent classes and created default instances")
        except ImportError as e:
            logger.warning(f"Could not load some agent classes: {e}")
    
    def process_analytics_request(self, request: AnalyticsRequest) -> AnalyticsResponse:
        """
        Process a high-level analytics request.
        
        Simplified version: Direct agent execution without context/state management.
        """
        start_time = time.time()
        request_id = request.request_id
        
        logger.info(f"Processing analytics request {request_id}: {request.query}")
        
        try:
            # 1. Analyze request and determine required agents
            required_agents = self._analyze_request_requirements(request)
            
            # 2. Execute agent requests directly
            agent_responses = self._execute_agent_requests(request_id, required_agents, request)
            
            # 3. Synthesize results into high-level response
            response = self._synthesize_response(request_id, request, agent_responses)
            
            # 4. Update performance metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, success=True)
            
            # 5. Store in session history (in-memory only)
            self.session_history.append({
                'request_id': request_id,
                'query': request.query,
                'status': response.status,
                'execution_time': execution_time,
                'timestamp': request.timestamp
            })
            
            # Keep only last 100 interactions
            if len(self.session_history) > 100:
                self.session_history = self.session_history[-100:]
            
            logger.info(f"Completed analytics request {request_id} in {execution_time:.2f}s")
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, success=False)
            
            error_message = f"Error processing analytics request: {str(e)}"
            logger.error(error_message)
            
            return AnalyticsResponse(
                request_id=request_id,
                status="error",
                results=None,
                insights=[],
                visualizations=[],
                error_message=error_message,
                execution_time=execution_time
            )
    
    def _analyze_request_requirements(self, request: AnalyticsRequest) -> List[Dict[str, Any]]:
        """Analyze request to determine which agents are needed"""
        requirements = []
        query_lower = request.query.lower()
        
        # Learning/educational requests
        if any(keyword in query_lower for keyword in ['learn', 'tutorial', 'explain', 'introduction', 'guide', 'help']):
            requirements.append({
                'agent_type': 'learning_navigator',
                'action': 'guide_learning_path' if 'path' in query_lower else 'recommend_content',
                'parameters': {
                    'query': request.query,
                    'current_notebook': request.parameters.get('current_notebook'),
                    'skill_level': request.context_hints.get('skill_level', 'beginner')
                }
            })
        
        # Model/prediction requests
        if any(keyword in query_lower for keyword in ['predict', 'model', 'analyze', 'forecast', 'outcome']):
            requirements.append({
                'agent_type': 'model_engine',
                'action': 'predict_game_outcome',
                'parameters': {
                    'query': request.query,
                    'teams': request.parameters.get('teams', []),
                    'model_type': request.parameters.get('model_type', 'ridge_model_2025')
                }
            })
        
        # Analysis requests
        if any(keyword in query_lower for keyword in ['analyze', 'analysis', 'compare', 'ranking', 'statistics', 'insights']):
            requirements.append({
                'agent_type': 'insight_generator',
                'action': 'generate_analysis',
                'parameters': {
                    'analysis_type': request.parameters.get('analysis_type', 'performance'),
                    'focus_areas': request.parameters.get('focus_areas', ['performance', 'descriptive'])
                }
            })
        
        # If no specific requirements detected, provide general guidance
        if not requirements:
            requirements.append({
                'agent_type': 'learning_navigator',
                'action': 'recommend_content',
                'parameters': {
                    'query': request.query,
                    'general_guidance': True
                }
            })
        
        return requirements
    
    def _execute_agent_requests(self, request_id: str, required_agents: List[Dict[str, Any]],
                                analytics_request: AnalyticsRequest) -> List[AgentResponse]:
        """Execute requests to required agents - simplified direct execution"""
        agent_responses = []
        
        user_permissions = PermissionLevel.READ_EXECUTE_WRITE
        
        for agent_req in required_agents:
            try:
                agent_id = f"default_{agent_req['agent_type']}"
                agent = self.agent_factory.get_agent(agent_id)
                
                if not agent:
                    # Create agent if it doesn't exist
                    agent = self.agent_factory.create_agent(agent_req['agent_type'], agent_id)
                
                # Create agent request
                agent_request = AgentRequest(
                    request_id=f"{request_id}_{agent_req['agent_type']}",
                    agent_type=agent_req['agent_type'],
                    action=agent_req['action'],
                    parameters=agent_req['parameters'],
                    user_context={
                        'user_id': analytics_request.user_id,
                        'query': analytics_request.query,
                        'query_type': analytics_request.query_type
                    },
                    timestamp=time.time(),
                    priority=analytics_request.priority
                )
                
                # Submit and process request
                self.request_router.submit_request(agent_request, user_permissions)
                self.request_router.process_requests(user_permissions)
                
                # Get response
                response = self.request_router.get_request_status(agent_request.request_id)
                if response and response['status'] == 'completed':
                    response_dict = response['response']
                    agent_response = AgentResponse(
                        request_id=response_dict['request_id'],
                        agent_type=response_dict['agent_type'],
                        status=response_dict['status'],
                        result=response_dict['result'],
                        error_message=response_dict['error_message'],
                        execution_time=response_dict['execution_time'],
                        metadata=response_dict['metadata']
                    )
                    agent_responses.append(agent_response)
                    
            except Exception as e:
                logger.error(f"Error executing agent request: {str(e)}")
                error_response = AgentResponse(
                    request_id=f"{request_id}_{agent_req['agent_type']}",
                    agent_type=agent_req['agent_type'],
                    status=AgentStatus.ERROR,
                    result=None,
                    error_message=str(e),
                    execution_time=0.0,
                    metadata={'error': True}
                )
                agent_responses.append(error_response)
        
        return agent_responses
    
    def _synthesize_response(self, request_id: str, analytics_request: AnalyticsRequest,
                           agent_responses: List[AgentResponse]) -> AnalyticsResponse:
        """Synthesize agent responses into high-level analytics response"""
        successful_responses = [r for r in agent_responses if r.status == AgentStatus.COMPLETED]
        failed_responses = [r for r in agent_responses if r.status == AgentStatus.ERROR]
        
        # Extract insights from successful responses
        insights = []
        visualizations = []
        results = {}
        
        for response in successful_responses:
            if response.result:
                results[response.agent_type] = response.result
                
                if isinstance(response.result, dict):
                    if 'insights' in response.result:
                        insights.extend(response.result['insights'][:5])
                    if 'visualizations' in response.result:
                        visualizations.extend(response.result['visualizations'])
                    if 'recommendations' in response.result:
                        for rec in response.result['recommendations'][:3]:
                            insights.append(f"Recommendation: {rec.get('reason', 'No reason provided')}")
        
        # Add insights about any errors
        for response in failed_responses:
            insights.append(f"Note: {response.error_message}")
        
        # Determine status
        if failed_responses and not successful_responses:
            status = "error"
        elif failed_responses:
            status = "partial_success"
        else:
            status = "success"
        
        return AnalyticsResponse(
            request_id=request_id,
            status=status,
            results=results,
            insights=insights,
            visualizations=visualizations,
            error_message=None if status != "error" else "All agent requests failed",
            metadata={
                'agents_used': [r.agent_type for r in successful_responses],
                'agents_failed': [r.agent_type for r in failed_responses]
            }
        )
    
    def _update_performance_metrics(self, execution_time: float, success: bool):
        """Update orchestrator performance metrics"""
        self.performance_metrics['total_requests'] += 1
        
        if success:
            self.performance_metrics['successful_requests'] += 1
        else:
            self.performance_metrics['failed_requests'] += 1
        
        # Update average response time
        total_requests = self.performance_metrics['total_requests']
        current_avg = self.performance_metrics.get('average_response_time', 0.0)
        self.performance_metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + execution_time) / total_requests
        )
    
    def get_live_scoreboard_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Expose live scoreboard events if available"""
        # Simplified - return empty list if no subscription manager
        return []


# Backward compatibility alias
AnalyticsOrchestrator = SimplifiedAnalyticsOrchestrator

