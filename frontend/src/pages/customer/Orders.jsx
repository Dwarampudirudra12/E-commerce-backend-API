import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listOrders } from "../../api/ordersApi.js";
import { useApi } from "../../hooks/useApi.js";
import { STATUS_META } from "../../constants/roles.js";
import { DataTable, Pagination } from "../../components/ui/DataTable.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassSelect, PageHeader } from "../../components/ui/primitives.jsx";
import { StatusBadge } from "../../components/commerce/OrderTimeline.jsx";
import { fmtDate, fmtMoney } from "../../utils/format.js";

export default function Orders() {
  const nav = useNavigate();
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const res = useApi(() => listOrders({ page, page_size: 12 }), [page]);
  const rows = (res.data?.items || []).filter((o) => !status || o.status === status);

  return (
    <div>
      <PageHeader title="Your orders" subtitle="Every state change is tracked and auditable." />
      <div className="glass mb-4 flex gap-3 p-4">
        <GlassSelect value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filter by status">
          <option value="">All statuses</option>
          {Object.keys(STATUS_META).map((s) => <option key={s} value={s}>{STATUS_META[s].label}</option>)}
        </GlassSelect>
      </div>
      {res.loading ? <TableSkeleton /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
        : rows.length === 0 ? <EmptyState title="No orders" hint="Your orders will appear here." />
        : (<>
          <DataTable rowKey="id" columns={[
            { key: "order_number", label: "Order", render: (o) => <Link to={`/orders/${o.id}`} className="font-semibold text-sky-300">{o.order_number}</Link> },
            { key: "status", label: "Status", render: (o) => <StatusBadge status={o.status} /> },
            { key: "total", label: "Total", render: (o) => fmtMoney(o.total) },
            { key: "created_at", label: "Placed", render: (o) => fmtDate(o.created_at) },
          ]} rows={rows} onRowClick={(o) => nav(`/orders/${o.id}`)} />
          <Pagination page={res.data.page} pageSize={res.data.page_size} total={res.data.total} onPage={setPage} />
        </>)}
    </div>
  );
}
