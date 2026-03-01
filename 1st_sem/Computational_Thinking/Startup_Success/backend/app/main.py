from fastapi import FastAPI
from backend.app.routes_auth import router as auth_router
from backend.app.routes_ml import router as ml_router
from backend.app.routes_metrics import router as metrics_router
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app = FastAPI(title="Startup Success Prediction API")

app.include_router(metrics_router, prefix="/ml")
app.include_router(auth_router, prefix="/ml")
app.include_router(ml_router, prefix="/ml")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
