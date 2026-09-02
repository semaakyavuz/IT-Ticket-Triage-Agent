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
