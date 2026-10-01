import {
  Ban, CheckCircle2, Circle, Clock, CreditCard, PackageCheck, Truck,
} from "lucide-react";
import { STATUS_META } from "../../constants/roles.js";
import { fmtDate } from "../../utils/format.js";
import { GlassBadge } from "../ui/primitives.jsx";

export function StatusBadge({ status }) {
  const m = STATUS_META[status] || { color: "#94a3b8", label: status };
  return <GlassBadge color={m.color}>{m.label}</GlassBadge>;
}

const FLOW = ["CREATED", "PENDING_PAYMENT", "PAID", "PACKED", "SHIPPED", "DELIVERED"];
const ICONS = {
  CREATED: Circle, PENDING_PAYMENT: Clock, PAID: CreditCard,
  PACKED: PackageCheck, SHIPPED: Truck, DELIVERED: CheckCircle2,
  CANCELLED: Ban, REFUNDED: Ban, ON_HOLD: Clock,
};

const BLURB = {
  CREATED: "Order received, stock reserved",
  PENDING_PAYMENT: "Waiting for payment confirmation",
  PAID: "Payment verified, sent to fulfilment",
  PACKED: "Packed by the seller",
  SHIPPED: "On its way to you",
  DELIVERED: "Delivered — enjoy!",
  CANCELLED: "Cancelled, stock released",
  REFUNDED: "Refunded to the payment method",
  ON_HOLD: "Held for manual fraud review",
};

export function OrderTimeline({ order, history = [] }) {
  const terminal = ["CANCELLED", "REFUNDED"].includes(order.status);
  const steps = terminal || order.status === "ON_HOLD"
    ? [...FLOW.slice(0, FLOW.indexOf("PAID") + 1), order.status]
    : FLOW;
  const activeIdx = steps.indexOf(order.status);
  const byStatus = {};
  history.forEach((h) => {
    byStatus[h.to_status] = h;
  });
  return (
    <ol className="relative ml-2 space-y-0 border-l border-white/10 pl-0" aria-label="Order timeline">
      {steps.map((s, i) => {
        const Icon = ICONS[s] || Circle;
        const done = terminal ? i < steps.length - 1 : i <= activeIdx;
        const current = s === order.status;
        const m = STATUS_META[s] || {};
        return (
          <li key={s} className="relative flex gap-3 pb-5 pl-6 last:pb-0">
            <span
              className="absolute -left-[9px] top-0.5 flex h-[18px] w-[18px] items-center justify-center rounded-full border"
              style={{
                borderColor: m.color, color: m.color,
                background: current ? `${m.color}26` : "#0B1020",
                boxShadow: current ? `0 0 12px ${m.color}66` : "none",
              }}
              aria-hidden
            >
              <Icon size={11} />
            </span>
            <div>
              <div className="flex items-center gap-2 text-sm font-semibold">
                {m.label || s}
                {current && <GlassBadge color={m.color}>current</GlassBadge>}
              </div>
              <div className="text-muted2 text-xs">{BLURB[s] || ""}</div>
              {byStatus[s]?.created_at && (
                <div className="text-faint text-xs">{fmtDate(byStatus[s].created_at)}</div>
              )}
              {done && !current && <span className="sr-only">completed</span>}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
