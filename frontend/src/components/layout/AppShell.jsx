import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiHealth } from "../../api/client.js";
import { useAuth } from "../../contexts/AuthContext.jsx";
import { homeFor } from "../../constants/roles.js";
import { MobileNav, Sidebar } from "./Sidebar.jsx";
import { Topbar } from "./Topbar.jsx";

export function PageContainer({ children }) {
  return <div className="mx-auto w-full max-w-7xl flex-1 overflow-y-auto p-4 md:p-6">{children}</div>;
}

export default function AppShell({ children }) {
  const { user, role, signOut } = useAuth();
  const nav = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [apiOnline, setApiOnline] = useState(null);

  useEffect(() => {
    let alive = true;
    apiHealth().then((h) => alive && setApiOnline(h.connected));
    const id = setInterval(() => {
      apiHealth().then((h) => alive && setApiOnline(h.connected));
    }, 30000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const logout = async () => {
    await signOut();
    nav("/login");
  };

  return (
    <div className="app-grid-bg flex h-full flex-col">
      <div className="flex min-h-0 flex-1">
        <Sidebar role={role} home={homeFor(role)} user={user} onLogout={user ? logout : null} />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar onMenu={() => setMenuOpen(true)} apiOnline={apiOnline} />
          {apiOnline === false && (
            <div className="border-b border-amber-400/30 bg-amber-400/10 px-4 py-1.5 text-center text-xs text-amber-200" role="status">
              Backend unreachable — showing cached/demo content. Start the API at http://localhost:8000.
            </div>
          )}
          {children}
        </div>
      </div>
      <MobileNav role={role} home={homeFor(role)} onLogout={user ? logout : null} open={menuOpen} onClose={() => setMenuOpen(false)} />
      <nav className="flex shrink-0 items-center justify-around border-t border-white/10 bg-white/[0.02] py-2 backdrop-blur-xl md:hidden" aria-label="Mobile">
        <MobileLink to={homeFor(role)} label="Home" />
        <MobileLink to="/products" label="Shop" />
        <MobileLink to="/cart" label="Cart" />
        <MobileLink to="/notifications" label="Alerts" />
      </nav>
    </div>
  );
}

function MobileLink({ to, label }) {
  return (
    <Link to={to} className="rounded-lg px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white">
      {label}
    </Link>
  );
}
