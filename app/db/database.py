import os
import sqlite3
from contextlib import contextmanager

from app.config import SQLITE_DB_PATH
from app.db.seed_data import TICKETS

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    solution TEXT NOT NULL,
    team TEXT NOT NULL
);
"""


@contextmanager
def get_connection(db_path: str = SQLITE_DB_PATH):
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: str = SQLITE_DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(SCHEMA)
        conn.commit()


def seed_if_empty(db_path: str = SQLITE_DB_PATH) -> int:
    """Tablo boşsa mock ticket verisini ekler. Eklenen kayıt sayısını döner."""
    with get_connection(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        if count > 0:
            return 0

        conn.executemany(
            """
            INSERT INTO tickets (id, title, description, category, priority, solution, team)
            VALUES (:id, :title, :description, :category, :priority, :solution, :team)
            """,
            TICKETS,
        )
        conn.commit()
        return len(TICKETS)


def fetch_all_tickets(db_path: str = SQLITE_DB_PATH) -> list[dict]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM tickets ORDER BY id").fetchall()
        return [dict(row) for row in rows]
