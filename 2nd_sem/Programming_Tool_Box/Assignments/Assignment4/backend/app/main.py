import csv
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder

from app.database import get_db_cursor
from app.schemas import (
    AuthResponse,
    DynamicPredictionRequest,
    LoginRequest,
    MLTrainRequest,
    PredictionRequest,
    PredictionResponse,
    SignUpRequest,
)
from app.security import create_access_token, decode_access_token, hash_password, verify_password

app = FastAPI(title="Happiness Web App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "model" / "happiness_linear_regression.pkl"
DEFAULT_CSV_PATH = BASE_DIR / "data" / "world-happiness-report-2019.csv"
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
MODELS_DIR = BASE_DIR / "model" / "uploads"
FEATURES = [
    "Social support",
    "Healthy life expectancy",
    "Log of GDP per capita",
    "Freedom",
]

load_dotenv()
MODEL = joblib.load(MODEL_PATH)


def init_db() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with get_db_cursor() as (conn, cur):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )
        conn.commit()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def get_current_user(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    with get_db_cursor() as (_, cur):
        cur.execute(
            "SELECT id, username, email FROM users WHERE email = %s",
            (email,),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="User not found")

    return {"id": row[0], "username": row[1], "email": row[2]}


def get_dataset_path(user: dict) -> Path:
    uploaded_path = UPLOADS_DIR / f"user_{user['id']}.csv"
    if uploaded_path.exists():
        return uploaded_path
    return DEFAULT_CSV_PATH


def get_model_artifact_path(user: dict) -> Path:
    return MODELS_DIR / f"user_{user['id']}_model.joblib"


def get_model_metadata_path(user: dict) -> Path:
    return MODELS_DIR / f"user_{user['id']}_metadata.json"


def clear_model_state(user: dict) -> None:
    for path in [get_model_artifact_path(user), get_model_metadata_path(user)]:
        if path.exists():
            path.unlink()


def load_dataset(user: dict) -> pd.DataFrame:
    data = pd.read_csv(get_dataset_path(user))
    if data.empty:
        raise HTTPException(status_code=500, detail="CSV file has no rows")
    return data


def persist_user_dataset(data: pd.DataFrame, user: dict) -> None:
    destination = UPLOADS_DIR / f"user_{user['id']}.csv"
    data.to_csv(destination, index=False)
    clear_model_state(user)


def extract_prediction_ranges(data: pd.DataFrame) -> dict[str, dict[str, float | None]]:
    ranges: dict[str, dict[str, float | None]] = {}
    for feature in FEATURES:
        if feature not in data.columns:
            ranges[feature] = {"min": None, "max": None}
            continue
        numeric_values = pd.to_numeric(data[feature], errors="coerce").dropna()
        if numeric_values.empty:
            ranges[feature] = {"min": None, "max": None}
            continue
        ranges[feature] = {
            "min": round(float(numeric_values.min()), 3),
            "max": round(float(numeric_values.max()), 3),
        }
    return ranges


def get_column_profile(data: pd.DataFrame, column: str) -> dict[str, Any]:
    series = data[column]
    unique_values = series.dropna().astype(str).unique().tolist()
    is_categorical = not is_numeric_dtype(series) or is_bool_dtype(series)
    return {
        "name": column,
        "dtype": str(series.dtype),
        "missing_count": int(series.isna().sum()),
        "unique_count": int(series.nunique(dropna=True)),
        "is_categorical": bool(is_categorical),
        "sample_values": unique_values[:25] if is_categorical else [],
    }


def get_feature_profiles(data: pd.DataFrame, feature_columns: list[str]) -> list[dict[str, Any]]:
    return [get_column_profile(data, column) for column in feature_columns]


def validate_columns_exist(data: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in data.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns in dataset: {', '.join(missing)}")


def build_ml_metadata(
    data: pd.DataFrame,
    training_frame: pd.DataFrame,
    user: dict,
    request: MLTrainRequest,
    encoded_feature_names: list[str],
    categorical_features: list[str],
    target_classes: list[str] | None,
) -> dict[str, Any]:
    return {
        "algorithm_type": request.algorithm_type,
        "feature_columns": request.feature_columns,
        "target_column": request.target_column,
        "categorical_encoding": request.categorical_encoding,
        "categorical_features": categorical_features,
        "encoded_feature_names": encoded_feature_names,
        "feature_profiles": get_feature_profiles(data, request.feature_columns),
        "training_rows": int(len(training_frame)),
        "dataset_name": get_dataset_path(user).name,
        "target_classes": target_classes,
    }


def preprocess_features(
    frame: pd.DataFrame,
    feature_columns: list[str],
    categorical_encoding: str,
    fitted_encoder: OrdinalEncoder | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    X = frame[feature_columns].copy()
    categorical_features = [column for column in feature_columns if not is_numeric_dtype(X[column]) or is_bool_dtype(X[column])]
    numeric_features = [column for column in feature_columns if column not in categorical_features]

    if categorical_encoding == "one_hot":
        encoded = pd.get_dummies(X, columns=categorical_features, dtype=int)
        encoded = encoded.astype(float)
        return encoded, {
            "categorical_features": categorical_features,
            "numeric_features": numeric_features,
            "ordinal_encoder": None,
        }

    encoder = fitted_encoder or OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    if categorical_features:
        values = encoder.fit_transform(X[categorical_features]) if fitted_encoder is None else encoder.transform(X[categorical_features])
        X.loc[:, categorical_features] = values
    encoded = X.astype(float)
    return encoded, {
        "categorical_features": categorical_features,
        "numeric_features": numeric_features,
        "ordinal_encoder": encoder,
    }


def load_trained_state(user: dict) -> tuple[dict[str, Any], dict[str, Any]]:
    artifact_path = get_model_artifact_path(user)
    metadata_path = get_model_metadata_path(user)
    if not artifact_path.exists() or not metadata_path.exists():
        raise HTTPException(status_code=400, detail="No trained model is available for the current dataset")

    artifact = joblib.load(artifact_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return artifact, metadata


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.post("/auth/signup", response_model=AuthResponse)
def signup(payload: SignUpRequest) -> AuthResponse:
    with get_db_cursor() as (conn, cur):
        cur.execute("SELECT 1 FROM users WHERE email = %s", (payload.email,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Email already registered")

        password_hash = hash_password(payload.password)
        cur.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (payload.username, payload.email, password_hash),
        )
        conn.commit()

    token = create_access_token(payload.email)
    return AuthResponse(access_token=token, username=payload.username, email=payload.email)


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    with get_db_cursor() as (_, cur):
        cur.execute(
            "SELECT username, email, password_hash FROM users WHERE email = %s",
            (payload.email,),
        )
        row = cur.fetchone()

    if not row or not verify_password(payload.password, row[2]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(row[1])
    return AuthResponse(access_token=token, username=row[0], email=row[1])


@app.get("/me")
def get_me(user: dict = Depends(get_current_user)) -> dict:
    return user


@app.get("/dashboard/dataset/shape")
def dataset_shape(user: dict = Depends(get_current_user)) -> dict:
    data = load_dataset(user)
    return {"rows": int(data.shape[0]), "columns": int(data.shape[1])}


@app.get("/dashboard/dataset/dtypes")
def dataset_dtypes(user: dict = Depends(get_current_user)) -> dict:
    data = load_dataset(user)
    rows = [{"column": column, "dtype": str(dtype)} for column, dtype in data.dtypes.items()]
    return {"rows": rows}


@app.get("/dashboard/dataset/columns")
def dataset_columns(user: dict = Depends(get_current_user)) -> dict:
    data = load_dataset(user)
    return {"rows": [get_column_profile(data, column) for column in data.columns]}


@app.get("/dashboard/dataset/head")
def dataset_head(n: int = 5, user: dict = Depends(get_current_user)) -> dict:
    n = max(1, min(n, 100))
    data = load_dataset(user).head(n)
    return {"rows": data.to_dict(orient="records")}


@app.get("/dashboard/dataset/tail")
def dataset_tail(n: int = 5, user: dict = Depends(get_current_user)) -> dict:
    n = max(1, min(n, 100))
    data = load_dataset(user).tail(n)
    return {"rows": data.to_dict(orient="records")}


@app.get("/dashboard/dataset/describe")
def dataset_describe(user: dict = Depends(get_current_user)) -> dict:
    data = load_dataset(user).describe(include="all")
    table = data.reset_index(names="stat")
    return {"rows": table.to_dict(orient="records")}


@app.get("/dashboard/dataset/config")
def dataset_config(user: dict = Depends(get_current_user)) -> dict:
    data = load_dataset(user)
    return {
        "dataset_name": get_dataset_path(user).name,
        "is_default_dataset": get_dataset_path(user) == DEFAULT_CSV_PATH,
        "prediction_ranges": extract_prediction_ranges(data),
    }


@app.post("/dashboard/dataset/upload")
async def upload_dataset(file: UploadFile = File(...), user: dict = Depends(get_current_user)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded") from exc

    rows = list(csv.reader(decoded.splitlines()))
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="CSV file must include a header and at least one data row")

    try:
        pd.read_csv(pd.io.common.StringIO(decoded))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid CSV content") from exc
    (UPLOADS_DIR / f"user_{user['id']}.csv").write_text(decoded, encoding="utf-8")
    clear_model_state(user)
    return dataset_config(user)


@app.post("/dashboard/dataset/dropna")
def drop_missing_rows(user: dict = Depends(get_current_user)) -> dict:
    data = load_dataset(user)
    cleaned_data = data.dropna()
    if cleaned_data.empty:
        raise HTTPException(status_code=400, detail="Removing empty rows would leave the dataset empty")

    persist_user_dataset(cleaned_data, user)

    return {
        **dataset_config(user),
        "removed_rows": int(len(data) - len(cleaned_data)),
    }


@app.get("/dashboard/ml/state")
def get_ml_state(user: dict = Depends(get_current_user)) -> dict:
    data = load_dataset(user)
    model_ready = get_model_artifact_path(user).exists() and get_model_metadata_path(user).exists()
    trained_model = None
    if model_ready:
        _, trained_model = load_trained_state(user)

    return {
        "columns": [get_column_profile(data, column) for column in data.columns],
        "trained_model": trained_model,
    }


@app.post("/dashboard/ml/train")
def train_model(payload: MLTrainRequest, user: dict = Depends(get_current_user)) -> dict:
    data = load_dataset(user)
    validate_columns_exist(data, payload.feature_columns)

    if len(set(payload.feature_columns)) != len(payload.feature_columns):
        raise HTTPException(status_code=400, detail="Feature columns must be unique")

    if payload.algorithm_type in {"regression", "classification"}:
        if not payload.target_column:
            raise HTTPException(status_code=400, detail="A target column is required for regression and classification")
        validate_columns_exist(data, [payload.target_column])
        if payload.target_column in payload.feature_columns:
            raise HTTPException(status_code=400, detail="Target column cannot also be used as a feature")
        relevant_columns = payload.feature_columns + [payload.target_column]
    else:
        if payload.target_column:
            raise HTTPException(status_code=400, detail="Clustering does not use a target column")
        relevant_columns = payload.feature_columns

    training_frame = data[relevant_columns].dropna()
    if training_frame.empty:
        raise HTTPException(status_code=400, detail="No rows remain for training after removing missing values")

    X_encoded, preprocessing_state = preprocess_features(
        training_frame,
        payload.feature_columns,
        payload.categorical_encoding,
    )

    artifact: dict[str, Any] = {
        "ordinal_encoder": preprocessing_state["ordinal_encoder"],
    }
    target_classes = None

    if payload.algorithm_type == "regression":
        target_series = pd.to_numeric(training_frame[payload.target_column], errors="coerce")
        valid_mask = target_series.notna()
        X_train = X_encoded.loc[valid_mask]
        y_train = target_series.loc[valid_mask]
        if y_train.empty:
            raise HTTPException(status_code=400, detail="Regression target must contain numeric values")
        model = LinearRegression()
        model.fit(X_train, y_train)
    elif payload.algorithm_type == "classification":
        y_train = training_frame[payload.target_column].astype(str)
        if y_train.nunique() < 2:
            raise HTTPException(status_code=400, detail="Classification needs at least two target classes")
        label_encoder = LabelEncoder()
        encoded_target = label_encoder.fit_transform(y_train)
        model = LogisticRegression(max_iter=1000)
        model.fit(X_encoded, encoded_target)
        artifact["target_label_encoder"] = label_encoder
        target_classes = [str(value) for value in label_encoder.classes_.tolist()]
    else:
        if len(training_frame) < 2:
            raise HTTPException(status_code=400, detail="Clustering needs at least two rows")
        n_clusters = min(3, len(training_frame))
        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        model.fit(X_encoded)
        artifact["n_clusters"] = n_clusters

    artifact["model"] = model
    artifact["categorical_encoding"] = payload.categorical_encoding
    artifact["feature_columns"] = payload.feature_columns
    artifact["encoded_feature_names"] = X_encoded.columns.tolist()
    artifact["categorical_features"] = preprocessing_state["categorical_features"]
    artifact["target_column"] = payload.target_column
    artifact["algorithm_type"] = payload.algorithm_type

    metadata = build_ml_metadata(
        data=data,
        training_frame=training_frame,
        user=user,
        request=payload,
        encoded_feature_names=X_encoded.columns.tolist(),
        categorical_features=preprocessing_state["categorical_features"],
        target_classes=target_classes,
    )
    if payload.algorithm_type == "clustering":
        metadata["cluster_count"] = artifact["n_clusters"]

    joblib.dump(artifact, get_model_artifact_path(user))
    get_model_metadata_path(user).write_text(json.dumps(metadata), encoding="utf-8")

    return {"message": "Model trained successfully", "trained_model": metadata}


@app.post("/dashboard/ml/predict")
def predict_dynamic(payload: DynamicPredictionRequest, user: dict = Depends(get_current_user)) -> dict:
    artifact, metadata = load_trained_state(user)
    feature_columns = metadata["feature_columns"]

    missing_values = [column for column in feature_columns if column not in payload.values]
    if missing_values:
        raise HTTPException(status_code=400, detail=f"Missing input values for: {', '.join(missing_values)}")

    input_row: dict[str, Any] = {}
    for profile in metadata["feature_profiles"]:
        column = profile["name"]
        raw_value = payload.values[column]
        if raw_value in ("", None):
            raise HTTPException(status_code=400, detail=f"Feature '{column}' cannot be empty")
        input_row[column] = str(raw_value) if profile["is_categorical"] else float(raw_value)

    input_frame = pd.DataFrame([input_row], columns=feature_columns)
    if artifact["categorical_encoding"] == "one_hot":
        transformed = pd.get_dummies(input_frame, columns=artifact["categorical_features"], dtype=int).astype(float)
        transformed = transformed.reindex(columns=artifact["encoded_feature_names"], fill_value=0)
    else:
        transformed = input_frame.copy()
        if artifact["categorical_features"]:
            transformed.loc[:, artifact["categorical_features"]] = artifact["ordinal_encoder"].transform(
                transformed[artifact["categorical_features"]]
            )
        transformed = transformed.astype(float)

    prediction = artifact["model"].predict(transformed)[0]

    if metadata["algorithm_type"] == "classification":
        predicted_value = artifact["target_label_encoder"].inverse_transform([int(prediction)])[0]
    elif metadata["algorithm_type"] == "clustering":
        predicted_value = int(prediction)
    else:
        predicted_value = round(float(prediction), 3)

    return {
        "prediction": predicted_value,
        "algorithm_type": metadata["algorithm_type"],
        "target_column": metadata["target_column"],
    }


@app.post("/dashboard/predict", response_model=PredictionResponse)
def predict_score(payload: PredictionRequest, user: dict = Depends(get_current_user)) -> PredictionResponse:
    _ = user
    values = np.array(
        [[
            payload.social_support,
            payload.healthy_life_expectancy,
            payload.log_gdp_per_capita,
            payload.freedom,
        ]],
        dtype=float,
    )
    prediction = MODEL.predict(values)[0]
    return PredictionResponse(predicted_score=float(round(prediction, 3)))
