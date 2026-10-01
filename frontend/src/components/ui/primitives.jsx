import { cx } from "../../utils/format.js";

export function GlassCard({ className, hover = false, children, ...rest }) {
  return (
    <div className={cx("glass p-5", hover && "glass-hover", className)} {...rest}>
      {children}
    </div>
  );
}

export function GlassButton({ variant = "primary", className, ...rest }) {
  return (
    <button
      className={cx(
        "px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed",
        variant === "primary" ? "btn-primary" : "btn-ghost",
        className
      )}
      {...rest}
    />
  );
}

export function GlassInput({ className, ...rest }) {
  return <input className={cx("glass-input w-full px-3 py-2 text-sm", className)} {...rest} />;
}

export function GlassSelect({ className, children, ...rest }) {
  return (
    <select className={cx("glass-input w-full px-3 py-2 text-sm", className)} {...rest}>
      {children}
    </select>
  );
}

export function GlassBadge({ color = "#94a3b8", children, className }) {
  return (
    <span
      className={cx("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium", className)}
      style={{ color, background: `${color}1f`, border: `1px solid ${color}55` }}
    >
      {children}
    </span>
  );
}

export function GlassTabs({ tabs, value, onChange }) {
  return (
    <div className="flex gap-1 rounded-xl border border-white/10 bg-white/[0.03] p-1" role="tablist">
      {tabs.map((t) => (
        <button
          key={t.value}
          role="tab"
          aria-selected={value === t.value}
          onClick={() => onChange(t.value)}
          className={cx(
            "rounded-lg px-3 py-1.5 text-sm transition",
            value === t.value
              ? "bg-white/10 font-semibold text-white"
              : "text-slate-400 hover:text-white"
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight md:text-3xl">{title}</h1>
        {subtitle && <p className="text-muted2 mt-1 text-sm">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}
