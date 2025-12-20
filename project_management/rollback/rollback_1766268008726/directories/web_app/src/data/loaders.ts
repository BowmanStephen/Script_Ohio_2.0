import fs from "fs";
import path from "path";
import {
  WeeklyPredictionsResponseSchema,
  type WeeklyGame,
} from "@/src/domain/schemas/weekly";
import {
  BowlPredictionsResponseSchema,
  type BowlPredictionsResponse,
} from "@/src/domain/schemas/bowls";
import {
  type ExternalModelAnalysis,
  ExternalModelAnalysisSchema,
} from "@/src/domain/schemas/analytics";

/**
 * Get project root (go up from web_app/)
 */
function getProjectRoot(): string {
  return path.resolve(__dirname, "../../..");
}

/**
 * Check if API proxy is configured
 */
function getApiBaseUrl(): string | null {
  return process.env.PY_API_BASE_URL || null;
}

/**
 * Load weekly predictions from artifacts
 * Default: reads from predictions/week{N}/week{N}_model_predictions.json
 * Optional: proxies to PY_API_BASE_URL if set
 */
export async function loadWeeklyPredictions(
  week: number,
  season: number = 2025
): Promise<WeeklyGame[]> {
  const apiUrl = getApiBaseUrl();

  // Try API first if configured
  if (apiUrl) {
    try {
      const response = await fetch(
        `${apiUrl}/api/predictions/week/${week}?season=${season}`
      );
      if (response.ok) {
        const data = await response.json();
        const validated = WeeklyPredictionsResponseSchema.parse(
          data.predictions || data
        );
        return validated;
      }
    } catch (error) {
      console.warn("API load failed, falling back to artifacts:", error);
    }
  }

  // Fall back to local artifacts
  const projectRoot = getProjectRoot();
  const predictionsPath = path.join(
    projectRoot,
    "predictions",
    `week${week}`,
    `week${week}_model_predictions.json`
  );

  if (!fs.existsSync(predictionsPath)) {
    throw new Error(
      `Weekly predictions not found: ${predictionsPath}. Run sync script first.`
    );
  }

  const rawData = JSON.parse(fs.readFileSync(predictionsPath, "utf-8"));
  const validated = WeeklyPredictionsResponseSchema.parse(
    Array.isArray(rawData) ? rawData : rawData.predictions || []
  );

  return validated;
}

/**
 * Load bowl predictions from artifacts
 * Default: reads from data/outputs/predictions/2025/bowl_season/*.json
 * Optional: proxies to PY_API_BASE_URL if set
 */
export async function loadBowlPredictions(
  season: number = 2025
): Promise<BowlPredictionsResponse> {
  const apiUrl = getApiBaseUrl();

  // Try API first if configured
  if (apiUrl) {
    try {
      const response = await fetch(`${apiUrl}/api/bowl-games`);
      if (response.ok) {
        const data = await response.json();
        // Transform API response to our schema
        if (data.success && data.data) {
          return BowlPredictionsResponseSchema.parse({
            generated_at: data.data.generated_at || new Date().toISOString(),
            season: data.data.season || season,
            games: data.data.games || [],
          });
        }
      }
    } catch (error) {
      console.warn("API load failed, falling back to artifacts:", error);
    }
  }

  // Fall back to local artifacts - find latest file
  const projectRoot = getProjectRoot();
  const bowlDir = path.join(
    projectRoot,
    "data",
    "outputs",
    "predictions",
    season.toString(),
    "bowl_season"
  );

  if (!fs.existsSync(bowlDir)) {
    throw new Error(
      `Bowl predictions directory not found: ${bowlDir}. Generate predictions first.`
    );
  }

  // Try bowls_2025_predictions_ml.json first, then fallback to any latest file
  const preferredFiles = [
    "bowls_2025_predictions_ml.json",
    "bowls_2025_predictions.json",
  ];

  let bowlFilePath: string | null = null;

  for (const fileName of preferredFiles) {
    const candidate = path.join(bowlDir, fileName);
    if (fs.existsSync(candidate)) {
      bowlFilePath = candidate;
      break;
    }
  }

  // If no preferred file, find latest JSON file
  if (!bowlFilePath) {
    const files = fs
      .readdirSync(bowlDir)
      .filter((f) => f.endsWith(".json") && !f.includes("backup"))
      .map((f) => ({
        name: f,
        path: path.join(bowlDir, f),
        mtime: fs.statSync(path.join(bowlDir, f)).mtime,
      }))
      .sort((a, b) => b.mtime.getTime() - a.mtime.getTime());

    if (files.length > 0) {
      bowlFilePath = files[0].path;
    }
  }

  if (!bowlFilePath) {
    throw new Error(
      `No bowl predictions file found in ${bowlDir}. Generate predictions first.`
    );
  }

  const rawData = JSON.parse(fs.readFileSync(bowlFilePath, "utf-8"));
  const validated = BowlPredictionsResponseSchema.parse(rawData);

  return validated;
}

/**
 * Load external model analysis from artifacts
 * Default: reads from data/outputs/analysis/external_model_analysis_*.json
 * Optional: proxies to PY_API_BASE_URL if set
 */
export async function loadExternalModelAnalysis(): Promise<ExternalModelAnalysis> {
  const apiUrl = getApiBaseUrl();

  // Try API first if configured
  if (apiUrl) {
    try {
      const response = await fetch(`${apiUrl}/api/external-model-analysis`);
      if (response.ok) {
        const data = await response.json();
        return ExternalModelAnalysisSchema.parse(data);
      }
    } catch (error) {
      console.warn("API load failed, falling back to artifacts:", error);
    }
  }

  // Fall back to local artifacts
  const projectRoot = getProjectRoot();
  const analysisDir = path.join(projectRoot, "data", "outputs", "analysis");

  if (!fs.existsSync(analysisDir)) {
    throw new Error(
      `Analysis directory not found: ${analysisDir}. Generate analysis first.`
    );
  }

  // Find latest external_model_analysis file
  const files = fs
    .readdirSync(analysisDir)
    .filter((f) => f.startsWith("external_model_analysis_") && f.endsWith(".json"))
    .map((f) => ({
      name: f,
      path: path.join(analysisDir, f),
      mtime: fs.statSync(path.join(analysisDir, f)).mtime,
    }))
    .sort((a, b) => b.mtime.getTime() - a.mtime.getTime());

  if (files.length === 0) {
    throw new Error(
      `No external model analysis file found in ${analysisDir}. Generate analysis first.`
    );
  }

  const latestFile = files[0].path;
  const rawData = JSON.parse(fs.readFileSync(latestFile, "utf-8"));
  const validated = ExternalModelAnalysisSchema.parse(rawData);

  return validated;
}
