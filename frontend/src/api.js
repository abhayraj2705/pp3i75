import { useEffect, useState } from "react";

// Thin wrappers around the backend. In dev Vite proxies /api; in production it is the same domain.
async function get(path, params = {}) {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`/api/${path}${query ? `?${query}` : ""}`);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail ? JSON.stringify(body.detail) : `Request failed (${response.status})`);
  }
  return body;
}

export const getMeta = () => get("meta");
export const getDayAhead = (date, cutoffHour) => get("day-ahead", { date, cutoff_hour: cutoffHour });
export const getAccuracy = (cutoffHour) => get("accuracy", { cutoff_hour: cutoffHour });

// Load data whenever `deps` change. Ignores responses that arrive after a newer request started.
export function useApi(load, deps) {
  const [state, setState] = useState({ data: null, loading: true, error: null });
  useEffect(() => {
    let current = true;
    setState((previous) => ({ ...previous, loading: true, error: null }));
    load()
      .then((data) => current && setState({ data, loading: false, error: null }))
      .catch((error) => current && setState({ data: null, loading: false, error: error.message }));
    return () => {
      current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return state;
}
