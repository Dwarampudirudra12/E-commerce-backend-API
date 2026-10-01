import { useState } from "react";
import { Link } from "react-router-dom";
import { forgotPassword, resetPassword, verifyEmail } from "../../api/authApi.js";
import { AuthShell, Field } from "./Login.jsx";
import { GlassAlert } from "../../components/ui/feedback.jsx";
import { GlassButton, GlassInput } from "../../components/ui/primitives.jsx";

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await forgotPassword(email);
      setDone(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <AuthShell title="Reset password" subtitle="We will email you a reset link." error={error}>
      {done ? (
        <GlassAlert tone="success">
          If the email exists, a reset link was sent. <Link to="/login" className="text-sky-300">Back to sign in</Link>
        </GlassAlert>
      ) : (
        <form onSubmit={submit}>
          <Field label="Email">
            <GlassInput type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </Field>
          <GlassButton type="submit" disabled={busy} className="w-full py-2.5">
            {busy ? "Sending…" : "Send reset link"}
          </GlassButton>
        </form>
      )}
    </AuthShell>
  );
}

export function ResetPassword() {
  const params = new URLSearchParams(window.location.search);
  const [token, setToken] = useState(params.get("token") || "");
  const [pw, setPw] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await resetPassword(token, pw);
      setDone(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <AuthShell title="Choose a new password" error={error}>
      {done ? (
        <GlassAlert tone="success">
          Password updated. <Link to="/login" className="text-sky-300">Sign in</Link>
        </GlassAlert>
      ) : (
        <form onSubmit={submit}>
          <Field label="Reset token">
            <GlassInput value={token} onChange={(e) => setToken(e.target.value)} placeholder="Paste the token from your email" required />
          </Field>
          <Field label="New password">
            <GlassInput type="password" value={pw} onChange={(e) => setPw(e.target.value)} required />
          </Field>
          <GlassButton type="submit" disabled={busy} className="w-full py-2.5">
            {busy ? "Saving…" : "Save new password"}
          </GlassButton>
        </form>
      )}
    </AuthShell>
  );
}

export function VerifyEmail() {
  const params = new URLSearchParams(window.location.search);
  const [token, setToken] = useState(params.get("token") || "");
  const [state, setState] = useState("idle");
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    setState("busy");
    try {
      await verifyEmail(token);
      setState("done");
    } catch (err) {
      setError(err.message);
      setState("idle");
    }
  };
  return (
    <AuthShell title="Verify your email" error={error}>
      {state === "done" ? (
        <GlassAlert tone="success">
          Email verified. <Link to="/login" className="text-sky-300">Sign in</Link>
        </GlassAlert>
      ) : (
        <form onSubmit={submit}>
          <Field label="Verification token">
            <GlassInput value={token} onChange={(e) => setToken(e.target.value)} required />
          </Field>
          <GlassButton type="submit" disabled={state === "busy"} className="w-full py-2.5">
            {state === "busy" ? "Verifying…" : "Verify email"}
          </GlassButton>
        </form>
      )}
    </AuthShell>
  );
}
