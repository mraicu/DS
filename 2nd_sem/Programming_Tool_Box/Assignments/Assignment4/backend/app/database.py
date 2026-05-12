import os
from contextlib import contextmanager

import psycopg2


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "PT_assign_3"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "m1234.="),
    )


@contextmanager
def get_db_cursor():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield conn, cur
    finally:
        conn.close()
