import api from "./client.js";

export const productForecast = (id, horizon = 14) =>
  api.get(`/forecasts/products/${id}`, { params: { horizon } }).then((r) => r.data);
export const reorderSuggestions = (admin = false) =>
  api.get(admin ? "/forecasts/admin/reorder-suggestions" : "/forecasts/reorder-suggestions").then((r) => r.data);
