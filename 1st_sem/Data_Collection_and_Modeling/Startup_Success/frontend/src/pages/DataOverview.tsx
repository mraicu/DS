import { useEffect, useState } from "react";
import { API_BASE_URL } from "../config";
import { TrendSummaryMetric } from "../types/trends";
import "./pages.css";

// const keyMetrics = [
//     { label: "Avg. Success Rate", value: "38%" },
//     { label: "Median Funding", value: "$4.2M" },
//     { label: "Median Age", value: "2.7 yrs" },
//     { label: "Avg. Burn Rate", value: "$180 / mo" },
// ];

const columnExplanations = [
    {
        label: "cagr_pct",
        text: "Compound Annual Growth Rate of search interest.",
    },
    {
        label: "time_to_peak_months",
        text: "Months until the maximum popularity is reached.",
    },
    {
        label: "recent_6m_slope",
        text: "Short-term momentum computed over the last 6 months.",
    },
    {
        label: "volatility",
        text: "How bumpy the interest is over time (standard deviation).",
    },
];

const formatPct = (value: number) =>
    Number.isFinite(value) ? `${value.toFixed(2)}%` : "N/A";
const formatMonths = (value: number) =>
    Number.isFinite(value) ? `${value.toFixed(0)} mo` : "N/A";
const formatNumber = (value: number) =>
    Number.isFinite(value) ? value.toFixed(2) : "N/A";

const DataOverview = () => {
    const [metrics, setMetrics] = useState<TrendSummaryMetric[]>([]);
    const [domainOptions, setDomainOptions] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [domainFilter, setDomainFilter] = useState<string>("all");
    const [sortBy, setSortBy] = useState<keyof TrendSummaryMetric>("cagr_pct");
    const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

    // Fetch domain list once for the filter dropdown
    useEffect(() => {
        const fetchDomains = async () => {
            try {
                const response = await fetch(
                    `${API_BASE_URL}/ml/trend-metrics`
                );
                if (!response.ok) return;
                const payload: TrendSummaryMetric[] = await response.json();
                const domainList = Array.from(
                    new Set(payload.map((m) => m.domain))
                ).sort();
                setDomainOptions(domainList);
            } catch {
                /* ignore dropdown load errors */
            }
        };
        fetchDomains();
    }, []);

    useEffect(() => {
        const fetchMetrics = async () => {
            setLoading(true);
            setError(null);
            try {
                const params = new URLSearchParams({
                    sort_by: sortBy,
                    order: sortDir,
                });
                const trimmedSearch = searchTerm.trim();
                let endpoint = `${API_BASE_URL}/ml/trend-metrics/sort`;

                if (trimmedSearch) {
                    endpoint = `${API_BASE_URL}/ml/trend-metrics/search`;
                    params.set("query", trimmedSearch);
                    if (domainFilter !== "all") {
                        params.set("domain", domainFilter);
                    }
                } else if (domainFilter !== "all") {
                    endpoint = `${API_BASE_URL}/ml/trend-metrics/filter`;
                    params.set("domain", domainFilter);
                }

                const response = await fetch(
                    `${endpoint}?${params.toString()}`
                );
                if (!response.ok) {
                    throw new Error(
                        `Failed to load trends (${response.status})`
                    );
                }
                const payload: TrendSummaryMetric[] = await response.json();
                setMetrics(payload);
            } catch (err) {
                const message =
                    err instanceof Error
                        ? err.message
                        : "Unable to load trend metrics.";
                setError(message);
            } finally {
                setLoading(false);
            }
        };

        fetchMetrics();
    }, [sortBy, sortDir, searchTerm, domainFilter]);

    const handleSort = (column: keyof TrendSummaryMetric) => {
        if (sortBy === column) {
            setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
        } else {
            setSortBy(column);
            setSortDir(column === "domain" ? "asc" : "desc");
        }
    };

    const sortIndicator = (column: keyof TrendSummaryMetric) => {
        if (sortBy !== column) return "";
        return sortDir === "asc" ? "▲" : "▼";
    };

    return (
        <section className="panel">
            <header className="panel__header">
                <h1>Portfolio Overview</h1>
            </header>

            {/* <div className="metrics-grid">
                {keyMetrics.map((metric) => (
                    <article className="metric-card" key={metric.label}>
                        <span className="metric-label">{metric.label}</span>
                        <span className="metric-value">{metric.value}</span>
                    </article>
                ))}
            </div> */}

            <section className="table-card">
                <div className="table-card__header">
                    <div>
                        <h2>Trend Summary Metrics</h2>
                        <p>
                            Google Trends growth and volatility by startup
                            domain.
                        </p>
                    </div>
                    <span className="pill">
                        CSV: trends_summary_metrics.csv
                    </span>
                </div>

                <div className="table-actions">
                    <input
                        type="search"
                        placeholder="Search domain..."
                        className="table-search"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    <select
                        className="table-filter"
                        value={domainFilter}
                        onChange={(e) => setDomainFilter(e.target.value)}
                    >
                        <option value="all">All domains</option>
                        {domainOptions.map((domain) => (
                            <option key={domain} value={domain}>
                                {domain}
                            </option>
                        ))}
                    </select>
                </div>

                {loading && (
                    <p className="table-status">Loading trend metrics...</p>
                )}
                {error && <div className="alert alert--error">{error}</div>}

                {!loading && !error && (
                    <>
                        {metrics.length === 0 ? (
                            <p className="table-status">
                                No trend metrics available.
                            </p>
                        ) : (
                            <div className="table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th
                                                role="button"
                                                className="sortable"
                                                onClick={() =>
                                                    handleSort("domain")
                                                }
                                            >
                                                Domain {sortIndicator("domain")}
                                            </th>
                                            <th
                                                role="button"
                                                className="sortable"
                                                onClick={() =>
                                                    handleSort("cagr_pct")
                                                }
                                            >
                                                CAGR {sortIndicator("cagr_pct")}
                                            </th>
                                            <th
                                                role="button"
                                                className="sortable"
                                                onClick={() =>
                                                    handleSort(
                                                        "time_to_peak_months"
                                                    )
                                                }
                                            >
                                                Time to Peak{" "}
                                                {sortIndicator(
                                                    "time_to_peak_months"
                                                )}
                                            </th>
                                            <th
                                                role="button"
                                                className="sortable"
                                                onClick={() =>
                                                    handleSort(
                                                        "recent_6m_slope"
                                                    )
                                                }
                                            >
                                                Recent 6M Slope{" "}
                                                {sortIndicator(
                                                    "recent_6m_slope"
                                                )}
                                            </th>
                                            <th
                                                role="button"
                                                className="sortable"
                                                onClick={() =>
                                                    handleSort("volatility")
                                                }
                                            >
                                                Volatility{" "}
                                                {sortIndicator("volatility")}
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {metrics.map((row) => (
                                            <tr key={row.domain}>
                                                <td>
                                                    <span className="badge">
                                                        {row.domain}
                                                    </span>
                                                </td>
                                                <td>
                                                    {formatPct(row.cagr_pct)}
                                                </td>
                                                <td>
                                                    {formatMonths(
                                                        row.time_to_peak_months
                                                    )}
                                                </td>
                                                <td>
                                                    {formatNumber(
                                                        row.recent_6m_slope
                                                    )}
                                                </td>
                                                <td>
                                                    {formatNumber(
                                                        row.volatility
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </>
                )}
            </section>

            <section className="insights">
                <h2>Metric Definitions</h2>
                <ul>
                    {columnExplanations.map((item) => (
                        <li key={item.label}>
                            <strong>{item.label}</strong> — {item.text}
                        </li>
                    ))}
                </ul>
            </section>
        </section>
    );
};

export default DataOverview;
