import { Link } from "react-router-dom";
import { ShoppingCart, Trash2 } from "lucide-react";
import { getCart, removeItem, updateItem } from "../../api/cartApi.js";
import { getProduct } from "../../api/productsApi.js";
import { useApi } from "../../hooks/useApi.js";
import { GlassButton, GlassCard, PageHeader } from "../../components/ui/primitives.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { QtySelector } from "../../components/commerce/ProductCard.jsx";
import { fmtMoney } from "../../utils/format.js";

export function useCartTotals(items) {
  const subtotal = (items || []).reduce((s, i) => s + Number(i.unit_price) * i.quantity, 0);
  const tax = Math.round(subtotal * 0.08 * 100) / 100;
  const shipping = subtotal === 0 || subtotal >= 50 ? 0 : 4;
  return { subtotal, tax, shipping, total: Math.round((subtotal + tax + shipping) * 100) / 100 };
}

export default function Cart() {
  const cart = useApi(() => getCart().then(async (items) => {
    const names = {};
    await Promise.all(items.map(async (i) => {
      try {
        names[i.product_id] = (await getProduct(i.product_id)).name;
      } catch { names[i.product_id] = `Product #${i.product_id}`; }
    }));
    return items.map((i) => ({ ...i, name: names[i.product_id] }));
  }));
  const t = useCartTotals(cart.data);

  const change = async (id, qty) => {
    await updateItem(id, qty);
    cart.reload();
  };
  const remove = async (id) => {
    await removeItem(id);
    cart.reload();
  };

  return (
    <div>
      <PageHeader title="Your cart" subtitle="Persistent across sessions." />
      {cart.loading ? <TableSkeleton /> : cart.error ? <ErrorState error={cart.error} onRetry={cart.reload} />
        : !cart.data.length ? (
          <EmptyState icon={ShoppingCart} title="Your cart is empty"
            hint="Discover something you will love."
            action={<Link to="/shop" className="btn-primary px-4 py-2 text-sm">Start shopping</Link>} />
        ) : (
          <div className="grid gap-5 lg:grid-cols-3">
            <div className="space-y-3 lg:col-span-2">
              {cart.data.map((i) => (
                <GlassCard key={i.id} className="flex items-center gap-3 p-4">
                  <div className="min-w-0 flex-1">
                    <Link to={`/products/${i.product_id}`} className="font-semibold hover:text-sky-300">{i.name}</Link>
                    <div className="text-faint text-xs">{fmtMoney(i.unit_price)} each</div>
                  </div>
                  <QtySelector value={i.quantity} onChange={(q) => change(i.id, q)} />
                  <div className="w-20 text-right font-semibold">{fmtMoney(Number(i.unit_price) * i.quantity)}</div>
                  <button onClick={() => remove(i.id)} aria-label={`Remove ${i.name}`}
                    className="rounded-lg p-2 text-slate-400 hover:text-rose-400">
                    <Trash2 size={16} />
                  </button>
                </GlassCard>
              ))}
            </div>
            <GlassCard className="h-fit p-5 lg:sticky lg:top-4">
              <h2 className="mb-3 font-semibold">Summary</h2>
              <dl className="space-y-1.5 text-sm">
                <div className="flex justify-between"><dt className="text-muted2">Subtotal</dt><dd>{fmtMoney(t.subtotal)}</dd></div>
                <div className="flex justify-between"><dt className="text-muted2">Tax (8% est.)</dt><dd>{fmtMoney(t.tax)}</dd></div>
                <div className="flex justify-between"><dt className="text-muted2">Shipping (est.)</dt><dd>{t.shipping === 0 ? "Free" : fmtMoney(t.shipping)}</dd></div>
                <div className="flex justify-between border-t border-white/10 pt-2 text-base font-bold">
                  <dt>Total</dt><dd>{fmtMoney(t.total)}</dd>
                </div>
              </dl>
              <p className="text-faint mt-2 text-xs">Estimates — exact totals are calculated at checkout.</p>
              <Link to="/checkout" className="btn-primary mt-4 block py-2.5 text-center text-sm">
                Proceed to Secure Checkout
              </Link>
            </GlassCard>
          </div>
        )}
    </div>
  );
}
