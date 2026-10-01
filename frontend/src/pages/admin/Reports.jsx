import { useState } from "react";
import { salesSummary } from "../../api/analyticsApi.js";
import { downloadCsv } from "../../api/reportsApi.js";
import { useApi } from "../../hooks/useApi.js";
import { GlassAlert } from "../../components/ui/feedback.jsx";
import { GlassButton, GlassCard, GlassInput, GlassSelect, PageHeader } from "../../components/ui/primitives.jsx";
import { fmtMoney } from "../../utils/format.js";

export default function Reports() {
  const [kind, setKind] = useState("orders");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [state, setState] = useState("idle");
  const preview = useApi(() => salesSummary({
    ...(from ? { from_date: from } : {}), ...(to ? { to_date: to } : {}),
  }));

  const generate = async () => {
    setState("preparing");
    try {
      setState("generating");
      await downloadCsv(kind);
      setState("ready");
      setTimeout(() => setState("idle"), 3000);
    } catch {
      setState("idle");
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Reports" subtitle="Filtered CSV exports generated on demand." />
      {preview.data && (
        <GlassCard className="mb-4 flex gap-6 p-4 text-sm">
          <span>Orders <strong>{preview.data.orders}</strong></span>
          <span>Revenue <strong>{fmtMoney(preview.data.revenue)}</strong></span>
          <span>AOV <strong>{fmtMoney(preview.data.average_order_value)}</strong></span>
        </GlassCard>
      )}
      <GlassCard className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm"><span className="text-muted2 mb-1 block">Report type</span>
            <GlassSelect value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="orders">Orders</option>
              <option value="products">Products</option>
            </GlassSelect>
          </label>
          <div />
          <label className="text-sm"><span className="text-muted2 mb-1 block">From</span>
            <GlassInput type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></label>
          <label className="text-sm"><span className="text-muted2 mb-1 block">To</span>
            <GlassInput type="date" value={to} onChange={(e) => setTo(e.target.value)} /></label>
        </div>
        {state !== "idle" && (
          <GlassAlert tone={state === "ready" ? "success" : "info"}>
            {state === "preparing" ? "Preparing report…" : state === "generating" ? "Generating…" : "Ready — download started."}
          </GlassAlert>
        )}
        <GlassButton onClick={generate} disabled={state === "preparing" || state === "generating"}>
          Download CSV
        </GlassButton>
      </GlassCard>
    </div>
  );
}
