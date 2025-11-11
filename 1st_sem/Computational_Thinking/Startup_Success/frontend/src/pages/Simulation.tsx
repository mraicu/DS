import "./pages.css";

const Simulation = () => (
  <section className="panel">
    <header className="panel__header">
      <h1>Scenario Simulation</h1>
      <p>
        Quickly experiment with what-if scenarios for burn, revenue, and headcount to
        understand the sensitivity of the model.
      </p>
    </header>
    <div className="simulation-grid">
      <article className="sim-card">
        <h2>Reduce Burn</h2>
        <p>See how trimming burn rate by 10% impacts the probability of survival.</p>
        <button type="button">Coming soon</button>
      </article>
      <article className="sim-card">
        <h2>Grow Revenue</h2>
        <p>Project the probability if MRR grows by 20% over the next two quarters.</p>
        <button type="button">Coming soon</button>
      </article>
      <article className="sim-card">
        <h2>Headcount Plan</h2>
        <p>Visualize impact of hiring plans on runway and long-term success odds.</p>
        <button type="button">Coming soon</button>
      </article>
    </div>
  </section>
);

export default Simulation;
