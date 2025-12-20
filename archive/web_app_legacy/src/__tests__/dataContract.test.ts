import { describe, expect, it } from "vitest"
import { week13Games } from "../data/week13Games"
import { week14Games } from "../data/week14Games"
import type { Game } from "../types"
import week13Raw from "../data/week13_data.json"
import week14Raw from "../data/week14_data.json"

const numericFields: Array<keyof Game> = [
    "spread",
    "home_elo",
    "away_elo",
    "home_talent",
    "away_talent",
    "home_adjusted_epa",
    "away_adjusted_epa",
    "home_adjusted_success",
    "away_adjusted_success",
    "home_adjusted_explosiveness",
    "away_adjusted_explosiveness",
    "home_points_per_opportunity_offense",
    "away_points_per_opportunity_offense",
]

const positiveFields: Array<keyof Game> = [
    "home_elo",
    "away_elo",
    "home_talent",
    "away_talent",
]

const EPA_BOUNDS = [-1.5, 1.5]

function validateGame(game: Game): void {
    expect(typeof game.id).toBe("number")
    expect(game.home_team).toBeTruthy()
    expect(game.away_team).toBeTruthy()

    numericFields.forEach((field) => {
        const value = game[field]
        expect(Number.isFinite(value)).toBe(true)
    })

    positiveFields.forEach((field) => {
        expect(game[field]).toBeGreaterThanOrEqual(0)
    })

    expect(game.home_team).not.toEqual(game.away_team)
    expect(game.home_team.trim().length).toBeGreaterThan(0)
    expect(game.away_team.trim().length).toBeGreaterThan(0)

    expect(game.home_adjusted_epa).toBeGreaterThanOrEqual(EPA_BOUNDS[0])
    expect(game.home_adjusted_epa).toBeLessThanOrEqual(EPA_BOUNDS[1])
    expect(game.away_adjusted_epa).toBeGreaterThanOrEqual(EPA_BOUNDS[0])
    expect(game.away_adjusted_epa).toBeLessThanOrEqual(EPA_BOUNDS[1])
}

describe("Game data contract", () => {
    it("ensures curated datasets satisfy the interface", () => {
        ;[week13Games, week14Games].forEach((games) => {
            games.forEach((game) => validateGame(game))
        })
    })

    it("stays in sync with the raw JSON payloads", () => {
        expect(week13Games.length).toEqual(week13Raw.length)
        expect(week14Games.length).toEqual(week14Raw.length)

        const requiredKeys = new Set(Object.keys(week14Raw[0] ?? {}))
        week14Games.forEach((game) => {
            requiredKeys.forEach((key) => {
                expect((game as Record<string, unknown>)[key]).not.toBeUndefined()
            })
        })
    })

    it("maintains spread symmetry (home + away)", () => {
        week14Games.forEach((game) => {
            expect(Math.abs(game.home_adjusted_success - game.away_adjusted_success)).toBeLessThan(1)
        })
    })
})

