import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listCategories } from "../../api/categoriesApi.js";
import { forMe } from "../../api/recommendationsApi.js";
import { getProduct, searchProducts } from "../../api/productsApi.js";
import { addItem } from "../../api/cartApi.js";
import { useAuth } from "../../contexts/AuthContext.jsx";
import { useApi } from "../../hooks/useApi.js";
import { GlassButton, GlassCard, PageHeader } from "../../components/ui/primitives.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { ProductGrid } from "../../components/commerce/ProductCard.jsx";

function useWishlist() {
  const [ids, setIds] = useState(() => new Set(JSON.parse(localStorage.getItem("wishlist") || "[]")));
  const toggle = (p) => setIds((prev) => {
    const n = new Set(prev);
    if (n.has(p.id)) n.delete(p.id);
    else n.add(p.id);
    localStorage.setItem("wishlist", JSON.stringify([...n]));
    return n;
  });
  return [ids, toggle];
}

export function useCartAdd() {
  const { isAuthed } = useAuth();
  const [msg, setMsg] = useState("");
  const add = async (product, qty = 1) => {
    if (!isAuthed) {
      setMsg("Sign in to add items to your cart.");
      return;
    }
    await addItem({ product_id: product.id, quantity: qty });
    try {
      const rv = JSON.parse(localStorage.getItem("recently_viewed") || "[]");
      localStorage.setItem("recently_viewed", JSON.stringify([product.id, ...rv.filter((x) => x !== product.id)].slice(0, 12)));
    } catch { /* ignore */ }
    setMsg(`${product.name} added to cart.`);
    setTimeout(() => setMsg(""), 2500);
  };
  return [add, msg];
}

export default function Shop() {
  const [wishlist, toggleWish] = useWishlist();
  const [add, msg] = useCartAdd();
  const feat = useApi(() => searchProducts({ q: "", page: 1, page_size: 8 }));
  const cats = useApi(() => listCategories());
  const recs = useApi(() => forMe(8).catch(() => ({ items: [] })));
  const [recProducts, setRecProducts] = useState([]);

  useEffect(() => {
    if (!recs.data?.items?.length) return;
    Promise.all(recs.data.items.slice(0, 8).map((id) => getProduct(id).catch(() => null))).then(
      (ps) => setRecProducts(ps.filter(Boolean))
    );
  }, [recs.data]);

  return (
    <div>
      <PageHeader title="Smarter shopping. Faster decisions."
        subtitle="Discover products powered by intelligent recommendations." />
      {msg && <div className="glass mb-4 px-4 py-2 text-sm text-emerald-300" role="status">{msg}</div>}

      <GlassCard className="mb-6 bg-gradient-to-r from-sky-500/10 to-violet-500/10 p-6">
        <h2 className="font-display text-xl font-bold">Featured this week</h2>
        <p className="text-muted2 text-sm">Top movers across the catalog.</p>
        <Link to="/products" className="btn-primary mt-3 inline-block px-4 py-2 text-sm">Browse all products</Link>
      </GlassCard>

      <section aria-label="Featured products" className="mb-8">
        <h2 className="mb-3 font-semibold">Featured products</h2>
        {feat.loading ? <TableSkeleton /> : feat.error ? <ErrorState error={feat.error} onRetry={feat.reload} />
          : feat.data.items.length === 0 ? <EmptyState title="No products yet" hint="Check back soon." />
          : <ProductGrid items={feat.data.items} onAdd={(p) => add(p)} wishlist={wishlist} onWish={toggleWish} />}
      </section>

      {recProducts.length > 0 && (
        <section aria-label="Recommended for you" className="mb-8">
          <div className="mb-3 flex items-baseline justify-between">
            <h2 className="font-semibold">Recommended for you</h2>
            <Link to="/recommendations" className="text-sm text-sky-300">View all</Link>
          </div>
          <ProductGrid items={recProducts} onAdd={(p) => add(p)} wishlist={wishlist} onWish={toggleWish}
            badges={Object.fromEntries(recProducts.map((p) => [p.id, "For you"]))} />
        </section>
      )}

      <section aria-label="Trending categories">
        <h2 className="mb-3 font-semibold">Trending categories</h2>
        <div className="flex flex-wrap gap-2">
          {(cats.data || []).map((c) => (
            <Link key={c.id} to={`/products?category=${c.id}`}
              className="btn-ghost px-4 py-2 text-sm">{c.name}</Link>
          ))}
          {!cats.data?.length && !cats.loading && (
            <span className="text-muted2 text-sm">No categories yet.</span>
          )}
        </div>
      </section>
    </div>
  );
}
