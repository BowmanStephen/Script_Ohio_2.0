"use client";

import { useEffect, useMemo, useState } from "react";
import type { WeeklyGame } from "@/src/domain/types";
import { EmptyState } from "@/src/components/empty-state";
import {
  ModelComparisonChart,
  type ModelComparisonDatum,
} from "@/src/components/charts/model-comparison-chart";

function confidenceFromProb(p: number): number {
  return Math.max(p, 1 - p);
}

export default function ModelsPage() {
  const [week14Games, setWeek14Games] = useState<WeeklyGame[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const response = await fetch("/api/week/14");
        if (response.ok) {
          const data = await response.json();
          setWeek14Games(data.games || []);
        }
      } catch (error) {
        console.error("Failed to load weekly predictions:", error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const { chartData, details } = useMemo(() => {
    const modelStats = {
      ridge: {
        label: "Ridge",
        predictions: 0,
        avgMargin: 0,
        avgConfidence: 0,
        hasMargin: true,
      },
      xgb: {
        label: "XGBoost",
        predictions: 0,
        avgMargin: 0,
        avgConfidence: 0,
        hasMargin: false,
      },
      fastai: {
        label: "FastAI",
        predictions: 0,
        avgMargin: 0,
        avgConfidence: 0,
        hasMargin: false,
      },
      ensemble: {
        label: "Ensemble",
        predictions: 0,
        avgMargin: 0,
        avgConfidence: 0,
        hasMargin: true,
      },
    };

    week14Games.forEach((game) => {
      if (typeof game.ridge_predicted_margin === "number") {
        modelStats.ridge.predictions += 1;
        modelStats.ridge.avgMargin += Math.abs(game.ridge_predicted_margin);
      }
      if (typeof game.ridge_home_win_probability === "number") {
        modelStats.ridge.avgConfidence +=
          Math.abs(game.ridge_home_win_probability - 0.5) * 2;
      }

      if (typeof game.xgb_home_win_probability === "number") {
        modelStats.xgb.predictions += 1;
        modelStats.xgb.avgConfidence +=
          Math.abs(game.xgb_home_win_probability - 0.5) * 2;
      }

      if (typeof game.fastai_home_win_probability === "number") {
        modelStats.fastai.predictions += 1;
        modelStats.fastai.avgConfidence +=
          Math.abs(game.fastai_home_win_probability - 0.5) * 2;
      }

      if (typeof game.ensemble_margin === "number") {
        modelStats.ensemble.predictions += 1;
        modelStats.ensemble.avgMargin += Math.abs(game.ensemble_margin);
      }

      if (typeof game.ensemble_confidence === "number") {
        modelStats.ensemble.avgConfidence += game.ensemble_confidence;
      } else if (typeof game.ensemble_home_win_probability === "number") {
        modelStats.ensemble.avgConfidence += confidenceFromProb(
          game.ensemble_home_win_probability
        );
      }
    });

    const statsArr = Object.values(modelStats);

    statsArr.forEach((stat) => {
      if (stat.predictions > 0) {
        stat.avgMargin = stat.avgMargin / stat.predictions;
        stat.avgConfidence = stat.avgConfidence / stat.predictions;
      }
    });

    const chartDataLocal: ModelComparisonDatum[] = statsArr.map((s) => ({
      model: s.label,
      predictions: s.predictions,
      avgConfidence: Math.round(s.avgConfidence * 1000) / 10,
    }));

    const detailsLocal = statsArr.map((s) => ({
      model: s.label,
      predictions: s.predictions,
      avgMargin: s.hasMargin ? (Math.round(s.avgMargin * 10) / 10).toFixed(1) : "N/A",
      avgConfidence: `${(Math.round(s.avgConfidence * 1000) / 10).toFixed(1)}%`,
    }));

    return { chartData: chartDataLocal, details: detailsLocal };
  }, [week14Games]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse space-y-6">
            <div className="space-y-2">
              <div className="h-8 w-60 rounded-md bg-muted" />
              <div className="h-4 w-72 rounded-md bg-muted" />
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div className="h-80 rounded-lg border border-border bg-card" />
              <div className="h-80 rounded-lg border border-border bg-card" />
            </div>

            <div className="h-72 rounded-lg border border-border bg-card" />
          </div>
        </div>
      </div>
    );
  }

  if (week14Games.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground">Model Comparison</h1>
            <p className="mt-2 text-muted-foreground">
              Compare Ridge, XGBoost, FastAI, and Ensemble models
            </p>
          </div>

          <EmptyState
            title="No weekly predictions found"
            description="Generate weekly predictions first, then refresh this page."
            action={
              <pre className="rounded-md bg-muted p-3 text-xs text-muted-foreground overflow-x-auto">
                {"python scripts/run_weekly_analysis.py --week 14"}
              </pre>
            }
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Model Comparison</h1>
          <p className="mt-2 text-muted-foreground">
            Performance metrics for Ridge, XGBoost, FastAI, and Ensemble models
          </p>
        </div>

        <div className="mb-8">
          <ModelComparisonChart data={chartData} />
        </div>

        <div className="rounded-lg border border-border bg-card shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-border">
            <h2 className="text-xl font-semibold text-card-foreground">
              Model Details
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Margins are shown only for models that output margin estimates.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-muted">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Model
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Predictions
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Avg Margin
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Avg Confidence
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {details.map((row) => (
                  <tr key={row.model} className="hover:bg-muted">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-card-foreground">
                      {row.model}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                      {row.predictions}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                      {row.avgMargin}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                      {row.avgConfidence}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
