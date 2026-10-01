import { useState } from "react";
import { Link } from "react-router-dom";
import { changeStatus, reviewQueue } from "../../api/ordersApi.js";
import { useApi } from "../../hooks/useApi.js";
import { riskMeta } from "../../constants/roles.js";
import { DataTable } from "../../components/ui/DataTable.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassButton, PageHeader } from "../../components/ui/primitives.jsx";
import { FactorBar, RiskGauge } from "../../components/analytics/widgets.jsx";
import { StatusBadge } from "../../components/commerce/OrderTimeline.jsx";
import { fmtMoney } from "../../utils/format.js";

/** Fraud review workbench: queue table + inline investigation + actions. */
export default function FraudReview() {
  const queue = useApi(() => reviewQueue());
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");

  const decide = async (order, to) => {
    setBusy(true);
    try {
      await changeStatus(order.id, to, note);
      setSelected(null);
      setNote("");
      queue.reload();
    } catch (e) {
      alert(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <PageHeader title="Fraud review" subtitle="Real-time risk analysis with plain-language factors." />
      {queue.loading ? <TableSkeleton /> : queue.error ? <ErrorState error={queue.error} onRetry={queue.reload} />
        : queue.data.total === 0 ? <EmptyState title="Queue is clear" hint="No orders are currently held for review." />
        : (
          <DataTable rowKey="id" onRowClick={setSelected} columns={[
            { key: "order_number", label: "Order", render: (o) => (
              <span className="font-semibold text-sky-300">{o.order_number}</span>) },
            { key: "total", label: "Amount", render: (o) => fmtMoney(o.total) },
            { key: "risk", label: "Risk", render: (o) => {
              const m = riskMeta(o.risk_score);
              return <span className="font-mono text-xs font-bold" style={{ color: m.color }}>
                {Number(o.risk_score).toFixed(2)} · {m.label}</span>;
            } },
            { key: "factors", label: "Top factors", render: (o) => (
              <span className="text-muted2 text-xs">{(o.risk_factors || []).slice(0, 2).join("; ")}</span>) },
            { key: "status", label: "Status", render: (o) => <StatusBadge status={o.status} /> },
          ]} rows={queue.data.items} />
        )}
      {selected && (
        <div className="glass mt-4 grid gap-4 p-5 md:grid-cols-3">
          <div className="flex flex-col items-center">
            <RiskGauge score={Number(selected.risk_score)} />
            <Link to={`/orders/${selected.id}`} className="mt-2 text-sm text-sky-300">{selected.order_number}</Link>
          </div>
          <div className="md:col-span-2">
            <h3 className="mb-2 font-semibold">Why was this order flagged?</h3>
            {(selected.risk_factors || []).map((f, i) => (
              <FactorBar key={f} factor={f} strength={0.9 - i * 0.2} />
            ))}
            {!selected.risk_factors?.length && (
              <p className="text-muted2 text-sm">No factor detail recorded for this order.</p>
            )}
            <textarea className="glass-input mt-3 min-h-[64px] w-full" placeholder="Internal note (stored with the status change)…"
              value={note} onChange={(e) => setNote(e.target.value)} aria-label="Internal note" />
            <div className="mt-3 flex flex-wrap gap-2">
              <GlassButton disabled={busy} onClick={() => decide(selected, "PENDING_PAYMENT")}>Approve</GlassButton>
              <GlassButton variant="ghost" disabled={busy} onClick={() => decide(selected, "CANCELLED")}>Reject</GlassButton>
              <GlassButton variant="ghost" onClick={() => setSelected(null)}>Close</GlassButton>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
