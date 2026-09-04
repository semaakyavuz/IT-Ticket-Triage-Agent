import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.state import TicketState
from app.agent.tools import assign_team, get_priority, search_similar_tickets
from app.config import CATEGORIES, PRIORITIES
from app.providers import get_chat_model

TOOLS = [search_similar_tickets, get_priority, assign_team]

SYSTEM_PROMPT = f"""Sen bir IT destek ticket triage asistanısın. Kullanıcının bildirdiği
IT sorununu incelemek için şu adımları SIRAYLA uygula:

1. Sorunu şu 4 kategoriden birine ata: {", ".join(CATEGORIES)}.
2. `get_priority` tool'unu, belirlediğin kategori ve ticket metniyle çağırarak önceliği
   belirle (olası değerler: {", ".join(PRIORITIES)}).
3. `search_similar_tickets` tool'unu ticket metniyle MUTLAKA çağır (her ticket için,
   istisnasız; sorun "bariz" görünse bile) ve geçmişte benzer bir ticket olup
   olmadığına bak.
4. Benzer ve alakalı bir ticket bulunduysa, onun çözümüne dayanarak kısa bir çözüm
   öner. Yeterince benzer bir ticket bulunamadıysa `assign_team` tool'unu belirlediğin
   kategoriyle çağırarak doğru ekibe yönlendir.

Gerekli tüm tool çağrılarını tamamladıktan sonra kısa bir onay mesajı yaz (bu mesaj
kullanıcıya gösterilmeyecek, sadece adımların tamamlandığını belirtir).
"""

# Ana ReAct döngüsü tool çağırmaktan sorumlu; son kullanıcıya gösterilecek cümle
# kasıtlı olarak AYRI ve basit bir çağrıyla üretiliyor (bkz. _compose_solution_text).
# Küçük, local bir modelin (llama3.2) çok adımlı tool-calling + dil/format
# kısıtlarını AYNI ANDA tutması güvenilir çalışmadı (İngilizce girdi Türkçe yerine
# İngilizce/liste formatlı yanıtla sonuçlanabiliyordu); tek amaçlı, kısa bir prompt
# bu modelde belirgin şekilde daha tutarlı sonuç verdi.
COMPOSE_PROMPT_TEMPLATE = """Sen bir IT destek asistanısın. Aşağıdaki bilgilere dayanarak
kullanıcıya söyleyeceğin TEK bir Türkçe cümle yaz (EN FAZLA 25 kelime). SADECE o
cümleyi yaz; liste, madde işareti, başlık veya ek açıklama KULLANMA.

Kategori: {category}
Öncelik: {priority}
Geçmişte bulunan en benzer çözüm: {best_solution}
Yönlendirilen ekip: {assigned_team}

Eğer geçmişte benzer bir çözüm varsa ona dayanarak somut bir çözüm öner; yoksa
sadece hangi ekibe yönlendirildiğini tek cümleyle belirt.

ÇOK ÖNEMLİ: Cümlenin TAMAMI Türkçe olmalı. "needed", "should", "issue",
"please" gibi TEK BİR İngilizce kelime bile kullanma; İngilizce bir kelime
aklına gelirse yerine Türkçe karşılığını yaz (örn. "gerekiyor", "öneriliyor")."""


def _get_llm() -> BaseChatModel:
    """Tool-calling döngüsünde kullanılan model (sağlayıcı: app/providers.py)."""
    return get_chat_model(temperature=0).bind_tools(TOOLS)


def _get_plain_llm() -> BaseChatModel:
    """Son cümleyi üreten, tool bağlı OLMAYAN model.

    Aynı (tool-bound) model kompozisyon için de kullanıldığında, model bir
    metin yazmak yerine tekrar bir tool çağırmayı seçebiliyordu (boş `content`
    ile sonuçlanan bir AIMessage). Tool'ları hiç görmeyen ayrı bir örnek bu
    riski ortadan kaldırıyor.
    """
    return get_chat_model(temperature=0)


def _agent_node(state: TicketState, llm: BaseChatModel) -> dict:
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


def _estimate_confidence(similar_tickets: list[dict]) -> int:
    """RAG'daki en benzer ticket'in mesafe skorundan kabaca bir güven yüzdesi türetir.

    Kalibre edilmiş bir olasılık değildir, sadece karşılaştırmalı/görsel bir
    göstergedir: skor küçüldükçe (daha benzer ticket bulundukça) güven artar.
    Hiç benzer ticket bulunamadıysa nötr bir değer (%50) döner.
    """
    if not similar_tickets:
        return 50
    best_score = min(t["score"] for t in similar_tickets)
    confidence = round(100 / (1 + max(best_score, 0)))
    return max(0, min(confidence, 100))


def _compose_solution_text(
    llm: BaseChatModel,
    category: str | None,
    priority: str | None,
    similar_tickets: list[dict],
    assigned_team: str | None,
) -> str:
    best_solution = similar_tickets[0]["solution"] if similar_tickets else "yok"
    prompt = COMPOSE_PROMPT_TEMPLATE.format(
        category=category or "belirsiz",
        priority=priority or "belirsiz",
        best_solution=best_solution,
        assigned_team=assigned_team or "belirtilmedi",
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


def _finalize_node(state: TicketState, llm: BaseChatModel) -> dict:
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

    # Benzer ticket bulunduğunda agent assign_team'i çağırmaz (çözüm önerir);
    # yine de geçmiş/dashboard için ilgili ekip bilinsin: en benzer ticket'ı çözen ekip.
    if assigned_team is None and similar_tickets:
        assigned_team = similar_tickets[0].get("team")

    confidence = _estimate_confidence(similar_tickets)
    solution = _compose_solution_text(llm, category, priority, similar_tickets, assigned_team)

    return {
        "category": category,
        "priority": priority,
        "confidence": confidence,
        "similar_tickets": similar_tickets,
        "solution": solution,
        "assigned_team": assigned_team,
    }


def _after_tools(state: TicketState) -> str:
    """Tool sonuçlarından sonra: plan tamamlandıysa agent'a dönmeden finalize'a geç.

    Aksi halde agent bir tur daha çağrılıp sadece "tamamlandı" der; bu tur hem
    gecikme hem de (Groq ücretsiz katmanında dakikada ~1000 olan) çıktı token
    kotasını harcar. Plan: öncelik + benzer ticket araması yapılmış ve ya benzer
    ticket bulunmuş ya da ekip atanmış olmalı.
    """
    messages = state["messages"]
    have_priority = _extract_tool_result(messages, "get_priority") is not None
    similar_raw = _extract_tool_result(messages, "search_similar_tickets")
    have_team = _extract_tool_result(messages, "assign_team") is not None

    if have_priority and similar_raw is not None:
        try:
            found_similar = bool(json.loads(similar_raw))
        except json.JSONDecodeError:
            found_similar = False
        if found_similar or have_team:
            return "finalize"
    return "agent"


def build_graph(llm: BaseChatModel | None = None, compose_llm: BaseChatModel | None = None):
    """LangGraph agent grafiğini oluşturur ve derler.

    `llm` tool-calling döngüsünde kullanılır; `compose_llm` son kullanıcıya
    gösterilecek cümleyi üretir (gerçek kullanımda bilerek tool bağlı olmayan
    ayrı bir model). İkisi de testlerde sahte bir modelle değiştirmek için
    opsiyoneldir; `compose_llm` verilmezse ve `llm` verilmişse (örn. testte
    tek bir sahte model kullanmak için) `llm` ile aynı nesne kullanılır.
    """
    react_llm = llm or _get_llm()
    finalize_llm = compose_llm or llm or _get_plain_llm()

    graph = StateGraph(TicketState)
    graph.add_node("agent", lambda state: _agent_node(state, react_llm))
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_node("finalize", lambda state: _finalize_node(state, finalize_llm))

    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent", tools_condition, {"tools": "tools", END: "finalize"}
    )
    graph.add_conditional_edges(
        "tools", _after_tools, {"agent": "agent", "finalize": "finalize"}
    )
    graph.add_edge("finalize", END)

    return graph.compile()
