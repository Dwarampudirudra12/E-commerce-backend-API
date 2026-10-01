import { motion } from "framer-motion";
import { Heart, Package, Plus, Star } from "lucide-react";
import { Link } from "react-router-dom";
import { fmtMoney } from "../../utils/format.js";
import { GlassBadge, GlassButton, GlassCard } from "../ui/primitives.jsx";

export function stockMeta(p) {
  const avail = (p.on_hand || 0) - (p.reserved || 0);
  if (avail <= 0) return { label: "Out of stock", color: "#f87171" };
  if (avail <= 5) return { label: `Only ${avail} left`, color: "#fbbf24" };
  return { label: "In stock", color: "#34d399" };
}

export function ProductVisual({ product, size = "md" }) {
  const h = size === "lg" ? "h-64" : "h-40";
  return (
    <div className={`${h} relative flex items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-sky-500/15 via-white/[0.03] to-violet-500/15`}>
      <Package size={size === "lg" ? 64 : 40} className="text-slate-500" aria-hidden />
      <span className="absolute bottom-2 right-2 rounded-md bg-black/50 px-1.5 py-0.5 font-mono text-[10px] text-slate-300">
        {product.sku}
      </span>
    </div>
  );
}

export function ProductCard({ product, onAdd, wished, onWish, badge }) {
  const s = stockMeta(product);
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
      <GlassCard hover className="flex h-full flex-col gap-3 p-4">
        <Link to={`/products/${product.id}`} aria-label={`View ${product.name}`}>
          <ProductVisual product={product} />
        </Link>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <Link to={`/products/${product.id}`} className="truncate font-semibold hover:text-sky-300">
              {product.name}
            </Link>
            <div className="text-faint text-xs">{product.sku}</div>
          </div>
          <button onClick={() => onWish?.(product)} aria-label="Toggle wishlist" aria-pressed={!!wished}
            className="rounded-lg p-1.5 text-slate-400 hover:text-rose-400">
            <Heart size={16} fill={wished ? "currentColor" : "none"} />
          </button>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <GlassBadge color={s.color}>{s.label}</GlassBadge>
          {badge && <GlassBadge color="#a78bfa"><Star size={11} /> {badge}</GlassBadge>}
        </div>
        <div className="mt-auto flex items-center justify-between">
          <span className="font-display text-lg font-bold">{fmtMoney(product.price)}</span>
          <GlassButton onClick={() => onAdd?.(product)} disabled={(product.on_hand || 0) - (product.reserved || 0) <= 0}
            className="flex items-center gap-1 px-3" aria-label={`Add ${product.name} to cart`}>
            <Plus size={15} /> Add
          </GlassButton>
        </div>
      </GlassCard>
    </motion.div>
  );
}

export function ProductGrid({ items, onAdd, wishlist, onWish, badges }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {items.map((p) => (
        <ProductCard key={p.id} product={p} onAdd={onAdd}
          wished={wishlist?.has(p.id)} onWish={onWish} badge={badges?.[p.id]} />
      ))}
    </div>
  );
}

export function QtySelector({ value, onChange, min = 1, max = 99 }) {
  return (
    <div className="inline-flex items-center gap-2" role="group" aria-label="Quantity">
      <button className="btn-ghost px-2.5 py-1" disabled={value <= min}
        onClick={() => onChange(value - 1)} aria-label="Decrease quantity">−</button>
      <span className="w-8 text-center font-semibold" aria-live="polite">{value}</span>
      <button className="btn-ghost px-2.5 py-1" disabled={value >= max}
        onClick={() => onChange(value + 1)} aria-label="Increase quantity">+</button>
    </div>
  );
}
