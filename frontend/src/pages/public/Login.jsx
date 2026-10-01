import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext.jsx";
import { GlassAlert } from "../../components/ui/feedback.jsx";
import { GlassButton, GlassCard, GlassInput } from "../../components/ui/primitives.jsx";

export function AuthShell({ title, subtitle, children, error }) {
  return (
    <div className="grid min-h-full md:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden p-10 md:flex"
        style={{ background: "linear-gradient(160deg, rgba(14,165,233,0.16), rgba(99,102,241,0.14) 55%, transparent)" }}>
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-violet-600 font-display text-sm font-bold">E</span>
          <div>
            <div className="font-display text-sm font-bold tracking-wide">ECOMMERCE AI</div>
            <div className="text-faint text-[11px]">Intelligence Platform</div>
          </div>
        </div>
        <div>
          <h2 className="font-display max-w-md text-3xl font-bold leading-tight">
            Secure commerce powered by intelligent infrastructure.
          </h2>
          <div className="mt-6 space-y-2.5 text-sm text-slate-300">
            {["Idempotent checkout — never double-charged", "Real-time fraud-risk scoring", "Demand forecasts & reorder intelligence"].map((t) => (
              <div key={t} className="flex items-center gap-2">
                <ShieldCheck size={15} className="text-emerald-400" aria-hidden /> {t}
              </div>
            ))}
          </div>
        </div>
        <div className="text-faint text-xs">JWT · RBAC · Audit trail · Prometheus</div>
      </div>
      <div className="flex items-center justify-center p-6">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
          <GlassCard className="p-7">
            <h1 className="font-display text-2xl font-bold">{title}</h1>
            {subtitle && <p className="text-muted2 mt-1 text-sm">{subtitle}</p>}
            {error && <div className="mt-4"><GlassAlert tone="danger">{error}</GlassAlert></div>}
            <div className="mt-5">{children}</div>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}

export function Field({ label, error, children }) {
  return (
    <label className="mb-3 block text-sm">
      <span className="text-muted2 mb-1 block font-medium">{label}</span>
      {children}
      {error && <span className="mt-1 block text-xs text-rose-400">{error}</span>}
    </label>
  );
}

export default function Login() {
  const { signIn } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [fieldErr, setFieldErr] = useState({});

  const submit = async (e) => {
    e.preventDefault();
    const fe = {};
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) fe.email = "Enter a valid email.";
    if (!password) fe.password = "Password is required.";
    setFieldErr(fe);
    if (Object.keys(fe).length) return;
    setBusy(true);
    setError("");
    try {
      const { home } = await signIn(email, password);
      nav(loc.state?.from || home, { replace: true });
    } catch (err) {
      setError(err.status === 423
        ? "Account locked after repeated failed logins. Reset your password."
        : err.message || "Login failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Welcome back" subtitle="Sign in to your workspace." error={error}>
      <form onSubmit={submit} noValidate>
        <Field label="Email" error={fieldErr.email}>
          <GlassInput type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com" autoComplete="email" />
        </Field>
        <Field label="Password" error={fieldErr.password}>
          <GlassInput type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••" autoComplete="current-password" />
        </Field>
        <div className="mb-4 flex items-center justify-between text-sm">
          <span />
          <Link to="/forgot-password" className="text-sky-300 hover:text-sky-200">Forgot password?</Link>
        </div>
        <GlassButton type="submit" disabled={busy} className="w-full py-2.5">
          {busy ? "Signing in…" : "Sign in"}
        </GlassButton>
      </form>
      <p className="text-muted2 mt-4 text-center text-sm">
        New here? <Link to="/register" className="text-sky-300 hover:text-sky-200">Create an account</Link>
      </p>
    </AuthShell>
  );
}
