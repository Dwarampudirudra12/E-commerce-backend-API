import api from "./client.js";

export const register = (p) => api.post("/auth/register", p).then((r) => r.data);
export const login = (email, password) =>
  api.post("/auth/login", { email, password }).then((r) => r.data);
export const refresh = (refresh_token) =>
  api.post("/auth/refresh", { refresh_token }).then((r) => r.data);
export const logout = (refresh_token) =>
  api.post("/auth/logout", refresh_token ? { refresh_token } : {}).then((r) => r.data);
export const verifyEmail = (token) =>
  api.post("/auth/verify-email", { token }).then((r) => r.data);
export const forgotPassword = (email) =>
  api.post("/auth/forgot-password", { email }).then((r) => r.data);
export const resetPassword = (token, new_password) =>
  api.post("/auth/reset-password", { token, new_password }).then((r) => r.data);
