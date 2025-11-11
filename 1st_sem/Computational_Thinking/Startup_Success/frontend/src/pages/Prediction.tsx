import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { API_BASE_URL } from "../config";
import { PredictionResponse, StartupInput } from "../types/prediction";
import "./pages.css";

const defaultForm: StartupInput = {
  Industry: "Technology",
  Startup_Age: 2,
  Funding_Amount: 2500000,
  Number_of_Founders: 2,
  Founder_Experience: 5,
  Employees_Count: 15,
  Revenue: 1500000,
  Burn_Rate: 120000,
  Market_Size: "Large",
  Business_Model: "B2B",
  Product_Uniqueness_Score: 7,
  Customer_Retention_Rate: 65,
  Marketing_Expense: 200000
};

const industries = ["Technology", "FinTech", "Health", "Education", "Energy"];
const markets = ["Niche", "Growing", "Large"];
const businessModels = ["B2B", "B2C", "Marketplace", "Subscription"];

const Prediction = () => {
  const [form, setForm] = useState<StartupInput>(defaultForm);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const probabilityPct = useMemo(() => {
    if (!result) return "0.0";
    return (result.predicted_probability * 100).toFixed(1);
  }, [result]);

  const handleChange = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({
      ...prev,
      [name]:
        typeof prev[name as keyof StartupInput] === "number" ? Number(value) : value
    }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/ml/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form)
      });

      if (!response.ok) {
        throw new Error(`Prediction failed (${response.status})`);
      }

      const payload: PredictionResponse = await response.json();
      setResult(payload);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <header className="panel__header">
        <h1>Predict Startup Success</h1>
        <p>Submit the latest operating metrics to run a probability forecast.</p>
      </header>

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          <span>Industry</span>
          <select name="Industry" value={form.Industry} onChange={handleChange}>
            {industries.map((industry) => (
              <option key={industry} value={industry}>
                {industry}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Startup Age (years)</span>
          <input
            type="number"
            name="Startup_Age"
            min={0}
            step={0.1}
            value={form.Startup_Age}
            onChange={handleChange}
          />
        </label>

        <label>
          <span>Funding Amount (USD)</span>
          <input
            type="number"
            name="Funding_Amount"
            min={0}
            step={10000}
            value={form.Funding_Amount}
            onChange={handleChange}
          />
        </label>

        <label>
          <span>Number of Founders</span>
          <input
            type="number"
            name="Number_of_Founders"
            min={1}
            step={1}
            value={form.Number_of_Founders}
            onChange={handleChange}
          />
        </label>

        <label>
          <span>Avg. Founder Experience (years)</span>
          <input
            type="number"
            name="Founder_Experience"
            min={0}
            step={0.5}
            value={form.Founder_Experience}
            onChange={handleChange}
          />
        </label>

        <label>
          <span>Employees Count</span>
          <input
            type="number"
            name="Employees_Count"
            min={1}
            step={1}
            value={form.Employees_Count}
            onChange={handleChange}
          />
        </label>

        <label>
          <span>Revenue (USD)</span>
          <input
            type="number"
            name="Revenue"
            min={0}
            step={1000}
            value={form.Revenue}
            onChange={handleChange}
          />
        </label>

        <label>
          <span>Monthly Burn Rate (USD)</span>
          <input
            type="number"
            name="Burn_Rate"
            min={0}
            step={1000}
            value={form.Burn_Rate}
            onChange={handleChange}
          />
        </label>

        <label>
          <span>Market Size</span>
          <select name="Market_Size" value={form.Market_Size} onChange={handleChange}>
            {markets.map((market) => (
              <option key={market} value={market}>
                {market}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Business Model</span>
          <select
            name="Business_Model"
            value={form.Business_Model}
            onChange={handleChange}
          >
            {businessModels.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Product Uniqueness (0-10)</span>
          <input
            type="number"
            name="Product_Uniqueness_Score"
            min={0}
            max={10}
            step={0.1}
            value={form.Product_Uniqueness_Score}
            onChange={handleChange}
          />
        </label>

        <label>
          <span>Customer Retention (%)</span>
          <input
            type="number"
            name="Customer_Retention_Rate"
            min={0}
            max={100}
            step={0.5}
            value={form.Customer_Retention_Rate}
            onChange={handleChange}
          />
        </label>

        <label>
          <span>Marketing Expense (USD)</span>
          <input
            type="number"
            name="Marketing_Expense"
            min={0}
            step={1000}
            value={form.Marketing_Expense}
            onChange={handleChange}
          />
        </label>

        <div className="form-actions">
          <button type="submit" disabled={loading}>
            {loading ? "Predicting..." : "Run Prediction"}
          </button>
          <button
            type="button"
            className="ghost"
            onClick={() => {
              setForm(defaultForm);
              setResult(null);
              setError(null);
            }}
            disabled={loading}
          >
            Reset
          </button>
        </div>
      </form>

      {error && <div className="alert alert--error">{error}</div>}

      {result && (
        <section className="result-card">
          <div className="result-card__main">
            <p className="result-card__label">Success Probability</p>
            <p className="result-card__value">{probabilityPct}%</p>
            <p className="result-card__pill">{result.predicted_class}</p>
          </div>
          <div className="result-card__factors">
            <div>
              <span className="factor-label">Most Positive Signal</span>
              <strong>{result.positive_factor}</strong>
            </div>
            <div>
              <span className="factor-label">Most Negative Signal</span>
              <strong>{result.negative_factor}</strong>
            </div>
          </div>
        </section>
      )}
    </section>
  );
};

export default Prediction;
