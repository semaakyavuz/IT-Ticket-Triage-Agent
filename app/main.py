from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agent.graph import build_graph
from app.config import SQLITE_DB_PATH
from app.db.database import (
    fetch_recurring_alerts,
    fetch_ticket_history,
    init_db,
    insert_ticket_history,
    seed_if_empty,
    update_ticket_correction,
)
from app.schemas import (
    CorrectionRequest,
    RecurringAlert,
    TicketHistoryItem,
    TicketRequest,
    TicketResponse,
)

STATIC_DIR = Path(__file__).parent / "static"

_graph = None


def get_agent_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def get_db_path() -> str:
    """Testlerde geçmiş tablosunu gerçek dev veritabanından izole etmek için
    override edilebilen basit bir dependency (bkz. tests/conftest.py)."""
    return SQLITE_DB_PATH


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_if_empty()
    yield


app = FastAPI(title="IT Ticket Triage Agent", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def frontend_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/ticket", response_model=TicketResponse)
def triage_ticket(
    payload: TicketRequest,
    graph=Depends(get_agent_graph),
    db_path: str = Depends(get_db_path),
) -> TicketResponse:
    result = graph.invoke({"ticket_text": payload.text, "messages": []})
    ticket_id = insert_ticket_history(
        ticket_text=payload.text,
        category=result.get("category"),
        priority=result.get("priority"),
        assigned_team=result.get("assigned_team"),
        db_path=db_path,
    )
    return TicketResponse(
        ticket_id=ticket_id,
        category=result.get("category"),
        priority=result.get("priority"),
        confidence=result.get("confidence"),
        similar_tickets=result.get("similar_tickets", []),
        solution=result.get("solution"),
        assigned_team=result.get("assigned_team"),
    )


@app.get("/tickets/history", response_model=list[TicketHistoryItem])
def get_ticket_history(db_path: str = Depends(get_db_path)) -> list[dict]:
    return fetch_ticket_history(db_path=db_path)


@app.patch("/tickets/history/{ticket_id}", response_model=TicketHistoryItem)
def correct_ticket_history(
    ticket_id: int,
    payload: CorrectionRequest,
    db_path: str = Depends(get_db_path),
) -> dict:
    updated = update_ticket_correction(ticket_id, payload.corrected_category, db_path=db_path)
    if updated is None:
        raise HTTPException(status_code=404, detail="Ticket geçmişte bulunamadı")
    return updated


@app.get("/tickets/alerts", response_model=list[RecurringAlert])
def get_recurring_alerts(db_path: str = Depends(get_db_path)) -> list[dict]:
    return fetch_recurring_alerts(db_path=db_path)
