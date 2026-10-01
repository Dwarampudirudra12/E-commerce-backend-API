import api from "./client.js";

export const myNotifications = (params) =>
  api.get("/notifications/me", { params }).then((r) => r.data);
export const markRead = (id) => api.patch(`/notifications/${id}/read`).then((r) => r.data);
