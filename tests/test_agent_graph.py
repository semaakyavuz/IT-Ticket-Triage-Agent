from langchain_core.messages import AIMessage, HumanMessage

from app.agent.graph import _estimate_confidence, build_graph


class FakeLLM:
    """Hem ReAct tool-calling dongusunu hem de son cumleyi ureten kompozisyon
    cagrisini tek bir sahte modelle simule eder (mesaj sekline gore ayirt eder)."""

    def __init__(self):
        self.calls = 0

    def invoke(self, messages):
        if len(messages) == 1 and isinstance(messages[0], HumanMessage) and "TEK bir Türkçe cümle" in messages[0].content:
            return AIMessage(content="Sorun ağ kategorisinde, Network Operasyon Ekibi'ne yönlendirildi.")

        self.calls += 1
        if self.calls == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {"name": "get_priority", "args": {"category": "ağ", "keywords": "VPN bağlanmıyor"}, "id": "1"},
                    {"name": "assign_team", "args": {"category": "ağ"}, "id": "2"},
                ],
            )
        return AIMessage(content="tamamlandı")


def test_build_graph_end_to_end_with_fake_llm():
    graph = build_graph(llm=FakeLLM())

    result = graph.invoke({"ticket_text": "VPN bağlanmıyor", "messages": []})

    assert result["category"] == "ağ"
    assert result["priority"] == "orta"
    assert result["assigned_team"] == "Network Operasyon Ekibi"
    assert result["similar_tickets"] == []
    assert result["confidence"] == 50  # RAG kullanılmadığı için nötr varsayılan
    assert result["solution"] == "Sorun ağ kategorisinde, Network Operasyon Ekibi'ne yönlendirildi."


def test_estimate_confidence_without_similar_tickets():
    assert _estimate_confidence([]) == 50


def test_estimate_confidence_scales_with_best_score():
    assert _estimate_confidence([{"score": 0.0}]) == 100
    assert _estimate_confidence([{"score": 1.0}]) == 50
    assert _estimate_confidence([{"score": 4.0}]) == 20


def test_estimate_confidence_uses_best_of_multiple_scores():
    assert _estimate_confidence([{"score": 4.0}, {"score": 0.0}, {"score": 1.0}]) == 100
