#!/usr/bin/env python3
"""
Collaborative Agent Framework
Integrates advanced agent collaboration with the existing analytics agents

This framework enables your existing agents to work together using OpenAI best practices:
- Peer review and validation of analysis results
- Knowledge sharing between agents
- Dynamic task delegation based on expertise
- Conflict resolution for competing insights
- Swarm intelligence for complex problems
"""

import logging
import warnings
from typing import Dict, List, Any, Optional
from datetime import datetime

warnings.warn(
    "collaborative_agent_framework relies on the deprecated `system.communication` "
    "package. Consider migrating collaboration flows to AnalyticsOrchestrator-compatible "
    "patterns. Legacy system imports will fail gracefully.",
    DeprecationWarning,
    stacklevel=2,
)

# Legacy system imports - will fail gracefully if system.communication is not available
try:
    from system.communication.agent_collaboration import (
        AgentCollaborationManager, AgentCapability, CollaborationType,
        collaboration_manager, initiate_peer_review, share_insight, find_expert
    )
    from system.communication.secure_messaging import register_agent, create_message, send_message
    LEGACY_SYSTEM_AVAILABLE = True
except ImportError:
    # Legacy system not available - create mock implementations
    LEGACY_SYSTEM_AVAILABLE = False
    logger.warning("Legacy system.communication not available - collaborative features disabled")
    
    # Create mock classes to prevent import errors
    class AgentCollaborationManager:
        pass
    class AgentCapability:
        def __init__(self, *args, **kwargs):
            pass
    class CollaborationType:
        SWARM_ANALYSIS = "swarm_analysis"
    collaboration_manager = None
    def initiate_peer_review(*args, **kwargs):
        return None
    def share_insight(*args, **kwargs):
        return None
    def find_expert(*args, **kwargs):
        return None
    def register_agent(*args, **kwargs):
        pass
    def create_message(*args, **kwargs):
        return None
    def send_message(*args, **kwargs):
        return None

logger = logging.getLogger("collaborative_framework")

class CollaborativeAgent:
    """
    Base class that extends existing agents with collaboration capabilities

    Any existing agent can inherit from this to gain collaboration features
    """

    def __init__(self, agent_id: str, capabilities: List[str], expertise_domains: List[str]):
        self.agent_id = agent_id

        # Register agent with collaboration system (if available)
        if LEGACY_SYSTEM_AVAILABLE and collaboration_manager is not None:
            self.capability = AgentCapability(
                agent_id=agent_id,
                capabilities=capabilities,
                expertise_domains=expertise_domains,
                max_concurrent_tasks=3
            )
            collaboration_manager.register_agent_capability(self.capability)

            # Register with messaging system
            register_agent(agent_id, {
                "capabilities": capabilities,
                "expertise_domains": expertise_domains,
                "supports_collaboration": True
            })
        else:
            # Legacy system not available - use mock capability
            self.capability = type('MockCapability', (), {
                'agent_id': agent_id,
                'capabilities': capabilities,
                'expertise_domains': expertise_domains,
                'max_concurrent_tasks': 3
            })()
            logger.warning(f"Collaborative agent {agent_id} initialized without legacy collaboration system")

        # Collaboration state
        self.active_collaborations = []
        self.knowledge_shared = []
        self.insights_received = []

        logger.info(f"Collaborative agent initialized: {agent_id}")

    def request_peer_review(self, work_to_review: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Request peer review of analysis work"""
        if not LEGACY_SYSTEM_AVAILABLE:
            logger.warning("Peer review requested but legacy collaboration system not available")
            return None
        
        collaboration_id = initiate_peer_review(
            initiating_agent=self.agent_id,
            work_to_review=work_to_review,
            context=context
        )

        if collaboration_id:
            self.active_collaborations.append(collaboration_id)
            logger.info(f"Peer review requested: {collaboration_id}")

        return collaboration_id

    def share_insight(self, insight: Dict[str, Any], confidence: float = 1.0, domains: List[str] = None) -> str:
        """Share an insight with other agents"""
        knowledge_id = share_insight(
            source_agent=self.agent_id,
            insight=insight,
            confidence=confidence,
            domains=domains or self.capability.expertise_domains
        )

        self.knowledge_shared.append(knowledge_id)
        logger.info(f"Insight shared: {knowledge_id}")

        return knowledge_id

    def find_expert_help(self, required_expertise: str, context: Dict[str, Any]) -> Optional[str]:
        """Find an expert agent for specific help"""
        expert_agent = find_expert(
            requesting_agent=self.agent_id,
            expertise=required_expertise,
            context=context
        )

        if expert_agent:
            logger.info(f"Expert found: {expert_agent} for {required_expertise}")

        return expert_agent

    def search_shared_knowledge(self, query: str, domain_filter: List[str] = None) -> List[Dict[str, Any]]:
        """Search knowledge shared by other agents"""
        if not LEGACY_SYSTEM_AVAILABLE or collaboration_manager is None:
            logger.warning("Knowledge search requested but legacy collaboration system not available")
            return []
        
        knowledge_items = collaboration_manager.search_knowledge_base(
            query=query,
            domain_tags=domain_filter
        )

        # Convert to simpler format
        results = []
        for item in knowledge_items:
            results.append({
                "knowledge_id": item.knowledge_id,
                "source_agent": item.source_agent,
                "knowledge_type": item.knowledge_type,
                "content": item.content,
                "confidence": item.confidence,
                "domains": item.domain_tags,
                "usage_count": item.usage_count
            })

            # Track for this agent
            self.insights_received.append(item.knowledge_id)

        return results

    def initiate_collaborative_analysis(self,
                                      analysis_objective: str,
                                      context: Dict[str, Any],
                                      collaboration_type: CollaborationType = CollaborationType.SWARM_ANALYSIS) -> str:
        """Initiate a collaborative analysis with multiple agents"""
        if not LEGACY_SYSTEM_AVAILABLE or collaboration_manager is None:
            logger.warning("Collaborative analysis requested but legacy collaboration system not available")
            return None
        
        collaboration_id = collaboration_manager.initiate_collaboration(
            initiating_agent=self.agent_id,
            collaboration_type=collaboration_type,
            objective=analysis_objective,
            context=context
        )

        if collaboration_id:
            self.active_collaborations.append(collaboration_id)
            logger.info(f"Collaborative analysis initiated: {collaboration_id}")

        return collaboration_id

    def get_collaboration_status(self, collaboration_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a collaboration"""
        if not LEGACY_SYSTEM_AVAILABLE or collaboration_manager is None:
            return None
        return collaboration_manager.get_collaboration_status(collaboration_id)

class EnhancedAnalyticsAgent(CollaborativeAgent):
    """
    Enhanced version of your existing analytics agents with collaboration capabilities
    """

    def __init__(self, agent_id: str, analytics_specialty: str):
        # Define capabilities based on analytics specialty
        capabilities = self._define_capabilities(analytics_specialty)
        expertise_domains = self._define_expertise_domains(analytics_specialty)

        super().__init__(agent_id, capabilities, expertise_domains)

        self.analytics_specialty = analytics_specialty
        self.analysis_history = []

    def _define_capabilities(self, specialty: str) -> List[str]:
        """Define agent capabilities based on specialty"""
        base_capabilities = ["analysis", "reporting"]

        specialty_capabilities = {
            "data_exploration": ["data_validation", "pattern_recognition", "visualization"],
            "modeling": ["ml_modeling", "feature_engineering", "model_validation"],
            "predictions": ["statistical_modeling", "probability_analysis", "risk_assessment"],
            "visualization": ["chart_creation", "dashboard_design", "storytelling"],
            "expertise": ["domain_knowledge", "comparative_analysis", "trend_analysis"]
        }

        return base_capabilities + specialty_capabilities.get(specialty, [])

    def _define_expertise_domains(self, specialty: str) -> List[str]:
        """Define expertise domains based on specialty"""
        base_domains = ["college_football_analytics"]

        specialty_domains = {
            "data_exploration": ["epa_analysis", "team_efficiency", "advanced_metrics"],
            "modeling": ["predictive_modeling", "machine_learning", "statistical_analysis"],
            "predictions": ["game_outcomes", "score_predictions", "win_probability"],
            "visualization": ["data_visualization", "analytics_dashboard", "interactive_charts"],
            "expertise": ["ranking_systems", "team_comparison", "matchup_analysis"]
        }

        return base_domains + specialty_domains.get(specialty, [])

    def analyze_with_collaboration(self,
                                 analysis_request: Dict[str, Any],
                                 use_peer_review: bool = True,
                                 use_knowledge_sharing: bool = True) -> Dict[str, Any]:
        """Perform analysis with collaboration features"""

        # Perform initial analysis
        analysis_result = self._perform_analysis(analysis_request)

        # Request peer review if enabled
        peer_review_result = None
        if use_peer_review:
            collaboration_id = self.request_peer_review(
                work_to_review=analysis_result,
                context=analysis_request
            )
            peer_review_result = {"collaboration_id": collaboration_id}

        # Share insights from analysis
        if use_knowledge_sharing and analysis_result.get("insights"):
            for insight in analysis_result["insights"]:
                self.share_insight(
                    insight=insight,
                    confidence=analysis_result.get("confidence", 1.0),
                    domains=self.capability.expertise_domains
                )

        # Enhance with shared knowledge
        shared_knowledge = self.search_shared_knowledge(
            query=analysis_request.get("query", ""),
            domain_filter=self.capability.expertise_domains
        )

        # Combine results
        collaborative_result = {
            "original_analysis": analysis_result,
            "peer_review": peer_review_result,
            "shared_knowledge": shared_knowledge[:3],  # Top 3 relevant insights
            "collaboration_enhanced": True,
            "agent_id": self.agent_id,
            "specialty": self.analytics_specialty
        }

        # Store in history
        self.analysis_history.append(collaborative_result)

        return collaborative_result

    def _perform_analysis(self, analysis_request: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual analysis (to be implemented by specific agents)"""
        # This is a placeholder - actual implementation would depend on the specific agent
        return {
            "analysis_type": self.analytics_specialty,
            "results": {"status": "completed"},
            "insights": [{"type": "pattern", "description": "Sample insight"}],
            "confidence": 0.8
        }

# Factory function to create enhanced agents
def create_enhanced_agent(agent_id: str, specialty: str) -> EnhancedAnalyticsAgent:
    """Create an enhanced analytics agent with collaboration capabilities"""
    return EnhancedAnalyticsAgent(agent_id, specialty)

# Demo collaboration functions
def demo_collaborative_football_analysis():
    """Demonstrate collaborative football analytics workflow"""
    print("🏈 Collaborative Football Analytics Demo")
    print("=" * 50)

    # Create specialized agents
    data_agent = create_enhanced_agent("data_explorer_001", "data_exploration")
    modeling_agent = create_enhanced_agent("modeler_001", "modeling")
    prediction_agent = create_enhanced_agent("predictor_001", "predictions")
    viz_agent = create_enhanced_agent("visualizer_001", "visualization")

    print(f"✅ Created 4 collaborative agents with different specialties")

    # Data exploration with collaboration
    print("\n📊 Phase 1: Collaborative Data Exploration")
    data_analysis = data_agent.analyze_with_collaboration({
        "query": "team efficiency patterns in 2025 season",
        "focus": "offensive efficiency",
        "season": "2025"
    })

    print(f"Data analysis completed with collaboration: {data_analysis['collaboration_enhanced']}")

    # Model development with peer review
    print("\n🤖 Phase 2: Collaborative Model Development")
    model_development = modeling_agent.analyze_with_collaboration({
        "query": "develop win probability model",
        "features": ["epa", "success_rate", "talent_differential"],
        "use_peer_review": True
    })

    print(f"Model development completed with peer review: {model_development['peer_review'] is not None}")

    # Prediction with expertise routing
    print("\n🎯 Phase 3: Expert-Led Predictions")
    expert_help = prediction_agent.find_expert_help(
        required_expertise="advanced_statistical_modeling",
        context={"analysis_type": "season_predictions"}
    )

    print(f"Expert found for advanced modeling: {expert_help}")

    # Visualization with shared insights
    print("\n📈 Phase 4: Visualization with Shared Insights")
    viz_analysis = viz_agent.analyze_with_collaboration({
        "query": "create dashboard showing team rankings",
        "shared_knowledge_count": len(viz_agent.search_shared_knowledge("team rankings"))
    })

    print(f"Visualization enhanced with {len(viz_analysis['shared_knowledge'])} shared insights")

    # System metrics
    print("\n📊 Collaboration System Metrics")
    if LEGACY_SYSTEM_AVAILABLE and collaboration_manager is not None:
        metrics = collaboration_manager.get_collaboration_metrics()
        print(f"Total collaborations: {metrics['total_collaborations']}")
        print(f"Knowledge shared: {metrics['knowledge_shared']}")
        print(f"Active collaborations: {metrics['active_collaborations']}")
        print(f"Knowledge base size: {metrics['knowledge_base_size']}")
        print(f"Registered agents: {metrics['registered_agents']}")
    else:
        print("⚠️  Legacy collaboration system not available - metrics unavailable")

    print("\n✅ Collaborative Analytics Demo Complete!")
    print("Agents are now working together using OpenAI best practices!")

if __name__ == "__main__":
    demo_collaborative_football_analysis()