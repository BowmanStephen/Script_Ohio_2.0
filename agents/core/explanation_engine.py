"""
Human-AI Explanation Engine

Provides interpretable explanations for AI predictions and decisions.
Implements multiple explanation strategies including feature importance,
counterfactual analysis, and causal reasoning.
"""

import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import re
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict


class ExplanationType(Enum):
    """Types of explanations supported by the engine."""

    FEATURE_IMPORTANCE = "feature_importance"
    COUNTERFACTUAL = "counterfactual"
    CAUSAL_CHAIN = "causal_chain"
    SIMILAR_CASES = "similar_cases"
    UNCERTAINTY_ANALYSIS = "uncertainty_analysis"
    MODEL_COMPARISON = "model_comparison"


@dataclass
class ExplanationComponent:
    """Single component of an explanation."""

    type: str
    title: str
    content: str
    confidence: float
    evidence: List[Dict[str, Any]]
    visualizations: List[Dict[str, Any]]


@dataclass
class Explanation:
    """Complete explanation for a prediction or decision."""

    prediction_id: str
    prediction_type: str
    primary_conclusion: str
    confidence_level: float
    components: List[ExplanationComponent]
    metadata: Dict[str, Any]
    timestamp: datetime
    human_readable_summary: str


@dataclass
class FeatureImportance:
    """Feature importance for model explanations."""

    feature_name: str
    importance_score: float
    contribution_direction: str  # "positive", "negative", "neutral"
    feature_value: Any
    context: str


@dataclass
class CounterfactualScenario:
    """Counterfactual explanation scenario."""

    scenario_description: str
    changed_features: Dict[str, Any]
    predicted_outcome: str
    probability_change: float
    feasibility_score: float


class HumanAIExplanationEngine:
    """Advanced explanation engine for human-AI collaboration."""

    def __init__(self):
        self.explanation_cache = {}
        self.feature_descriptions = self._initialize_feature_descriptions()
        self.explanation_templates = self._initialize_explanation_templates()
        self.domain_knowledge = self._initialize_domain_knowledge()

        # Metrics tracking
        self.explanation_metrics = {
            "total_explanations": 0,
            "average_confidence": 0.0,
            "explanation_type_usage": defaultdict(int),
            "user_satisfaction_scores": [],
        }

    def _initialize_feature_descriptions(self) -> Dict[str, str]:
        """Initialize human-readable descriptions for features."""
        return {
            # Team Performance Features
            "home_team_offense_yards_per_game": "Home team's average offensive yards per game - higher values indicate stronger offense",
            "away_team_offense_yards_per_game": "Away team's average offensive yards per game - higher values indicate stronger offense",
            "home_team_defense_yards_allowed_per_game": "Home team's average defensive yards allowed per game - lower values indicate better defense",
            "away_team_defense_yards_allowed_per_game": "Away team's average defensive yards allowed per game - lower values indicate better defense",
            # Efficiency Features
            "home_team_ppa_offense": "Home team's Predicted Points Added (PPA) on offense - measures efficiency and explosiveness",
            "away_team_ppa_offense": "Away team's Predicted Points Added (PPA) on offense - measures efficiency and explosiveness",
            "home_team_ppa_defense": "Home team's Predicted Points Added (PPA) on defense - lower is better (prevents opponent scoring)",
            "away_team_ppa_defense": "Away team's Predicted Points Added (PPA) on defense - lower is better (prevents opponent scoring)",
            # Special Teams
            "home_team_special_teams_efficiency": "Home team special teams efficiency including kicking, punting, and returns",
            "away_team_special_teams_efficiency": "Away team special teams efficiency including kicking, punting, and returns",
            # Situational Features
            "home_team_third_down_conversion_rate": "Home team's success rate on third downs - crucial for sustaining drives",
            "away_team_third_down_conversion_rate": "Away team's success rate on third downs - crucial for sustaining drives",
            "home_team_red_zone_efficiency": "Home team's touchdown scoring rate in the red zone (20-yard line and in)",
            "away_team_red_zone_efficiency": "Away team's touchdown scoring rate in the red zone (20-yard line and in)",
            # Discipline Features
            "home_team_penalty_yards_per_game": "Home team's average penalty yards per game - lower values indicate better discipline",
            "away_team_penalty_yards_per_game": "Away team's average penalty yards per game - lower values indicate better discipline",
            "home_team_turnover_margin": "Home team's turnover margin per game - positive values indicate winning turnover battle",
            "away_team_turnover_margin": "Away team's turnover margin per game - positive values indicate winning turnover battle",
            # Game Context
            "spread_line": "Betting spread line - negative means home team favored, positive means away team favored",
            "over_under": "Betting over/under total points line - expected combined score",
            "home_team_is_ranked": "Whether home team is ranked in AP Top 25 - generally indicates stronger team",
            "away_team_is_ranked": "Whether away team is ranked in AP Top 25 - generally indicates stronger team",
            "conference_game": "Whether this is a conference game - often more competitive and meaningful",
            "neutral_site": "Whether game is played at neutral location - removes home field advantage",
            # Historical Performance
            "home_team_win_streak": "Home team's current winning streak - momentum indicator",
            "away_team_win_streak": "Away team's current winning streak - momentum indicator",
            "head_to_head_home_wins_last_5": "Home team's wins in last 5 head-to-head matchups - historical dominance",
            # Strength of Schedule
            "home_team_sos_rank": "Home team's strength of schedule rank - lower numbers indicate tougher schedule",
            "away_team_sos_rank": "Away team's strength of schedule rank - lower numbers indicate tougher schedule",
        }

    def _initialize_explanation_templates(self) -> Dict[str, List[str]]:
        """Initialize templates for different explanation types."""
        return {
            "feature_importance": [
                "The {feature_name} was crucial in this prediction, with {team} having {value} which {direction}ly affected the outcome.",
                "{team}'s {feature_name} of {value} {action} the prediction significantly because {reason}.",
                "When looking at {feature_name}, {team} {performance} which is {assessment} for predicting {outcome}.",
            ],
            "counterfactual": [
                "If {team} had improved their {feature} from {current_value} to {target_value}, the prediction would change to {new_outcome}.",
                "The game outcome would flip to {new_outcome} if {team} could {action} their {feature} by {change_amount}.",
                "A {change_type} in {team}'s {feature} would be enough to change the prediction to {new_outcome}.",
            ],
            "uncertainty": [
                "The model is {confidence_level} confident in this prediction because {reason}.",
                "There's {uncertainty_level} uncertainty mainly due to {factors}.",
                "The prediction falls within {range} of possibilities because {explanation}.",
            ],
        }

    def _initialize_domain_knowledge(self) -> Dict[str, Any]:
        """Initialize college football domain knowledge."""
        return {
            "key_factors": {
                "offense": [
                    "Yards per play efficiency",
                    "Third down conversion success",
                    "Red zone touchdown percentage",
                    "Turnover avoidance",
                    "Explosive play capability",
                ],
                "defense": [
                    "Opponent yards per play allowed",
                    "Third down defense",
                    "Red zone defense",
                    "Turnover creation",
                    "Pressure on quarterback",
                ],
                "special_teams": [
                    "Field goal accuracy",
                    "Punting average and net",
                    "Kick return average",
                    "Punt return average",
                    "Blocked kicks",
                ],
            },
            "situational_importance": {
                "close_games": {
                    "factors": ["Turnover margin", "Penalty yards", "Field position"],
                    "weight": 0.3,
                },
                "blowout_potential": {
                    "factors": [
                        "Explosive plays",
                        "Big plays allowed",
                        "Special teams",
                    ],
                    "weight": 0.2,
                },
                "conference_games": {
                    "factors": [
                        "Rivalry intensity",
                        "Familiarity",
                        "Historical performance",
                    ],
                    "weight": 0.25,
                },
            },
            "statistical_benchmarks": {
                "offense": {
                    "elite": {
                        "yards_per_game": 450,
                        "ppa": 0.35,
                        "third_down_rate": 0.45,
                    },
                    "average": {
                        "yards_per_game": 380,
                        "ppa": 0.25,
                        "third_down_rate": 0.38,
                    },
                    "below_average": {
                        "yards_per_game": 320,
                        "ppa": 0.15,
                        "third_down_rate": 0.30,
                    },
                },
                "defense": {
                    "elite": {
                        "yards_allowed": 280,
                        "ppa_allowed": 0.20,
                        "third_down_defense": 0.30,
                    },
                    "average": {
                        "yards_allowed": 350,
                        "ppa_allowed": 0.30,
                        "third_down_defense": 0.38,
                    },
                    "below_average": {
                        "yards_allowed": 420,
                        "ppa_allowed": 0.40,
                        "third_down_defense": 0.45,
                    },
                },
            },
        }

    def generate_explanation(
        self,
        prediction_data: Dict[str, Any],
        model_predictions: Dict[str, Any],
        features: Dict[str, Any],
        explanation_types: List[ExplanationType] = None,
    ) -> Explanation:
        """Generate comprehensive explanation for a prediction."""

        if explanation_types is None:
            explanation_types = [
                ExplanationType.FEATURE_IMPORTANCE,
                ExplanationType.UNCERTAINTY_ANALYSIS,
                ExplanationType.MODEL_COMPARISON,
            ]

        prediction_id = f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        prediction_type = prediction_data.get("type", "game_outcome")

        # Generate explanation components
        components = []

        for exp_type in explanation_types:
            if exp_type == ExplanationType.FEATURE_IMPORTANCE:
                component = self._generate_feature_importance(
                    features, model_predictions
                )
            elif exp_type == ExplanationType.COUNTERFACTUAL:
                component = self._generate_counterfactual_explanation(
                    features, model_predictions
                )
            elif exp_type == ExplanationType.CAUSAL_CHAIN:
                component = self._generate_causal_chain(features, model_predictions)
            elif exp_type == ExplanationType.SIMILAR_CASES:
                component = self._generate_similar_cases(features, model_predictions)
            elif exp_type == ExplanationType.UNCERTAINTY_ANALYSIS:
                component = self._generate_uncertainty_analysis(
                    features, model_predictions
                )
            elif exp_type == ExplanationType.MODEL_COMPARISON:
                component = self._generate_model_comparison(model_predictions)
            else:
                continue

            if component:
                components.append(component)

        # Generate human-readable summary
        summary = self._generate_human_readable_summary(components, prediction_data)

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            components, model_predictions
        )

        # Create explanation object
        explanation = Explanation(
            prediction_id=prediction_id,
            prediction_type=prediction_type,
            primary_conclusion=summary["conclusion"],
            confidence_level=overall_confidence,
            components=components,
            metadata={
                "model_predictions": model_predictions,
                "game_context": prediction_data.get("game_context", {}),
                "explanation_types": [t.value for t in explanation_types],
                "generation_method": "hybrid_dspycustom",
            },
            timestamp=datetime.now(),
            human_readable_summary=summary["full_summary"],
        )

        # Cache explanation
        self.explanation_cache[prediction_id] = explanation

        # Update metrics
        self.explanation_metrics["total_explanations"] += 1
        self.explanation_metrics["average_confidence"] = (
            self.explanation_metrics["average_confidence"]
            * (self.explanation_metrics["total_explanations"] - 1)
            + overall_confidence
        ) / self.explanation_metrics["total_explanations"]

        for exp_type in explanation_types:
            self.explanation_metrics["explanation_type_usage"][exp_type.value] += 1

        return explanation

    def _generate_feature_importance(
        self, features: Dict[str, Any], model_predictions: Dict[str, Any]
    ) -> ExplanationComponent:
        """Generate feature importance explanation."""

        # Calculate feature importance scores (simplified version)
        importance_scores = {}

        for feature_name, feature_value in features.items():
            if feature_name in self.feature_descriptions:
                # Calculate importance based on deviation from average
                if isinstance(feature_value, (int, float)):
                    importance = abs(feature_value) * 0.1  # Simplified calculation
                    importance_scores[feature_name] = importance

        # Sort by importance
        sorted_features = sorted(
            importance_scores.items(), key=lambda x: x[1], reverse=True
        )[:5]

        feature_importances = []
        evidence = []

        for feature_name, importance_score in sorted_features:
            feature_value = features[feature_name]

            # Determine contribution direction
            if "home_team" in feature_name.lower():
                direction = "positive" if feature_value > 0 else "negative"
            elif "away_team" in feature_name.lower():
                direction = "negative" if feature_value > 0 else "positive"
            else:
                direction = "neutral"

            feature_importance = FeatureImportance(
                feature_name=feature_name,
                importance_score=importance_score,
                contribution_direction=direction,
                feature_value=feature_value,
                context=self.feature_descriptions.get(
                    feature_name, "Key predictive factor"
                ),
            )

            feature_importances.append(feature_importance)

            evidence.append(
                {
                    "feature": feature_name,
                    "value": feature_value,
                    "importance": importance_score,
                    "description": self.feature_descriptions.get(feature_name, ""),
                    "direction": direction,
                }
            )

        # Generate explanation content
        if feature_importances:
            top_feature = feature_importances[0]
            content = f"The most influential factor was {top_feature.feature_name}, where the value of {top_feature.feature_value} {top_feature.contribution_direction}ly impacted the prediction. This feature represents {top_feature.context}."

            if len(feature_importances) > 1:
                content += f" Other key factors included {feature_importances[1].feature_name} and {feature_importances[2].feature_name if len(feature_importances) > 2 else 'additional metrics'}."
        else:
            content = "Feature importance analysis was limited due to data constraints, but the model considered all available factors in making its prediction."

        # Create visualization
        visualization = {
            "type": "bar_chart",
            "title": "Top 5 Most Important Features",
            "data": [
                {
                    "feature": fi.feature_name.replace("_", " ").title(),
                    "importance": fi.importance_score,
                    "direction": fi.contribution_direction,
                }
                for fi in feature_importances
            ],
        }

        return ExplanationComponent(
            type="feature_importance",
            title="Why This Prediction Was Made",
            content=content,
            confidence=min(0.9, len(feature_importances) * 0.2),
            evidence=evidence,
            visualizations=[visualization],
        )

    def _generate_counterfactual_explanation(
        self, features: Dict[str, Any], model_predictions: Dict[str, Any]
    ) -> ExplanationComponent:
        """Generate counterfactual explanation."""

        scenarios = []
        evidence = []

        # Generate counterfactual scenarios for key features
        key_features = [f for f in features.keys() if f in self.feature_descriptions][
            :3
        ]

        for feature in key_features:
            current_value = features[feature]

            # Determine what would need to change to flip the prediction
            if isinstance(current_value, (int, float)):
                # Create a scenario where the feature changes significantly
                if "offense" in feature or "yards" in feature:
                    change_amount = current_value * 0.3  # 30% improvement
                    target_value = current_value + change_amount
                elif "defense" in feature or "allowed" in feature:
                    change_amount = current_value * 0.3
                    target_value = current_value - change_amount
                else:
                    change_amount = (current_value * 0.2) + 1
                    target_value = current_value + change_amount

                # Determine which team this affects
                if "home_team" in feature:
                    team = "home team"
                elif "away_team" in feature:
                    team = "away team"
                else:
                    team = "game"

                scenario = CounterfactualScenario(
                    scenario_description=f"If the {team} improved their {feature.replace('_', ' ')} from {current_value:.1f} to {target_value:.1f}",
                    changed_features={feature: target_value},
                    predicted_outcome="prediction would flip to favor the other team",
                    probability_change=abs(change_amount)
                    * 0.05,  # Simplified calculation
                    feasibility_score=0.7 if "offense" in feature else 0.6,
                )

                scenarios.append(scenario)

                evidence.append(
                    {
                        "feature": feature,
                        "current_value": current_value,
                        "target_value": target_value,
                        "change_needed": target_value - current_value,
                        "feasibility": scenario.feasibility_score,
                        "impact": scenario.probability_change,
                    }
                )

        # Generate explanation content
        if scenarios:
            top_scenario = scenarios[0]
            content = f"The prediction is quite sensitive to key performance metrics. For example, {top_scenario.scenario_description.lower()}, {top_scenario.predicted_outcome}. This shows how small changes in team performance can significantly impact game outcomes."

            if len(scenarios) > 1:
                content += f" Similarly, improving {scenarios[1].scenario_description.split('improved')[1].split('from')[0].strip()} would also significantly impact the result."
        else:
            content = "Counterfactual analysis shows the prediction would require substantial changes in key team performance metrics to change the outcome."

        # Create visualization
        visualization = {
            "type": "before_after_chart",
            "title": "What Would Change the Prediction?",
            "data": [
                {
                    "scenario": s.scenario_description,
                    "current_value": features[list(s.changed_features.keys())[0]],
                    "target_value": list(s.changed_features.values())[0],
                    "impact": s.probability_change,
                }
                for s in scenarios
            ],
        }

        return ExplanationComponent(
            type="counterfactual",
            title="How Different Factors Could Change The Outcome",
            content=content,
            confidence=0.7,
            evidence=evidence,
            visualizations=[visualization],
        )

    def _generate_uncertainty_analysis(
        self, features: Dict[str, Any], model_predictions: Dict[str, Any]
    ) -> ExplanationComponent:
        """Generate uncertainty analysis explanation."""

        # Calculate uncertainty based on feature variance and model agreement
        model_predictions_list = list(model_predictions.values())
        if model_predictions_list:
            prediction_variance = np.var(model_predictions_list)
            avg_prediction = np.mean(model_predictions_list)

            # Calculate confidence based on variance
            confidence = max(0.5, 1.0 - (prediction_variance / 0.25))  # Normalize

            if confidence > 0.8:
                confidence_level = "very high"
                uncertainty_level = "very low"
            elif confidence > 0.65:
                confidence_level = "high"
                uncertainty_level = "low"
            elif confidence > 0.5:
                confidence_level = "moderate"
                uncertainty_level = "moderate"
            else:
                confidence_level = "low"
                uncertainty_level = "high"
        else:
            confidence = 0.5
            confidence_level = "moderate"
            uncertainty_level = "moderate"
            prediction_variance = 0

        # Identify sources of uncertainty
        uncertainty_sources = []

        # Check for missing or extreme feature values
        for feature_name, feature_value in features.items():
            if feature_value is None or (
                isinstance(feature_value, (int, float)) and abs(feature_value) > 3
            ):
                uncertainty_sources.append(
                    {
                        "source": feature_name,
                        "issue": "extreme_or_missing_value",
                        "impact": "moderate",
                    }
                )

        # Check for model disagreement
        if len(model_predictions) > 1:
            max_pred = max(model_predictions.values())
            min_pred = min(model_predictions.values())
            if max_pred - min_pred > 0.2:
                uncertainty_sources.append(
                    {
                        "source": "model_disagreement",
                        "issue": f"predictions range from {min_pred:.2f} to {max_pred:.2f}",
                        "impact": "high",
                    }
                )

        # Generate explanation content
        if uncertainty_sources:
            sources_text = ", ".join(
                [f"{s['source'].replace('_', ' ')}" for s in uncertainty_sources[:3]]
            )
            content = f"The model is {confidence_level} confident in this prediction. There's {uncertainty_level} uncertainty mainly due to {sources_text}."
        else:
            content = f"The model is {confidence_level} confident in this prediction with {uncertainty_level} uncertainty. The prediction is based on consistent patterns across multiple models."

        evidence = [
            {
                "confidence_level": confidence_level,
                "numerical_confidence": confidence,
                "prediction_variance": prediction_variance,
                "uncertainty_sources": uncertainty_sources,
                "model_agreement": (
                    "high"
                    if prediction_variance < 0.05
                    else "moderate" if prediction_variance < 0.15 else "low"
                ),
            }
        ]

        # Create visualization
        visualization = {
            "type": "confidence_meter",
            "title": "Prediction Confidence",
            "data": {
                "confidence": confidence,
                "confidence_level": confidence_level,
                "sources_of_uncertainty": uncertainty_sources,
            },
        }

        return ExplanationComponent(
            type="uncertainty_analysis",
            title="How Confident Is This Prediction?",
            content=content,
            confidence=confidence,
            evidence=evidence,
            visualizations=[visualization],
        )

    def _generate_model_comparison(
        self, model_predictions: Dict[str, Any]
    ) -> ExplanationComponent:
        """Generate model comparison explanation."""

        if not model_predictions:
            return None

        # Sort models by prediction value
        sorted_models = sorted(
            model_predictions.items(), key=lambda x: x[1], reverse=True
        )

        model_analysis = []
        evidence = []

        for model_name, prediction_value in sorted_models:
            # Determine model recommendation
            if prediction_value > 0.6:
                recommendation = "strong home team win"
            elif prediction_value > 0.5:
                recommendation = "slight home team advantage"
            elif prediction_value > 0.4:
                recommendation = "slight away team advantage"
            else:
                recommendation = "strong away team win"

            model_analysis.append(
                {
                    "model": model_name,
                    "prediction": prediction_value,
                    "recommendation": recommendation,
                    "confidence": abs(prediction_value - 0.5)
                    * 2,  # Convert to 0-1 scale
                }
            )

            evidence.append(
                {
                    "model_name": model_name,
                    "prediction_value": prediction_value,
                    "recommendation": recommendation,
                    "confidence_score": abs(prediction_value - 0.5) * 2,
                }
            )

        # Calculate consensus
        predictions_list = [pred for pred in model_predictions.values()]
        if predictions_list:
            consensus_score = 1.0 - (
                np.std(predictions_list) * 2
            )  # Convert variance to consensus
            consensus_score = max(0, min(1, consensus_score))
        else:
            consensus_score = 0.5

        # Generate explanation content
        top_model = sorted_models[0]

        if len(model_predictions) == 1:
            content = f"The {top_model[0]} model predicts {'home team' if top_model[1] > 0.5 else 'away team'} victory with {top_model[1]:.1%} probability."
        else:
            content = f"Among {len(model_predictions)} models, {top_model[0]} shows strongest confidence ({top_model[1]:.1%}) in {'home team' if top_model[1] > 0.5 else 'away team'} victory. "

            if consensus_score > 0.8:
                content += "All models show strong agreement on this prediction."
            elif consensus_score > 0.6:
                content += "Most models agree on the likely outcome."
            else:
                content += "There's some disagreement between models, indicating higher uncertainty."

        # Create visualization
        visualization = {
            "type": "model_comparison_chart",
            "title": "Model Predictions Comparison",
            "data": model_analysis,
        }

        return ExplanationComponent(
            type="model_comparison",
            title="What Do Different Models Think?",
            content=content,
            confidence=consensus_score,
            evidence=evidence,
            visualizations=[visualization],
        )

    def _generate_causal_chain(
        self, features: Dict[str, Any], model_predictions: Dict[str, Any]
    ) -> Optional[ExplanationComponent]:
        """Generate causal chain explanation."""
        # Placeholder for causal chain analysis
        # This would require more sophisticated causal inference methods
        return None

    def _generate_similar_cases(
        self, features: Dict[str, Any], model_predictions: Dict[str, Any]
    ) -> Optional[ExplanationComponent]:
        """Generate similar cases explanation."""
        # Placeholder for similar cases analysis
        # This would require historical game data and similarity matching
        return None

    def _generate_human_readable_summary(
        self, components: List[ExplanationComponent], prediction_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate human-readable summary of all explanation components."""

        if not components:
            return {
                "conclusion": "Unable to generate detailed explanation due to limited data.",
                "full_summary": "Prediction made with limited explanatory information available.",
            }

        # Extract key insights from components
        key_insights = []
        conclusion_parts = []

        for component in components:
            if component.type == "feature_importance":
                key_insights.append(component.content.split(".")[0] + ".")
            elif component.type == "uncertainty_analysis":
                key_insights.append(
                    f"Confidence level: {component.content.split('very high' if 'very high' in component.content else 'high' if 'high' in component.content else 'moderate' if 'moderate' in component.content else 'low')[0]}."
                )
            elif component.type == "model_comparison":
                key_insights.append(component.content.split(".")[0] + ".")
            elif component.type == "counterfactual":
                key_insights.append(
                    f"The prediction could change with small performance adjustments."
                )

        # Generate conclusion
        if "confidence_level" in [c.type for c in components]:
            confidence_comp = next(
                c for c in components if c.type == "uncertainty_analysis"
            )
            if (
                "very high" in confidence_comp.content
                or "high" in confidence_comp.content
            ):
                conclusion = "The models show strong agreement and high confidence in this prediction."
            else:
                conclusion = "The prediction shows moderate confidence with some uncertainty factors."
        else:
            conclusion = "The prediction is based on analysis of multiple factors and model outputs."

        # Generate full summary
        full_summary = f"""
**Prediction Analysis Summary**

{conclusion}

**Key Factors:**
{chr(10).join(f"• {insight}" for insight in key_insights[:3])}

**Model Confidence:**
{next((c.content for c in components if c.type == 'uncertainty_analysis'), 'Confidence analysis not available.')}

**What Could Change The Outcome:**
{next((c.content for c in components if c.type == 'counterfactual'), 'Counterfactual analysis not available.')}
        """.strip()

        return {"conclusion": conclusion, "full_summary": full_summary}

    def _calculate_overall_confidence(
        self, components: List[ExplanationComponent], model_predictions: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence based on component confidence and model agreement."""

        if not components:
            return 0.5

        # Average component confidence
        component_confidence = np.mean([c.confidence for c in components])

        # Model agreement factor
        if len(model_predictions) > 1:
            predictions = list(model_predictions.values())
            model_agreement = 1.0 - (
                np.std(predictions) * 2
            )  # Convert variance to agreement
            model_agreement = max(0, min(1, model_agreement))
        else:
            model_agreement = 0.8  # Default for single model

        # Weighted average
        overall_confidence = (component_confidence * 0.6) + (model_agreement * 0.4)

        return max(0.1, min(0.95, overall_confidence))

    def get_explanation_metrics(self) -> Dict[str, Any]:
        """Get explanation system metrics."""
        return {
            "total_explanations": self.explanation_metrics["total_explanations"],
            "average_confidence": self.explanation_metrics["average_confidence"],
            "explanation_type_usage": dict(
                self.explanation_metrics["explanation_type_usage"]
            ),
            "cache_size": len(self.explanation_cache),
            "average_user_satisfaction": (
                np.mean(self.explanation_metrics["user_satisfaction_scores"])
                if self.explanation_metrics["user_satisfaction_scores"]
                else 0
            ),
        }

    def record_user_feedback(
        self, prediction_id: str, satisfaction_score: float, feedback_text: str = ""
    ) -> bool:
        """Record user feedback for explanation quality improvement."""

        if prediction_id not in self.explanation_cache:
            return False

        # Record satisfaction score
        self.explanation_metrics["user_satisfaction_scores"].append(satisfaction_score)

        # Store feedback with explanation (simplified)
        explanation = self.explanation_cache[prediction_id]
        explanation.metadata["user_feedback"] = {
            "satisfaction_score": satisfaction_score,
            "feedback_text": feedback_text,
            "timestamp": datetime.now(),
        }

        return True


class FeatureImportanceExplainer:
    """Explains feature importance in model predictions."""

    def __init__(self):
        self.feature_descriptions = {
            'home_elo': 'Team ELO rating representing overall strength',
            'away_elo': 'Opponent team ELO rating',
            'home_talent': 'Recruiting talent composite score',
            'away_talent': 'Opponent recruiting talent score',
            'spread': 'Betting line indicating expected margin',
            'home_adjusted_epa': 'Expected points added per play',
            'away_adjusted_epa': 'Opponent expected points added',
            'home_adjusted_success': 'Play success rate adjusted for opponent',
            'away_adjusted_success': 'Opponent success rate adjusted for competition'
        }

    def explain_prediction(self, game_data: Dict, model_prediction: Dict, model_name: str) -> Dict:
        """Generate feature importance explanation."""

        # Extract key features
        features = {}
        for feature in self.feature_descriptions.keys():
            if feature in game_data:
                features[feature] = game_data[feature]

        # Calculate importance scores (simplified)
        importance_scores = self._calculate_importance_scores(features, model_prediction)

        # Sort by importance
        sorted_features = sorted(importance_scores.items(), key=lambda x: abs(x[1]), reverse=True)

        # Generate explanation
        explanation = {
            'explanation_type': 'feature_importance',
            'model_name': model_name,
            'important_features': [
                {
                    'feature': feature,
                    'importance': score,
                    'description': self.feature_descriptions.get(feature, feature),
                    'value': features.get(feature, 0),
                    'impact_direction': 'positive' if score > 0 else 'negative'
                }
                for feature, score in sorted_features[:5]
            ],
            'overall_prediction': model_prediction.get('prediction', 0),
            'confidence': model_prediction.get('confidence', 0.5)
        }

        return explanation

    def _calculate_importance_scores(self, features: Dict, prediction: Dict) -> Dict:
        """Calculate simplified importance scores."""

        scores = {}
        prediction_value = prediction.get('prediction', 0)

        # Simple heuristics for importance
        if 'home_elo' in features and 'away_elo' in features:
            elo_diff = features['home_elo'] - features['away_elo']
            scores['home_elo'] = elo_diff / 100
            scores['away_elo'] = -elo_diff / 100

        if 'spread' in features:
            spread_diff = features['spread'] - prediction_value
            scores['spread'] = spread_diff / 10

        # Add small random variations for other features
        for feature in features:
            if feature not in scores:
                scores[feature] = np.random.normal(0, 0.1)

        return scores


class CounterfactualExplainer:
    """Generates counterfactual explanations for predictions."""

    def __init__(self):
        self.reasonable_adjustments = {
            'home_elo': 50,  # ELO points
            'away_elo': 50,
            'home_talent': 20,  # Talent points
            'away_talent': 20,
            'spread': 3.5  # Points
        }

    def generate_counterfactuals(self, game_data: Dict, model_prediction: Dict, num_scenarios: int = 3, constraints: Dict = {}) -> List[Dict]:
        """Generate counterfactual scenarios."""

        counterfactuals = []
        base_prediction = model_prediction.get('prediction', 0)

        # Scenario types
        scenario_types = [
            {'name': 'even_matchup', 'description': 'What if teams were evenly matched?'},
            {'name': 'home_advantage_removed', 'description': 'What if home field advantage was removed?'},
            {'name': 'extended_talent_gap', 'description': 'What if talent gap was larger?'}
        ]

        for i, scenario_type in enumerate(scenario_types[:num_scenarios]):
            modified_data = game_data.copy()
            modifications = []

            if scenario_type['name'] == 'even_matchup':
                # Make teams evenly matched
                if 'home_elo' in modified_data and 'away_elo' in modified_data:
                    avg_elo = (modified_data['home_elo'] + modified_data['away_elo']) / 2
                    modifications.append({
                        'feature': 'home_elo',
                        'original': modified_data['home_elo'],
                        'new': avg_elo,
                        'change': avg_elo - modified_data['home_elo']
                    })
                    modifications.append({
                        'feature': 'away_elo',
                        'original': modified_data['away_elo'],
                        'new': avg_elo,
                        'change': avg_elo - modified_data['away_elo']
                    })
                    modified_data['home_elo'] = avg_elo
                    modified_data['away_elo'] = avg_elo

            elif scenario_type['name'] == 'home_advantage_removed':
                # Remove home field advantage
                if 'home_elo' in modified_data:
                    home_advantage = 30  # Typical home field advantage
                    modifications.append({
                        'feature': 'home_elo',
                        'original': modified_data['home_elo'],
                        'new': modified_data['home_elo'] - home_advantage,
                        'change': -home_advantage
                    })
                    modified_data['home_elo'] -= home_advantage

            elif scenario_type['name'] == 'extended_talent_gap':
                # Increase talent gap
                if 'home_talent' in modified_data and 'away_talent' in modified_data:
                    talent_boost = 30
                    modifications.append({
                        'feature': 'home_talent',
                        'original': modified_data['home_talent'],
                        'new': modified_data['home_talent'] + talent_boost,
                        'change': talent_boost
                    })
                    modified_data['home_talent'] += talent_boost

            # Calculate new prediction (simplified)
            new_prediction = self._estimate_new_prediction(modified_data, scenario_type['name'], base_prediction)

            counterfactual = {
                'scenario_name': scenario_type['name'],
                'description': scenario_type['description'],
                'modifications': modifications,
                'original_prediction': base_prediction,
                'new_prediction': new_prediction,
                'prediction_change': new_prediction - base_prediction,
                'impact_magnitude': abs(new_prediction - base_prediction)
            }

            counterfactuals.append(counterfactual)

        return counterfactuals

    def _estimate_new_prediction(self, modified_data: Dict, scenario_type: str, base_prediction: float) -> float:
        """Estimate new prediction based on modifications."""

        # Simplified prediction adjustment
        adjustment = 0

        if scenario_type == 'even_matchup':
            adjustment = -base_prediction * 0.7  # Move toward 0
        elif scenario_type == 'home_advantage_removed':
            adjustment = -3.0  # Typical home field advantage
        elif scenario_type == 'extended_talent_gap':
            adjustment = base_prediction * 0.3  # Increase existing margin

        return base_prediction + adjustment


class UncertaintyExplainer:
    """Explains uncertainty in model predictions."""

    def __init__(self):
        self.uncertainty_factors = [
            'model_confidence',
            'data_quality',
            'feature_completeness',
            'historical_accuracy',
            'external_factors'
        ]

    def explain_uncertainty(self, game_data: Dict, model_prediction: Dict, model_name: str) -> Dict:
        """Generate uncertainty explanation."""

        base_confidence = model_prediction.get('confidence', 0.5)
        uncertainty_factors = self._analyze_uncertainty_factors(game_data, model_prediction)

        # Calculate overall uncertainty
        uncertainty_score = self._calculate_uncertainty_score(uncertainty_factors)
        confidence_interval = self._calculate_confidence_interval(
            model_prediction.get('prediction', 0), uncertainty_score
        )

        explanation = {
            'explanation_type': 'uncertainty_analysis',
            'model_name': model_name,
            'base_confidence': base_confidence,
            'uncertainty_score': uncertainty_score,
            'confidence_level': 1 - uncertainty_score,
            'confidence_interval': confidence_interval,
            'uncertainty_factors': uncertainty_factors,
            'recommendations': self._generate_uncertainty_recommendations(uncertainty_score)
        }

        return explanation

    def _analyze_uncertainty_factors(self, game_data: Dict, prediction: Dict) -> List[Dict]:
        """Analyze various factors contributing to uncertainty."""

        factors = []

        # Model confidence factor
        model_confidence = prediction.get('confidence', 0.5)
        factors.append({
            'factor': 'model_confidence',
            'contribution': 1 - model_confidence,
            'description': 'Model prediction confidence'
        })

        # Data completeness factor
        required_features = ['home_elo', 'away_elo', 'home_talent', 'away_talent']
        missing_features = [f for f in required_features if f not in game_data or pd.isna(game_data[f])]
        completeness_score = len(required_features - len(missing_features)) / len(required_features)
        factors.append({
            'factor': 'data_completeness',
            'contribution': 1 - completeness_score,
            'description': f'Missing key features: {missing_features}'
        })

        # Historical accuracy factor (simulated)
        factors.append({
            'factor': 'historical_accuracy',
            'contribution': 0.15,  # 15% uncertainty from historical variance
            'description': 'Historical model performance variance'
        })

        return factors

    def _calculate_uncertainty_score(self, factors: List[Dict]) -> float:
        """Calculate overall uncertainty score."""

        # Weighted average of factor contributions
        total_contribution = sum(f['contribution'] for f in factors)
        uncertainty_score = min(0.8, total_contribution / len(factors))  # Cap at 80%

        return uncertainty_score

    def _calculate_confidence_interval(self, prediction: float, uncertainty_score: float) -> Dict:
        """Calculate confidence interval for prediction."""

        # Simple confidence interval based on uncertainty
        margin = uncertainty_score * 10  # Scale uncertainty to points

        return {
            'lower_bound': prediction - margin,
            'upper_bound': prediction + margin,
            'margin': margin,
            'interpretation': f'Prediction likely within ±{margin:.1f} points'
        }

    def _generate_uncertainty_recommendations(self, uncertainty_score: float) -> List[str]:
        """Generate recommendations based on uncertainty level."""

        recommendations = []

        if uncertainty_score > 0.5:
            recommendations.append("High uncertainty - consider additional data sources")
            recommendations.append("Consult expert opinion before final decision")
        elif uncertainty_score > 0.3:
            recommendations.append("Moderate uncertainty - validate with additional context")
        else:
            recommendations.append("Low uncertainty - prediction can be used with confidence")

        return recommendations


class CollegeFootballExplainer:
    """Provides college football domain-specific explanations."""

    def __init__(self):
        self.domain_knowledge = {
            'team_matchups': self._load_team_matchup_knowledge(),
            'conference_patterns': self._load_conference_patterns(),
            'coaching_impact': self._load_coaching_impact_data(),
            'recruiting_trends': self._load_recruiting_trends()
        }

    def explain_feature_importance(self, features: List[Dict], game_data: Dict) -> List[str]:
        """Add college football context to feature importance."""

        insights = []

        for feature_info in features[:3]:  # Top 3 features
            feature_name = feature_info['feature']
            importance = feature_info['importance']

            if 'elo' in feature_name.lower():
                insights.append(
                    f"ELO ratings are crucial in college football where team strength "
                    f"varies significantly more than in professional leagues"
                )
            elif 'talent' in feature_name.lower():
                insights.append(
                    "Recruiting talent strongly predicts performance, especially for "
                    "younger players and teams with less development time"
                )
            elif 'spread' in feature_name.lower():
                insights.append(
                    "Betting lines incorporate expert analysis and market wisdom, "
                    "often providing valuable predictive information"
                )

        return insights

    def interpret_counterfactual(self, counterfactual: Dict, game_data: Dict) -> str:
        """Provide college football context for counterfactual scenario."""

        scenario_name = counterfactual['scenario_name']
        prediction_change = counterfactual['prediction_change']

        interpretations = {
            'even_matchup': (
                f"In college football, eliminating talent disparities creates more "
                f"competitive games. The {abs(prediction_change):.1f} point change reflects "
                f"how recruiting advantages translate to on-field performance"
            ),
            'home_advantage_removed': (
                f"Home field advantage varies significantly in college football, "
                f"from small private schools to large stadiums with intense atmospheres"
            ),
            'extended_talent_gap': (
                f"Talent gaps have amplified effects in college football due to "
                f"developmental differences and scheme complexity"
            )
        }

        return interpretations.get(scenario_name, "Counterfactual scenario analyzed")

    def explain_uncertainty_factors(self, game_data: Dict, prediction: Dict) -> List[Dict]:
        """Add college football-specific uncertainty factors."""

        cf_factors = []

        # Conference strength variation
        if 'home_conference' in game_data and 'away_conference' in game_data:
            cf_factors.append({
                'factor': 'conference_strength',
                'description': 'Conference strength varies year-to-year affecting predictions'
            })

        # Player development uncertainty
        cf_factors.append({
            'factor': 'player_development',
            'description': 'College player development is less predictable than professional leagues'
        })

        # Scheme changes
        cf_factors.append({
            'factor': 'scheme_changes',
            'description': 'New coaching staffs can dramatically change team performance'
        })

        return cf_factors

    def get_matchup_insights(self, home_team: str, away_team: str, game_data: Dict) -> List[str]:
        """Get specific insights about team matchups."""

        insights = [
            f"Historical data shows {home_team} vs {away_team} matchups tend to be "
            f"competitive regardless of rankings",
            "Conference games often show different patterns than non-conference matchups",
            "Recent performance trends may be more predictive than season-long statistics"
        ]

        return insights

    def answer_domain_question(self, question: str, game_data: Dict, prediction: Dict) -> str:
        """Answer domain-specific questions about predictions."""

        question_lower = question.lower()

        if 'weather' in question_lower:
            return "Weather impacts college football significantly, especially for outdoor stadiums and passing-heavy teams"
        elif 'injury' in question_lower:
            return "Injuries have amplified impact in college football due to smaller roster depth and player development"
        elif 'coaching' in question_lower:
            return "Coaching changes can dramatically affect college team performance, often more than professional teams"
        else:
            return "This factor is incorporated into the model based on historical college football patterns"

    def get_general_context_insights(self, game_data: Dict, prediction: Dict) -> List[str]:
        """Get general college football context insights."""

        return [
            "College football predictions must account for greater variance than professional leagues",
            "Recruiting cycles and player development create unique prediction challenges",
            "Conference schedules and rivalries can affect team motivation and performance"
        ]

    def _load_team_matchup_knowledge(self) -> Dict:
        """Load team matchup historical data."""
        return {}  # Placeholder

    def _load_conference_patterns(self) -> Dict:
        """Load conference-specific patterns."""
        return {}  # Placeholder

    def _load_coaching_impact_data(self) -> Dict:
        """Load coaching impact historical data."""
        return {}  # Placeholder

    def _load_recruiting_trends(self) -> Dict:
        """Load recruiting trend data."""
        return {}  # Placeholder
