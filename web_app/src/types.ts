export interface Game {
    id: number;
    home_team: string;
    away_team: string;
    spread: number;
    home_elo: number;
    away_elo: number;
    home_talent: number;
    away_talent: number;
    home_adjusted_epa: number;
    away_adjusted_epa: number;
    home_adjusted_success: number;
    away_adjusted_success: number;
    home_adjusted_explosiveness: number;
    away_adjusted_explosiveness: number;
    home_points_per_opportunity_offense: number;
    away_points_per_opportunity_offense: number;
    prediction?: PredictionResult;
    wcflPoints?: number;
    reasoning?: string;
}

export interface FeatureWeights {
    elo: number;
    talent: number;
    epa: number;
    success: number;
    [key: string]: number;
}

export interface PredictionResult {
    predictedMargin: string;
    confidence: string;
    lineValue: string;
    valueRating: string;
    winner: string;
    suggestedSide: string;
}

export interface ModelMetric {
    accuracy: number;
    mae: number;
    weight: number;
}

export interface ModelPerformance {
    ridge: ModelMetric;
    xgboost: ModelMetric;
    fastai: ModelMetric;
    consensus: ModelMetric;
    [key: string]: ModelMetric;
}

export interface TrainingHistory {
    epoch: number;
    loss: number;
    val_loss: number;
    accuracy: number;
}

export interface ModelMetricsState {
    accuracy: number;
    mae: number;
    rmse: number;
    r2: number;
}
