export const ROLES = {
  GUEST: "GUEST",
  CUSTOMER: "CUSTOMER",
  SELLER: "SELLER",
  SUPPORT: "SUPPORT",
  ADMIN: "ADMIN",
};

/** Mirrors the backend permission matrix (docs/API_SPEC.md). */
export const CAPABILITIES = {
  browse_catalog: ["CUSTOMER", "SELLER", "SUPPORT", "ADMIN"],
  manage_cart_order: ["CUSTOMER"],
  view_own_orders: ["CUSTOMER"],
  create_product: ["SELLER", "ADMIN"],
  update_inventory: ["SELLER", "ADMIN"],
  view_all_orders: ["SUPPORT", "ADMIN"],
  review_fraud: ["SUPPORT", "ADMIN"],
  issue_refund: ["SUPPORT", "ADMIN"],
  manage_users: ["ADMIN"],
  view_analytics: ["SELLER", "SUPPORT", "ADMIN"],
  view_audit: ["ADMIN"],
};

export const can = (role, capability) =>
  (CAPABILITIES[capability] || []).includes(role);

export const homeFor = (role) => {
  switch (role) {
    case "ADMIN": return "/admin/dashboard";
    case "SELLER": return "/seller/dashboard";
    case "SUPPORT": return "/support/dashboard";
    case "CUSTOMER": return "/shop";
    default: return "/";
  }
};

export const ORDER_STATUSES = [
  "CREATED", "PENDING_PAYMENT", "PAID", "PACKED", "SHIPPED",
  "DELIVERED", "CANCELLED", "REFUNDED", "ON_HOLD",
];

export const STATUS_META = {
  CREATED: { color: "#94a3b8", label: "Created" },
  PENDING_PAYMENT: { color: "#fbbf24", label: "Pending payment" },
  PAID: { color: "#34d399", label: "Paid" },
  PACKED: { color: "#38bdf8", label: "Packed" },
  SHIPPED: { color: "#818cf8", label: "Shipped" },
  DELIVERED: { color: "#34d399", label: "Delivered" },
  CANCELLED: { color: "#64748b", label: "Cancelled" },
  REFUNDED: { color: "#f472b6", label: "Refunded" },
  ON_HOLD: { color: "#fb7185", label: "On hold" },
};

export const riskMeta = (score) => {
  if (score == null) return { label: "Unscored", color: "#64748b" };
  if (score < 0.3) return { label: "Low risk", color: "#34d399" };
  if (score <= 0.7) return { label: "Medium risk", color: "#fbbf24" };
  return { label: "High risk", color: "#f87171" };
};
