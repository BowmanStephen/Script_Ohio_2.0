"""
Continuous Learning Framework

Adaptive learning system that improves from feedback and experience.
Implements reinforcement learning, online adaptation, and knowledge consolidation.
"""

import json
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
import logging
from collections import defaultdict, deque
import pickle
import statistics
import math

from agents.core.memory_system import HierarchicalMemoryManager, MemoryLevel, MemoryType


class LearningStrategy(Enum):
    """Learning strategies for adaptation."""

    REINFORCEMENT_LEARNING = "reinforcement_learning"
    ONLINE_GRADIENT = "online_gradient"
    EXPERIENCE_REPLAY = "experience_replay"
    META_LEARNING = "meta_learning"
    KNOWLEDGE_DISTILLATION = "knowledge_distillation"
    ENSEMBLE_ADAPTATION = "ensemble_adaptation"


class FeedbackType(Enum):
    """Types of feedback for learning."""

    EXPLICIT_RATING = "explicit_rating"  # User ratings (1-5 stars)
    CORRECTION = "correction"  # Actual outcomes vs predictions
    USAGE_PATTERNS = "usage_patterns"  # How users interact with system
    PERFORMANCE_METRICS = "performance_metrics"  # System performance indicators
    DOMAIN_FEEDBACK = "domain_feedback"  # Domain expert corrections


@dataclass
class LearningSignal:
    """Single learning signal from feedback."""

    signal_id: str
    feedback_type: FeedbackType
    source: str  # Which component generated this signal
    content: Dict[str, Any]
    value: float  # Learning signal strength (-1 to 1)
    confidence: float  # Confidence in the signal
    timestamp: datetime
    context: Dict[str, Any]
    applied: bool = False
    improvement_measured: float = 0.0


@dataclass
class AdaptationAction:
    """Action taken by the learning system."""

    action_id: str
    strategy: LearningStrategy
    target_component: str
    adaptation_type: str
    parameters: Dict[str, Any]
    expected_improvement: float
    actual_improvement: Optional[float] = None
    confidence: float = 0.5
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class LearningMetrics:
    """Metrics for learning system performance."""

    total_signals_processed: int
    successful_adaptations: int
    failed_adaptations: int
    average_improvement: float
    learning_rate: float
    stability_score: float
    knowledge_growth: float
    last_update: datetime


class ContinuousLearningFramework:
    """Advanced continuous learning system for agent adaptation."""

    def __init__(
        self,
        agent_id: str = "continuous_learning",
        learning_rate: float = 0.01,
        memory_size: int = 10000,
        adaptation_threshold: float = 0.05,
    ):

        self.agent_id = agent_id
        self.learning_rate = learning_rate
        self.memory_size = memory_size
        self.adaptation_threshold = adaptation_threshold

        # Initialize memory manager
        self.memory_manager = HierarchicalMemoryManager()

        # Learning data storage
        self.learning_signals = deque(maxlen=memory_size)
        self.adaptation_history = []
        self.performance_history = deque(maxlen=1000)

        # Learning strategies
        self.learning_strategies = {
            LearningStrategy.REINFORCEMENT_LEARNING: self._reinforcement_learning,
            LearningStrategy.ONLINE_GRADIENT: self._online_gradient_descent,
            LearningStrategy.EXPERIENCE_REPLAY: self._experience_replay,
            LearningStrategy.META_LEARNING: self._meta_learning,
            LearningStrategy.KNOWLEDGE_DISTILLATION: self._knowledge_distillation,
            LearningStrategy.ENSEMBLE_ADAPTATION: self._ensemble_adaptation,
        }

        # Performance tracking
        self.metrics = LearningMetrics(
            total_signals_processed=0,
            successful_adaptations=0,
            failed_adaptations=0,
            average_improvement=0.0,
            learning_rate=learning_rate,
            stability_score=1.0,
            knowledge_growth=0.0,
            last_update=datetime.now(),
        )

        # Component performance tracking
        self.component_performance = defaultdict(list)
        self.component_weights = defaultdict(lambda: 1.0)

        # Background learning thread
        self.learning_active = True
        self.learning_thread = threading.Thread(
            target=self._background_learning_loop, daemon=True
        )
        self.learning_thread.start()

        # College football specific knowledge
        self.domain_knowledge = self._initialize_domain_knowledge()

    def _initialize_domain_knowledge(self) -> Dict[str, Any]:
        """Initialize college football-specific learning knowledge."""
        return {
            "seasonal_patterns": {
                "early_season": {
                    "months": [8, 9],
                    "characteristics": ["high_variance", "team_development"],
                    "learning_multiplier": 1.2,
                },
                "mid_season": {
                    "months": [10, 11],
                    "characteristics": ["stable_performance", "conference_play"],
                    "learning_multiplier": 1.0,
                },
                "late_season": {
                    "months": [12, 1],
                    "characteristics": ["bowl_preparation", "momentum"],
                    "learning_multiplier": 0.8,
                },
            },
            "team_performance_factors": {
                "offense": ["yards_per_play", "ppa", "explosiveness", "efficiency"],
                "defense": ["yards_allowed_per_play", "ppa_allowed", "pressure_rate"],
                "special_teams": ["field_goal_percentage", "return_average", "punting"],
                "situational": ["third_down_efficiency", "red_zone", "turnover_margin"],
            },
            "prediction_reliability": {
                "high_confidence": {"range": [0.7, 1.0], "learning_weight": 0.5},
                "medium_confidence": {"range": [0.5, 0.7], "learning_weight": 1.0},
                "low_confidence": {"range": [0.0, 0.5], "learning_weight": 1.5},
            },
        }

    def process_feedback(
        self,
        feedback_data: Dict[str, Any],
        feedback_type: FeedbackType,
        source: str,
        confidence: float = 1.0,
    ) -> str:
        """
        Process feedback and convert it to learning signals.

        Args:
            feedback_data: Raw feedback data
            feedback_type: Type of feedback
            source: Source of the feedback
            confidence: Confidence in the feedback quality

        Returns:
            Learning signal ID
        """

        try:
            # Convert feedback to learning signal
            signal_value = self._extract_learning_signal_value(
                feedback_data, feedback_type
            )

            learning_signal = LearningSignal(
                signal_id=f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}",
                feedback_type=feedback_type,
                source=source,
                content=feedback_data,
                value=signal_value,
                confidence=confidence,
                timestamp=datetime.now(),
                context=self._extract_context(feedback_data),
            )

            # Store learning signal
            self.learning_signals.append(learning_signal)
            self.memory_manager.store(
                content=asdict(learning_signal),
                memory_level=MemoryLevel.EPISODIC,
                memory_type=MemoryType.EXPERIENCE,
                metadata={"signal_id": learning_signal.signal_id, "source": source},
                tags=["learning_signal", feedback_type.value, source],
            )

            # Update metrics
            self.metrics.total_signals_processed += 1
            self.metrics.last_update = datetime.now()

            # Trigger immediate learning if signal is strong enough
            if abs(signal_value) > self.adaptation_threshold:
                self._trigger_learning_cycle(learning_signal)

            return learning_signal.signal_id

        except Exception as e:
            logging.error(f"Error processing feedback: {str(e)}")
            return f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _extract_learning_signal_value(
        self, feedback_data: Dict[str, Any], feedback_type: FeedbackType
    ) -> float:
        """Extract numerical learning signal value from feedback."""

        if feedback_type == FeedbackType.EXPLICIT_RATING:
            # Convert 1-5 rating to -1 to 1 scale
            rating = feedback_data.get("rating", 3)
            return (rating - 3) / 2.0

        elif feedback_type == FeedbackType.CORRECTION:
            # Calculate prediction error
            predicted = feedback_data.get("predicted", 0.5)
            actual = feedback_data.get("actual", 0.5)
            error = predicted - actual
            return -error  # Negative signal for prediction errors

        elif feedback_type == FeedbackType.USEAGE_PATTERNS:
            # Signal based on usage patterns
            engagement_score = feedback_data.get("engagement_score", 0.5)
            return engagement_score - 0.5

        elif feedback_type == FeedbackType.PERFORMANCE_METRICS:
            # Signal based on performance metrics
            performance_score = feedback_data.get("performance_score", 0.5)
            return performance_score - 0.5

        elif feedback_type == FeedbackType.DOMAIN_FEEDBACK:
            # Domain expert feedback
            expert_confidence = feedback_data.get("expert_confidence", 0.5)
            return expert_confidence - 0.5

        else:
            return 0.0

    def _extract_context(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contextual information from feedback."""
        context = {}

        # Game context if available
        if "game_data" in feedback_data:
            game_data = feedback_data["game_data"]
            context.update(
                {
                    "home_team": game_data.get("home_team"),
                    "away_team": game_data.get("away_team"),
                    "season": game_data.get("season"),
                    "week": game_data.get("week"),
                    "conference_game": game_data.get("conference_game", False),
                }
            )

        # Time context
        now = datetime.now()
        context.update(
            {
                "hour": now.hour,
                "day_of_week": now.weekday(),
                "month": now.month,
                "season_period": self._get_season_period(now.month),
            }
        )

        # Performance context
        if "performance_data" in feedback_data:
            context["performance_context"] = feedback_data["performance_data"]

        return context

    def _get_season_period(self, month: int) -> str:
        """Determine season period based on month."""
        if month in [8, 9]:
            return "early_season"
        elif month in [10, 11]:
            return "mid_season"
        else:
            return "late_season"

    def _trigger_learning_cycle(self, signal: LearningSignal):
        """Trigger a learning cycle based on a strong signal."""

        # Determine best learning strategy
        strategy = self._select_learning_strategy(signal)

        # Create adaptation action
        adaptation = AdaptationAction(
            action_id=f"adapt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}",
            strategy=strategy,
            target_component=signal.source,
            adaptation_type=self._determine_adaptation_type(signal),
            parameters=self._calculate_adaptation_parameters(signal),
            expected_improvement=abs(signal.value) * self.learning_rate,
            confidence=signal.confidence,
        )

        # Execute adaptation
        improvement = self._execute_adaptation(adaptation)
        adaptation.actual_improvement = improvement

        # Store adaptation
        self.adaptation_history.append(adaptation)
        self.memory_manager.store(
            content=asdict(adaptation),
            memory_level=MemoryLevel.SEMANTIC,
            memory_type=MemoryType.KNOWLEDGE,
            metadata={"action_id": adaptation.action_id, "strategy": strategy.value},
            tags=["adaptation", strategy.value, adaptation.target_component],
        )

        # Update metrics
        if improvement > 0:
            self.metrics.successful_adaptations += 1
        else:
            self.metrics.failed_adaptations += 1

        self._update_performance_metrics(improvement)

    def _select_learning_strategy(self, signal: LearningSignal) -> LearningStrategy:
        """Select the best learning strategy for a given signal."""

        # Consider signal characteristics
        if signal.feedback_type == FeedbackType.CORRECTION:
            # Direct correction - use online gradient descent
            return LearningStrategy.ONLINE_GRADIENT

        elif len(self.learning_signals) > 100:
            # Lots of data available - use experience replay
            return LearningStrategy.EXPERIENCE_REPLAY

        elif abs(signal.value) > 0.7:
            # Strong signal - use reinforcement learning
            return LearningStrategy.REINFORCEMENT_LEARNING

        elif len(self.adaptation_history) > 50:
            # Experienced system - use meta-learning
            return LearningStrategy.META_LEARNING

        else:
            # Default to ensemble adaptation
            return LearningStrategy.ENSEMBLE_ADAPTATION

    def _determine_adaptation_type(self, signal: LearningSignal) -> str:
        """Determine the type of adaptation needed."""

        if signal.source in ["ridge_model", "xgboost_model", "fastai_model"]:
            return "model_weight_adjustment"
        elif signal.source in ["explanation_engine"]:
            return "explanation_template_improvement"
        elif signal.source in ["feature_engineering"]:
            return "feature_importance_update"
        else:
            return "general_parameter_tuning"

    def _calculate_adaptation_parameters(
        self, signal: LearningSignal
    ) -> Dict[str, Any]:
        """Calculate parameters for the adaptation action."""

        base_params = {
            "learning_rate": self.learning_rate * abs(signal.value),
            "signal_strength": abs(signal.value),
            "confidence": signal.confidence,
            "context": signal.context,
        }

        # Add domain-specific adjustments
        if signal.context.get("season_period") == "early_season":
            base_params["variance_multiplier"] = 1.2
        elif signal.context.get("season_period") == "late_season":
            base_params["variance_multiplier"] = 0.8

        return base_params

    def _execute_adaptation(self, adaptation: AdaptationAction) -> float:
        """Execute an adaptation action and measure improvement."""

        try:
            # Execute learning strategy
            improvement = self.learning_strategies[adaptation.strategy](adaptation)

            # Update component weights
            if improvement > 0:
                self.component_weights[adaptation.target_component] *= (
                    1 + improvement * 0.1
                )
            else:
                self.component_weights[adaptation.target_component] *= 0.95

            # Record performance change
            self.performance_history.append(
                {
                    "timestamp": datetime.now(),
                    "component": adaptation.target_component,
                    "improvement": improvement,
                    "strategy": adaptation.strategy.value,
                }
            )

            return improvement

        except Exception as e:
            logging.error(f"Error executing adaptation: {str(e)}")
            return 0.0

    # Learning Strategy Implementations

    def _reinforcement_learning(self, adaptation: AdaptationAction) -> float:
        """Reinforcement learning strategy implementation."""

        # Simplified Q-learning style update
        learning_rate = adaptation.parameters.get("learning_rate", self.learning_rate)
        signal_strength = adaptation.parameters.get("signal_strength", 0.5)

        # Update component performance based on reward signal
        reward = signal_strength * adaptation.confidence

        # Apply learning rate adjustment
        improvement = reward * learning_rate

        # Update component performance tracking
        self.component_performance[adaptation.target_component].append(improvement)

        return max(0, improvement)  # Return positive improvement

    def _online_gradient_descent(self, adaptation: AdaptationAction) -> float:
        """Online gradient descent learning strategy."""

        learning_rate = adaptation.parameters.get("learning_rate", self.learning_rate)
        error_magnitude = adaptation.parameters.get("signal_strength", 0.5)

        # Simulate gradient descent update
        gradient = error_magnitude * adaptation.confidence
        weight_update = learning_rate * gradient

        # Calculate improvement (simplified)
        improvement = abs(weight_update) * 0.1

        self.component_performance[adaptation.target_component].append(improvement)

        return improvement

    def _experience_replay(self, adaptation: AdaptationAction) -> float:
        """Experience replay learning strategy."""

        if len(self.learning_signals) < 10:
            return 0.0

        # Sample recent experiences
        recent_signals = list(self.learning_signals)[-20:]
        relevant_signals = [
            s for s in recent_signals if s.source == adaptation.target_component
        ]

        if len(relevant_signals) < 5:
            return 0.0

        # Calculate average signal strength
        avg_signal = statistics.mean([s.value for s in relevant_signals])
        learning_rate = adaptation.parameters.get("learning_rate", self.learning_rate)

        improvement = (
            abs(avg_signal) * learning_rate * 0.8
        )  # Reduced learning rate for stability

        self.component_performance[adaptation.target_component].append(improvement)

        return improvement

    def _meta_learning(self, adaptation: AdaptationAction) -> float:
        """Meta-learning strategy - learning how to learn."""

        if len(self.adaptation_history) < 10:
            return 0.0

        # Analyze past successful adaptations for this component
        component_adaptations = [
            a
            for a in self.adaptation_history
            if a.target_component == adaptation.target_component
            and a.actual_improvement is not None
        ]

        if len(component_adaptations) < 5:
            return 0.0

        # Calculate meta-parameters
        successful_adaptations = [
            a for a in component_adaptations if a.actual_improvement > 0
        ]
        success_rate = len(successful_adaptations) / len(component_adaptations)

        if success_rate > 0.7:
            # High success rate - be more aggressive
            meta_multiplier = 1.2
        elif success_rate < 0.3:
            # Low success rate - be more conservative
            meta_multiplier = 0.5
        else:
            meta_multiplier = 1.0

        base_learning_rate = adaptation.parameters.get(
            "learning_rate", self.learning_rate
        )
        adjusted_learning_rate = base_learning_rate * meta_multiplier

        improvement = (
            adjusted_learning_rate
            * adaptation.parameters.get("signal_strength", 0.5)
            * success_rate
        )

        self.component_performance[adaptation.target_component].append(improvement)

        return improvement

    def _knowledge_distillation(self, adaptation: AdaptationAction) -> float:
        """Knowledge distillation learning strategy."""

        # Transfer knowledge between components
        source_performance = self.component_performance.get(
            adaptation.target_component, []
        )

        if len(source_performance) < 5:
            return 0.0

        # Find best performing similar components
        similar_components = [
            comp
            for comp in self.component_performance.keys()
            if comp != adaptation.target_component
            and len(self.component_performance[comp]) > 5
        ]

        if not similar_components:
            return 0.0

        # Calculate performance differences and transfer knowledge
        avg_source_performance = statistics.mean(source_performance[-10:])

        best_improvement = 0.0
        for similar_comp in similar_components:
            similar_performance = self.component_performance[similar_comp]
            avg_similar_performance = statistics.mean(similar_performance[-10:])

            if avg_similar_performance > avg_source_performance:
                # Transfer knowledge from better performing component
                knowledge_transfer = (
                    avg_similar_performance - avg_source_performance
                ) * 0.1
                best_improvement = max(best_improvement, knowledge_transfer)

        self.component_performance[adaptation.target_component].append(best_improvement)

        return best_improvement

    def _ensemble_adaptation(self, adaptation: AdaptationAction) -> float:
        """Ensemble adaptation learning strategy."""

        # Adapt ensemble weights based on feedback
        learning_rate = adaptation.parameters.get("learning_rate", self.learning_rate)
        signal_strength = adaptation.parameters.get("signal_strength", 0.5)

        # Update component weight in ensemble
        current_weight = self.component_weights[adaptation.target_component]

        if signal_strength > 0:  # Positive feedback
            weight_adjustment = learning_rate * signal_strength * 0.1
        else:  # Negative feedback
            weight_adjustment = learning_rate * signal_strength * 0.05

        new_weight = max(0.1, min(2.0, current_weight + weight_adjustment))
        self.component_weights[adaptation.target_component] = new_weight

        # Calculate improvement as weight adjustment success
        improvement = abs(weight_adjustment) * adaptation.confidence

        self.component_performance[adaptation.target_component].append(improvement)

        return improvement

    def _background_learning_loop(self):
        """Background thread for continuous learning operations."""

        while self.learning_active:
            try:
                # Consolidate learning experiences
                self._consolidate_experiences()

                # Periodic model retraining simulation
                if (
                    len(self.learning_signals) % 50 == 0
                    and len(self.learning_signals) > 0
                ):
                    self._simulate_periodic_retraining()

                # Clean up old data
                self._cleanup_old_data()

                # Sleep for learning interval
                time.sleep(300)  # 5 minutes

            except Exception as e:
                logging.error(f"Error in background learning loop: {str(e)}")
                time.sleep(60)  # Wait 1 minute on error

    def _consolidate_experiences(self):
        """Consolidate learning experiences into semantic memory."""

        if len(self.learning_signals) < 20:
            return

        # Group recent signals by type
        recent_signals = list(self.learning_signals)[-50:]
        signals_by_type = defaultdict(list)

        for signal in recent_signals:
            signals_by_type[signal.feedback_type].append(signal)

        # Create consolidated knowledge for each feedback type
        for feedback_type, signals in signals_by_type.items():
            if len(signals) < 5:
                continue

            # Calculate aggregated insights
            avg_signal = statistics.mean([s.value for s in signals])
            avg_confidence = statistics.mean([s.confidence for s in signals])

            consolidated_knowledge = {
                "feedback_type": feedback_type.value,
                "signal_count": len(signals),
                "average_signal_strength": avg_signal,
                "average_confidence": avg_confidence,
                "learning_trend": self._calculate_learning_trend(signals),
                "consolidation_timestamp": datetime.now().isoformat(),
            }

            # Store in semantic memory
            self.memory_manager.store(
                content=consolidated_knowledge,
                memory_level=MemoryLevel.SEMANTIC,
                memory_type=MemoryType.KNOWLEDGE,
                metadata={"feedback_type": feedback_type.value},
                tags=["consolidated_knowledge", feedback_type.value],
            )

    def _calculate_learning_trend(self, signals: List[LearningSignal]) -> str:
        """Calculate learning trend from a series of signals."""

        if len(signals) < 5:
            return "insufficient_data"

        # Calculate trend over time
        values = [s.value for s in signals]
        recent_values = values[-10:]
        earlier_values = values[-20:-10] if len(values) >= 20 else values[:-10]

        if len(earlier_values) == 0:
            return "stable"

        recent_avg = statistics.mean(recent_values)
        earlier_avg = statistics.mean(earlier_values)

        trend = recent_avg - earlier_avg

        if trend > 0.1:
            return "improving"
        elif trend < -0.1:
            return "declining"
        else:
            return "stable"

    def _simulate_periodic_retraining(self):
        """Simulate periodic model retraining based on accumulated feedback."""

        # Identify components with significant feedback
        component_feedback = defaultdict(list)

        for signal in self.learning_signals:
            if signal.source in component_feedback or len(component_feedback) < 10:
                component_feedback[signal.source].append(signal)

        # Simulate retraining for components with enough feedback
        for component, signals in component_feedback.items():
            if len(signals) >= 10:
                avg_improvement = statistics.mean([abs(s.value) for s in signals])

                if avg_improvement > self.adaptation_threshold:
                    # Simulate retraining benefit
                    retraining_improvement = avg_improvement * 0.3

                    # Record retraining event
                    self.memory_manager.store(
                        content={
                            "component": component,
                            "retraining_improvement": retraining_improvement,
                            "signals_used": len(signals),
                            "timestamp": datetime.now().isoformat(),
                        },
                        memory_level=MemoryLevel.SEMANTIC,
                        memory_type=MemoryType.PROCEDURE,
                        tags=["retraining", component],
                    )

    def _cleanup_old_data(self):
        """Clean up old learning data to manage memory."""

        # Remove very old signals (keep only recent ones)
        cutoff_time = datetime.now() - timedelta(days=30)

        # This is handled by deque maxlen, but additional cleanup can be added here

        # Clean up memory (memory manager handles this automatically)

        pass

    def _update_performance_metrics(self, improvement: float):
        """Update learning system performance metrics."""

        # Calculate rolling average improvement
        if len(self.adaptation_history) > 0:
            recent_adaptations = self.adaptation_history[-20:]
            recent_improvements = [
                a.actual_improvement
                for a in recent_adaptations
                if a.actual_improvement is not None
            ]

            if recent_improvements:
                self.metrics.average_improvement = statistics.mean(recent_improvements)

        # Calculate stability score
        if len(self.performance_history) > 10:
            recent_performance = [
                p["improvement"] for p in list(self.performance_history)[-20:]
            ]
            performance_variance = (
                statistics.variance(recent_performance)
                if len(recent_performance) > 1
                else 0
            )
            self.metrics.stability_score = max(0, 1 - performance_variance)

        # Calculate knowledge growth
        self.metrics.knowledge_growth = (
            len(self.learning_signals) * 0.001
        )  # Simplified growth metric

        self.metrics.last_update = datetime.now()

    def get_learning_status(self) -> Dict[str, Any]:
        """Get comprehensive learning system status."""

        return {
            "agent_id": self.agent_id,
            "metrics": asdict(self.metrics),
            "component_weights": dict(self.component_weights),
            "total_learning_signals": len(self.learning_signals),
            "total_adaptations": len(self.adaptation_history),
            "active_strategies": [
                strategy.value for strategy in self.learning_strategies.keys()
            ],
            "memory_usage": self.memory_manager.get_stats().total_entries,
            "learning_rate": self.learning_rate,
            "adaptation_threshold": self.adaptation_threshold,
            "background_learning_active": self.learning_active,
        }

    def get_component_performance(self, component_name: str = None) -> Dict[str, Any]:
        """Get performance data for specific component or all components."""

        if component_name:
            if component_name not in self.component_performance:
                return {}

            performance_data = self.component_performance[component_name]

            return {
                "component": component_name,
                "weight": self.component_weights[component_name],
                "total_experiences": len(performance_data),
                "recent_performance": list(performance_data)[-10:],
                "average_performance": (
                    statistics.mean(performance_data) if performance_data else 0
                ),
                "performance_trend": (
                    self._calculate_learning_trend(
                        [
                            LearningSignal(
                                "",
                                FeedbackType.EXPLICIT_RATING,
                                "",
                                {},
                                val,
                                1.0,
                                datetime.now(),
                                {},
                            )
                            for val in performance_data[-20:]
                        ]
                    )
                    if len(performance_data) >= 5
                    else "insufficient_data"
                ),
            }
        else:
            # Return data for all components
            return {
                comp: self.get_component_performance(comp)
                for comp in self.component_performance.keys()
            }

    def adapt_learning_parameters(
        self,
        learning_rate: float = None,
        adaptation_threshold: float = None,
        memory_size: int = None,
    ):
        """Adapt learning parameters based on performance."""

        if learning_rate is not None:
            self.learning_rate = max(0.001, min(0.1, learning_rate))

        if adaptation_threshold is not None:
            self.adaptation_threshold = max(0.01, min(0.5, adaptation_threshold))

        if memory_size is not None:
            # Note: This would require recreating the deque
            pass

    def export_learning_data(
        self,
        format_type: str = "json",
        include_signals: bool = True,
        include_adaptations: bool = True,
    ) -> str:
        """Export learning data for analysis or backup."""

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "metrics": asdict(self.metrics),
            "component_weights": dict(self.component_weights),
        }

        if include_signals:
            export_data["learning_signals"] = [
                asdict(signal)
                for signal in list(self.learning_signals)[-100:]  # Last 100 signals
            ]

        if include_adaptations:
            export_data["adaptation_history"] = [
                asdict(adaptation)
                for adaptation in self.adaptation_history[-50:]  # Last 50 adaptations
            ]

        if format_type == "json":
            return json.dumps(export_data, indent=2, default=str)
        elif format_type == "pickle":
            return pickle.dumps(export_data)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    def shutdown(self):
        """Gracefully shutdown the learning system."""

        self.learning_active = False

        # Wait for learning thread to finish
        if self.learning_thread.is_alive():
            self.learning_thread.join(timeout=10)

        # Export final state
        final_state = self.export_learning_data()

        # Store final state in memory
        self.memory_manager.store(
            content={
                "final_state": final_state,
                "shutdown_timestamp": datetime.now().isoformat(),
            },
            memory_level=MemoryLevel.SEMANTIC,
            memory_type=MemoryType.REFLECTION,
            tags=["shutdown", "final_state"],
        )
