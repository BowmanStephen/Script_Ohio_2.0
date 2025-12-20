/**
 * Re-export all domain types for convenience
 */
export type {
  WeeklyGame,
  PredictionResult,
  WeeklyPredictionsResponse,
} from "../schemas/weekly";
export type {
  BowlGame,
  BowlPredictionsResponse,
} from "../schemas/bowls";
export type {
  ModelMetric,
  ModelPerformance,
  ModelDetails,
} from "../schemas/models";
export type {
  ExternalModel,
  ExternalModelAnalysis,
} from "../schemas/analytics";
