import api from "./client.js";

export const listAuditLogs = (params) =>
  api.get("/audit-logs", { params }).then((r) => r.data);
