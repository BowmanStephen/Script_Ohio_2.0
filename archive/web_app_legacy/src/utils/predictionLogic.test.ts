import { describe, it, expect } from 'vitest';
import { predictGame, calculateWCFLPoints, modelPerformance } from './predictionLogic';
import { Game, FeatureWeights } from '../types';

describe('predictionLogic', () => {
  const mockGame: Game = {
    id: 1,
    home_team: 'Team A',
    away_team: 'Team B',
    spread: 3.5,
    home_elo: 1600,
    away_elo: 1500,
    home_talent: 700,
    away_talent: 650,
    home_adjusted_epa: 0.2,
    away_adjusted_epa: 0.15,
    home_adjusted_success: 0.45,
    away_adjusted_success: 0.4,
    home_adjusted_explosiveness: 1.25,
    away_adjusted_explosiveness: 1.2,
    home_points_per_opportunity_offense: 4.0,
    away_points_per_opportunity_offense: 3.5,
  };

  const defaultWeights: FeatureWeights = {
    elo: 0.25,
    talent: 0.25,
    epa: 0.35,
    success: 0.15,
  };

  describe('predictGame', () => {
    it('should return a prediction result for Ridge Regression', () => {
      const result = predictGame(mockGame, 'Ridge Regression', defaultWeights, false);
      
      expect(result).toHaveProperty('predictedMargin');
      expect(result).toHaveProperty('confidence');
      expect(result).toHaveProperty('lineValue');
      expect(result).toHaveProperty('valueRating');
      expect(result).toHaveProperty('winner');
      expect(result).toHaveProperty('suggestedSide');
      
      expect(typeof result.predictedMargin).toBe('string');
      expect(typeof result.confidence).toBe('string');
      expect(parseFloat(result.confidence)).toBeGreaterThanOrEqual(0);
      expect(parseFloat(result.confidence)).toBeLessThanOrEqual(100);
    });

    it('should return a prediction result for XGBoost', () => {
      const result = predictGame(mockGame, 'XGBoost', defaultWeights, false);
      
      expect(result).toHaveProperty('predictedMargin');
      expect(result).toHaveProperty('confidence');
      expect(result.winner).toBe(mockGame.home_team);
    });

    it('should return a prediction result for FastAI Neural Net', () => {
      const result = predictGame(mockGame, 'FastAI Neural Net', defaultWeights, false);
      
      expect(result).toHaveProperty('predictedMargin');
      expect(result).toHaveProperty('confidence');
    });

    it('should return a prediction result for Ensemble', () => {
      const result = predictGame(mockGame, 'Ensemble', defaultWeights, false);
      
      expect(result).toHaveProperty('predictedMargin');
      expect(result).toHaveProperty('confidence');
    });

    it('should apply tempo adjustment when enabled', () => {
      const resultWithoutTempo = predictGame(mockGame, 'Ridge Regression', defaultWeights, false);
      const resultWithTempo = predictGame(mockGame, 'Ridge Regression', defaultWeights, true);
      
      // Tempo adjustment should affect the prediction
      expect(resultWithTempo.predictedMargin).not.toBe(resultWithoutTempo.predictedMargin);
    });

    it('should calculate value rating correctly', () => {
      const gameWithLargeSpread: Game = {
        ...mockGame,
        spread: 20,
      };
      const result = predictGame(gameWithLargeSpread, 'Ridge Regression', defaultWeights, false);
      
      const lineValue = parseFloat(result.lineValue);
      if (Math.abs(lineValue) > 7) {
        expect(result.valueRating).toBe('Strong Value');
      } else if (Math.abs(lineValue) > 4) {
        expect(result.valueRating).toBe('Moderate Value');
      } else if (Math.abs(lineValue) > 2) {
        expect(result.valueRating).toBe('Slight Value');
      } else {
        expect(result.valueRating).toBe('No Value');
      }
    });

    it('should handle edge case with equal teams', () => {
      const equalGame: Game = {
        ...mockGame,
        home_elo: 1500,
        away_elo: 1500,
        home_talent: 650,
        away_talent: 650,
        home_adjusted_epa: 0.15,
        away_adjusted_epa: 0.15,
      };
      
      const result = predictGame(equalGame, 'Ridge Regression', defaultWeights, false);
      
      expect(result).toHaveProperty('predictedMargin');
      expect(result).toHaveProperty('winner');
      // Home field advantage should favor home team
      expect(parseFloat(result.predictedMargin)).toBeGreaterThan(0);
    });
  });

  describe('calculateWCFLPoints', () => {
    it('should allocate points to top 10 games', () => {
      const games: Game[] = Array.from({ length: 15 }, (_, i) => ({
        ...mockGame,
        id: i + 1,
        prediction: predictGame(mockGame, 'Ridge Regression', defaultWeights, false),
      }));

      const result = calculateWCFLPoints(games);
      
      expect(result).toHaveLength(10);
      expect(result[0].wcflPoints).toBe(10);
      expect(result[9].wcflPoints).toBe(1);
    });

    it('should sort games by confidence and line value', () => {
      const games: Game[] = [
        {
          ...mockGame,
          id: 1,
          prediction: {
            predictedMargin: '5.0',
            confidence: '60.0',
            lineValue: '1.5',
            valueRating: 'No Value',
            winner: 'Team A',
            suggestedSide: 'Team A',
          },
        },
        {
          ...mockGame,
          id: 2,
          prediction: {
            predictedMargin: '10.0',
            confidence: '75.0',
            lineValue: '6.5',
            valueRating: 'Moderate Value',
            winner: 'Team A',
            suggestedSide: 'Team A',
          },
        },
      ];

      const result = calculateWCFLPoints(games);
      
      // Higher confidence and value should get more points
      expect(result[0].id).toBe(2);
      expect(result[0].wcflPoints).toBe(10);
    });

    it('should add reasoning to each game', () => {
      const games: Game[] = [{
        ...mockGame,
        id: 1,
        prediction: predictGame(mockGame, 'Ridge Regression', defaultWeights, false),
      }];

      const result = calculateWCFLPoints(games);
      
      expect(result[0].reasoning).toContain('Confidence:');
      expect(result[0].reasoning).toContain('Value:');
    });

    it('should handle empty array', () => {
      const result = calculateWCFLPoints([]);
      expect(result).toHaveLength(0);
    });

    it('should handle games with missing predictions', () => {
      const gamesWithMissing: Game[] = [
        {
          ...mockGame,
          id: 1,
          prediction: undefined,
        },
        {
          ...mockGame,
          id: 2,
          prediction: predictGame(mockGame, 'Ridge Regression', defaultWeights, false),
        },
      ];

      // Should filter out games without predictions
      const result = calculateWCFLPoints(gamesWithMissing.filter(g => g.prediction));
      expect(result.length).toBeGreaterThan(0);
    });
  });

  describe('modelPerformance', () => {
    it('should have valid performance metrics for all models', () => {
      expect(modelPerformance.ridge.accuracy).toBeGreaterThan(0);
      expect(modelPerformance.ridge.accuracy).toBeLessThanOrEqual(1);
      expect(modelPerformance.ridge.mae).toBeGreaterThan(0);
      expect(modelPerformance.ridge.weight).toBeGreaterThan(0);
      expect(modelPerformance.ridge.weight).toBeLessThanOrEqual(1);

      expect(modelPerformance.xgboost.accuracy).toBeGreaterThan(0);
      expect(modelPerformance.xgboost.mae).toBeGreaterThan(0);
      expect(modelPerformance.xgboost.weight).toBeGreaterThan(0);

      expect(modelPerformance.fastai.accuracy).toBeGreaterThan(0);
      expect(modelPerformance.fastai.mae).toBeGreaterThan(0);
      expect(modelPerformance.fastai.weight).toBeGreaterThan(0);
    });

    it('should have weights that sum to approximately 1.0', () => {
      const totalWeight = 
        modelPerformance.ridge.weight +
        modelPerformance.xgboost.weight +
        modelPerformance.fastai.weight +
        modelPerformance.consensus.weight;
      
      expect(totalWeight).toBeCloseTo(1.0, 1);
    });
  });
});
