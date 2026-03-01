from fastapi import APIRouter
from pydantic import BaseModel
import os
import joblib
import torch
import pandas as pd

from backend.ml.LogisticRegression import LogisticRegressionModel
from backend.ml.preprocessor import GrowthPreprocessor

router = APIRouter()

# Globals
model = None
preproc = None


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


@router.on_event("startup")
def load_model_and_preprocessor():
    global model, preproc

    here = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(here, "data", "models")

    model_path = os.path.join(models_dir, "model.pt")
    preproc_path = os.path.join(models_dir, "preprocessor.pkl")

    # Load preprocessor (dict) and rebuild GrowthPreprocessor
    preproc_data = joblib.load(preproc_path)

    preproc_obj = GrowthPreprocessor()
    preproc_obj.numeric_cols = preproc_data["numeric_cols"]
    preproc_obj.feature_cols = preproc_data["feature_cols"]
    preproc_obj.scaler = preproc_data["scaler"]

    preproc = preproc_obj

    # Load model with correct input dim
    input_dim = len(preproc_obj.feature_cols)
    logistic_model = LogisticRegressionModel(input_dim)
    logistic_model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
    logistic_model.eval()

    model = logistic_model


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
    x_new = torch.tensor(X_new_df.to_numpy(dtype=float), dtype=torch.float32)

    with torch.no_grad():
        output = model(x_new)
        prob = output.item()

    weights = model.linear.weight.detach().cpu().flatten()
    coef_values = weights.tolist()
    coef = pd.Series(coef_values, index=preproc.feature_cols, dtype=float)

    positive_factor = coef.idxmax()
    negative_factor = coef.idxmin()
    predicted_class = int(prob >= 0.5)

    return {
        "predicted_probability": round(prob, 4),
        "predicted_class": "Success" if predicted_class == 1 else "Failure",
        "positive_factor": positive_factor,
        "negative_factor": negative_factor,
    }
