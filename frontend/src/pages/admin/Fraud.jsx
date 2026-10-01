import { Link } from "react-router-dom";
import { fraudDistribution } from "../../api/fraudApi.js";
import { reviewQueue } from "../../api/ordersApi.js";
import { usePolling } from "../../hooks/useApi.js";
import { DonutChart, palette } from "../../components/charts/charts.jsx";
import { ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassCard, PageHeader } from "../../components/ui/primitives.jsx";
import { KPICard, RiskGauge } from "../../components/analytics/widgets.jsx";

export default function Fraud() {
  const dist = usePolling(() => fraudDistribution().catch(() => ({})), 30000);
  const queue = usePolling(() => reviewQueue(), 30000);
  const d = dist.data || {};
  const total = Object.values(d).reduce((s, v) => s + v, 0);
  const avgNote = "Mean score across analysed orders";

  return (
    <div>
      <PageHeader title="Fraud intelligence" subtitle="Real-time order risk analysis · thresholds 0.30 / 0.70." />
      <div className="mb-5 flex flex-wrap gap-3">
        <KPICard label="Orders analysed" value={total || "—"} />
        <KPICard label="High risk" value={d.high || 0} />
        <KPICard label="Medium risk" value={d.medium || 0} />
        <KPICard label="Low risk" value={d.low || 0} />
        <KPICard label="Manual reviews" value={queue.data?.total ?? "—"} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <GlassCard>
          <h2 className="mb-3 font-semibold">Risk distribution</h2>
          {dist.loading ? <TableSkeleton /> : dist.error ? <ErrorState error={dist.error} /> : (
            <DonutChart labels={Object.keys(d)} values={Object.values(d)}
              colors={[palette.emerald, palette.amber, palette.rose]} />
          )}
          <p className="text-faint mt-2 text-xs">{avgNote}. Green &lt; 0.30 · amber 0.30–0.70 · red &gt; 0.70.</p>
        </GlassCard>
        <GlassCard>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">Held for review</h2>
            <Link to="/support/fraud-review" className="text-xs text-sky-300">Open workbench</Link>
          </div>
          <ul className="space-y-2">
            {(queue.data?.items || []).slice(0, 5).map((o) => (
              <li key={o.id}>
                <Link to={`/admin/fraud/${o.id}`} className="glass-hover glass flex items-center gap-3 p-3">
                  <RiskGauge score={Number(o.risk_score)} size={64} />
                  <div className="min-w-0">
                    <div className="font-semibold">{o.order_number}</div>
                    <div className="text-muted2 truncate text-xs">{(o.risk_factors || []).join("; ")}</div>
                  </div>
                </Link>
              </li>
            ))}
            {!queue.data?.items?.length && !queue.loading && (
              <li className="text-muted2 text-sm">Queue is clear.</li>
            )}
          </ul>
        </GlassCard>
      </div>
    </div>
  );
}
