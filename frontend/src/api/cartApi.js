import api from "./client.js";

export const getCart = () => api.get("/cart").then((r) => r.data);
export const addItem = (p) => api.post("/cart/items", p).then((r) => r.data);
export const updateItem = (id, quantity) =>
  api.patch(`/cart/items/${id}?quantity=${quantity}`).then((r) => r.data);
export const removeItem = (id) => api.delete(`/cart/items/${id}`).then((r) => r.data);
