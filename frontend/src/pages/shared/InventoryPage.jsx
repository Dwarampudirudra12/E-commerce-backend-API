import { useState } from "react";
import { getInventory, updateInventory } from "../../api/inventoryApi.js";
import { searchProducts } from "../../api/productsApi.js";
import { useApi } from "../../hooks/useApi.js";
import { DataTable } from "../../components/ui/DataTable.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { Modal } from "../../components/ui/feedback.jsx";
import { GlassBadge, GlassButton, GlassCard, GlassInput, PageHeader } from "../../components/ui/primitives.jsx";

export function stockState(inv) {
  const avail = (inv.on_hand || 0) - (inv.reserved || 0);
  if (avail <= 0) return { label: "Out of stock", color: "#f87171" };
  if (avail <= (inv.reorder_level || 0)) return { label: "Critical", color: "#fb7185" };
  if (avail <= (inv.reorder_level || 0) * 2) return { label: "Low stock", color: "#fbbf24" };
  return { label: "Healthy", color: "#34d399" };
}

/** Seller (own) / Admin (all) inventory console. */
export default function InventoryPage({ scope }) {
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState("");
  const [editing, setEditing] = useState(null);
  const res = useApi(() => searchProducts({ q: q || undefined, page: 1, page_size: 50 }).then(async (d) => {
    const rows = [];
    for (const p of d.items) {
      try {
        const inv = await getInventory(p.id);
        rows.push({ ...p, inv: inv[0] });
      } catch { /* not visible to this role */ }
    }
    return rows;
  }), [q]);

  const rows = (res.data || []).filter((r) => {
    if (!filter || !r.inv) return true;
    return stockState(r.inv).label === filter;
  });

  return (
    <div>
      <PageHeader title={scope === "seller" ? "My inventory" : "Inventory"}
        subtitle="Optimistic locking — stale edits are rejected with 409." />
      <div className="glass mb-4 flex flex-wrap gap-3 p-4">
        <GlassInput placeholder="Search SKU or name…" value={q} className="max-w-xs"
          onChange={(e) => setQ(e.target.value)} aria-label="Search inventory" />
        {["", "Healthy", "Low stock", "Critical", "Out of stock"].map((s) => (
          <button key={s} onClick={() => setFilter(s)}
            className={`rounded-lg px-3 py-1.5 text-sm ${filter === s ? "bg-white/10 font-semibold" : "text-slate-400"}`}>
            {s || "All"}
          </button>
        ))}
      </div>
      {res.loading ? <TableSkeleton /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
        : rows.length === 0 ? <EmptyState title="No inventory rows" hint="Create products to track stock." />
        : (
          <DataTable rowKey="id" columns={[
            { key: "sku", label: "SKU", render: (r) => <span className="font-mono text-xs">{r.sku}</span> },
            { key: "name", label: "Product", render: (r) => <span className="font-medium">{r.name}</span> },
            { key: "on_hand", label: "On hand", render: (r) => r.inv?.on_hand ?? "—" },
            { key: "reserved", label: "Reserved", render: (r) => r.inv?.reserved ?? "—" },
            { key: "available", label: "Available", render: (r) => r.inv ? r.inv.on_hand - r.inv.reserved : "—" },
            { key: "reorder", label: "Reorder at", render: (r) => r.inv?.reorder_level ?? "—" },
            { key: "state", label: "State", render: (r) => r.inv ? (() => {
              const s = stockState(r.inv);
              return <GlassBadge color={s.color}>{s.label}</GlassBadge>;
            })() : "—" },
            { key: "actions", label: "Actions", render: (r) => r.inv && (
              <GlassButton variant="ghost" className="px-3 py-1 text-xs" onClick={() => setEditing(r)}>Adjust</GlassButton>) },
          ]} rows={rows} />
        )}
      <AdjustModal row={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); res.reload(); }} />
    </div>
  );
}

function AdjustModal({ row, onClose, onSaved }) {
  const [onHand, setOnHand] = useState("");
  const [reorder, setReorder] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  if (!row) return <Modal open={false} onClose={onClose} title="" children={null} />;
  const save = async () => {
    setBusy(true);
    setError("");
    try {
      await updateInventory(row.id, {
        ...(onHand !== "" ? { on_hand: Number(onHand) } : {}),
        ...(reorder !== "" ? { reorder_level: Number(reorder) } : {}),
        version: row.inv.version,
      });
      onSaved();
    } catch (e) {
      setError(e.status === 409 ? "Stale version — someone else updated stock. Reload and retry." : e.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal open onClose={onClose} title={`Adjust stock — ${row.sku}`}>
      {error && <p className="mb-3 text-sm text-rose-400" role="alert">{error}</p>}
      <GlassCard className="mb-3 p-3 text-sm">
        On hand {row.inv.on_hand} · Reserved {row.inv.reserved} · Version {row.inv.version}
      </GlassCard>
      <div className="grid grid-cols-2 gap-3">
        <GlassInput placeholder={`On hand (${row.inv.on_hand})`} value={onHand}
          onChange={(e) => setOnHand(e.target.value)} inputMode="numeric" aria-label="On hand quantity" />
        <GlassInput placeholder={`Reorder level (${row.inv.reorder_level})`} value={reorder}
          onChange={(e) => setReorder(e.target.value)} inputMode="numeric" aria-label="Reorder level" />
      </div>
      <p className="text-faint mt-2 text-xs">Setting on-hand below reserved stock is rejected (422).</p>
      <div className="mt-4 flex gap-2">
        <GlassButton onClick={save} disabled={busy}>{busy ? "Saving…" : "Save"}</GlassButton>
        <GlassButton variant="ghost" onClick={onClose}>Cancel</GlassButton>
      </div>
    </Modal>
  );
}
