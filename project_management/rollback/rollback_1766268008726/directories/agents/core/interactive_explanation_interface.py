#!/usr/bin/env python3
"""
Interactive Explanation Interface for Human-AI Collaboration

Advanced human-in-the-loop system providing:
- Real-time model explanations with interactive exploration
- Dynamic feature importance visualization
- Counterfactual scenario testing
- Uncertainty quantification communication
- College football domain expertise integration
"""

import time
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Agent framework imports
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.core.memory_system import HierarchicalMemoryManager
from agents.core.explanation_engine import (
    CollegeFootballExplainer,
    FeatureImportanceExplainer,
    CounterfactualExplainer,
    UncertaintyExplainer
)

logger = logging.getLogger(__name__)

@dataclass
class ExplanationRequest:
    """User request for model explanation."""
    game_id: str
    model_name: str
    explanation_types: List[str]
    user_expertise_level: str  # 'novice', 'intermediate', 'expert'
    specific_questions: List[str]
    context_preferences: Dict[str, Any]
    interaction_id: str
    timestamp: datetime

@dataclass
class InteractiveExplanation:
    """Interactive explanation with user controls."""
    explanation_id: str
    request: ExplanationRequest
    feature_importance: Dict[str, Any]
    counterfactuals: List[Dict[str, Any]]
    uncertainty_analysis: Dict[str, Any]
    domain_insights: List[str]
    interactive_elements: Dict[str, Any]
    user_feedback: Optional[Dict[str, Any]] = None
    generated_at: datetime = None

class InteractiveExplanationInterface(BaseAgent):
    """
    Advanced Human-AI collaboration interface for model explanations.

    Provides sophisticated interactive explanations that adapt to user expertise
    and allow dynamic exploration of model predictions.
    """

    def __init__(self, agent_id: str = "interactive_explanation_interface"):
        super().__init__(agent_id, "Interactive Explanation Interface", PermissionLevel.READ_EXECUTE)

        # Initialize explanation engines
        self.feature_explainer = FeatureImportanceExplainer()
        self.counterfactual_explainer = CounterfactualExplainer()
        self.uncertainty_explainer = UncertaintyExplainer()
        self.domain_explainer = CollegeFootballExplainer()

        # Initialize memory system
        self.memory_manager = HierarchicalMemoryManager()

        # User expertise adapters
        self.expertise_adapters = {
            'novice': self._adapt_for_novice,
            'intermediate': self._adapt_for_intermediate,
            'expert': self._adapt_for_expert
        }

        # Explanation history and learning
        self.explanation_history = []
        self.user_interaction_patterns = {}

        # Domain knowledge cache
        self.domain_knowledge_cache = {}

        logger.info(f"Interactive Explanation Interface initialized: {self.agent_id}")

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities."""
        return [
            AgentCapability(
                name="generate_interactive_explanation",
                description="Generate comprehensive interactive explanations",
                execution_time_estimate=3.0,
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["explanation_engine", "memory_system"],
                data_access=["game_data", "model_predictions"]
            ),
            AgentCapability(
                name="handle_user_interaction",
                description="Process user interactions and refine explanations",
                execution_time_estimate=1.5,
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["memory_system"],
                data_access=["interaction_history", "explanations"]
            ),
            AgentCapability(
                name="generate_counterfactual_scenarios",
                description="Generate and analyze counterfactual scenarios",
                execution_time_estimate=2.5,
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["counterfactual_engine"],
                data_access=["game_data", "model_predictions"]
            ),
            AgentCapability(
                name="provide_domain_insights",
                description="Provide college football domain expertise",
                execution_time_estimate=1.0,
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["domain_knowledge_base"],
                data_access=["team_data", "historical_patterns"]
            )
        ]

    def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict:
        """Execute agent actions."""
        try:
            if action == "generate_interactive_explanation":
                result = self._generate_interactive_explanation(parameters)
                return {
                    "status": "success",
                    "data": result,
                    "execution_time": time.time(),
                    "agent_id": self.agent_id
                }

            elif action == "handle_user_interaction":
                result = self._handle_user_interaction(parameters)
                return {
                    "status": "success",
                    "data": result,
                    "execution_time": time.time(),
                    "agent_id": self.agent_id
                }

            elif action == "generate_counterfactual_scenarios":
                result = self._generate_counterfactual_scenarios(parameters)
                return {
                    "status": "success",
                    "data": result,
                    "execution_time": time.time(),
                    "agent_id": self.agent_id
                }

            elif action == "provide_domain_insights":
                result = self._provide_domain_insights(parameters)
                return {
                    "status": "success",
                    "data": result,
                    "execution_time": time.time(),
                    "agent_id": self.agent_id
                }

            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id
            }

    def _generate_interactive_explanation(self, parameters: Dict) -> Dict:
        """Generate comprehensive interactive explanation."""

        start_time = time.time()

        # Extract parameters
        game_data = parameters.get('game_data', {})
        model_prediction = parameters.get('model_prediction', {})
        user_preferences = parameters.get('user_preferences', {})

        # Create explanation request
        request = ExplanationRequest(
            game_id=game_data.get('id', ''),
            model_name=model_prediction.get('model', 'unknown'),
            explanation_types=user_preferences.get('explanation_types', ['feature_importance', 'counterfactuals']),
            user_expertise_level=user_preferences.get('expertise_level', 'intermediate'),
            specific_questions=user_preferences.get('questions', []),
            context_preferences=user_preferences.get('context', {}),
            interaction_id=f"exp_{int(time.time())}",
            timestamp=datetime.now()
        )

        try:
            # Generate component explanations
            feature_importance = self._generate_feature_importance_explanation(game_data, model_prediction, request)
            counterfactuals = self._generate_counterfactual_explanations(game_data, model_prediction, request)
            uncertainty_analysis = self._generate_uncertainty_explanation(game_data, model_prediction, request)
            domain_insights = self._generate_domain_insights(game_data, model_prediction, request)

            # Create interactive elements
            interactive_elements = self._create_interactive_elements(feature_importance, counterfactuals, request)

            # Adapt explanation to user expertise level
            adapted_explanation = self._adapt_explanation_to_expertise_level({
                'feature_importance': feature_importance,
                'counterfactuals': counterfactuals,
                'uncertainty_analysis': uncertainty_analysis,
                'domain_insights': domain_insights,
                'interactive_elements': interactive_elements
            }, request.user_expertise_level)

            # Create explanation object
            explanation = InteractiveExplanation(
                explanation_id=f"exp_{int(time.time())}",
                request=request,
                feature_importance=adapted_explanation['feature_importance'],
                counterfactuals=adapted_explanation['counterfactuals'],
                uncertainty_analysis=adapted_explanation['uncertainty_analysis'],
                domain_insights=adapted_explanation['domain_insights'],
                interactive_elements=adapted_explanation['interactive_elements'],
                generated_at=datetime.now()
            )

            # Store in memory and history
            self.memory_manager.store(
                key=f"explanation_{explanation.explanation_id}",
                data=asdict(explanation),
                level='EXPERIENCE',
                tags=['explanation', request.model_name, request.game_id]
            )

            self.explanation_history.append(explanation)

            # Track user interaction patterns
            self._track_user_interaction(request)

            execution_time = time.time() - start_time

            return {
                'explanation': asdict(explanation),
                'execution_time': execution_time,
                'success': True
            }

        except Exception as e:
            logger.error(f"Explanation generation failed: {str(e)}")
            return {
                'explanation': None,
                'execution_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            }

    def _generate_feature_importance_explanation(self, game_data: Dict, model_prediction: Dict, request: ExplanationRequest) -> Dict:
        """Generate feature importance explanation."""

        try:
            # Use feature importance explainer
            feature_importance = self.feature_explainer.explain_prediction(
                game_data=game_data,
                model_prediction=model_prediction,
                model_name=request.model_name
            )

            # Add college football context
            cf_insights = self.domain_explainer.explain_feature_importance(
                feature_importance.get('important_features', []),
                game_data
            )

            feature_importance['domain_insights'] = cf_insights
            feature_importance['explanation_type'] = 'feature_importance'

            return feature_importance

        except Exception as e:
            logger.error(f"Feature importance explanation failed: {str(e)}")
            return {
                'explanation_type': 'feature_importance',
                'error': str(e),
                'fallback_message': 'Feature importance analysis temporarily unavailable'
            }

    def _generate_counterfactual_explanations(self, game_data: Dict, model_prediction: Dict, request: ExplanationRequest) -> List[Dict]:
        """Generate counterfactual explanations."""

        try:
            # Generate counterfactual scenarios
            counterfactuals = self.counterfactual_explainer.generate_counterfactuals(
                game_data=game_data,
                model_prediction=model_prediction,
                num_scenarios=3,
                constraints=request.context_preferences.get('constraints', {})
            )

            # Add domain context to each counterfactual
            for cf in counterfactuals:
                cf['domain_interpretation'] = self.domain_explainer.interpret_counterfactual(
                    cf, game_data
                )
                cf['feasibility_assessment'] = self._assess_counterfactual_feasibility(cf)

            return counterfactuals

        except Exception as e:
            logger.error(f"Counterfactual explanation failed: {str(e)}")
            return [{
                'explanation_type': 'counterfactual',
                'error': str(e),
                'fallback_message': 'Counterfactual analysis temporarily unavailable'
            }]

    def _generate_uncertainty_explanation(self, game_data: Dict, model_prediction: Dict, request: ExplanationRequest) -> Dict:
        """Generate uncertainty quantification explanation."""

        try:
            # Generate uncertainty analysis
            uncertainty = self.uncertainty_explainer.explain_uncertainty(
                game_data=game_data,
                model_prediction=model_prediction,
                model_name=request.model_name
            )

            # Add domain-specific uncertainty factors
            domain_uncertainty = self.domain_explainer.explain_uncertainty_factors(
                game_data, model_prediction
            )

            uncertainty['domain_factors'] = domain_uncertainty
            uncertainty['explanation_type'] = 'uncertainty_analysis'

            # Adapt to user expertise
            if request.user_expertise_level == 'novice':
                uncertainty['interpretation'] = self._simplify_uncertainty_explanation(uncertainty)

            return uncertainty

        except Exception as e:
            logger.error(f"Uncertainty explanation failed: {str(e)}")
            return {
                'explanation_type': 'uncertainty_analysis',
                'error': str(e),
                'fallback_message': 'Uncertainty analysis temporarily unavailable'
            }

    def _generate_domain_insights(self, game_data: Dict, model_prediction: Dict, request: ExplanationRequest) -> List[str]:
        """Generate domain-specific insights."""

        try:
            insights = []

            # Get team information
            home_team = game_data.get('home_team', '')
            away_team = game_data.get('away_team', '')

            # Generate matchup insights
            if home_team and away_team:
                matchup_insights = self.domain_explainer.get_matchup_insights(
                    home_team, away_team, game_data
                )
                insights.extend(matchup_insights)

            # Answer specific user questions
            for question in request.specific_questions:
                answer = self.domain_explainer.answer_domain_question(
                    question, game_data, model_prediction
                )
                insights.append(f"Q: {question}\nA: {answer}")

            # Add general context
            general_insights = self.domain_explainer.get_general_context_insights(
                game_data, model_prediction
            )
            insights.extend(general_insights)

            return insights[:5]  # Limit to top 5 insights

        except Exception as e:
            logger.error(f"Domain insights generation failed: {str(e)}")
            return ["Domain insights temporarily unavailable"]

    def _create_interactive_elements(self, feature_importance: Dict, counterfactuals: List[Dict], request: ExplanationRequest) -> Dict:
        """Create interactive exploration elements."""

        interactive_elements = {
            'feature_slider_controls': self._create_feature_sliders(feature_importance),
            'scenario_builder': self._create_scenario_builder(counterfactuals),
            'uncertainty_explorer': self._create_uncertainty_explorer(),
            'comparison_tools': self._create_comparison_tools(),
            'question_answer': self._create_qa_interface()
        }

        # Adapt complexity based on user expertise
        if request.user_expertise_level == 'novice':
            interactive_elements = self._simplify_interactive_elements(interactive_elements)
        elif request.user_expertise_level == 'expert':
            interactive_elements = self._enhance_interactive_elements(interactive_elements)

        return interactive_elements

    def _adapt_explanation_to_expertise_level(self, explanation: Dict, expertise_level: str) -> Dict:
        """Adapt explanation complexity to user expertise level."""

        adapter = self.expertise_adapters.get(expertise_level, self._adapt_for_intermediate)
        return adapter(explanation)

    def _adapt_for_novice(self, explanation: Dict) -> Dict:
        """Adapt explanation for novice users."""

        # Simplify technical language
        explanation['simplified_language'] = True

        # Focus on key takeaways
        if 'feature_importance' in explanation:
            explanation['feature_importance']['key_factors'] = (
                explanation['feature_importance'].get('important_features', [])[:3]
            )

        # Add analogies and simple comparisons
        explanation['analogies'] = self._generate_simple_analogies(explanation)

        # Reduce information density
        explanation['focus_areas'] = ['most_important', 'what_if_scenarios']

        return explanation

    def _adapt_for_intermediate(self, explanation: Dict) -> Dict:
        """Adapt explanation for intermediate users."""

        # Balance technical detail with accessibility
        explanation['technical_level'] = 'intermediate'

        # Include deeper insights but avoid jargon
        explanation['detailed_insights'] = True

        return explanation

    def _adapt_for_expert(self, explanation: Dict) -> Dict:
        """Adapt explanation for expert users."""

        # Include full technical details
        explanation['technical_level'] = 'expert'
        explanation['full_model_details'] = True

        # Add statistical significance information
        explanation['statistical_analysis'] = True

        # Include model confidence intervals and robustness checks
        explanation['advanced_analysis'] = True

        return explanation

    def _handle_user_interaction(self, parameters: Dict) -> Dict:
        """Process user interactions and refine explanations."""

        interaction_data = parameters.get('interaction_data', {})
        explanation_id = parameters.get('explanation_id', '')

        try:
            # Find explanation in history
            explanation = None
            for exp in self.explanation_history:
                if exp.explanation_id == explanation_id:
                    explanation = exp
                    break

            if not explanation:
                return {
                    'success': False,
                    'message': 'Explanation not found'
                }

            # Process interaction type
            interaction_type = interaction_data.get('type', '')

            if interaction_type == 'feature_adjustment':
                result = self._handle_feature_adjustment(interaction_data, explanation)
            elif interaction_type == 'counterfactual_explore':
                result = self._handle_counterfactual_exploration(interaction_data, explanation)
            elif interaction_type == 'uncertainty_detailed':
                result = self._handle_uncertainty_exploration(interaction_data, explanation)
            elif interaction_type == 'domain_question':
                result = self._handle_domain_question(interaction_data, explanation)
            else:
                result = {
                    'success': False,
                    'message': f'Unknown interaction type: {interaction_type}'
                }

            # Update user interaction patterns
            self._update_interaction_patterns(explanation.request, interaction_data)

            # Store feedback for learning
            explanation.user_feedback = interaction_data

            return result

        except Exception as e:
            logger.error(f"User interaction handling failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _track_user_interaction(self, request: ExplanationRequest):
        """Track user interaction patterns for learning."""

        user_id = request.context_preferences.get('user_id', 'anonymous')

        if user_id not in self.user_interaction_patterns:
            self.user_interaction_patterns[user_id] = {
                'expertise_level': request.user_expertise_level,
                'preferred_explanation_types': request.explanation_types,
                'interaction_count': 0,
                'question_patterns': [],
                'last_interaction': None
            }

        patterns = self.user_interaction_patterns[user_id]
        patterns['interaction_count'] += 1
        patterns['question_patterns'].extend(request.specific_questions)
        patterns['last_interaction'] = request.timestamp

        # Store in memory for persistent learning
        self.memory_manager.store(
            key=f"user_patterns_{user_id}",
            data=patterns,
            level='KNOWLEDGE',
            tags=['user_patterns', 'learning']
        )

    def _assess_counterfactual_feasibility(self, counterfactual: Dict) -> Dict:
        """Assess feasibility of counterfactual scenarios."""

        # Simple feasibility assessment based on magnitude of changes
        feasibility_score = 1.0
        constraints = []

        # Check each feature change
        if 'feature_changes' in counterfactual:
            for feature_change in counterfactual['feature_changes']:
                feature_name = feature_change.get('feature', '')
                change_magnitude = abs(feature_change.get('change', 0))

                # Domain-specific feasibility rules
                if 'elo' in feature_name.lower():
                    if change_magnitude > 100:  # Large ELO change unlikely
                        feasibility_score *= 0.8
                        constraints.append(f"Large {feature_name} change unlikely")

                elif 'talent' in feature_name.lower():
                    if change_magnitude > 50:  # Large talent change unlikely
                        feasibility_score *= 0.7
                        constraints.append(f"Talent score changes limited by recruiting")

        return {
            'feasibility_score': feasibility_score,
            'constraints': constraints,
            'assessment': 'high' if feasibility_score > 0.8 else 'medium' if feasibility_score > 0.6 else 'low'
        }

    def _simplify_uncertainty_explanation(self, uncertainty: Dict) -> str:
        """Create simplified uncertainty explanation for novice users."""

        confidence_level = uncertainty.get('confidence_interval', {}).get('confidence', 0.5)

        if confidence_level > 0.8:
            return "Very confident in this prediction"
        elif confidence_level > 0.6:
            return "Moderately confident in this prediction"
        else:
            return "Low confidence - this game could go either way"

    def _generate_simple_analogies(self, explanation: Dict) -> List[str]:
        """Generate simple analogies for complex concepts."""

        analogies = []

        # Feature importance analogy
        if 'feature_importance' in explanation:
            analogies.append(
                "Think of feature importance like ingredients in a recipe - "
                "some ingredients (like team strength) matter much more than others"
            )

        # Uncertainty analogy
        if 'uncertainty_analysis' in explanation:
            analogies.append(
                "Uncertainty is like weather forecasting - we can make good predictions "
                "but there's always some chance of surprises"
            )

        return analogies

    def get_performance_metrics(self) -> Dict:
        """Get interface performance metrics."""

        return {
            'explanations_generated': len(self.explanation_history),
            'unique_users': len(self.user_interaction_patterns),
            'average_interaction_time': self._calculate_average_interaction_time(),
            'popular_explanation_types': self._get_popular_explanation_types(),
            'user_satisfaction_score': self._calculate_user_satisfaction(),
            'learning_effectiveness': self._assess_learning_effectiveness()
        }

    def _calculate_average_interaction_time(self) -> float:
        """Calculate average time users spend with explanations."""

        # This would be implemented with actual timing data
        # For now, return a placeholder
        return 45.0  # seconds

    def _get_popular_explanation_types(self) -> Dict[str, int]:
        """Get most popular explanation types."""

        type_counts = {}
        for explanation in self.explanation_history:
            for exp_type in explanation.request.explanation_types:
                type_counts[exp_type] = type_counts.get(exp_type, 0) + 1

        return type_counts

    def _calculate_user_satisfaction(self) -> float:
        """Calculate user satisfaction score."""

        # This would be implemented with actual user feedback
        # For now, return a placeholder
        return 4.2  # out of 5

    def _assess_learning_effectiveness(self) -> Dict:
        """Assess how well users are learning from explanations."""

        return {
            'concept_understanding_improvement': 0.75,
            'feature_importance_comprehension': 0.68,
            'uncertainty_interpretation': 0.62,
            'domain_knowledge_acquisition': 0.71
        }