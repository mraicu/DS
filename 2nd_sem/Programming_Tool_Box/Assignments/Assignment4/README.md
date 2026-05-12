# Happiness Web Application

## Stack

- Frontend: React + Vite + TypeScript
- Backend: FastAPI
- Database: PostgreSQL (`users` table)

## Backend Setup

1. Go to `backend`.
2. Create/activate your Python environment.
3. Install dependencies:
    - `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` (already included) and update values if needed.
5. Start API:
    - `uvicorn app.main:app --reload`

The backend reads:

- `backend/data/world-happiness-report-2019.csv`
- `backend/model/happiness_linear_regression.pkl`

## Frontend Setup

1. Go to `frontend`.
2. Install dependencies:
    - `npm install`
3. Copy `.env.example` to `.env` (optional if default is fine).
4. Start app:
    - `npm run dev`

## App Flow

- `/` -> Sign in / Sign up page.
- Successful auth -> `/dashboard`.
- Dashboard has:
    - dataset summary
    - happiness prediction form backed by the trained linear regression model.

## PostgreSQL Notes

`users` table is auto-created at backend startup.
