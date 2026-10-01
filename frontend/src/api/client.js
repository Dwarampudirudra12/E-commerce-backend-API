import axios from "axios";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: `${BASE}/api/v1`, timeout: 20000 });

export const raw = axios.create({ baseURL: BASE, timeout: 20000 });

function readTokens() {
  try {
    return JSON.parse(localStorage.getItem("ecom_tokens") || "null");
  } catch {
    return null;
  }
}

api.interceptors.request.use((cfg) => {
  const t = readTokens();
  if (t?.access_token) cfg.headers.Authorization = `Bearer ${t.access_token}`;
  cfg.headers["X-Request-ID"] = Math.random().toString(36).slice(2, 10);
  return cfg;
});

let refreshing = null;

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const { config, response } = err;
    if (response?.status === 401 && !config._retried) {
      const t = readTokens();
      if (t?.refresh_token) {
        try {
          refreshing =
            refreshing ||
            axios
              .post(`${BASE}/api/v1/auth/refresh`, { refresh_token: t.refresh_token })
              .then((r) => r.data);
          const nt = await refreshing;
          localStorage.setItem("ecom_tokens", JSON.stringify(nt));
          config._retried = true;
          config.headers.Authorization = `Bearer ${nt.access_token}`;
          return api(config);
        } catch {
          localStorage.removeItem("ecom_tokens");
        } finally {
          refreshing = null;
        }
      } else {
        localStorage.removeItem("ecom_tokens");
      }
      window.dispatchEvent(new CustomEvent("auth:expired"));
    }
    return Promise.reject(normalizeError(err));
  }
);

export function normalizeError(err) {
  const data = err?.response?.data;
  const e = new Error(
    (typeof data?.detail === "string" && data.detail) ||
      err.message ||
      "Request failed"
  );
  e.status = err?.response?.status || 0;
  e.code = data?.code;
  e.requestId = data?.request_id || err?.config?.headers?.["X-Request-ID"];
  return e;
}

export async function apiHealth() {
  try {
    const [live, ready] = await Promise.all([
      raw.get("/health/live").then((r) => r.data),
      raw.get("/health/ready").then((r) => r.data).catch(() => null),
    ]);
    return { connected: live?.status === "ok", ready };
  } catch {
    return { connected: false, ready: null };
  }
}

export default api;
