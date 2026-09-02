import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

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

CREATE TABLE IF NOT EXISTS ticket_history (
    id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    ticket_text TEXT NOT NULL,
    category TEXT,
    priority TEXT,
    assigned_team TEXT,
    corrected_category TEXT
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
        conn.executescript(SCHEMA)
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


def insert_ticket_history(
    ticket_text: str,
    category: str | None,
    priority: str | None,
    assigned_team: str | None,
    db_path: str = SQLITE_DB_PATH,
) -> int:
    """Gönderilen bir ticket'ı geçmiş tablosuna kaydeder, yeni kaydın id'sini döner."""
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO ticket_history (created_at, ticket_text, category, priority, assigned_team)
            VALUES (?, ?, ?, ?, ?)
            """,
            (created_at, ticket_text, category, priority, assigned_team),
        )
        conn.commit()
        return cursor.lastrowid


def fetch_ticket_history(db_path: str = SQLITE_DB_PATH) -> list[dict]:
    """Ticket geçmişini en yeni kayıt üstte olacak şekilde döner."""
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM ticket_history ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


def update_ticket_correction(
    ticket_id: int, corrected_category: str, db_path: str = SQLITE_DB_PATH
) -> dict | None:
    """Bir ticket geçmişi kaydına kullanıcı düzeltmesini yazar.

    Kayıt bulunamazsa None döner; bulunursa güncellenmiş satırı döner.
    """
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "UPDATE ticket_history SET corrected_category = ? WHERE id = ?",
            (corrected_category, ticket_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None
        row = conn.execute(
            "SELECT * FROM ticket_history WHERE id = ?", (ticket_id,)
        ).fetchone()
        return dict(row)
