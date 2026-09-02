import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.state import TicketState
from app.agent.tools import assign_team, get_priority, search_similar_tickets
from app.config import CATEGORIES, OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, PRIORITIES

TOOLS = [search_similar_tickets, get_priority, assign_team]

SYSTEM_PROMPT = f"""Sen bir IT destek ticket triage asistanısın. Kullanıcının bildirdiği
IT sorununu incelemek için şu adımları SIRAYLA uygula:

1. Sorunu şu 4 kategoriden birine ata: {", ".join(CATEGORIES)}.
2. `get_priority` tool'unu, belirlediğin kategori ve ticket metniyle çağırarak önceliği
   belirle (olası değerler: {", ".join(PRIORITIES)}).
3. `search_similar_tickets` tool'unu ticket metniyle çağırarak geçmişte benzer bir
   ticket olup olmadığına bak.
4. Benzer ve alakalı bir ticket bulunduysa, onun çözümüne dayanarak kısa bir çözüm
   öner. Yeterince benzer bir ticket bulunamadıysa `assign_team` tool'unu belirlediğin
   kategoriyle çağırarak doğru ekibe yönlendir.

Gerekli tüm tool çağrılarını tamamladıktan sonra, kullanıcıya tek bir kısa paragrafla
(Türkçe) ya önerdiğin çözümü ya da yönlendirildiği ekibi bildir. Başka açıklama ekleme.
"""


def _get_llm() -> ChatOllama:
    return ChatOllama(
        model=OLLAMA_CHAT_MODEL, base_url=OLLAMA_BASE_URL, temperature=0
    ).bind_tools(TOOLS)


def _agent_node(state: TicketState, llm: ChatOllama) -> dict:
    messages = state["messages"]
    if not messages:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=state["ticket_text"]),
        ]
    response = llm.invoke(messages)
    return {"messages": [response]}


def _extract_tool_call_args(messages: list, tool_name: str) -> dict | None:
    for message in messages:
        if isinstance(message, AIMessage):
            for call in message.tool_calls or []:
                if call["name"] == tool_name:
                    return call["args"]
    return None


def _extract_tool_result(messages: list, tool_name: str) -> str | None:
    for message in messages:
        if isinstance(message, ToolMessage) and message.name == tool_name:
            return message.content
    return None


def _finalize_node(state: TicketState) -> dict:
    messages = state["messages"]

    category = None
    for tool_name in ("get_priority", "assign_team"):
        args = _extract_tool_call_args(messages, tool_name)
        if args and args.get("category"):
            category = args["category"]
            break

    priority = _extract_tool_result(messages, "get_priority")
    assigned_team = _extract_tool_result(messages, "assign_team")

    similar_raw = _extract_tool_result(messages, "search_similar_tickets")
    try:
        similar_tickets = json.loads(similar_raw) if similar_raw else []
    except json.JSONDecodeError:
        similar_tickets = []

    final_ai_message = next(
        (m for m in reversed(messages) if isinstance(m, AIMessage) and m.content),
        None,
    )
    solution = final_ai_message.content.strip() if final_ai_message else None

    return {
        "category": category,
        "priority": priority,
        "similar_tickets": similar_tickets,
        "solution": solution,
        "assigned_team": assigned_team,
    }


def build_graph(llm: ChatOllama | None = None):
    """LangGraph agent grafiğini oluşturur ve derler.

    `llm` parametresi testlerde sahte bir modelle değiştirmek için opsiyoneldir;
    verilmezse gerçek Ollama modeli kullanılır.
    """
    llm = llm or _get_llm()

    graph = StateGraph(TicketState)
    graph.add_node("agent", lambda state: _agent_node(state, llm))
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_node("finalize", _finalize_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent", tools_condition, {"tools": "tools", END: "finalize"}
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("finalize", END)

    return graph.compile()
