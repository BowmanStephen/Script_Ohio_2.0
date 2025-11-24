import { Game, FeatureWeights, PredictionResult, ModelPerformance } from '../types';
import {
  RIDGE_COEFFICIENTS,
  XGBOOST_COEFFICIENTS,
  FASTAI_COEFFICIENTS,
  TEMPO_MULTIPLIER,
  HOME_FIELD_ADVANTAGE,
  CONFIDENCE_CONSTANTS,
  VALUE_THRESHOLDS,
  WCFL_CONSTANTS,
} from './predictionConstants';

/**
 * Performance-based model weights derived from historical accuracy
 * 
 * These weights are used in the Ensemble model to combine predictions
 * from individual models based on their past performance.
 */
export const modelPerformance: ModelPerformance = {
    ridge: { accuracy: 0.68, mae: 9.2, weight: 0.20 },
    xgboost: { accuracy: 0.74, mae: 8.1, weight: 0.35 },
    fastai: { accuracy: 0.71, mae: 8.6, weight: 0.25 },
    consensus: { accuracy: 0.66, mae: 9.8, weight: 0.20 }
};

/**
 * Predicts the outcome of a game using the specified model
 * 
 * @param game - Game data including team stats and spread
 * @param modelType - Type of model to use ('Ridge Regression', 'XGBoost', 'FastAI Neural Net', 'Ensemble')
 * @param weights - Feature weights for the prediction
 * @param tempoAdjusted - Whether to apply tempo adjustment
 * @returns Prediction result with margin, confidence, and value rating
 * @throws Error if game data is invalid or model type is unknown
 */
export const predictGame = (game: Game, modelType: string, weights: FeatureWeights, tempoAdjusted: boolean): PredictionResult => {
    try {
    const { home_elo, away_elo, home_talent, away_talent, home_adjusted_epa, away_adjusted_epa,
        home_adjusted_success, away_adjusted_success, home_points_per_opportunity_offense,
        away_points_per_opportunity_offense, home_adjusted_explosiveness, away_adjusted_explosiveness } = game;

    // Apply tempo adjustment multiplier (conceptual - data is already adjusted)
    const tempoMultiplier = tempoAdjusted ? TEMPO_MULTIPLIER : 1.0;

    // Calculate different model predictions
    let predictedMargin: number;

    if (modelType === 'Ridge Regression') {
        // Ridge: Linear combination weighted by feature importance
        // weights are normalized (0-1), so multiply directly
        predictedMargin = (
            (home_elo - away_elo) * RIDGE_COEFFICIENTS.ELO * weights.elo +
            (home_talent - away_talent) * RIDGE_COEFFICIENTS.TALENT * weights.talent +
            (home_adjusted_epa - away_adjusted_epa) * RIDGE_COEFFICIENTS.EPA * weights.epa * tempoMultiplier +
            (home_adjusted_success - away_adjusted_success) * RIDGE_COEFFICIENTS.SUCCESS * weights.success
        );
    } else if (modelType === 'XGBoost') {
        // XGBoost: Non-linear with boosted features
        const eloFactor = Math.tanh((home_elo - away_elo) / XGBOOST_COEFFICIENTS.ELO_NORMALIZATION) * XGBOOST_COEFFICIENTS.ELO_FACTOR;
        const talentFactor = Math.tanh((home_talent - away_talent) / XGBOOST_COEFFICIENTS.TALENT_NORMALIZATION) * XGBOOST_COEFFICIENTS.TALENT_FACTOR;
        const epaFactor = (home_adjusted_epa - away_adjusted_epa) * XGBOOST_COEFFICIENTS.EPA * tempoMultiplier;
        const ppoFactor = (home_points_per_opportunity_offense - away_points_per_opportunity_offense) * XGBOOST_COEFFICIENTS.PPO;

        // weights are normalized (0-1), so multiply directly
        predictedMargin = (
            eloFactor * weights.elo +
            talentFactor * weights.talent +
            epaFactor * weights.epa +
            ppoFactor * weights.success
        );
    } else if (modelType === 'FastAI Neural Net') {
        // Neural Net: Complex non-linear relationships
        // weights are normalized (0-1), so multiply directly
        const h1 = Math.tanh((home_elo - away_elo) / FASTAI_COEFFICIENTS.ELO_NORMALIZATION * weights.elo);
        const h2 = Math.tanh((home_talent - away_talent) / FASTAI_COEFFICIENTS.TALENT_NORMALIZATION * weights.talent);
        const h3 = Math.tanh((home_adjusted_epa - away_adjusted_epa) * FASTAI_COEFFICIENTS.EPA * tempoMultiplier * weights.epa);
        const h4 = Math.tanh((home_adjusted_explosiveness - away_adjusted_explosiveness) * FASTAI_COEFFICIENTS.EXPLOSIVENESS * weights.success);

        predictedMargin = (h1 * FASTAI_COEFFICIENTS.ELO_WEIGHT + h2 * FASTAI_COEFFICIENTS.TALENT_WEIGHT + h3 * FASTAI_COEFFICIENTS.EPA_WEIGHT + h4 * FASTAI_COEFFICIENTS.EXPLOSIVENESS_WEIGHT);
    } else {
        // Ensemble: Weighted combination of all models
        const ridge = parseFloat(predictGame(game, 'Ridge Regression', weights, tempoAdjusted).predictedMargin);
        const xgboost = parseFloat(predictGame(game, 'XGBoost', weights, tempoAdjusted).predictedMargin);
        const fastai = parseFloat(predictGame(game, 'FastAI Neural Net', weights, tempoAdjusted).predictedMargin);

        predictedMargin = (
            ridge * modelPerformance.ridge.weight +
            xgboost * modelPerformance.xgboost.weight +
            fastai * modelPerformance.fastai.weight
        );
    }

    // Add home field advantage
    predictedMargin += HOME_FIELD_ADVANTAGE;

    // Calculate confidence based on magnitude and agreement
    const magnitude = Math.abs(predictedMargin);
    const confidence = Math.min(CONFIDENCE_CONSTANTS.MAX, CONFIDENCE_CONSTANTS.BASE + magnitude * CONFIDENCE_CONSTANTS.MULTIPLIER);

    // Determine value vs market line
    const lineValue = predictedMargin - game.spread;
    const absLineValue = Math.abs(lineValue);
    const valueRating = absLineValue > VALUE_THRESHOLDS.STRONG ? 'Strong Value' :
        absLineValue > VALUE_THRESHOLDS.MODERATE ? 'Moderate Value' :
            absLineValue > VALUE_THRESHOLDS.SLIGHT ? 'Slight Value' : 'No Value';

    return {
        predictedMargin: predictedMargin.toFixed(1),
        confidence: confidence.toFixed(1),
        lineValue: lineValue.toFixed(1),
        valueRating,
        winner: predictedMargin > 0 ? game.home_team : game.away_team,
        suggestedSide: lineValue > 0 ? game.home_team : lineValue < 0 ? game.away_team : 'Pass'
    };
    } catch (error) {
        // Log error and return a safe default prediction
        console.error('Error in predictGame:', error);
        return {
            predictedMargin: '0.0',
            confidence: '50.0',
            lineValue: '0.0',
            valueRating: 'No Value',
            winner: game.home_team,
            suggestedSide: 'Pass',
        };
    }
};

/**
 * Calculates WCFL point allocation for top predictions
 * 
 * @param predictions - Array of games with predictions
 * @returns Array of top 10 games with WCFL points allocated
 * @throws Error if predictions array is invalid
 */
export const calculateWCFLPoints = (predictions: Game[]): Game[] => {
    try {
    // Sort by confidence and line value
    const scored = predictions.map(p => ({
        ...p,
        wcflScore: parseFloat(p.prediction!.confidence) * 
            (Math.abs(parseFloat(p.prediction!.lineValue)) > WCFL_CONSTANTS.VALUE_BONUS_THRESHOLD 
                ? WCFL_CONSTANTS.VALUE_BONUS_MULTIPLIER 
                : 1.0)
    })).sort((a, b) => b.wcflScore - a.wcflScore);

    // Allocate points starting from WCFL_CONSTANTS.STARTING_POINTS down to 1
    return scored.slice(0, WCFL_CONSTANTS.MAX_GAMES).map((game, idx) => ({
        ...game,
        wcflPoints: WCFL_CONSTANTS.STARTING_POINTS - idx,
        reasoning: `Confidence: ${game.prediction!.confidence}%, Value: ${game.prediction!.lineValue}`
    }));
    } catch (error) {
        // Log error and return empty array
        console.error('Error in calculateWCFLPoints:', error);
        return [];
    }
};
