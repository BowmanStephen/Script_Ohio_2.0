"use client";

import { useEffect, useMemo, useState } from "react";
import type { ExternalModelAnalysis } from "@/src/domain/types";
import { EmptyState } from "@/src/components/empty-state";
import {
  AnalyticsChart,
  type AnalyticsChartDatum,
} from "@/src/components/charts/analytics-chart";

export default function AnalyticsPage() {
  const [analysis, setAnalysis] = useState<ExternalModelAnalysis>({
    models: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const response = await fetch("/api/analytics");
        if (response.ok) {
          const data = await response.json();
          setAnalysis(data);
        }
      } catch (error) {
        console.error("Failed to load analytics:", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const models = analysis.models ?? [];
  const insights = analysis.insights ?? {};
  const recommendations = analysis.recommendations ?? {};

  const chartData = useMemo<AnalyticsChartDatum[]>(() => {
    return models.slice(0, 10).map((model) => ({
      name: model.name,
      accuracy: model.straightUpAccuracy,
      vsSpread: model.vsSpreadAccuracy || 0,
    }));
  }, [models]);

  const showVsSpread = useMemo(
    () => chartData.some((d) => d.vsSpread > 0),
    [chartData]
  );

  const scriptOhioModels = useMemo(
    () => models.filter((m) => Boolean(m.isScriptOhio)),
    [models]
  );
  const topScriptOhio = scriptOhioModels.length > 0 ? scriptOhioModels[0] : null;

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse space-y-6">
            <div className="space-y-2">
              <div className="h-8 w-64 rounded-md bg-muted" />
              <div className="h-4 w-80 rounded-md bg-muted" />
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="h-44 rounded-lg border border-border bg-card" />
              <div className="h-44 rounded-lg border border-border bg-card" />
            </div>

            <div className="h-96 rounded-lg border border-border bg-card" />
            <div className="h-72 rounded-lg border border-border bg-card" />
          </div>
        </div>
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground">Advanced Analytics</h1>
            <p className="mt-2 text-muted-foreground">
              Model performance comparison and competitive analysis
            </p>
          </div>

          <EmptyState
            title="No analytics data found"
            description={
              "Generate external model analysis first, then refresh this page."
            }
            action={
              <pre className="rounded-md bg-muted p-3 text-xs text-muted-foreground overflow-x-auto">
                {"python scripts/external_model_research_analysis.py"}
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
          <h1 className="text-3xl font-bold text-foreground">Advanced Analytics</h1>
          <p className="mt-2 text-muted-foreground">
            Model performance comparison and competitive analysis
          </p>
          {analysis.generated_at ? (
            <p className="mt-1 text-xs text-muted-foreground">
              Generated: {new Date(analysis.generated_at).toLocaleString()}
            </p>
          ) : null}
        </div>

        {(Object.keys(insights).length > 0 || topScriptOhio) && (
          <div className="grid grid-cols-1 gap-6 mb-8 md:grid-cols-2">
            <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-4 text-card-foreground">
                Script Ohio Status
              </h2>
              {topScriptOhio ? (
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Ranking:</span>
                    <span className="font-medium text-card-foreground">
                      #{topScriptOhio.ranking ?? "-"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Accuracy:</span>
                    <span className="font-medium text-card-foreground">
                      {topScriptOhio.straightUpAccuracy}%
                    </span>
                  </div>
                  {insights.gapToLeader !== undefined ? (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Gap to Leader:</span>
                      <span className="font-medium text-card-foreground">
                        {insights.gapToLeader}%
                      </span>
                    </div>
                  ) : null}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No Script Ohio model found in this analysis.
                </p>
              )}
            </div>

            {insights.keyAdvantages && insights.keyAdvantages.length > 0 ? (
              <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                <h2 className="text-xl font-semibold mb-4 text-card-foreground">
                  Key Advantages
                </h2>
                <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                  {insights.keyAdvantages.map((advantage, idx) => (
                    <li key={idx}>{advantage}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        )}

        <div className="mb-8">
          <AnalyticsChart data={chartData} showVsSpread={showVsSpread} />
        </div>

        {Object.keys(recommendations).length > 0 ? (
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm mb-8">
            <h2 className="text-xl font-semibold mb-4 text-card-foreground">
              Recommendations
            </h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {recommendations.immediate && recommendations.immediate.length > 0 ? (
                <div>
                  <h3 className="font-medium text-card-foreground mb-2">Immediate</h3>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    {recommendations.immediate.slice(0, 3).map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {recommendations.medium && recommendations.medium.length > 0 ? (
                <div>
                  <h3 className="font-medium text-card-foreground mb-2">Medium Term</h3>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    {recommendations.medium.slice(0, 3).map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {recommendations.long && recommendations.long.length > 0 ? (
                <div>
                  <h3 className="font-medium text-card-foreground mb-2">Long Term</h3>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    {recommendations.long.slice(0, 3).map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}

        <div className="rounded-lg border border-border bg-card shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-border">
            <h2 className="text-xl font-semibold text-card-foreground">
              All Models ({models.length})
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-muted">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Model
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Accuracy
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    VS Spread
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Methodology
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {models.map((model) => (
                  <tr
                    key={model.name}
                    className={
                      model.isScriptOhio ? "bg-blue-50 dark:bg-blue-950/30" : "hover:bg-muted"
                    }
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-card-foreground">
                      #{model.ranking ?? "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-card-foreground">
                      {model.name}
                      {model.isScriptOhio ? (
                        <span className="ml-2 text-xs text-primary">(Script Ohio)</span>
                      ) : null}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                      {model.straightUpAccuracy}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                      {model.vsSpreadAccuracy != null
                        ? `${model.vsSpreadAccuracy}%`
                        : "N/A"}
                    </td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">
                      {model.methodology || "N/A"}
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
