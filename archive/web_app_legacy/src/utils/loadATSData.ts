/**
 * Utility to load and parse ATS analysis data
 * For now, returns empty array - data should be loaded from API or static JSON
 */

import { ATSAnalysis } from '../types';

const clampProbability = (value: number): number => Math.max(0, Math.min(1, value));

const parseNumber = (value: unknown): number | null => {
    if (typeof value === 'number' && Number.isFinite(value)) {
        return value;
    }
    const parsed = parseFloat(String(value ?? ''));
    return Number.isFinite(parsed) ? parsed : null;
};

const coerceGrade = (value: unknown): 'High' | 'Medium' | 'Low' => {
    const grade = typeof value === 'string' ? value : '';
    if (grade === 'High' || grade === 'Medium' || grade === 'Low') {
        return grade;
    }
    return 'Low';
};

const coerceAgreement = (value: unknown): 'high' | 'moderate' => {
    const agreement = typeof value === 'string' ? value : '';
    if (agreement === 'high' || agreement === 'moderate') {
        return agreement;
    }
    return 'moderate';
};

const buildATSRecord = (raw: unknown, index: number): ATSAnalysis | null => {
    if (typeof raw !== 'object' || raw === null) {
        return null;
    }

    const record = raw as Record<string, unknown>;
    const matchup = typeof record.matchup === 'string' ? record.matchup.trim() : '';
    const spread = parseNumber(record.spread);
    const predictedMargin = parseNumber(record.predicted_margin);
    const homeWinProb = parseNumber(record.home_win_prob);
    const awayWinProb = parseNumber(record.away_win_prob);
    const modelEdgePts = parseNumber(record.model_edge_pts);
    const ensembleConfidence = parseNumber(record.ensemble_confidence);

    if (
        !matchup ||
        spread === null ||
        predictedMargin === null ||
        homeWinProb === null ||
        awayWinProb === null ||
        modelEdgePts === null ||
        ensembleConfidence === null
    ) {
        return null;
    }

    return {
        id: record.id ?? index,
        matchup,
        spread,
        predicted_margin: predictedMargin,
        home_win_prob: clampProbability(homeWinProb),
        away_win_prob: clampProbability(awayWinProb),
        ats_pick: typeof record.ats_pick === 'string' ? record.ats_pick.trim() : '',
        model_edge_pts: modelEdgePts,
        confidence_grade: coerceGrade(record.confidence_grade),
        model_agreement: coerceAgreement(record.model_agreement),
        ensemble_confidence: clampProbability(ensembleConfidence),
        model_summary: typeof record.model_summary === 'string' ? record.model_summary.trim() : ''
    };
};

/**
 * Parse CSV string into ATSAnalysis array
 */
export function parseATSCSV(csvText: string): ATSAnalysis[] {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) return [];

    const headers = lines[0].split(',');
    const data: ATSAnalysis[] = [];

    for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        // Handle CSV with quoted fields (especially model_summary)
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
        values.push(current); // Last value

        if (values.length < headers.length) {
            continue;
        }

        try {
            // Type-safe parsing with validation
            const spread = parseNumber(values[1]);
            const predictedMargin = parseNumber(values[2]);
            const homeWinProb = parseNumber(values[3]);
            const awayWinProb = parseNumber(values[4]);
            const modelEdgePts = parseNumber(values[6]);
            const ensembleConf = parseNumber(values[9]);

            if (
                spread === null ||
                predictedMargin === null ||
                homeWinProb === null ||
                awayWinProb === null ||
                modelEdgePts === null ||
                ensembleConf === null
            ) {
                console.warn(`Skipping line ${i}: Invalid numeric values`);
                continue;
            }

            const item: ATSAnalysis = {
                id: values[11]?.trim() || `${values[0]}_${i}`,
                matchup: values[0]?.trim() || '',
                spread,
                predicted_margin: predictedMargin,
                home_win_prob: clampProbability(homeWinProb), // Clamp 0-1
                away_win_prob: clampProbability(awayWinProb), // Clamp 0-1
                ats_pick: values[5]?.trim() || '',
                model_edge_pts: modelEdgePts,
                confidence_grade: coerceGrade(values[7]),
                model_agreement: coerceAgreement(values[8]),
                ensemble_confidence: clampProbability(ensembleConf), // Clamp 0-1
                model_summary: values[10]?.replace(/^"|"$/g, '').trim() || '',
            };
            data.push(item);
        } catch (error) {
            console.error(`Error parsing line ${i}:`, error);
        }
    }

    return data;
}

/**
 * Load ATS data from a URL (CSV or JSON)
 */
export async function loadATSData(url: string): Promise<ATSAnalysis[]> {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to fetch ATS data: ${response.status} ${response.statusText}`);
        }

        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            const json = await response.json();
            if (Array.isArray(json)) {
                return json
                    .map((item, index) => buildATSRecord(item, index))
                    .filter((item): item is ATSAnalysis => item !== null);
            }
            throw new Error('ATS JSON payload is not an array');
        }

        // Try JSON first, fall back to CSV
        const text = await response.text();
        try {
            const json = JSON.parse(text);
            if (Array.isArray(json)) {
                return json
                    .map((item, index) => buildATSRecord(item, index))
                    .filter((item): item is ATSAnalysis => item !== null);
            }
        } catch {
            // Not JSON, parse as CSV
            const parsedCsv = parseATSCSV(text);
            if (parsedCsv.length === 0) {
                throw new Error('Parsed ATS CSV returned no records');
            }
            return parsedCsv;
        }
    } catch (error) {
        console.error('Error loading ATS data:', error);
        throw error;
    }

    return [];
}

/**
 * Default empty ATS data (for development/testing)
 */
export const emptyATSData: ATSAnalysis[] = [];
