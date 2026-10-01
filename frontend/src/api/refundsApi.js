import api from "./client.js";

export const listRefunds = () => api.get("/refunds").then((r) => r.data);
