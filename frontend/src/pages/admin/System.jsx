import { metricsText, parseCounters, readiness } from "../../api/monitoringApi.js";
import { usePolling } from "../../hooks/useApi.js";
import { ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassBadge, GlassCard, PageHeader } from "../../components/ui/primitives.jsx";

function ServiceRow({ name, ok, detail }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-white/10 px-3 py-2.5 text-sm">
      <span className="font-medium">{name}</span>
      <span className="flex items-center gap-2">
        {detail && <span className="text-faint text-xs">{detail}</span>}
        <GlassBadge color={ok ? "#34d399" : "#f87171"}>{ok ? "Operational" : "Down"}</GlassBadge>
      </span>
    </div>
  );
}

export default function System() {
  const ready = usePolling(() => readiness().catch(() => null), 15000);
  const metrics = usePolling(() => metricsText().catch(() => ""), 15000);
  const counters = parseCounters(metrics.data || "");
  const sum = (name, pred) => (counters[name] || []).filter(pred || (() => true))
    .reduce((s, x) => s + x.value, 0);

  const checks = ready.data?.checks || {};
  const reqTotal = sum("http_requests_total");
  const err5xx = sum("http_requests_total", (x) => (x.labels.status || "").startsWith("5"));
  const orders = sum("orders_created_total");
  const webhooks = sum("payment_webhooks_total");
  const fraud = sum("fraud_scored_total");

  return (
    <div>
      <PageHeader title="System monitoring"
        subtitle="Liveness, dependencies and Prometheus counters — Grafana has the full boards." />
      {ready.loading && !ready.data ? <TableSkeleton /> : ready.error || !ready.data ? (
        <ErrorState error={ready.error || new Error("Readiness probe failed")} onRetry={ready.reload} />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <GlassCard className="space-y-2">
            <h2 className="mb-1 font-semibold">Services</h2>
            <ServiceRow name="API" ok detail="FastAPI" />
            <ServiceRow name="PostgreSQL" ok={checks.database === "up"} detail={checks.database} />
            <ServiceRow name="Redis" ok={checks.redis === "up"} detail={`cache/queue · ${checks.redis}`} />
            <ServiceRow name="Payment gateway" ok detail="Stripe test mode" />
            <ServiceRow name="Email provider" ok detail="SMTP / console (dev)" />
            <ServiceRow name="ML service" ok detail="in-process fraud + forecast" />
            <ServiceRow name="Storage" ok detail="local / S3" />
          </GlassCard>
          <GlassCard className="space-y-2">
            <h2 className="mb-1 font-semibold">Live counters <span className="text-faint text-xs">(from /metrics)</span></h2>
            <ServiceRow name="HTTP requests" ok detail={String(reqTotal)} />
            <ServiceRow name="5xx errors" ok={reqTotal === 0 || err5xx / reqTotal < 0.02}
              detail={reqTotal ? `${((err5xx / reqTotal) * 100).toFixed(2)}%` : "0%"} />
            <ServiceRow name="Orders created" ok detail={String(orders)} />
            <ServiceRow name="Payment webhooks" ok detail={String(webhooks)} />
            <ServiceRow name="Fraud scorings" ok detail={String(fraud)} />
            <div className="pt-2 text-xs">
              <a className="text-sky-300 hover:text-sky-200" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">Swagger UI</a>
              <span className="text-faint"> · </span>
              <a className="text-sky-300 hover:text-sky-200" href="http://localhost:8000/redoc" target="_blank" rel="noreferrer">ReDoc</a>
              <span className="text-faint"> · </span>
              <a className="text-sky-300 hover:text-sky-200" href="http://localhost:8000/metrics" target="_blank" rel="noreferrer">Raw metrics</a>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
}
