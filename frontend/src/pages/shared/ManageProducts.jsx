import { useState } from "react";
import { createProduct, searchProducts, updateProduct, uploadImage } from "../../api/productsApi.js";
import { listCategories } from "../../api/categoriesApi.js";
import { useApi } from "../../hooks/useApi.js";
import { DataTable, Pagination } from "../../components/ui/DataTable.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { Modal } from "../../components/ui/feedback.jsx";
import { GlassButton, GlassCard, GlassInput, GlassSelect, PageHeader } from "../../components/ui/primitives.jsx";
import { fmtMoney } from "../../utils/format.js";

/** Seller (own) / Admin (all) product management with table/grid toggle. */
export default function ManageProducts({ scope }) {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [view, setView] = useState("table");
  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);
  const res = useApi(() => searchProducts({ q: q || undefined, page, page_size: 12 }), [q, page]);
  const cats = useApi(() => listCategories());

  return (
    <div>
      <PageHeader title={scope === "seller" ? "My products" : "Products"}
        subtitle={scope === "seller" ? "Only your products are visible." : "Full catalog management."}
        actions={[
          <div key="v" className="flex gap-1 rounded-xl border border-white/10 p-1" role="group" aria-label="View">
            {(["table", "grid"]).map((v) => (
              <button key={v} onClick={() => setView(v)}
                className={`rounded-lg px-3 py-1 text-sm ${view === v ? "bg-white/10 font-semibold" : "text-slate-400"}`}>
                {v}
              </button>
            ))}
          </div>,
          <GlassButton key="c" onClick={() => setCreating(true)}>New product</GlassButton>,
        ]} />
      <div className="glass mb-4 p-4">
        <GlassInput placeholder="Search SKU or name…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} aria-label="Search products" />
      </div>
      {res.loading ? <TableSkeleton /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
        : res.data.items.length === 0 ? <EmptyState title="No products" />
        : view === "table" ? (<>
          <DataTable rowKey="id" columns={[
            { key: "sku", label: "SKU", render: (p) => <span className="font-mono text-xs">{p.sku}</span> },
            { key: "name", label: "Name", render: (p) => <span className="font-medium">{p.name}</span> },
            { key: "price", label: "Price", render: (p) => fmtMoney(p.price) },
            { key: "stock", label: "Available", render: (p) => (p.on_hand || 0) - (p.reserved || 0) },
            { key: "active", label: "Active", render: (p) => (p.is_active ? "Yes" : "No") },
            { key: "actions", label: "Actions", render: (p) => (
              <GlassButton variant="ghost" className="px-3 py-1 text-xs" onClick={() => setEditing(p)}>Edit</GlassButton>) },
          ]} rows={res.data.items} />
          <Pagination page={res.data.page} pageSize={res.data.page_size} total={res.data.total} onPage={setPage} />
        </>) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {res.data.items.map((p) => (
              <GlassCard key={p.id} hover className="p-4">
                <div className="font-mono text-xs text-slate-400">{p.sku}</div>
                <div className="font-semibold">{p.name}</div>
                <div className="mt-1 flex items-center justify-between">
                  <span className="font-bold">{fmtMoney(p.price)}</span>
                  <GlassButton variant="ghost" className="px-3 py-1 text-xs" onClick={() => setEditing(p)}>Edit</GlassButton>
                </div>
              </GlassCard>
            ))}
          </div>
        )}
      <ProductForm open={creating || !!editing} initial={editing}
        categories={cats.data || []}
        onClose={() => { setCreating(false); setEditing(null); }}
        onSaved={() => { setCreating(false); setEditing(null); res.reload(); }} />
    </div>
  );
}

function ProductForm({ open, initial, categories, onClose, onSaved }) {
  const [f, setF] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [createdId, setCreatedId] = useState(initial?.id || null);

  const cur = f || {
    sku: initial?.sku || "", name: initial?.name || "", description: initial?.description || "",
    price: initial?.price || "", category_id: initial?.category_id || "", is_active: initial?.is_active ?? true,
  };
  const set = (k) => (e) => setF({
    ...cur,
    [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value,
  });

  const save = async () => {
    setBusy(true);
    setError("");
    try {
      const payload = {
        sku: cur.sku, name: cur.name, description: cur.description,
        price: Number(cur.price), category_id: cur.category_id ? Number(cur.category_id) : null,
        ...(initial ? { is_active: cur.is_active } : {}),
      };
      let id = createdId;
      if (initial) {
        await updateProduct(initial.id, { name: payload.name, description: payload.description, price: payload.price, is_active: payload.is_active });
        id = initial.id;
      } else if (!createdId) {
        const p = await createProduct(payload);
        id = p.id;
        setCreatedId(p.id);
      }
      if (file && id) {
        await uploadImage(id, file, setProgress);
        setFile(null);
        setProgress(0);
      }
      if (initial || !file) onSaved();
      else setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={initial ? "Edit product" : "New product"} wide>
      {error && <p className="mb-3 text-sm text-rose-400" role="alert">{error}</p>}
      <div className="grid gap-3 md:grid-cols-2">
        <GlassInput placeholder="SKU *" value={cur.sku} disabled={!!initial} onChange={set("sku")} aria-label="SKU" />
        <GlassInput placeholder="Name *" value={cur.name} onChange={set("name")} aria-label="Name" />
        <GlassInput placeholder="Price *" value={cur.price} onChange={set("price")} inputMode="decimal" aria-label="Price" />
        <GlassSelect value={cur.category_id || ""} onChange={(e) => setF({ ...cur, category_id: e.target.value })} aria-label="Category">
          <option value="">No category</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </GlassSelect>
        <textarea className="glass-input min-h-[80px] md:col-span-2" placeholder="Description"
          value={cur.description} onChange={set("description")} aria-label="Description" />
        {initial && (
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={cur.is_active} onChange={set("is_active")} /> Active
          </label>
        )}
        <div className="md:col-span-2">
          <label className="text-muted2 mb-1 block text-sm font-medium">Product image (drag & drop or browse)</label>
          <label
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); setFile(e.dataTransfer.files?.[0] || null); }}
            className="flex cursor-pointer flex-col items-center rounded-xl border border-dashed border-white/20 px-4 py-6 text-sm text-slate-300 hover:border-sky-400/60"
          >
            {file ? `${file.name} (${Math.round(file.size / 1024)} KB)` : "Drop an image here, or click to browse"}
            <input type="file" accept="image/*" className="hidden" aria-label="Product image"
              onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>
          {progress > 0 && progress < 100 && (
            <div className="mt-2 h-1.5 rounded-full bg-white/10" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
              <div className="h-full rounded-full bg-sky-400" style={{ width: `${progress}%` }} />
            </div>
          )}
          <p className="text-faint mt-1 text-xs">Stored in S3 when configured, otherwise local uploads.</p>
        </div>
      </div>
      <div className="mt-4 flex gap-2">
        <GlassButton onClick={save} disabled={busy}>{busy ? "Saving…" : initial ? "Save changes" : createdId ? "Upload & finish" : "Create product"}</GlassButton>
        <GlassButton variant="ghost" onClick={onClose}>Cancel</GlassButton>
      </div>
    </Modal>
  );
}
