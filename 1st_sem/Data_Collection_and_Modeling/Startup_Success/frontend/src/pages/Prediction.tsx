import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { API_BASE_URL } from "../config";
import { PredictionResponse, StartupInput } from "../types/prediction";
import "./pages.css";

const industries = [
    "IoT",
    "FinTech",
    "HealthTech",
    "EdTech",
    "E-Commerce",
    "Cybersecurity",
    "Gaming",
];

const regions = ["Europe", "North America", "South America", "Australia"];

const exitStatuses = ["Private", "IPO"];

const defaultForm: StartupInput = {
    startup_name: "My Startup",
    industry: "IoT",
    funding_rounds: 1,
    funding_amount_musd: 101.09,
    valuation_musd: 844.75,
    revenue_musd: 67.87,
    employees: 1468,
    market_share_pct: 5.2,
    year_founded: 2006,
    region: "Europe",
    exit_status: "Private",
};

const Prediction = () => {
    const [form, setForm] = useState<StartupInput>(defaultForm);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<PredictionResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const probabilityPct = useMemo(() => {
        if (!result) return "0.0";
        return (result.predicted_probability * 100).toFixed(1);
    }, [result]);

    const handleChange = (
        event: ChangeEvent<HTMLInputElement | HTMLSelectElement>
    ) => {
        const { name, value } = event.target;

        setForm((prev) => ({
            ...prev,
            [name]:
                typeof prev[name as keyof StartupInput] === "number"
                    ? Number(value)
                    : value,
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
                body: JSON.stringify(form),
            });

            if (!response.ok) {
                throw new Error(`Prediction failed (${response.status})`);
            }

            const payload: PredictionResponse = await response.json();
            setResult(payload);
        } catch (err) {
            const message =
                err instanceof Error ? err.message : "Unknown error";
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <section className="panel">
            <header className="panel__header">
                <h1>Predict Startup Success</h1>
                <p>
                    Submit the latest metrics to run a profitability forecast.
                </p>
            </header>

            <form className="form-grid" onSubmit={handleSubmit}>
                <label>
                    <span>Startup Name</span>
                    <input
                        type="text"
                        name="startup_name"
                        value={form.startup_name}
                        onChange={handleChange}
                    />
                </label>

                <label>
                    <span>Industry</span>
                    <select
                        name="industry"
                        value={form.industry}
                        onChange={handleChange}
                    >
                        {industries.map((industry) => (
                            <option key={industry} value={industry}>
                                {industry}
                            </option>
                        ))}
                    </select>
                </label>

                <label>
                    <span>Funding Rounds</span>
                    <input
                        type="number"
                        name="funding_rounds"
                        min={0}
                        step={1}
                        value={form.funding_rounds}
                        onChange={handleChange}
                    />
                </label>

                <label>
                    <span>Funding Amount (M USD)</span>
                    <input
                        type="number"
                        name="funding_amount_musd"
                        min={0}
                        step={0.01}
                        value={form.funding_amount_musd}
                        onChange={handleChange}
                    />
                </label>

                <label>
                    <span>Valuation (M USD)</span>
                    <input
                        type="number"
                        name="valuation_musd"
                        min={0}
                        step={0.01}
                        value={form.valuation_musd}
                        onChange={handleChange}
                    />
                </label>

                <label>
                    <span>Revenue (M USD)</span>
                    <input
                        type="number"
                        name="revenue_musd"
                        min={0}
                        step={0.01}
                        value={form.revenue_musd}
                        onChange={handleChange}
                    />
                </label>

                <label>
                    <span>Employees</span>
                    <input
                        type="number"
                        name="employees"
                        min={1}
                        step={1}
                        value={form.employees}
                        onChange={handleChange}
                    />
                </label>

                <label>
                    <span>Market Share (%)</span>
                    <input
                        type="number"
                        name="market_share_pct"
                        min={0}
                        max={100}
                        step={0.1}
                        value={form.market_share_pct}
                        onChange={handleChange}
                    />
                </label>

                <label>
                    <span>Year Founded</span>
                    <input
                        type="number"
                        name="year_founded"
                        min={1900}
                        max={2100}
                        step={1}
                        value={form.year_founded}
                        onChange={handleChange}
                    />
                </label>

                <label>
                    <span>Region</span>
                    <select
                        name="region"
                        value={form.region}
                        onChange={handleChange}
                    >
                        {regions.map((region) => (
                            <option key={region} value={region}>
                                {region}
                            </option>
                        ))}
                    </select>
                </label>

                <label>
                    <span>Exit Status</span>
                    <select
                        name="exit_status"
                        value={form.exit_status}
                        onChange={handleChange}
                    >
                        {exitStatuses.map((status) => (
                            <option key={status} value={status}>
                                {status}
                            </option>
                        ))}
                    </select>
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
                        <p className="result-card__label">
                            Success Probability
                        </p>
                        <p className="result-card__value">{probabilityPct}%</p>
                        <p className="result-card__pill">
                            {result.predicted_class}
                        </p>
                    </div>
                    <div className="result-card__factors">
                        <div>
                            <span className="factor-label">
                                Most Positive Signal
                            </span>
                            <strong>{result.positive_factor}</strong>
                        </div>
                        <div>
                            <span className="factor-label">
                                Most Negative Signal
                            </span>
                            <strong>{result.negative_factor}</strong>
                        </div>
                    </div>
                </section>
            )}
        </section>
    );
};

export default Prediction;
