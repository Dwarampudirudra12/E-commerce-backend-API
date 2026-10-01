import { useState } from "react";
import { Link } from "react-router-dom";
import { listOrders } from "../../api/ordersApi.js";
import { useApi } from "../../hooks/useApi.js";
import { DataTable } from "../../components/ui/DataTable.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassInput, PageHeader } from "../../components/ui/primitives.jsx";
import { StatusBadge } from "../../components/commerce/OrderTimeline.jsx";
import { fmtMoney } from "../../utils/format.js";

/**
 * Customer lookup derived from order history (the API exposes customers
 * read-only through orders; profile data stays restricted).
 */
export default function Customers() {
  const [q, setQ] = useState("");
  const res = useApi(() => listOrders({ page: 1, page_size: 100 }));
  const byUser = {};
  (res.data?.items || []).forEach((o) => {
    byUser[o.user_id] = byUser[o.user_id] || { user_id: o.user_id, orders: 0, spent: 0, last: null, held: 0 };
    byUser[o.user_id].orders += 1;
    byUser[o.user_id].spent += Number(o.total);
    byUser[o.user_id].last = o.order_number;
    if (o.status === "ON_HOLD") byUser[o.user_id].held += 1;
  });
  const rows = Object.values(byUser).filter((c) =>
    !q || String(c.user_id).includes(q) || String(c.last).toLowerCase().includes(q.toLowerCase()));

  return (
    <div>
      <PageHeader title="Customers" subtitle="Read-only lookup aggregated from order history." />
      <div className="glass mb-4 max-w-xs p-4">
        <GlassInput placeholder="Search by user ID or order…" value={q}
          onChange={(e) => setQ(e.target.value)} aria-label="Search customers" />
      </div>
      {res.loading ? <TableSkeleton /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
        : rows.length === 0 ? <EmptyState title="No customers found" />
        : (
          <DataTable rowKey="user_id" columns={[
            { key: "user_id", label: "Customer", render: (c) => `#${c.user_id}` },
            { key: "orders", label: "Orders", render: (c) => c.orders },
            { key: "spent", label: "Lifetime value", render: (c) => fmtMoney(c.spent) },
            { key: "held", label: "Held", render: (c) => c.held > 0
              ? <StatusBadge status="ON_HOLD" /> : <span className="text-faint">—</span> },
            { key: "last", label: "Latest order", render: (c) => (
              <Link to="/support/orders" className="text-sky-300">{c.last}</Link>) },
          ]} rows={rows} />
        )}
    </div>
  );
}
