from typing import Annotated, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class TicketState(TypedDict):
    ticket_text: str
    messages: Annotated[list[BaseMessage], add_messages]
    category: Optional[str]
    priority: Optional[str]
    similar_tickets: list[dict]
    solution: Optional[str]
    assigned_team: Optional[str]
