import { Link } from "react-router-dom";
import { listOrders, reviewQueue } from "../../api/ordersApi.js";
import { listRefunds } from "../../api/refundsApi.js";
import { usePolling } from "../../hooks/useApi.js";
import { ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassCard, PageHeader } from "../../components/ui/primitives.jsx";
import { ActivityFeed, KPICard } from "../../components/analytics/widgets.jsx";
import { StatusBadge } from "../../components/commerce/OrderTimeline.jsx";

export default function SupportDashboard() {
  const queue = usePolling(() => reviewQueue(), 30000);
  const refunds = usePolling(() => listRefunds().catch(() => ({ items: [] })), 30000);
  const orders = usePolling(() => listOrders({ page: 1, page_size: 50 }), 30000);
  const queued = queue.data?.items || [];
  const pendingRefunds = (refunds.data?.items || []).filter((r) => r.status === "PENDING");

  return (
    <div>
      <PageHeader title="Support console" subtitle="Review queue, refunds and live order flow." />
      <div className="mb-5 flex flex-wrap gap-3">
        <KPICard label="Awaiting review" value={queue.data?.total ?? "—"} />
        <KPICard label="Refund requests" value={pendingRefunds.length} />
        <KPICard label="Orders (page)" value={orders.data?.total ?? "—"} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <GlassCard>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">Fraud review queue</h2>
            <Link to="/support/fraud-review" className="text-xs text-sky-300">Open queue</Link>
          </div>
          <ActivityFeed items={queued.slice(0, 6).map((o) => ({
            id: o.id, text: `${o.order_number} · risk ${Number(o.risk_score).toFixed(2)} · $${o.total}`,
            sub: (o.risk_factors || []).slice(0, 2).join("; "),
          }))} />
        </GlassCard>
        <GlassCard>
          <h2 className="mb-3 font-semibold">Latest orders</h2>
          <ul className="space-y-2 text-sm">
            {(orders.data?.items || []).slice(0, 6).map((o) => (
              <li key={o.id} className="flex items-center justify-between gap-2">
                <Link to={`/orders/${o.id}`} className="font-medium text-sky-300">{o.order_number}</Link>
                <StatusBadge status={o.status} />
              </li>
            ))}
          </ul>
        </GlassCard>
      </div>
      {queue.error && <div className="mt-4"><ErrorState error={queue.error} onRetry={queue.reload} /></div>}
      {(queue.loading || orders.loading) && <div className="mt-4"><TableSkeleton /></div>}
    </div>
  );
}
