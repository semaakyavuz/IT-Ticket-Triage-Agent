import pytest

from app import config, providers


def test_collection_name_is_chroma_safe_and_provider_specific(monkeypatch):
    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "fastembed")
    monkeypatch.setattr(
        config, "FASTEMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    name = providers.collection_name()

    assert name == "tickets_fastembed_paraphrase-multilingual-MiniLM-L12-v2"
    assert 3 <= len(name) <= 63


def test_collection_name_changes_with_embedding_model(monkeypatch):
    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "ollama")
    monkeypatch.setattr(config, "OLLAMA_EMBED_MODEL", "nomic-embed-text")
    ollama_name = providers.collection_name()

    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "fastembed")
    fastembed_name = providers.collection_name()

    assert ollama_name != fastembed_name


def test_describe_providers_has_no_secrets(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(config, "GROQ_MODEL", "llama-3.3-70b-versatile")
    monkeypatch.setattr(config, "GROQ_API_KEY", "gsk_super_secret")

    info = providers.describe_providers()

    assert info["llm_provider"] == "groq"
    assert info["llm_model"] == "llama-3.3-70b-versatile"
    assert "gsk_super_secret" not in str(info)


def test_get_chat_model_requires_groq_api_key(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(config, "GROQ_API_KEY", "")

    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        providers.get_chat_model()


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "bilinmeyen")
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        providers.get_chat_model()

    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "bilinmeyen")
    with pytest.raises(ValueError, match="EMBEDDING_PROVIDER"):
        providers.get_embeddings()


def test_gemini_requires_api_key(monkeypatch):
    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "gemini")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        providers.get_embeddings()


class CountingEmbeddings:
    """Kac metnin gercekten saglayiciya gittigini sayan sahte embedding."""

    def __init__(self):
        self.document_calls: list[list[str]] = []

    def embed_documents(self, texts):
        self.document_calls.append(list(texts))
        return [[float(len(t)), 1.0] for t in texts]

    def embed_query(self, text):
        return [0.5, 0.5]


def test_cached_embeddings_serves_hits_and_persists_warm(tmp_path):
    inner = CountingEmbeddings()
    path = tmp_path / "cache.json"
    cached = providers.CachedEmbeddings(inner, path)

    assert cached.warm(["a", "bb"]) == 2
    assert path.exists() and cached.size == 2

    # Yeni bir instance dosyadan okur; bilinen metinler saglayiciya gitmez.
    inner2 = CountingEmbeddings()
    cached2 = providers.CachedEmbeddings(inner2, path)
    vectors = cached2.embed_documents(["a", "ccc", "bb"])

    assert inner2.document_calls == [["ccc"]]
    assert vectors == [[1.0, 1.0], [3.0, 1.0], [2.0, 1.0]]
    assert cached2.embed_query("x") == [0.5, 0.5]  # sorgular her zaman saglayiciya


def test_gemini_embeddings_request_shape_and_parsing():
    import httpx

    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith(":batchEmbedContents"):
            n = len(request.read() and httpx.Response(200, content=request.content).json()["requests"])
            return httpx.Response(200, json={"embeddings": [{"values": [0.1 * (i + 1), 0.2]} for i in range(n)]})
        return httpx.Response(200, json={"embedding": {"values": [0.9, 0.8]}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    emb = providers.GeminiEmbeddings("test-key", "gemini-embedding-001", 768, client=client)

    docs = emb.embed_documents(["ilk", "ikinci"])
    query = emb.embed_query("soru")

    assert docs == [[0.1, 0.2], [0.2, 0.2]]
    assert query == [0.9, 0.8]
    batch, single = seen
    assert batch.headers["x-goog-api-key"] == "test-key" and "test-key" not in str(batch.url)
    batch_body = httpx.Response(200, content=batch.content).json()
    assert batch_body["requests"][0]["taskType"] == "RETRIEVAL_DOCUMENT"
    assert batch_body["requests"][0]["outputDimensionality"] == 768
    single_body = httpx.Response(200, content=single.content).json()
    assert single_body["taskType"] == "RETRIEVAL_QUERY"


def test_collection_name_for_gemini_includes_dimension(monkeypatch):
    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "gemini")
    monkeypatch.setattr(config, "GEMINI_EMBED_MODEL", "gemini-embedding-001")
    monkeypatch.setattr(config, "GEMINI_EMBED_DIM", 768)

    assert providers.collection_name() == "tickets_gemini_gemini-embedding-001-768d"
