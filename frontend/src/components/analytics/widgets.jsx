import { riskMeta } from "../../constants/roles.js";
import { fmtMoney, timeAgo } from "../../utils/format.js";
import { GlassBadge, GlassCard } from "../ui/primitives.jsx";
import { Sparkline } from "../charts/charts.jsx";

export function KPICard({ label, value, delta, spark, money = false }) {
  return (
    <GlassCard className="min-w-[150px] flex-1">
      <div className="text-muted2 text-xs font-medium uppercase tracking-wide">{label}</div>
      <div className="font-display mt-1 text-2xl font-bold">
        {money ? fmtMoney(value) : value ?? "—"}
      </div>
      <div className="mt-1 flex items-end justify-between gap-2">
        {delta != null ? (
          <span className={`text-xs font-semibold ${delta >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            {delta >= 0 ? "▲" : "▼"} {Math.abs(delta)}%
          </span>
        ) : <span />}
        {spark && <Sparkline values={spark} />}
      </div>
    </GlassCard>
  );
}

export function RiskGauge({ score, size = 120 }) {
  const m = riskMeta(score);
  const pct = Math.round((score || 0) * 100);
  const r = 44;
  const circ = 2 * Math.PI * r;
  return (
    <div className="flex flex-col items-center" role="img" aria-label={`Risk score ${score}, ${m.label}`}>
      <svg width={size} height={size} viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
        <circle cx="60" cy="60" r={r} fill="none" stroke={m.color} strokeWidth="10"
          strokeLinecap="round" strokeDasharray={circ}
          strokeDashoffset={circ - (circ * pct) / 100}
          transform="rotate(-90 60 60)"
          style={{ filter: `drop-shadow(0 0 6px ${m.color})` }} />
        <text x="60" y="58" textAnchor="middle" fill="#f1f5f9" fontSize="20" fontWeight="700">
          {score?.toFixed(2) ?? "—"}
        </text>
        <text x="60" y="76" textAnchor="middle" fill={m.color} fontSize="10" fontWeight="600">
          {m.label.toUpperCase()}
        </text>
      </svg>
    </div>
  );
}

export function FactorBar({ factor, strength }) {
  const w = Math.round(Math.min(1, Math.max(0, strength || 0.5)) * 100);
  return (
    <div className="mb-2">
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-slate-300">{factor}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-white/10" role="progressbar"
        aria-valuenow={w} aria-valuemin={0} aria-valuemax={100} aria-label={factor}>
        <div className="h-full rounded-full bg-gradient-to-r from-amber-400 to-rose-400" style={{ width: `${w}%` }} />
      </div>
    </div>
  );
}

export function ActivityFeed({ items }) {
  if (!items?.length) return <p className="text-muted2 text-sm">No recent activity.</p>;
  return (
    <ul className="space-y-2.5">
      {items.map((a, i) => (
        <li key={a.id || i} className="flex gap-2.5 text-sm">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-400" aria-hidden />
          <div className="min-w-0">
            <div className="text-slate-200">{a.text}</div>
            <div className="text-faint text-xs">{a.time ? timeAgo(a.time) : ""} {a.sub || ""}</div>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function PriorityBadge({ type }) {
  const map = {
    api_error_spike: "#f87171", payment_failed: "#f87171", high_risk_order: "#f87171",
    webhook_failure: "#f87171", account_locked: "#f87171",
    low_stock: "#fbbf24", stockout_risk: "#fbbf24",
  };
  const color = map[type] || "#38bdf8";
  const pri = map[type] === "#f87171" ? "High" : map[type] ? "Medium" : "Normal";
  return <GlassBadge color={color}>{pri}</GlassBadge>;
}
