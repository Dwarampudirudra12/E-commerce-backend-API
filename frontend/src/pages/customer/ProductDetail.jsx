import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getProduct, logView } from "../../api/productsApi.js";
import { forProduct } from "../../api/recommendationsApi.js";
import { useApi } from "../../hooks/useApi.js";
import { GlassButton, GlassCard, PageHeader } from "../../components/ui/primitives.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { ProductGrid, ProductVisual, QtySelector, stockMeta } from "../../components/commerce/ProductCard.jsx";
import { useCartAdd } from "./Shop.jsx";
import { fmtMoney } from "../../utils/format.js";

function RecRow({ title, hint, productId, kind, onAdd }) {
  const recs = useApi(() => forProduct(productId, kind, 4).catch(() => ({ items: [] })), [productId]);
  const [items, setItems] = useState([]);
  useEffect(() => {
    if (!recs.data?.items?.length) return;
    Promise.all(recs.data.items.map((id) => getProduct(id).catch(() => null))).then(
      (ps) => setItems(ps.filter(Boolean))
    );
  }, [recs.data]);
  if (!items.length) return null;
  return (
    <section className="mt-8" aria-label={title}>
      <h2 className="font-semibold">{title}</h2>
      <p className="text-muted2 mb-3 text-sm">{hint}</p>
      <ProductGrid items={items} onAdd={onAdd} />
    </section>
  );
}

export default function ProductDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [qty, setQty] = useState(1);
  const [add, msg] = useCartAdd();
  const res = useApi(() => getProduct(id), [id]);

  useEffect(() => {
    logView(id).catch(() => {});
    try {
      const rv = JSON.parse(localStorage.getItem("recently_viewed") || "[]");
      localStorage.setItem("recently_viewed", JSON.stringify([Number(id), ...rv.filter((x) => x !== Number(id))].slice(0, 12)));
    } catch { /* ignore */ }
  }, [id]);

  if (res.loading) return <TableSkeleton />;
  if (res.error) return <ErrorState error={res.error} onRetry={res.reload} />;
  const p = res.data;
  if (!p) return <EmptyState title="Product not found" action={<Link to="/products" className="btn-ghost px-4 py-2 text-sm">Back to catalog</Link>} />;
  const s = stockMeta(p);

  return (
    <div>
      <PageHeader title={p.name} subtitle={`${p.sku} · ${fmtMoney(p.price)}`} />
      {msg && <div className="glass mb-4 px-4 py-2 text-sm text-emerald-300" role="status">{msg}</div>}
      <div className="grid gap-5 md:grid-cols-2">
        <GlassCard><ProductVisual product={p} size="lg" /></GlassCard>
        <GlassCard className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-sm">
            <span className="font-semibold" style={{ color: s.color }}>● {s.label}</span>
            <span className="text-faint">{p.on_hand} on hand{p.reserved ? ` · ${p.reserved} reserved` : ""}</span>
          </div>
          <p className="text-muted2 text-sm leading-relaxed">{p.description || "No description yet."}</p>
          <div className="font-display text-3xl font-bold">{fmtMoney(p.price)}</div>
          <div className="flex items-center gap-3">
            <QtySelector value={qty} onChange={setQty} max={Math.min(99, p.on_hand - p.reserved || 1)} />
            <GlassButton onClick={() => add(p, qty)} disabled={(p.on_hand || 0) - (p.reserved || 0) <= 0}>
              Add to cart
            </GlassButton>
            <GlassButton variant="ghost" onClick={async () => { await add(p, qty); nav("/checkout"); }}>
              Buy now
            </GlassButton>
          </div>
          <p className="text-faint text-xs">Stock is reserved atomically at checkout — no overselling.</p>
        </GlassCard>
      </div>
      <RecRow title="Frequently bought together" hint="Customers who purchased this also purchased…" productId={p.id} kind="bought_together" onAdd={(x) => add(x)} />
      <RecRow title="Customers also viewed" hint="Based on shared browsing sessions." productId={p.id} kind="also_viewed" onAdd={(x) => add(x)} />
    </div>
  );
}
