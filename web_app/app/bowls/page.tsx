"use client";

import { useEffect, useMemo, useState } from "react";
import type { BowlGame, BowlPredictionsResponse } from "@/src/domain/types";
import { SearchInput } from "@/src/components/search-input";
import { FilterDropdown } from "@/src/components/filter-dropdown";
import { EmptyState } from "@/src/components/empty-state";

function getDateKey(date: string): string {
  // Prefer stable ISO date slicing when possible.
  if (date.length >= 10) return date.slice(0, 10);
  return date;
}

function formatDate(date: string): string {
  try {
    return new Date(date).toLocaleDateString();
  } catch {
    return date;
  }
}

function getConfidence(game: BowlGame): number {
  const pHome = typeof game.home_win_prob === "number" ? game.home_win_prob : 0.5;
  // predicted_margin is (home - away)
  const winnerIsHome = game.predicted_margin >= 0;
  const pWinner = winnerIsHome ? pHome : 1 - pHome;
  return Math.max(pWinner, 1 - pWinner);
}

function getWinner(game: BowlGame): string {
  return game.predicted_margin >= 0 ? game.home_team : game.away_team;
}

type SortKey = "date" | "confidence" | "margin";

export default function BowlsPage() {
  const [bowlData, setBowlData] = useState<BowlPredictionsResponse>({
    generated_at: new Date().toISOString(),
    season: 2025,
    games: [],
  });
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");
  const [dateFilter, setDateFilter] = useState("all");
  const [minConfidence, setMinConfidence] = useState("0");
  const [sortKey, setSortKey] = useState<SortKey>("date");

  useEffect(() => {
    async function loadData() {
      try {
        const response = await fetch("/api/bowls");
        if (response.ok) {
          const data = await response.json();
          setBowlData(data);
        }
      } catch (error) {
        console.error("Failed to load bowl predictions:", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const games = bowlData.games ?? [];

  const dateOptions = useMemo(() => {
    const set = new Set<string>();
    games.forEach((g) => set.add(getDateKey(g.date)));

    const opts = Array.from(set)
      .sort((a, b) => a.localeCompare(b))
      .map((d) => ({ value: d, label: formatDate(d) }));

    return [{ value: "all", label: "All dates" }, ...opts];
  }, [games]);

  const minConfidenceOptions = useMemo(
    () => [
      { value: "0", label: "All" },
      { value: "0.6", label: "60%+" },
      { value: "0.7", label: "70%+" },
      { value: "0.8", label: "80%+" },
      { value: "0.9", label: "90%+" },
    ],
    []
  );

  const sortOptions = useMemo(
    () => [
      { value: "date", label: "Date" },
      { value: "confidence", label: "Confidence" },
      { value: "margin", label: "Margin" },
    ],
    []
  );

  const filteredGames = useMemo(() => {
    const q = query.trim().toLowerCase();
    const min = Number(minConfidence);

    let list = games.filter((g) => {
      const dateOk = dateFilter === "all" || getDateKey(g.date) === dateFilter;
      const confOk = Number.isFinite(min) ? getConfidence(g) >= min : true;

      if (!dateOk || !confOk) return false;

      if (!q) return true;

      const haystack = [g.home_team, g.away_team, g.bowl_name, g.location]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return haystack.includes(q);
    });

    list = list.sort((a, b) => {
      if (sortKey === "confidence") {
        return getConfidence(b) - getConfidence(a);
      }
      if (sortKey === "margin") {
        return Math.abs(b.predicted_margin) - Math.abs(a.predicted_margin);
      }
      // date
      return getDateKey(a.date).localeCompare(getDateKey(b.date));
    });

    return list;
  }, [games, query, dateFilter, minConfidence, sortKey]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground">
            Bowl Season Predictions
          </h1>
          <p className="mt-2 text-muted-foreground">
            {filteredGames.length} of {games.length} bowl games
            {bowlData.generated_at ? (
              <span className="ml-2 text-xs text-muted-foreground">
                (Generated: {new Date(bowlData.generated_at).toLocaleDateString()})
              </span>
            ) : null}
          </p>
        </div>

        <div className="mb-6 grid grid-cols-1 gap-3 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <SearchInput
              value={query}
              onChange={setQuery}
              placeholder="Search bowls, teams, locations..."
            />
          </div>
          <FilterDropdown
            label="Date"
            value={dateFilter}
            options={dateOptions}
            onChange={setDateFilter}
          />
          <FilterDropdown
            label="Min conf"
            value={minConfidence}
            options={minConfidenceOptions}
            onChange={setMinConfidence}
          />
        </div>

        <div className="mb-6">
          <FilterDropdown
            label="Sort"
            value={sortKey}
            options={sortOptions}
            onChange={(v) => setSortKey(v as SortKey)}
          />
        </div>

        {filteredGames.length === 0 ? (
          <EmptyState
            title="No bowl predictions found"
            description={
              "Generate bowl predictions first, then refresh this page. " +
              "You can also broaden your filters/search."
            }
            action={
              <pre className="rounded-md bg-muted p-3 text-xs text-muted-foreground overflow-x-auto">
                {"python scripts/predict_bowls_2025.py --season 2025 --method ml"}
              </pre>
            }
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredGames.map((game) => {
              const winner = getWinner(game);
              const confidence = getConfidence(game);
              const pct = confidence * 100;
              const winnerIsHome = game.predicted_margin >= 0;

              return (
                <div
                  key={game.id}
                  className="rounded-lg border border-border bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
                >
                  <div className="mb-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-base font-semibold text-card-foreground">
                          {game.bowl_name || "Bowl Game"}
                        </h3>
                        <div className="mt-1 text-xs text-muted-foreground">
                          {formatDate(game.date)}
                        </div>
                        {game.location ? (
                          <div className="mt-1 text-xs text-muted-foreground">
                            {game.location}
                          </div>
                        ) : null}
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-muted-foreground">Pick</div>
                        <div className="text-sm font-semibold text-card-foreground">
                          {winner}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span
                        className={
                          "text-sm " +
                          (!winnerIsHome
                            ? "font-semibold text-primary"
                            : "text-card-foreground")
                        }
                      >
                        {game.away_team}
                      </span>
                      {!winnerIsHome ? (
                        <span className="text-xs text-primary">Winner</span>
                      ) : null}
                    </div>
                    <div className="flex items-center justify-between">
                      <span
                        className={
                          "text-sm " +
                          (winnerIsHome
                            ? "font-semibold text-primary"
                            : "text-card-foreground")
                        }
                      >
                        {game.home_team}
                      </span>
                      {winnerIsHome ? (
                        <span className="text-xs text-primary">Winner</span>
                      ) : null}
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-border">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Predicted Margin</span>
                      <span className="font-medium text-card-foreground">
                        {game.predicted_margin >= 0 ? "+" : ""}
                        {game.predicted_margin.toFixed(1)}
                      </span>
                    </div>
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Confidence</span>
                        <span className="font-medium text-card-foreground">
                          {pct.toFixed(1)}%
                        </span>
                      </div>
                      <div className="mt-2 h-2 w-full rounded-full bg-muted">
                        <div
                          className="h-2 rounded-full bg-primary"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
