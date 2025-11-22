#!/usr/bin/env python3
"""
Analytics Orchestrator - Main Coordination System for Script Ohio 2.0

This is the main orchestrator that coordinates all agents, manages context,
and provides the primary interface for the intelligent analytics platform.

Author: Claude Code Assistant
Created: 2025-11-07
Version: 1.0
"""

import json
import os
import sys
import time
import logging
import uuid
from collections import deque
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agents.core.agent_framework import (
    AgentFactory,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    PermissionLevel,
    RequestRouter,
)
from src.utils.cache_manager import get_cache_manager
try:
    from cfbd_client import CFBDDataProvider
except ImportError:
    CFBDDataProvider = None

try:
    from agents.system.cfbd_subscription_manager import CFBDSubscriptionManager
except ImportError:
    CFBDSubscriptionManager = None

# Import Week 13 specialized agents
try:
    from agents.week13_consolidation_agent import Week13ConsolidationAgent
    from agents.legacy_creation_agent import LegacyCreationAgent
except ImportError:
    Week13ConsolidationAgent = None
    LegacyCreationAgent = None

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
    context_hints: Dict[str, Any]
    request_id: str = None
    priority: int = 1
    timestamp: float = None

    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = time.time()

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

class AnalyticsOrchestrator:
    """
    Main orchestrator for the Script Ohio 2.0 analytics platform.

    This class coordinates all agents, manages context, and provides the
    primary interface for intelligent college football analytics.
    """

    def __init__(self, base_path: str = None):
        """Initialize the analytics orchestrator"""
        self.base_path = base_path or os.getcwd()
        self.agent_factory = AgentFactory(base_path)
        self.request_router = RequestRouter(self.agent_factory)
        self.cfbd_telemetry_events = deque(maxlen=200)
        self.monitoring_events = deque(maxlen=200)
        self.cfbd_provider = self._initialize_cfbd_provider()

        # Initialize subscription manager (polling or websocket)
        if CFBDSubscriptionManager:
            try:
                self.subscription_manager = CFBDSubscriptionManager(
                    telemetry_hook=self._record_cfbd_event,
                    use_websockets=True
                )
                self.subscription_manager.start_scoreboard_feed()
            except Exception as e:
                logger.warning(f"Failed to start subscription manager: {e}")
                self.subscription_manager = None
        else:
            self.subscription_manager = None

        # Load available agents
        self._load_agents()

        # Session management (simplified - no state persistence)
        self.active_sessions = {}
        self.session_history = []

        # Performance tracking
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'cache_hit_rate': 0.0
        }
        self.cache_manager = get_cache_manager(max_size_mb=50, max_entries=2048)
        self.agent_io_contracts = self._build_agent_io_contracts()
        self.qa_agent_id: Optional[str] = None
        self.performance_agent_id: Optional[str] = None
        if "default_quality_assurance" in self.agent_factory.agents:
            self.qa_agent_id = "default_quality_assurance"
        if "default_performance_monitor" in self.agent_factory.agents:
            self.performance_agent_id = "default_performance_monitor"

        logger.info("Analytics Orchestrator initialized (simplified)")

    def _initialize_cfbd_provider(self) -> Optional["CFBDDataProvider"]:
        """Instantiate CFBD provider only when dependencies and API key are available."""
        if not CFBDDataProvider:
            logger.warning("CFBDDataProvider not available - CFBD integration will be limited")
            return None

        api_key = os.getenv("CFBD_API_KEY")
        if not api_key:
            logger.warning("CFBD_API_KEY not set - skipping CFBD provider initialization")
            return None

        try:
            return CFBDDataProvider(telemetry_hook=self._record_cfbd_event)
        except Exception as exc:  # pragma: no cover - defensive guard for env issues
            logger.warning("Unable to initialize CFBDDataProvider: %s", exc)
            return None

    def _load_agents(self):
        """Load and register all available agents"""
        try:
            # Import and register agent classes
            # Core agents for happy path (keep these)
            from agents.model_execution_engine import ModelExecutionEngine
            from agents.insight_generator_agent import InsightGeneratorAgent
            
            # Register core agents
            self.agent_factory.register_agent_class(ModelExecutionEngine, "model_engine")
            self.agent_factory.register_agent_class(InsightGeneratorAgent, "insight_generator")
            
            # Create default agent instances for core agents
            self.agent_factory.create_agent("model_engine", "default_model_engine")
            # Create insight generator with CFBD if available
            if self.cfbd_provider:
                self.agent_factory.create_agent(
                    "insight_generator",
                    "default_insight_generator",
                    cfbd_data_provider=self.cfbd_provider,
                    live_feed_provider=self.subscription_manager,
                    telemetry_hook=self._record_cfbd_event,
                )
            else:
                self.agent_factory.create_agent("insight_generator", "default_insight_generator")
            
            # DISABLED: Unused agents for local-only pipeline
            # These are commented out to reduce surface area and maintenance overhead
            # Uncomment if needed for specific use cases
            #
            # from agents.learning_navigator_agent import LearningNavigatorAgent
            # from agents.conversational_ai_agent import ConversationalAIAgent
            # from agents.performance_monitor_agent import PerformanceMonitorAgent
            # self.agent_factory.register_agent_class(LearningNavigatorAgent, "learning_navigator")
            # self.agent_factory.register_agent_class(ConversationalAIAgent, "conversational_ai")
            # self.agent_factory.register_agent_class(PerformanceMonitorAgent, "performance_monitor")
            # self.agent_factory.create_agent("learning_navigator", "default_learning_nav")
            # self.agent_factory.create_agent("conversational_ai", "default_conversational_ai")
            # self.agent_factory.create_agent("performance_monitor", "default_performance_monitor")

            # DISABLED: Prompt Library Generator (not used in happy path)
            # Uncomment if needed for specific use cases
            # try:
            #     from agents.prompt_library_agent import PromptLibraryAgent
            #     self.agent_factory.register_agent_class(PromptLibraryAgent, "prompt_library_generator")
            #     self.agent_factory.create_agent("prompt_library_generator", "default_prompt_library_generator")
            #     logger.info("Loaded Prompt Library Generator agent")
            # except ImportError as e:
            #     logger.warning(f"Could not load Prompt Library Generator agent: {e}")

            # Import and register new consolidated agents
            try:
                from agents.cfbd_integration_agent import CFBDIntegrationAgent
                from agents.quality_assurance_agent import QualityAssuranceAgent

                self.agent_factory.register_agent_class(CFBDIntegrationAgent, "cfbd_integration")
                self.agent_factory.register_agent_class(QualityAssuranceAgent, "quality_assurance")

                try:
                    cfbd_kwargs = {}
                    if self.cfbd_provider:
                        cfbd_kwargs = {
                            "cfbd_data_provider": self.cfbd_provider,
                            "live_feed_provider": self.subscription_manager,
                        }
                    self.agent_factory.create_agent(
                        "cfbd_integration",
                        "default_cfbd_integration",
                        **cfbd_kwargs,
                    )
                    self.agent_factory.create_agent(
                        "quality_assurance",
                        "default_quality_assurance",
                        telemetry_events=self.cfbd_telemetry_events,
                        cfbd_data_provider=self.cfbd_provider,
                    )
                    logger.info("Loaded consolidated agents: CFBD Integration, Quality Assurance")
                except TypeError as exc:
                    logger.warning("Skipping consolidated agent instantiation: %s", exc)

            except ImportError as e:
                logger.warning(f"Could not load consolidated agents: {e}")

            # DISABLED: Weekly/week12/week13 specialized agents (not used in happy path)
            # These agents are used by WeeklyAnalysisOrchestrator directly, not via this orchestrator
            # Uncomment if you need to access them through the main orchestrator
            #
            # Weekly analysis agents are still available via WeeklyAnalysisOrchestrator
            # which is used by scripts/run_weekly_analysis.py
            #
            # try:
            #     from agents.weekly_prediction_generation_agent import WeeklyPredictionGenerationAgent
            #     from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
            #     from agents.weekly_model_validation_agent import WeeklyModelValidationAgent
            #     from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator
            #     self.agent_factory.register_agent_class(WeeklyPredictionGenerationAgent, "weekly_prediction_generation")
            #     self.agent_factory.register_agent_class(WeeklyMatchupAnalysisAgent, "weekly_matchup_analysis")
            #     self.agent_factory.register_agent_class(WeeklyModelValidationAgent, "weekly_model_validation")
            #     self.agent_factory.register_agent_class(WeeklyAnalysisOrchestrator, "weekly_analysis_orchestrator")
            #     logger.info("Registered weekly analysis agents")
            # except ImportError as e:
            #     logger.warning(f"Could not load weekly agents: {e}")
            #
            # Week 12 and Week 13 agents are legacy/specialized - disabled for local-only pipeline

            logger.info("Loaded agent classes and created default instances")

        except ImportError as e:
            logger.warning(f"Could not load some agent classes: {e}")

    def process_analytics_request(self, request: AnalyticsRequest) -> AnalyticsResponse:
        """
        Process a high-level analytics request.

        Args:
            request: Analytics request from user

        Returns:
            Analytics response with results and insights
        """
        start_time = time.time()
        request_id = request.request_id

        logger.info(f"Processing analytics request {request_id}: {request.query}")

        try:
            # Simplified: Direct agent execution without context/state management
            # 1. Analyze request and determine required agents
            context = {
                'user_id': request.user_id,
                'role': request.context_hints.get('role', 'analyst'),
                'query': request.query,
                'query_type': request.query_type
            }
            required_agents = self._analyze_request_requirements(request, context)

            # 2. Prepare shared datasets if needed
            self._prepare_shared_datasets(request, context)

            # 3. Create and route agent requests
            agent_responses = self._execute_agent_requests(request_id, required_agents, request, context)

            # 4. Synthesize results into high-level response
            response = self._synthesize_response(request_id, request, agent_responses, context)

            # 5. Update performance metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, success=True)

            # 6. Store in session history (simplified - no state persistence)
            self._store_session_interaction(request, response, context.get('role', 'analyst'), context)

            self._log_health_event(request, agent_responses, execution_time)

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

    def _record_cfbd_event(self, event: Dict[str, Any]) -> None:
        """Capture telemetry emitted by CFBD clients."""
        self.cfbd_telemetry_events.append(event)

    def get_live_scoreboard_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Expose the most recent subscription events to agents/tests."""
        if self.subscription_manager:
            return self.subscription_manager.latest_events(limit=limit)
        return []

    def _build_agent_io_contracts(self) -> Dict[str, Dict[str, List[str]]]:
        """Document high-level input/output expectations for core agents."""
        return {
            'learning_navigator': {
                'inputs': ['skill_level', 'current_notebook', 'focus_area'],
                'outputs': ['learning_path', 'recommendations', 'next_steps']
            },
            'model_engine': {
                'inputs': ['home_team', 'away_team', 'model_type', 'feature_frame'],
                'outputs': ['predictions', 'model_performance', 'confidence_interval']
            },
            'insight_generator': {
                'inputs': ['analysis_type', 'focus_areas', 'datasets', 'shared_context'],
                'outputs': ['insights', 'visualizations', 'statistical_results']
            }
        }


    def _prepare_shared_datasets(self, request: AnalyticsRequest, context: Dict[str, Any]) -> None:
        """Fetch and cache shared datasets that multiple agents can reuse."""
        shared_context = context.setdefault('shared_context', {})
        dataset_targets = []

        teams = request.parameters.get('teams', [])
        if isinstance(teams, list):
            dataset_targets.extend(teams)
        team = request.parameters.get('team')
        if isinstance(team, str):
            dataset_targets.append(team)

        season = request.parameters.get('season')
        week = request.parameters.get('week')
        if not dataset_targets:
            return

        snapshots = {}
        for team_name in dataset_targets:
            snapshot = self._fetch_cfbd_dataset(team_name, season, week)
            if snapshot:
                snapshots[team_name] = snapshot

        if snapshots:
            shared_context.setdefault('cfbd_snapshots', {}).update(snapshots)

    def _get_cfbd_agent(self):
        """Return the default CFBD integration agent if available."""
        return self.agent_factory.agents.get("default_cfbd_integration")

    def _fetch_cfbd_dataset(self, team: str, season: Optional[int], week: Optional[int]) -> Optional[Dict[str, Any]]:
        """Retrieve CFBD data for a team with caching."""
        cfbd_agent = self._get_cfbd_agent()
        if not cfbd_agent:
            return None

        cache_key = f"cfbd_shared:{team}:{season}:{week or 'latest'}"
        cached = self.cache_manager.get(cache_key) if self.cache_manager else None
        if cached:
            return cached

        try:
            snapshot_response = cfbd_agent._team_snapshot({
                "team": team,
                "season": season,
                "week": week
            })
            snapshot = snapshot_response.get('snapshot')
            if snapshot and self.cache_manager:
                self.cache_manager.put(cache_key, snapshot, ttl_seconds=300, tags=['cfbd', 'shared'])
            return snapshot
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Unable to fetch CFBD dataset for %s: %s", team, exc)
            return None

    def _extract_week_from_query(self, query: str) -> Optional[int]:
        """Extract week number from query string"""
        import re
        # Look for patterns like "week 12", "week12", "week 13", etc.
        week_match = re.search(r'week\s*(\d+)', query.lower())
        if week_match:
            try:
                return int(week_match.group(1))
            except ValueError:
                pass
        return None


    def _log_health_event(self, request: AnalyticsRequest, agent_responses: List[AgentResponse],
                          execution_time: float) -> None:
        """Push a monitoring event for QA and performance agents."""
        event = {
            "request_id": request.request_id,
            "user_id": request.user_id,
            "timestamp": time.time(),
            "agents_used": [resp.agent_type for resp in agent_responses],
            "success_count": len([resp for resp in agent_responses if resp.status == AgentStatus.COMPLETED]),
            "failure_count": len([resp for resp in agent_responses if resp.status == AgentStatus.ERROR]),
            "execution_time": execution_time,
        }
        self.monitoring_events.append(event)

        if self.qa_agent_id:
            qa_agent = self.agent_factory.agents.get(self.qa_agent_id)
            if qa_agent and hasattr(qa_agent, "telemetry_events"):
                qa_agent.telemetry_events.append(event)

        if self.performance_agent_id:
            performance_agent = self.agent_factory.agents.get(self.performance_agent_id)
            if performance_agent and hasattr(performance_agent, "metrics_history"):
                performance_agent.metrics_history['workflow'].append(event)

    def _analyze_request_requirements(self, request: AnalyticsRequest, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze request to determine which agents are needed"""
        requirements = []

        query_lower = request.query.lower()
        user_role = context.get('role', 'analyst')

        # Week 13 specialized requests (highest priority)
        if 'week13' in query_lower or request.parameters.get('week') == 13:
            if 'consolidate' in query_lower or 'catalog' in query_lower or 'organize' in query_lower:
                requirements.append({
                    'agent_type': 'week13_consolidation',
                    'action': 'full_consolidation',
                    'parameters': {},
                    'priority': 1
                })
            elif 'legacy' in query_lower or 'template' in query_lower or 'future' in query_lower:
                requirements.append({
                    'agent_type': 'legacy_creation',
                    'action': 'full_legacy_creation',
                    'parameters': {},
                    'priority': 1
                })
            else:
                # Default Week 13 consolidation for general Week 13 queries
                requirements.append({
                    'agent_type': 'week13_consolidation',
                    'action': 'asset_discovery',
                    'parameters': {},
                    'priority': 1
                })

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

        # Bridge to model pack requests
        if any(keyword in query_lower for keyword in ['bridge', 'model pack', 'ml features', '86 features', 'weekly training']):
            requirements.append({
                'agent_type': 'learning_navigator',
                'action': 'bridge_to_model_pack',
                'parameters': {
                    'current_notebook': request.parameters.get('current_notebook'),
                    'query': request.query,
                    'skill_level': request.context_hints.get('skill_level', 'beginner')
                }
            })

        # Data exploration requests
        if any(keyword in query_lower for keyword in ['data', 'dataset', 'explore', 'show me', 'tell me about']):
            if user_role == 'analyst':
                requirements.append({
                    'agent_type': 'learning_navigator',
                    'action': 'recommend_content',
                    'parameters': {
                        'focus_area': 'data_exploration',
                        'query': request.query
                    }
                })

        # Model/prediction requests
        if any(keyword in query_lower for keyword in ['predict', 'model', 'analyze', 'forecast', 'outcome']):
            if user_role in ['data_scientist', 'production']:
                requirements.append({
                    'agent_type': 'model_engine',
                    'action': 'predict_game_outcome',
                    'parameters': {
                        'query': request.query,
                        'teams': request.parameters.get('teams', []),
                        'model_type': request.parameters.get('model_type', 'ridge_model_2025')
                    }
                })

        # Conversational AI routing for natural language interactions
        conversational_keywords = ['help', 'explain', 'tell me', 'what is', 'how do', 'show me', 'can you', 'would you', 'i want to', 'looking for']
        if any(keyword in query_lower for keyword in conversational_keywords) or len(query_lower.split()) > 10:
            requirements.append({
                'agent_type': 'conversational_ai',
                'action': 'natural_language_processing',
                'parameters': {
                    'query': request.query,
                    'user_id': request.user_id,
                    'conversation_id': f"conv_{request.request_id}",
                    'entities': request.parameters.get('entities', {}),
                    'intent_context': request.context_hints
                }
            })

        # Analysis requests - Enhanced with role-based routing and analysis keywords
        analysis_keywords = ['analyze', 'analysis', 'compare', 'ranking', 'statistics', 'insights', 'performance', 'metrics', 'data', 'advanced']
        if any(keyword in query_lower for keyword in analysis_keywords):
            # Enhanced user role detection for analysis requests
            target_role = request.context_hints.get('role', user_role)
            skill_level = request.context_hints.get('skill_level', 'intermediate')

            # Route to insight generator for most users seeking analysis
            if (target_role in ['data_scientist', 'analyst', 'production'] or
                skill_level in ['advanced', 'intermediate', 'expert'] or
                'analysis' in query_lower or
                'insights' in query_lower or
                'advanced' in query_lower):

                requirements.append({
                    'agent_type': 'insight_generator',
                    'action': 'generate_analysis',
                    'parameters': {
                        'analysis_type': request.parameters.get('analysis_type', 'performance'),
                        'focus_areas': request.parameters.get('focus_areas', ['performance', 'descriptive'])
                    }
                })


        # GraphQL requests - Check for GraphQL-specific keywords
        graphql_keywords = ['graphql', 'gql', 'scoreboard via graphql', 'recruiting via graphql', 'graphql api']
        if any(keyword in query_lower for keyword in graphql_keywords):
            season_param = request.parameters.get('season') or request.parameters.get('year')
            week_param = request.parameters.get('week')
            team_param = request.parameters.get('team') or request.parameters.get('school')
            
            # Determine which GraphQL capability to use
            if any(word in query_lower for word in ['scoreboard', 'games', 'game', 'matchup']):
                requirements.append({
                    'agent_type': 'cfbd_integration',
                    'action': 'graphql_scoreboard',
                    'parameters': {
                        'season': season_param,
                        'week': week_param,
                        'team': team_param,
                    }
                })
            elif any(word in query_lower for word in ['recruiting', 'recruit', 'recruits']):
                requirements.append({
                    'agent_type': 'cfbd_integration',
                    'action': 'graphql_recruiting',
                    'parameters': {
                        'year': season_param or request.parameters.get('year'),
                        'season': season_param,
                        'school': team_param or request.parameters.get('school'),
                        'team': team_param,
                        'limit': request.parameters.get('limit', 25),
                    }
                })
            else:
                # Default to scoreboard if GraphQL keyword present but capability unclear
                requirements.append({
                    'agent_type': 'cfbd_integration',
                    'action': 'graphql_scoreboard',
                    'parameters': {
                        'season': season_param,
                        'week': week_param,
                        'team': team_param,
                    }
                })

        # CFBD ingestion requests (REST-based) - Only if GraphQL not specified
        elif any(keyword in query_lower for keyword in ['cfbd', 'ingest', 'next api', 'rest api', 'live data']):
            season_param = request.parameters.get('season')
            week_param = request.parameters.get('week')
            team_param = request.parameters.get('team')

            requirements.append({
                'agent_type': 'insight_generator',
                'action': 'cfbd_real_time_analysis',
                'parameters': {
                    'season': season_param,
                    'week': week_param,
                    'team': team_param,
                    'use_next': 'next' in query_lower or request.parameters.get('use_next', False),
                }
            })

        # Weekly analysis requests - Check for weekly-specific query patterns
        if any(keyword in query_lower for keyword in ['week', 'weekly', 'prediction', 'matchup']):
            # Extract week number if present
            week = self._extract_week_from_query(request.query) or request.parameters.get('week')
            season = request.parameters.get('season', 2025)
            
            if week:
                # Route to weekly analysis orchestrator for comprehensive analysis
                requirements.append({
                    'agent_type': 'weekly_analysis_orchestrator',
                    'agent_id': f'week{week}_orchestrator',
                    'action': 'run_weekly_analysis',
                    'parameters': {
                        'week': week,
                        'season': season
                    },
                    'priority': 1
                })
            elif 'week12' in query_lower or request.parameters.get('week') == 12:
                # Route to Week 12 agents for backward compatibility
                requirements.append({
                    'agent_type': 'week12_prediction_generation',
                    'action': 'generate_predictions',
                    'parameters': {
                        'week': 12,
                        'season': season
                    },
                    'priority': 1
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
                              analytics_request: AnalyticsRequest, context: Dict[str, Any]) -> List[AgentResponse]:
        """Execute requests to required agents"""
        execution_start_time = time.time()
        agent_responses = []
        router_overhead_times = []
        
        # Track orchestrator metrics
        agent_count = len(required_agents)
        agent_types = [req.get('agent_type', 'unknown') for req in required_agents]
        priorities = [req.get('priority', analytics_request.priority) for req in required_agents]
        
        logger.info(f"[ORCHESTRATOR_AUDIT] ROUTER_CALL: request_id={request_id} agent_count={agent_count} agent_types={agent_types} priorities={priorities}")

        user_role = context.get('role', 'analyst')
        # Check context hints for advanced users to grant appropriate permissions
        if (user_role == 'analyst' and
            (analytics_request.context_hints.get('skill_level') == 'advanced' or
             analytics_request.context_hints.get('role') == 'data_scientist')):
            user_role = 'data_scientist'
        user_permissions = self._get_permissions_for_role(user_role)

        shared_context = context.get('shared_context') or {}

        for agent_req in required_agents:
            try:
                # Handle parameterized agent creation for weekly agents
                agent_id = agent_req.get('agent_id', f"default_{agent_req['agent_type']}")
                agent_type = agent_req['agent_type']
                
                # Check if this is a weekly agent that needs parameters
                if agent_type.startswith('weekly_'):
                    # Extract parameters for weekly agents
                    week = agent_req.get('parameters', {}).get('week')
                    season = agent_req.get('parameters', {}).get('season', 2025)
                    
                    if week is not None:
                        # Create weekly agent instance with parameters if it doesn't exist
                        if agent_id not in self.agent_factory.agents:
                            try:
                                self.agent_factory.create_agent(
                                    agent_type,
                                    agent_id,
                                    week=week,
                                    season=season
                                )
                                logger.info(f"Created weekly agent {agent_type} for week {week}, season {season}")
                            except Exception as exc:
                                logger.error(f"Failed to create weekly agent {agent_type}: {exc}")
                                # Create error response
                                error_response = AgentResponse(
                                    request_id=f"{request_id}_{agent_type}",
                                    agent_type=agent_type,
                                    status=AgentStatus.ERROR,
                                    result=None,
                                    error_message=f"Failed to create weekly agent: {str(exc)}",
                                    execution_time=0.0,
                                    metadata={'error': True}
                                )
                                agent_responses.append(error_response)
                                continue
                    else:
                        logger.warning(f"Missing week parameter for weekly agent: {agent_type}")
                        # Create error response
                        error_response = AgentResponse(
                            request_id=f"{request_id}_{agent_type}",
                            agent_type=agent_type,
                            status=AgentStatus.ERROR,
                            result=None,
                            error_message=f"Missing week parameter for weekly agent: {agent_type}",
                            execution_time=0.0,
                            metadata={'error': True}
                        )
                        agent_responses.append(error_response)
                        continue

                step_parameters = dict(agent_req['parameters'])
                if shared_context and agent_req['agent_type'] != 'quality_assurance':
                    step_parameters.setdefault('shared_context', shared_context)

                # Create agent request
                agent_request = AgentRequest(
                    request_id=f"{request_id}_{agent_req['agent_type']}",
                    agent_type=agent_req['agent_type'],
                    action=agent_req['action'],
                    parameters=step_parameters,
                    user_context=context,
                    timestamp=time.time(),
                    priority=agent_req.get('priority', analytics_request.priority)
                )

                # Submit and process request with timing
                router_call_start = time.time()
                logger.info(f"[ORCHESTRATOR_AUDIT] ROUTER_CALL: request_id={agent_request.request_id} action=submit")
                self.request_router.submit_request(agent_request, user_permissions)
                
                logger.info(f"[ORCHESTRATOR_AUDIT] ROUTER_CALL: request_id={agent_request.request_id} action=process")
                self.request_router.process_requests(user_permissions)
                router_overhead_ms = (time.time() - router_call_start) * 1000
                router_overhead_times.append(router_overhead_ms)
                logger.info(f"[ORCHESTRATOR_AUDIT] ROUTER_CALL: request_id={agent_request.request_id} router_overhead_ms={router_overhead_ms:.2f}")

                # Get response
                response = self.request_router.get_request_status(agent_request.request_id)
                if response and response['status'] == 'completed':
                    # Convert dict back to AgentResponse
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
                # Create error response
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

        # Calculate final metrics
        total_time_ms = (time.time() - execution_start_time) * 1000
        successful_agents = len([r for r in agent_responses if r.status == AgentStatus.COMPLETED])
        failed_agents = len([r for r in agent_responses if r.status == AgentStatus.ERROR])
        
        # Calculate router overhead (sum of all router calls)
        total_router_overhead_ms = sum(router_overhead_times) if router_overhead_times else 0.0
        
        logger.info(f"[ORCHESTRATOR_AUDIT] ROUTER_CALL: request_id={request_id} total_time_ms={total_time_ms:.2f} total_router_overhead_ms={total_router_overhead_ms:.2f} successful_agents={successful_agents} failed_agents={failed_agents}")

        return agent_responses

    def _synthesize_response(self, request_id: str, analytics_request: AnalyticsRequest,
                           agent_responses: List[AgentResponse], context: Dict[str, Any]) -> AnalyticsResponse:
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

                # Enhanced insight extraction for all agent types
                if isinstance(response.result, dict):
                    # Learning Navigator insights
                    if 'recommendations' in response.result:
                        for rec in response.result['recommendations']:
                            insights.append(f"Recommendation: {rec.get('reason', 'No reason provided')}")
                    if 'recommended_path' in response.result:
                        insights.append(f"Suggested learning path: {' → '.join(response.result['recommended_path'])}")
                    if 'next_steps' in response.result:
                        insights.extend([f"Next step: {step}" for step in response.result['next_steps']])
                    if 'resources' in response.result:
                        resources = response.result['resources']
                        insights.append(f"Found {len(resources)} learning resources for you")
                        for resource in resources[:3]:  # Add first 3 resources as insights
                            title = resource.get('title', 'Untitled Resource')
                            difficulty = resource.get('difficulty', 'unknown difficulty')
                            insights.append(f"Recommended: {title} ({difficulty})")
                    if 'concepts_explained' in response.result:
                        concepts = response.result['concepts_explained']
                        insights.append(f"Explained {len(concepts)} analytics concepts")

                    # Insight Generator Agent insights
                    if 'insights' in response.result:
                        insight_generator_insights = response.result['insights']
                        if isinstance(insight_generator_insights, list):
                            for insight in insight_generator_insights[:5]:  # Top 5 insights
                                if isinstance(insight, dict):
                                    insight_text = insight.get('insight', str(insight))
                                    if 'confidence' in insight:
                                        insights.append(f"Analysis Insight ({insight['confidence']}% confidence): {insight_text}")
                                    else:
                                        insights.append(f"Analysis Insight: {insight_text}")
                                else:
                                    insights.append(f"Analysis Insight: {insight}")
                        else:
                            insights.append(f"Analysis Insight: {insight_generator_insights}")

                    # Model Execution Engine insights
                    if 'predictions' in response.result:
                        predictions = response.result['predictions']
                        if isinstance(predictions, dict):
                            if 'home_win_probability' in predictions:
                                prob = predictions['home_win_probability']
                                insights.append(f"Home win probability: {prob:.1%}")
                            if 'predicted_margin' in predictions:
                                margin = predictions['predicted_margin']
                                insights.append(f"Predicted margin: {margin:+.1f} points")
                            if 'confidence_interval' in predictions:
                                ci = predictions['confidence_interval']
                                insights.append(f"95% confidence interval: {ci}")
                        else:
                            insights.append(f"Prediction: {predictions}")


                    # Statistical results and metrics
                    if 'statistical_results' in response.result:
                        stats = response.result['statistical_results']
                        if isinstance(stats, dict):
                            for key, value in stats.items():
                                if isinstance(value, (int, float)):
                                    insights.append(f"{key.replace('_', ' ').title()}: {value:.3f}")
                                else:
                                    insights.append(f"{key.replace('_', ' ').title()}: {value}")

                    # Model performance metrics
                    if 'model_performance' in response.result:
                        perf = response.result['model_performance']
                        if isinstance(perf, dict):
                            for metric, value in perf.items():
                                if isinstance(value, (int, float)):
                                    insights.append(f"Model {metric}: {value:.3f}")

                    # General results that might contain insights
                    if 'analysis_results' in response.result:
                        analysis = response.result['analysis_results']
                        insights.append(f"Analysis completed: {len(str(analysis))} characters of results")

                    # Data quality and validation results
                    if 'data_quality' in response.result:
                        quality = response.result['data_quality']
                        if isinstance(quality, dict):
                            completeness = quality.get('completeness', 0)
                            insights.append(f"Data quality: {completeness:.1%} complete")

                    # Any other meaningful content
                    for key, value in response.result.items():
                        if key not in ['recommendations', 'recommended_path', 'next_steps', 'resources',
                                     'concepts_explained', 'insights', 'predictions',
                                     'statistical_results', 'model_performance',
                                     'analysis_results', 'data_quality']:
                            if isinstance(value, str) and len(value) < 200:  # Short text insights
                                insights.append(f"{key.replace('_', ' ').title()}: {value}")
                            elif isinstance(value, list) and len(value) > 0:
                                insights.append(f"Found {len(value)} {key.replace('_', ' ')}")

        # Add insights about any errors
        for response in failed_responses:
            insights.append(f"Note: {response.error_message}")

        # Enhanced visualization extraction for all agent types
        for response in successful_responses:
            if response.result and isinstance(response.result, dict):
                # Learning Navigator visualizations
                if response.agent_type == 'learning_navigator' and 'recommended_path' in response.result:
                    visualizations.append({
                        'type': 'learning_path',
                        'title': 'Recommended Learning Path',
                        'data': response.result['recommended_path'],
                        'source_agent': 'learning_navigator'
                    })

                # Insight Generator visualizations
                if response.agent_type == 'insightgenerator' or response.agent_type == 'insight_generator':
                    if 'visualizations' in response.result:
                        insight_viz = response.result['visualizations']
                        if isinstance(insight_viz, list):
                            for viz in insight_viz:
                                if isinstance(viz, dict):
                                    viz['source_agent'] = 'insight_generator'
                                    visualizations.append(viz)

                    # Create automatic visualizations for analysis results
                    if 'analysis_results' in response.result:
                        visualizations.append({
                            'type': 'analysis_summary',
                            'title': 'Analysis Results Summary',
                            'data': response.result['analysis_results'],
                            'source_agent': 'insight_generator'
                        })

                # Model Execution Engine visualizations
                if response.agent_type == 'modelengine' or response.agent_type == 'model_engine':
                    if 'predictions' in response.result:
                        predictions = response.result['predictions']
                        visualizations.append({
                            'type': 'prediction_dashboard',
                            'title': 'Game Predictions Dashboard',
                            'data': predictions,
                            'source_agent': 'model_engine'
                        })

                    if 'model_performance' in response.result:
                        visualizations.append({
                            'type': 'model_performance',
                            'title': 'Model Performance Metrics',
                            'data': response.result['model_performance'],
                            'source_agent': 'model_engine'
                        })


        # Legacy fallback for learning path visualization
        if any('notebook' in str(result).lower() for result in successful_responses):
            learning_path = results.get('learning_navigator', {}).get('recommended_path', [])
            if learning_path and not any(viz.get('type') == 'learning_path' for viz in visualizations):
                visualizations.append({
                    'type': 'learning_path',
                    'title': 'Recommended Learning Path',
                    'data': learning_path,
                    'source_agent': 'learning_navigator'
                })

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
                'user_role': context.get('role'),
                'agents_used': [r.agent_type for r in successful_responses],
                'agents_failed': [r.agent_type for r in failed_responses]
            }
        )

    def _get_permissions_for_role(self, user_role: Union[str, None]) -> PermissionLevel:
        """Map user role (string) to permission level."""
        if isinstance(user_role, str):
            role_key = user_role.lower()
        else:
            role_key = 'analyst'

        permission_map = {
            'analyst': PermissionLevel.READ_EXECUTE_WRITE,
            'data_scientist': PermissionLevel.READ_EXECUTE_WRITE,
            'production': PermissionLevel.READ_EXECUTE
        }
        return permission_map.get(role_key, PermissionLevel.READ_ONLY)

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

        # Cache hit rate (simplified - no context manager)
        self.performance_metrics['cache_hit_rate'] = 0.0

    def _store_session_interaction(self, request: AnalyticsRequest, response: AnalyticsResponse,
                                 user_role: str, context: Dict[str, Any]):
        """Store interaction in session history"""
        interaction = {
            'timestamp': request.timestamp,
            'request_id': response.request_id,
            'user_id': request.user_id,
            'query': request.query,
            'query_type': request.query_type,
            'user_role': user_role,
            'status': response.status,
            'execution_time': response.execution_time,
            'insights_count': len(response.insights),
            'visualizations_count': len(response.visualizations)
        }

        self.session_history.append(interaction)

        # Keep only last 100 interactions
        if len(self.session_history) > 100:
            self.session_history = self.session_history[-100:]

    def get_session_summary(self, user_id: str = None) -> Dict[str, Any]:
        """Get summary of session interactions"""
        history = self.session_history
        if user_id:
            history = [h for h in history if h.get('user_id') == user_id]

        if not history:
            return {'message': 'No interactions recorded'}

        # Calculate summary statistics
        total_interactions = len(history)
        successful_interactions = len([h for h in history if h['status'] == 'success'])
        avg_execution_time = sum(h['execution_time'] for h in history) / total_interactions

        # Most common query types
        query_types = [h['query_type'] for h in history]
        most_common_queries = list(set(query_types))

        # User role distribution
        user_roles = [h['user_role'] for h in history]
        role_distribution = {role: user_roles.count(role) for role in set(user_roles)}

        return {
            'total_interactions': total_interactions,
            'success_rate': (successful_interactions / total_interactions) * 100,
            'average_execution_time': round(avg_execution_time, 3),
            'most_common_query_types': most_common_queries,
            'user_role_distribution': role_distribution,
            'recent_interactions': history[-5:],
            'performance_metrics': self.performance_metrics
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        router_queue_status = self.request_router.get_queue_status()
        router_instrumentation = self.request_router.get_instrumentation_report()
        
        return {
            'orchestrator': {
                'status': 'active',
                'uptime': time.time(),  # Would calculate actual uptime
                'performance_metrics': self.performance_metrics
            },
            'agent_factory': {
                'registered_agents': list(self.agent_factory.agent_registry.keys()),
                'active_agents': len(self.agent_factory.agents),
                'agent_list': self.agent_factory.list_agents()
            },
            'request_router': {
                'queue_status': router_queue_status,
                'instrumentation': router_instrumentation
            },
            'sessions': {
                'total_interactions': len(self.session_history),
                'active_sessions': len(self.active_sessions)
            }
        }

    def start_session(self, user_id: str, user_context: Dict[str, Any] = None) -> str:
        """Start a new analytics session"""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'start_time': time.time(),
            'user_context': user_context or {},
            'interactions': []
        }
        logger.info(f"Started session {session_id} for user {user_id}")
        return session_id

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End an analytics session and return summary"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}

        session = self.active_sessions[session_id]
        session['end_time'] = time.time()
        session['duration'] = session['end_time'] - session['start_time']

        # Move to history and remove from active
        self.session_history.append(session)
        del self.active_sessions[session_id]

        logger.info(f"Ended session {session_id} after {session['duration']:.2f} seconds")
        return session

# Example usage
if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = AnalyticsOrchestrator()

    # Create a test request
    test_request = AnalyticsRequest(
        user_id="user_001",
        query="I want to learn about college football data analytics",
        query_type="learning",
        parameters={},
        context_hints={
            'skill_level': 'beginner',
            'interests': ['data_analysis', 'sports']
        },
        priority=2
    )

    # Process the request
    response = orchestrator.process_analytics_request(test_request)

    print("=== Analytics Response ===")
    print(f"Status: {response.status}")
    print(f"Insights: {response.insights}")
    print(f"Visualizations: {response.visualizations}")
    print(f"Execution Time: {response.execution_time:.3f}s")

    # Get system status
    print("\n=== System Status ===")
    status = orchestrator.get_system_status()
    print(json.dumps(status, indent=2, default=str))
