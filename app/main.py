from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.agent.graph import build_graph
from app.db.database import init_db, seed_if_empty
from app.schemas import TicketRequest, TicketResponse

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


@app.post("/ticket", response_model=TicketResponse)
def triage_ticket(payload: TicketRequest, graph=Depends(get_agent_graph)) -> TicketResponse:
    result = graph.invoke({"ticket_text": payload.text, "messages": []})
    return TicketResponse(
        category=result.get("category"),
        priority=result.get("priority"),
        similar_tickets=result.get("similar_tickets", []),
        solution=result.get("solution"),
        assigned_team=result.get("assigned_team"),
    )
