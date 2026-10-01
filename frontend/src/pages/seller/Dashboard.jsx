import { reorderSuggestions } from "../../api/forecastApi.js";
import { revenueTrend, salesSummary } from "../../api/analyticsApi.js";
import { usePolling } from "../../hooks/useApi.js";
import { LineChart, palette } from "../../components/charts/charts.jsx";
import { ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassBadge, GlassCard, PageHeader } from "../../components/ui/primitives.jsx";
import { ActivityFeed, KPICard } from "../../components/analytics/widgets.jsx";
import { Link } from "react-router-dom";

export default function SellerDashboard() {
  const kpis = usePolling(() => salesSummary(), 30000);
  const trend = usePolling(() => revenueTrend(30), 30000);
  const reorder = usePolling(() => reorderSuggestions().catch(() => ({ items: [] })), 30000);
  const atRisk = (reorder.data?.items || []).filter((r) => r.at_risk).slice(0, 5);

  return (
    <div>
      <PageHeader title="Seller dashboard" subtitle="Revenue, stock health and AI reorder intelligence." />
      {kpis.loading ? <TableSkeleton /> : kpis.error ? <ErrorState error={kpis.error} onRetry={kpis.reload} /> : (
        <div className="mb-5 flex flex-wrap gap-3">
          <KPICard label="Revenue" value={kpis.data.revenue} money spark={trend.data?.points?.map((p) => p.revenue)} />
          <KPICard label="Orders" value={kpis.data.orders} />
          <KPICard label="Avg order value" value={kpis.data.average_order_value} money />
          <KPICard label="Low stock items" value={kpis.data.low_stock_count} />
          <KPICard label="Forecast stock-outs" value={(reorder.data?.items || []).filter((r) => r.at_risk).length} />
        </div>
      )}
      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard className="lg:col-span-2">
          <h2 className="mb-3 font-semibold">Sales trend · 30 days</h2>
          <LineChart
            labels={(trend.data?.points || []).map((p) => p.day)}
            series={[{ label: "Revenue", data: (trend.data?.points || []).map((p) => p.revenue),
              borderColor: palette.cyan, backgroundColor: "rgba(56,189,248,0.12)", fill: true, tension: 0.35, pointRadius: 0 }]}
          />
        </GlassCard>
        <GlassCard>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">Stock-out risks</h2>
            <Link to="/seller/forecast" className="text-xs text-sky-300">Forecast</Link>
          </div>
          <ActivityFeed items={atRisk.map((r) => ({
            id: r.product_id, text: `${r.sku} — reorder ${r.reorder_qty}`,
            sub: r.days_until_stockout != null ? `out in ~${r.days_until_stockout}d` : "watch",
          }))} />
          {!atRisk.length && <p className="text-muted2 text-sm">No imminent stock-outs. <GlassBadge color="#34d399">Healthy</GlassBadge></p>}
        </GlassCard>
      </div>
    </div>
  );
}
