import { Link } from "react-router-dom";
import { listCategories } from "../../api/categoriesApi.js";
import { useApi } from "../../hooks/useApi.js";
import { PageHeader } from "../../components/ui/primitives.jsx";
import { EmptyState, ErrorState, TableSkeleton } from "../../components/ui/feedback.jsx";
import { GlassCard } from "../../components/ui/primitives.jsx";
import { FolderTree } from "lucide-react";

export default function Categories() {
  const res = useApi(() => listCategories());
  return (
    <div>
      <PageHeader title="Categories" subtitle="Browse the catalog by category." />
      {res.loading ? <TableSkeleton /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
        : !res.data.length ? <EmptyState title="No categories yet" />
        : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {res.data.map((c) => (
              <Link key={c.id} to={`/products?category=${c.id}`} aria-label={`Browse ${c.name}`}>
                <GlassCard hover className="flex items-center gap-3 p-5">
                  <FolderTree size={22} className="text-violet-300" aria-hidden />
                  <div>
                    <div className="font-semibold">{c.name}</div>
                    <div className="text-faint text-xs">{c.slug}</div>
                  </div>
                </GlassCard>
              </Link>
            ))}
          </div>
        )}
    </div>
  );
}
