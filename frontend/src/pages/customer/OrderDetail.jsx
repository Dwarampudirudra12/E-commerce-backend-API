import { useState } from "react";
import { useParams } from "react-router-dom";
import { changeStatus, getOrder, orderHistory } from "../../api/ordersApi.js";
import { paymentForOrder, refund as refundPayment } from "../../api/paymentsApi.js";
import { useAuth } from "../../contexts/AuthContext.jsx";
import { useApi } from "../../hooks/useApi.js";
import { EmptyState, ErrorState, GlassAlert, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassButton, GlassCard, PageHeader } from "../../components/ui/primitives.jsx";
import { OrderTimeline, StatusBadge } from "../../components/commerce/OrderTimeline.jsx";
import { RiskGauge } from "../../components/analytics/widgets.jsx";
import { riskMeta } from "../../constants/roles.js";
import { fmtDate, fmtMoney } from "../../utils/format.js";

function RefundButton({ orderId, payment, onDone }) {
  const [busy, setBusy] = useState(false);
  const [amount, setAmount] = useState("");
  const go = async () => {
    if (!window.confirm(`Refund ${amount || "the full amount"} for this order?`)) return;
    setBusy(true);
    try {
      const r = await refundPayment(payment.id, amount ? { amount: Number(amount) } : {});
      onDone(`Refund ${r.gateway_refund_id} processed.`);
    } catch (e) {
      onDone(e.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <span className="flex items-center gap-1">
      <input value={amount} onChange={(e) => setAmount(e.target.value)}
        placeholder="Amount" inputMode="decimal" aria-label="Refund amount"
        className="glass-input w-20 px-2 py-1 text-xs" />
      <button disabled={busy} onClick={go} className="btn-ghost px-2 py-1 text-xs">
        {busy ? "…" : "Refund"}
      </button>
    </span>
  );
}

export default function OrderDetail() {
  const { id } = useParams();
  const { role } = useAuth();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const res = useApi(() => getOrder(id).then(async (o) => {
    let payment = null;
    let history = [];
    try {
      payment = await paymentForOrder(o.id);
    } catch { /* no intent yet (ON_HOLD) */ }
    try {
      history = (await orderHistory(o.id)).items || [];
    } catch { /* unavailable to this role */ }
    return { ...o, payment, history };
  }), [id]);

  const act = async (to) => {
    setBusy(true);
    try {
      await changeStatus(id, to);
      setMsg(`Order moved to ${to}.`);
      res.reload();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (res.loading) return <TableSkeleton />;
  if (res.error) return <ErrorState error={res.error} onRetry={res.reload} />;
  const o = res.data;
  if (!o) return <EmptyState title="Order not found" />;
  const rm = riskMeta(o.risk_score);
  const cancellable = ["CREATED", "PENDING_PAYMENT", "ON_HOLD", "PAID", "PACKED"].includes(o.status);

  return (
    <div>
      <PageHeader title={o.order_number} subtitle={`Placed ${fmtDate(o.created_at)}`}
        actions={[<StatusBadge key="s" status={o.status} />]} />
      {msg && <div className="glass mb-4 px-4 py-2 text-sm" role="status">{msg}</div>}
      <div className="grid gap-5 lg:grid-cols-3">
        <GlassCard className="lg:col-span-2">
          <h2 className="mb-4 font-semibold">Tracking</h2>
          <OrderTimeline order={o} history={o.history || []} />
        </GlassCard>
        <div className="space-y-5">
          <GlassCard>
            <h2 className="mb-2 font-semibold">Totals</h2>
            <dl className="space-y-1 text-sm">
              {[["Subtotal", o.subtotal], ["Discount", o.discount], ["Tax", o.tax], ["Shipping", o.shipping]].map(([l, v]) => (
                <div key={l} className="flex justify-between"><dt className="text-muted2">{l}</dt><dd>{fmtMoney(v)}</dd></div>
              ))}
              <div className="flex justify-between border-t border-white/10 pt-1.5 font-bold"><dt>Total</dt><dd>{fmtMoney(o.total)}</dd></div>
            </dl>
            <h3 className="mb-1 mt-4 font-semibold">Items</h3>
            <ul className="space-y-1 text-sm">
              {o.items.map((i, x) => (
                <li key={x} className="flex justify-between">
                  <span className="text-muted2">#{i.product_id} × {i.quantity}</span>
                  <span>{fmtMoney(i.subtotal)}</span>
                </li>
              ))}
            </ul>
          </GlassCard>
          <GlassCard>
            <h2 className="mb-2 font-semibold">Payment</h2>
            {o.payment ? (
              <dl className="space-y-1 text-sm">
                <div className="flex justify-between"><dt className="text-muted2">State</dt><dd>{o.payment.status}</dd></div>
                <div className="flex justify-between"><dt className="text-muted2">Reference</dt><dd className="font-mono text-xs">{o.payment.gateway_ref}</dd></div>
                <div className="flex justify-between"><dt className="text-muted2">Amount</dt><dd>{fmtMoney(o.payment.amount)}</dd></div>
              </dl>
            ) : <p className="text-muted2 text-sm">No payment intent yet.</p>}
          </GlassCard>
          {o.risk_score != null && (
            <GlassCard className="flex items-center gap-4">
              <RiskGauge score={Number(o.risk_score)} size={110} />
              <div className="text-sm">
                <div className="font-semibold" style={{ color: rm.color }}>{rm.label}</div>
                <div className="text-muted2 text-xs">Scored before payment capture.</div>
              </div>
            </GlassCard>
          )}
          {(role === "CUSTOMER" || cancellable) && o.status !== "CANCELLED" && (
            <GlassCard>
              <h2 className="mb-2 font-semibold">Actions</h2>
              <div className="flex flex-wrap gap-2">
                {role === "CUSTOMER" && cancellable && (
                  <GlassButton variant="ghost" disabled={busy} onClick={() => act("CANCELLED")}>Cancel order</GlassButton>
                )}
                {(role === "SELLER" || role === "SUPPORT" || role === "ADMIN") && o.status === "PAID" && (
                  <GlassButton disabled={busy} onClick={() => act("PACKED")}>Mark packed</GlassButton>
                )}
                {(role === "SELLER" || role === "SUPPORT" || role === "ADMIN") && o.status === "PACKED" && (
                  <GlassButton disabled={busy} onClick={() => act("SHIPPED")}>Mark shipped</GlassButton>
                )}
                {(role === "SUPPORT" || role === "ADMIN") && o.status === "SHIPPED" && (
                  <GlassButton disabled={busy} onClick={() => act("DELIVERED")}>Mark delivered</GlassButton>
                )}
                {(role === "SUPPORT" || role === "ADMIN") && o.payment?.status === "SUCCEEDED" && o.status !== "REFUNDED" && (
                  <RefundButton orderId={o.id} payment={o.payment} onDone={(m) => { setMsg(m); res.reload(); }} />
                )}
              </div>
              {role === "CUSTOMER" && !cancellable && (
                <GlassAlert tone="info">This order can no longer be cancelled.</GlassAlert>
              )}
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
}
