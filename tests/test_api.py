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
    assert response.json() == FAKE_RESULT


def test_triage_ticket_rejects_empty_text(make_client):
    client = make_client(FAKE_RESULT)

    response = client.post("/ticket", json={"text": ""})

    assert response.status_code == 422


def test_triage_ticket_requires_text_field(make_client):
    client = make_client(FAKE_RESULT)

    response = client.post("/ticket", json={})

    assert response.status_code == 422
