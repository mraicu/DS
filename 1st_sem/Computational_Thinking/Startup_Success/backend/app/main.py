from fastapi import FastAPI
from backend.app.endpoints import router
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app = FastAPI(title="Startup Success Prediction API")

app.include_router(router, prefix="/ml", tags=["Startup Prediction"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
