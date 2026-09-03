from typing import Optional

from pydantic import BaseModel, Field, computed_field, field_validator

from app.config import CATEGORIES


class TicketRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Kullanıcının yazdığı IT sorunu (LLM bağlamını korumak için en fazla 1000 karakter)",
    )


class SimilarTicket(BaseModel):
    ticket_id: int
    title: str
    category: str
    priority: str
    solution: str
    team: str
    score: float


class TicketResponse(BaseModel):
    ticket_id: Optional[int] = Field(
        default=None, description="Ticket geçmişi tablosuna kaydedilen satırın id'si (düzeltme göndermek için kullanılır)"
    )
    category: Optional[str] = None
    priority: Optional[str] = None
    confidence: Optional[int] = Field(
        default=None, description="RAG'daki en benzer ticket skorundan türetilen, 0-100 arası kaba bir güven yüzdesi"
    )
    similar_tickets: list[SimilarTicket] = []
    solution: Optional[str] = None
    assigned_team: Optional[str] = None


class TicketHistoryItem(BaseModel):
    id: int
    created_at: str
    ticket_text: str
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_team: Optional[str] = None
    corrected_category: Optional[str] = None

    @computed_field
    @property
    def is_corrected(self) -> bool:
        return self.corrected_category is not None


class CorrectionRequest(BaseModel):
    corrected_category: str

    @field_validator("corrected_category")
    @classmethod
    def _validate_category(cls, value: str) -> str:
        if value not in CATEGORIES:
            raise ValueError(f"Geçersiz kategori: {value!r}. Beklenen değerler: {CATEGORIES}")
        return value


class RecurringAlert(BaseModel):
    category: str
    count: int
    days: int
    threshold: int
