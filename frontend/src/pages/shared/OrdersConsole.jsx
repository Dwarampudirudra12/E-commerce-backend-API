import { useState } from "react";
import { Link } from "react-router-dom";
import { changeStatus, listOrders } from "../../api/ordersApi.js";
import { useApi } from "../../hooks/useApi.js";
import { STATUS_META, riskMeta } from "../../constants/roles.js";
import { DataTable, Pagination } from "../../components/ui/DataTable.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassInput, GlassSelect, PageHeader } from "../../components/ui/primitives.jsx";
import { StatusBadge } from "../../components/commerce/OrderTimeline.jsx";
import { fmtDate, fmtMoney } from "../../utils/format.js";

/**
 * Role-aware order console.
 * variant: "seller" (own products) | "support" (all + fulfil actions) | "admin" (all).
 */
export default function OrdersConsole({ variant, title, subtitle }) {
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const res = useApi(() => listOrders({ page, page_size: 15 }), [page]);
  const [busy, setBusy] = useState(null);

  const rows = (res.data?.items || []).filter((o) => {
    if (status && o.status !== status) return false;
    if (q && !(o.order_number || "").toLowerCase().includes(q.toLowerCase())) return false;
    return true;
  });

  const act = async (o, to) => {
    setBusy(o.id);
    try {
      await changeStatus(o.id, to);
      res.reload();
    } catch (e) {
      alert(e.message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      <PageHeader title={title} subtitle={subtitle} />
      <div className="glass mb-4 flex flex-wrap gap-3 p-4">
        <GlassInput placeholder="Search order number…" value={q} className="max-w-xs"
          onChange={(e) => setQ(e.target.value)} aria-label="Search orders" />
        <GlassSelect value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filter by status">
          <option value="">All statuses</option>
          {Object.keys(STATUS_META).map((s) => <option key={s} value={s}>{STATUS_META[s].label}</option>)}
        </GlassSelect>
      </div>
      {res.loading ? <TableSkeleton /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
        : rows.length === 0 ? <EmptyState title="No orders" hint="Orders matching these filters will appear here." />
        : (<>
          <DataTable rowKey="id" columns={[
            { key: "order_number", label: "Order", render: (o) => (
              <Link to={`/orders/${o.id}`} className="font-semibold text-sky-300">{o.order_number}</Link>) },
            { key: "total", label: "Amount", render: (o) => fmtMoney(o.total) },
            { key: "status", label: "Status", render: (o) => <StatusBadge status={o.status} /> },
            ...(variant !== "seller" ? [{
              key: "risk", label: "Risk", render: (o) => {
                const m = riskMeta(o.risk_score);
                return o.risk_score == null ? <span className="text-faint">—</span>
                  : <span className="font-mono text-xs font-bold" style={{ color: m.color }}>
                    {Number(o.risk_score).toFixed(2)} · {m.label}
                  </span>;
              },
            }] : []),
            { key: "created_at", label: "Placed", render: (o) => fmtDate(o.created_at) },
            { key: "actions", label: "Actions", render: (o) => (
              <span className="flex gap-1">
                {o.status === "PAID" && (
                  <button disabled={busy === o.id} onClick={() => act(o, "PACKED")}
                    className="btn-ghost px-2 py-1 text-xs">Pack</button>)}
                {o.status === "PACKED" && (
                  <button disabled={busy === o.id} onClick={() => act(o, "SHIPPED")}
                    className="btn-ghost px-2 py-1 text-xs">Ship</button>)}
                {(variant !== "seller" && o.status === "SHIPPED") && (
                  <button disabled={busy === o.id} onClick={() => act(o, "DELIVERED")}
                    className="btn-ghost px-2 py-1 text-xs">Deliver</button>)}
              </span>) },
          ]} rows={rows} />
          <Pagination page={res.data.page} pageSize={res.data.page_size} total={res.data.total} onPage={setPage} />
        </>)}
    </div>
  );
}
