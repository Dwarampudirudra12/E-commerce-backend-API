import api from "./client.js";

export const checkout = (body, idempotencyKey) =>
  api
    .post("/orders", body, { headers: { "Idempotency-Key": idempotencyKey } })
    .then((r) => r.data);
export const listOrders = (params) => api.get("/orders", { params }).then((r) => r.data);
export const getOrder = (id) => api.get(`/orders/${id}`).then((r) => r.data);
export const changeStatus = (id, to_status, note = "") =>
  api.patch(`/orders/${id}/status`, { to_status, note }).then((r) => r.data);
export const reviewQueue = () => api.get("/orders/review/queue").then((r) => r.data);
export const orderHistory = (id) => api.get(`/orders/${id}/history`).then((r) => r.data);
