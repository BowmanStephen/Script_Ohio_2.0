#!/usr/bin/env python3
"""
Dynamic Team Formation System for Script Ohio 2.0

Intelligent agent teaming system that forms optimal agent teams
based on task complexity, capabilities, and performance metrics.

Features:
- Dynamic team composition based on task requirements
- Agent capability matching and optimization
- Performance-based team selection
- Real-time team coordination
- Learning from team performance
- Load balancing and resource optimization
"""

import os
import sys
import json
import time
import math
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.core.memory_system import (
    memory_manager,
    MemoryLevel,
    MemoryType,
    MemoryQuery,
)


class TaskComplexity(Enum):
    """Task complexity levels"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


class TeamRole(Enum):
    """Agent roles within teams"""

    LEAD = "lead"
    SPECIALIST = "specialist"
    VALIDATOR = "validator"
    COORDINATOR = "coordinator"
    MONITOR = "monitor"


class TaskType(Enum):
    """Types of tasks requiring team formation"""

    ANALYSIS = "analysis"
    PREDICTION = "prediction"
    VALIDATION = "validation"
    OPTIMIZATION = "optimization"
    INTEGRATION = "integration"
    RESEARCH = "research"


@dataclass
class AgentProfile:
    """Agent capability and performance profile"""

    agent_id: str
    agent_type: str
    capabilities: List[str]
    performance_score: float  # 0.0 - 1.0
    availability: bool  # Available for assignment
    current_load: int = 0  # Number of active tasks
    specialties: List[str] = field(default_factory=list)  # Domain specialties
    max_concurrent: int = 3
    recent_success_rate: float = 0.0
    average_execution_time: float = 0.0
    cost_per_hour: float = 0.0
    team_role_preferences: List[TeamRole] = field(default_factory=list)
    collaboration_history: Dict[str, int] = field(default_factory=dict)  # Agent ID -> collaboration count


@dataclass
class TaskRequirement:
    """Task requirements for team formation"""

    task_id: str
    task_type: TaskType
    complexity: TaskComplexity
    required_capabilities: List[str]
    preferred_capabilities: List[str]
    optional_capabilities: List[str]
    min_team_size: int
    max_team_size: int
    priority: int  # 1-10 scale
    estimated_duration: float  # In seconds
    budget_constraint: Optional[float] = None
    security_level: int = 1  # 1-5 scale
    coordination_required: bool = True


@dataclass
class TeamComposition:
    """Agent team composition plan"""

    task_id: str
    team_id: str
    agents: List[AgentProfile]
    roles: Dict[str, TeamRole]
    confidence_score: float  # 0.0 - 1.0
    estimated_cost: float
    estimated_duration: float
    risk_factors: List[str]
    formation_reasoning: str
    coordination_protocol: str


@dataclass
class TeamPerformance:
    """Team performance metrics"""

    team_id: str
    task_id: str
    success_rate: float
    execution_time: float
    cost_efficiency: float
    collaboration_score: float
    individual_performances: Dict[str, float]
    created_at: datetime
    completed_at: Optional[datetime] = None


class DynamicTeamFormationEngine:
    """
    Advanced team formation engine for adaptive agent coordination

    Forms optimal agent teams based on task requirements,
    agent capabilities, and historical performance data.
    """

    def __init__(self, max_team_size: int = 8, learning_enabled: bool = True):
        self.max_team_size = max_team_size
        self.learning_enabled = learning_enabled

        self.logger = self._setup_logging()

        # Agent registry and profiles
        self.agent_profiles = {}
        self.agent_capabilities = {}

        # Team composition cache
        self.composition_cache = {}
        self.performance_history = {}

        # Learning data
        self.success_patterns = defaultdict(list)
        self.failure_patterns = defaultdict(list)
        self.optimal_team_sizes = defaultdict(int)

        # Background processes
        self._profile_update_thread = None
        self._learning_thread = None
        self._running = True

        # Performance metrics
        self.stats = {
            "total_formations": 0,
            "successful_formations": 0,
            "average_team_size": 0.0,
            "average_formation_time": 0.0,
            "cache_hit_rate": 0.0,
            "last_optimization": datetime.utcnow(),
        }

        # Initialize background processes
        self._start_background_processes()

        self.logger.info("🤝 Dynamic Team Formation Engine initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("team_formation")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def register_agent(
        self, agent: BaseAgent, performance_data: Optional[Dict] = None
    ) -> bool:
        """
        Register an agent for team formation

        Args:
            agent: Agent instance
            performance_data: Historical performance data

        Returns:
            Success of registration
        """
        try:
            # Extract agent capabilities
            capabilities = [cap.name for cap in agent.capabilities]

            # Create agent profile
            profile = AgentProfile(
                agent_id=agent.agent_id,
                agent_type=agent.__class__.__name__,
                capabilities=capabilities,
                performance_score=(
                    performance_data.get("performance_score", 0.7)
                    if performance_data
                    else 0.7
                ),
                availability=True,
                current_load=0,
                max_concurrent=3,
                specialties=self._extract_specialties(agent),
                recent_success_rate=(
                    performance_data.get("success_rate", 0.8)
                    if performance_data
                    else 0.8
                ),
                average_execution_time=(
                    performance_data.get("avg_execution_time", 30.0)
                    if performance_data
                    else 30.0
                ),
                cost_per_hour=self._estimate_cost(agent),
                team_role_preferences=self._analyze_role_preferences(agent),
                collaboration_history={},
            )

            self.agent_profiles[agent.agent_id] = profile
            self.agent_capabilities[agent.agent_id] = capabilities

            self.logger.info(
                f"🤝 Registered agent {agent.agent_id} with {len(capabilities)} capabilities"
            )
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to register agent {agent.agent_id}: {e}")
            return False

    def form_optimal_team(
        self, requirement: TaskRequirement, available_agents: Optional[List[str]] = None
    ) -> TeamComposition:
        """
        Form optimal team for the given task requirement

        Args:
            requirement: Task requirements
            available_agents: List of available agent IDs (None = all)

        Returns:
            Optimized team composition
        """
        start_time = time.time()

        try:
            # Check cache first
            cache_key = self._generate_cache_key(requirement)
            if cache_key in self.composition_cache:
                cached_composition = self.composition_cache[cache_key]
                cached_composition.estimated_duration = requirement.estimated_duration
                cached_composition.estimated_cost = self._calculate_team_cost(
                    cached_composition.agents
                )
                self.stats["cache_hit_rate"] += 1
                self.logger.info(
                    f"💾 Using cached team composition for task {requirement.task_id}"
                )
                return cached_composition

            # Get candidate agents
            candidates = self._get_candidate_agents(requirement, available_agents)

            if len(candidates) < requirement.min_team_size:
                # Not enough candidates
                return self._create_inadequate_team_composition(requirement, candidates)

            # Analyze task complexity and determine optimal approach
            if requirement.complexity == TaskComplexity.SIMPLE:
                composition = self._form_simple_team(requirement, candidates)
            elif requirement.complexity == TaskComplexity.MODERATE:
                composition = self._form_balanced_team(requirement, candidates)
            elif requirement.complexity == TaskComplexity.COMPLEX:
                composition = self._form_specialized_team(requirement, candidates)
            else:  # CRITICAL
                composition = self._form_expert_team(requirement, candidates)

            # Validate and optimize composition
            composition = self._validate_and_optimize_composition(
                composition, requirement
            )

            # Cache the result
            self.composition_cache[cache_key] = composition

            # Update stats
            formation_time = time.time() - start_time
            self._update_stats(composition, formation_time)

            self.logger.info(
                f"🤝 Formed optimal team: {len(composition.agents)} agents, "
                f"confidence: {composition.confidence_score:.2f}, "
                f"time: {formation_time:.3f}s"
            )

            return composition

        except Exception as e:
            self.logger.error(f"❌ Team formation failed: {e}")
            return self._create_default_team_composition(requirement)

    def _get_candidate_agents(
        self, requirement: TaskRequirement, available_agents: Optional[List[str]]
    ) -> List[AgentProfile]:
        """Get candidate agents that meet task requirements"""
        candidates = []

        # Filter by availability if specified
        agent_ids = (
            available_agents if available_agents else list(self.agent_profiles.keys())
        )

        for agent_id in agent_ids:
            if agent_id not in self.agent_profiles:
                continue

            profile = self.agent_profiles[agent_id]

            # Check availability
            if not profile.availability:
                continue

            # Check capability match
            capability_match = self._calculate_capability_match(profile, requirement)
            if capability_match == 0.0:
                continue

            # Check performance threshold
            if (
                profile.performance_score < 0.3
            ):  # Low performers excluded from critical tasks
                if requirement.priority >= 8:
                    continue

            candidates.append(profile)

        # Sort by capability match and performance
        candidates.sort(
            key=lambda x: (
                self._calculate_capability_match(x, requirement),
                x.performance_score,
                -x.current_load,
            ),
            reverse=True,
        )

        return candidates

    def _form_simple_team(
        self, requirement: TaskRequirement, candidates: List[AgentProfile]
    ) -> TeamComposition:
        """Form simple team for basic tasks"""
        # Simple tasks need 1-2 agents with basic capabilities
        team_size = min(requirement.min_team_size, len(candidates))
        selected_agents = candidates[:team_size]

        return TeamComposition(
            task_id=requirement.task_id,
            team_id=f"simple_team_{int(time.time())}",
            agents=selected_agents,
            roles=self._assign_simple_roles(selected_agents),
            confidence_score=0.8,
            estimated_cost=self._calculate_team_cost(selected_agents),
            estimated_duration=requirement.estimated_duration,
            risk_factors=[],
            formation_reasoning="Simple task requiring basic capabilities",
            coordination_protocol="sequential",
        )

    def _form_balanced_team(
        self, requirement: TaskRequirement, candidates: List[AgentProfile]
    ) -> TeamComposition:
        """Form balanced team for moderate complexity tasks"""
        # Moderate tasks need diverse capabilities
        optimal_size = max(requirement.min_team_size, min(4, len(candidates)))

        # Select agents with diverse capabilities
        selected_agents = self._select_diverse_agents(
            candidates, requirement, optimal_size
        )

        return TeamComposition(
            task_id=requirement.task_id,
            team_id=f"balanced_team_{int(time.time())}",
            agents=selected_agents,
            roles=self._assign_balanced_roles(selected_agents, requirement),
            confidence_score=0.7,
            estimated_cost=self._calculate_team_cost(selected_agents),
            estimated_duration=requirement.estimated_duration * 0.9,  # Efficiency gain
            risk_factors=["medium_complexity"],
            formation_reasoning="Balanced team with diverse capabilities",
            coordination_protocol="parallel_with_lead",
        )

    def _form_specialized_team(
        self, requirement: TaskRequirement, candidates: List[AgentProfile]
    ) -> TeamComposition:
        """Form specialized team for complex tasks"""
        # Complex tasks need specialized expertise
        team_size = max(requirement.min_team_size, min(6, len(candidates)))

        # Prioritize agents with required capabilities
        priority_agents = []
        support_agents = []

        for candidate in candidates:
            if self._has_required_capability(candidate, requirement):
                priority_agents.append(candidate)
            else:
                support_agents.append(candidate)

        # Balance priority and support agents
        selected_priority = priority_agents[
            : min(len(priority_agents), team_size // 2 + 1)
        ]
        remaining_slots = team_size - len(selected_priority)
        selected_support = support_agents[:remaining_slots]

        selected_agents = selected_priority + selected_support

        return TeamComposition(
            task_id=requirement.task_id,
            team_id=f"specialized_team_{int(time.time())}",
            agents=selected_agents,
            roles=self._assign_specialized_roles(selected_agents, requirement),
            confidence_score=0.6,
            estimated_cost=self._calculate_team_cost(selected_agents),
            estimated_duration=requirement.estimated_duration * 0.8,  # Efficiency gain
            risk_factors=["high_complexity", "coordination_overhead"],
            formation_reasoning="Specialized team with expert capabilities",
            coordination_protocol="hierarchical",
        )

    def _form_expert_team(
        self, requirement: TaskRequirement, candidates: List[AgentProfile]
    ) -> TeamComposition:
        """Form expert team for critical tasks"""
        # Critical tasks need top-performing specialized agents
        team_size = min(requirement.max_team_size, len(candidates))

        # Select top performers with relevant capabilities
        top_candidates = sorted(
            [c for c in candidates if self._has_required_capability(c, requirement)],
            key=lambda x: (x.performance_score, x.recent_success_rate),
            reverse=True,
        )

        # Add supporting specialists if needed
        if len(top_candidates) < team_size:
            remaining_candidates = [c for c in candidates if c not in top_candidates]
            top_candidates.extend(
                remaining_candidates[: team_size - len(top_candidates)]
            )

        selected_agents = top_candidates[:team_size]

        return TeamComposition(
            task_id=requirement.task_id,
            team_id=f"expert_team_{int(time.time())}",
            agents=selected_agents,
            roles=self._assign_expert_roles(selected_agents, requirement),
            confidence_score=0.9,
            estimated_cost=self._calculate_team_cost(selected_agents)
            * 1.2,  # Premium for expertise
            estimated_duration=requirement.estimated_duration
            * 0.7,  # Expert efficiency
            risk_factors=["high_stakes", "resource_intensive"],
            formation_reasoning="Expert team with top performers",
            coordination_protocol="distributed_consensus",
        )

    def _select_diverse_agents(
        self,
        candidates: List[AgentProfile],
        requirement: TaskRequirement,
        team_size: int,
    ) -> List[AgentProfile]:
        """Select agents with diverse capabilities"""
        selected = []
        covered_capabilities = set()

        for candidate in candidates:
            if len(selected) >= team_size:
                break

            # Check if agent brings new capabilities
            new_capabilities = set(candidate.capabilities) - covered_capabilities
            if new_capabilities or len(selected) == 0:
                selected.append(candidate)
                covered_capabilities.update(candidate.capabilities)

        # Fill remaining slots if needed
        if len(selected) < team_size:
            for candidate in candidates:
                if candidate not in selected and len(selected) < team_size:
                    selected.append(candidate)

        return selected

    def _calculate_capability_match(
        self, agent: AgentProfile, requirement: TaskRequirement
    ) -> float:
        """Calculate how well agent capabilities match task requirements"""
        required_capabilities = set(requirement.required_capabilities)
        agent_capabilities = set(agent.capabilities)

        if not required_capabilities:
            return 1.0

        intersection = required_capabilities.intersection(agent_capabilities)

        # Weighted scoring
        score = len(intersection) / len(required_capabilities)

        # Boost for preferred capabilities
        if requirement.preferred_capabilities:
            preferred_set = set(requirement.preferred_capabilities)
            preferred_intersection = preferred_set.intersection(agent_capabilities)
            if preferred_intersection:
                score += 0.2 * (len(preferred_intersection) / len(preferred_set))

        return min(score, 1.0)

    def _has_required_capability(
        self, agent: AgentProfile, requirement: TaskRequirement
    ) -> bool:
        """Check if agent has all required capabilities"""
        required_capabilities = set(requirement.required_capabilities)
        agent_capabilities = set(agent.capabilities)
        return required_capabilities.issubset(agent_capabilities)

    def _calculate_team_cost(self, agents: List[AgentProfile]) -> float:
        """Calculate total cost of team"""
        return sum(agent.cost_per_hour for agent in agents)

    def _assign_simple_roles(self, agents: List[AgentProfile]) -> Dict[str, TeamRole]:
        """Assign simple roles to team members"""
        roles = {}

        if agents:
            roles[agents[0].agent_id] = TeamRole.LEAD

        for i, agent in enumerate(agents[1:], start=1):
            roles[agent.agent_id] = TeamRole.SPECIALIST

        return roles

    def _assign_balanced_roles(
        self, agents: List[AgentProfile], requirement: TaskRequirement
    ) -> Dict[str, TeamRole]:
        """Assign balanced roles based on agent profiles"""
        roles = {}

        # Assign lead to best performer
        lead_agent = max(agents, key=lambda x: x.performance_score)
        roles[lead_agent.agent_id] = TeamRole.LEAD

        # Assign specialists based on capabilities
        remaining_agents = [a for a in agents if a != lead_agent]

        for agent in remaining_agents:
            if "validation" in agent.capabilities:
                roles[agent.agent_id] = TeamRole.VALIDATOR
            elif (
                "coordination" in agent.capabilities
                or "orchestration" in agent.capabilities
            ):
                roles[agent.agent_id] = TeamRole.COORDINATOR
            else:
                roles[agent.agent_id] = TeamRole.SPECIALIST

        return roles

    def _assign_specialized_roles(
        self, agents: List[AgentProfile], requirement: TaskRequirement
    ) -> Dict[str, TeamRole]:
        """Assign specialized roles for complex tasks"""
        roles = {}

        # Assign lead to highest performer
        lead_agent = max(agents, key=lambda x: x.performance_score)
        roles[lead_agent.agent_id] = TeamRole.LEAD

        # Assign coordinator if available
        coordinator = next(
            (a for a in agents if a != lead_agent and "coordination" in a.capabilities),
            None,
        )
        if coordinator:
            roles[coordinator.agent_id] = TeamRole.COORDINATOR
            remaining = [a for a in agents if a not in [lead_agent, coordinator]]
        else:
            remaining = [a for a in agents if a != lead_agent]

        # Assign validator if validation needed
        if requirement.task_type in [TaskType.VALIDATION, TaskType.RESEARCH]:
            validator = next(
                (a for a in remaining if "validation" in a.capabilities), None
            )
            if validator:
                roles[validator.agent_id] = TeamRole.VALIDATOR
                remaining = [a for a in remaining if a != validator]

        # Assign monitors for critical tasks
        if requirement.priority >= 8 and remaining:
            monitor = min(remaining, key=lambda x: x.performance_score)
            roles[monitor.agent_id] = TeamRole.MONITOR
            remaining = [a for a in remaining if a != monitor]

        # Remaining agents are specialists
        for agent in remaining:
            roles[agent.agent_id] = TeamRole.SPECIALIST

        return roles

    def _assign_expert_roles(
        self, agents: List[AgentProfile], requirement: TaskRequirement
    ) -> Dict[str, TeamRole]:
        """Assign expert roles for critical tasks"""
        roles = {}

        # Multi-leader structure for critical tasks
        primary_lead = max(agents, key=lambda x: x.performance_score)
        secondary_lead = max(
            [a for a in agents if a != primary_lead], key=lambda x: x.performance_score
        )

        roles[primary_lead.agent_id] = TeamRole.LEAD
        roles[secondary_lead.agent_id] = TeamRole.COORDINATOR

        # Assign expert monitors
        top_performers = sorted(
            [a for a in agents if a not in [primary_lead, secondary_lead]],
            key=lambda x: x.performance_score,
            reverse=True,
        )[:2]

        for agent in top_performers:
            roles[agent.agent_id] = TeamRole.MONITOR

        # Remaining agents are expert specialists
        remaining = [
            a
            for a in agents
            if a not in [primary_lead, secondary_lead] + top_performers
        ]
        for agent in remaining:
            roles[agent.agent_id] = TeamRole.SPECIALIST

        return roles

    def _validate_and_optimize_composition(
        self, composition: TeamComposition, requirement: TaskRequirement
    ) -> TeamComposition:
        """Validate and optimize team composition"""
        # Check minimum requirements
        if len(composition.agents) < requirement.min_team_size:
            composition.confidence_score *= 0.5

        # Check maximum constraints
        if len(composition.agents) > requirement.max_team_size:
            # Remove lowest performing agents
            composition.agents.sort(key=lambda x: x.performance_score)
            composition.agents = composition.agents[: requirement.max_team_size]

        # Update roles after agent removal
        composition.roles = self._reassign_roles(composition.agents, requirement)

        # Update confidence score
        composition.confidence_score = self._calculate_team_confidence(
            composition.agents, requirement
        )

        # Update costs and timing
        composition.estimated_cost = self._calculate_team_cost(composition.agents)
        composition.estimated_duration = self._estimate_team_execution_time(
            composition, requirement
        )

        return composition

    def _reassign_roles(
        self, agents: List[AgentProfile], requirement: TaskRequirement
    ) -> Dict[str, TeamRole]:
        """Reassign roles after team optimization"""
        if requirement.complexity == TaskComplexity.SIMPLE:
            return self._assign_simple_roles(agents)
        elif requirement.complexity == TaskComplexity.MODERATE:
            return self._assign_balanced_roles(agents, requirement)
        elif requirement.complexity == TaskComplexity.COMPLEX:
            return self._assign_specialized_roles(agents, requirement)
        else:  # CRITICAL
            return self._assign_expert_roles(agents, requirement)

    def _calculate_team_confidence(
        self, agents: List[AgentProfile], requirement: TaskRequirement
    ) -> float:
        """Calculate confidence score for team composition"""
        if not agents:
            return 0.0

        # Average performance score
        avg_performance = sum(a.performance_score for a in agents) / len(agents)

        # Capability coverage
        capability_score = 0.0
        for agent in agents:
            capability_score += self._calculate_capability_match(agent, requirement)
        capability_score /= len(agents)

        # Load balancing
        load_balance = 1.0 - (
            max(a.current_load for a in agents) / 5.0
        )  # Assume max load of 5

        # Experience level
        experience_score = min(
            sum(a.recent_success_rate for a in agents) / len(agents), 1.0
        )

        # Weighted combination
        weights = {
            "performance": 0.4,
            "capabilities": 0.4,
            "load_balance": 0.1,
            "experience": 0.1,
        }
        confidence = (
            weights["performance"] * avg_performance
            + weights["capabilities"] * capability_score
            + weights["load_balance"] * load_balance
            + weights["experience"] * experience_score
        )

        return min(confidence, 1.0)

    def _estimate_team_execution_time(
        self, composition: TeamComposition, requirement: TaskRequirement
    ) -> float:
        """Estimate team execution time based on composition"""
        if not composition.agents:
            return requirement.estimated_duration

        # Base time modified by team efficiency
        base_time = requirement.estimated_duration

        # Team size efficiency (diminishing returns after 3 agents)
        if len(composition.agents) <= 3:
            team_efficiency = 0.8 + (len(composition.agents) * 0.1)
        else:
            team_efficiency = 1.1 - (len(composition.agents) - 3) * 0.05

        # Performance-based speed adjustment
        avg_performance = sum(a.performance_score for a in composition.agents) / len(
            composition.agents
        )
        performance_factor = (
            2.0 - avg_performance
        )  # Higher performance = faster execution

        return base_time * team_efficiency * performance_factor

    def _extract_specialties(self, agent: BaseAgent) -> List[str]:
        """Extract agent specialties from class name and capabilities"""
        specialties = []

        # Extract from class name
        class_name = agent.__class__.__name__.lower()

        if "analytics" in class_name:
            specialties.append("analytics")
        if "prediction" in class_name:
            specialties.append("prediction")
        if "validation" in class_name:
            specialties.append("validation")
        if "integration" in class_name:
            specialties.append("integration")
        if "insight" in class_name:
            specialties.append("insight")
        if "learning" in class_name:
            specialties.append("learning")
        if "cfbd" in class_name:
            specialties.append("cfbd")
        if "model" in class_name:
            specialties.append("machine_learning")

        return specialties

    def _analyze_role_preferences(self, agent: BaseAgent) -> List[TeamRole]:
        """Analyze agent's preferred team roles"""
        preferences = [TeamRole.SPECIALIST]  # Default

        class_name = agent.__class__.__name__.lower()

        if "orchestrator" in class_name or "coordination" in class_name:
            preferences.append(TeamRole.COORDINATOR)

        if "meta" in class_name or "manager" in class_name:
            preferences.append(TeamRole.LEAD)

        if "validation" in class_name:
            preferences.append(TeamRole.VALIDATOR)

        return preferences

    def _estimate_cost(self, agent: BaseAgent) -> float:
        """Estimate agent cost per hour"""
        # Base cost plus complexity-based adjustment
        base_cost = 50.0

        class_name = agent.__class__.__name__.lower()

        if "orchestrator" in class_name or "meta" in class_name:
            return base_cost * 3.0
        elif "analytics" in class_name or "insight" in class_name:
            return base_cost * 2.0
        elif "model" in class_name or "prediction" in class_name:
            return base_cost * 1.5
        else:
            return base_cost

    def _create_inadequate_team_composition(
        self, requirement: TaskRequirement, candidates: List[AgentProfile]
    ) -> TeamComposition:
        """Create team composition when requirements cannot be met"""
        return TeamComposition(
            task_id=requirement.task_id,
            team_id=f"inadequate_team_{int(time.time())}",
            agents=candidates,
            roles={},
            confidence_score=0.1,
            estimated_cost=0.0,
            estimated_duration=requirement.estimated_duration * 2.0,
            risk_factors=["insufficient_capabilities", "high_risk"],
            formation_reasoning="Insufficient qualified agents available",
            coordination_protocol="manual_intervention",
        )

    def _create_default_team_composition(
        self, requirement: TaskRequirement
    ) -> TeamComposition:
        """Create default team composition"""
        return TeamComposition(
            task_id=requirement.task_id,
            team_id=f"default_team_{int(time.time())}",
            agents=[],
            roles={},
            confidence_score=0.0,
            estimated_cost=0.0,
            estimated_duration=requirement.estimated_duration,
            risk_factors=["no_agents_available", "manual_formation_required"],
            formation_reasoning="Default composition - no agents available",
            coordination_protocol="manual",
        )

    def update_agent_performance(self, agent_id: str, performance_data: Dict) -> None:
        """Update agent performance profile"""
        if agent_id not in self.agent_profiles:
            return

        profile = self.agent_profiles[agent_id]

        # Update performance metrics
        if "performance_score" in performance_data:
            # Smooth update
            profile.performance_score = (
                profile.performance_score * 0.7
                + performance_data["performance_score"] * 0.3
            )

        if "success_rate" in performance_data:
            profile.recent_success_rate = (
                profile.recent_success_rate * 0.8
                + performance_data["success_rate"] * 0.2
            )

        if "execution_time" in performance_data:
            profile.average_execution_time = (
                profile.average_execution_time * 0.8
                + performance_data["execution_time"] * 0.2
            )

        # Update availability and load
        if "availability" in performance_data:
            profile.availability = performance_data["availability"]

        # Update load based on current tasks
        profile.current_load = max(
            0,
            profile.current_load + (1 if performance_data.get("active", False) else -1),
        )

        self.logger.debug(
            f"📊 Updated performance for agent {agent_id}: "
            f"score={profile.performance_score:.2f}, "
            f"load={profile.current_load}"
        )

    def record_team_performance(self, performance: TeamPerformance) -> None:
        """Record team performance for learning"""
        try:
            self.performance_history[performance.team_id] = performance

            # Update learning patterns
            if performance.success_rate >= 0.8:
                self.success_patterns[performance.task_type.value].append(performance)
            else:
                self.failure_patterns[performance.task_type.value].append(performance)

            # Update optimal team sizes
            team_size = len(performance.individual_performances)
            if performance.success_rate >= 0.9:
                self.optimal_team_sizes[performance.task_type.value] = max(
                    self.optimal_team_sizes[performance.task_type.value], team_size
                )

            # Limit history size
            if len(self.success_patterns[performance.task_type.value]) > 100:
                self.success_patterns[performance.task_type.value] = (
                    self.success_patterns[performance.task_type.value][-50:]
                )
            if len(self.failure_patterns[performance.task_type.value]) > 100:
                self.failure_patterns[performance.task_type.value] = (
                    self.failure_patterns[performance.task_type.value][-50:]
                )

        except Exception as e:
            self.logger.error(f"Could not record team performance: {e}")

    def get_optimal_team_size(
        self, task_type: TaskType, complexity: TaskComplexity
    ) -> int:
        """Get optimal team size for given task type and complexity"""
        try:
            # Base team size by complexity
            base_sizes = {
                TaskComplexity.SIMPLE: 1,
                TaskComplexity.MODERATE: 2,
                TaskComplexity.COMPLEX: 4,
                TaskComplexity.CRITICAL: 6,
            }

            # Adjust by task type based on learned patterns
            adjustment_factors = {
                TaskType.ANALYSIS: 1.2,
                TaskType.PREDICTION: 1.1,
                TaskType.VALIDATION: 1.0,
                TaskType.OPTIMIZATION: 1.5,
                TaskType.INTEGRATION: 2.0,
                TaskType.RESEARCH: 1.3,
            }

            base_size = base_sizes.get(complexity, 3)

            # Apply learned adjustments
            adjustment = adjustment_factors.get(task_type, 1.0)

            # Use learned optimal size if available
            learned_size = self.optimal_team_sizes.get(task_type.value)
            if learned_size and complexity != TaskComplexity.CRITICAL:
                optimal_size = int(learned_size * adjustment)
                return min(optimal_size, self.max_team_size)

            optimal_size = int(base_size * adjustment)
            return min(optimal_size, self.max_team_size)

        except Exception as e:
            self.logger.error(f"Could not determine optimal team size: {e}")
            return 3  # Default fallback

    def get_team_formation_stats(self) -> Dict[str, Any]:
        """Get team formation statistics"""
        try:
            return {
                "total_formations": self.stats["total_formations"],
                "successful_formations": self.stats["successful_formations"],
                "success_rate": (
                    self.stats["successful_formations"]
                    / max(1, self.stats["total_formations"])
                ),
                "average_team_size": self.stats["average_team_size"],
                "average_formation_time": self.stats["average_formation_time"],
                "cache_hit_rate": (
                    self.stats["cache_hit_rate"]
                    / max(1, self.stats["total_formations"])
                ),
                "registered_agents": len(self.agent_profiles),
                "available_agents": sum(
                    1 for p in self.agent_profiles.values() if p.availability
                ),
                "optimal_team_sizes": dict(self.optimal_team_sizes),
                "learning_enabled": self.learning_enabled,
                "last_optimization": self.stats["last_optimization"].isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}

    def clear_cache(self) -> None:
        """Clear team composition cache"""
        self.composition_cache.clear()
        self.logger.info("🧹 Cleared team formation cache")

    def _generate_cache_key(self, requirement: TaskRequirement) -> str:
        """Generate cache key for task requirement"""
        key_data = f"{requirement.task_type.value}_{requirement.complexity.value}"
        key_data += f"_{requirement.min_team_size}_{requirement.max_team_size}"
        key_data += f"_{requirement.priority}_{len(requirement.required_capabilities)}"

        return hashlib.md5(key_data.encode()).hexdigest()[:12]

    def _update_stats(
        self, composition: TeamComposition, formation_time: float
    ) -> None:
        """Update formation statistics"""
        self.stats["total_formations"] += 1
        self.stats["average_formation_time"] = (
            self.stats["average_formation_time"] * (self.stats["total_formations"] - 1)
            + formation_time
        ) / self.stats["total_formations"]
        self.stats["average_team_size"] = (
            self.stats["average_team_size"] * (self.stats["total_formations"] - 1)
            + len(composition.agents)
        ) / self.stats["total_formations"]

        if composition.confidence_score >= 0.5:
            self.stats["successful_formations"] += 1

    def _start_background_processes(self) -> None:
        """Start background optimization processes"""
        if self.learning_enabled:
            self._profile_update_thread = threading.Thread(
                target=self._profile_update_worker, daemon=True
            )
            self._profile_update_thread.start()

            self._learning_thread = threading.Thread(
                target=self._learning_worker, daemon=True
            )
            self._learning_thread.start()

    def _profile_update_worker(self) -> None:
        """Background worker for updating agent profiles"""
        while self._running:
            try:
                time.sleep(300)  # Update every 5 minutes

                # Update agent profiles based on recent activity
                for agent_id, profile in self.agent_profiles.items():
                    if profile.current_load > 0:
                        # Gradually reduce load
                        profile.current_load = max(0, profile.current_load - 1)

                        # Decay recent success rate over time
                        profile.recent_success_rate *= 0.99

                self.logger.debug("🔄 Updated agent profiles")

            except Exception as e:
                self.logger.error(f"Profile update error: {e}")

    def _learning_worker(self) -> None:
        """Background worker for learning from team performance"""
        while self._running:
            try:
                time.sleep(3600)  # Learn every hour

                if self.learning_enabled:
                    self._analyze_performance_patterns()
                    self._optimize_team_strategies()

                self.logger.debug("🧠 Learning cycle completed")

            except Exception as e:
                self.logger.error(f"Learning error: {e}")

    def _analyze_performance_patterns(self) -> None:
        """Analyze performance patterns for optimization"""
        try:
            for task_type, patterns in self.success_patterns.items():
                if len(patterns) >= 10:
                    # Analyze common success factors
                    recent_patterns = patterns[-10:]

                    # Extract common team sizes
                    team_sizes = [
                        len(p.individual_performances) for p in recent_patterns
                    ]
                    most_common_size = max(set(team_sizes), key=team_sizes.count)

                    # Update optimal team size
                    if most_common_size > self.optimal_team_sizes.get(task_type, 0):
                        self.optimal_team_sizes[task_type] = most_common_size

        except Exception as e:
            self.logger.error(f"Pattern analysis error: {e}")

    def _optimize_team_strategies(self) -> None:
        """Optimize team formation strategies based on learning"""
        try:
            # Clean old cache entries periodically
            if len(self.composition_cache) > 1000:
                # Remove oldest half
                cache_items = list(self.composition_cache.items())
                cache_items.sort(key=lambda x: x[1])  # Sort by timestamp
                self.composition_cache = dict(cache_items[len(cache_items) // 2 :])

        except Exception as e:
            self.logger.error(f"Strategy optimization error: {e}")

    def shutdown(self) -> None:
        """Shutdown the team formation engine gracefully"""
        self.logger.info("🔄 Shutting down Dynamic Team Formation Engine...")

        self._running = False

        # Wait for background threads
        if self._profile_update_thread:
            self._profile_update_thread.join(timeout=5)
        if self._learning_thread:
            self._learning_thread.join(timeout=5)

        # Clear cache
        self.clear_cache()

        self.logger.info("✅ Dynamic Team Formation Engine shutdown complete")


# Global team formation engine instance
team_formation_engine = DynamicTeamFormationEngine()

if __name__ == "__main__":
    # Test team formation engine
    print("🤝 Testing Dynamic Team Formation Engine")

    # Create mock agent profile for testing
    from agents.core.agent_framework import AgentCapability, PermissionLevel

    class MockAgent(BaseAgent):
        def __init__(self, agent_id: str):
            super().__init__(agent_id, "MockAgent", PermissionLevel.READ_EXECUTE)

        def _define_capabilities(self) -> List[AgentCapability]:
            return [
                AgentCapability(
                    name="test_capability",
                    description="Test capability",
                    execution_time_estimate=1.0,
                    required_permissions=[PermissionLevel.READ_EXECUTE],
                    parameters=["test_param"],
                    returns={"result": "string"},
                )
            ]

        def _execute_action(
            self, action: str, parameters: Dict, user_context: Dict
        ) -> Dict:
            return {"status": "success", "result": "test result"}

    # Register test agents
    test_agents = [
        ("analytics_1", MockAgent),
        ("prediction_1", MockAgent),
        ("validation_1", MockAgent),
        ("integration_1", MockAgent),
    ]

    for agent_id, agent_class in test_agents:
        agent = agent_class(agent_id)
        team_formation_engine.register_agent(agent)

    print(f"✅ Registered {len(test_agents)} test agents")

    # Test team formation
    requirement = TaskRequirement(
        task_id="test_task_1",
        task_type=TaskType.ANALYSIS,
        complexity=TaskComplexity.MODERATE,
        required_capabilities=["test_capability"],
        preferred_capabilities=["test_capability"],
        optional_capabilities=["optional_capability"],
        min_team_size=2,
        max_team_size=4,
        priority=5,
        estimated_duration=60.0,
        security_level=2,
    )

    team = team_formation_engine.form_optimal_team(requirement)

    print(f"🤝 Formed team: {len(team.agents)} agents")
    print(f"📊 Confidence score: {team.confidence_score:.2f}")
    print(f"💰 Estimated cost: ${team.estimated_cost:.2f}")
    print(f"⏱️ Estimated time: {team.estimated_duration:.1f}s")

    # Get stats
    stats = team_formation_engine.get_team_formation_stats()
    print(f"📈 Team formation stats: {json.dumps(stats, indent=2, default=str)}")

    # Shutdown
    team_formation_engine.shutdown()
    print("🏁 Test completed!")
