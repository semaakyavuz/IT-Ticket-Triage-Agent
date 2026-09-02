from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agent.graph import build_graph
from app.db.database import init_db, seed_if_empty
from app.schemas import TicketRequest, TicketResponse

STATIC_DIR = Path(__file__).parent / "static"

_graph = None


def get_agent_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


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
def triage_ticket(payload: TicketRequest, graph=Depends(get_agent_graph)) -> TicketResponse:
    result = graph.invoke({"ticket_text": payload.text, "messages": []})
    return TicketResponse(
        category=result.get("category"),
        priority=result.get("priority"),
        confidence=result.get("confidence"),
        similar_tickets=result.get("similar_tickets", []),
        solution=result.get("solution"),
        assigned_team=result.get("assigned_team"),
    )
