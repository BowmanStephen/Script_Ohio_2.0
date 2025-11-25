import { APP_CONSTANTS } from '../config/constants';
import { week14Games } from '../data/week14Games';
import { Game, PredictionResult } from '../types';
import { VALUE_THRESHOLDS } from './predictionConstants';

type RawPredictionRecord = Record<string, unknown>;

const numeric = (value: unknown): number | null => {
    if (typeof value === 'number' && Number.isFinite(value)) {
        return value;
    }
    const parsed = parseFloat(String(value ?? ''));
    return Number.isFinite(parsed) ? parsed : null;
};

const clampProbability = (value: number | null): number | null => {
    if (value === null) return null;
    return Math.max(0, Math.min(1, value));
};

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

const buildPrediction = (
    raw: RawPredictionRecord,
    homeTeam: string,
    awayTeam: string,
    spread: number,
    predictedMargin: number,
    homeProb: number | null,
    awayProb: number | null
): PredictionResult => {
    const winnerIsHome = predictedMargin >= 0;
    const winner = winnerIsHome ? homeTeam : awayTeam;
    const lineValue = predictedMargin - spread;
    const confidenceProb = winnerIsHome ? homeProb ?? awayProb : awayProb ?? homeProb;
    const confidencePercent = Math.max(0, Math.min(100, (confidenceProb ?? 0.5) * 100));

    return {
        predictedMargin: predictedMargin.toFixed(1),
        confidence: confidencePercent.toFixed(1),
        lineValue: lineValue.toFixed(1),
        valueRating: getValueRating(lineValue),
        winner,
        suggestedSide: buildSuggestedSide(lineValue, spread, homeTeam, awayTeam),
    };
};

const mapPredictionRecord = (raw: RawPredictionRecord): Game | null => {
    const id = numeric(raw.game_id);
    if (id === null) {
        return null;
    }

    const baseGame = week14Games.find((g) => g.id === id);
    const homeTeam = (typeof raw.home_team === 'string' && raw.home_team) || baseGame?.home_team;
    const awayTeam = (typeof raw.away_team === 'string' && raw.away_team) || baseGame?.away_team;

    if (!homeTeam || !awayTeam) {
        return null;
    }

    const spread = numeric(raw.spread) ?? baseGame?.spread ?? 0;
    const predictedMargin =
        numeric(raw.ensemble_margin) ??
        numeric(raw.predicted_margin) ??
        numeric(raw.ridge_predicted_margin) ??
        0;

    const homeWinProb = clampProbability(
        numeric(raw.home_win_probability) ??
        numeric(raw.ensemble_home_win_probability) ??
        numeric(raw.ridge_home_win_probability) ??
        numeric(raw.ensemble_confidence)
    );
    const awayWinProb = clampProbability(
        numeric(raw.away_win_probability) ??
        numeric(raw.ensemble_away_win_probability) ??
        (homeWinProb !== null ? 1 - homeWinProb : null)
    );

    const prediction = buildPrediction(raw, homeTeam, awayTeam, spread, predictedMargin, homeWinProb, awayWinProb);

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
        week: (numeric(raw.week) ?? baseGame?.week ?? APP_CONSTANTS.CURRENT_WEEK) as number,
        prediction,
    };
};

const parsePredictionCsv = (csvText: string): RawPredictionRecord[] => {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) return [];

    const headers = lines[0].split(',').map((h) => h.trim());
    const records: RawPredictionRecord[] = [];

    for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        const values: string[] = [];
        let current = '';
        let inQuotes = false;

        for (let j = 0; j < line.length; j++) {
            const char = line[j];
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                values.push(current);
                current = '';
            } else {
                current += char;
            }
        }
        values.push(current);

        if (values.length < headers.length) continue;

        const record: RawPredictionRecord = {};
        headers.forEach((header, idx) => {
            record[header] = values[idx];
        });
        records.push(record);
    }

    return records;
};

const parseJsonPayload = (payload: unknown): RawPredictionRecord[] => {
    if (!Array.isArray(payload)) return [];
    return payload.filter((item): item is RawPredictionRecord => typeof item === 'object' && item !== null);
};

const toGames = (records: RawPredictionRecord[]): Game[] =>
    records
        .map((record) => mapPredictionRecord(record))
        .filter((game): game is Game => game !== null);

export async function loadPredictionsData(jsonUrl: string, csvFallbackUrl?: string): Promise<Game[]> {
    try {
        const response = await fetch(jsonUrl);
        if (!response.ok) {
            throw new Error(`Failed to fetch predictions JSON: ${response.status}`);
        }
        const json = await response.json();
        const records = parseJsonPayload(json);
        const games = toGames(records);
        if (games.length > 0) {
            return games;
        }
        throw new Error('No prediction records parsed from JSON payload');
    } catch (jsonError) {
        console.warn('Predictions JSON load failed, attempting CSV fallback', jsonError);
    }

    if (csvFallbackUrl) {
        const response = await fetch(csvFallbackUrl);
        if (!response.ok) {
            throw new Error(`Failed to fetch predictions CSV: ${response.status}`);
        }
        const text = await response.text();
        const records = parsePredictionCsv(text);
        const games = toGames(records);
        if (games.length > 0) {
            return games;
        }
    }

    throw new Error('Unable to load predictions from provided sources');
}
