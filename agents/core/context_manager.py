#!/usr/bin/env python3
"""
DEPRECATED: Context Manager Agent - Intelligent Context Optimization for College Football Analytics

⚠️  DEPRECATION WARNING (2025-11-19):
This module is DEPRECATED and will be removed in a future version.
It was identified as unused in production code analysis.

The role-based context optimization system is NOT used by:
- scripts/generate_comprehensive_week13_analysis.py
- scripts/run_weekly_analysis.py
- Any production weekly analysis scripts

Weekly agents use direct execute_task() calls without role/context management.

Migration path:
- If you need role-based filtering, implement it directly in your orchestrator
- If you need context optimization, use simple parameter passing
- See agents/weekly_analysis_orchestrator.py for the pattern actually used
- See agents/simplified_analytics_orchestrator.py for simplified orchestrator

This module will be removed after 2025-12-19 (30-day deprecation period).

Original description:
This agent manages context loading, optimization, and role-based user experiences
for the Script Ohio 2.0 analytics platform.

Author: Claude Code Assistant
Created: 2025-11-07
Version: 1.0 (DEPRECATED)
"""
import warnings

warnings.warn(
    "ContextManager is deprecated and will be removed after 2025-12-19. "
    "Use direct agent instantiation pattern from WeeklyAnalysisOrchestrator instead. "
    "See agents/weekly_analysis_orchestrator.py for the recommended pattern.",
    DeprecationWarning,
    stacklevel=2
)

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import pickle

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles for context management"""
    ANALYST = "analyst"
    DATA_SCIENTIST = "data_scientist"
    PRODUCTION = "production"

@dataclass
class ContextProfile:
    """Configuration for user role-based context loading"""
    role: UserRole
    token_budget_percentage: float
    data_scope: str
    focus_areas: List[str]
    notebook_access: List[str]
    model_access: List[str]
    features_priority: List[str]

@dataclass
class ContextMetrics:
    """Metrics for context usage and optimization"""
    tokens_used: int
    tokens_saved: int
    compression_ratio: float
    load_time_ms: float
    cache_hit_rate: float

@dataclass
class ConversationTurn:
    """Single conversation turn with context"""
    user_id: str
    query: str
    response: str
    context_used: Dict[str, Any]
    timestamp: datetime
    session_id: str
    turn_number: int
    tokens_used: int
    role_detected: UserRole

@dataclass
class SessionSummary:
    """Compressed summary of a conversation session"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: datetime
    total_turns: int
    total_tokens: int
    topics_discussed: List[str]
    key_insights: List[str]
    user_preferences: Dict[str, Any]
    session_effectiveness: float  # 0-1 score

@dataclass
class ConversationMemory:
    """Long-term conversation memory for context continuity"""
    user_id: str
    sessions: List[SessionSummary]
    recent_turns: List[ConversationTurn]  # Last 10 turns for quick access
    total_conversations: int
    average_session_length: float
    preferred_topics: List[str]
    expert_level_assessment: str

class ContextManager:
    """
    Intelligent context management system for role-based user experiences.

    Features:
    - Role-based context profiles
    - Token optimization and compression
    - Smart caching mechanisms
    - Progressive context loading
    - Performance monitoring

    .. deprecated:: 2025-11-19
        ContextManager is deprecated and will be removed in 30 days.
        Production code uses direct agent instantiation without role-based filtering.
        Migration: Use direct agent instantiation (see WeeklyAnalysisOrchestrator pattern).
    """

    def __init__(self, base_path: str = None):
        """Initialize Context Manager with configuration"""
        import warnings
        warnings.warn(
            "ContextManager is deprecated and will be removed on 2025-12-19. "
            "Use direct agent instantiation instead (see WeeklyAnalysisOrchestrator pattern).",
            DeprecationWarning,
            stacklevel=2
        )
        self.base_path = base_path or os.getcwd()
        self.context_cache = {}
        self.usage_metrics = {}
        self.profiles = self._initialize_profiles()
        self.token_budgets = self._initialize_token_budgets()

        # Conversation memory components
        self.conversation_memory: Dict[str, ConversationMemory] = {}
        self.active_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.memory_path = Path(self.base_path) / "memory"
        self.memory_path.mkdir(exist_ok=True)

        # Load existing conversation memory
        self._load_conversation_memory()

        logger.info(f"Context Manager initialized with conversation memory at: {self.base_path}")

    def _initialize_profiles(self) -> Dict[UserRole, ContextProfile]:
        """Initialize role-based context profiles"""
        return {
            UserRole.ANALYST: ContextProfile(
                role=UserRole.ANALYST,
                token_budget_percentage=0.5,
                data_scope="sample_data_only",
                focus_areas=["starter_pack", "basic_modeling", "educational_content"],
                notebook_access=[
                    "starter_pack/00_data_dictionary.ipynb",
                    "starter_pack/01_intro_to_data.ipynb",
                    "starter_pack/02_build_simple_rankings.ipynb",
                    "starter_pack/03_metrics_comparison.ipynb",
                    "starter_pack/04_team_similarity.ipynb",
                    "starter_pack/05_matchup_predictor.ipynb"
                ],
                model_access=["ridge_model_2025.joblib"],
                features_priority=[
                    "home_talent", "away_talent", "home_elo", "away_elo",
                    "home_adjusted_epa", "away_adjusted_epa"
                ]
            ),

            UserRole.DATA_SCIENTIST: ContextProfile(
                role=UserRole.DATA_SCIENTIST,
                token_budget_percentage=0.75,
                data_scope="full_feature_set",
                focus_areas=["model_pack", "advanced_analytics", "feature_engineering"],
                notebook_access=[
                    "model_pack/01_linear_regression_margin.ipynb",
                    "model_pack/02_random_forest_team_points.ipynb",
                    "model_pack/03_xgboost_win_probability.ipynb",
                    "model_pack/04_fastai_win_probability.ipynb",
                    "model_pack/05_logistic_regression_win_probability.ipynb",
                    "model_pack/06_shap_interpretability.ipynb",
                    "model_pack/07_stacked_ensemble.ipynb"
                ],
                model_access=[
                    "ridge_model_2025.joblib",
                    "xgb_home_win_model_2025.pkl",
                    "fastai_home_win_model_2025.pkl"
                ],
                features_priority=[
                    "home_adjusted_epa", "away_adjusted_epa",
                    "home_adjusted_success", "away_adjusted_success",
                    "home_adjusted_explosiveness", "away_adjusted_explosiveness",
                    "home_total_havoc_offense", "away_total_havoc_offense"
                ]
            ),

            UserRole.PRODUCTION: ContextProfile(
                role=UserRole.PRODUCTION,
                token_budget_percentage=0.25,
                data_scope="current_season_only",
                focus_areas=["model_inference", "monitoring", "automated_analysis"],
                notebook_access=[
                    "model_pack/01_linear_regression_margin.ipynb",
                    "model_pack/03_xgboost_win_probability.ipynb"
                ],
                model_access=[
                    "ridge_model_2025.joblib",
                    "xgb_home_win_model_2025.pkl"
                ],
                features_priority=[
                    "home_talent", "away_talent", "spread",
                    "home_elo", "away_elo"
                ]
            )
        }

    def _initialize_token_budgets(self) -> Dict[UserRole, int]:
        """Initialize token budgets for different roles"""
        # Assuming a base token budget of 100,000 tokens
        base_budget = 100000
        return {
            role: int(base_budget * profile.token_budget_percentage)
            for role, profile in self.profiles.items()
        }

    def detect_user_role(self, user_context: Dict[str, Any]) -> UserRole:
        """
        Detect user role based on context and behavior patterns.

        Args:
            user_context: Dictionary containing user information and request context

        Returns:
            Detected user role
        """
        # Extract clues from user context
        requested_notebooks = user_context.get('notebooks', [])
        requested_models = user_context.get('models', [])
        query_type = user_context.get('query_type', '')

        # Score each role based on context
        role_scores = {role: 0 for role in UserRole}

        # Analyze notebook access patterns
        for notebook in requested_notebooks:
            if 'starter_pack' in notebook:
                role_scores[UserRole.ANALYST] += 2
            elif 'model_pack' in notebook:
                role_scores[UserRole.DATA_SCIENTIST] += 2
                if 'shap' in notebook or 'ensemble' in notebook:
                    role_scores[UserRole.DATA_SCIENTIST] += 1

        # Analyze model access patterns
        for model in requested_models:
            if 'ridge' in model and len(requested_models) == 1:
                role_scores[UserRole.PRODUCTION] += 2
            elif 'fastai' in model or 'shap' in query_type:
                role_scores[UserRole.DATA_SCIENTIST] += 2

        # Analyze query patterns
        if any(keyword in query_type.lower() for keyword in ['learn', 'tutorial', 'introduction', 'explain']):
            role_scores[UserRole.ANALYST] += 2
        elif any(keyword in query_type.lower() for keyword in ['predict', 'production', 'api', 'deploy']):
            role_scores[UserRole.PRODUCTION] += 2
        elif any(keyword in query_type.lower() for keyword in ['feature', 'model', 'optimize', 'advanced']):
            role_scores[UserRole.DATA_SCIENTIST] += 2

        # Return role with highest score
        detected_role = max(role_scores, key=role_scores.get)

        logger.info(f"Detected user role: {detected_role.value} (scores: {role_scores})")
        return detected_role

    def load_context_for_role(self, role: UserRole, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load optimized context for a specific user role.

        Args:
            role: User role
            request_context: Context of the user's request

        Returns:
            Optimized context dictionary
        """
        profile = self.profiles[role]
        token_budget = self.token_budgets[role]

        # Check cache first
        cache_key = self._generate_cache_key(role, request_context)
        if cache_key in self.context_cache:
            logger.info(f"Context cache hit for role: {role.value}")
            cached_context = self.context_cache[cache_key]
            self._update_metrics(cache_key, hit=True)
            return cached_context

        # Build context from scratch
        context = {
            'role': role.value,
            'profile': asdict(profile),
            'data': self._load_data_for_role(profile),
            'notebooks': self._load_notebooks_for_role(profile),
            'models': self._load_models_for_role(profile),
            'features': self._load_features_for_role(profile),
            'documentation': self._load_documentation_for_role(profile),
            'optimization_applied': True
        }

        # Apply token optimization
        optimized_context = self._optimize_context(context, token_budget)

        # Cache the result
        self.context_cache[cache_key] = optimized_context
        self._update_metrics(cache_key, hit=False)

        logger.info(f"Loaded optimized context for {role.value}: {len(str(optimized_context))} chars")
        return optimized_context

    def _load_data_for_role(self, profile: ContextProfile) -> Dict[str, Any]:
        """Load data appropriate for the user role"""
        data_path = Path(self.base_path) / "model_pack"

        if profile.data_scope == "current_season_only":
            # Load only 2025 data summary
            return {
                'current_season': {
                    'games': 469,
                    'season': 2025,
                    'features': 86,
                    'summary': '2025 season data available for current analysis'
                }
            }
        elif profile.data_scope == "sample_data_only":
            # Load sample datasets
            return {
                'sample_data': {
                    'games_sample': 100,
                    'features_sample': profile.features_priority[:6],
                    'seasons': [2024, 2025],
                    'summary': 'Sample data for learning and exploration'
                }
            }
        else:  # full_feature_set
            # Load comprehensive data information
            return {
                'full_dataset': {
                    'total_games': 4989,
                    'seasons': list(range(2016, 2026)),
                    'features': 86,
                    'models_available': 3,
                    'summary': 'Complete dataset for advanced analytics'
                }
            }

    def _load_notebooks_for_role(self, profile: ContextProfile) -> List[Dict[str, str]]:
        """Load notebook metadata appropriate for the user role"""
        notebooks = []

        for notebook_path in profile.notebook_access:
            full_path = Path(self.base_path) / notebook_path
            if full_path.exists():
                notebooks.append({
                    'path': notebook_path,
                    'name': Path(notebook_path).stem,
                    'type': 'starter_pack' if 'starter_pack' in notebook_path else 'model_pack',
                    'description': self._get_notebook_description(notebook_path)
                })

        return notebooks

    def _load_models_for_role(self, profile: ContextProfile) -> List[Dict[str, Any]]:
        """Load model information appropriate for the user role"""
        models = []
        model_path = Path(self.base_path) / "model_pack"

        for model_file in profile.model_access:
            full_path = model_path / model_file
            if full_path.exists():
                models.append({
                    'file': model_file,
                    'name': model_file.replace('.joblib', '').replace('.pkl', ''),
                    'type': 'regression' if 'ridge' in model_file else 'classification',
                    'size_kb': os.path.getsize(full_path) / 1024,
                    'description': self._get_model_description(model_file)
                })

        return models

    def _load_features_for_role(self, profile: ContextProfile) -> List[Dict[str, Any]]:
        """Load feature descriptions for priority features"""
        feature_descriptions = {
            'home_talent': {'type': 'numeric', 'description': 'Home team talent composite rating'},
            'away_talent': {'type': 'numeric', 'description': 'Away team talent composite rating'},
            'home_elo': {'type': 'numeric', 'description': 'Home team pre-game Elo rating'},
            'away_elo': {'type': 'numeric', 'description': 'Away team pre-game Elo rating'},
            'spread': {'type': 'numeric', 'description': 'Vegas betting spread (negative = home favored)'},
            'home_adjusted_epa': {'type': 'numeric', 'description': 'Home team adjusted EPA per play'},
            'away_adjusted_epa': {'type': 'numeric', 'description': 'Away team adjusted EPA per play'},
            'home_adjusted_success': {'type': 'numeric', 'description': 'Home team adjusted success rate'},
            'away_adjusted_success': {'type': 'numeric', 'description': 'Away team adjusted success rate'},
            'home_adjusted_explosiveness': {'type': 'numeric', 'description': 'Home team explosiveness metric'},
            'away_adjusted_explosiveness': {'type': 'numeric', 'description': 'Away team explosiveness metric'},
            'home_total_havoc_offense': {'type': 'numeric', 'description': 'Home team havoc rate allowed'},
            'away_total_havoc_offense': {'type': 'numeric', 'description': 'Away team havoc rate allowed'}
        }

        features = []
        for feature_name in profile.features_priority:
            if feature_name in feature_descriptions:
                feature_info = feature_descriptions[feature_name].copy()
                feature_info['name'] = feature_name
                feature_info['priority'] = profile.features_priority.index(feature_name) + 1
                features.append(feature_info)

        return features

    def _load_documentation_for_role(self, profile: ContextProfile) -> List[Dict[str, str]]:
        """Load documentation appropriate for the user role"""
        base_docs = [
            {'file': 'CLAUDE.md', 'name': 'Project Overview', 'priority': 1},
            {'file': 'QUICK_START_2025.md', 'name': 'Quick Start Guide', 'priority': 2}
        ]

        if profile.role == UserRole.ANALYST:
            base_docs.extend([
                {'file': 'starter_pack/README.md', 'name': 'Starter Pack Guide', 'priority': 3}
            ])
        elif profile.role == UserRole.DATA_SCIENTIST:
            base_docs.extend([
                {'file': 'model_pack/model_deployment_guide_2025.md', 'name': 'Model Deployment Guide', 'priority': 3},
                {'file': 'MODEL_USAGE_GUIDE.md', 'name': 'Model Usage Guide', 'priority': 4}
            ])
        elif profile.role == UserRole.PRODUCTION:
            base_docs.extend([
                {'file': '2025_UPDATE_GUIDE.md', 'name': 'Production Update Guide', 'priority': 3}
            ])

        # Filter existing files
        docs = []
        for doc in base_docs:
            doc_path = Path(self.base_path) / doc['file']
            if doc_path.exists():
                docs.append(doc)

        return docs

    def _optimize_context(self, context: Dict[str, Any], token_budget: int) -> Dict[str, Any]:
        """
        Apply token optimization strategies to context.

        Args:
            context: Original context
            token_budget: Maximum tokens allowed

        Returns:
            Optimized context
        """
        # Estimate current token usage (rough approximation: 1 token ≈ 4 characters)
        current_size = len(str(context))
        current_tokens = current_size // 4

        if current_tokens <= token_budget:
            return context

        # Apply optimization strategies
        optimization_ratio = token_budget / current_tokens
        optimized_context = context.copy()

        # 1. Compress data descriptions
        if 'data' in optimized_context:
            optimized_context['data'] = self._compress_data_info(optimized_context['data'], optimization_ratio)

        # 2. Limit notebook descriptions
        if 'notebooks' in optimized_context:
            optimized_context['notebooks'] = self._compress_notebook_info(optimized_context['notebooks'], optimization_ratio)

        # 3. Limit model information
        if 'models' in optimized_context:
            optimized_context['models'] = self._compress_model_info(optimized_context['models'], optimization_ratio)

        # 4. Prioritize features
        if 'features' in optimized_context:
            optimized_context['features'] = self._prioritize_features(optimized_context['features'], optimization_ratio)

        # 5. Compress documentation
        if 'documentation' in optimized_context:
            optimized_context['documentation'] = self._compress_documentation(optimized_context['documentation'], optimization_ratio)

        # Add optimization metadata
        optimized_context['optimization_metadata'] = {
            'original_tokens': current_tokens,
            'optimized_tokens': int(current_tokens * optimization_ratio),
            'compression_ratio': optimization_ratio,
            'savings_percentage': round((1 - optimization_ratio) * 100, 1)
        }

        return optimized_context

    def _compress_data_info(self, data: Dict[str, Any], ratio: float) -> Dict[str, Any]:
        """Compress data information while preserving key details"""
        compressed = {}
        for key, value in data.items():
            if isinstance(value, dict):
                compressed[key] = {k: v for k, v in list(value.items())[:int(len(value) * ratio)]}
            else:
                compressed[key] = value
        return compressed

    def _compress_notebook_info(self, notebooks: List[Dict], ratio: float) -> List[Dict]:
        """Compress notebook information"""
        max_notebooks = max(1, int(len(notebooks) * ratio))
        return notebooks[:max_notebooks]

    def _compress_model_info(self, models: List[Dict], ratio: float) -> List[Dict]:
        """Compress model information"""
        max_models = max(1, int(len(models) * ratio))
        compressed_models = models[:max_models]

        # Keep only essential fields
        essential_fields = ['name', 'type', 'description']
        for model in compressed_models:
            model = {k: v for k, v in model.items() if k in essential_fields}

        return compressed_models

    def _prioritize_features(self, features: List[Dict], ratio: float) -> List[Dict]:
        """Prioritize and limit features"""
        max_features = max(1, int(len(features) * ratio))
        return features[:max_features]

    def _compress_documentation(self, documentation: List[Dict], ratio: float) -> List[Dict]:
        """Compress documentation list"""
        max_docs = max(1, int(len(documentation) * ratio))
        return documentation[:max_docs]

    def _get_notebook_description(self, notebook_path: str) -> str:
        """Get description for a notebook"""
        descriptions = {
            '00_data_dictionary.ipynb': 'Comprehensive overview of all data files',
            '01_intro_to_data.ipynb': 'Introduction to data structure and loading',
            '02_build_simple_rankings.ipynb': 'Build basic team rankings using EPA',
            '03_metrics_comparison.ipynb': 'Compare team metrics visually',
            '04_team_similarity.ipynb': 'Find similar teams using profiles',
            '05_matchup_predictor.ipynb': 'Simple matchup prediction model',
            '06_custom_rankings_by_metric.ipynb': 'Custom rankings by selected metrics',
            '07_drive_efficiency.ipynb': 'Analyze drive-level efficiency',
            '08_offense_vs_defense_comparison.ipynb': 'Compare offense vs defense',
            '09_opponent_adjustments.ipynb': 'Iterative opponent adjustments',
            '10_srs_adjusted_metrics.ipynb': 'SRS-like metric adjustments',
            '11_metric_distribution_explorer.ipynb': 'Explore metric distributions',
            '12_efficiency_dashboards.ipynb': 'Create efficiency dashboards',
            '01_linear_regression_margin.ipynb': 'Predict score margins with linear regression',
            '02_random_forest_team_points.ipynb': 'Predict team points with random forest',
            '03_xgboost_win_probability.ipynb': 'Predict win probability with XGBoost',
            '04_fastai_win_probability.ipynb': 'Neural network for win probability',
            '05_logistic_regression_win_probability.ipynb': 'Logistic regression classifier',
            '06_shap_interpretability.ipynb': 'Explain model predictions with SHAP',
            '07_stacked_ensemble.ipynb': 'Combine multiple models in ensemble'
        }

        notebook_name = Path(notebook_path).name
        return descriptions.get(notebook_name, 'Analytics notebook for college football data')

    def _get_model_description(self, model_file: str) -> str:
        """Get description for a model file"""
        descriptions = {
            'ridge_model_2025.joblib': 'Linear regression model for score margin prediction',
            'xgb_home_win_model_2025.pkl': 'XGBoost classifier for win probability prediction',
            'fastai_home_win_model_2025.pkl': 'Neural network model for classification'
        }
        return descriptions.get(model_file, 'Machine learning model for predictions')

    def _generate_cache_key(self, role: UserRole, request_context: Dict[str, Any]) -> str:
        """Generate cache key for context"""
        # Create a simple cache key based on role and key context elements
        key_elements = [role.value]

        # Add relevant context elements
        if 'notebooks' in request_context:
            key_elements.extend(sorted(request_context['notebooks'][:3]))  # Limit to prevent long keys

        if 'models' in request_context:
            key_elements.extend(sorted(request_context['models'][:2]))

        if 'query_type' in request_context:
            key_elements.append(request_context['query_type'])

        return '_'.join(key_elements)

    def _update_metrics(self, cache_key: str, hit: bool):
        """Update usage metrics"""
        if cache_key not in self.usage_metrics:
            self.usage_metrics[cache_key] = {
                'hits': 0,
                'misses': 0,
                'total_requests': 0
            }

        self.usage_metrics[cache_key]['total_requests'] += 1
        if hit:
            self.usage_metrics[cache_key]['hits'] += 1
        else:
            self.usage_metrics[cache_key]['misses'] += 1

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the context manager"""
        total_requests = sum(metrics['total_requests'] for metrics in self.usage_metrics.values())
        total_hits = sum(metrics['hits'] for metrics in self.usage_metrics.values())

        cache_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_entries': len(self.context_cache),
            'total_requests': total_requests,
            'cache_hit_rate': round(cache_hit_rate, 2),
            'context_profiles': len(self.profiles),
            'token_budgets': {role.value: budget for role, budget in self.token_budgets.items()},
            'supported_roles': [role.value for role in UserRole]
        }

    def clear_cache(self):
        """Clear the context cache"""
        self.context_cache.clear()
        self.usage_metrics.clear()
        logger.info("Context cache cleared")

    def get_context_summary(self, role: UserRole) -> Dict[str, Any]:
        """Get summary of context for a specific role"""
        profile = self.profiles[role]

        return {
            'role': role.value,
            'token_budget': self.token_budgets[role],
            'token_budget_percentage': profile.token_budget_percentage,
            'data_scope': profile.data_scope,
            'focus_areas': profile.focus_areas,
            'notebook_count': len(profile.notebook_access),
            'model_count': len(profile.model_access),
            'feature_count': len(profile.features_priority),
            'cache_entries': len([k for k in self.context_cache.keys() if role.value in k])
        }

    def start_conversation_session(self, user_id: str, initial_query: str) -> str:
        """Start a new conversation session for context tracking"""
        session_id = self._generate_session_id(user_id)
        self.active_sessions[user_id] = session_id

        # Initialize memory if user doesn't exist
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = ConversationMemory(
                user_id=user_id,
                sessions=[],
                recent_turns=[],
                total_conversations=0,
                average_session_length=0.0,
                preferred_topics=[],
                expert_level_assessment="beginner"
            )

        logger.info(f"Started conversation session {session_id} for user {user_id}")
        return session_id

    def add_conversation_turn(self, user_id: str, query: str, response: str,
                           context_used: Dict[str, Any], tokens_used: int,
                           role_detected: UserRole) -> str:
        """Add a conversation turn to memory"""
        session_id = self.active_sessions.get(user_id)
        if not session_id:
            session_id = self.start_conversation_session(user_id, query)

        # Get current turn number
        recent_turns = self.conversation_memory[user_id].recent_turns
        turn_number = len(recent_turns) + 1 if recent_turns else 1

        # Create conversation turn
        turn = ConversationTurn(
            user_id=user_id,
            query=query,
            response=response,
            context_used=context_used,
            timestamp=datetime.now(),
            session_id=session_id,
            turn_number=turn_number,
            tokens_used=tokens_used,
            role_detected=role_detected
        )

        # Add to recent turns (keep last 10 for quick access)
        recent_turns.append(turn)
        if len(recent_turns) > 10:
            recent_turns.pop(0)

        self._save_conversation_memory(user_id)
        logger.debug(f"Added conversation turn {turn_number} for user {user_id}")

        return session_id

    def get_conversation_context(self, user_id: str, max_turns: int = 5) -> Dict[str, Any]:
        """Get conversation memory for context continuity"""
        if user_id not in self.conversation_memory:
            return {}

        memory = self.conversation_memory[user_id]
        recent_turns = memory.recent_turns[-max_turns:] if memory.recent_turns else []

        # Build conversation context
        conversation_context = {
            'user_id': user_id,
            'total_conversations': memory.total_conversations,
            'expert_level_assessment': memory.expert_level_assessment,
            'preferred_topics': memory.preferred_topics,
            'average_session_length': memory.average_session_length,
            'recent_turns': [],
            'session_summaries': []
        }

        # Add recent turns with context
        for turn in recent_turns:
            conversation_context['recent_turns'].append({
                'turn_number': turn.turn_number,
                'query': turn.query,
                'response': turn.response[:200] + "..." if len(turn.response) > 200 else turn.response,
                'timestamp': turn.timestamp.isoformat(),
                'role_detected': turn.role_detected.value,
                'tokens_used': turn.tokens_used
            })

        # Add recent session summaries (last 3 sessions)
        for session in memory.sessions[-3:]:
            conversation_context['session_summaries'].append({
                'session_id': session.session_id,
                'start_time': session.start_time.isoformat(),
                'total_turns': session.total_turns,
                'topics_discussed': session.topics_discussed,
                'key_insights': session.key_insights[:3],  # Top 3 insights
                'session_effectiveness': session.session_effectiveness
            })

        return conversation_context

    def enhance_context_with_memory(self, user_id: str, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance current context with conversation memory"""
        conversation_context = self.get_conversation_context(user_id)

        if not conversation_context:
            return current_context

        # Create enhanced context
        enhanced_context = current_context.copy()

        # Add conversation memory
        enhanced_context['conversation_memory'] = conversation_context

        # Add role progression if detected
        if conversation_context.get('expert_level_assessment'):
            enhanced_context['role_progression'] = {
                'current_assessment': conversation_context['expert_level_assessment'],
                'preferred_topics': conversation_context['preferred_topics'],
                'conversation_count': conversation_context['total_conversations']
            }

        # Add continuity hints
        if conversation_context.get('recent_turns'):
            last_turn = conversation_context['recent_turns'][-1]
            enhanced_context['continuity_hints'] = {
                'last_topic': self._extract_main_topic(last_turn['query']),
                'last_role': last_turn['role_detected'],
                'conversation_momentum': self._calculate_conversation_momentum(conversation_context['recent_turns'])
            }

        logger.info(f"Enhanced context with conversation memory for user {user_id}")
        return enhanced_context

    def end_conversation_session(self, user_id: str, effectiveness_score: float = None) -> Optional[SessionSummary]:
        """End current conversation session and create summary"""
        if user_id not in self.active_sessions:
            return None

        session_id = self.active_sessions[user_id]
        memory = self.conversation_memory[user_id]

        # Get session turns
        session_turns = [turn for turn in memory.recent_turns if turn.session_id == session_id]

        if not session_turns:
            return None

        # Create session summary
        summary = self._create_session_summary(session_id, user_id, session_turns, effectiveness_score)

        # Add to memory
        memory.sessions.append(summary)
        memory.total_conversations += 1
        memory.average_session_length = sum(s.total_turns for s in memory.sessions) / len(memory.sessions)

        # Clear active session
        del self.active_sessions[user_id]

        # Update user preferences and expert level
        self._update_user_preferences(user_id, summary)

        self._save_conversation_memory(user_id)
        logger.info(f"Ended conversation session {session_id} for user {user_id}")

        return summary

    def _generate_session_id(self, user_id: str) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().isoformat()
        raw_string = f"{user_id}_{timestamp}"
        return hashlib.md5(raw_string.encode()).hexdigest()[:12]

    def _extract_main_topic(self, query: str) -> str:
        """Extract main topic from query"""
        query_lower = query.lower()

        # Simple topic extraction
        if any(keyword in query_lower for keyword in ['predict', 'outcome', 'winner']):
            return 'predictions'
        elif any(keyword in query_lower for keyword in ['model', 'algorithm', 'regression']):
            return 'modeling'
        elif any(keyword in query_lower for keyword in ['data', 'dataset', 'features']):
            return 'data_analysis'
        elif any(keyword in query_lower for keyword in ['learn', 'tutorial', 'explain']):
            return 'learning'
        elif any(keyword in query_lower for keyword in ['rank', 'rating', 'best']):
            return 'rankings'
        else:
            return 'general'

    def _calculate_conversation_momentum(self, recent_turns: List[Dict]) -> float:
        """Calculate conversation momentum based on recent activity"""
        if len(recent_turns) < 2:
            return 1.0

        # Calculate based on recency and topic consistency
        latest_turn = recent_turns[-1]
        latest_time = datetime.fromisoformat(latest_turn['timestamp'])
        time_diff = (datetime.now() - latest_time).total_seconds() / 3600  # hours

        # Decay factor based on time
        time_momentum = max(0.1, 1.0 - (time_diff / 24))  # Decay over 24 hours

        # Topic consistency
        topics = [self._extract_main_topic(turn['query']) for turn in recent_turns[-3:]]
        topic_consistency = len(set(topics)) / len(topics) if topics else 1.0
        topic_momentum = 1.0 - topic_consistency  # Higher momentum for topic changes

        return (time_momentum + topic_momentum) / 2

    def _create_session_summary(self, session_id: str, user_id: str,
                              turns: List[ConversationTurn], effectiveness_score: float) -> SessionSummary:
        """Create summary of conversation session"""
        if not turns:
            return None

        start_time = min(turn.timestamp for turn in turns)
        end_time = max(turn.timestamp for turn in turns)
        total_tokens = sum(turn.tokens_used for turn in turns)

        # Extract topics discussed
        topics_discussed = list(set(self._extract_main_topic(turn.query) for turn in turns))

        # Extract key insights (simplified - look for important responses)
        key_insights = []
        for turn in turns:
            if any(keyword in turn.response.lower() for keyword in ['important', 'key', 'critical', 'essential']):
                key_insights.append(turn.response[:150] + "..." if len(turn.response) > 150 else turn.response)

        # User preferences (simplified)
        user_preferences = {
            'preferred_role': turns[-1].role_detected.value if turns else 'analyst',
            'average_tokens_per_turn': total_tokens / len(turns) if turns else 0,
            'session_duration_hours': (end_time - start_time).total_seconds() / 3600
        }

        # Calculate effectiveness if not provided
        if effectiveness_score is None:
            effectiveness_score = self._calculate_session_effectiveness(turns)

        return SessionSummary(
            session_id=session_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            total_turns=len(turns),
            total_tokens=total_tokens,
            topics_discussed=topics_discussed,
            key_insights=key_insights[:5],  # Keep top 5
            user_preferences=user_preferences,
            session_effectiveness=effectiveness_score
        )

    def _calculate_session_effectiveness(self, turns: List[ConversationTurn]) -> float:
        """Calculate session effectiveness score (0-1)"""
        if not turns:
            return 0.5

        # Factors for effectiveness
        factors = []

        # 1. Conversation depth (more turns = deeper engagement)
        depth_score = min(1.0, len(turns) / 10)  # Normalize to 10 turns as ideal
        factors.append(depth_score)

        # 2. Token efficiency (not too short, not too long)
        avg_tokens = sum(turn.tokens_used for turn in turns) / len(turns)
        if 100 <= avg_tokens <= 1000:
            token_score = 1.0
        else:
            token_score = max(0.3, 1.0 - abs(avg_tokens - 500) / 500)
        factors.append(token_score)

        # 3. Role progression (advancing to more complex roles)
        roles = [turn.role_detected for turn in turns]
        if len(set(roles)) > 1:
            role_progression = 0.8
        else:
            role_progression = 0.5
        factors.append(role_progression)

        # 4. Topic diversity (exploring different areas)
        topics = [self._extract_main_topic(turn.query) for turn in turns]
        topic_diversity = len(set(topics) / len(topics)) if topics else 0
        factors.append(topic_diversity)

        return sum(factors) / len(factors)

    def _update_user_preferences(self, user_id: str, session_summary: SessionSummary):
        """Update user preferences based on session summary"""
        memory = self.conversation_memory[user_id]

        # Update preferred topics
        for topic in session_summary.topics_discussed:
            if topic not in memory.preferred_topics:
                memory.preferred_topics.append(topic)

        # Keep only top 5 preferred topics
        if len(memory.preferred_topics) > 5:
            # Count topic frequency
            topic_counts = {}
            for session in memory.sessions:
                for topic in session.topics_discussed:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

            # Keep top 5 most frequent
            sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
            memory.preferred_topics = [topic for topic, count in sorted_topics[:5]]

        # Update expert level based on session effectiveness and complexity
        if session_summary.session_effectiveness > 0.8:
            if memory.expert_level_assessment == "beginner":
                memory.expert_level_assessment = "intermediate"
            elif memory.expert_level_assessment == "intermediate":
                memory.expert_level_assessment = "advanced"

    def _load_conversation_memory(self):
        """Load conversation memory from disk"""
        try:
            memory_file = self.memory_path / "conversation_memory.pkl"
            if memory_file.exists():
                with open(memory_file, 'rb') as f:
                    self.conversation_memory = pickle.load(f)
                logger.info(f"Loaded conversation memory for {len(self.conversation_memory)} users")
        except Exception as e:
            logger.warning(f"Failed to load conversation memory: {e}")
            self.conversation_memory = {}

    def _save_conversation_memory(self, user_id: str = None):
        """Save conversation memory to disk"""
        try:
            memory_file = self.memory_path / "conversation_memory.pkl"

            if user_id:
                # Save specific user memory
                if user_id in self.conversation_memory:
                    temp_memory = {user_id: self.conversation_memory[user_id]}
                    with open(memory_file, 'wb') as f:
                        pickle.dump(temp_memory, f)
            else:
                # Save all memory
                with open(memory_file, 'wb') as f:
                    pickle.dump(self.conversation_memory, f)

        except Exception as e:
            logger.warning(f"Failed to save conversation memory: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Initialize Context Manager
    cm = ContextManager()

    # Test role detection
    test_contexts = [
        {
            'notebooks': ['starter_pack/01_intro_to_data.ipynb'],
            'models': ['ridge_model_2025.joblib'],
            'query_type': 'learn about college football data'
        },
        {
            'notebooks': ['model_pack/06_shap_interpretability.ipynb'],
            'models': ['xgb_home_win_model_2025.pkl', 'fastai_home_win_model_2025.pkl'],
            'query_type': 'advanced feature engineering and model optimization'
        },
        {
            'models': ['ridge_model_2025.joblib'],
            'query_type': 'predict game outcomes for production use'
        }
    ]

    print("=== Context Manager Testing ===")

    for i, test_context in enumerate(test_contexts, 1):
        print(f"\nTest Case {i}:")
        print(f"Input context: {test_context}")

        # Detect role
        detected_role = cm.detect_user_role(test_context)
        print(f"Detected role: {detected_role.value}")

        # Load context
        context = cm.load_context_for_role(detected_role, test_context)
        print(f"Context loaded with {len(context)} keys")

        # Show context summary
        summary = cm.get_context_summary(detected_role)
        print(f"Context summary: {summary}")

    # Show performance metrics
    print(f"\n=== Performance Metrics ===")
    metrics = cm.get_performance_metrics()
    print(json.dumps(metrics, indent=2))