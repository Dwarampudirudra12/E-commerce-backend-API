import { Link } from "react-router-dom";
import { salesSummary } from "../../api/analyticsApi.js";
import { reviewQueue } from "../../api/ordersApi.js";
import { myNotifications } from "../../api/notificationsApi.js";
import { fraudDistribution } from "../../api/fraudApi.js";
import { revenueTrend, topProducts } from "../../api/analyticsApi.js";
import { usePolling } from "../../hooks/useApi.js";
import { BarChart, DonutChart, LineChart, palette } from "../../components/charts/charts.jsx";
import { ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassBadge, GlassCard, PageHeader } from "../../components/ui/primitives.jsx";
import { ActivityFeed, KPICard } from "../../components/analytics/widgets.jsx";
import { apiHealth } from "../../api/client.js";

export default function AdminDashboard() {
  const kpis = usePolling(() => salesSummary(), 30000);
  const trend = usePolling(() => revenueTrend(30), 30000);
  const top = usePolling(() => topProducts(8), 30000);
  const fraud = usePolling(() => fraudDistribution().catch(() => ({})), 30000);
  const queue = usePolling(() => reviewQueue().catch(() => ({ items: [], total: 0 })), 30000);
  const notes = usePolling(() => myNotifications({ page_size: 6 }).catch(() => ({ items: [] })), 30000);
  const health = usePolling(() => apiHealth().catch(() => ({ connected: false })), 30000);

  return (
    <div>
      <PageHeader
        title="Command center"
        subtitle="Revenue, risk and operations — refreshed every 30 seconds."
        actions={[
          <span key="api" title="Backend connection">
            <GlassBadge color={health.data?.connected === false ? "#fbbf24" : "#34d399"}>
              {health.data?.connected === false ? "Demo Mode" : "API Connected"}
            </GlassBadge>
          </span>,
          <Link key="api-docs" to="/admin/system" className="btn-ghost px-3 py-1.5 text-sm">System</Link>,
        ]}
      />
      {kpis.loading ? <TableSkeleton /> : kpis.error ? <ErrorState error={kpis.error} onRetry={kpis.reload} /> : (
        <div className="mb-5 flex flex-wrap gap-3">
          <KPICard label="Total revenue" value={kpis.data.revenue} money spark={trend.data?.points?.map((p) => p.revenue)} />
          <KPICard label="Orders" value={kpis.data.orders} />
          <KPICard label="Avg order value" value={kpis.data.average_order_value} money />
          <KPICard label="Refund rate" value={`${(kpis.data.refund_rate * 100).toFixed(1)}%`} />
          <KPICard label="Fraud held" value={kpis.data.fraud_held} />
          <KPICard label="Low stock" value={kpis.data.low_stock_count} />
        </div>
      )}
      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard className="lg:col-span-2">
          <h2 className="mb-3 font-semibold">Revenue trend</h2>
          <LineChart
            labels={(trend.data?.points || []).map((p) => p.day)}
            series={[
              { label: "Revenue", data: (trend.data?.points || []).map((p) => p.revenue),
                borderColor: palette.cyan, backgroundColor: "rgba(56,189,248,0.12)", fill: true, tension: 0.35, pointRadius: 0 },
            ]}
          />
        </GlassCard>
        <GlassCard>
          <h2 className="mb-3 font-semibold">Orders by status</h2>
          <DonutChart
            labels={Object.keys(kpis.data?.by_status || {})}
            values={Object.values(kpis.data?.by_status || {})}
            colors={[palette.emerald, palette.amber, palette.cyan, palette.violet, palette.rose, palette.slate]}
          />
        </GlassCard>
        <GlassCard>
          <h2 className="mb-3 font-semibold">Top products</h2>
          <BarChart horizontal
            labels={(top.data?.items || []).map((p) => p.sku)}
            series={[{ label: "Units", data: (top.data?.items || []).map((p) => p.units),
              backgroundColor: "rgba(167,139,250,0.7)", borderRadius: 6 }]}
          />
        </GlassCard>
        <GlassCard>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">Fraud distribution</h2>
            <Link to="/admin/fraud" className="text-xs text-sky-300">Investigate</Link>
          </div>
          <DonutChart
            labels={Object.keys(fraud.data || {})}
            values={Object.values(fraud.data || {})}
            colors={[palette.emerald, palette.amber, palette.rose]}
          />
        </GlassCard>
        <GlassCard>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">Live activity</h2>
            <span className="flex items-center gap-1 text-xs text-emerald-300">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" /> live
            </span>
          </div>
          <ActivityFeed items={[
            ...(queue.data?.items || []).slice(0, 3).map((o) => ({
              id: `q-${o.id}`, text: `${o.order_number} held · risk ${Number(o.risk_score).toFixed(2)}`, time: o.created_at,
            })),
            ...((notes.data?.items || []).slice(0, 4).map((n) => ({
              id: `n-${n.id}`, text: n.type.replace(/_/g, " "), time: n.created_at,
            }))),
          ]} />
        </GlassCard>
      </div>
    </div>
  );
}
