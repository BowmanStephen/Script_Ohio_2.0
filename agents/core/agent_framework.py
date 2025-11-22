#!/usr/bin/env python3
"""
Agent Framework - Core Architecture for Intelligent Analytics Agents

This module provides the foundation for creating and managing specialized agents
in the Script Ohio 2.0 analytics platform.

Author: Claude Code Assistant
Created: 2025-11-07
Version: 1.0
"""

import json
import os
import time
import logging
from abc import ABC, abstractmethod
from collections import deque
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import importlib.util

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    COMPLETED = "completed"

class PermissionLevel(Enum):
    """Permission levels for agent access control"""
    READ_ONLY = 1
    READ_EXECUTE = 2
    READ_EXECUTE_WRITE = 3
    ADMIN = 4

@dataclass
class AgentCapability:
    """Defines what an agent can do"""
    name: str
    description: str
    permission_required: PermissionLevel
    tools_required: List[str]
    data_access: List[str]
    execution_time_estimate: float  # in seconds

@dataclass
class AgentRequest:
    """Request to an agent"""
    request_id: str
    agent_type: str
    action: str
    parameters: Dict[str, Any]
    user_context: Dict[str, Any]
    timestamp: float
    priority: int = 1  # 1=low, 2=medium, 3=high

@dataclass
class AgentResponse:
    """Response from an agent"""
    request_id: str
    agent_type: str
    status: AgentStatus
    result: Optional[Any]
    error_message: Optional[str]
    execution_time: float
    metadata: Dict[str, Any]

class BaseAgent(ABC):
    """
    Base class for all specialized agents in the Script Ohio 2.0 platform.

    All agents must inherit from this class and implement the required methods.
    """

    def __init__(self, agent_id: str, name: str, permission_level: PermissionLevel, tool_loader=None):
        self.agent_id = agent_id
        self.name = name
        self.permission_level = permission_level
        self.status = AgentStatus.IDLE
        self.capabilities = self._define_capabilities()
        self.execution_history = []
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_execution_time': 0.0,
            'total_execution_time': 0.0
        }
        self.tool_loader = tool_loader

        logger.info(f"Agent {self.name} ({self.agent_id}) initialized")

    @abstractmethod
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of this agent"""
        pass

    @abstractmethod
    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the specific action requested"""
        pass

    def can_handle_request(self, request: AgentRequest, user_permissions: PermissionLevel) -> bool:
        """
        Check if this agent can handle the given request.

        Args:
            request: The agent request
            user_permissions: User's permission level

        Returns:
            True if the agent can handle the request
        """
        # Check if this is the right agent type
        agent_type_from_class = self.__class__.__name__.replace('Agent', '').lower()
        # Handle special case for learning navigator (LearningNavigator -> learning_navigator)
        if 'learning' in agent_type_from_class and 'navigator' in agent_type_from_class:
            agent_type_from_class = 'learning_navigator'
        # Handle special case for model execution engine (ModelExecutionEngine -> model_engine)
        elif 'model' in agent_type_from_class and 'execution' in agent_type_from_class and 'engine' in agent_type_from_class:
            agent_type_from_class = 'model_engine'
        # Handle special case for insight generator (InsightGenerator -> insight_generator)
        elif 'insight' in agent_type_from_class and 'generator' in agent_type_from_class:
            agent_type_from_class = 'insight_generator'
        # Handle special case for workflow automator (WorkflowAutomator -> workflow_automator)
        elif 'workflow' in agent_type_from_class and 'automator' in agent_type_from_class:
            agent_type_from_class = 'workflow_automator'
        # Handle special case for conversational AI (ConversationalAI -> conversational_ai)
        elif 'conversational' in agent_type_from_class and 'ai' in agent_type_from_class:
            agent_type_from_class = 'conversational_ai'
        # Handle special case for Week 12 prediction orchestrator (Week12PredictionOrchestrator -> week12_prediction_orchestrator)
        elif 'week12' in agent_type_from_class and 'prediction' in agent_type_from_class and 'orchestrator' in agent_type_from_class:
            agent_type_from_class = 'week12_prediction_orchestrator'
        # Handle special case for weekly analysis orchestrator (WeeklyAnalysisOrchestrator -> weekly_analysis_orchestrator)
        elif 'weekly' in agent_type_from_class and 'analysis' in agent_type_from_class and 'orchestrator' in agent_type_from_class:
            agent_type_from_class = 'weekly_analysis_orchestrator'
        # Handle special case for weekly agents (WeeklyPredictionGenerationAgent -> weekly_prediction_generation)
        elif 'weekly' in agent_type_from_class and 'prediction' in agent_type_from_class and 'generation' in agent_type_from_class:
            agent_type_from_class = 'weekly_prediction_generation'
        elif 'weekly' in agent_type_from_class and 'matchup' in agent_type_from_class and 'analysis' in agent_type_from_class:
            agent_type_from_class = 'weekly_matchup_analysis'
        elif 'weekly' in agent_type_from_class and 'model' in agent_type_from_class and 'validation' in agent_type_from_class:
            agent_type_from_class = 'weekly_model_validation'
        # Handle special case for Week 12 agents (Week12PredictionGenerationAgent -> week12_prediction_generation)
        elif 'week12' in agent_type_from_class and 'prediction' in agent_type_from_class and 'generation' in agent_type_from_class:
            agent_type_from_class = 'week12_prediction_generation'
        elif 'week12' in agent_type_from_class and 'matchup' in agent_type_from_class and 'analysis' in agent_type_from_class:
            agent_type_from_class = 'week12_matchup_analysis'
        elif 'week12' in agent_type_from_class and 'model' in agent_type_from_class and 'validation' in agent_type_from_class:
            agent_type_from_class = 'week12_model_validation'
        elif 'week12' in agent_type_from_class and 'mock' in agent_type_from_class and 'enhancement' in agent_type_from_class:
            agent_type_from_class = 'week12_mock_enhancement'
        # Handle special case for Week 13 agents (Week13ConsolidationAgent -> week13_consolidation)
        elif 'week13' in agent_type_from_class and 'consolidation' in agent_type_from_class:
            agent_type_from_class = 'week13_consolidation'
        # Handle special case for Legacy Creation Agent (LegacyCreationAgent -> legacy_creation)
        elif 'legacy' in agent_type_from_class and 'creation' in agent_type_from_class:
            agent_type_from_class = 'legacy_creation'

        if request.agent_type != agent_type_from_class:
            return False

        # Check permission level
        required_permission = self.permission_level
        if user_permissions.value < required_permission.value:
            logger.warning(f"Insufficient permissions for {request.action} on {self.name}")
            return False

        # Check if action is supported
        action_capability = next((cap for cap in self.capabilities if cap.name == request.action), None)
        if not action_capability:
            return False

        return True

    def execute_request(self, request: AgentRequest, user_permissions: PermissionLevel) -> AgentResponse:
        """
        Execute a request to this agent.

        Args:
            request: The agent request
            user_permissions: User's permission level

        Returns:
            Agent response with results or error
        """
        start_time = time.time()
        self.status = AgentStatus.BUSY

        logger.info(f"Executing {request.action} on {self.name} (Request ID: {request.request_id})")

        try:
            # Validate request
            if not self.can_handle_request(request, user_permissions):
                raise PermissionError(f"Agent {self.name} cannot handle request {request.request_id}")

            # Execute the action
            result = self._execute_action(request.action, request.parameters, request.user_context)

            # Update metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, success=True)

            # Create response
            response = AgentResponse(
                request_id=request.request_id,
                agent_type=self.__class__.__name__,
                status=AgentStatus.COMPLETED,
                result=result,
                error_message=None,
                execution_time=execution_time,
                metadata={
                    'agent_id': self.agent_id,
                    'capabilities_used': [cap.name for cap in self.capabilities if cap.name == request.action],
                    'user_role': request.user_context.get('role', 'unknown')
                }
            )

            # Store execution history
            self.execution_history.append({
                'request_id': request.request_id,
                'action': request.action,
                'timestamp': time.time(),
                'execution_time': execution_time,
                'success': True
            })

            self.status = AgentStatus.IDLE
            return response

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, success=False)

            error_message = f"Error executing {request.action} on {self.name}: {str(e)}"
            logger.error(error_message)

            # Store execution history
            self.execution_history.append({
                'request_id': request.request_id,
                'action': request.action,
                'timestamp': time.time(),
                'execution_time': execution_time,
                'success': False,
                'error': str(e)
            })

            self.status = AgentStatus.ERROR
            return AgentResponse(
                request_id=request.request_id,
                agent_type=self.__class__.__name__,
                status=AgentStatus.ERROR,
                result=None,
                error_message=error_message,
                execution_time=execution_time,
                metadata={'agent_id': self.agent_id}
            )

    def _update_performance_metrics(self, execution_time: float, success: bool):
        """Update performance metrics for this agent"""
        self.performance_metrics['total_requests'] += 1
        self.performance_metrics['total_execution_time'] += execution_time

        if success:
            self.performance_metrics['successful_requests'] += 1
        else:
            self.performance_metrics['failed_requests'] += 1

        # Update average execution time
        total_requests = self.performance_metrics['total_requests']
        self.performance_metrics['average_execution_time'] = (
            self.performance_metrics['total_execution_time'] / total_requests
        )

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any],
                    user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool using the tool loader.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool execution parameters
            user_context: User context for permissions

        Returns:
            Tool execution result
        """
        if not self.tool_loader:
            raise ValueError("Tool loader not available for this agent")

        # Check if agent has permission to use this tool
        tool = self.tool_loader.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        if tool.metadata.permission_required > self.permission_level.value:
            raise PermissionError(f"Insufficient permissions for tool: {tool_name}")

        # Execute the tool
        result = self.tool_loader.execute_tool(tool_name, parameters, user_context)

        if result.success:
            return result.result
        else:
            raise Exception(f"Tool execution failed: {result.error_message}")

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of tools available to this agent based on permission level"""
        if not self.tool_loader:
            return []

        tools = self.tool_loader.get_tools_for_permission_level(self.permission_level.value)
        return [{'name': tool, 'available': True} for tool in tools]

    def get_status(self) -> Dict[str, Any]:
        """Get current status and metrics for this agent"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'status': self.status.value,
            'permission_level': self.permission_level.value,
            'capabilities': [asdict(cap) for cap in self.capabilities],
            'performance_metrics': self.performance_metrics.copy(),
            'recent_executions': self.execution_history[-5:] if self.execution_history else [],
            'available_tools': len(self.get_available_tools())
        }

class AgentFactory:
    """
    Factory for creating and managing agent instances.
    """

    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.getcwd()
        self.agents = {}
        self.agent_registry = {}

        # Initialize tool loader
        from agents.core.tool_loader import ToolLoader
        self.tool_loader = ToolLoader(base_path=base_path)

        logger.info("Agent Factory initialized with tool loader")

    def register_agent_class(self, agent_class: type, agent_type: str):
        """Register an agent class with the factory"""
        self.agent_registry[agent_type] = agent_class
        logger.info(f"Registered agent class: {agent_type}")

    def create_agent(self, agent_type: str, agent_id: str = None, **kwargs) -> BaseAgent:
        """
        Create an instance of a registered agent.

        Args:
            agent_type: Type of agent to create
            agent_id: Unique ID for the agent (optional)
            **kwargs: Additional arguments for agent initialization

        Returns:
            Created agent instance
        """
        if agent_type not in self.agent_registry:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent_class = self.agent_registry[agent_type]

        # Generate ID if not provided
        if agent_id is None:
            agent_id = f"{agent_type}_{int(time.time())}"

        # Ensure tool_loader is passed to agent
        if 'tool_loader' not in kwargs:
            kwargs['tool_loader'] = self.tool_loader

        # Create agent instance
        agent = agent_class(agent_id=agent_id, **kwargs)

        # Store in registry
        self.agents[agent_id] = agent

        logger.info(f"Created agent {agent_type} with ID {agent_id}")
        return agent

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent instance by ID"""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [agent.get_status() for agent in self.agents.values()]

    def destroy_agent(self, agent_id: str) -> bool:
        """Destroy an agent instance"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Destroyed agent {agent_id}")
            return True
        return False

class RequestRouter:
    """
    Routes requests to appropriate agents based on capabilities and permissions.
    """

    def __init__(self, agent_factory: AgentFactory):
        self.agent_factory = agent_factory
        self.request_queue = []
        self.active_requests = {}
        self.completed_requests = {}
        
        # Instrumentation metrics
        self.instrumentation_metrics = {
            'submit_count': 0,
            'process_count': 0,
            'total_overhead_ms': 0.0,
            'permission_denials': 0,
            'agent_not_found_count': 0,
            'priority_sorts': 0,
            'queue_sizes_at_submit': deque(maxlen=1000),
            'queue_sizes_at_process': deque(maxlen=1000),
            'errors_caught': 0,
            'completed_requests_queries': 0
        }
        
        logger.info("Request Router initialized")

    def submit_request(self, request: AgentRequest, user_permissions: PermissionLevel = PermissionLevel.READ_ONLY) -> str:
        """
        Submit a request to be routed to an appropriate agent.

        Args:
            request: The request to submit
            user_permissions: User's permission level

        Returns:
            Request ID for tracking
        """
        start_time = time.time()
        
        # Track queue size at submit
        queue_size = len(self.request_queue)
        self.instrumentation_metrics['queue_sizes_at_submit'].append(queue_size)
        self.instrumentation_metrics['submit_count'] += 1
        
        # Add to queue
        self.request_queue.append(request)
        self.active_requests[request.request_id] = request

        overhead_ms = (time.time() - start_time) * 1000
        self.instrumentation_metrics['total_overhead_ms'] += overhead_ms
        
        logger.info(f"[ROUTER_AUDIT] SUBMIT: request_id={request.request_id} queue_size={queue_size} priority={request.priority} overhead_ms={overhead_ms:.2f}")
        logger.info(f"Submitted request {request.request_id} to queue")
        return request.request_id

    def process_requests(self, user_permissions: PermissionLevel = PermissionLevel.READ_ONLY):
        """
        Process queued requests by routing them to appropriate agents.
        """
        if not self.request_queue:
            return

        process_start_time = time.time()
        queue_size_at_start = len(self.request_queue)
        self.instrumentation_metrics['queue_sizes_at_process'].append(queue_size_at_start)
        self.instrumentation_metrics['process_count'] += 1
        
        logger.info(f"[ROUTER_AUDIT] PROCESS_START: queue_size={queue_size_at_start}")

        # Sort by priority
        priorities_before = [r.priority for r in self.request_queue]
        self.request_queue.sort(key=lambda x: x.priority, reverse=True)
        priorities_after = [r.priority for r in self.request_queue]
        
        # Check if sorting actually changed order
        if priorities_before != priorities_after:
            self.instrumentation_metrics['priority_sorts'] += 1
            logger.info(f"[ROUTER_AUDIT] PRIORITY_SORT: queue_size={queue_size_at_start}")

        # Process requests
        processed_requests = []

        for request in self.request_queue:
            try:
                # Find appropriate agent
                agent = self._find_agent_for_request(request, user_permissions)

                if agent:
                    # Agent found means permissions already validated in _find_agent_for_request()
                    logger.info(f"[ROUTER_AUDIT] PERMISSION_GRANTED: request_id={request.request_id} agent_type={request.agent_type}")
                    
                    # Execute request
                    response = agent.execute_request(request, user_permissions)

                    # Store response
                    self.completed_requests[request.request_id] = response

                    # Remove from active requests
                    if request.request_id in self.active_requests:
                        del self.active_requests[request.request_id]

                    processed_requests.append(request)
                    logger.info(f"Completed request {request.request_id}")
                else:
                    self.instrumentation_metrics['agent_not_found_count'] += 1
                    logger.warning(f"[ROUTER_AUDIT] AGENT_NOT_FOUND: request_id={request.request_id} agent_type={request.agent_type}")
                    logger.warning(f"No suitable agent found for request {request.request_id}")

            except Exception as e:
                self.instrumentation_metrics['errors_caught'] += 1
                logger.error(f"[ROUTER_AUDIT] ERROR_CAUGHT: request_id={request.request_id} error={str(e)}")
                logger.error(f"Error processing request {request.request_id}: {str(e)}")
                processed_requests.append(request)

        # Remove processed requests from queue
        for request in processed_requests:
            if request in self.request_queue:
                self.request_queue.remove(request)
        
        process_overhead_ms = (time.time() - process_start_time) * 1000
        self.instrumentation_metrics['total_overhead_ms'] += process_overhead_ms

    def _find_agent_for_request(self, request: AgentRequest, user_permissions: PermissionLevel) -> Optional[BaseAgent]:
        """Find an agent that can handle the request"""
        for agent in self.agent_factory.agents.values():
            if agent.can_handle_request(request, user_permissions):
                return agent
        return None

    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific request"""
        self.instrumentation_metrics['completed_requests_queries'] += 1
        logger.info(f"[ROUTER_AUDIT] STATUS_RETRIEVED: request_id={request_id}")
        
        if request_id in self.completed_requests:
            response = self.completed_requests[request_id]
            return {
                'status': 'completed',
                'response': asdict(response)
            }
        elif request_id in self.active_requests:
            return {
                'status': 'processing',
                'queue_position': self.request_queue.index(self.active_requests[request_id]) + 1 if self.active_requests[request_id] in self.request_queue else 0
            }
        else:
            return None

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'queue_length': len(self.request_queue),
            'active_requests': len(self.active_requests),
            'completed_requests': len(self.completed_requests),
            'pending_requests': [req.request_id for req in self.request_queue]
        }
    
    def get_instrumentation_report(self) -> Dict[str, Any]:
        """
        Get comprehensive instrumentation report with metrics and statistics.
        
        Returns:
            Dictionary containing all tracked metrics and computed statistics
        """
        metrics = self.instrumentation_metrics.copy()
        
        # Compute statistics
        submit_count = metrics['submit_count']
        process_count = metrics['process_count']
        
        # Average queue sizes
        avg_queue_at_submit = (
            sum(metrics['queue_sizes_at_submit']) / len(metrics['queue_sizes_at_submit'])
            if metrics['queue_sizes_at_submit'] else 0.0
        )
        avg_queue_at_process = (
            sum(metrics['queue_sizes_at_process']) / len(metrics['queue_sizes_at_process'])
            if metrics['queue_sizes_at_process'] else 0.0
        )
        
        # Average overhead per operation
        avg_overhead_per_submit = (
            metrics['total_overhead_ms'] / submit_count if submit_count > 0 else 0.0
        )
        avg_overhead_per_process = (
            metrics['total_overhead_ms'] / process_count if process_count > 0 else 0.0
        )
        
        # Rates
        permission_denial_rate = (
            metrics['permission_denials'] / process_count if process_count > 0 else 0.0
        )
        agent_not_found_rate = (
            metrics['agent_not_found_count'] / process_count if process_count > 0 else 0.0
        )
        error_rate = (
            metrics['errors_caught'] / process_count if process_count > 0 else 0.0
        )
        priority_sort_rate = (
            metrics['priority_sorts'] / process_count if process_count > 0 else 0.0
        )
        
        return {
            'raw_metrics': metrics,
            'statistics': {
                'average_queue_size_at_submit': round(avg_queue_at_submit, 2),
                'average_queue_size_at_process': round(avg_queue_at_process, 2),
                'average_overhead_per_submit_ms': round(avg_overhead_per_submit, 2),
                'average_overhead_per_process_ms': round(avg_overhead_per_process, 2),
                'permission_denial_rate': round(permission_denial_rate, 4),
                'agent_not_found_rate': round(agent_not_found_rate, 4),
                'error_rate': round(error_rate, 4),
                'priority_sort_rate': round(priority_sort_rate, 4),
            },
            'summary': {
                'total_submits': submit_count,
                'total_processes': process_count,
                'total_overhead_ms': round(metrics['total_overhead_ms'], 2),
                'total_permission_denials': metrics['permission_denials'],
                'total_agent_not_found': metrics['agent_not_found_count'],
                'total_errors': metrics['errors_caught'],
                'total_priority_sorts': metrics['priority_sorts'],
                'total_status_queries': metrics['completed_requests_queries'],
            }
        }

    def reset_instrumentation(self) -> None:
        """
        Reset all instrumentation metrics to initial state.
        
        Useful for testing or starting a new measurement period.
        """
        self.instrumentation_metrics = {
            'submit_count': 0,
            'process_count': 0,
            'total_overhead_ms': 0.0,
            'permission_denials': 0,
            'agent_not_found_count': 0,
            'priority_sorts': 0,
            'queue_sizes_at_submit': deque(maxlen=1000),
            'queue_sizes_at_process': deque(maxlen=1000),
            'errors_caught': 0,
            'completed_requests_queries': 0
        }
        logger.info("RequestRouter instrumentation metrics reset")

# Example agent implementations for testing
class LearningNavigatorAgent(BaseAgent):
    """Agent for educational guidance and learning path navigation"""

    def __init__(self, agent_id: str, tool_loader=None):
        super().__init__(agent_id, "Learning Navigator", PermissionLevel.READ_EXECUTE, tool_loader)

    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="guide_learning_path",
                description="Guide users through starter pack notebooks",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["notebook_loader", "progress_tracker"],
                data_access=["starter_pack/*"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="recommend_content",
                description="Recommend content based on user skill level",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["content_analyzer", "user_profiler"],
                data_access=["starter_pack/*"],
                execution_time_estimate=1.5
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "guide_learning_path":
            return self._guide_learning_path(parameters, user_context)
        elif action == "recommend_content":
            return self._recommend_content(parameters, user_context)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _guide_learning_path(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Guide user through learning path using tools"""
        try:
            # Use tool to load notebook metadata
            notebook_paths = [
                "starter_pack/00_data_dictionary.ipynb",
                "starter_pack/01_intro_to_data.ipynb",
                "starter_pack/02_build_simple_rankings.ipynb",
                "starter_pack/03_metrics_comparison.ipynb",
                "starter_pack/04_team_similarity.ipynb",
                "starter_pack/05_matchup_predictor.ipynb"
            ]

            notebook_metadata = self.execute_tool(
                "load_notebook_metadata",
                {"notebook_paths": notebook_paths, "include_content": False},
                user_context
            )

            # Create learning path based on available notebooks
            available_notebooks = [
                meta['name'] + '.ipynb' for meta in notebook_metadata['metadata'] if meta.get('exists', False)
            ]

            recommended_path = available_notebooks[:3] if available_notebooks else notebook_paths[:3]

            return {
                "recommended_path": recommended_path,
                "current_position": parameters.get("current_notebook", "start"),
                "next_steps": ["Learn about data structure", "Explore basic rankings"],
                "estimated_time": f"{len(recommended_path) * 15} minutes",
                "notebooks_available": len(available_notebooks),
                "path_foundation": notebook_metadata.get('summary', {})
            }

        except Exception as e:
            # Fallback if tool execution fails
            return {
                "recommended_path": [
                    "00_data_dictionary.ipynb",
                    "01_intro_to_data.ipynb",
                    "02_build_simple_rankings.ipynb"
                ],
                "current_position": parameters.get("current_notebook", "start"),
                "next_steps": ["Learn about data structure", "Explore basic rankings"],
                "estimated_time": "45 minutes",
                "fallback_used": True
            }

    def _recommend_content(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend content based on user context using tools"""
        skill_level = user_context.get("skill_level", "beginner")

        try:
            # Determine notebook paths based on skill level
            if skill_level == "beginner":
                notebook_paths = [
                    "starter_pack/01_intro_to_data.ipynb",
                    "starter_pack/02_build_simple_rankings.ipynb",
                    "starter_pack/03_metrics_comparison.ipynb"
                ]
            elif skill_level == "intermediate":
                notebook_paths = [
                    "starter_pack/05_matchup_predictor.ipynb",
                    "starter_pack/09_opponent_adjustments.ipynb",
                    "model_pack/01_linear_regression_margin.ipynb"
                ]
            else:  # advanced
                notebook_paths = [
                    "starter_pack/12_efficiency_dashboards.ipynb",
                    "model_pack/06_shap_interpretability.ipynb",
                    "model_pack/07_stacked_ensemble.ipynb"
                ]

            # Use tool to get notebook information
            notebook_metadata = self.execute_tool(
                "load_notebook_metadata",
                {"notebook_paths": notebook_paths, "include_content": False},
                user_context
            )

            # Create recommendations based on available notebooks
            recommendations = []
            for meta in notebook_metadata['metadata']:
                if meta.get('exists', False):
                    recommendations.append({
                        "notebook": meta['path'],
                        "reason": self._get_recommendation_reason(meta['name'], skill_level),
                        "size_kb": round(meta.get('size_bytes', 0) / 1024, 1),
                        "available": True
                    })

            return {
                "recommendations": recommendations,
                "skill_level_assessed": skill_level,
                "personalization_factors": ["previous_notebooks", "time_available", "interests"],
                "notebooks_analyzed": len(notebook_paths),
                "available_recommendations": len(recommendations)
            }

        except Exception as e:
            # Fallback recommendations
            fallback_recommendations = {
                "beginner": [
                    {"notebook": "starter_pack/01_intro_to_data.ipynb", "reason": "Perfect starting point"},
                    {"notebook": "starter_pack/02_build_simple_rankings.ipynb", "reason": "Hands-on learning"}
                ],
                "intermediate": [
                    {"notebook": "starter_pack/05_matchup_predictor.ipynb", "reason": "Apply your knowledge"},
                    {"notebook": "starter_pack/09_opponent_adjustments.ipynb", "reason": "Advanced concepts"}
                ],
                "advanced": [
                    {"notebook": "starter_pack/12_efficiency_dashboards.ipynb", "reason": "Complex analysis"},
                    {"notebook": "model_pack/06_shap_interpretability.ipynb", "reason": "Model explainability"}
                ]
            }

            return {
                "recommendations": fallback_recommendations.get(skill_level, fallback_recommendations["beginner"]),
                "skill_level_assessed": skill_level,
                "personalization_factors": ["previous_notebooks", "time_available", "interests"],
                "fallback_used": True
            }

    def _get_recommendation_reason(self, notebook_name: str, skill_level: str) -> str:
        """Get recommendation reason based on notebook and skill level"""
        reasons = {
            "00_data_dictionary": "Essential reference for all data analysis",
            "01_intro_to_data": "Perfect introduction to the dataset structure",
            "02_build_simple_rankings": "Hands-on experience with data manipulation",
            "03_metrics_comparison": "Visual analysis and comparison skills",
            "04_team_similarity": "Learn clustering and similarity analysis",
            "05_matchup_predictor": "Apply predictive modeling techniques",
            "06_custom_rankings": "Custom analysis and ranking methods",
            "07_drive_efficiency": "Advanced drive-level analysis",
            "08_offense_vs_defense_comparison": "Comparative analysis techniques",
            "09_opponent_adjustments": "Advanced statistical adjustments",
            "10_srs_adjusted_metrics": "Sophisticated rating systems",
            "11_metric_distribution_explorer": "Statistical distribution analysis",
            "12_efficiency_dashboards": "Create professional dashboards",
            "01_linear_regression_margin": "Foundation machine learning concepts",
            "06_shap_interpretability": "Model explainability and interpretation",
            "07_stacked_ensemble": "Advanced ensemble techniques"
        }

        return reasons.get(notebook_name, f"Recommended for {skill_level} level learning")

# Example usage
if __name__ == "__main__":
    # Initialize agent framework
    factory = AgentFactory()
    router = RequestRouter(factory)

    # Register agent classes
    factory.register_agent_class(LearningNavigatorAgent, "learning_navigator")

    # Create an agent
    learning_agent = factory.create_agent("learning_navigator", "nav_001")

    # Create a test request
    test_request = AgentRequest(
        request_id="req_001",
        agent_type="learning_navigator",
        action="guide_learning_path",
        parameters={"current_notebook": "start"},
        user_context={"role": "analyst", "skill_level": "beginner"},
        timestamp=time.time(),
        priority=2
    )

    # Submit and process request
    request_id = router.submit_request(test_request, PermissionLevel.READ_EXECUTE)
    router.process_requests(PermissionLevel.READ_EXECUTE)

    # Get results
    status = router.get_request_status(request_id)
    print("Request Status:", json.dumps(status, indent=2))

    # Get agent status
    print("Agent Status:", json.dumps(learning_agent.get_status(), indent=2))