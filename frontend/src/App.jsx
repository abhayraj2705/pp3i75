import { useState } from "react";
import { getMeta, useApi } from "./api.js";
import AccuracyView from "./components/AccuracyView.jsx";
import DayAheadView from "./components/DayAheadView.jsx";
import { Status } from "./components/ChartCard.jsx";

const TABS = [
  { id: "day-ahead", label: "Day-ahead forecast" },
  { id: "accuracy", label: "Forecast accuracy" },
];
const HOURS = Array.from({ length: 24 }, (_, hour) => hour);

export default function App() {
  const meta = useApi(getMeta, []);
  // The tab lives in the URL hash so a view can be linked to directly (e.g. /#accuracy).
  const [tab, setTabState] = useState(() => (window.location.hash === "#accuracy" ? "accuracy" : "day-ahead"));
  const setTab = (id) => {
    window.location.hash = id;
    setTabState(id);
  };
  const [cutoffHour, setCutoffHour] = useState(10);

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>GB Wind Forecast Monitor</h1>
          <p className="subtitle">
            National wind generation · Elexon BMRS · purchase decisions made in January 2026
          </p>
        </div>
        <label className="control">
          Decision time (day before delivery, UK)
          <select value={cutoffHour} onChange={(event) => setCutoffHour(Number(event.target.value))}>
            {HOURS.map((hour) => (
              <option key={hour} value={hour}>
                {String(hour).padStart(2, "0")}:00
              </option>
            ))}
          </select>
        </label>
      </header>

      <nav className="tabs" role="tablist">
        {TABS.map((item) => (
          <button
            key={item.id}
            role="tab"
            aria-selected={tab === item.id}
            className={tab === item.id ? "tab active" : "tab"}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <main>
        <Status loading={meta.loading} error={meta.error} />
        {meta.data && tab === "day-ahead" && <DayAheadView meta={meta.data} cutoffHour={cutoffHour} />}
        {meta.data && tab === "accuracy" && <AccuracyView cutoffHour={cutoffHour} />}
      </main>

      <footer className="footer">
        Forecast = Elexon WINDFOR, latest run published before the decision time. Actual = Elexon FUELHH
        (fuel type WIND), compared on the hour. Error = actual − forecast.
      </footer>
    </div>
  );
}
