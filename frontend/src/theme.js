import { useEffect, useState } from "react";

// Chart colours (SVG attributes cannot read CSS variables reliably, so they live here).
// Values from a colour-blind-validated palette; dark mode has its own steps.
const LIGHT = {
  forecast: "#2a78d6",
  actual: "#eb6834",
  bar: "#2a78d6",
  grid: "#e4e3df",
  axis: "#52514e",
};
const DARK = {
  forecast: "#3987e5",
  actual: "#d95926",
  bar: "#3987e5",
  grid: "#33332f",
  axis: "#c3c2b7",
};

const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

export function useChartColors() {
  const [dark, setDark] = useState(darkQuery.matches);
  useEffect(() => {
    const onChange = (event) => setDark(event.matches);
    darkQuery.addEventListener("change", onChange);
    return () => darkQuery.removeEventListener("change", onChange);
  }, []);
  return dark ? DARK : LIGHT;
}

// Number formatting helpers.
export const mw = (value) => (value == null ? "–" : `${Math.round(value).toLocaleString("en-GB")} MW`);
export const signedMw = (value) => (value == null ? "–" : `${value > 0 ? "+" : ""}${mw(value)}`);
export const signedNum = (value) => `${value > 0 ? "+" : ""}${Math.round(value).toLocaleString("en-GB")}`;
export const gw = (value) => `${(value / 1000).toLocaleString("en-GB", { maximumFractionDigits: 1 })} GW`;
export const ukDateTime = (iso) =>
  new Date(iso).toLocaleString("en-GB", {
    timeZone: "Europe/London",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
