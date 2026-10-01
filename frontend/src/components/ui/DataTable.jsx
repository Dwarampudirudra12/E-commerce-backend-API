import { cx } from "../../utils/format.js";
import { GlassCard } from "./primitives.jsx";

/** Responsive table: horizontal scroll on small screens. */
export function DataTable({ columns, rows, rowKey, empty, onRowClick }) {
  if (!rows?.length) return empty || null;
  return (
    <GlassCard className="overflow-x-auto p-0">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-400">
            {columns.map((c) => (
              <th key={c.key} className="px-4 py-3 font-medium">{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row[rowKey]} onClick={() => onRowClick?.(row)}
              className={cx("border-b border-white/5 last:border-0",
                onRowClick && "cursor-pointer hover:bg-white/[0.04]")}
            >
              {columns.map((c) => (
                <td key={c.key} className="px-4 py-3 align-middle">
                  {c.render ? c.render(row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </GlassCard>
  );
}

export function Pagination({ page, pageSize, total, onPage }) {
  const pages = Math.max(1, Math.ceil((total || 0) / pageSize));
  if (pages <= 1) return null;
  return (
    <div className="mt-4 flex items-center justify-center gap-2 text-sm">
      <button className="btn-ghost px-3 py-1" disabled={page <= 1} onClick={() => onPage(page - 1)}>
        Prev
      </button>
      <span className="text-muted2">Page {page} of {pages}</span>
      <button className="btn-ghost px-3 py-1" disabled={page >= pages} onClick={() => onPage(page + 1)}>
        Next
      </button>
    </div>
  );
}
