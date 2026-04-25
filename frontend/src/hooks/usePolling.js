import { useState, useEffect, useCallback, useRef } from 'react';

export function usePolling(apiFunction, interval = 3000, dependencies = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Keep a stable ref to the latest apiFunction so we don't
  // have to list it as a dependency (which would cause infinite loops)
  const apiFnRef = useRef(apiFunction);
  useEffect(() => { apiFnRef.current = apiFunction; }, [apiFunction]);

  const fetchData = useCallback(async () => {
    try {
      const response = await apiFnRef.current();
      setData(response.data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []); // stable — reads from ref

  useEffect(() => {
    let isActive = true;
    let timer;

    // ── Reset state when dependencies change so stale data never flashes ──
    setData(null);
    setLoading(true);
    setError(null);

    const poll = async () => {
      if (!isActive) return;
      try {
        const response = await apiFnRef.current();
        if (isActive) {
          setData(response.data);
          setError(null);
        }
      } catch (err) {
        if (isActive) setError(err);
      } finally {
        if (isActive) setLoading(false);
      }
      if (isActive) {
        timer = setTimeout(poll, interval);
      }
    };

    poll();

    return () => {
      isActive = false;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...dependencies, interval]);

  return { data, loading, error, refetch: fetchData };
}
