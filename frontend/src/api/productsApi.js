import api from "./client.js";

export const listProducts = (params) => api.get("/products", { params }).then((r) => r.data);
export const searchProducts = (params) =>
  api.get("/products/search", { params }).then((r) => r.data);
export const getProduct = (id) => api.get(`/products/${id}`).then((r) => r.data);
export const createProduct = (p) => api.post("/products", p).then((r) => r.data);
export const updateProduct = (id, p) => api.patch(`/products/${id}`, p).then((r) => r.data);
export const addVariant = (id, p) =>
  api.post(`/products/${id}/variants`, p).then((r) => r.data);
export const logView = (id) => api.post(`/products/${id}/view`).then((r) => r.data);
export const uploadImage = (id, file, onProgress) => {
  const fd = new FormData();
  fd.append("file", file);
  return api
    .post(`/products/${id}/images`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / (e.total || 1))),
    })
    .then((r) => r.data);
};
