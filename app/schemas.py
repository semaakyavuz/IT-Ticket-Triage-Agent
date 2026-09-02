from typing import Optional

from pydantic import BaseModel, Field


class TicketRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Kullanıcının yazdığı IT sorunu")


class SimilarTicket(BaseModel):
    ticket_id: int
    title: str
    category: str
    priority: str
    solution: str
    team: str
    score: float


class TicketResponse(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None
    similar_tickets: list[SimilarTicket] = []
    solution: Optional[str] = None
    assigned_team: Optional[str] = None
