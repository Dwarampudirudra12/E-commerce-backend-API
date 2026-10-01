import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext.jsx";
import { updateMe } from "../../api/usersApi.js";
import { GlassAlert } from "../../components/ui/feedback.jsx";
import { GlassButton, GlassCard, GlassInput, PageHeader } from "../../components/ui/primitives.jsx";

export default function Settings() {
  const { user, role, reloadUser } = useAuth();
  const [name, setName] = useState(user?.full_name || "");
  const [saved, setSaved] = useState("");
  const [prefs, setPrefs] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("ecom_prefs") || '{"emailAlerts":true,"inApp":true}');
    } catch {
      return { emailAlerts: true, inApp: true };
    }
  });
  const savePrefs = (p) => {
    setPrefs(p);
    localStorage.setItem("ecom_prefs", JSON.stringify(p));
  };

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Settings" />
      {saved && <div className="mb-4"><GlassAlert tone="success">{saved}</GlassAlert></div>}
      <GlassCard className="mb-4 space-y-3">
        <h2 className="font-semibold">Profile</h2>
        <p className="text-muted2 text-sm">{user?.email} · <strong className="text-white">{role}</strong></p>
        <GlassInput value={name} onChange={(e) => setName(e.target.value)} aria-label="Full name" />
        <GlassButton onClick={async () => {
          await updateMe({ full_name: name });
          await reloadUser();
          setSaved("Profile saved.");
          setTimeout(() => setSaved(""), 2500);
        }}>Save profile</GlassButton>
      </GlassCard>
      <GlassCard className="mb-4 space-y-2">
        <h2 className="font-semibold">Notification preferences</h2>
        {(["emailAlerts", "inApp"]).map((k) => (
          <label key={k} className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={!!prefs[k]}
              onChange={(e) => savePrefs({ ...prefs, [k]: e.target.checked })} />
            {k === "emailAlerts" ? "Email alerts" : "In-app notifications"}
          </label>
        ))}
      </GlassCard>
      {role === "ADMIN" && (
        <GlassCard className="space-y-2">
          <h2 className="font-semibold">Platform thresholds <span className="text-faint text-xs">(server-configured)</span></h2>
          <dl className="grid grid-cols-2 gap-1 text-sm">
            <dt className="text-muted2">Fraud approve below</dt><dd>0.30</dd>
            <dt className="text-muted2">Fraud hold above</dt><dd>0.70</dd>
            <dt className="text-muted2">Support refund limit</dt><dd>$100.00</dd>
            <dt className="text-muted2">Failed-login lockout</dt><dd>5 attempts</dd>
            <dt className="text-muted2">Dashboard refresh</dt><dd>30 s</dd>
          </dl>
          <p className="text-faint text-xs">Changed via server environment + redeploy; every change path is audited.</p>
        </GlassCard>
      )}
    </div>
  );
}
