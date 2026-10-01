import {
  BarChart3, Bell, Boxes, FolderTree, Headset, Home, LayoutDashboard,
  LogOut, Package, ScrollText, Settings, ShieldAlert, ShoppingBag,
  ShoppingCart, Sparkles, TrendingUp, Truck, Users, Wallet, Activity,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { cx } from "../../utils/format.js";

const GROUPS = [
  { label: "Overview", items: [{ to: "auto", icon: LayoutDashboard, label: "Dashboard", home: true }] },
  {
    label: "Commerce",
    roles: ["CUSTOMER", "SELLER", "SUPPORT", "ADMIN"],
    items: [
      { to: "/shop", icon: ShoppingBag, label: "Shop", roles: ["CUSTOMER", "GUEST"] },
      { to: "/products", icon: Package, label: "Products", roles: ["CUSTOMER", "GUEST", "SELLER", "ADMIN"] },
      { to: "/categories", icon: FolderTree, label: "Categories" },
      { to: "/seller/inventory", icon: Boxes, label: "Inventory", roles: ["SELLER", "ADMIN"] },
      { to: "/orders", icon: Truck, label: "Orders", roles: ["CUSTOMER", "SELLER", "SUPPORT", "ADMIN"] },
      { to: "/cart", icon: ShoppingCart, label: "Cart", roles: ["CUSTOMER"] },
      { to: "/admin/payments", icon: Wallet, label: "Payments", roles: ["SUPPORT", "ADMIN"] },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { to: "/recommendations", icon: Sparkles, label: "Recommendations", roles: ["CUSTOMER"] },
      { to: "/admin/fraud", icon: ShieldAlert, label: "Fraud Detection", roles: ["SUPPORT", "ADMIN"] },
      { to: "/admin/forecast", icon: TrendingUp, label: "Demand Forecast", roles: ["SELLER", "ADMIN"] },
    ],
  },
  {
    label: "Operations",
    items: [
      { to: "/notifications", icon: Bell, label: "Notifications" },
      { to: "/support/dashboard", icon: Headset, label: "Support Queue", roles: ["SUPPORT", "ADMIN"] },
      { to: "/admin/audit-logs", icon: ScrollText, label: "Audit Logs", roles: ["ADMIN"] },
      { to: "/admin/system", icon: Activity, label: "System Monitoring", roles: ["ADMIN"] },
    ],
  },
  {
    label: "Admin",
    items: [
      { to: "/admin/users", icon: Users, label: "Users", roles: ["ADMIN"] },
      { to: "/admin/analytics", icon: BarChart3, label: "Analytics", roles: ["SELLER", "SUPPORT", "ADMIN"] },
      { to: "/admin/reports", icon: BarChart3, label: "Reports", roles: ["SELLER", "ADMIN"] },
      { to: "/settings", icon: Settings, label: "Settings" },
    ],
  },
];

function visible(items, role, home) {
  return (items || []).filter((i) => !i.roles || i.roles.includes(role));
}

export function navFor(role, home) {
  return GROUPS.map((g) => ({
    ...g,
    items: visible(g.items, role, home).map((i) =>
      i.home ? { ...i, to: home } : i
    ),
  })).filter((g) => g.items.length);
}

export function Sidebar({ role, home, user, onLogout, collapsed, onNavigate }) {
  return (
    <aside
      className="hidden h-full w-64 shrink-0 flex-col border-r border-white/10 bg-white/[0.02] p-4 backdrop-blur-xl md:flex"
      aria-label="Primary navigation"
    >
      <nav className="flex-1 space-y-5 overflow-y-auto">
        {navFor(role, home).map((g) => (
          <div key={g.label}>
            <div className="text-faint mb-1.5 px-2 text-[11px] font-semibold uppercase tracking-wider">
              {g.label}
            </div>
            {g.items.map((i) => (
              <NavLink
                key={i.to + i.label} to={i.to} onClick={onNavigate}
                className={({ isActive }) =>
                  cx("mb-0.5 flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm transition",
                    isActive ? "bg-white/10 font-semibold text-white" : "text-slate-400 hover:bg-white/5 hover:text-white")
                }
              >
                <i.icon size={17} aria-hidden />
                {i.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <div className="mt-3 rounded-xl border border-white/10 bg-white/[0.03] p-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5" aria-hidden>
            <span className="absolute h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
          </span>
          <span className="text-xs text-slate-300">{user?.email || "Guest"}</span>
        </div>
        <div className="mt-1.5 flex items-center justify-between">
          <span className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] text-slate-300">{role}</span>
          {user && (
            <button onClick={onLogout} className="flex items-center gap-1 text-xs text-slate-400 hover:text-white" aria-label="Log out">
              <LogOut size={13} /> Logout
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}

export function MobileNav({ role, home, onLogout, open, onClose }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 md:hidden">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} aria-hidden />
      <div className="absolute left-0 top-0 h-full w-72 overflow-y-auto border-r border-white/10 bg-[#080B12] p-4">
        <div className="mb-4 flex items-center justify-between">
          <span className="font-display font-bold">ECOMMERCE AI</span>
          <button onClick={onClose} aria-label="Close menu" className="btn-ghost px-2 py-1">✕</button>
        </div>
        {navFor(role, home).map((g) => (
          <div key={g.label} className="mb-4">
            <div className="text-faint mb-1 px-2 text-[11px] font-semibold uppercase tracking-wider">{g.label}</div>
            {g.items.map((i) => (
              <NavLink
                key={i.to + i.label} to={i.to} onClick={onClose}
                className={({ isActive }) =>
                  cx("mb-0.5 flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm",
                    isActive ? "bg-white/10 font-semibold" : "text-slate-400")}
              >
                <i.icon size={17} aria-hidden />{i.label}
              </NavLink>
            ))}
          </div>
        ))}
        {onLogout && (
          <button onClick={() => { onLogout(); onClose(); }} className="btn-ghost flex w-full items-center gap-2 px-3 py-2 text-sm">
            <LogOut size={15} /> Logout
          </button>
        )}
      </div>
    </div>
  );
}

export function HomeIcon(props) {
  return <Home {...props} />;
}
