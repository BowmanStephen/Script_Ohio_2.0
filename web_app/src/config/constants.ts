/**
 * Application-wide constants
 * Centralizes hardcoded values for easier maintenance
 */

const CURRENT_WEEK_VALUE = 14;

export const APP_CONSTANTS = {
    // Current week configuration
    CURRENT_WEEK: CURRENT_WEEK_VALUE,
    DEFAULT_SEASON: 2025,

    // ATS data paths (dynamically use current week)
    ATS_DATA_PATHS: {
        JSON: () => `/week${CURRENT_WEEK_VALUE}_ats_data.json`,
        CSV: () => `/week${CURRENT_WEEK_VALUE}_ats_full_table.csv`,
    },

    // Prediction data paths (served from /public)
    PREDICTIONS_DATA_PATHS: {
        JSON: () => `/week${CURRENT_WEEK_VALUE}_model_predictions.json`,
        CSV: () => `/week${CURRENT_WEEK_VALUE}_model_predictions.csv`,
    },

    // File naming patterns
    FILE_NAMES: {
        ATS_EXPORT: () => `week${CURRENT_WEEK_VALUE}_ats_analysis.csv`,
        PREDICTIONS_EXPORT: (week: number | null) => `predictions_week${week || 'all'}.csv`,
        WCFL_EXPORT: (week: number) => `wcfl_week${week}_picks.csv`,
    },

    // UI Configuration
    UI: {
        MIN_EDGE_THRESHOLD: 5,
        TOP_PICKS_COUNT: 3,
        DEFAULT_MODEL: 'Ensemble',
        TRAINING_INTERVAL: 20, // ms per training step
        TRAINING_STEPS: 100,
    },

    // Feature weights defaults
    FEATURE_WEIGHTS: {
        DEFAULT: {
            elo: 0.25,
            talent: 0.25,
            epa: 0.35,
            success: 0.15
        }
    },

    // Model configuration
    MODELS: {
        AVAILABLE: ['Ensemble', 'Ridge', 'XGBoost', 'FastAI'] as const,
        DEFAULT_WEIGHTS: {
            accuracy: 0.4,
            mae: 0.3,
            recent_performance: 0.3
        }
    }
} as const;

// Type exports for better TypeScript support
export type AvailableModel = typeof APP_CONSTANTS.MODELS.AVAILABLE[number];
export type FeatureWeightKey = keyof typeof APP_CONSTANTS.FEATURE_WEIGHTS.DEFAULT;
