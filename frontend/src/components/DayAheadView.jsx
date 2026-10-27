import { useState } from "react";
import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getDayAhead, useApi } from "../api.js";
import { gw, mw, signedMw, ukDateTime, useChartColors } from "../theme.js";
import ChartCard, { Status } from "./ChartCard.jsx";
import KpiCard from "./KpiCard.jsx";

function shiftDate(iso, days) {
  const date = new Date(`${iso}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function DayTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="tooltip">
      <strong>{point.hour_uk}</strong>
      <div>Forecast: {mw(point.forecast)}</div>
      <div>Actual: {mw(point.actual)}</div>
      <div>Error: {signedMw(point.error)}</div>
      <div className="muted">
        Likely range: {mw(point.band_low)} – {mw(point.band_high)}
      </div>
      <div className="muted">Forecast made {point.horizon_h}h ahead</div>
    </div>
  );
}

export default function DayAheadView({ meta, cutoffHour }) {
  const colors = useChartColors();
  const [date, setDate] = useState("2026-01-15");
  const { data, loading, error } = useApi(() => getDayAhead(date, cutoffHour), [date, cutoffHour]);

  const canGoBack = date > meta.delivery_start;
  const canGoForward = date < meta.delivery_end;
  const summary = data?.summary;
  const missingHours = data ? 24 - data.points.length : 0;

  return (
    <div className="view">
      <div className="toolbar">
        <button onClick={() => setDate(shiftDate(date, -1))} disabled={!canGoBack} aria-label="Previous day">
          ←
        </button>
        <label className="control">
          Delivery day
          <input
            type="date"
            value={date}
            min={meta.delivery_start}
            max={meta.delivery_end}
            onChange={(event) => event.target.value && setDate(event.target.value)}
          />
        </label>
        <button onClick={() => setDate(shiftDate(date, 1))} disabled={!canGoForward} aria-label="Next day">
          →
        </button>
      </div>

      <Status loading={loading && !data} error={error} />

      {data && (
        <>
          <p className="banner">
            {data.forecast_published ? (
              <>
                Showing the forecast published <strong>{ukDateTime(data.forecast_published)}</strong>, the latest
                one available at your decision time of <strong>{ukDateTime(data.cutoff)}</strong>.
              </>
            ) : (
              <>No forecast was published before {ukDateTime(data.cutoff)}.</>
            )}
            {missingHours > 0 && (
              <> {missingHours} late hour(s) were not covered by any forecast available at that time.</>
            )}
          </p>

          {summary?.count > 0 && (
            <div className="kpis">
              <KpiCard label="Average forecast" value={mw(summary.mean_forecast)} note="what you planned on" />
              <KpiCard label="Average actual" value={mw(summary.mean_actual)} note="what the wind delivered" />
              <KpiCard
                label="Average miss (MAE)"
                value={mw(summary.mae)}
                note={`${summary.nmae_pct}% of actual output`}
              />
              <KpiCard
                label="Bias"
                value={signedMw(summary.bias)}
                note={summary.bias < 0 ? "forecast was too high" : "forecast was too low"}
              />
            </div>
          )}

          <ChartCard
            title={`Wind generation on ${new Date(`${date}T12:00:00Z`).toLocaleDateString("en-GB", {
              weekday: "long",
              day: "numeric",
              month: "long",
              year: "numeric",
            })}`}
            subtitle={`Shaded band: where the actual landed 80% of the time in January, given this forecast (${signedMw(
              data.band.p10
            )} to ${signedMw(data.band.p90)}).`}
          >
            <ResponsiveContainer width="100%" height={360}>
              <ComposedChart data={data.points} margin={{ top: 10, right: 16, bottom: 0, left: 8 }}>
                <CartesianGrid stroke={colors.grid} vertical={false} />
                <XAxis dataKey="hour_uk" tick={{ fill: colors.axis, fontSize: 12 }} interval={2} />
                <YAxis tickFormatter={gw} tick={{ fill: colors.axis, fontSize: 12 }} width={68} domain={[0, "auto"]} />
                <Tooltip content={<DayTooltip />} />
                <Legend />
                <Area
                  name="Likely range (P10–P90)"
                  dataKey={(point) => [point.band_low, point.band_high]}
                  fill={colors.forecast}
                  fillOpacity={0.12}
                  stroke="none"
                  isAnimationActive={false}
                />
                <Line isAnimationActive={false} name="Forecast" dataKey="forecast" stroke={colors.forecast} strokeWidth={2} dot={false} />
                <Line isAnimationActive={false} name="Actual" dataKey="actual" stroke={colors.actual} strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </ChartCard>
        </>
      )}
    </div>
  );
}
