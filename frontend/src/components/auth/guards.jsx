import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext.jsx";
import { usePermissions } from "../../contexts/PermissionContext.jsx";
import { homeFor } from "../../constants/roles.js";
import { Skeleton } from "../ui/feedback.jsx";

export function RequireAuth() {
  const { isAuthed, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <AuthLoading />;
  if (!isAuthed) return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  return <Outlet />;
}

export function RequireRole({ roles }) {
  const { role, isAuthed, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <AuthLoading />;
  if (!isAuthed) return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  if (!roles.includes(role)) return <Navigate to={homeFor(role)} replace />;
  return <Outlet />;
}

export function RequireCapability({ capability, fallback = null }) {
  const { can } = usePermissions();
  if (!can(capability)) return fallback;
  return <Outlet />;
}

/** Render-guard for inline UI (route guards above handle navigation). */
export function RoleGuard({ roles, children, fallback = null }) {
  const { role } = useAuth();
  if (!roles.includes(role)) return fallback;
  return <>{children}</>;
}

export function PermissionGuard({ capability, children, fallback = null }) {
  const { can } = usePermissions();
  if (!can(capability)) return fallback;
  return <>{children}</>;
}

function AuthLoading() {
  return (
    <div className="mx-auto w-full max-w-7xl p-6" aria-label="Loading session">
      <Skeleton className="mb-3 h-8 w-56" />
      <Skeleton className="h-64" />
    </div>
  );
}
