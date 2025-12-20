"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type ModelComparisonDatum = {
  model: string;
  predictions: number;
  avgConfidence: number; // percentage (0-100)
};

const MODEL_COLORS: Record<string, string> = {
  Ridge: "#3b82f6",
  XGBoost: "#10b981",
  FastAI: "#a855f7",
  Ensemble: "#f59e0b",
};

function ChartTooltip({
  active,
  payload,
  label,
  valueSuffix,
}: {
  active?: boolean;
  payload?: ReadonlyArray<{ name?: string; value?: unknown }>;
  label?: string;
  valueSuffix?: string;
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
            <span className="tabular-nums">
              {valueText}
              {valueSuffix || ""}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function MetricCard({
  title,
  dataKey,
  data,
  yDomain,
  valueSuffix,
}: {
  title: string;
  dataKey: "predictions" | "avgConfidence";
  data: ModelComparisonDatum[];
  yDomain?: [number, number];
  valueSuffix?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
      <h2 className="text-xl font-semibold mb-4 text-card-foreground">{title}</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
          <XAxis dataKey="model" tick={{ fill: "var(--muted-foreground)" }} />
          <YAxis
            domain={yDomain}
            tick={{ fill: "var(--muted-foreground)" }}
          />
          <Tooltip
            content={({ active, payload, label }) => (
              <ChartTooltip
                active={active}
                payload={payload}
                label={label as string}
                valueSuffix={valueSuffix}
              />
            )}
          />
          <Legend />
          <Bar dataKey={dataKey} name={dataKey === "predictions" ? "Predictions" : "Avg Confidence"}>
            {data.map((entry) => (
              <Cell
                key={entry.model}
                fill={MODEL_COLORS[entry.model] || "#3b82f6"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ModelComparisonChart({ data }: { data: ModelComparisonDatum[] }) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <MetricCard title="Model Predictions Count" dataKey="predictions" data={data} />
      <MetricCard
        title="Average Confidence"
        dataKey="avgConfidence"
        data={data}
        yDomain={[0, 100]}
        valueSuffix="%"
      />
    </div>
  );
}
