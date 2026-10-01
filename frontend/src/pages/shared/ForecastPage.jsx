import { useState } from "react";
import { productForecast, reorderSuggestions } from "../../api/forecastApi.js";
import { useApi } from "../../hooks/useApi.js";
import { LineChart, palette } from "../../components/charts/charts.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassBadge, GlassCard, GlassInput, PageHeader } from "../../components/ui/primitives.jsx";

/** Demand intelligence: 14-day forecast + reorder cards (seller own / admin all). */
export default function ForecastPage({ admin = false, title = "Demand intelligence" }) {
  const [pid, setPid] = useState("");
  const [asked, setAsked] = useState(null);
  const fc = useApi(() => (asked ? productForecast(asked) : Promise.resolve(null)), [asked]);
  const reorder = useApi(() => reorderSuggestions(admin).catch(() => ({ items: [] })));

  return (
    <div>
      <PageHeader title={title} subtitle="Actual vs predicted demand, reorder points and stock-out dates." />
      <div className="glass mb-4 flex max-w-md gap-2 p-4">
        <GlassInput placeholder="Product ID for detail forecast…" value={pid}
          onChange={(e) => setPid(e.target.value)} inputMode="numeric" aria-label="Product ID" />
        <button className="btn-primary shrink-0 px-4 text-sm" onClick={() => setAsked(Number(pid))}>Forecast</button>
      </div>
      {asked && (fc.loading ? <TableSkeleton /> : fc.error ? <ErrorState error={fc.error} />
        : fc.data && (
          <GlassCard className="mb-5">
            <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
              <strong>Product #{fc.data.product_id}</strong>
              <GlassBadge color="#a78bfa">{fc.data.model}</GlassBadge>
              <span className="text-muted2">hold-out MAPE {fc.data.holdout_mape_pct}% · {fc.data.history_days} days history</span>
            </div>
            <LineChart
              labels={fc.data.forecast.map((f) => f.day.slice(5))}
              series={[{ label: "Predicted demand", data: fc.data.forecast.map((f) => f.qty),
                borderColor: palette.violet, backgroundColor: "rgba(167,139,250,0.12)", fill: true, tension: 0.35, pointRadius: 0 }]}
            />
          </GlassCard>
        ))}
      <h2 className="mb-3 font-semibold">Reorder suggestions</h2>
      {reorder.loading ? <TableSkeleton /> : !reorder.data?.items?.length ? (
        <EmptyState title="No forecast data" hint="Seed demand history to generate suggestions." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {reorder.data.items.map((r) => (
            <GlassCard key={r.product_id} hover className="p-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs text-slate-400">{r.sku}</span>
                {r.at_risk ? <GlassBadge color="#f87171">Stock-out risk</GlassBadge>
                  : <GlassBadge color="#34d399">OK</GlassBadge>}
              </div>
              <div className="mt-2 grid grid-cols-2 gap-1 text-sm">
                <span className="text-muted2">Forecast 14d</span><strong>{r.forecast_14d} units</strong>
                <span className="text-muted2">On hand</span><strong>{r.on_hand}</strong>
                <span className="text-muted2">Stock-out in</span>
                <strong>{r.days_until_stockout != null ? `~${r.days_until_stockout} days` : "—"}</strong>
                <span className="text-muted2">Reorder</span>
                <strong className="text-sky-300">{r.reorder_qty} units</strong>
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}
