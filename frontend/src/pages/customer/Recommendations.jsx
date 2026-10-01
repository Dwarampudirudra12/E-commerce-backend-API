import { useEffect, useState } from "react";
import { getProduct } from "../../api/productsApi.js";
import { forMe } from "../../api/recommendationsApi.js";
import { useApi } from "../../hooks/useApi.js";
import { PageHeader } from "../../components/ui/primitives.jsx";
import { EmptyState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { ProductGrid } from "../../components/commerce/ProductCard.jsx";
import { useCartAdd } from "./Shop.jsx";

function RecSection({ title, hint, ids, onAdd }) {
  const [items, setItems] = useState(null);
  useEffect(() => {
    if (!ids) return;
    Promise.all(ids.slice(0, 8).map((id) => getProduct(id).catch(() => null))).then(
      (ps) => setItems(ps.filter(Boolean))
    );
  }, [ids]);
  if (!ids) return null;
  return (
    <section className="mb-8" aria-label={title}>
      <h2 className="font-semibold">{title}</h2>
      <p className="text-muted2 mb-3 text-sm">{hint}</p>
      {items === null ? <TableSkeleton />
        : items.length === 0 ? <p className="text-muted2 text-sm">Nothing here yet.</p>
        : <ProductGrid items={items} onAdd={onAdd} />}
    </section>
  );
}

export default function Recommendations() {
  const [add, msg] = useCartAdd();
  const recs = useApi(() => forMe(12).catch(() => ({ items: [] })));
  const [recent, setRecent] = useState([]);
  useEffect(() => {
    const ids = JSON.parse(localStorage.getItem("recently_viewed") || "[]").slice(0, 4);
    Promise.all(ids.map((id) => getProduct(id).catch(() => null))).then(
      (ps) => setRecent(ps.filter(Boolean))
    );
  }, []);

  return (
    <div>
      <PageHeader title="Recommended for you" subtitle="Ranked by what customers buy and view together." />
      {msg && <div className="glass mb-4 px-4 py-2 text-sm text-emerald-300" role="status">{msg}</div>}
      {recs.loading ? <TableSkeleton />
        : !recs.data?.items?.length ? (
          <EmptyState title="No recommendations yet"
            hint="Buy or view a few products and personal picks will appear here." />
        ) : (
          <RecSection title="Picked for you" hint="Based on your purchase history." ids={recs.data.items} onAdd={add} />
        )}
      {recent.length > 0 && (
        <section aria-label="Recently viewed">
          <h2 className="font-semibold">Recently viewed</h2>
          <p className="text-muted2 mb-3 text-sm">Picked up where you left off.</p>
          <ProductGrid items={recent} onAdd={add} />
        </section>
      )}
    </div>
  );
}
