import { z } from "zod";

/**
 * Model metric schema
 */
export const ModelMetricSchema = z.object({
  accuracy: z.number(),
  mae: z.number(),
  weight: z.number().optional(),
});

/**
 * Model performance comparison schema
 */
export const ModelPerformanceSchema = z.object({
  ridge: ModelMetricSchema.optional(),
  xgboost: ModelMetricSchema.optional(),
  fastai: ModelMetricSchema.optional(),
  consensus: ModelMetricSchema.optional(),
});

/**
 * Individual model details (for detailed comparison)
 */
export const ModelDetailsSchema = z.object({
  name: z.string(),
  type: z.enum(["regression", "classification", "neural_network", "ensemble"]),
  description: z.string().optional(),
  accuracy: z.number().optional(),
  mae: z.number().optional(),
  margin: z.number().optional(),
  probability: z.number().optional(),
});

/**
 * Inferred TypeScript types
 */
export type ModelMetric = z.infer<typeof ModelMetricSchema>;
export type ModelPerformance = z.infer<typeof ModelPerformanceSchema>;
export type ModelDetails = z.infer<typeof ModelDetailsSchema>;
