import { useState } from "react";
import { listAuditLogs } from "../../api/auditApi.js";
import { useApi } from "../../hooks/useApi.js";
import { DataTable, Pagination } from "../../components/ui/DataTable.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassInput, PageHeader } from "../../components/ui/primitives.jsx";
import { fmtDate } from "../../utils/format.js";

export default function AuditLogs() {
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);
  const res = useApi(() => listAuditLogs({ page, page_size: 20, ...(action ? { action } : {}) }),
    [page]);

  const search = (e) => {
    e.preventDefault();
    setPage(1);
    res.reload();
  };

  return (
    <div>
      <PageHeader title="Audit logs" subtitle="Append-only trail of security-relevant actions." />
      <form onSubmit={search} className="glass mb-4 flex max-w-md gap-2 p-4">
        <GlassInput placeholder="Filter by action, e.g. user.login" value={action}
          onChange={(e) => setAction(e.target.value)} aria-label="Filter by action" />
        <button className="btn-primary shrink-0 px-4 text-sm" type="submit">Filter</button>
      </form>
      {res.loading ? <TableSkeleton /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
        : !res.data.items.length ? <EmptyState title="No audit records" />
        : (<>
          <DataTable rowKey="id" columns={[
            { key: "created_at", label: "Timestamp", render: (a) => <span className="whitespace-nowrap">{fmtDate(a.created_at)}</span> },
            { key: "user_id", label: "User", render: (a) => a.user_id ? `#${a.user_id}` : <span className="text-faint">system</span> },
            { key: "action", label: "Action", render: (a) => <span className="font-mono text-xs">{a.action}</span> },
            { key: "entity", label: "Entity", render: (a) => `${a.entity_type || "—"}${a.entity_id ? ` #${a.entity_id}` : ""}` },
            { key: "ip", label: "IP", render: (a) => a.ip_address || "—" },
          ]} rows={res.data.items} />
          <Pagination page={res.data.page} pageSize={res.data.page_size} total={res.data.total} onPage={setPage} />
        </>)}
    </div>
  );
}
