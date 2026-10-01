export const fmtMoney = (n) =>
  n == null ? "—" : `$${Number(n).toFixed(2)}`;

export const fmtDate = (iso) => {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
};

export const fmtPct = (n) => (n == null ? "—" : `${(Number(n) * 100).toFixed(1)}%`);

export const timeAgo = (iso) => {
  if (!iso) return "—";
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${Math.floor(s)}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};

export const cx = (...parts) => parts.filter(Boolean).join(" ");
