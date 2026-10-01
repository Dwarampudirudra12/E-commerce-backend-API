import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext.jsx";
import { addAddress, myAddresses, updateMe } from "../../api/usersApi.js";
import { useApi } from "../../hooks/useApi.js";
import { GlassAlert } from "../../components/ui/feedback.jsx";
import { GlassButton, GlassCard, GlassInput, PageHeader } from "../../components/ui/primitives.jsx";

export default function Profile() {
  const { user, reloadUser } = useAuth();
  const [name, setName] = useState(user?.full_name || "");
  const [saved, setSaved] = useState("");
  const [addr, setAddr] = useState({ label: "home", street: "", city: "", country: "", zip_code: "", is_default: true });
  const addrs = useApi(() => myAddresses().catch(() => []));

  const save = async () => {
    await updateMe({ full_name: name });
    await reloadUser();
    setSaved("Profile updated.");
    setTimeout(() => setSaved(""), 2500);
  };
  const add = async () => {
    await addAddress(addr);
    setAddr({ label: "home", street: "", city: "", country: "", zip_code: "", is_default: false });
    addrs.reload();
  };

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Profile" />
      {saved && <div className="mb-4"><GlassAlert tone="success">{saved}</GlassAlert></div>}
      <GlassCard className="mb-5 space-y-3">
        <h2 className="font-semibold">Account</h2>
        <p className="text-muted2 text-sm">{user?.email} · <span className="font-semibold text-white">{user?.role}</span></p>
        <GlassInput value={name} onChange={(e) => setName(e.target.value)} aria-label="Full name" placeholder="Full name" />
        <GlassButton onClick={save} className="px-5">Save</GlassButton>
      </GlassCard>
      <GlassCard className="space-y-3">
        <h2 className="font-semibold">Address book</h2>
        {(addrs.data || []).map((a) => (
          <div key={a.id} className="rounded-xl border border-white/10 px-3 py-2 text-sm">
            <span className="font-medium">{a.label}</span>
            <span className="text-muted2"> — {a.street}, {a.city} {a.zip_code}, {a.country}</span>
            {a.is_default && <span className="ml-2 text-xs text-sky-300">default</span>}
          </div>
        ))}
        <div className="grid grid-cols-2 gap-2">
          {(["street", "city", "country", "zip_code"]).map((f) => (
            <GlassInput key={f} placeholder={f} value={addr[f]}
              onChange={(e) => setAddr({ ...addr, [f]: e.target.value })} aria-label={f} />
          ))}
        </div>
        <GlassButton variant="ghost" onClick={add}>Add address</GlassButton>
      </GlassCard>
    </div>
  );
}
