import api from "./client.js";

export const forProduct = (id, kind = "bought_together", limit = 10) =>
  api.get(`/products/${id}/recommendations`, { params: { kind, limit } }).then((r) => r.data);
export const forMe = (limit = 10) =>
  api.get("/users/me/recommendations", { params: { limit } }).then((r) => r.data);
