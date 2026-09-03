import pytest
from fastapi.testclient import TestClient

from app.db.database import init_db
from app.main import app, get_agent_graph, get_db_path
from app.ratelimit import rate_limit


class FakeGraph:
    def __init__(self, result: dict):
        self._result = result

    def invoke(self, state):
        return self._result


@pytest.fixture
def make_client(tmp_path):
    """/ticket endpoint'ini gerçek LLM'e ihtiyaç duymadan test etmek için
    agent grafiğini sahte, sabit bir sonuç döndüren nesneyle değiştirir.

    Ticket geçmişi de gerçek dev veritabanına (data/tickets.db) değil,
    testler arasında izole, tmp_path altında geçici bir SQLite dosyasına
    yazılır. Rate limit süreç genelinde sayaç tuttuğu için testlerde
    varsayılan olarak kapatılır (kendi testi limiter'ı doğrudan kullanır)."""

    db_path = str(tmp_path / "test_tickets.db")
    init_db(db_path)

    def _make(result: dict) -> TestClient:
        app.dependency_overrides[get_agent_graph] = lambda: FakeGraph(result)
        app.dependency_overrides[get_db_path] = lambda: db_path
        app.dependency_overrides[rate_limit] = lambda: None
        return TestClient(app)

    yield _make

    app.dependency_overrides.pop(get_agent_graph, None)
    app.dependency_overrides.pop(get_db_path, None)
    app.dependency_overrides.pop(rate_limit, None)
