import csv
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_db_cursor
from app.schemas import AuthResponse, LoginRequest, PredictionRequest, PredictionResponse, SignUpRequest
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
CSV_PATH = BASE_DIR / "data" / "world-happiness-report-2019.csv"
FEATURES = [
    "Social support",
    "Healthy life expectancy",
    "Log of GDP per capita",
    "Freedom",
]

load_dotenv()
MODEL = joblib.load(MODEL_PATH)


def init_db() -> None:
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


def load_dataset() -> pd.DataFrame:
    data = pd.read_csv(CSV_PATH)
    if data.empty:
        raise HTTPException(status_code=500, detail="CSV file has no rows")
    return data


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


@app.get("/dashboard/summary")
def dashboard_summary(user: dict = Depends(get_current_user)) -> dict:
    with CSV_PATH.open("r", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    if not rows:
        raise HTTPException(status_code=500, detail="CSV file has no rows")

    score_key = next((k for k in ["Score", "Ladder", "Ladder score"] if k in rows[0]), None)
    country_key = next((k for k in ["Country (region)", "Country name", "Country"] if k in rows[0]), None)

    if not score_key or not country_key:
        raise HTTPException(status_code=500, detail="Required CSV columns are missing")

    top_country = max(rows, key=lambda row: float(row[score_key]))
    avg_score = sum(float(row[score_key]) for row in rows) / len(rows)

    return {
        "records": len(rows),
        "average_score": round(avg_score, 3),
        "top_country": top_country[country_key],
        "top_score": float(top_country[score_key]),
        "user": user,
    }


@app.get("/dashboard/dataset/shape")
def dataset_shape(user: dict = Depends(get_current_user)) -> dict:
    _ = user
    data = load_dataset()
    return {"rows": int(data.shape[0]), "columns": int(data.shape[1])}


@app.get("/dashboard/dataset/dtypes")
def dataset_dtypes(user: dict = Depends(get_current_user)) -> dict:
    _ = user
    data = load_dataset()
    rows = [{"column": column, "dtype": str(dtype)} for column, dtype in data.dtypes.items()]
    return {"rows": rows}


@app.get("/dashboard/dataset/head")
def dataset_head(n: int = 5, user: dict = Depends(get_current_user)) -> dict:
    _ = user
    n = max(1, min(n, 100))
    data = load_dataset().head(n)
    return {"rows": data.to_dict(orient="records")}


@app.get("/dashboard/dataset/tail")
def dataset_tail(n: int = 5, user: dict = Depends(get_current_user)) -> dict:
    _ = user
    n = max(1, min(n, 100))
    data = load_dataset().tail(n)
    return {"rows": data.to_dict(orient="records")}


@app.get("/dashboard/dataset/describe")
def dataset_describe(user: dict = Depends(get_current_user)) -> dict:
    _ = user
    data = load_dataset().describe(include="all")
    table = data.reset_index(names="stat")
    return {"rows": table.to_dict(orient="records")}


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
