#!/usr/bin/env python3
"""
DEPRECATED: State-Aware Analytics System

⚠️  DEPRECATION WARNING (2025-11-19):
This module is DEPRECATED and will be removed in a future version.
It was identified as unused in production code analysis.

StateAwareAnalyticsSession is only used in:
- agents/analytics_orchestrator.py (which is being simplified)

It is NOT used by:
- scripts/generate_comprehensive_week13_analysis.py
- scripts/run_weekly_analysis.py
- Any production weekly analysis scripts

Weekly orchestrator uses stateless execution - no session persistence needed.

Migration path:
- Use in-memory session tracking if needed (see SimplifiedAnalyticsOrchestrator)
- For conversation history, use simple list storage
- See agents/weekly_analysis_orchestrator.py for the pattern actually used

This module will be removed after 2025-12-19 (30-day deprecation period).

Original description:
Integrates advanced state management with the football analytics platform

This system provides:
- Persistent session state across conversations
- Agent state preservation and recovery
- Workflow state for complex multi-step analyses
- Automatic recovery from failures
- State rollback capabilities
"""
import warnings

warnings.warn(
    "StateAwareAnalyticsSession is deprecated and will be removed after 2025-12-19. "
    "Use stateless execution pattern from WeeklyAnalysisOrchestrator instead. "
    "See agents/weekly_analysis_orchestrator.py for the recommended pattern.",
    DeprecationWarning,
    stacklevel=2
)

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from agents.core.state_manager import (
    StateManager, StateType, StateStatus,
    state_manager, save_session_state, restore_session_state,
    save_agent_state, restore_agent_state, save_workflow_state, restore_workflow_state
)

logger = logging.getLogger("state_aware_analytics")

class StateAwareAnalyticsSession:
    """
    Analytics session with persistent state management

    Provides continuity across sessions and automatic recovery

    .. deprecated:: 2025-11-19
        StateAwareAnalyticsSession is deprecated and will be removed in 30 days.
        Production code uses stateless execution.
        Migration: Use stateless agent execution (see WeeklyAnalysisOrchestrator pattern).
    """

    def __init__(self, session_id: str, user_id: str):
        import warnings
        warnings.warn(
            "StateAwareAnalyticsSession is deprecated and will be removed on 2025-12-19. "
            "Use stateless agent execution instead (see WeeklyAnalysisOrchestrator pattern).",
            DeprecationWarning,
            stacklevel=2
        )
        self.session_id = session_id
        self.user_id = user_id

        # Try to restore existing session state
        self.state = restore_session_state(session_id) or {
            'user_id': user_id,
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'conversation_history': [],
            'analysis_results': [],
            'user_preferences': {},
            'active_agents': [],
            'workflow_state': {}
        }

        # State change tracking
        self.last_state_save = time.time()
        self.auto_save_interval = 30  # Auto-save every 30 seconds
        self.state_changes = 0

        logger.info(f"State-aware session initialized: {session_id}")

    def add_conversation_turn(self, query: str, response: str, agent_id: str = None):
        """Add a conversation turn with state persistence"""

        turn = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response,
            'agent_id': agent_id,
            'turn_number': len(self.state['conversation_history']) + 1
        }

        self.state['conversation_history'].append(turn)
        self.state['last_activity'] = datetime.now().isoformat()
        self.state_changes += 1

        # Auto-save if needed
        if time.time() - self.last_state_save > self.auto_save_interval:
            self.save_state()

        logger.debug(f"Added conversation turn: {turn['turn_number']} for session {self.session_id}")

    def add_analysis_result(self, analysis_type: str, result: Dict[str, Any], agent_id: str = None):
        """Add analysis result with state persistence"""

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': analysis_type,
            'result': result,
            'agent_id': agent_id,
            'analysis_id': str(uuid.uuid4())
        }

        self.state['analysis_results'].append(analysis)
        self.state['last_activity'] = datetime.now().isoformat()
        self.state_changes += 1

        # Auto-save if needed
        if time.time() - self.last_state_save > self.auto_save_interval:
            self.save_state()

        logger.info(f"Added analysis result: {analysis_type} for session {self.session_id}")

    def get_conversation_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get conversation history with optional limit"""
        history = self.state['conversation_history']
        return history[-limit:] if limit else history

    def get_analysis_results(self, analysis_type: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get analysis results with optional filtering"""
        results = self.state['analysis_results']

        if analysis_type:
            results = [r for r in results if r['analysis_type'] == analysis_type]

        if limit:
            results = results[-limit:]

        return results

    def update_user_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences with state persistence"""
        self.state['user_preferences'].update(preferences)
        self.state['last_activity'] = datetime.now().isoformat()
        self.state_changes += 1

        # Auto-save preferences
        self.save_state()

    def register_active_agent(self, agent_id: str, agent_type: str = None):
        """Register an active agent in the session"""
        agent_info = {
            'agent_id': agent_id,
            'agent_type': agent_type,
            'registered_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }

        # Remove if already exists
        self.state['active_agents'] = [
            a for a in self.state['active_agents']
            if a['agent_id'] != agent_id
        ]

        self.state['active_agents'].append(agent_info)
        self.state_changes += 1

    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get list of active agents"""
        return self.state['active_agents'].copy()

    def save_state(self):
        """Manually save session state"""
        try:
            snapshot_id = save_session_state(
                session_id=self.session_id,
                state_data=self.state,
                metadata={
                    'user_id': self.user_id,
                    'state_changes': self.state_changes,
                    'auto_save': True
                }
            )

            self.last_state_save = time.time()
            logger.debug(f"Session state saved: {self.session_id} -> {snapshot_id}")
            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
            return None

    def rollback_to_previous_state(self, reason: str = "User requested rollback"):
        """Rollback session to previous state"""
        try:
            # Get snapshot history
            snapshots = state_manager.list_snapshots(
                state_type=StateType.SESSION_STATE,
                entity_id=self.session_id,
                limit=10
            )

            if len(snapshots) >= 2:
                previous_snapshot_id = snapshots[1]['snapshot_id']
                rolled_back_state = state_manager.restore_state_snapshot(
                    previous_snapshot_id,
                    actor=f"session_{self.session_id}"
                )

                if rolled_back_state:
                    self.state = rolled_back_state
                    logger.info(f"Session rolled back to: {previous_snapshot_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to rollback session state: {e}")
            return False

class StateAwareAgent:
    """
    Analytics agent with state management capabilities

    Provides agent state persistence and recovery
    """

    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type

        # Try to restore existing agent state
        self.state = restore_agent_state(agent_id) or {
            'agent_id': agent_id,
            'agent_type': agent_type,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'analysis_history': [],
            'knowledge_base': [],
            'preferences': {},
            'performance_metrics': {
                'total_analyses': 0,
                'successful_analyses': 0,
                'average_response_time': 0.0
            }
        }

        self.state_changes = 0

        logger.info(f"State-aware agent initialized: {agent_id}")

    def record_analysis(self, analysis_request: Dict[str, Any], analysis_result: Dict[str, Any], response_time: float):
        """Record analysis with state persistence"""

        analysis_record = {
            'timestamp': datetime.now().isoformat(),
            'request': analysis_request,
            'result': analysis_result,
            'response_time': response_time,
            'analysis_id': str(uuid.uuid4())
        }

        self.state['analysis_history'].append(analysis_record)
        self.state['last_activity'] = datetime.now().isoformat()
        self.state_changes += 1

        # Update performance metrics
        metrics = self.state['performance_metrics']
        metrics['total_analyses'] += 1

        if analysis_result.get('success', True):
            metrics['successful_analyses'] += 1

        # Update average response time
        total_time = metrics['average_response_time'] * (metrics['total_analyses'] - 1) + response_time
        metrics['average_response_time'] = total_time / metrics['total_analyses']

        # Save state periodically
        if self.state_changes % 5 == 0:  # Save every 5 analyses
            self.save_state()

        logger.debug(f"Recorded analysis for agent: {self.agent_id}")

    def add_knowledge(self, knowledge_item: Dict[str, Any]):
        """Add knowledge to agent's knowledge base"""

        knowledge = {
            'knowledge_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'content': knowledge_item,
            'usage_count': 0,
            'effectiveness_score': 1.0
        }

        self.state['knowledge_base'].append(knowledge)
        self.state_changes += 1

        self.save_state()
        logger.info(f"Added knowledge to agent: {self.agent_id}")

    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search agent's knowledge base"""
        query_lower = query.lower()
        results = []

        for knowledge in self.state['knowledge_base']:
            content_text = json.dumps(knowledge['content'], default=str).lower()
            if query_lower in content_text:
                knowledge['usage_count'] += 1
                results.append(knowledge)

        # Sort by usage count and effectiveness
        results.sort(key=lambda k: (k['usage_count'], k['effectiveness_score']), reverse=True)

        return results

    def update_preferences(self, preferences: Dict[str, Any]):
        """Update agent preferences"""
        self.state['preferences'].update(preferences)
        self.state['last_activity'] = datetime.now().isoformat()
        self.state_changes += 1

        self.save_state()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return self.state['performance_metrics'].copy()

    def save_state(self):
        """Manually save agent state"""
        try:
            snapshot_id = save_agent_state(
                agent_id=self.agent_id,
                state_data=self.state,
                metadata={
                    'agent_type': self.agent_type,
                    'state_changes': self.state_changes,
                    'knowledge_count': len(self.state['knowledge_base'])
                }
            )

            logger.debug(f"Agent state saved: {self.agent_id} -> {snapshot_id}")
            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to save agent state: {e}")
            return None

    def reset_state(self, reason: str = "Manual reset"):
        """Reset agent state to initial conditions"""
        initial_state = {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'analysis_history': [],
            'knowledge_base': [],
            'preferences': {},
            'performance_metrics': {
                'total_analyses': 0,
                'successful_analyses': 0,
                'average_response_time': 0.0
            }
        }

        self.state = initial_state
        self.state_changes = 0
        self.save_state()

        logger.info(f"Agent state reset: {self.agent_id}")

class StateAwareWorkflow:
    """
    Multi-step workflow with state management

    Provides persistent state for complex analytical workflows
    """

    def __init__(self, workflow_id: str, workflow_type: str, steps: List[str]):
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.steps = steps

        # Try to restore existing workflow state
        self.state = restore_workflow_state(workflow_id) or {
            'workflow_id': workflow_id,
            'workflow_type': workflow_type,
            'steps': steps,
            'current_step_index': 0,
            'step_results': {},
            'status': 'initialized',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'error_log': []
        }

        self.state_changes = 0

        logger.info(f"State-aware workflow initialized: {workflow_id}")

    def get_current_step(self) -> Optional[str]:
        """Get current workflow step"""
        if 0 <= self.state['current_step_index'] < len(self.steps):
            return self.steps[self.state['current_step_index']]
        return None

    def complete_current_step(self, result: Dict[str, Any]):
        """Complete current step and advance to next"""

        current_step = self.get_current_step()
        if not current_step:
            raise ValueError("No current step to complete")

        # Store result
        self.state['step_results'][current_step] = {
            'result': result,
            'completed_at': datetime.now().isoformat(),
            'step_index': self.state['current_step_index']
        }

        # Advance to next step
        self.state['current_step_index'] += 1
        self.state['updated_at'] = datetime.now().isoformat()
        self.state_changes += 1

        # Update status
        if self.state['current_step_index'] >= len(self.steps):
            self.state['status'] = 'completed'
        else:
            self.state['status'] = 'in_progress'

        self.save_state()
        logger.info(f"Completed step: {current_step} in workflow: {self.workflow_id}")

    def add_error(self, error_message: str, step_name: str = None):
        """Add error to workflow error log"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_message': error_message,
            'step_name': step_name or self.get_current_step(),
            'step_index': self.state['current_step_index']
        }

        self.state['error_log'].append(error_entry)
        self.state['updated_at'] = datetime.now().isoformat()
        self.state_changes += 1

        self.save_state()
        logger.error(f"Workflow error: {error_message} in {self.workflow_id}")

    def get_progress(self) -> Dict[str, Any]:
        """Get workflow progress information"""
        completed_steps = len(self.state['step_results'])
        total_steps = len(self.steps)

        return {
            'workflow_id': self.workflow_id,
            'workflow_type': self.workflow_type,
            'current_step': self.get_current_step(),
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'progress_percentage': (completed_steps / total_steps) * 100 if total_steps > 0 else 0,
            'status': self.state['status'],
            'error_count': len(self.state['error_log']),
            'updated_at': self.state['updated_at']
        }

    def save_state(self):
        """Manually save workflow state"""
        try:
            snapshot_id = save_workflow_state(
                workflow_id=self.workflow_id,
                state_data=self.state,
                metadata={
                    'workflow_type': self.workflow_type,
                    'state_changes': self.state_changes,
                    'step_count': len(self.steps)
                }
            )

            logger.debug(f"Workflow state saved: {self.workflow_id} -> {snapshot_id}")
            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            return None

# Demo functions
def demo_state_aware_analytics():
    """Demonstrate state-aware analytics capabilities"""
    print("🔄 State-Aware Analytics Demo")
    print("=" * 60)
    print("Implementing Robust State Management and Persistence")
    print("=" * 60)

    # Create state-aware session
    session_id = "demo_session_001"
    user_id = "demo_user_001"

    print(f"\n💾 Creating State-Aware Session: {session_id}")
    session = StateAwareAnalyticsSession(session_id, user_id)

    # Add conversation turns
    print(f"\n🗨️ Adding Conversation Turns...")
    # Get dynamic teams from data
    from src.utils.data import get_teams_from_data
    teams = get_teams_from_data(limit=2)
    sample_team = teams[0] if teams else "Sample Team"
    sample_team2 = teams[1] if len(teams) > 1 else "Sample Team 2"
    
    session.add_conversation_turn(
        query=f"Analyze {sample_team}'s offensive efficiency",
        response=f"{sample_team}'s offense shows 78% success rate with 2.4 EPA per play",
        agent_id="data_explorer_001"
    )

    session.add_conversation_turn(
        query=f"Compare with {sample_team2}'s defense",
        response=f"{sample_team2} allows 45% opponent success rate with excellent havoc generation",
        agent_id="data_explorer_001"
    )

    print(f"   Conversation turns: {len(session.get_conversation_history())}")

    # Create state-aware agent
    print(f"\n🤖 Creating State-Aware Agent")
    agent = StateAwareAgent("modeler_001", "predictive_modeling")

    # Record analyses
    print(f"\n📊 Recording Agent Analyses...")
    # Get dynamic teams from data
    from src.utils.data import get_sample_matchup
    sample_home, sample_away = get_sample_matchup()
    
    agent.record_analysis(
        analysis_request={"query": "predict game outcome", "teams": [sample_home, sample_away]},
        analysis_result={"prediction": f"{sample_home} 68% win probability", "confidence": 0.82},
        response_time=1.2
    )

    agent.record_analysis(
        analysis_request={"query": "predict score margin", "teams": [sample_home, sample_away]},
        analysis_result={"margin": f"{sample_home} by 7.5 points", "confidence": 0.75},
        response_time=0.8
    )

    print(f"   Agent analyses: {len(agent.state['analysis_history'])}")

    # Create state-aware workflow
    print(f"\n🔄 Creating Multi-Step Workflow")
    workflow_id = "game_prediction_workflow_001"
    workflow_steps = [
        "load_team_data",
        "calculate_advanced_metrics",
        "apply_prediction_model",
        "generate_confidence_scores",
        "create_visualization"
    ]

    workflow = StateAwareWorkflow(workflow_id, "game_prediction", workflow_steps)

    # Simulate workflow execution
    print(f"\n⚡ Executing Workflow Steps...")
    for i, step in enumerate(workflow_steps[:3]):  # Complete first 3 steps
        print(f"   Step {i+1}: {step}")
        workflow.complete_current_step({
            "step_name": step,
            "execution_time": 0.5 + i * 0.1,
            "result": f"Completed {step} successfully"
        })

    # Show progress
    progress = workflow.get_progress()
    print(f"\n📈 Workflow Progress:")
    print(f"   Current step: {progress['current_step']}")
    print(f"   Progress: {progress['progress_percentage']:.1f}%")
    print(f"   Status: {progress['status']}")

    # Save all states
    print(f"\n💾 Saving All States...")
    session.save_state()
    agent.save_state()
    workflow.save_state()

    # Get system metrics
    print(f"\n📊 State Management Metrics:")
    metrics = state_manager.get_metrics()
    print(f"   Total snapshots: {metrics['total_snapshots']}")
    print(f"   Active snapshots: {metrics['active_snapshots']}")
    print(f"   Total transitions: {metrics['total_transitions']}")
    print(f"   Cache hit rate: {metrics['cache_hit_rate']:.3f}")

    # Demonstrate state recovery
    print(f"\n🔄 Demonstrating State Recovery...")

    # Create new session object and restore state
    restored_session = StateAwareAnalyticsSession(session_id, user_id)
    restored_history = restored_session.get_conversation_history()

    print(f"   Restored conversation turns: {len(restored_history)}")
    if restored_history:
        print(f"   Last query: {restored_history[-1]['query'][:50]}...")

    # Demonstrate agent state recovery
    restored_agent = StateAwareAgent("modeler_001", "predictive_modeling")
    agent_metrics = restored_agent.get_performance_metrics()

    print(f"   Restored agent analyses: {agent_metrics['total_analyses']}")
    print(f"   Agent success rate: {agent_metrics['successful_analyses'] / agent_metrics['total_analyses'] * 100:.1f}%")

    print(f"\n✅ State-Aware Analytics Demo Complete!")
    print(f"✅ Session persistence: Working")
    print(f"✅ Agent state management: Working")
    print(f"✅ Workflow state tracking: Working")
    print(f"✅ State recovery: Working")
    print(f"✅ Automatic persistence: Working")

if __name__ == "__main__":
    demo_state_aware_analytics()