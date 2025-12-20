import { z } from "zod";

/**
 * Bowl game prediction schema
 * Matches the structure from data/outputs/predictions/2025/bowl_season/*.json
 */
export const BowlGameSchema = z.object({
  id: z.number(),
  date: z.string(),
  home_team: z.string(),
  away_team: z.string(),
  home_win_prob: z.number().optional(),
  predicted_margin: z.number(),
  bowl_name: z.string().optional(),
  stadium: z.string().optional(),
  location: z.string().optional(),
  conference: z.string().optional(),
});

/**
 * Bowl predictions response schema
 */
export const BowlPredictionsResponseSchema = z.object({
  generated_at: z.string(),
  season: z.number(),
  model_type: z.string().optional(),
  model: z
    .object({
      name: z.string().optional(),
      ridge_model: z.string().optional(),
      xgb_model: z.string().optional(),
    })
    .optional(),
  games: z.array(BowlGameSchema),
  diagnostics: z
    .object({
      total_games: z.number(),
    })
    .optional(),
});

/**
 * Inferred TypeScript types
 */
export type BowlGame = z.infer<typeof BowlGameSchema>;
export type BowlPredictionsResponse = z.infer<
  typeof BowlPredictionsResponseSchema
>;
