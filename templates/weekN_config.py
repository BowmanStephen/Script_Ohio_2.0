# Week N Configuration Template
# Generated from Week 13 configuration - 2025-11-20 20:41:26

# Week Specific Configuration
WEEK_NUMBER = 13  # Replace with target week
SEASON_YEAR = 2025

# Data Configuration
DATA_CONFIG = {
    "cfbd_api_url": "https://api.collegefootballdata.com",
    "rate_limit": 6,  # requests per second
    "feature_count": 86,  # opponent-adjusted features
    "required_columns": [  # Validate these columns exist
        "home_team", "away_team", "week", "season"
    ]
}

# Model Configuration
MODEL_CONFIG = {
    "ridge": {
        "model_file": "model_pack/ridge_model_2025.joblib",
        "prediction_type": "margin",
        "confidence_threshold": 0.7
    },
    "xgboost": {
        "model_file": "model_pack/xgb_home_win_model_2025.pkl",
        "prediction_type": "probability",
        "confidence_threshold": 0.6
    },
    "fastai": {
        "model_file": "model_pack/fastai_home_win_model_2025.pkl",
        "prediction_type": "probability",
        "confidence_threshold": 0.65
    }
}

# Analysis Configuration
ANALYSIS_CONFIG = {
    "components": [
        "head_to_head_analysis",
        "team_strength_metrics",
        "matchup_insights",
        "situational_factors",
        "advanced_statistics",
        "strategic_recommendations"
    ],
    "output_formats": ["json", "csv", "html", "markdown"],
    "min_confidence_display": 0.5
}

# Performance Targets
PERFORMANCE_CONFIG = {
    "max_response_time_seconds": 2.0,
    "max_memory_usage_mb": 512,
    "max_processing_time_minutes": 180,  # 3 hours
    "min_model_accuracy": 0.40
}

# Quality Gates
QUALITY_CONFIG = {
    "min_games_analyzed": 30,
    "max_missing_features_percent": 5,
    "min_confidence_score": 0.3,
    "required_output_files": [
        "predictions_csv",
        "predictions_json",
        "analysis_json",
        "dashboard_html"
    ]
}

# Notification Configuration
NOTIFICATION_CONFIG = {
    "error_email": "admin@example.com",
    "success_email": "team@example.com",
    "webhook_url": "https://hooks.slack.com/your-webhook",
    "notify_on_completion": True,
    "notify_on_errors": True
}

# Automation Configuration
AUTOMATION_CONFIG = {
    "parallel_feature_generation": True,
    "cache_api_responses": True,
    "auto_validate_outputs": True,
    "auto_generate_documentation": True,
    "retry_failed_operations": True,
    "max_retries": 3
}

# Week 13 Specific Settings (for reference)
WEEK13_REFERENCE = {
    "total_games_analyzed": 47,
    "processing_time_minutes": 15,
    "model_accuracy": {
        "ridge_mae": 17.31,
        "xgboost_accuracy": 0.431,
        "ensemble_performance": "excellent"
    },
    "data_quality_score": 0.95,
    "user_satisfaction": 4.6
}
