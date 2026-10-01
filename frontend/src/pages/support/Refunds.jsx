import { Link } from "react-router-dom";
import { listRefunds } from "../../api/refundsApi.js";
import { useApi } from "../../hooks/useApi.js";
import { DataTable } from "../../components/ui/DataTable.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { PageHeader } from "../../components/ui/primitives.jsx";
import { fmtDate, fmtMoney } from "../../utils/format.js";

export default function Refunds() {
  const res = useApi(() => listRefunds().catch(() => ({ items: [] })));
  return (
    <div>
      <PageHeader title="Refunds" subtitle="Issue refunds from the order page; history lives here." />
      {res.loading ? <TableSkeleton /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
        : !res.data.items?.length ? <EmptyState title="No refunds" />
        : (
          <DataTable rowKey="id" columns={[
            { key: "id", label: "ID", render: (r) => `#${r.id}` },
            { key: "order_id", label: "Order", render: (r) => (
              <Link to={`/orders/${r.order_id}`} className="text-sky-300">#{r.order_id}</Link>) },
            { key: "amount", label: "Amount", render: (r) => fmtMoney(r.amount) },
            { key: "status", label: "Status", render: (r) => r.status },
            { key: "reason", label: "Reason", render: (r) => r.reason || "—" },
            { key: "created_at", label: "Created", render: (r) => fmtDate(r.created_at) },
          ]} rows={res.data.items} />
        )}
    </div>
  );
}
