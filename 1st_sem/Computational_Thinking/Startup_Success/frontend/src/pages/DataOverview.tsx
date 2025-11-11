import "./pages.css";

const keyMetrics = [
  { label: "Avg. Success Rate", value: "38%" },
  { label: "Median Funding", value: "$4.2M" },
  { label: "Median Age", value: "2.7 yrs" },
  { label: "Avg. Burn Rate", value: "$180K / mo" }
];

const topSignals = [
  "Recurring revenue and low burn correlates with success.",
  "Founders with >5 years experience fare 22% better.",
  "Market size above $1B greatly increases investor interest."
];

const DataOverview = () => (
  <section className="panel">
    <header className="panel__header">
      <h1>Portfolio Overview</h1>
      <p>High-level signals extracted from the historical training dataset.</p>
    </header>
    <div className="metrics-grid">
      {keyMetrics.map((metric) => (
        <article className="metric-card" key={metric.label}>
          <span className="metric-label">{metric.label}</span>
          <span className="metric-value">{metric.value}</span>
        </article>
      ))}
    </div>
    <section className="insights">
      <h2>Headline Insights</h2>
      <ul>
        {topSignals.map((signal) => (
          <li key={signal}>{signal}</li>
        ))}
      </ul>
    </section>
  </section>
);

export default DataOverview;
