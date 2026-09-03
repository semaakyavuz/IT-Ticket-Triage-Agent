FAKE_RESULT = {
    "category": "yazılım",
    "priority": "orta",
    "similar_tickets": [],
    "solution": "Test çözümü",
    "assigned_team": "Uygulama Destek Ekibi",
}


def test_triage_ticket_returns_agent_result(make_client):
    client = make_client(FAKE_RESULT)

    response = client.post("/ticket", json={"text": "Excel dosyası açılırken çöküyor"})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body.pop("ticket_id"), int)
    # FakeGraph "confidence" alani doldurmuyor, agent grafiginin kendisi
    # _estimate_confidence ile hesapliyor (bkz. tests/test_agent_graph.py)
    assert body.pop("confidence") is None
    assert body == FAKE_RESULT


def test_triage_ticket_rejects_empty_text(make_client):
    client = make_client(FAKE_RESULT)

    response = client.post("/ticket", json={"text": ""})

    assert response.status_code == 422


def test_triage_ticket_requires_text_field(make_client):
    client = make_client(FAKE_RESULT)

    response = client.post("/ticket", json={})

    assert response.status_code == 422


def test_ticket_history_starts_empty(make_client):
    client = make_client(FAKE_RESULT)

    response = client.get("/tickets/history")

    assert response.status_code == 200
    assert response.json() == []


def test_ticket_creates_history_entry(make_client):
    client = make_client(FAKE_RESULT)

    client.post("/ticket", json={"text": "Excel dosyası açılırken çöküyor"})
    response = client.get("/tickets/history")

    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    entry = history[0]
    assert entry["ticket_text"] == "Excel dosyası açılırken çöküyor"
    assert entry["category"] == FAKE_RESULT["category"]
    assert entry["priority"] == FAKE_RESULT["priority"]
    assert entry["assigned_team"] == FAKE_RESULT["assigned_team"]
    assert entry["corrected_category"] is None
    assert entry["is_corrected"] is False


def test_ticket_history_lists_newest_first(make_client):
    client = make_client(FAKE_RESULT)

    client.post("/ticket", json={"text": "ilk ticket"})
    client.post("/ticket", json={"text": "ikinci ticket"})

    history = client.get("/tickets/history").json()

    assert [item["ticket_text"] for item in history] == ["ikinci ticket", "ilk ticket"]


def test_correct_ticket_history_updates_category(make_client):
    client = make_client(FAKE_RESULT)
    ticket_id = client.post("/ticket", json={"text": "Excel dosyası açılırken çöküyor"}).json()["ticket_id"]

    response = client.patch(f"/tickets/history/{ticket_id}", json={"corrected_category": "ağ"})

    assert response.status_code == 200
    body = response.json()
    assert body["corrected_category"] == "ağ"
    assert body["is_corrected"] is True

    history = client.get("/tickets/history").json()
    assert history[0]["corrected_category"] == "ağ"


def test_correct_ticket_history_rejects_unknown_category(make_client):
    client = make_client(FAKE_RESULT)
    ticket_id = client.post("/ticket", json={"text": "Excel dosyası açılırken çöküyor"}).json()["ticket_id"]

    response = client.patch(f"/tickets/history/{ticket_id}", json={"corrected_category": "bilinmeyen"})

    assert response.status_code == 422


def test_correct_ticket_history_404_for_missing_id(make_client):
    client = make_client(FAKE_RESULT)

    response = client.patch("/tickets/history/999", json={"corrected_category": "ağ"})

    assert response.status_code == 404


def test_recurring_alerts_empty_below_threshold(make_client):
    client = make_client(FAKE_RESULT)
    for _ in range(3):
        client.post("/ticket", json={"text": "Excel dosyası açılırken çöküyor"})

    response = client.get("/tickets/alerts")

    assert response.status_code == 200
    assert response.json() == []


def test_recurring_alerts_triggers_above_threshold(make_client):
    client = make_client(FAKE_RESULT)
    for _ in range(4):
        client.post("/ticket", json={"text": "Excel dosyası açılırken çöküyor"})

    response = client.get("/tickets/alerts")

    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) == 1
    assert alerts[0]["category"] == FAKE_RESULT["category"]
    assert alerts[0]["count"] == 4
    assert alerts[0]["threshold"] == 3


def test_health_reports_providers_without_secrets(make_client):
    client = make_client(FAKE_RESULT)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert {"llm_provider", "llm_model", "embedding_provider", "embedding_model"} <= body.keys()
    assert "api_key" not in str(body).lower()


def test_triage_ticket_rejects_overlong_text(make_client):
    client = make_client(FAKE_RESULT)

    response = client.post("/ticket", json={"text": "a" * 1001})

    assert response.status_code == 422


def test_triage_ticket_returns_503_when_agent_fails(make_client):
    from app.main import app, get_agent_graph

    class BrokenGraph:
        def invoke(self, state):
            raise RuntimeError("Groq: rate limit exceeded")

    client = make_client(FAKE_RESULT)
    app.dependency_overrides[get_agent_graph] = lambda: BrokenGraph()

    response = client.post("/ticket", json={"text": "VPN kopuyor"})

    assert response.status_code == 503
    assert "tekrar deneyin" in response.json()["detail"]
    # Basarisiz istek gecmise yazilmamali.
    assert client.get("/tickets/history").json() == []


def test_triage_ticket_rate_limited_after_threshold(make_client):
    from app.main import app
    from app.ratelimit import SlidingWindowLimiter, rate_limit

    limiter = SlidingWindowLimiter(limit=2, window_seconds=60)
    client = make_client(FAKE_RESULT)
    app.dependency_overrides[rate_limit] = lambda: limiter.check("test-client")

    statuses = [client.post("/ticket", json={"text": "VPN kopuyor"}).status_code for _ in range(3)]

    assert statuses == [200, 200, 429]
