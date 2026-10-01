import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext.jsx";
import { homeFor } from "../../constants/roles.js";
import { AuthShell, Field } from "./Login.jsx";
import { GlassButton, GlassInput, GlassSelect } from "../../components/ui/primitives.jsx";

export default function Register() {
  const { signUp, signIn } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ email: "", password: "", confirm: "", full_name: "", role: "CUSTOMER" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [fieldErr, setFieldErr] = useState({});
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    const fe = {};
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email)) fe.email = "Enter a valid email.";
    if (form.password.length < 8) fe.password = "Minimum 8 characters.";
    if (form.confirm !== form.password) fe.confirm = "Passwords do not match.";
    setFieldErr(fe);
    if (Object.keys(fe).length) return;
    setBusy(true);
    setError("");
    try {
      await signUp({ email: form.email, password: form.password, full_name: form.full_name, role: form.role });
      const { home } = await signIn(form.email, form.password);
      nav(home || homeFor(form.role), { replace: true });
    } catch (err) {
      setError(err.message || "Registration failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Create your account" subtitle="Customers and sellers can self-register." error={error}>
      <form onSubmit={submit} noValidate>
        <Field label="Full name">
          <GlassInput value={form.full_name} onChange={set("full_name")} placeholder="Ada Lovelace" autoComplete="name" />
        </Field>
        <Field label="Email" error={fieldErr.email}>
          <GlassInput type="email" value={form.email} onChange={set("email")} placeholder="you@example.com" autoComplete="email" />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Password" error={fieldErr.password}>
            <GlassInput type="password" value={form.password} onChange={set("password")} placeholder="••••••••" autoComplete="new-password" />
          </Field>
          <Field label="Confirm" error={fieldErr.confirm}>
            <GlassInput type="password" value={form.confirm} onChange={set("confirm")} placeholder="••••••••" autoComplete="new-password" />
          </Field>
        </div>
        <Field label="Role">
          <GlassSelect value={form.role} onChange={set("role")}>
            <option value="CUSTOMER">Customer</option>
            <option value="SELLER">Seller</option>
          </GlassSelect>
        </Field>
        <GlassButton type="submit" disabled={busy} className="w-full py-2.5">
          {busy ? "Creating…" : "Create account"}
        </GlassButton>
      </form>
      <p className="text-muted2 mt-4 text-center text-sm">
        Support and admin accounts are created by administrators.{" "}
        <Link to="/login" className="text-sky-300 hover:text-sky-200">Sign in</Link>
      </p>
    </AuthShell>
  );
}
