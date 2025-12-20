"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type AnalyticsChartDatum = {
  name: string;
  accuracy: number;
  vsSpread: number;
};

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: ReadonlyArray<{ name?: string; value?: unknown }>;
  label?: string;
}) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 text-xs text-card-foreground shadow-sm">
      <div className="mb-1 font-semibold">{label}</div>
      {payload.map((p, idx) => {
        const valueText =
          typeof p.value === "number" ? String(p.value) : String(p.value ?? "");

        return (
          <div key={idx} className="flex items-center justify-between gap-4">
            <span className="text-muted-foreground">{p.name}</span>
            <span className="tabular-nums">{valueText}%</span>
          </div>
        );
      })}
    </div>
  );
}

export function AnalyticsChart({
  data,
  showVsSpread,
}: {
  data: AnalyticsChartDatum[];
  showVsSpread: boolean;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
      <h2 className="text-xl font-semibold mb-4 text-card-foreground">
        Model Accuracy Comparison (Top 10)
      </h2>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={120}
            tick={{ fill: "var(--muted-foreground)" }}
          />
          <YAxis domain={[0, 100]} tick={{ fill: "var(--muted-foreground)" }} />
          <Tooltip
            content={({ active, payload, label }) => (
              <ChartTooltip
                active={active}
                payload={payload}
                label={label as string}
              />
            )}
          />
          <Legend />
          <Bar dataKey="accuracy" fill="#3b82f6" name="Straight Up Accuracy %" />
          {showVsSpread ? (
            <Bar dataKey="vsSpread" fill="#10b981" name="VS Spread Accuracy %" />
          ) : null}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
