import { raw } from "./client.js";

export const readiness = () => raw.get("/health/ready").then((r) => r.data);
export const metricsText = () =>
  raw.get("/metrics", { responseType: "text" }).then((r) =>
    typeof r.data === "string" ? r.data : ""
  );

/** Parse the few Prometheus counters the System page needs. */
export function parseCounters(text) {
  const out = {};
  for (const line of text.split("\n")) {
    const m = line.match(/^(\w+)(?:\{([^}]*)\})?\s+([\d.e+-]+)$/);
    if (!m) continue;
    const [, name, labels, value] = m;
    if (!/^(http_requests_total|orders_created_total|payment_webhooks_total|fraud_scored_total)$/.test(name))
      continue;
    out[name] = out[name] || [];
    out[name].push({ labels: Object.fromEntries(
      [...labels.matchAll(/(\w+)="([^"]*)"/g)].map((x) => [x[1], x[2]])
    ), value: Number(value) });
  }
  return out;
}
