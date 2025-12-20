import { z } from "zod";

/**
 * External model analysis schema
 * Matches data/outputs/analysis/external_model_analysis_*.json
 */
export const ExternalModelSchema = z.object({
  name: z.string(),
  straightUpAccuracy: z.number(),
  vsSpreadAccuracy: z.number().optional(),
  methodology: z.string().optional(),
  researchConfidence: z.string().optional(),
  isScriptOhio: z.boolean().optional(),
  dataSources: z.array(z.string()).optional(),
  updateFrequency: z.string().optional(),
  coverage: z.string().optional(),
  ranking: z.number().optional(),
});

export const ExternalModelAnalysisSchema = z.object({
  models: z.array(ExternalModelSchema),
  insights: z
    .object({
      gapToLeader: z.number().optional(),
      improvementNeeded: z.number().optional(),
      keyAdvantages: z.array(z.string()).optional(),
      mainChallenges: z.array(z.string()).optional(),
    })
    .optional(),
  recommendations: z
    .object({
      immediate: z.array(z.string()).optional(),
      medium: z.array(z.string()).optional(),
      long: z.array(z.string()).optional(),
    })
    .optional(),
  generated_at: z.string().optional(),
  total_models_analyzed: z.number().optional(),
});

/**
 * Inferred TypeScript types
 */
export type ExternalModel = z.infer<typeof ExternalModelSchema>;
export type ExternalModelAnalysis = z.infer<
  typeof ExternalModelAnalysisSchema
>;
