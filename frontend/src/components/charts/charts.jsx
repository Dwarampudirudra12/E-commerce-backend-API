import {
  ArcElement, BarElement, CategoryScale, Chart as ChartJS, Filler,
  Legend, LinearScale, LineElement, PointElement, Title, Tooltip,
} from "chart.js";
import { Bar, Doughnut, Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, ArcElement, Title, Tooltip, Legend, Filler);

const grid = "rgba(255,255,255,0.07)";
const ticks = { color: "#94a3b8", font: { size: 11 } };
const baseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: "#cbd5e1", font: { size: 11 }, boxWidth: 12 } },
    tooltip: {
      backgroundColor: "rgba(8,11,18,0.94)",
      borderColor: "rgba(255,255,255,0.12)",
      borderWidth: 1,
      titleColor: "#f1f5f9",
      bodyColor: "#cbd5e1",
      padding: 10,
      cornerRadius: 10,
    },
  },
  scales: {
    x: { grid: { color: grid }, ticks },
    y: { grid: { color: grid }, ticks, beginAtZero: true },
  },
};

const noAxes = {
  ...baseOptions,
  scales: { x: { display: false }, y: { display: false } },
};

export function LineChart({ labels, series, height = 240 }) {
  return (
    <div style={{ height }}>
      <Line
        data={{ labels, datasets: series }}
        options={baseOptions}
      />
    </div>
  );
}

export function BarChart({ labels, series, height = 240, horizontal = false }) {
  return (
    <div style={{ height }}>
      <Bar data={{ labels, datasets: series }} options={{ ...baseOptions, indexAxis: horizontal ? "y" : "x" }} />
    </div>
  );
}

export function DonutChart({ labels, values, colors, height = 220 }) {
  return (
    <div style={{ height }}>
      <Doughnut
        data={{ labels, datasets: [{ data: values, backgroundColor: colors, borderWidth: 0 }] }}
        options={{ ...noAxes, cutout: "68%" }}
      />
    </div>
  );
}

export function Sparkline({ values, color = "#38bdf8" }) {
  return (
    <div style={{ height: 36, width: 110 }}>
      <Line
        data={{ labels: values.map((_, i) => i), datasets: [{
          data: values, borderColor: color, borderWidth: 1.5, pointRadius: 0,
          fill: true, backgroundColor: `${color}22`, tension: 0.4,
        }] }}
        options={{ ...noAxes, plugins: { legend: { display: false }, tooltip: { enabled: false } } }}
      />
    </div>
  );
}

export const palette = {
  cyan: "#38bdf8", violet: "#a78bfa", emerald: "#34d399",
  amber: "#fbbf24", rose: "#fb7185", slate: "#94a3b8",
};
