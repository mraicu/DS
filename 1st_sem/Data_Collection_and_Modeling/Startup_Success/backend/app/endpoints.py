
from pydantic import BaseModel
import os
import joblib
import pandas as pd

from backend.ml.XGBoost import XGBoostModel
from backend.ml.preprocessor import GrowthPreprocessor

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional


router = APIRouter()


class StartupInput(BaseModel):
    startup_name: str
    industry: str
    funding_rounds: int
    funding_amount_musd: float
    valuation_musd: float
    revenue_musd: float
    employees: int
    market_share_pct: float
    year_founded: int
    region: str
    exit_status: str


class TrendSummary(BaseModel):
    domain: str
    cagr_pct: float
    time_to_peak_months: float
    recent_6m_slope: float
    volatility: float


# Global model and column variables
model = None
training_columns = None


@router.on_event("startup")
def load_model_and_preprocessor():
    global model, preproc

    here = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(here, "data", "models")

    model_path = os.path.join(models_dir, "model_xgboost.pt")
    preproc_path = os.path.join(models_dir, "preprocessor.pkl")

    # Load preprocessor (dict) and rebuild GrowthPreprocessor
    preproc_data = joblib.load(preproc_path)

    preproc_obj = GrowthPreprocessor()
    preproc_obj.numeric_cols = preproc_data["numeric_cols"]
    preproc_obj.feature_cols = preproc_data["feature_cols"]
    preproc_obj.scaler = preproc_data["scaler"]

    preproc = preproc_obj

    # Load XGBoost model
    model = XGBoostModel()
    model.model = joblib.load(model_path)


@router.post("/predict")
def predict_success(input_data: StartupInput):
    """Predict startup success probability and identify key influencing factors."""
    if model is None or preproc is None:
        return {"error": "Model or preprocessor not loaded."}

    # Convert input to DataFrame in original training schema
    new_df_raw = pd.DataFrame([input_data.dict()])
    new_df_raw = new_df_raw.rename(columns={
        "startup_name": "Startup Name",
        "industry": "Industry",
        "funding_rounds": "Funding Rounds",
        "funding_amount_musd": "Funding Amount (M USD)",
        "valuation_musd": "Valuation (M USD)",
        "revenue_musd": "Revenue (M USD)",
        "employees": "Employees",
        "market_share_pct": "Market Share (%)",
        "year_founded": "Year Founded",
        "region": "Region",
        "exit_status": "Exit Status",
    })

    X_new_df = preproc.transform(new_df_raw)
    x_new = X_new_df.to_numpy(dtype=float)

    prob = float(model.predict_proba(x_new)[0])

    feature_importances = getattr(model.model, "feature_importances_", None)
    if feature_importances is not None and len(feature_importances) == len(preproc.feature_cols):
        importances = pd.Series(feature_importances, index=preproc.feature_cols, dtype=float)
        positive_factor = importances.idxmax()
        negative_factor = importances.idxmin()
    else:
        positive_factor = None
        negative_factor = None

    predicted_class = int(prob >= 0.5)

    return {
        "predicted_probability": round(prob, 4),
        "predicted_class": "Success" if predicted_class == 1 else "Failure",
        "positive_factor": positive_factor,
        "negative_factor": negative_factor,
    }



# --- Trend metrics helpers ---
def load_trend_df() -> pd.DataFrame:
    """Load the trends summary CSV."""
    here = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(here, "data", "trends_summary_metrics.csv")

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
