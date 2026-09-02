import hashlib

from app.db.seed_data import TICKETS
from app.rag.vector_store import get_vector_store, index_tickets, search_similar


class FakeEmbeddings:
    """Ollama'ya bağımlı olmadan Chroma'yı test etmek için deterministik sahte embedding."""

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [b / 255.0 for b in digest[:16]]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


def _fresh_store():
    # persist_directory=None -> Chroma'nın bellek içi (ephemeral) client'ı; diske
    # yazmadığı için Windows'ta dosya kilidi/temizlik sorunu yaşanmaz.
    return get_vector_store(embeddings=FakeEmbeddings(), persist_directory=None)


def test_index_tickets_returns_inserted_count():
    store = _fresh_store()
    count = index_tickets(store, TICKETS[:5])
    assert count == 5


def test_search_similar_returns_expected_shape():
    store = _fresh_store()
    index_tickets(store, TICKETS[:5])

    results = search_similar(store, TICKETS[0]["description"], k=2)

    assert len(results) == 2
    for result in results:
        assert set(result.keys()) == {
            "ticket_id",
            "title",
            "category",
            "priority",
            "solution",
            "team",
            "score",
        }
