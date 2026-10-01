import api from "./client.js";

export const me = () => api.get("/users/me").then((r) => r.data);
export const updateMe = (p) => api.patch("/users/me", p).then((r) => r.data);
export const myAddresses = () => api.get("/users/me/addresses").then((r) => r.data);
export const addAddress = (p) => api.post("/users/me/addresses", p).then((r) => r.data);
export const listUsers = () => api.get("/users").then((r) => r.data);
export const setRole = (id, role) =>
  api.patch(`/users/${id}/role`, { role }).then((r) => r.data);
export const unlockUser = (id) => api.post(`/users/${id}/unlock`).then((r) => r.data);
