from typing import Literal

from pydantic import BaseModel, Field


class SignUpRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    email: str


class PredictionRequest(BaseModel):
    social_support: float
    healthy_life_expectancy: float
    log_gdp_per_capita: float
    freedom: float


class PredictionResponse(BaseModel):
    predicted_score: float


class MLTrainRequest(BaseModel):
    algorithm_type: Literal["regression", "classification", "clustering"]
    feature_columns: list[str] = Field(min_length=1)
    target_column: str | None = None
    categorical_encoding: Literal["one_hot", "ordinal"] = "one_hot"


class DynamicPredictionRequest(BaseModel):
    values: dict[str, str | int | float | bool | None]
