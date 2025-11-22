import { Game, FeatureWeights, PredictionResult, ModelPerformance } from '../types';

// Performance-based model weights (from historical accuracy)
export const modelPerformance: ModelPerformance = {
    ridge: { accuracy: 0.68, mae: 9.2, weight: 0.20 },
    xgboost: { accuracy: 0.74, mae: 8.1, weight: 0.35 },
    fastai: { accuracy: 0.71, mae: 8.6, weight: 0.25 },
    consensus: { accuracy: 0.66, mae: 9.8, weight: 0.20 }
};

// Simulate model prediction with different approaches
export const predictGame = (game: Game, modelType: string, weights: FeatureWeights, tempoAdjusted: boolean): PredictionResult => {
    const { home_elo, away_elo, home_talent, away_talent, home_adjusted_epa, away_adjusted_epa,
        home_adjusted_success, away_adjusted_success, home_points_per_opportunity_offense,
        away_points_per_opportunity_offense, home_adjusted_explosiveness, away_adjusted_explosiveness } = game;

    // Apply tempo adjustment multiplier (conceptual - data is already adjusted)
    const tempoMultiplier = tempoAdjusted ? 1.15 : 1.0;

    // Calculate different model predictions
    let predictedMargin: number;

    if (modelType === 'Ridge Regression') {
        // Ridge: Linear combination weighted by feature importance
        predictedMargin = (
            (home_elo - away_elo) * 0.015 * weights.elo / 100 +
            (home_talent - away_talent) * 0.012 * weights.talent / 100 +
            (home_adjusted_epa - away_adjusted_epa) * 45 * weights.epa / 100 * tempoMultiplier +
            (home_adjusted_success - away_adjusted_success) * 25 * weights.success / 100
        );
    } else if (modelType === 'XGBoost') {
        // XGBoost: Non-linear with boosted features
        const eloFactor = Math.tanh((home_elo - away_elo) / 200) * 12;
        const talentFactor = Math.tanh((home_talent - away_talent) / 100) * 10;
        const epaFactor = (home_adjusted_epa - away_adjusted_epa) * 50 * tempoMultiplier;
        const ppoFactor = (home_points_per_opportunity_offense - away_points_per_opportunity_offense) * 8;

        predictedMargin = (
            eloFactor * weights.elo / 100 +
            talentFactor * weights.talent / 100 +
            epaFactor * weights.epa / 100 +
            ppoFactor * weights.success / 100
        );
    } else if (modelType === 'FastAI Neural Net') {
        // Neural Net: Complex non-linear relationships
        const h1 = Math.tanh((home_elo - away_elo) / 150 * weights.elo / 100);
        const h2 = Math.tanh((home_talent - away_talent) / 80 * weights.talent / 100);
        const h3 = Math.tanh((home_adjusted_epa - away_adjusted_epa) * 40 * tempoMultiplier * weights.epa / 100);
        const h4 = Math.tanh((home_adjusted_explosiveness - away_adjusted_explosiveness) * 35 * weights.success / 100);

        predictedMargin = (h1 * 8 + h2 * 7 + h3 * 12 + h4 * 6);
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
    predictedMargin += 2.5;

    // Calculate confidence based on magnitude and agreement
    const magnitude = Math.abs(predictedMargin);
    const confidence = Math.min(95, 50 + magnitude * 2.5);

    // Determine value vs market line
    const lineValue = predictedMargin - game.spread;
    const valueRating = Math.abs(lineValue) > 7 ? 'Strong Value' :
        Math.abs(lineValue) > 4 ? 'Moderate Value' :
            Math.abs(lineValue) > 2 ? 'Slight Value' : 'No Value';

    return {
        predictedMargin: predictedMargin.toFixed(1),
        confidence: confidence.toFixed(1),
        lineValue: lineValue.toFixed(1),
        valueRating,
        winner: predictedMargin > 0 ? game.home_team : game.away_team,
        suggestedSide: lineValue > 0 ? game.home_team : lineValue < 0 ? game.away_team : 'Pass'
    };
};

// Calculate WCFL point allocation
export const calculateWCFLPoints = (predictions: Game[]): Game[] => {
    // Sort by confidence and line value
    const scored = predictions.map(p => ({
        ...p,
        wcflScore: parseFloat(p.prediction!.confidence) * (Math.abs(parseFloat(p.prediction!.lineValue)) > 3 ? 1.5 : 1.0)
    })).sort((a, b) => b.wcflScore - a.wcflScore);

    // Allocate points 10-1
    return scored.slice(0, 10).map((game, idx) => ({
        ...game,
        wcflPoints: 10 - idx,
        reasoning: `Confidence: ${game.prediction!.confidence}%, Value: ${game.prediction!.lineValue}`
    }));
};
