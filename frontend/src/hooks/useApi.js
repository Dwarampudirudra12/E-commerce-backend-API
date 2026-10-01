import { useCallback, useEffect, useRef, useState } from "react";

/** Generic async-data hook: { data, loading, error, reload }. */
export function useApi(fn, deps = [], { immediate = true } = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);
  const alive = useRef(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await fn();
      if (alive.current) setData(d);
      return d;
    } catch (e) {
      if (alive.current) setError(e);
      throw e;
    } finally {
      if (alive.current) setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    alive.current = true;
    if (immediate) load().catch(() => {});
    return () => {
      alive.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error, reload: load };
}

/** Re-run loader on an interval (dashboard 30s auto-refresh). */
export function usePolling(fn, ms, deps = []) {
  const api = useApi(fn, deps);
  useEffect(() => {
    if (!ms) return;
    const id = setInterval(() => api.reload().catch(() => {}), ms);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ms, ...deps]);
  return api;
}

export function useDebounce(value, ms = 400) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return v;
}
