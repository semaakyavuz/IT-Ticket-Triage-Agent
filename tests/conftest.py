import pytest
from fastapi.testclient import TestClient

from app.main import app, get_agent_graph


class FakeGraph:
    def __init__(self, result: dict):
        self._result = result

    def invoke(self, state):
        return self._result


@pytest.fixture
def make_client():
    """/ticket endpoint'ini gerçek LLM'e ihtiyaç duymadan test etmek için
    agent grafiğini sahte, sabit bir sonuç döndüren nesneyle değiştirir."""

    def _make(result: dict) -> TestClient:
        app.dependency_overrides[get_agent_graph] = lambda: FakeGraph(result)
        return TestClient(app)

    yield _make

    app.dependency_overrides.pop(get_agent_graph, None)
