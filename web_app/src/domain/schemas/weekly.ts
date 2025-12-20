import { z } from "zod";

/**
 * Prediction result schema
 */
export const PredictionResultSchema = z.object({
  predictedMargin: z.string(),
  confidence: z.string(),
  lineValue: z.string(),
  valueRating: z.string(),
  winner: z.string(),
  suggestedSide: z.string(),
});

/**
 * Weekly game prediction schema
 * Matches the structure from predictions/week{N}/week{N}_model_predictions.json
 */
export const WeeklyGameSchema = z.object({
  game_id: z.number(),
  season: z.number(),
  week: z.number(),
  home_team: z.string(),
  away_team: z.string(),
  start_date: z.string().optional(),
  home_conference: z.string().optional(),
  away_conference: z.string().optional(),
  spread: z.number().nullable().optional(),
  ridge_predicted_margin: z.number().optional(),
  predicted_margin: z.number(),
  ridge_home_win_probability: z.number().optional(),
  xgb_home_win_probability: z.number().optional(),
  fastai_home_win_probability: z.number().optional(),
  ensemble_margin: z.number().optional(),
  ensemble_home_win_probability: z.number().optional(),
  ensemble_away_win_probability: z.number().optional(),
  ensemble_confidence: z.number().optional(),
  models_used: z.string().optional(),
  model_agreement: z.enum(["high", "moderate", "low"]).optional(),
  home_win_probability: z.number().optional(),
  away_win_probability: z.number().optional(),
  predicted_winner: z.string().optional(),
});

export const WeeklyPredictionsResponseSchema = z.array(WeeklyGameSchema);

/**
 * Inferred TypeScript types
 */
export type WeeklyGame = z.infer<typeof WeeklyGameSchema>;
export type PredictionResult = z.infer<typeof PredictionResultSchema>;
export type WeeklyPredictionsResponse = z.infer<
  typeof WeeklyPredictionsResponseSchema
>;
