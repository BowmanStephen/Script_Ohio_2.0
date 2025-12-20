"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, notFound } from "next/navigation";
import type { WeeklyGame } from "@/src/domain/types";
import {
  DataTable,
  type DataTableColumn,
} from "@/src/components/data-table";
import { SearchInput } from "@/src/components/search-input";
import { FilterDropdown } from "@/src/components/filter-dropdown";
import { EmptyState } from "@/src/components/empty-state";

function getPredictedWinner(game: WeeklyGame): string {
  return (
    game.predicted_winner ||
    (game.predicted_margin >= 0 ? game.home_team : game.away_team)
  );
}

function getConfidence(game: WeeklyGame): number {
  if (typeof game.ensemble_confidence === "number") return game.ensemble_confidence;

  const candidates = [
    game.ensemble_home_win_probability,
    game.home_win_probability,
    game.ridge_home_win_probability,
    game.xgb_home_win_probability,
    game.fastai_home_win_probability,
  ].filter((v): v is number => typeof v === "number");

  if (candidates.length === 0) return 0.5;

  const p = candidates[0];
  return Math.max(p, 1 - p);
}

function formatSpread(game: WeeklyGame): string {
  if (game.spread == null) return "N/A";

  if (game.spread > 0) {
    return `${game.home_team} -${game.spread}`;
  }

  if (game.spread < 0) {
    return `${game.away_team} ${Math.abs(game.spread)}`;
  }

  return "Pick";
}

export default function WeekPage() {
  const params = useParams();
  const week = params?.week as string;
  const weekNum = parseInt(week || "14", 10);

  const [games, setGames] = useState<WeeklyGame[]>([]);
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");
  const [conference, setConference] = useState("all");
  const [minConfidence, setMinConfidence] = useState("0");

  useEffect(() => {
    if (isNaN(weekNum) || weekNum < 1 || weekNum > 16) {
      return;
    }

    async function loadData() {
      try {
        const response = await fetch(`/api/week/${weekNum}`);
        if (response.ok) {
          const data = await response.json();
          setGames(data.games || []);
        }
      } catch (error) {
        console.error("Failed to load weekly predictions:", error);
      } finally {
        setLoading(false);
      }
    }

    setLoading(true);
    loadData();
  }, [weekNum]);

  if (isNaN(weekNum) || weekNum < 1 || weekNum > 16) {
    notFound();
  }

  const conferenceOptions = useMemo(() => {
    const set = new Set<string>();
    games.forEach((g) => {
      if (g.home_conference) set.add(g.home_conference);
      if (g.away_conference) set.add(g.away_conference);
    });

    const opts = Array.from(set)
      .sort((a, b) => a.localeCompare(b))
      .map((c) => ({ value: c, label: c }));

    return [{ value: "all", label: "All" }, ...opts];
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

  const filteredGames = useMemo(() => {
    const q = query.trim().toLowerCase();
    const min = Number(minConfidence);

    return games.filter((g) => {
      const confOk =
        conference === "all" ||
        g.home_conference === conference ||
        g.away_conference === conference;

      const confVal = getConfidence(g);
      const confOk2 = Number.isFinite(min) ? confVal >= min : true;

      if (!confOk || !confOk2) return false;

      if (!q) return true;

      const haystack = [
        g.home_team,
        g.away_team,
        g.home_conference,
        g.away_conference,
        g.predicted_winner,
        getPredictedWinner(g),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return haystack.includes(q);
    });
  }, [games, query, conference, minConfidence]);

  const columns = useMemo<Array<DataTableColumn<WeeklyGame>>>(
    () => [
      {
        id: "matchup",
        header: "Matchup",
        sortValue: (g) => `${g.away_team} @ ${g.home_team}`,
        className: "px-4 py-3 text-sm text-card-foreground",
        cell: (g) => (
          <div className="min-w-[14rem] max-w-[22rem]">
            <div className="font-medium text-card-foreground">
              {g.away_team} @ {g.home_team}
            </div>
            {(g.home_conference || g.away_conference) && (
              <div className="mt-1 text-xs text-muted-foreground truncate">
                {(g.away_conference || "-") + " @ " + (g.home_conference || "-")}
              </div>
            )}
          </div>
        ),
      },
      {
        id: "spread",
        header: "Spread",
        sortValue: (g) => (g.spread == null ? null : g.spread),
        cell: (g) => formatSpread(g),
      },
      {
        id: "margin",
        header: "Predicted Margin",
        sortValue: (g) => g.predicted_margin,
        cell: (g) => (
          <span className="font-medium">
            {g.predicted_margin >= 0 ? "+" : ""}
            {g.predicted_margin.toFixed(1)}
          </span>
        ),
      },
      {
        id: "winner",
        header: "Winner",
        sortValue: (g) => getPredictedWinner(g),
        cell: (g) => <span className="font-medium">{getPredictedWinner(g)}</span>,
      },
      {
        id: "confidence",
        header: "Confidence",
        sortValue: (g) => getConfidence(g),
        className: "px-4 py-3 text-sm text-card-foreground",
        cell: (g) => {
          const c = getConfidence(g);
          const pct = c * 100;

          return (
            <div className="flex items-center gap-2">
              <div className="tabular-nums">{pct.toFixed(1)}%</div>
              <div className="h-2 w-20 rounded-full bg-muted">
                <div
                  className="h-2 rounded-full bg-primary"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        },
      },
    ],
    []
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse space-y-6">
            <div className="space-y-2">
              <div className="h-8 w-56 rounded-md bg-muted" />
              <div className="h-4 w-36 rounded-md bg-muted" />
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <div className="h-10 w-full rounded-md bg-muted" />
              <div className="h-10 w-full rounded-md bg-muted" />
              <div className="h-10 w-full rounded-md bg-muted" />
            </div>

            <div className="rounded-lg border border-border bg-card overflow-hidden">
              <div className="h-10 bg-muted" />
              <div className="divide-y divide-border">
                {Array.from({ length: 10 }).map((_, idx) => (
                  <div key={idx} className="h-12 bg-card" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground">
            Week {weekNum} Predictions
          </h1>
          <p className="mt-2 text-muted-foreground">
            {filteredGames.length} of {games.length} games
          </p>
        </div>

        <div className="mb-6 grid grid-cols-1 gap-3 md:grid-cols-3">
          <SearchInput
            value={query}
            onChange={setQuery}
            placeholder="Search teams, conferences, winners..."
          />
          <FilterDropdown
            label="Conference"
            value={conference}
            options={conferenceOptions}
            onChange={setConference}
          />
          <FilterDropdown
            label="Confidence"
            value={minConfidence}
            options={minConfidenceOptions}
            onChange={setMinConfidence}
          />
        </div>

        <DataTable
          rows={filteredGames}
          columns={columns}
          getRowKey={(g) => g.game_id}
          initialSort={{ columnId: "confidence", direction: "desc" }}
          pageSize={25}
          emptyState={
            <EmptyState
              title={`No predictions found for week ${weekNum}`}
              description={
                "Generate predictions first, then refresh this page. " +
                "You can also broaden your filters/search."
              }
              action={
                <pre className="rounded-md bg-muted p-3 text-xs text-muted-foreground overflow-x-auto">
                  {`python scripts/run_weekly_analysis.py --week ${weekNum}`}
                </pre>
              }
            />
          }
        />
      </div>
    </div>
  );
}
