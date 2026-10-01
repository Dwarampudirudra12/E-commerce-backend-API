import { revenueTrend, salesSummary, topProducts } from "../../api/analyticsApi.js";
import { useApi } from "../../hooks/useApi.js";
import { BarChart, LineChart, palette } from "../../components/charts/charts.jsx";
import { ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassCard, PageHeader } from "../../components/ui/primitives.jsx";
import { KPICard } from "../../components/analytics/widgets.jsx";
import { fmtMoney } from "../../utils/format.js";

/**
 * Shared analytics surface. The backend scopes rows by role
 * (seller: own products; admin/support: full), so one page serves all.
 */
export default function AnalyticsPage({ title, subtitle, days: defaultDays = 30 }) {
  const kpis = useApi(() => salesSummary());
  const trend = useApi(() => revenueTrend(defaultDays));
  const top = useApi(() => topProducts(8));

  return (
    <div>
      <PageHeader title={title} subtitle={subtitle} />
      {kpis.loading ? <TableSkeleton /> : kpis.error ? <ErrorState error={kpis.error} onRetry={kpis.reload} /> : (
        <div className="mb-5 flex flex-wrap gap-3">
          <KPICard label="Revenue" value={kpis.data.revenue} money
            spark={trend.data?.points?.map((p) => p.revenue)} />
          <KPICard label="Orders" value={kpis.data.orders} />
          <KPICard label="Avg order value" value={kpis.data.average_order_value} money />
          <KPICard label="Refund rate" value={`${(kpis.data.refund_rate * 100).toFixed(1)}%`} />
          <KPICard label="Fraud held" value={kpis.data.fraud_held} />
          <KPICard label="Low stock" value={kpis.data.low_stock_count} />
        </div>
      )}
      <div className="grid gap-4 lg:grid-cols-2">
        <GlassCard>
          <h2 className="mb-3 font-semibold">Revenue trend</h2>
          {trend.loading ? <TableSkeleton /> : (
            <LineChart
              labels={(trend.data?.points || []).map((p) => p.day)}
              series={[{ label: "Revenue", data: (trend.data?.points || []).map((p) => p.revenue),
                borderColor: palette.cyan, backgroundColor: "rgba(56,189,248,0.12)", fill: true, tension: 0.35, pointRadius: 0 }]}
            />)}
        </GlassCard>
        <GlassCard>
          <h2 className="mb-3 font-semibold">Top products by units</h2>
          {top.loading ? <TableSkeleton /> : (
            <BarChart
              labels={(top.data?.items || []).map((p) => p.sku)}
              series={[{ label: "Units", data: (top.data?.items || []).map((p) => p.units),
                backgroundColor: "rgba(167,139,250,0.7)", borderRadius: 6 }]}
            />)}
        </GlassCard>
      </div>
      <GlassCard className="mt-4">
        <h2 className="mb-2 font-semibold">Top products</h2>
        <ul className="divide-y divide-white/5 text-sm">
          {(top.data?.items || []).map((p) => (
            <li key={p.product_id} className="flex justify-between py-2">
              <span>{p.name} <span className="text-faint font-mono text-xs">{p.sku}</span></span>
              <span>{p.units} units · <strong>{fmtMoney(p.revenue)}</strong></span>
            </li>
          ))}
          {!top.data?.items?.length && !top.loading && (
            <li className="text-muted2 py-2 text-sm">No sales yet.</li>
          )}
        </ul>
      </GlassCard>
    </div>
  );
}
