/**
 * Constants for prediction logic calculations
 * 
 * These values represent model coefficients, thresholds, and multipliers
 * used in the game prediction algorithms.
 */

/**
 * Ridge Regression model coefficients
 */
export const RIDGE_COEFFICIENTS = {
  /** ELO rating difference multiplier */
  ELO: 0.015,
  /** Talent rating difference multiplier */
  TALENT: 0.012,
  /** EPA (Expected Points Added) difference multiplier */
  EPA: 45,
  /** Success rate difference multiplier */
  SUCCESS: 25,
} as const;

/**
 * XGBoost model coefficients
 */
export const XGBOOST_COEFFICIENTS = {
  /** ELO normalization factor for tanh transformation */
  ELO_NORMALIZATION: 200,
  /** ELO factor multiplier */
  ELO_FACTOR: 12,
  /** Talent normalization factor for tanh transformation */
  TALENT_NORMALIZATION: 100,
  /** Talent factor multiplier */
  TALENT_FACTOR: 10,
  /** EPA difference multiplier */
  EPA: 50,
  /** Points per opportunity multiplier */
  PPO: 8,
} as const;

/**
 * FastAI Neural Net model coefficients
 */
export const FASTAI_COEFFICIENTS = {
  /** ELO normalization factor */
  ELO_NORMALIZATION: 150,
  /** ELO hidden layer weight */
  ELO_WEIGHT: 8,
  /** Talent normalization factor */
  TALENT_NORMALIZATION: 80,
  /** Talent hidden layer weight */
  TALENT_WEIGHT: 7,
  /** EPA multiplier */
  EPA: 40,
  /** EPA hidden layer weight */
  EPA_WEIGHT: 12,
  /** Explosiveness multiplier */
  EXPLOSIVENESS: 35,
  /** Explosiveness hidden layer weight */
  EXPLOSIVENESS_WEIGHT: 6,
} as const;

/**
 * Tempo adjustment multiplier
 * Applied when tempo-adjusted predictions are enabled
 */
export const TEMPO_MULTIPLIER = 1.15;

/**
 * Home field advantage in points
 * Added to all predictions to account for home team advantage
 */
export const HOME_FIELD_ADVANTAGE = 2.5;

/**
 * Confidence calculation constants
 */
export const CONFIDENCE_CONSTANTS = {
  /** Base confidence percentage */
  BASE: 50,
  /** Confidence multiplier per point of margin */
  MULTIPLIER: 2.5,
  /** Maximum confidence percentage */
  MAX: 95,
} as const;

/**
 * Value rating thresholds
 * Used to categorize betting value based on line value difference
 */
export const VALUE_THRESHOLDS = {
  /** Strong value threshold (points) */
  STRONG: 7,
  /** Moderate value threshold (points) */
  MODERATE: 4,
  /** Slight value threshold (points) */
  SLIGHT: 2,
} as const;

/**
 * WCFL point allocation constants
 */
export const WCFL_CONSTANTS = {
  /** Value bonus multiplier for high-value games */
  VALUE_BONUS_MULTIPLIER: 1.5,
  /** Value threshold for bonus (points) */
  VALUE_BONUS_THRESHOLD: 3,
  /** Maximum number of games to allocate points to */
  MAX_GAMES: 10,
  /** Starting point value for top game */
  STARTING_POINTS: 10,
} as const;


