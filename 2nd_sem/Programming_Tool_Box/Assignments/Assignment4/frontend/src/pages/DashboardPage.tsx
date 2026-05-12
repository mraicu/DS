import { FormEvent, useEffect, useState } from "react";

import {
  getDatasetDescribe,
  getDatasetDtypes,
  getDatasetHead,
  getDatasetShape,
  getDatasetTail,
  getSummary,
  predictScore,
  PredictionRequest,
  SummaryResponse,
} from "../api";

type DashboardPageProps = {
  session: { token: string; username: string; email: string };
  onLogout: () => void;
};

const initialForm: PredictionRequest = {
  social_support: 1,
  healthy_life_expectancy: 1,
  log_gdp_per_capita: 1,
  freedom: 1,
};

const fieldLabels: Record<keyof PredictionRequest, string> = {
  social_support: "Social support",
  healthy_life_expectancy: "Healthy life expectancy",
  log_gdp_per_capita: "Log of GDP per capita",
  freedom: "Freedom",
};

const fieldRanges: Record<keyof PredictionRequest, { min: number; max: number }> = {
  social_support: { min: 1, max: 155 },
  healthy_life_expectancy: { min: 1, max: 150 },
  log_gdp_per_capita: { min: 1, max: 152 },
  freedom: { min: 1, max: 155 },
};

export function DashboardPage({ session, onLogout }: DashboardPageProps) {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [shape, setShape] = useState<{ rows: number; columns: number } | null>(null);
  const [tableRows, setTableRows] = useState<Record<string, unknown>[]>([]);
  const [tableTitle, setTableTitle] = useState("Dataset preview");
  const [nHead, setNHead] = useState(5);
  const [nTail, setNTail] = useState(5);
  const [form, setForm] = useState<PredictionRequest>(initialForm);
  const [prediction, setPrediction] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [datasetError, setDatasetError] = useState("");

  useEffect(() => {
    Promise.all([getSummary(session.token), getDatasetShape(session.token)])
      .then(([summaryResponse, shapeResponse]) => {
        setSummary(summaryResponse);
        setShape(shapeResponse);
      })
      .catch(() => {
        onLogout();
      });
  }, [session.token, onLogout]);

  async function handlePredict(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      const result = await predictScore(session.token, form);
      setPrediction(result.predicted_score);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prediction failed");
    }
  }

  async function showDtypes() {
    setDatasetError("");
    try {
      const result = await getDatasetDtypes(session.token);
      setTableTitle("Column names and data types");
      setTableRows(result.rows);
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : "Failed to load column types");
    }
  }

  async function showHead() {
    setDatasetError("");
    try {
      const result = await getDatasetHead(session.token, nHead);
      setTableTitle(`First ${nHead} rows`);
      setTableRows(result.rows);
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : "Failed to load first rows");
    }
  }

  async function showTail() {
    setDatasetError("");
    try {
      const result = await getDatasetTail(session.token, nTail);
      setTableTitle(`Last ${nTail} rows`);
      setTableRows(result.rows);
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : "Failed to load last rows");
    }
  }

  async function showDescribe() {
    setDatasetError("");
    try {
      const result = await getDatasetDescribe(session.token);
      setTableTitle("Basic dataset statistics");
      setTableRows(result.rows);
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : "Failed to load statistics");
    }
  }

  const tableColumns = tableRows.length > 0 ? Object.keys(tableRows[0]) : [];

  return (
    <main className="page dashboard-page">
      <header className="topbar">
        <div>
          <h1>Dashboard</h1>
          <p>
            Logged in as <strong>{session.username}</strong>
          </p>
        </div>
        <button onClick={onLogout}>Log out</button>
      </header>

      <section className="stats-grid">
        <article className="card">
          <h3>Total records</h3>
          <p>{summary?.records ?? "..."}</p>
        </article>
        <article className="card">
          <h3>Average score</h3>
          <p>{summary?.average_score ?? "..."}</p>
        </article>
        <article className="card">
          <h3>Top country</h3>
          <p>{summary ? `${summary.top_country} (${summary.top_score})` : "..."}</p>
        </article>
      </section>

      <section className="card dataset-card">
        <h2>Dataset Tools</h2>
        <p>
          Rows: <strong>{shape?.rows ?? "..."}</strong> | Columns: <strong>{shape?.columns ?? "..."}</strong>
        </p>

        <div className="dataset-actions">
          <button type="button" onClick={showDtypes}>
            Show columns and types
          </button>

          <div className="inline-action">
            <input type="number" min={1} value={nHead} onChange={(event) => setNHead(Number(event.target.value) || 1)} />
            <button type="button" onClick={showHead}>
              Show first N rows
            </button>
          </div>

          <div className="inline-action">
            <input type="number" min={1} value={nTail} onChange={(event) => setNTail(Number(event.target.value) || 1)} />
            <button type="button" onClick={showTail}>
              Show last N rows
            </button>
          </div>

          <button type="button" onClick={showDescribe}>
            Show basic statistics
          </button>
        </div>

        <h3>{tableTitle}</h3>
        {tableRows.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {tableColumns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableRows.map((row, index) => (
                  <tr key={index}>
                    {tableColumns.map((column) => (
                      <td key={`${index}-${column}`}>{String(row[column] ?? "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {datasetError && <p className="error">{datasetError}</p>}
      </section>

      <section className="card predict-card">
        <h2>Predict Happiness Score</h2>
        <p>Adjust the indicators and estimate the happiness score.</p>
        <p className="hint">Use values within the ranges shown for each field.</p>

        <form onSubmit={handlePredict} className="form-grid two-columns">
          {Object.entries(form).map(([key, value]) => (
            <label key={key}>
              {fieldLabels[key as keyof PredictionRequest]} (
              {fieldRanges[key as keyof PredictionRequest].min} - {fieldRanges[key as keyof PredictionRequest].max})
              <input
                type="number"
                step="1"
                min={fieldRanges[key as keyof PredictionRequest].min}
                max={fieldRanges[key as keyof PredictionRequest].max}
                value={value}
                onChange={(event) =>
                  setForm((prev) => ({
                    ...prev,
                    [key]: Number(event.target.value),
                  }))
                }
              />
            </label>
          ))}

          <button type="submit">Predict</button>
        </form>

        {prediction !== null && <p className="prediction-result">Predicted score: {prediction}</p>}
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  );
}
