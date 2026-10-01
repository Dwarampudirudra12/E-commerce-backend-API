import { useEffect, useState } from "react";
import { Bell, Menu, Search } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext.jsx";
import { myNotifications } from "../../api/notificationsApi.js";

const TITLES = [
  [/^\/shop/, "Shop"], [/^\/products/, "Catalog"], [/^\/categories/, "Categories"],
  [/^\/cart/, "Cart"], [/^\/checkout/, "Checkout"], [/^\/orders/, "Orders"],
  [/^\/recommendations/, "Recommendations"], [/^\/notifications/, "Notifications"],
  [/^\/seller/, "Seller Console"], [/^\/support/, "Support Console"], [/^\/admin/, "Administration"],
  [/^\/settings/, "Settings"], [/^\/profile/, "Profile"],
];

export function Topbar({ onMenu, apiOnline }) {
  const { user, role } = useAuth();
  const loc = useLocation();
  const nav = useNavigate();
  const [unread, setUnread] = useState(0);
  const [q, setQ] = useState("");

  useEffect(() => {
    if (!user) return;
    myNotifications({ page_size: 1 }).then((d) => setUnread(d.unread || 0)).catch(() => {});
    const id = setInterval(() => {
      myNotifications({ page_size: 1 }).then((d) => setUnread(d.unread || 0)).catch(() => {});
    }, 30000);
    return () => clearInterval(id);
  }, [user]);

  const title = (TITLES.find(([re]) => re.test(loc.pathname)) || [])[1] || "Overview";

  return (
    <header className="flex h-16 shrink-0 items-center gap-3 border-b border-white/10 bg-white/[0.02] px-4 backdrop-blur-xl">
      <button className="btn-ghost rounded-lg p-2 md:hidden" onClick={onMenu} aria-label="Open navigation">
        <Menu size={18} />
      </button>
      <nav aria-label="Breadcrumb" className="text-sm text-slate-400">
        <Link to="/" className="hover:text-white">Home</Link>
        <span className="mx-1.5 text-slate-600">/</span>
        <span className="font-medium text-white">{title}</span>
      </nav>
      <form
        className="mx-auto hidden w-full max-w-sm items-center md:flex"
        onSubmit={(e) => {
          e.preventDefault();
          if (q.trim()) nav(`/products?q=${encodeURIComponent(q.trim())}`);
        }}
        role="search"
      >
        <div className="relative w-full">
          <Search size={15} className="text-faint absolute left-3 top-1/2 -translate-y-1/2" aria-hidden />
          <input
            value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="Search products…  (Ctrl+K)" aria-label="Global search"
            className="glass-input pl-9"
          />
        </div>
      </form>
      <div className="ml-auto flex items-center gap-2 md:ml-0">
        <span
          className="hidden items-center gap-1.5 rounded-full border border-white/10 px-2.5 py-1 text-xs text-slate-300 sm:flex"
          title={apiOnline === false ? "Backend unreachable — demo data" : "Backend connected"}
        >
          <span className={`h-2 w-2 rounded-full ${apiOnline === false ? "bg-amber-400" : "bg-emerald-400 animate-pulse"}`} aria-hidden />
          {apiOnline === false ? "Demo Mode" : "Operational"}
        </span>
        {user && (
          <button
            onClick={() => nav("/notifications")} aria-label={`Notifications, ${unread} unread`}
            className="btn-ghost relative rounded-lg p-2"
          >
            <Bell size={17} />
            {unread > 0 && (
              <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold">
                {unread > 9 ? "9+" : unread}
              </span>
            )}
          </button>
        )}
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-sky-500 to-violet-600 text-xs font-bold" title={user?.email || "Guest"}>
          {(user?.email || "G").slice(0, 1).toUpperCase()}
        </span>
      </div>
    </header>
  );
}
