import { raw } from "./client.js";

export function csvUrl(kind = "orders") {
  const t = localStorage.getItem("ecom_tokens");
  return { url: `/api/v1/reports/export.csv?kind=${kind}`, token: t };
}

export async function downloadCsv(kind = "orders") {
  const { url, token } = csvUrl(kind);
  const access = token ? JSON.parse(token).access_token : null;
  const res = await raw.get(url, {
    headers: access ? { Authorization: `Bearer ${access}` } : {},
    responseType: "blob",
  });
  const blob = new Blob([res.data], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${kind}-report.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}
