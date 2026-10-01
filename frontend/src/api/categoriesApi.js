import api from "./client.js";

export const listCategories = () => api.get("/categories").then((r) => r.data);
export const createCategory = (p) => api.post("/categories", p).then((r) => r.data);
