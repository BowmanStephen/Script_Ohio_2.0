/**
 * Live API Client for Script Ohio 2.0 Predictions
 *
 * This client fetches live data from the Flask API server instead of static JSON files.
 * Provides the same interface as the existing loadPredictionsData function.
 */

import { APP_CONSTANTS } from '../config/constants';
import { Game, PredictionResult, ATSAnalysis } from '../types';
import { week14Games } from '../data/week14Games';

// API Configuration
const API_BASE_URL = 'http://localhost:5001';
const API_TIMEOUT = 10000; // 10 seconds

// Type definitions for API responses
interface ApiPredictionsResponse {
    week: number;
    season: number;
    total_games: number;
    predictions: any[]; // Raw prediction data from API
    api_metadata: {
        timestamp: string;
        source: string;
        note: string;
    };
}

interface ApiStatsResponse {
    system_status: string;
    agent_system: {
        initialized: boolean;
        model_agent_available: boolean;
        registered_agents: number;
        active_agents: number;
    };
    api_info: {
        version: string;
        endpoints: string[];
    };
    timestamp: string;
}

interface ApiHealthResponse {
    status: string;
    timestamp: string;
    agent_system: boolean;
    version: string;
}

/**
 * Helper function to format percentages consistently (copied from MLSimulator)
 */
const formatPercent = (value: string | number | undefined): string => {
    const parsed = typeof value === 'number' ? value : parseFloat(value || '0');
    const clamped = Math.min(100, Math.max(0, parsed));
    return clamped.toFixed(1);
};

/**
 * Transform API prediction data to match existing frontend format
 */
const transformApiPrediction = (apiPrediction: any): Game | null => {
    const id = apiPrediction.game_id;
    if (!id) return null;

    // Find matching game in week14Games for additional data
    const baseGame = week14Games.find((g) => g.id === id);
    const homeTeam = apiPrediction.home_team || baseGame?.home_team;
    const awayTeam = apiPrediction.away_team || baseGame?.away_team;

    if (!homeTeam || !awayTeam) {
        return null;
    }

    const spread = apiPrediction.spread ?? baseGame?.spread ?? 0;
    // Prefer calibrated predictions if available, then ensemble, then individual models
    const predictedMargin = apiPrediction.calibrated_margin ?? apiPrediction.market_adjusted_margin ?? apiPrediction.ensemble_margin ?? apiPrediction.predicted_margin ?? apiPrediction.ridge_predicted_margin ?? 0;

    const homeWinProb = apiPrediction.calibrated_home_win_prob ?? apiPrediction.home_win_probability ?? apiPrediction.ensemble_home_win_probability ?? apiPrediction.ridge_home_win_probability ?? 0.5;
    const awayWinProb = apiPrediction.away_win_probability ?? apiPrediction.ensemble_away_win_probability ?? (1 - homeWinProb);

    const winnerIsHome = predictedMargin >= 0;
    const winner = winnerIsHome ? homeTeam : awayTeam;
    const lineValue = predictedMargin - spread;
    const confidenceProb = winnerIsHome ? homeWinProb : awayWinProb;
    const confidencePercent = Math.max(0, Math.min(100, confidenceProb * 100));

    // Build prediction result object
    const prediction: PredictionResult = {
        predictedMargin: predictedMargin.toFixed(1),
        confidence: confidencePercent.toFixed(1),
        lineValue: lineValue.toFixed(1),
        valueRating: getValueRating(lineValue),
        winner,
        suggestedSide: buildSuggestedSide(lineValue, spread, homeTeam, awayTeam),
    };

    const fallbackGame: Game = {
        id,
        home_team: homeTeam,
        away_team: awayTeam,
        spread,
        home_elo: 0,
        away_elo: 0,
        home_talent: 0,
        away_talent: 0,
        home_adjusted_epa: 0,
        away_adjusted_epa: 0,
        home_adjusted_success: 0,
        away_adjusted_success: 0,
        home_adjusted_explosiveness: 0,
        away_adjusted_explosiveness: 0,
        home_points_per_opportunity_offense: 0,
        away_points_per_opportunity_offense: 0,
    };

    return {
        ...(baseGame ?? fallbackGame),
        spread,
        week: (apiPrediction.week ?? baseGame?.week ?? APP_CONSTANTS.CURRENT_WEEK) as number,
        prediction,
    };
};

/**
 * Helper functions for value calculation (copied from loadPredictionsData)
 */
const VALUE_THRESHOLDS = {
    SLIGHT: 3,
    MODERATE: 6,
    STRONG: 10,
} as const;

const getValueRating = (lineValue: number): string => {
    const absLineValue = Math.abs(lineValue);
    if (absLineValue > VALUE_THRESHOLDS.STRONG) return 'Strong Value';
    if (absLineValue > VALUE_THRESHOLDS.MODERATE) return 'Moderate Value';
    if (absLineValue > VALUE_THRESHOLDS.SLIGHT) return 'Slight Value';
    return 'No Value';
};

const buildSuggestedSide = (lineValue: number, spread: number, homeTeam: string, awayTeam: string): string => {
    if (Math.abs(lineValue) < 0.5) return 'Pass';

    if (lineValue >= 0) {
        const spreadDisplay = spread >= 0 ? `+${spread}` : `${spread}`;
        return `${homeTeam} ${spreadDisplay}`;
    }

    const awaySpread = -spread;
    const spreadDisplay = awaySpread >= 0 ? `+${awaySpread}` : `${awaySpread}`;
    return `${awayTeam} ${spreadDisplay}`;
};

/**
 * Check if the API server is available
 */
export async function checkApiHealth(): Promise<boolean> {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(API_TIMEOUT),
        });

        if (response.ok) {
            const health: ApiHealthResponse = await response.json();
            return health.status === 'healthy' && health.agent_system;
        }
        return false;
    } catch (error) {
        console.warn('API health check failed:', error);
        return false;
    }
}

/**
 * Load predictions from the live API server
 * Falls back to static data if API is unavailable
 */
export async function loadLivePredictionsData(): Promise<Game[]> {
    try {
        // Check if API is available first
        const isApiHealthy = await checkApiHealth();
        if (!isApiHealthy) {
            console.warn('API server is not available, falling back to static data');
            return loadStaticPredictionsData();
        }

        // Fetch predictions from API
        const response = await fetch(`${API_BASE_URL}/api/predictions/week/${APP_CONSTANTS.CURRENT_WEEK}`, {
            method: 'GET',
            signal: AbortSignal.timeout(API_TIMEOUT),
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch predictions from API: ${response.status}`);
        }

        const apiData: ApiPredictionsResponse = await response.json();

        // Transform API data to frontend format
        const games = apiData.predictions
            .map(transformApiPrediction)
            .filter((game): game is Game => game !== null);

        if (games.length > 0) {
            console.log(`✅ Loaded ${games.length} predictions from live API server`);
            return games;
        } else {
            throw new Error('No valid prediction data received from API');
        }

    } catch (error) {
        console.warn('Failed to load predictions from API, falling back to static data:', error);
        return loadStaticPredictionsData();
    }
}

/**
 * Load static predictions data (fallback mechanism)
 */
async function loadStaticPredictionsData(): Promise<Game[]> {
    try {
        // Import the existing function to maintain compatibility
        const { loadPredictionsData } = await import('./loadPredictionsData');
        return await loadPredictionsData(
            APP_CONSTANTS.PREDICTIONS_DATA_PATHS.JSON(),
            APP_CONSTANTS.PREDICTIONS_DATA_PATHS.CSV()
        );
    } catch (error) {
        console.error('Failed to load static predictions data:', error);
        throw new Error('Unable to load predictions from any source');
    }
}

/**
 * Load ATS data from the live API server
 * Falls back to static data if API is unavailable
 */
export async function loadLiveATSData(): Promise<ATSAnalysis[]> {
    try {
        // Check if API is available first
        const isApiHealthy = await checkApiHealth();
        if (!isApiHealthy) {
            console.warn('API server is not available, falling back to static ATS data');
            return loadStaticATSData();
        }

        // Try to get ATS data from API (if endpoint exists)
        const response = await fetch(`${API_BASE_URL}/api/ats/week/${APP_CONSTANTS.CURRENT_WEEK}`, {
            method: 'GET',
            signal: AbortSignal.timeout(API_TIMEOUT),
        });

        if (response.ok) {
            const atsData = await response.json();
            console.log(`✅ Loaded ATS data from live API server`);
            return atsData;
        } else {
            // ATS endpoint might not exist, fallback to static
            console.warn('ATS endpoint not available, falling back to static data');
            return loadStaticATSData();
        }

    } catch (error) {
        console.warn('Failed to load ATS data from API, falling back to static data:', error);
        return loadStaticATSData();
    }
}

/**
 * Load static ATS data (fallback mechanism)
 */
async function loadStaticATSData(): Promise<ATSAnalysis[]> {
    try {
        // Import the existing function to maintain compatibility
        const { loadATSData } = await import('./loadATSData');
        return await loadATSData(APP_CONSTANTS.ATS_DATA_PATHS.JSON());
    } catch (error) {
        console.error('Failed to load static ATS data:', error);
        throw new Error('Unable to load ATS data from any source');
    }
}

/**
 * Get system statistics from the API
 */
export async function getApiStats(): Promise<ApiStatsResponse | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`, {
            method: 'GET',
            signal: AbortSignal.timeout(API_TIMEOUT),
        });

        if (response.ok) {
            const stats: ApiStatsResponse = await response.json();
            return stats;
        }
        return null;
    } catch (error) {
        console.warn('Failed to fetch API stats:', error);
        return null;
    }
}

/**
 * Make a single game prediction request
 */
export async function predictGame(homeTeam: string, awayTeam: string, modelType: string = 'ridge_model_2025'): Promise<any> {
    try {
        const params = new URLSearchParams({
            home_team: homeTeam,
            away_team: awayTeam,
            model_type: modelType,
        });

        const response = await fetch(`${API_BASE_URL}/api/predict?${params}`, {
            method: 'GET',
            signal: AbortSignal.timeout(API_TIMEOUT),
        });

        if (!response.ok) {
            throw new Error(`Prediction request failed: ${response.status}`);
        }

        const result = await response.json();
        return result;

    } catch (error) {
        console.error('Failed to make prediction request:', error);
        throw error;
    }
}

/**
 * Compatibility function that matches the existing loadPredictionsData interface
 * This allows us to swap the implementation without changing the calling code
 */
export const loadPredictionsData = loadLivePredictionsData;
export const loadATSData = loadLiveATSData;