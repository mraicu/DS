from backend.ml.LogisticRegression import LogisticRegressionModel

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import torch
import pandas as pd
import os
from typing import List, Optional


router = APIRouter()


# --- Define input schema ---
class StartupInput(BaseModel):
    Industry: str
    Startup_Age: float
    Funding_Amount: float
    Number_of_Founders: float
    Founder_Experience: float
    Employees_Count: float
    Revenue: float
    Burn_Rate: float
    Market_Size: str
    Business_Model: str
    Product_Uniqueness_Score: float
    Customer_Retention_Rate: float
    Marketing_Expense: float


class TrendSummary(BaseModel):
    domain: str
    cagr_pct: float
    time_to_peak_months: float
    recent_6m_slope: float
    volatility: float


# Global model and column variables
model = None
training_columns = None


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


@router.on_event("startup")
def load_model_once():
    """Load model and column schema at startup."""
    global model, training_columns

    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, "..", "app", "data", "models"))
    model_path = os.path.join(repo_root, "model.pt")
    data_path = os.path.abspath(os.path.join(here, "..", "app", "data", "startup_growth_processed.csv"))

    # Load reference data for column schema
    df = pd.read_csv(data_path)
    target_col = "Profitable"
    drop_cols = [c for c in ["Startup_Name"] if c in df.columns]
    X_df = df.drop(columns=[target_col] + drop_cols)
    X_df = pd.get_dummies(X_df, drop_first=True)
    X_df = X_df.apply(pd.to_numeric, errors="coerce").fillna(0)
    training_columns = X_df.columns.tolist()

    # Load trained model
    input_dim = len(training_columns)
    model = LogisticRegressionModel(input_dim)
    model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
    model.eval()

    print("Model and schema loaded successfully.")


@router.post("/predict")
def predict_success(input_data: StartupInput):
    """Predict startup success probability and identify key influencing factors."""
    if model is None or training_columns is None:
        return {"error": "Model not loaded. Please ensure the startup event is triggered."}

    # Convert input to DataFrame
    new_df = pd.DataFrame([input_data.dict()])

    # Apply same preprocessing as training
    new_df = pd.get_dummies(new_df, drop_first=True)
    new_df = new_df.reindex(columns=training_columns, fill_value=0)
    new_df = new_df.apply(pd.to_numeric, errors="coerce").fillna(0)

    # Convert to tensor
    x_new = torch.tensor(new_df.to_numpy(dtype=float), dtype=torch.float32)

    # Predict
    with torch.no_grad():
        output = model(x_new)
        prob = output.item()

    # Extract coefficients
    weights = model.linear.weight.detach().cpu().flatten()      # stays in torch land
    coef_values = weights.tolist()                               # pure Python list
    coef = pd.Series(coef_values, index=training_columns, dtype=float)

    positive_factor = coef.idxmax()
    negative_factor = coef.idxmin()
    predicted_class = int(prob >= 0.5)

    return {
        "predicted_probability": round(prob, 4),
        "predicted_class": "Success" if predicted_class == 1 else "Failure",
        "positive_factor": positive_factor,
        "negative_factor": negative_factor
    }


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
