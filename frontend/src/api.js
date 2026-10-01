import axios from "axios";

const api = axios.create({ baseURL: "/api/v1" });

api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("access_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

export async function login(email, password) {
  const { data } = await api.post("/auth/login", { email, password });
  localStorage.setItem("access_token", data.access_token);
  return data;
}

export const get = (path, params) => api.get(path, { params }).then((r) => r.data);
export const patch = (path, body) => api.patch(path, body).then((r) => r.data);
export default api;
