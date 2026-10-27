import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getAccuracy, useApi } from "../api.js";
import { mw, signedMw, signedNum, useChartColors } from "../theme.js";
import ChartCard, { Status } from "./ChartCard.jsx";
import KpiCard from "./KpiCard.jsx";

const shortDate = (iso) => new Date(`${iso}T12:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "short" });

// Round ticks every 2,000 MW across the histogram's range.
function histogramTicks(bins) {
  if (!bins.length) return [];
  const ticks = [];
  for (let tick = Math.ceil(bins[0].from / 2000) * 2000; tick <= bins[bins.length - 1].to; tick += 2000) {
    ticks.push(tick);
  }
  return ticks;
}

// Shared tooltip: title line + any number of "label: value" rows.
function SimpleTooltip({ active, payload, title, rows }) {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;
  return (
    <div className="tooltip">
      <strong>{title(item)}</strong>
      {rows(item).map(([label, value]) => (
        <div key={label}>
          {label}: {value}
        </div>
      ))}
    </div>
  );
}

function MwBarChart({ data, xKey, xFormat, colors, tooltip, height = 260 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 10, right: 16, bottom: 0, left: 8 }}>
        <CartesianGrid stroke={colors.grid} vertical={false} />
        <XAxis dataKey={xKey} tickFormatter={xFormat} tick={{ fill: colors.axis, fontSize: 12 }} />
        <YAxis
          tickFormatter={(value) => value.toLocaleString("en-GB")}
          tick={{ fill: colors.axis, fontSize: 12 }}
          width={56}
        />
        <Tooltip content={tooltip} cursor={{ fill: colors.grid, opacity: 0.5 }} />
        <Bar isAnimationActive={false} dataKey="mae" fill={colors.bar} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export default function AccuracyView({ cutoffHour }) {
  const colors = useChartColors();
  const { data, loading, error } = useApi(() => getAccuracy(cutoffHour), [cutoffHour]);
  if (!data) return <Status loading={loading} error={error} />;

  const s = data.summary;
  const fix = data.bias_correction;
  const worstDay = [...data.daily].sort((a, b) => b.mae - a.mae)[0];
  const histogram = data.histogram.map((bin) => ({ ...bin, mid: (bin.from + bin.to) / 2 }));

  return (
    <div className="view">
      <p className="banner">
        Every delivery hour from 2 Jan to 1 Feb 2026 ({s.count} hours), scored using only the forecast that was
        available at {String(cutoffHour).padStart(2, "0")}:00 the day before.
      </p>

      <div className="kpis">
        <KpiCard label="Average miss (MAE)" value={mw(s.mae)} note={`${s.nmae_pct}% of average wind output`} />
        <KpiCard
          label="Bias"
          value={signedMw(s.bias)}
          note={s.bias < 0 ? "forecast is too high on average" : "forecast is too low on average"}
        />
        <KpiCard
          label="80% error range (P10 to P90)"
          value={`${signedNum(s.p10)} / ${signedNum(s.p90)}`}
          note="MW, actual − forecast"
        />
        <KpiCard label="Worst single hour" value={mw(s.max_abs_error)} note={`RMSE ${mw(s.rmse)}`} />
      </div>

      <section className="insight">
        <h3>What this means for buying</h3>
        <ul>
          <li>
            In 1 hour out of 10, wind came in more than <strong>{mw(-s.p10)}</strong> below the forecast. That is
            the shortfall to cover with extra purchases or reserve.
          </li>
          <li>
            The forecast ran <strong>{s.bias < 0 ? "high" : "low"}</strong> by <strong>{mw(Math.abs(s.bias))}</strong>{" "}
            on average. A likely cause is wind being curtailed (turned down) by the grid, which the forecast does
            not include.
          </li>
          {fix?.raw_mae && (
            <li>
              Correcting each day by the average bias of the <em>previous</em> days cuts the average miss from{" "}
              {mw(fix.raw_mae)} to <strong>{mw(fix.corrected_mae)}</strong> ({fix.improvement_pct}% better), with no
              look-ahead.
            </li>
          )}
          <li>
            The hardest day was <strong>{shortDate(worstDay.date)}</strong>, with an average miss of {mw(worstDay.mae)}.
          </li>
        </ul>
      </section>

      <div className="grid">
        <ChartCard title="Average miss by delivery day" subtitle="MAE per day, MW. Tall bars are days to investigate.">
          <MwBarChart
            data={data.daily}
            xKey="date"
            xFormat={shortDate}
            colors={colors}
            tooltip={
              <SimpleTooltip
                title={(d) => shortDate(d.date)}
                rows={(d) => [
                  ["Average miss", mw(d.mae)],
                  ["Bias", signedMw(d.bias)],
                  ["Average actual", mw(d.mean_actual)],
                ]}
              />
            }
          />
        </ChartCard>

        <ChartCard
          title="Average miss by forecast lead time"
          subtitle="All forecast runs. Forecasts made further ahead miss by more."
        >
          <MwBarChart
            data={data.by_horizon}
            xKey="horizon"
            colors={colors}
            tooltip={
              <SimpleTooltip
                title={(d) => `${d.horizon} ahead`}
                rows={(d) => [
                  ["Average miss", mw(d.mae)],
                  ["Hours scored", d.count.toLocaleString("en-GB")],
                ]}
              />
            }
          />
        </ChartCard>

        <ChartCard title="Average miss by hour of day" subtitle="UK time. Shows which hours are hardest to forecast.">
          <MwBarChart
            data={data.by_hour}
            xKey="hour"
            xFormat={(hour) => `${String(hour).padStart(2, "0")}h`}
            colors={colors}
            tooltip={
              <SimpleTooltip
                title={(d) => `${String(d.hour).padStart(2, "0")}:00`}
                rows={(d) => [
                  ["Average miss", mw(d.mae)],
                  ["Bias", signedMw(d.bias)],
                ]}
              />
            }
          />
        </ChartCard>

        <ChartCard title="How big are the errors?" subtitle="Number of hours per 500 MW error bin. Left of 0 = forecast too high.">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={histogram} margin={{ top: 10, right: 16, bottom: 0, left: 8 }} barCategoryGap={2}>
              <CartesianGrid stroke={colors.grid} vertical={false} />
              <XAxis
                dataKey="mid"
                type="number"
                domain={["dataMin - 250", "dataMax + 250"]}
                ticks={histogramTicks(histogram)}
                tickFormatter={(value) => (value === 0 ? "0" : `${value / 1000}k`)}
                tick={{ fill: colors.axis, fontSize: 12 }}
              />
              <YAxis tick={{ fill: colors.axis, fontSize: 12 }} width={40} />
              <Tooltip
                cursor={{ fill: colors.grid, opacity: 0.5 }}
                content={
                  <SimpleTooltip
                    title={(d) => `${signedMw(d.from)} to ${signedMw(d.to)}`}
                    rows={(d) => [["Hours", d.count]]}
                  />
                }
              />
              <ReferenceLine x={0} stroke={colors.axis} strokeDasharray="4 4" />
              <Bar isAnimationActive={false} dataKey="count" fill={colors.bar} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
