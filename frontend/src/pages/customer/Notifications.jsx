import { useState } from "react";
import { markRead, myNotifications } from "../../api/notificationsApi.js";
import { useApi } from "../../hooks/useApi.js";
import { DataTable, Pagination } from "../../components/ui/DataTable.jsx";
import { EmptyState, ErrorState, Modal, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassCard, GlassSelect, PageHeader } from "../../components/ui/primitives.jsx";
import { PriorityBadge } from "../../components/analytics/widgets.jsx";
import { fmtDate, timeAgo } from "../../utils/format.js";

const TYPES = ["order_confirmed", "payment_failed", "high_risk_order", "low_stock",
  "stockout_risk", "order_shipped", "order_delivered", "refund_processed",
  "account_locked", "webhook_failure", "api_error_spike"];

export default function Notifications() {
  const [type, setType] = useState("");
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState(null);
  const res = useApi(
    () => myNotifications({ page, page_size: 15, ...(unreadOnly ? { unread_only: true } : {}) }),
    [page, unreadOnly]
  );
  const rows = (res.data?.items || []).filter((n) => !type || n.type === type);

  const read = async (n) => {
    setOpen(n);
    if (!n.is_read) {
      await markRead(n.id);
      res.reload();
    }
  };

  return (
    <div>
      <PageHeader title="Notifications" subtitle={res.data ? `${res.data.unread} unread` : ""} />
      <div className="glass mb-4 flex flex-wrap gap-3 p-4">
        <GlassSelect value={type} onChange={(e) => setType(e.target.value)} aria-label="Filter by type">
          <option value="">All types</option>
          {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </GlassSelect>
        <label className="flex items-center gap-2 text-sm text-slate-300">
          <input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} />
          Unread only
        </label>
      </div>
      {res.loading ? <TableSkeleton /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
        : rows.length === 0 ? <EmptyState title="All caught up" hint="Order, payment, stock and risk alerts land here." />
        : (<>
          <DataTable rowKey="id" onRowClick={read} columns={[
            { key: "type", label: "Event", render: (n) => <span className="font-medium">{n.type}</span> },
            { key: "priority", label: "Priority", render: (n) => <PriorityBadge type={n.type} /> },
            { key: "is_read", label: "State", render: (n) => (
              <span className={n.is_read ? "text-faint" : "font-semibold text-white"}>
                {n.is_read ? "Read" : "Unread"}
              </span>) },
            { key: "created_at", label: "When", render: (n) => timeAgo(n.created_at) },
          ]} rows={rows} />
          <Pagination page={page} pageSize={15} total={res.data.total} onPage={setPage} />
        </>)}
      <Modal open={!!open} onClose={() => setOpen(null)} title={open?.type || "Notification"}>
        {open && (
          <div className="space-y-2 text-sm">
            <div className="flex gap-2"><PriorityBadge type={open.type} />
              <span className="text-faint">{fmtDate(open.created_at)}</span></div>
            <GlassCard className="p-3 font-mono text-xs">
              {JSON.stringify(open.payload || {}, null, 2)}
            </GlassCard>
          </div>
        )}
      </Modal>
    </div>
  );
}
