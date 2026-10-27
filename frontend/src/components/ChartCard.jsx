// A titled box that holds one chart.
export default function ChartCard({ title, subtitle, children }) {
  return (
    <section className="card">
      <h3>{title}</h3>
      {subtitle && <p className="card-subtitle">{subtitle}</p>}
      <div className="chart">{children}</div>
    </section>
  );
}

export function Status({ loading, error }) {
  if (error) return <p className="status error">Could not load data: {error}</p>;
  if (loading) return <p className="status">Loading…</p>;
  return null;
}
