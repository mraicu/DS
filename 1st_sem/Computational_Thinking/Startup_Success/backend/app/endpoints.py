from backend.ml.LogisticRegression import LogisticRegressionModel

from fastapi import APIRouter
from pydantic import BaseModel
import torch
import pandas as pd
import os


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


# Global model and column variables
model = None
training_columns = None


@router.on_event("startup")
def load_model_once():
    """Load model and column schema at startup."""
    global model, training_columns

    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, "..", "app", "data", "models"))
    model_path = os.path.join(repo_root, "model.pt")
    data_path = os.path.abspath(os.path.join(here, "..", "app", "data", "startup_failure_prediction.csv"))

    # Load reference data for column schema
    df = pd.read_csv(data_path)
    target_col = "Startup_Status"
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
    weights = model.linear.weight.detach().cpu().flatten()      # stays in torch land, no numpy bridge
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
