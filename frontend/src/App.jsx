import { useCallback, useEffect, useState } from "react";
import { Bar, Doughnut, Line } from "react-chartjs-2";
import {
  ArcElement, BarElement, CategoryScale, Chart as ChartJS,
  Legend, LinearScale, LineElement, PointElement, Title, Tooltip,
} from "chart.js";
import { get, login, patch } from "./api.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, ArcElement, Title, Tooltip, Legend);

const card = { border: "1px solid #ddd", borderRadius: 8, padding: 12, minWidth: 140 };

function Kpis({ k }) {
  if (!k) return null;
  const cells = [
    ["Revenue", `$${k.revenue}`], ["Orders", k.orders],
    ["AOV", `$${k.average_order_value}`], ["Refund rate", k.refund_rate],
    ["Fraud held", k.fraud_held], ["Low stock", k.low_stock_count],
  ];
  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
      {cells.map(([l, v]) => (
        <div key={l} style={card}><div style={{ fontSize: 12 }}>{l}</div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{v}</div></div>
      ))}
    </div>
  );
}

export default function App() {
  const [auth, setAuth] = useState(!!localStorage.getItem("access_token"));
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("Password123!");
  const [tab, setTab] = useState("overview");
  const [days, setDays] = useState(30);
  const [kpis, setKpis] = useState(null);
  const [trend, setTrend] = useState([]);
  const [byStatus, setByStatus] = useState({});
  const [top, setTop] = useState([]);
  const [fraud, setFraud] = useState({});
  const [queue, setQueue] = useState([]);
  const [reorder, setReorder] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const load = useCallback(async () => {
    try {
      const [k, t, tp, f] = await Promise.all([
        get("/reports/sales/summary"),
        get("/reports/revenue-trend", { days }),
        get("/reports/top-products", { limit: 10 }),
        get("/reports/fraud-distribution").catch(() => ({})),
      ]);
      setKpis(k); setTrend(t.points || []); setByStatus(k.by_status || {});
      setTop(tp.items || []); setFraud(f);
      try {
        const q = await get("/orders/review/queue");
        setQueue(q.items || []);
      } catch { /* sellers have no review queue */ }
      try {
        const r = await get("/forecasts/reorder-suggestions");
        setReorder(r.items || []);
      } catch { /* customers have no forecasts */ }
      try {
        const n = await get("/notifications/me", { page_size: 10 });
        setAlerts(n.items || []);
      } catch { /* ignore */ }
    } catch { /* not authorised for some endpoints */ }
  }, [days]);

  useEffect(() => {
    if (!auth) return;
    load();
    const id = setInterval(load, 30000); // doc 3.8: 30s auto-refresh
    return () => clearInterval(id);
  }, [auth, load]);

  if (!auth) {
    return (
      <main style={{ fontFamily: "system-ui", padding: 24, maxWidth: 420 }}>
        <h1>Analytics Dashboard</h1>
        <input value={email} onChange={(e) => setEmail(e.target.value)}
          placeholder="email" style={{ display: "block", width: "100%", marginBottom: 8 }} />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
          placeholder="password" style={{ display: "block", width: "100%", marginBottom: 8 }} />
        <button onClick={() => login(email, password).then(() => setAuth(true))}>
          Sign in
        </button>
      </main>
    );
  }

  const review = async (id, to) => {
    await patch(`/orders/${id}/status`, { to_status: to });
    load();
  };

  return (
    <main style={{ fontFamily: "system-ui", padding: 24 }}>
      <h1>Analytics Dashboard</h1>
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {["overview", "products", "fraud", "alerts"].map((t) => (
          <button key={t} disabled={tab === t} onClick={() => setTab(t)}>{t}</button>
        ))}
        <label style={{ marginLeft: 16 }}>Days:
          <input type="number" value={days} min={1} max={365}
            onChange={(e) => setDays(Number(e.target.value))} style={{ width: 64 }} />
        </label>
        <a href="/api/v1/reports/export.csv?kind=orders" style={{ marginLeft: "auto" }}>
          Export orders CSV
        </a>
      </div>

      {tab === "overview" && (<>
        <Kpis k={kpis} />
        <div style={{ maxWidth: 720, marginTop: 16 }}>
          <Line data={{ labels: trend.map((p) => p.day),
            datasets: [{ label: "Revenue", data: trend.map((p) => p.revenue) }] }} />
        </div>
        <div style={{ maxWidth: 480, marginTop: 16 }}>
          <Bar data={{ labels: Object.keys(byStatus),
            datasets: [{ label: "Orders by status", data: Object.values(byStatus) }] }} />
        </div>
      </>)}

      {tab === "products" && (<>
        <div style={{ maxWidth: 640 }}>
          <Bar data={{ labels: top.map((p) => p.sku),
            datasets: [{ label: "Units sold", data: top.map((p) => p.units) }] }} />
        </div>
        <h2>Reorder suggestions</h2>
        <table border={1} cellPadding={4}>
          <thead><tr><th>SKU</th><th>On hand</th><th>Stock-out in (days)</th><th>Reorder</th><th>Risk</th></tr></thead>
          <tbody>{reorder.map((r) => (
            <tr key={r.product_id}><td>{r.sku}</td><td>{r.on_hand}</td>
              <td>{r.days_until_stockout ?? "—"}</td><td>{r.reorder_qty}</td>
              <td>{r.at_risk ? "YES" : ""}</td></tr>
          ))}</tbody>
        </table>
      </>)}

      {tab === "fraud" && (<>
        <div style={{ maxWidth: 380 }}>
          <Doughnut data={{ labels: Object.keys(fraud),
            datasets: [{ data: Object.values(fraud) }] }} />
        </div>
        <h2>Review queue</h2>
        <table border={1} cellPadding={4}>
          <thead><tr><th>Order</th><th>Total</th><th>Score</th><th>Factors</th><th>Action</th></tr></thead>
          <tbody>{queue.map((o) => (
            <tr key={o.id}><td>{o.order_number}</td><td>${o.total}</td>
              <td>{o.risk_score}</td><td>{(o.risk_factors || []).join("; ")}</td>
              <td><button onClick={() => review(o.id, "PENDING_PAYMENT")}>Approve</button>
                <button onClick={() => review(o.id, "CANCELLED")}>Reject</button></td></tr>
          ))}</tbody>
        </table>
      </>)}

      {tab === "alerts" && (
        <ul>{alerts.map((a) => (
          <li key={a.id}>[{a.type}] {JSON.stringify(a.payload)} — {a.created_at}</li>
        ))}</ul>
      )}
    </main>
  );
}
