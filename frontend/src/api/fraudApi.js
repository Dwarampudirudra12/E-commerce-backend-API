import api from "./client.js";

/** Fraud surfaces through orders + reports; no standalone scorer endpoint. */
export const fraudDistribution = () =>
  api.get("/reports/fraud-distribution").then((r) => r.data);
