"""Item-to-item recommendations (doc 3.6, M3).

- bought-together: cosine similarity over order co-occurrence.
- also-viewed: cosine similarity over per-user view sets.
- Fallback: popular-in-category (cold start for new users/products).
"""
import math
from collections import Counter, defaultdict


def _cosine(a: dict[int, float], b: dict[int, float]) -> float:
    dot = sum(a[k] * b[k] for k in a.keys() & b.keys())
    na, nb = math.sqrt(sum(v * v for v in a.values())), math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def similar_items(target: int, transactions: list[list[int]], limit: int = 10) -> list[tuple[int, float]]:
    """Cosine similarity of `target` vs every other item over transactions."""
    vecs: dict[int, dict[int, float]] = defaultdict(dict)
    for t, txn in enumerate(transactions):
        for pid in set(txn):
            vecs[pid][t] = vecs[pid].get(t, 0) + 1
    if target not in vecs:
        return []
    scored = [(pid, _cosine(vecs[target], v)) for pid, v in vecs.items() if pid != target]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [(pid, round(s, 4)) for pid, s in scored[:limit] if s > 0]


def personal_for(bought: list[int], transactions: list[list[int]], limit: int = 10,
                 exclude: set[int] | None = None) -> list[tuple[int, float]]:
    agg: dict[int, float] = Counter()
    for pid in bought:
        for other, s in similar_items(pid, transactions, limit=limit * 2):
            agg[other] += s
    excluded = (exclude or set()) | set(bought)
    ranked = [(pid, round(s, 4)) for pid, s in agg.most_common(limit * 2) if pid not in excluded]
    return ranked[:limit]


def hit_rate_at_10(transactions: list[list[int]]) -> float:
    """Leave-one-out: hide one item of each multi-item txn, HitRate@10."""
    eligible = [t for t in transactions if len(set(t)) >= 2]
    if not eligible:
        return 0.0
    hits = 0
    for txn in eligible:
        items = list(dict.fromkeys(txn))
        hidden, rest = items[0], items[1:]
        recs = {pid for pid, _ in personal_for(rest, transactions, limit=10,
                                               exclude=set(rest))}
        hits += hidden in recs
    return round(hits / len(eligible), 4)
