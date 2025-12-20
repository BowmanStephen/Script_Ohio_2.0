import { describe, expect, it } from 'vitest';
import { week14Games } from './week14Games';

const numericFields = [
  'spread',
  'home_elo',
  'away_elo',
  'home_talent',
  'away_talent',
  'home_adjusted_epa',
  'away_adjusted_epa',
  'home_adjusted_success',
  'away_adjusted_success',
  'home_adjusted_explosiveness',
  'away_adjusted_explosiveness',
  'home_points_per_opportunity_offense',
  'away_points_per_opportunity_offense',
];

describe('front-end data contract', () => {
  it('ensures every game record contains required fields', () => {
    expect(week14Games.length).toBeGreaterThan(0);

    const ids = new Set<number>();
    week14Games.forEach((game) => {
      expect(game.home_team).toBeTruthy();
      expect(game.away_team).toBeTruthy();
      expect(typeof game.id).toBe('number');
      ids.add(game.id);

      numericFields.forEach((field) => {
        const value = (game as Record<string, unknown>)[field];
        expect(typeof value).toBe('number');
        expect(Number.isFinite(value as number)).toBe(true);
      });
    });

    expect(ids.size).toBe(week14Games.length);
  });

  it('reserves optional prediction fields without polluting base data', () => {
    week14Games.forEach((game) => {
      if (game.prediction) {
        expect(typeof game.prediction.predictedMargin).toBe('string');
        expect(typeof game.prediction.confidence).toBe('string');
      }
      expect(game.reasoning ?? '').toBeTypeOf('string');
    });
  });
});
