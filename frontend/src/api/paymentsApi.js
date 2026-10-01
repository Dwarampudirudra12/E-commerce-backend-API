import api from "./client.js";

export const paymentForOrder = (orderId) =>
  api.get(`/payments/by-order/${orderId}`).then((r) => r.data);
export const refund = (paymentId, p = {}) =>
  api.post(`/payments/${paymentId}/refund`, p).then((r) => r.data);
/** Test-mode gateway confirmation (dev/demo only, refused in prod). */
export const confirmTestPayment = (orderId) =>
  api.post(`/payments/by-order/${orderId}/confirm-test`).then((r) => r.data);
