"""
Explanation Orchestrator Agent

Coordinates explanation generation and human-AI collaboration.
Provides interpretable explanations for predictions, decisions, and insights.
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.core.explanation_engine import (
    HumanAIExplanationEngine,
    Explanation,
    ExplanationType,
    ExplanationComponent,
)
from agents.core.memory_system import HierarchicalMemoryManager, MemoryLevel, MemoryType


class ExplanationOrchestratorAgent(BaseAgent):
    """Specialized agent for generating and coordinating explanations."""

    def __init__(self, agent_id: str = "explanation_orchestrator"):
        super().__init__(
            agent_id, "Explanation Orchestrator", PermissionLevel.READ_EXECUTE
        )

        # Initialize explanation engine
        self.explanation_engine = HumanAIExplanationEngine()
        self.memory_manager = HierarchicalMemoryManager()

        # Enhanced capabilities
        self.explanation_strategies = {
            "simple": ["feature_importance", "uncertainty_analysis"],
            "detailed": [
                "feature_importance",
                "counterfactual",
                "uncertainty_analysis",
                "model_comparison",
            ],
            "comprehensive": [
                "feature_importance",
                "counterfactual",
                "causal_chain",
                "similar_cases",
                "uncertainty_analysis",
                "model_comparison",
            ],
        }

        # Domain-specific contexts
        self.prediction_contexts = {
            "game_outcome": {
                "key_factors": ["team_performance", "matchups", "situational_factors"],
                "audience": "fans_and_bettors",
                "complexity": "medium",
            },
            "player_performance": {
                "key_factors": [
                    "individual_stats",
                    "team_context",
                    "historical_performance",
                ],
                "audience": "coaches_and_analysts",
                "complexity": "high",
            },
            "season_predictions": {
                "key_factors": [
                    "team_trends",
                    "schedule_difficulty",
                    "historical_patterns",
                ],
                "audience": "analysts_and_fans",
                "complexity": "low",
            },
            "betting_insights": {
                "key_factors": [
                    "market_efficiency",
                    "value_opportunities",
                    "risk_factors",
                ],
                "audience": "sports_bettors",
                "complexity": "high",
            },
        }

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define explanation orchestrator capabilities."""

        return [
            AgentCapability(
                name="explain_prediction",
                description="Generate comprehensive explanations for game predictions",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["explanation_engine", "memory_system"],
                data_access=["prediction_data", "model_predictions", "features"],
                execution_time_estimate=3.0,
            ),
            AgentCapability(
                name="explain_model_decision",
                description="Explain why a model made a specific decision",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["explanation_engine", "feature_analyzer"],
                data_access=["model_output", "input_features", "decision_context"],
                execution_time_estimate=2.5,
            ),
            AgentCapability(
                name="create_comparative_analysis",
                description="Generate explanations comparing multiple predictions or scenarios",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["explanation_engine", "comparison_tools"],
                data_access=["prediction_set", "comparison_type", "context"],
                execution_time_estimate=4.0,
            ),
            AgentCapability(
                name="generate_insight_explanation",
                description="Explain analytical insights and patterns",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["explanation_engine", "pattern_analyzer"],
                data_access=["insight_data", "pattern_analysis", "context"],
                execution_time_estimate=3.5,
            ),
            AgentCapability(
                name="optimize_explanation_for_audience",
                description="Tailor explanations for specific audience types",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["explanation_engine", "audience_optimizer"],
                data_access=["explanation", "audience_type", "detail_level"],
                execution_time_estimate=2.0,
            ),
            AgentCapability(
                name="track_explanation_effectiveness",
                description="Monitor and analyze explanation effectiveness",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["explanation_engine", "analytics", "memory_system"],
                data_access=["explanation_id", "user_feedback", "performance_metrics"],
                execution_time_estimate=1.5,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Execute explanation orchestrator actions."""

        try:
            if action == "explain_prediction":
                return self._explain_prediction(parameters, user_context)
            elif action == "explain_model_decision":
                return self._explain_model_decision(parameters, user_context)
            elif action == "create_comparative_analysis":
                return self._create_comparative_analysis(parameters, user_context)
            elif action == "generate_insight_explanation":
                return self._generate_insight_explanation(parameters, user_context)
            elif action == "optimize_explanation_for_audience":
                return self._optimize_explanation_for_audience(parameters, user_context)
            elif action == "track_explanation_effectiveness":
                return self._track_explanation_effectiveness(parameters, user_context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
                "timestamp": datetime.now(),
            }

    def _explain_prediction(self, parameters: Dict, user_context: Dict) -> Dict:
        """Generate comprehensive explanation for a prediction."""

        prediction_data = parameters.get("prediction_data", {})
        model_predictions = parameters.get("model_predictions", {})
        features = parameters.get("features", {})
        explanation_strategy = parameters.get("explanation_strategy", "detailed")

        try:
            # Determine explanation types based on strategy
            if explanation_strategy in self.explanation_strategies:
                explanation_types_str = self.explanation_strategies[
                    explanation_strategy
                ]
                explanation_types = [
                    ExplanationType(t)
                    for t in explanation_types_str
                    if t in [e.value for e in ExplanationType]
                ]
            else:
                explanation_types = [
                    ExplanationType.FEATURE_IMPORTANCE,
                    ExplanationType.UNCERTAINTY_ANALYSIS,
                ]

            # Generate explanation
            explanation = self.explanation_engine.generate_explanation(
                prediction_data=prediction_data,
                model_predictions=model_predictions,
                features=features,
                explanation_types=explanation_types,
            )

            # Store in memory for future reference
            self.memory_manager.store(
                content={
                    "explanation": explanation,
                    "context": prediction_data,
                    "user_preferences": user_context.get("preferences", {}),
                },
                memory_level=MemoryLevel.EPISODIC,
                memory_type=MemoryType.EXPERIENCE,
                metadata={
                    "explanation_id": explanation.prediction_id,
                    "prediction_type": explanation.prediction_type,
                    "user_context": user_context.get("preferences", {}),
                },
                expires_in=86400,  # 24 hours
                tags=["explanation", "prediction", explanation.prediction_type],
            )

            return {
                "status": "success",
                "data": {
                    "explanation": explanation.__dict__,
                    "summary": explanation.human_readable_summary,
                    "confidence": explanation.confidence_level,
                    "explanation_id": explanation.prediction_id,
                    "generation_time": explanation.timestamp.isoformat(),
                },
                "execution_time": time.time(),
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to generate explanation: {str(e)}",
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
            }

    def _explain_model_decision(self, parameters: Dict, user_context: Dict) -> Dict:
        """Explain why a model made a specific decision."""

        model_output = parameters.get("model_output", {})
        input_features = parameters.get("input_features", {})
        decision_context = parameters.get("decision_context", {})

        try:
            # Convert model output to prediction format
            if isinstance(model_output, dict):
                model_predictions = model_output
            else:
                # Assume single model output
                model_predictions = {"primary_model": model_output}

            # Create prediction data
            prediction_data = {
                "type": decision_context.get("prediction_type", "model_decision"),
                "context": decision_context,
                "timestamp": datetime.now(),
            }

            # Generate focused explanation
            explanation = self.explanation_engine.generate_explanation(
                prediction_data=prediction_data,
                model_predictions=model_predictions,
                features=input_features,
                explanation_types=[
                    ExplanationType.FEATURE_IMPORTANCE,
                    ExplanationType.UNCERTAINTY_ANALYSIS,
                ],
            )

            # Extract decision-specific insights
            decision_factors = []
            for component in explanation.components:
                if component.type == "feature_importance":
                    decision_factors.extend(
                        [e["feature"] for e in component.evidence[:3]]
                    )

            # Create alternative scenarios
            alternative_scenarios = self._generate_decision_alternatives(
                input_features, model_predictions
            )

            return {
                "status": "success",
                "data": {
                    "decision_explanation": explanation.human_readable_summary,
                    "key_factors": decision_factors,
                    "alternative_scenarios": alternative_scenarios,
                    "confidence": explanation.confidence_level,
                    "reasoning_trace": [
                        comp.content for comp in explanation.components
                    ],
                },
                "execution_time": time.time(),
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to explain model decision: {str(e)}",
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
            }

    def _create_comparative_analysis(
        self, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Generate explanations comparing multiple predictions or scenarios."""

        prediction_set = parameters.get("prediction_set", [])
        comparison_type = parameters.get("comparison_type", "predictions")
        context = parameters.get("context", {})

        try:
            if not prediction_set:
                raise ValueError("No predictions provided for comparison")

            # Generate explanations for each prediction
            explanations = []
            for i, pred_data in enumerate(prediction_set):
                explanation = self.explanation_engine.generate_explanation(
                    prediction_data=pred_data.get("data", {}),
                    model_predictions=pred_data.get("models", {}),
                    features=pred_data.get("features", {}),
                    explanation_types=[
                        ExplanationType.FEATURE_IMPORTANCE,
                        ExplanationType.UNCERTAINTY_ANALYSIS,
                    ],
                )
                explanations.append(
                    {
                        "prediction_index": i,
                        "prediction_label": pred_data.get("label", f"Prediction {i+1}"),
                        "explanation": explanation,
                        "key_outcome": pred_data.get("outcome", "Unknown"),
                    }
                )

            # Analyze key differences
            key_differences = self._analyze_prediction_differences(explanations)

            # Generate recommendation
            recommendation = self._generate_comparison_recommendation(
                explanations, comparison_type, context
            )

            # Create comparative explanation
            comparative_summary = f"""
**Comparative Analysis Summary**

This analysis compares {len(explanations)} different predictions or scenarios:

**Key Differences:**
{chr(10).join(f"• {diff}" for diff in key_differences[:5])}

**Recommendation:**
{recommendation}

**Individual Prediction Analyses:**
{chr(10).join(f"**{exp['prediction_label']}**: {exp['explanation'].human_readable_summary.split('**Prediction Analysis Summary**')[1].split('**Key Factors**')[0].strip()}" for exp in explanations)}
            """.strip()

            return {
                "status": "success",
                "data": {
                    "comparison_explanation": comparative_summary,
                    "key_differences": key_differences,
                    "recommendation": recommendation,
                    "individual_explanations": [
                        {
                            "label": exp["prediction_label"],
                            "summary": exp["explanation"].human_readable_summary,
                            "confidence": exp["explanation"].confidence_level,
                            "outcome": exp["key_outcome"],
                        }
                        for exp in explanations
                    ],
                    "comparison_metrics": {
                        "total_predictions": len(explanations),
                        "average_confidence": np.mean(
                            [
                                exp["explanation"].confidence_level
                                for exp in explanations
                            ]
                        ),
                        "confidence_range": {
                            "min": min(
                                [
                                    exp["explanation"].confidence_level
                                    for exp in explanations
                                ]
                            ),
                            "max": max(
                                [
                                    exp["explanation"].confidence_level
                                    for exp in explanations
                                ]
                            ),
                        },
                    },
                },
                "execution_time": time.time(),
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to create comparative analysis: {str(e)}",
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
            }

    def _generate_insight_explanation(
        self, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Explain analytical insights and patterns."""

        insight_data = parameters.get("insight_data", {})
        pattern_analysis = parameters.get("pattern_analysis", {})
        context = parameters.get("context", {})

        try:
            # Generate explanation for the insight
            insight_type = insight_data.get("type", "pattern")
            insight_value = insight_data.get("value", "")
            insight_significance = insight_data.get("significance", "moderate")

            # Create contextual explanation
            significance_descriptions = {
                "low": "interesting observation that may warrant monitoring",
                "moderate": "noteworthy pattern that could influence predictions",
                "high": "significant finding that strongly impacts outcomes",
                "critical": "game-changing insight that should be prioritized",
            }

            # Generate explanation content
            explanation_content = f"""
**Insight Analysis: {insight_type}**

This {insight_type} represents a {significance_descriptions.get(insight_significance, 'relevant pattern')} in the data.

**What This Means:**
The insight {insight_value} suggests important trends that could affect future predictions and strategy decisions.

**Statistical Significance:**
{pattern_analysis.get('statistical_significance', 'Not quantified')}

**Historical Context:**
This pattern has been observed in {pattern_analysis.get('historical_occurrences', 'recent')} similar situations, making it a reliable indicator for future analysis.

**Actionable Implications:**
This insight should be considered when making predictions about similar scenarios and could inform strategic decisions.
            """.strip()

            # Generate specific implications
            implications = []
            if "offensive" in insight_type.lower() or "defense" in insight_type.lower():
                implications.append(
                    "Consider team matchup strategies and player utilization"
                )
            if "seasonal" in insight_type.lower():
                implications.append("Account for seasonal trends and team development")
            if "betting" in insight_type.lower() or "market" in insight_type.lower():
                implications.append(
                    "Factor into betting value assessments and market efficiency"
                )

            return {
                "status": "success",
                "data": {
                    "insight_explanation": explanation_content,
                    "significance": f"{insight_significance} significance - {significance_descriptions.get(insight_significance, '')}",
                    "implications": implications,
                    "contextual_factors": {
                        "data_quality": pattern_analysis.get("data_quality", "unknown"),
                        "sample_size": pattern_analysis.get(
                            "sample_size", "not specified"
                        ),
                        "confidence_interval": pattern_analysis.get(
                            "confidence_interval", "not calculated"
                        ),
                    },
                    "next_steps": [
                        "Monitor this insight in future predictions",
                        "Consider incorporating into model features",
                        "Validate against upcoming game outcomes",
                    ],
                },
                "execution_time": time.time(),
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to generate insight explanation: {str(e)}",
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
            }

    def _optimize_explanation_for_audience(
        self, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Tailor explanations for specific audience types."""

        explanation = parameters.get("explanation", {})
        audience_type = parameters.get("audience_type", "general")
        detail_level = parameters.get("detail_level", "medium")

        try:
            # Define audience profiles
            audience_profiles = {
                "general": {
                    "technical_level": "low",
                    "focus_areas": [
                        "main_conclusion",
                        "key_factors",
                        "simple_language",
                    ],
                    "avoid": ["technical_jargon", "statistical_details"],
                    "tone": "conversational",
                },
                "analysts": {
                    "technical_level": "high",
                    "focus_areas": [
                        "methodology",
                        "confidence_intervals",
                        "model_performance",
                    ],
                    "include": ["technical_details", "statistical_analysis"],
                    "tone": "professional",
                },
                "coaches": {
                    "technical_level": "medium",
                    "focus_areas": [
                        "actionable_insights",
                        "practical_implications",
                        "strategy",
                    ],
                    "include": ["performance_metrics", "tactical_takeaways"],
                    "tone": "direct",
                },
                "bettors": {
                    "technical_level": "medium",
                    "focus_areas": ["value_assessment", "risk_factors", "probability"],
                    "include": ["betting_relevance", "market_comparison"],
                    "tone": "analytical",
                },
            }

            profile = audience_profiles.get(audience_type, audience_profiles["general"])

            # Optimize explanation content
            if isinstance(explanation, dict):
                if "human_readable_summary" in explanation:
                    original_summary = explanation["human_readable_summary"]
                elif "summary" in explanation:
                    original_summary = explanation["summary"]
                else:
                    original_summary = str(explanation)
            else:
                original_summary = str(explanation)

            # Apply optimization based on audience profile
            optimized_content = self._apply_audience_optimization(
                original_summary, profile, detail_level
            )

            # Calculate accessibility score
            accessibility_score = self._calculate_accessibility_score(
                optimized_content, profile
            )

            return {
                "status": "success",
                "data": {
                    "optimized_explanation": optimized_content,
                    "accessibility_score": accessibility_score,
                    "audience_profile": profile,
                    "optimization_applied": {
                        "technical_level_adjusted": profile["technical_level"],
                        "focus_areas_addressed": profile["focus_areas"],
                        "tone_matched": profile["tone"],
                    },
                },
                "execution_time": time.time(),
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to optimize explanation: {str(e)}",
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
            }

    def _track_explanation_effectiveness(
        self, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Monitor and analyze explanation effectiveness."""

        explanation_id = parameters.get("explanation_id", "")
        user_feedback = parameters.get("user_feedback", {})
        performance_metrics = parameters.get("performance_metrics", {})

        try:
            # Record feedback in explanation engine
            satisfaction_score = user_feedback.get("satisfaction_score", 0.5)
            feedback_text = user_feedback.get("feedback_text", "")

            success = self.explanation_engine.record_user_feedback(
                explanation_id=explanation_id,
                satisfaction_score=satisfaction_score,
                feedback_text=feedback_text,
            )

            # Analyze effectiveness
            effectiveness_score = self._calculate_effectiveness_score(
                satisfaction_score, performance_metrics, user_feedback
            )

            # Generate improvement suggestions
            improvement_suggestions = self._generate_improvement_suggestions(
                effectiveness_score, user_feedback, performance_metrics
            )

            # Store effectiveness metrics
            effectiveness_data = {
                "explanation_id": explanation_id,
                "effectiveness_score": effectiveness_score,
                "user_satisfaction": satisfaction_score,
                "performance_metrics": performance_metrics,
                "improvement_suggestions": improvement_suggestions,
                "timestamp": datetime.now(),
            }

            self.memory_manager.store(
                content=effectiveness_data,
                memory_level=MemoryLevel.SEMANTIC,
                memory_type=MemoryType.KNOWLEDGE,
                metadata={
                    "explanation_id": explanation_id,
                    "analysis_type": "effectiveness",
                },
                expires_in=2592000,  # 30 days
                tags=["explanation", "effectiveness", "feedback"],
            )

            return {
                "status": "success",
                "data": {
                    "effectiveness_score": effectiveness_score,
                    "improvement_suggestions": improvement_suggestions,
                    "feedback_recorded": success,
                    "metrics_summary": {
                        "user_satisfaction": satisfaction_score,
                        "key_performance_areas": list(performance_metrics.keys()),
                        "overall_quality": (
                            "high"
                            if effectiveness_score > 0.8
                            else (
                                "medium"
                                if effectiveness_score > 0.6
                                else "needs_improvement"
                            )
                        ),
                    },
                },
                "execution_time": time.time(),
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to track explanation effectiveness: {str(e)}",
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
            }

    def _generate_decision_alternatives(
        self, features: Dict, model_predictions: Dict
    ) -> List[Dict]:
        """Generate alternative scenarios for model decisions."""
        alternatives = []

        # Create simple alternatives based on key features
        key_features = [
            "home_team_offense_yards_per_game",
            "away_team_defense_yards_allowed_per_game",
        ]

        for feature in key_features:
            if feature in features:
                current_value = features[feature]
                if isinstance(current_value, (int, float)):
                    alternative_value = current_value * 1.2  # 20% improvement
                    alternatives.append(
                        {
                            "scenario": f'Increase {feature.replace("_", " ")} by 20%',
                            "expected_impact": "Significant change in prediction likely",
                            "feasibility": "Medium",
                        }
                    )

        return alternatives[:3]  # Return top 3 alternatives

    def _analyze_prediction_differences(self, explanations: List[Dict]) -> List[str]:
        """Analyze key differences between predictions."""
        differences = []

        if len(explanations) < 2:
            return differences

        # Compare confidence levels
        confidences = [exp["explanation"].confidence_level for exp in explanations]
        if max(confidences) - min(confidences) > 0.2:
            differences.append(
                f"Significant confidence difference between predictions ({max(confidences):.1%} vs {min(confidences):.1%})"
            )

        # Compare key factors from evidence
        all_features = set()
        for exp in explanations:
            for component in exp["explanation"].components:
                if component.type == "feature_importance":
                    for evidence in component.evidence:
                        if "feature" in evidence:
                            all_features.add(evidence["feature"])

        differences.append(
            f"Analysis considered {len(all_features)} unique features across all predictions"
        )

        return differences

    def _generate_comparison_recommendation(
        self, explanations: List[Dict], comparison_type: str, context: Dict
    ) -> str:
        """Generate recommendation based on comparison analysis."""

        if not explanations:
            return "Unable to generate recommendation due to insufficient data."

        # Find highest confidence prediction
        best_explanation = max(
            explanations, key=lambda x: x["explanation"].confidence_level
        )

        if comparison_type == "predictions":
            return f"Recommend focusing on {best_explanation['prediction_label']} which has the highest confidence ({best_explanation['explanation'].confidence_level:.1%})."
        else:
            return f"Consider the prediction with highest confidence ({best_explanation['explanation'].confidence_level:.1%}) as the primary guidance."

    def _apply_audience_optimization(
        self, content: str, profile: Dict, detail_level: str
    ) -> str:
        """Apply audience-specific optimizations to content."""
        optimized = content

        # Adjust technical level
        if profile["technical_level"] == "low":
            # Simplify technical terms
            replacements = {
                "statistical significance": "strong evidence",
                "confidence interval": "range of likely outcomes",
                "regression analysis": "trend analysis",
                "feature importance": "key factors",
            }
            for technical, simple in replacements.items():
                optimized = optimized.replace(technical, simple)

        # Adjust detail level
        if detail_level == "low":
            # Keep only main conclusions
            lines = optimized.split("\n")
            essential_lines = [
                line
                for line in lines
                if "Main" in line or "Conclusion" in line or "Key" in line
            ]
            if essential_lines:
                optimized = "\n".join(essential_lines[:3])

        return optimized

    def _calculate_accessibility_score(self, content: str, profile: Dict) -> float:
        """Calculate how accessible the content is for the target audience."""
        base_score = 0.8

        # Check for appropriate language level
        if profile["technical_level"] == "low":
            # Penalize technical jargon
            jargon_terms = [
                "statistical",
                "regression",
                "confidence interval",
                "algorithm",
            ]
            jargon_count = sum(
                1 for term in jargon_terms if term.lower() in content.lower()
            )
            base_score -= min(0.3, jargon_count * 0.1)

        return max(0.1, min(1.0, base_score))

    def _calculate_effectiveness_score(
        self, satisfaction_score: float, performance_metrics: Dict, user_feedback: Dict
    ) -> float:
        """Calculate overall effectiveness score."""

        # Weight different factors
        satisfaction_weight = 0.4
        performance_weight = 0.3
        feedback_weight = 0.3

        # Performance score (simplified)
        if performance_metrics:
            performance_score = min(
                1.0, len(performance_metrics.get("positive_aspects", [])) / 5
            )
        else:
            performance_score = 0.5

        # Feedback quality score
        feedback_text = user_feedback.get("feedback_text", "")
        feedback_quality = (
            min(1.0, len(feedback_text.split()) / 50) if feedback_text else 0.5
        )

        # Calculate weighted average
        effectiveness = (
            satisfaction_score * satisfaction_weight
            + performance_score * performance_weight
            + feedback_quality * feedback_weight
        )

        return max(0.0, min(1.0, effectiveness))

    def _generate_improvement_suggestions(
        self, effectiveness_score: float, user_feedback: Dict, performance_metrics: Dict
    ) -> List[str]:
        """Generate suggestions for improving explanations."""
        suggestions = []

        if effectiveness_score < 0.7:
            suggestions.append("Consider increasing detail level for better clarity")

        if user_feedback.get("satisfaction_score", 0) < 0.6:
            feedback_text = user_feedback.get("feedback_text", "").lower()
            if "confusing" in feedback_text:
                suggestions.append("Simplify technical language and use more analogies")
            if "long" in feedback_text or "wordy" in feedback_text:
                suggestions.append(
                    "Make explanations more concise and focused on key points"
                )
            if "missing" in feedback_text:
                suggestions.append(
                    "Include more context about why predictions were made"
                )

        if not performance_metrics.get("clarity_score", 0):
            suggestions.append("Add more visual elements to improve comprehension")

        if not suggestions:
            suggestions.append(
                "Explanation quality is good - maintain current approach"
            )

        return suggestions[:3]  # Return top 3 suggestions


# Initialize the explanation orchestrator agent
explanation_orchestrator_agent = ExplanationOrchestratorAgent()
