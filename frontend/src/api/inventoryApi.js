import api from "./client.js";

export const getInventory = (id) =>
  api.get(`/products/${id}/inventory`).then((r) => r.data);
export const updateInventory = (id, p) =>
  api.patch(`/products/${id}/inventory`, p).then((r) => r.data);
