import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { listCategories } from "../../api/categoriesApi.js";
import { searchProducts } from "../../api/productsApi.js";
import { useApi } from "../../hooks/useApi.js";
import { useDebounce } from "../../hooks/useApi.js";
import { GlassInput, GlassSelect, PageHeader } from "../../components/ui/primitives.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { Pagination } from "../../components/ui/DataTable.jsx";
import { ProductGrid } from "../../components/commerce/ProductCard.jsx";
import { useCartAdd } from "./Shop.jsx";

export default function Products() {
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") || "");
  const [category, setCategory] = useState(params.get("category") || "");
  const [sort, setSort] = useState("name");
  const [order, setOrder] = useState("asc");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [page, setPage] = useState(1);
  const dq = useDebounce(q);
  const [wishlist, setWishlist] = useState(() => new Set(JSON.parse(localStorage.getItem("wishlist") || "[]")));
  const [add, msg] = useCartAdd();
  const cats = useApi(() => listCategories());

  const query = {
    q: dq || undefined,
    category_id: category || undefined,
    min_price: minPrice || undefined,
    max_price: maxPrice || undefined,
    sort, order, page, page_size: 12,
  };
  const res = useApi(() => searchProducts(query),
    [dq, category, sort, order, minPrice, maxPrice, page]);

  useEffect(() => { setPage(1); }, [dq, category, sort, order, minPrice, maxPrice]);
  useEffect(() => {
    const next = {};
    if (q) next.q = q;
    if (category) next.category = category;
    setParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, category]);

  const toggleWish = (p) => setWishlist((prev) => {
    const n = new Set(prev);
    if (n.has(p.id)) n.delete(p.id);
    else n.add(p.id);
    localStorage.setItem("wishlist", JSON.stringify([...n]));
    return n;
  });

  return (
    <div>
      <PageHeader title="Catalog" subtitle="Search, filter and sort the live catalog." />
      {msg && <div className="glass mb-4 px-4 py-2 text-sm text-emerald-300" role="status">{msg}</div>}
      <div className="glass mb-4 grid gap-3 p-4 md:grid-cols-6">
        <GlassInput className="md:col-span-2" placeholder="Search products…" value={q}
          onChange={(e) => setQ(e.target.value)} aria-label="Search products" />
        <GlassSelect value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Category filter">
          <option value="">All categories</option>
          {(cats.data || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </GlassSelect>
        <GlassInput placeholder="Min $" value={minPrice} onChange={(e) => setMinPrice(e.target.value)} inputMode="decimal" aria-label="Minimum price" />
        <GlassInput placeholder="Max $" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} inputMode="decimal" aria-label="Maximum price" />
        <div className="flex gap-2">
          <GlassSelect value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort by">
            <option value="name">Name</option><option value="price">Price</option>
          </GlassSelect>
          <GlassSelect value={order} onChange={(e) => setOrder(e.target.value)} aria-label="Sort order">
            <option value="asc">Asc</option><option value="desc">Desc</option>
          </GlassSelect>
        </div>
      </div>
      {res.loading ? <TableSkeleton /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
        : res.data.items.length === 0 ? (
          <EmptyState title="No products found" hint="Try a different search or clear the filters."
            action={<button className="btn-ghost px-4 py-2 text-sm" onClick={() => { setQ(""); setCategory(""); setMinPrice(""); setMaxPrice(""); }}>Clear filters</button>} />
        ) : (<>
          <ProductGrid items={res.data.items} onAdd={(p) => add(p)} wishlist={wishlist} onWish={toggleWish} />
          <Pagination page={res.data.page} pageSize={res.data.page_size} total={res.data.total} onPage={setPage} />
        </>)}
    </div>
  );
}
