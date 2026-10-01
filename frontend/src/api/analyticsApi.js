import api from "./client.js";

export const salesSummary = (params) =>
  api.get("/reports/sales/summary", { params }).then((r) => r.data);
export const revenueTrend = (days = 30) =>
  api.get("/reports/revenue-trend", { params: { days } }).then((r) => r.data);
export const topProducts = (limit = 10) =>
  api.get("/reports/top-products", { params: { limit } }).then((r) => r.data);
export const exportCsvUrl = (kind = "orders") => `/api/v1/reports/export.csv?kind=${kind}`;
