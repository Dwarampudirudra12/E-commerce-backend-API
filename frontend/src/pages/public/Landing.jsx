import { Link } from "react-router-dom";
import {
  ArrowRight, BarChart3, Cpu, FileText, Lock, ShieldAlert,
  ShoppingBag, TrendingUp, Zap,
} from "lucide-react";
import { motion } from "framer-motion";
import { LineChart, DonutChart } from "../../components/charts/charts.jsx";
import { GlassBadge, GlassButton, GlassCard } from "../../components/ui/primitives.jsx";
import { RiskGauge } from "../../components/analytics/widgets.jsx";

const FEATURES = [
  { icon: Lock, title: "Secure commerce", text: "JWT auth, RBAC for four roles, idempotent checkout, atomic inventory — overselling and double-charges engineered out." },
  { icon: ShieldAlert, title: "Fraud intelligence", text: "Every order scored in real time with plain-language risk factors and a manual review queue." },
  { icon: TrendingUp, title: "Demand forecasting", text: "14-day per-product forecasts with reorder quantities and stock-out dates." },
  { icon: BarChart3, title: "Enterprise analytics", text: "Revenue, conversion, fraud distribution and operational latency — auto-refreshed, exportable." },
  { icon: Zap, title: "Real-time operations", text: "Order lifecycle events, low-stock and error-spike alerts delivered to inbox, email and dashboard." },
  { icon: Cpu, title: "Cloud-native core", text: "FastAPI, Postgres, Redis, Celery, Prometheus and Grafana behind a versioned, documented API." },
];

export default function Landing() {
  return (
    <div className="min-h-full">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-4 py-5 md:px-6">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-violet-600 font-display text-sm font-bold">E</span>
          <div>
            <div className="font-display text-sm font-bold tracking-wide">ECOMMERCE AI</div>
            <div className="text-faint text-[11px]">Intelligence Platform</div>
          </div>
        </div>
        <nav className="flex items-center gap-2" aria-label="Public">
          <Link to="/shop" className="btn-ghost px-4 py-2 text-sm">Shop</Link>
          <Link to="/login" className="btn-ghost px-4 py-2 text-sm">Sign in</Link>
          <Link to="/register" className="btn-primary px-4 py-2 text-sm">Get started</Link>
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-4 pb-20 md:px-6">
        <section className="grid items-center gap-10 py-10 md:grid-cols-2 md:py-16">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
            <GlassBadge color="#38bdf8">Secure · Intelligent · Observable</GlassBadge>
            <h1 className="font-display mt-4 text-4xl font-bold leading-tight tracking-tight md:text-5xl">
              E-Commerce Intelligence,
              <br />Built for Modern Retail.
            </h1>
            <p className="text-muted2 mt-4 max-w-lg">
              Secure commerce infrastructure with real-time fraud intelligence,
              demand forecasting, inventory optimization and analytics.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/register" className="btn-primary flex items-center gap-2 px-5 py-2.5 text-sm">
                Explore Platform <ArrowRight size={15} />
              </Link>
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
                className="btn-ghost flex items-center gap-2 px-5 py-2.5 text-sm">
                <FileText size={15} /> API Documentation
              </a>
            </div>
            <div className="text-faint mt-6 flex gap-5 text-xs">
              <span>4 roles · RBAC enforced</span><span>Idempotent checkout</span><span>44 API endpoints</span>
            </div>
          </motion.div>

          {/* product-preview dashboard mock (illustrative) */}
          <motion.div
            initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
            className="glass relative p-5" aria-label="Platform preview"
          >
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-semibold">Operations overview</span>
              <GlassBadge color="#34d399">● Live</GlassBadge>
            </div>
            <LineChart
              height={150}
              labels={["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
              series={[{ label: "Revenue", data: [42, 58, 51, 74, 69, 92, 88], borderColor: "#38bdf8", tension: 0.4, fill: true, backgroundColor: "rgba(56,189,248,0.12)", pointRadius: 0 }]}
            />
            <div className="mt-3 grid grid-cols-3 gap-3">
              <GlassCard className="p-3 text-center">
                <div className="text-faint text-[11px]">Revenue</div>
                <div className="font-display text-lg font-bold">$128k</div>
              </GlassCard>
              <GlassCard className="flex items-center justify-center p-2">
                <RiskGauge score={0.07} size={92} />
              </GlassCard>
              <GlassCard className="p-3 text-center">
                <div className="text-faint text-[11px]">Forecast</div>
                <div className="font-display text-lg font-bold text-violet-300">+12%</div>
              </GlassCard>
            </div>
            <div className="mt-3">
              <DonutChart labels={["Paid", "Pending", "Review"]} values={[72, 18, 10]}
                colors={["#34d399", "#fbbf24", "#f87171"]} height={120} />
            </div>
          </motion.div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Features">
          {FEATURES.map((f) => (
            <GlassCard key={f.title} hover className="p-5">
              <f.icon size={22} className="mb-3 text-sky-300" aria-hidden />
              <h3 className="font-semibold">{f.title}</h3>
              <p className="text-muted2 mt-1.5 text-sm leading-relaxed">{f.text}</p>
            </GlassCard>
          ))}
        </section>

        <section className="glass mt-10 flex flex-col items-center p-10 text-center">
          <ShoppingBag size={28} className="mb-3 text-violet-300" aria-hidden />
          <h2 className="font-display text-2xl font-bold">Start with the storefront.</h2>
          <p className="text-muted2 mt-2 max-w-md text-sm">
            Browse the live catalog, check out securely, and watch fraud scoring,
            inventory and notifications react in real time.
          </p>
          <div className="mt-5 flex gap-3">
            <Link to="/shop" className="btn-primary px-5 py-2.5 text-sm">Open the shop</Link>
            <Link to="/login" className="btn-ghost px-5 py-2.5 text-sm">Sign in</Link>
          </div>
        </section>
      </main>
    </div>
  );
}
