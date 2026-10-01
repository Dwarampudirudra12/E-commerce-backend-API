import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, Inbox, WifiOff } from "lucide-react";
import { GlassButton, GlassCard } from "./primitives.jsx";

export function Skeleton({ className = "h-4" }) {
  return <div className={`animate-pulse rounded-lg bg-white/10 ${className}`} aria-hidden />;
}

export function ChartSkeleton() {
  return (
    <GlassCard>
      <Skeleton className="mb-3 h-5 w-40" />
      <Skeleton className="h-56" />
    </GlassCard>
  );
}

export function TableSkeleton({ rows = 5 }) {
  return (
    <GlassCard>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="mb-2 h-10" />
      ))}
    </GlassCard>
  );
}

export function EmptyState({ icon, title, hint, action }) {
  const Icon = icon || Inbox;
  return (
    <GlassCard className="flex flex-col items-center py-12 text-center">
      <Icon size={36} className="text-faint mb-3" aria-hidden />
      <h3 className="font-semibold">{title}</h3>
      {hint && <p className="text-muted2 mt-1 max-w-sm text-sm">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </GlassCard>
  );
}

export function ErrorState({ error, onRetry, title }) {
  const status = error?.status;
  const headline =
    title ||
    (status === 401 ? "Session expired" :
      status === 403 ? "Not allowed" :
      status === 404 ? "Not found" :
      status === 0 ? "API unreachable" : "Something went wrong");
  const Icon = status === 0 ? WifiOff : AlertTriangle;
  return (
    <GlassCard className="flex flex-col items-center py-12 text-center" role="alert">
      <Icon size={36} className="mb-3 text-amber-400" aria-hidden />
      <h3 className="font-semibold">{headline}</h3>
      <p className="text-muted2 mt-1 max-w-md text-sm">
        {error?.message || "An unexpected error occurred."}
        {error?.requestId && <span className="text-faint"> (ref {error.requestId})</span>}
      </p>
      {onRetry && (
        <div className="mt-4">
          <GlassButton variant="ghost" onClick={onRetry}>Retry</GlassButton>
        </div>
      )}
    </GlassCard>
  );
}

export function GlassAlert({ tone = "info", children }) {
  const colors = {
    info: "#38bdf8", success: "#34d399", warning: "#fbbf24", danger: "#f87171",
  };
  const c = colors[tone] || colors.info;
  return (
    <div
      role="alert"
      className="rounded-xl px-4 py-3 text-sm"
      style={{ background: `${c}14`, border: `1px solid ${c}44`, color: "#e2e8f0" }}
    >
      {children}
    </div>
  );
}

export function Modal({ open, onClose, title, children, wide = false }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          onClick={onClose}
          role="dialog" aria-modal="true" aria-label={title}
        >
          <motion.div
            className={`glass w-full ${wide ? "max-w-3xl" : "max-w-lg"} max-h-[90vh] overflow-y-auto p-6`}
            initial={{ scale: 0.96, y: 8 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.96, y: 8 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold">{title}</h2>
              <button onClick={onClose} aria-label="Close dialog" className="btn-ghost rounded-lg px-2 py-1">✕</button>
            </div>
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
