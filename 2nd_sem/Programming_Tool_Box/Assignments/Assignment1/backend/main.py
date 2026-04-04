import os
from datetime import date
from typing import Any, Dict, List

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "pt_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "m1234.="),
    )


def format_birth_date(value: date | None) -> str:
    if value is None:
        return ""
    return value.strftime("%d-%m-%Y")


@app.get("/api/about")
def get_about() -> Dict[str, Any]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT person_id, full_name, role, date_of_birth, location, summary
                    FROM person
                    ORDER BY person_id DESC
                    LIMIT 1
                    """
                )
                person_row = cur.fetchone()

                if not person_row:
                    raise HTTPException(status_code=404, detail="No person found")

                person_id = person_row[0]

                cur.execute(
                    """
                    SELECT highlight_text
                    FROM person_highlight
                    WHERE person_id = %s
                    ORDER BY sort_order ASC, highlight_id ASC
                    """,
                    (person_id,),
                )
                highlights = [row[0] for row in cur.fetchall()]

                return {
                    "person": {
                        "fullName": person_row[1],
                        "role": person_row[2] or "",
                        "dateOfBirth": format_birth_date(person_row[3]),
                        "location": person_row[4] or "",
                        "summary": person_row[5] or "",
                        "highlights": highlights,
                    }
                }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


@app.get("/api/career")
def get_career() -> Dict[str, List[Dict[str, str]]]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT person_id
                    FROM person
                    ORDER BY person_id DESC
                    LIMIT 1
                    """
                )
                person_row = cur.fetchone()
                if not person_row:
                    raise HTTPException(status_code=404, detail="No person found")

                person_id = person_row[0]

                cur.execute(
                    """
                    SELECT title, organization, period, details
                    FROM education
                    WHERE person_id = %s
                    ORDER BY sort_order ASC, education_id ASC
                    """,
                    (person_id,),
                )
                education = [
                    {
                        "title": row[0],
                        "organization": row[1],
                        "period": row[2],
                        "details": row[3] or "",
                    }
                    for row in cur.fetchall()
                ]

                cur.execute(
                    """
                    SELECT title, organization, period, details
                    FROM experience
                    WHERE person_id = %s
                    ORDER BY sort_order ASC, experience_id ASC
                    """,
                    (person_id,),
                )
                experience = [
                    {
                        "title": row[0],
                        "organization": row[1],
                        "period": row[2],
                        "details": row[3] or "",
                    }
                    for row in cur.fetchall()
                ]

                return {
                    "education": education,
                    "experience": experience,
                }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


@app.get("/api/hobbies")
def get_hobbies() -> Dict[str, List[Dict[str, str]]]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT person_id
                    FROM person
                    ORDER BY person_id DESC
                    LIMIT 1
                    """
                )
                person_row = cur.fetchone()
                if not person_row:
                    raise HTTPException(status_code=404, detail="No person found")

                person_id = person_row[0]

                cur.execute(
                    """
                    SELECT title, description
                    FROM hobby
                    WHERE person_id = %s
                    ORDER BY sort_order ASC, hobby_id ASC
                    """,
                    (person_id,),
                )
                hobbies = [
                    {
                        "title": row[0],
                        "description": row[1] or "",
                    }
                    for row in cur.fetchall()
                ]

                return {"hobbies": hobbies}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc
