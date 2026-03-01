from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from io import BytesIO
import os

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

router = APIRouter()

HERE = os.path.dirname(os.path.abspath(__file__))


# --------- Metrics visualization ----------

class TrendSummary(BaseModel):
    domain: str
    cagr_pct: float
    time_to_peak_months: float
    recent_6m_slope: float
    volatility: float


def load_trend_df() -> pd.DataFrame:
    """Load the trends summary CSV."""
    csv_path = os.path.join(HERE, "data", "trends_summary_metrics.csv")

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="trends_summary_metrics.csv not found")

    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read metrics CSV: {exc}") from exc

    required_cols = {"domain", "cagr_pct", "time_to_peak_months", "recent_6m_slope", "volatility"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(status_code=500, detail="Metrics CSV missing required columns")
    return df


def search_metrics(df: pd.DataFrame, query: Optional[str]) -> pd.DataFrame:
    if not query:
        return df
    return df[df["domain"].str.contains(query, case=False, na=False)]


def filter_metrics(df: pd.DataFrame, domain: Optional[str]) -> pd.DataFrame:
    if not domain:
        return df
    return df[df["domain"].str.lower() == domain.lower()]


def sort_metrics(df: pd.DataFrame, sort_by: str, order: str) -> pd.DataFrame:
    sort_by = sort_by.strip().lower()
    order = order.strip().lower()
    column_map = {
        "domain": "domain",
        "cagr_pct": "cagr_pct",
        "time_to_peak_months": "time_to_peak_months",
        "recent_6m_slope": "recent_6m_slope",
        "volatility": "volatility",
    }
    if sort_by not in column_map:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by '{sort_by}'")
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")
    return df.sort_values(column_map[sort_by], ascending=(order == "asc"))


@router.get("/trend-metrics", response_model=List[TrendSummary])
def get_trend_metrics():
    """Return the full trends table, sorted by CAGR descending."""
    df = load_trend_df()
    df = sort_metrics(df, sort_by="cagr_pct", order="desc")
    return df.to_dict(orient="records")


@router.get("/trend-metrics/search", response_model=List[TrendSummary])
def search_trend_metrics(
    query: str = Query(..., description="Case-insensitive domain search"),
    sort_by: str = Query("cagr_pct", description="Column to sort by"),
    order: str = Query("desc", description="Sort direction: asc|desc"),
    domain: Optional[str] = Query(None, description="Optional exact domain filter"),
):
    """Search trend metrics by domain substring."""
    df = load_trend_df()
    df = search_metrics(df, query=query)
    df = filter_metrics(df, domain=domain)
    df = sort_metrics(df, sort_by=sort_by, order=order)
    return df.to_dict(orient="records")


@router.get("/trend-metrics/filter", response_model=List[TrendSummary])
def filter_trend_metrics(
    domain: str = Query(..., description="Exact domain filter"),
    sort_by: str = Query("cagr_pct", description="Column to sort by"),
    order: str = Query("desc", description="Sort direction: asc|desc"),
    search: Optional[str] = Query(None, description="Optional search term"),
):
    """Filter trend metrics by an exact domain match."""
    df = load_trend_df()
    df = filter_metrics(df, domain=domain)
    df = search_metrics(df, query=search)
    df = sort_metrics(df, sort_by=sort_by, order=order)
    return df.to_dict(orient="records")


@router.get("/trend-metrics/sort", response_model=List[TrendSummary])
def sort_trend_metrics(
    sort_by: str = Query("cagr_pct", description="Column to sort by"),
    order: str = Query("desc", description="Sort direction: asc|desc"),
    search: Optional[str] = Query(None, description="Optional search term"),
    domain: Optional[str] = Query(None, description="Optional domain filter"),
):
    """Sort trend metrics, optionally narrowing by search/filter first."""
    df = load_trend_df()
    df = search_metrics(df, query=search)
    df = filter_metrics(df, domain=domain)
    df = sort_metrics(df, sort_by=sort_by, order=order)
    return df.to_dict(orient="records")


@router.get("/trend-metrics/recent-6m-slope-plot")
def recent_six_month_slope_plot(
    top_n: int = Query(12, ge=1, le=30, description="How many domains to plot"),
):
    """Generate a PNG plot of the strongest recent 6-month slopes."""
    df = load_trend_df()
    df = sort_metrics(df, sort_by="recent_6m_slope", order="desc").head(top_n)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(df["domain"], df["recent_6m_slope"], color="#2563eb")
    ax.invert_yaxis()
    ax.set_xlabel("Recent 6M Slope")
    ax.set_ylabel("Domain")
    ax.set_title(f"Top {len(df)} domains by recent 6M slope")
    ax.grid(axis="x", linestyle="--", linewidth=0.5, alpha=0.6)

    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.1,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.1f}",
            va="center",
            fontsize=8,
            color="#0f172a",
        )

    fig.tight_layout()
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")
