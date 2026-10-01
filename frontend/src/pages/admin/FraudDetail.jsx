import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { changeStatus, reviewQueue } from "../../api/ordersApi.js";
import { useApi } from "../../hooks/useApi.js";
import { EmptyState, ErrorState, GlassAlert, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassButton, GlassCard, PageHeader } from "../../components/ui/primitives.jsx";
import { FactorBar, RiskGauge } from "../../components/analytics/widgets.jsx";
import { fmtMoney } from "../../utils/format.js";

/** Order risk investigation: score, ablation-style factors, disposition. */
export default function FraudDetail() {
  const { id } = useParams();
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const [done, setDone] = useState("");
  const queue = useApi(() => reviewQueue(), [id]);
  const order = queue.data?.items?.find((o) => String(o.id) === String(id));

  const decide = async (to) => {
    setBusy(true);
    try {
      await changeStatus(id, to, note);
      setDone(to === "PENDING_PAYMENT" ? "Approved — payment intent created." : "Rejected — order cancelled, stock released.");
      queue.reload();
    } catch (e) {
      setDone(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (queue.loading) return <TableSkeleton />;
  if (queue.error) return <ErrorState error={queue.error} onRetry={queue.reload} />;
  if (!order) {
    return (
      <div>
        <PageHeader title="Order risk analysis" />
        <EmptyState title="Not in the review queue"
          hint="This order is no longer held — it may already have been approved or rejected."
          action={<Link to="/admin/fraud" className="btn-ghost px-4 py-2 text-sm">Back to fraud intelligence</Link>} />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Order risk analysis" subtitle={`${order.order_number} · ${fmtMoney(order.total)}`} />
      {done && <div className="mb-4"><GlassAlert tone="info">{done}</GlassAlert></div>}
      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard className="flex flex-col items-center p-6">
          <RiskGauge score={Number(order.risk_score)} size={150} />
          <p className="text-muted2 mt-2 text-xs">Model output at checkout, before capture.</p>
        </GlassCard>
        <GlassCard className="lg:col-span-2">
          <h2 className="mb-3 font-semibold">Why was this order flagged?</h2>
          {(order.risk_factors || []).map((f, i) => (
            <FactorBar key={f} factor={f} strength={0.9 - i * 0.2} />
          ))}
          {!order.risk_factors?.length && (
            <p className="text-muted2 text-sm">No factor detail recorded.</p>
          )}
          <p className="text-faint mt-3 text-xs">
            Factors come from the checkout risk scorer (model ablation when available,
            rule-based fallback otherwise) — never hand-written.
          </p>
        </GlassCard>
      </div>
      <GlassCard className="mt-4">
        <h2 className="mb-2 font-semibold">Disposition</h2>
        <textarea className="glass-input min-h-[64px] w-full" placeholder="Internal note…"
          value={note} onChange={(e) => setNote(e.target.value)} aria-label="Internal note" />
        <div className="mt-3 flex flex-wrap gap-2">
          <GlassButton disabled={busy} onClick={() => decide("PENDING_PAYMENT")}>Approve</GlassButton>
          <GlassButton variant="ghost" disabled={busy} onClick={() => decide("CANCELLED")}>Reject</GlassButton>
          <Link to={`/orders/${order.id}`} className="btn-ghost px-4 py-2 text-sm">Full order</Link>
        </div>
      </GlassCard>
    </div>
  );
}
