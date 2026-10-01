import { useState } from "react";
import { listUsers, setRole, unlockUser } from "../../api/usersApi.js";
import { useApi } from "../../hooks/useApi.js";
import { DataTable } from "../../components/ui/DataTable.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { Modal } from "../../components/ui/feedback.jsx";
import { GlassBadge, GlassButton, GlassSelect, PageHeader } from "../../components/ui/primitives.jsx";
import { useAuth } from "../../contexts/AuthContext.jsx";

const ROLE_COLORS = { CUSTOMER: "#38bdf8", SELLER: "#a78bfa", SUPPORT: "#fbbf24", ADMIN: "#f87171" };

export default function Users() {
  const res = useApi(() => listUsers());
  const { user: self } = useAuth();
  const [target, setTarget] = useState(null);
  const [role, setRoleV] = useState("CUSTOMER");
  const [busy, setBusy] = useState(false);

  const confirm = async () => {
    setBusy(true);
    try {
      await setRole(target.id, role);
      setTarget(null);
      res.reload();
    } catch (e) {
      alert(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <PageHeader title="Users & roles" subtitle="Role changes are audited. You cannot change your own role here." />
      {res.loading ? <TableSkeleton /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
        : !res.data.length ? <EmptyState title="No users" />
        : (
          <DataTable rowKey="id" columns={[
            { key: "email", label: "User", render: (u) => (
              <span><span className="font-medium">{u.full_name || "—"}</span>
                <span className="text-faint block text-xs">{u.email}</span></span>) },
            { key: "role", label: "Role", render: (u) => (
              <GlassBadge color={ROLE_COLORS[u.role] || "#94a3b8"}>{u.role}</GlassBadge>) },
            { key: "status", label: "Status", render: (u) => (
              <span className={u.status === "locked" ? "font-semibold text-rose-400" : "text-slate-300"}>{u.status}</span>) },
            { key: "failed", label: "Failed logins", render: (u) => u.failed_logins ?? "—" },
            { key: "actions", label: "Actions", render: (u) => (
              <span className="flex gap-1">
                <button disabled={u.id === self?.id}
                  onClick={() => { setTarget(u); setRoleV(u.role); }}
                  className="btn-ghost px-2 py-1 text-xs disabled:opacity-40">Role</button>
                {u.status === "locked" && (
                  <button onClick={() => unlockUser(u.id).then(() => res.reload())}
                    className="btn-ghost px-2 py-1 text-xs">Unlock</button>)}
              </span>) },
          ]} rows={res.data} />
        )}
      <Modal open={!!target} onClose={() => setTarget(null)} title={`Change role — ${target?.email}`}>
        <p className="text-muted2 mb-3 text-sm">
          Assigning SUPPORT or ADMIN grants access to orders, refunds and system data.
          This action is written to the audit log.
        </p>
        <GlassSelect value={role} onChange={(e) => setRoleV(e.target.value)} aria-label="New role">
          {Object.keys(ROLE_COLORS).map((r) => <option key={r} value={r}>{r}</option>)}
        </GlassSelect>
        <div className="mt-4 flex gap-2">
          <GlassButton onClick={confirm} disabled={busy}>{busy ? "Saving…" : "Confirm change"}</GlassButton>
          <GlassButton variant="ghost" onClick={() => setTarget(null)}>Cancel</GlassButton>
        </div>
      </Modal>
    </div>
  );
}
