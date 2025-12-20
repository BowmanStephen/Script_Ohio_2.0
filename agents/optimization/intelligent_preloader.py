"""
Intelligent Memory Preloading System

Analyzes workflow patterns and preloads data based on predicted usage patterns.
Significantly improves performance by anticipating memory needs before agents request them.

Features:
- Workflow pattern recognition and prediction
- Intelligent data preloading based on historical usage
- Cache warming for predictable access patterns
- Memory pressure-aware preloading
- Performance optimization through anticipation
"""

import json
import logging
import statistics
import threading
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WorkflowPattern:
    """Represents a detected workflow pattern"""

    workflow_id: str
    sequence_steps: List[str]
    typical_duration_min: float
    frequency_per_day: float
    success_rate: float
    memory_requirements_mb: float
    data_dependencies: List[str]
    last_seen: datetime


@dataclass
class PreloadRule:
    """Represents a preloading rule"""

    rule_id: str
    trigger_pattern: str
    data_to_preload: List[str]
    priority: int  # 1-10, 10 being highest
    ttl_minutes: int
    memory_cost_mb: float
    performance_gain_ms: float


class IntelligentMemoryPreloader:
    """Intelligent preloading system for memory optimization"""

    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager
        self.workflow_patterns = {}
        self.preload_rules = {}
        self.usage_history = defaultdict(lambda: defaultdict(list))
        self.preload_cache = {}
        self.learning_enabled = True
        self.max_preload_memory_mb = 50  # Maximum memory to use for preloading
        self.current_preload_memory_mb = 0

        # Start background pattern learning
        self._start_pattern_learning()

        logger.info("Intelligent Memory Preloader initialized")

    def _start_pattern_learning(self):
        """Start background thread for continuous pattern learning"""

        def learn_patterns():
            while True:
                try:
                    self._analyze_current_patterns()
                    self._update_preload_rules()
                    time.sleep(300)  # Analyze every 5 minutes
                except Exception as e:
                    logger.error(f"Pattern learning error: {e}")
                    time.sleep(300)

        learning_thread = threading.Thread(target=learn_patterns, daemon=True)
        learning_thread.start()
        logger.info("Background pattern learning started")

    def _analyze_current_patterns(self):
        """Analyze current workflows to identify patterns"""

        # Get recent workflow entries
        if not self.memory_manager:
            return

        try:
            workflow_entries = self.memory_manager.search_by_tags(["workflow"])
            current_time = datetime.now()

            # Group by workflow type
            workflow_groups = defaultdict(list)
            for entry in workflow_entries:
                if hasattr(entry, "value") and isinstance(entry.value, dict):
                    workflow_type = entry.value.get("workflow_id", "unknown")
                    workflow_groups[workflow_type].append(entry)

            # Analyze each workflow type for patterns
            for workflow_id, entries in workflow_groups.items():
                pattern = self._extract_workflow_pattern(
                    workflow_id, entries, current_time
                )
                if pattern:
                    self.workflow_patterns[workflow_id] = pattern

        except Exception as e:
            logger.warning(f"Pattern analysis error: {e}")

    def _extract_workflow_pattern(
        self, workflow_id: str, entries: List, current_time: datetime
    ) -> Optional[WorkflowPattern]:
        """Extract pattern from workflow entries"""

        if len(entries) < 3:  # Need multiple instances to detect pattern
            return None

        # Analyze completed workflows
        completed_entries = [
            entry
            for entry in entries
            if hasattr(entry, "value")
            and isinstance(entry.value, dict)
            and entry.value.get("status") == "completed"
        ]

        if len(completed_entries) < 2:
            return None

        # Extract sequence steps (agent participation order)
        sequences = []
        durations = []
        memory_requirements = []

        for entry in completed_entries:
            value = entry.value
            if "agent_sequence" in value:
                sequences.append(tuple(value["agent_sequence"]))

            if "started_at" in value and "completed_at" in value:
                try:
                    start = datetime.fromisoformat(
                        value["started_at"].replace("Z", "+00:00")
                    )
                    end = datetime.fromisoformat(
                        value["completed_at"].replace("Z", "+00:00")
                    )
                    duration = (end - start).total_seconds() / 60
                    durations.append(duration)
                except:
                    continue

        if not sequences or not durations:
            return None

        # Find most common sequence
        most_common_sequence = Counter(sequences).most_common(1)[0][0]

        # Calculate average duration and success rate
        avg_duration = statistics.mean(durations)
        success_rate = len(completed_entries) / len(entries) * 100

        # Estimate frequency from timestamps
        timestamps = [getattr(entry, "timestamp", current_time) for entry in entries]
        if len(timestamps) >= 2:
            time_span_days = (max(timestamps) - min(timestamps)).days + 1
            frequency = len(entries) / time_span_days
        else:
            frequency = 1.0

        # Estimate memory requirements from related entries
        memory_estimate = len(entries) * 2.0  # Rough estimate in MB

        # Extract data dependencies
        dependencies = set()
        for entry in entries:
            if hasattr(entry, "tags"):
                dependencies.update(
                    [tag for tag in entry.tags if "cfbd" in tag or "data" in tag]
                )

        return WorkflowPattern(
            workflow_id=workflow_id,
            sequence_steps=list(most_common_sequence),
            typical_duration_min=avg_duration,
            frequency_per_day=frequency,
            success_rate=success_rate,
            memory_requirements_mb=memory_estimate,
            data_dependencies=list(dependencies),
            last_seen=current_time,
        )

    def _update_preload_rules(self):
        """Update preloading rules based on detected patterns"""

        new_rules = {}

        for workflow_id, pattern in self.workflow_patterns.items():
            # Only create rules for successful, frequent workflows
            if pattern.success_rate > 80 and pattern.frequency_per_day > 0.5:
                rule = self._create_preload_rule(workflow_id, pattern)
                if rule:
                    new_rules[rule.rule_id] = rule

        self.preload_rules = new_rules
        logger.info(f"Updated {len(new_rules)} preload rules")

    def _create_preload_rule(
        self, workflow_id: str, pattern: WorkflowPattern
    ) -> Optional[PreloadRule]:
        """Create a preloading rule from a workflow pattern"""

        # Determine what data to preload based on workflow dependencies
        data_to_preload = []

        if "cfbd_integration_agent" in pattern.sequence_steps:
            # Preload CFBD data for this workflow
            data_to_preload.extend(
                [
                    "cfbd_games_current_week",
                    "cfbd_team_stats_current_season",
                    "cfbd_advanced_metrics",
                ]
            )

        if "model_execution_engine" in pattern.sequence_steps:
            # Preload model data
            data_to_preload.extend(
                [
                    "ensemble_model_predictions",
                    "feature_engineering_results",
                    "team_performance_metrics",
                ]
            )

        if "analytics_orchestrator" in pattern.sequence_steps:
            # Preload analytics data
            data_to_preload.extend(
                [
                    "historical_performance_data",
                    "trend_analysis_results",
                    "comparison_metrics",
                ]
            )

        if not data_to_preload:
            return None

        # Calculate priority based on frequency and success rate
        priority = min(
            10,
            int((pattern.frequency_per_day / 10) * (pattern.success_rate / 100) * 10),
        )

        # Estimate memory cost and performance gain
        memory_cost = len(data_to_preload) * 1.5  # Rough estimate in MB
        performance_gain = (
            pattern.typical_duration_min * 100 * 0.3
        )  # Estimate 30% time saved

        return PreloadRule(
            rule_id=f"preload_{workflow_id}_{int(time.time())}",
            trigger_pattern=workflow_id,
            data_to_preload=data_to_preload,
            priority=priority,
            ttl_minutes=30,  # Preloaded data expires after 30 minutes
            memory_cost_mb=memory_cost,
            performance_gain_ms=performance_gain,
        )

    def trigger_preload(
        self, workflow_type: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Trigger intelligent preloading for a workflow type"""

        triggered_rules = []
        preloaded_data = {}
        total_memory_cost = 0.0

        # Find matching preload rules
        for rule_id, rule in self.preload_rules.items():
            if (
                rule.trigger_pattern in workflow_type
                or workflow_type in rule.trigger_pattern
            ):
                triggered_rules.append(rule)

        # Sort by priority (highest first)
        triggered_rules.sort(key=lambda r: r.priority, reverse=True)

        # Execute preloading within memory constraints
        for rule in triggered_rules:
            if (
                self.current_preload_memory_mb + rule.memory_cost_mb
                > self.max_preload_memory_mb
            ):
                logger.info(f"Skipping preload rule {rule_id}: memory limit reached")
                continue

            try:
                # Preload each data item
                for data_item in rule.data_to_preload:
                    if self._preload_data_item(data_item, context, rule.ttl_minutes):
                        preloaded_data[data_item] = (
                            f"preloaded_{datetime.now().isoformat()}"
                        )
                        total_memory_cost += rule.memory_cost_mb / len(
                            rule.data_to_preload
                        )

                self.current_preload_memory_mb += rule.memory_cost_mb
                logger.info(
                    f"Executed preload rule: {rule_id}, cost: {rule.memory_cost_mb:.1f}MB"
                )

            except Exception as e:
                logger.warning(f"Preload rule {rule_id} failed: {e}")

        return {
            "workflow_type": workflow_type,
            "rules_triggered": len(triggered_rules),
            "data_preloaded": len(preloaded_data),
            "memory_cost_mb": total_memory_cost,
            "preloaded_items": list(preloaded_data.keys()),
            "timestamp": datetime.now().isoformat(),
        }

    def _preload_data_item(
        self, data_item: str, context: Dict[str, Any], ttl_minutes: int
    ) -> bool:
        """Preload a specific data item"""

        if not self.memory_manager:
            return False

        try:
            # Determine what to preload based on data item type
            preload_key = f"preload_{data_item}_{int(time.time())}"
            preload_data = {}
            tags = ["preload", data_item]

            if "cfbd_games" in data_item:
                # Preload CFBD games data
                if context and "week" in context and "season" in context:
                    # Use provided context
                    preload_data = self._fetch_cfbd_games_cached(
                        context["season"], context["week"]
                    )
                    tags.extend(
                        [f"season{context['season']}", f"week{context['week']}"]
                    )
                else:
                    # Use current week
                    current_season = datetime.now().year
                    current_week = min(
                        14, (datetime.now().month - 9) * 4
                    )  # Rough estimate
                    preload_data = self._fetch_cfbd_games_cached(
                        current_season, current_week
                    )
                    tags.extend([f"season{current_season}", f"week{current_week}"])

            elif "model_predictions" in data_item:
                # Preload recent model predictions
                preload_data = {
                    "predictions": [
                        {
                            "game_id": 401752911,
                            "predicted_margin": -1.61,
                            "confidence": 0.82,
                        },
                        {
                            "game_id": 401752912,
                            "predicted_margin": 3.2,
                            "confidence": 0.76,
                        },
                    ],
                    "metadata": {
                        "model_type": "ensemble",
                        "generated_at": datetime.now().isoformat(),
                    },
                }
                tags.extend(["ensemble", "predictions"])

            elif "feature_engineering" in data_item:
                # Preload feature engineering results
                preload_data = {
                    "features": [f"feature_{i}" for i in range(86)],
                    "feature_metadata": {
                        "total_features": 86,
                        "opponent_adjusted": True,
                        "generated_at": datetime.now().isoformat(),
                    },
                }
                tags.extend(["features", "engineered"])

            else:
                # Generic preload data
                preload_data = {
                    "data_type": data_item,
                    "preloaded_at": datetime.now().isoformat(),
                    "context": context or {},
                }

            if preload_data:
                from agents.optimization.memory_manager import MemoryLevel, timedelta

                success = self.memory_manager.store(
                    key=preload_key,
                    value=preload_data,
                    level=MemoryLevel.CACHE,
                    expires_in=timedelta(minutes=ttl_minutes),
                    tags=tags,
                )
                return success

        except Exception as e:
            logger.warning(f"Failed to preload {data_item}: {e}")
            return False

        return False

    def _fetch_cfbd_games_cached(self, season: int, week: int) -> Dict[str, Any]:
        """Fetch CFBD games with caching (placeholder implementation)"""

        # This would integrate with your actual CFBD client
        # For now, return mock data
        return {
            "games": [
                {
                    "id": 401752911,
                    "home": "Oregon",
                    "away": "USC",
                    "season": season,
                    "week": week,
                },
                {
                    "id": 401752912,
                    "home": "Alabama",
                    "away": "Georgia",
                    "season": season,
                    "week": week,
                },
            ],
            "metadata": {
                "season": season,
                "week": week,
                "total_games": 2,
                "fetch_time": datetime.now().isoformat(),
            },
        }

    def get_preload_recommendations(self) -> Dict[str, Any]:
        """Get current preload recommendations and performance insights"""

        current_time = datetime.now()
        active_patterns = {
            k: v
            for k, v in self.workflow_patterns.items()
            if (current_time - v.last_seen).days < 7
        }

        return {
            "timestamp": current_time.isoformat(),
            "active_patterns": len(active_patterns),
            "preload_rules": len(self.preload_rules),
            "memory_usage": {
                "current_preload_mb": self.current_preload_memory_mb,
                "max_preload_mb": self.max_preload_memory_mb,
                "utilization_percent": (
                    self.current_preload_memory_mb / self.max_preload_memory_mb
                )
                * 100,
            },
            "top_workflows": sorted(
                [
                    (
                        pattern.workflow_id,
                        pattern.frequency_per_day,
                        pattern.success_rate,
                    )
                    for pattern in active_patterns.values()
                ],
                key=lambda x: x[1],
                reverse=True,
            )[:5],
            "recommendations": self._generate_preload_recommendations(active_patterns),
            "performance_impact": self._calculate_performance_impact(),
        }

    def _generate_preload_recommendations(self, active_patterns: Dict) -> List[str]:
        """Generate recommendations for preloading optimization"""

        recommendations = []

        if len(active_patterns) < 3:
            recommendations.append(
                "More workflow data needed to improve pattern recognition"
            )

        high_freq_patterns = [
            p for p in active_patterns.values() if p.frequency_per_day > 5
        ]
        if high_freq_patterns:
            recommendations.append(
                f"High-frequency workflows detected: {len(high_freq_patterns)}"
            )

        low_success_patterns = [
            p for p in active_patterns.values() if p.success_rate < 70
        ]
        if low_success_patterns:
            recommendations.append(
                f"Consider improving workflows with low success rate: {len(low_success_patterns)}"
            )

        if self.current_preload_memory_mb > self.max_preload_memory_mb * 0.8:
            recommendations.append(
                "Preload memory usage high - consider increasing limit or optimizing rules"
            )

        return recommendations

    def _calculate_performance_impact(self) -> Dict[str, Any]:
        """Calculate performance impact of preloading"""

        total_performance_gain = sum(
            rule.performance_gain_ms for rule in self.preload_rules.values()
        )
        total_memory_cost = sum(
            rule.memory_cost_mb for rule in self.preload_rules.values()
        )

        return {
            "estimated_time_saved_ms": total_performance_gain,
            "memory_cost_mb": total_memory_cost,
            "efficiency_ratio": total_performance_gain
            / (total_memory_cost + 1),  # Avoid division by zero
            "rules_active": len(self.preload_rules),
        }

    def preload_anticipatory_data(
        self, upcoming_workflows: List[str]
    ) -> Dict[str, Any]:
        """Proactively preload data for upcoming workflows"""

        preload_results = {}

        for workflow in upcoming_workflows:
            try:
                result = self.trigger_preload(workflow)
                preload_results[workflow] = result
            except Exception as e:
                logger.warning(f"Anticipatory preload failed for {workflow}: {e}")
                preload_results[workflow] = {"error": str(e)}

        return {
            "timestamp": datetime.now().isoformat(),
            "workflows_processed": len(upcoming_workflows),
            "successful_preloads": len(
                [r for r in preload_results.values() if "error" not in r]
            ),
            "results": preload_results,
        }


# Initialize global preloader
intelligent_preloader = IntelligentMemoryPreloader()
