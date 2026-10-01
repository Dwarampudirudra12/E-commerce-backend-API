import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { getCart } from "../../api/cartApi.js";
import { checkout } from "../../api/ordersApi.js";
import { confirmTestPayment, paymentForOrder } from "../../api/paymentsApi.js";
import { myAddresses } from "../../api/usersApi.js";
import { useApi } from "../../hooks/useApi.js";
import { GlassAlert } from "../../components/ui/feedback.jsx";
import { GlassButton, GlassCard, GlassInput, PageHeader } from "../../components/ui/primitives.jsx";
import { fmtMoney } from "../../utils/format.js";

const STEPS = ["Address", "Delivery", "Payment", "Review", "Done"];

export default function Checkout() {
  const nav = useNavigate();
  const [step, setStep] = useState(0);
  const [address, setAddress] = useState({ street: "", city: "", country: "US", zip_code: "" });
  const [code, setCode] = useState("");
  const [idemKey] = useState(() => (crypto.randomUUID ? crypto.randomUUID() : String(Date.now())));
  const [order, setOrder] = useState(null);
  const [payment, setPayment] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const cart = useApi(() => getCart());
  const addrs = useApi(() => myAddresses().catch(() => []));

  useEffect(() => {
    if (addrs.data?.find((a) => a.is_default)) {
      const d = addrs.data.find((a) => a.is_default);
      setAddress({ street: d.street || "", city: d.city || "", country: d.country || "US", zip_code: d.zip_code || "" });
    }
  }, [addrs.data]);

  const placeOrder = async () => {
    setBusy(true);
    setError("");
    try {
      const o = await checkout(
        { shipping_address: address, discount_code: code || null },
        idemKey
      );
      setOrder(o);
      try {
        setPayment(await paymentForOrder(o.id));
      } catch { /* ON_HOLD orders have no intent yet */ }
      setStep(4);
      cart.reload();
    } catch (e) {
      setError(e.status === 409
        ? "Some items just sold out — nothing was reserved. Adjust quantities and retry."
        : e.message);
    } finally {
      setBusy(false);
    }
  };

  const payTest = async () => {
    setBusy(true);
    setError("");
    try {
      await confirmTestPayment(order.id);
      const p = await paymentForOrder(order.id);
      setPayment(p);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="Secure checkout" subtitle="Idempotent — safe to retry on network errors." />
      <ol className="mb-6 flex items-center gap-1" aria-label="Checkout progress">
        {STEPS.map((s, i) => (
          <li key={s} className="flex flex-1 items-center gap-1">
            <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${i <= step ? "bg-gradient-to-br from-sky-500 to-violet-600" : "bg-white/10 text-slate-400"}`}>
              {i + 1}
            </span>
            <span className={`hidden text-xs sm:block ${i <= step ? "text-white" : "text-faint"}`}>{s}</span>
            {i < STEPS.length - 1 && <span className="mx-1 h-px flex-1 bg-white/10" aria-hidden />}
          </li>
        ))}
      </ol>

      {error && <div className="mb-4"><GlassAlert tone="danger">{error}</GlassAlert></div>}

      {step === 0 && (
        <GlassCard className="space-y-3">
          <h2 className="font-semibold">Shipping address</h2>
          {(["street", "city", "zip_code", "country"]).map((f) => (
            <GlassInput key={f} placeholder={f.replace("_", " ")} value={address[f]}
              onChange={(e) => setAddress({ ...address, [f]: e.target.value })}
              aria-label={f} />
          ))}
          <GlassButton onClick={() => setStep(1)} className="px-5">Continue</GlassButton>
        </GlassCard>
      )}

      {step === 1 && (
        <GlassCard className="space-y-3">
          <h2 className="font-semibold">Delivery</h2>
          <label className="glass flex cursor-pointer items-center justify-between p-4">
            <span><span className="font-medium">Standard</span>
              <span className="text-muted2 block text-xs">3–5 business days · $4.00 (free over $50)</span></span>
            <input type="radio" checked readOnly aria-label="Standard delivery" />
          </label>
          <div className="flex gap-2">
            <GlassButton variant="ghost" onClick={() => setStep(0)}>Back</GlassButton>
            <GlassButton onClick={() => setStep(2)} className="px-5">Continue</GlassButton>
          </div>
        </GlassCard>
      )}

      {step === 2 && (
        <GlassCard className="space-y-3">
          <h2 className="font-semibold">Payment · Stripe test mode</h2>
          <p className="text-muted2 text-sm">
            A test-mode payment intent is created with your order. No real charge occurs;
            card details are never collected in this demo.
          </p>
          <GlassInput placeholder="Discount code (optional)" value={code}
            onChange={(e) => setCode(e.target.value)} aria-label="Discount code" />
          <div className="flex gap-2">
            <GlassButton variant="ghost" onClick={() => setStep(1)}>Back</GlassButton>
            <GlassButton onClick={() => setStep(3)} className="px-5">Review order</GlassButton>
          </div>
        </GlassCard>
      )}

      {step === 3 && (
        <GlassCard className="space-y-3">
          <h2 className="font-semibold">Review</h2>
          <p className="text-muted2 text-sm">
            {(cart.data || []).length} item(s) · {address.city}, {address.country}
          </p>
          <GlassAlert tone="info">Stock is reserved atomically when you confirm — it can never go negative.</GlassAlert>
          <div className="flex gap-2">
            <GlassButton variant="ghost" onClick={() => setStep(2)}>Back</GlassButton>
            <GlassButton onClick={placeOrder} disabled={busy} className="px-5">
              {busy ? "Placing order…" : "Confirm & pay"}
            </GlassButton>
          </div>
        </GlassCard>
      )}

      {step === 4 && order && (
        <GlassCard className="space-y-3 text-center">
          {order.status === "ON_HOLD" ? (
            <>
              <XCircle size={40} className="mx-auto text-amber-400" aria-hidden />
              <h2 className="font-display text-xl font-bold">Order held for review</h2>
              <p className="text-muted2 text-sm">
                {order.order_number} was flagged (risk {Number(order.risk_score).toFixed(2)}).
                Our team reviews held orders promptly.
              </p>
              <Link to={`/orders/${order.id}`} className="btn-ghost inline-block px-5 py-2 text-sm">Track order</Link>
            </>
          ) : payment?.status === "SUCCEEDED" ? (
            <>
              <CheckCircle2 size={40} className="mx-auto text-emerald-400" aria-hidden />
              <h2 className="font-display text-xl font-bold">Payment confirmed</h2>
              <p className="text-muted2 text-sm">{order.order_number} · {fmtMoney(order.total)} · PAID</p>
              <Link to={`/orders/${order.id}`} className="btn-primary inline-block px-5 py-2 text-sm">Track order</Link>
            </>
          ) : (
            <>
              <Loader2 size={40} className="mx-auto animate-spin text-sky-300" aria-hidden />
              <h2 className="font-display text-xl font-bold">Awaiting payment</h2>
              <p className="text-muted2 text-sm">{order.order_number} · {fmtMoney(order.total)} · {order.status}</p>
              <div className="flex justify-center gap-2">
                <GlassButton onClick={payTest} disabled={busy}>
                  {busy ? "Confirming…" : "Complete test payment"}
                </GlassButton>
                <GlassButton variant="ghost" onClick={() => nav(`/orders/${order.id}`)}>Track order</GlassButton>
              </div>
            </>
          )}
        </GlassCard>
      )}
    </div>
  );
}
