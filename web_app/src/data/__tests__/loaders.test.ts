import { describe, it, expect } from "vitest";
import { WeeklyGameSchema } from "../../domain/schemas/weekly";
import { BowlGameSchema } from "../../domain/schemas/bowls";

describe("Schema Validation", () => {
  it("should validate weekly game schema", () => {
    const validGame = {
      game_id: 401756964,
      season: 2025,
      week: 14,
      home_team: "Kansas",
      away_team: "Utah",
      spread: 13.0,
      predicted_margin: -10.9,
      ensemble_home_win_probability: 0.15,
    };

    const result = WeeklyGameSchema.safeParse(validGame);
    expect(result.success).toBe(true);
  });

  it("should validate bowl game schema", () => {
    const validBowl = {
      id: 401778123,
      date: "2025-12-13 17:00:00+00:00",
      home_team: "Prairie View A&M",
      away_team: "South Carolina State",
      home_win_prob: 0.57,
      predicted_margin: 2.64,
    };

    const result = BowlGameSchema.safeParse(validBowl);
    expect(result.success).toBe(true);
  });

  it("should reject invalid weekly game", () => {
    const invalidGame = {
      game_id: "not-a-number",
      season: 2025,
    };

    const result = WeeklyGameSchema.safeParse(invalidGame);
    expect(result.success).toBe(false);
  });
});
