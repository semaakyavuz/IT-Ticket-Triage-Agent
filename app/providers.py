"""LLM ve embedding sağlayıcı fabrikaları.

Local geliştirmede Ollama (varsayılan; API key gerekmez, her şey makinede
çalışır). Canlı demoda (Hugging Face Spaces) LLM için Groq'un ücretsiz API'si,
embedding için sunucu içinde CPU'da çalışan fastembed (ONNX) kullanılır.

Seçim tamamen ortam değişkenleriyle yapılır (LLM_PROVIDER, EMBEDDING_PROVIDER);
agent/RAG kodu hangi sağlayıcının kullanıldığını bilmez. Sağlayıcı paketleri
fonksiyon içinde import edilir ki kullanılmayan sağlayıcının bağımlılığı
(ör. testlerde fastembed modeli) yüklenmek zorunda kalmasın.
"""

import re

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app import config


def get_chat_model(temperature: float = 0) -> BaseChatModel:
    if config.LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq

        if not config.GROQ_API_KEY:
            raise RuntimeError("LLM_PROVIDER=groq için GROQ_API_KEY ortam değişkeni tanımlı olmalı")
        return ChatGroq(model=config.GROQ_MODEL, api_key=config.GROQ_API_KEY, temperature=temperature)

    if config.LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=config.OLLAMA_CHAT_MODEL, base_url=config.OLLAMA_BASE_URL, temperature=temperature
        )

    raise ValueError(f"Bilinmeyen LLM_PROVIDER: {config.LLM_PROVIDER!r} (beklenen: ollama | groq)")


class FastEmbedEmbeddings(Embeddings):
    """fastembed'i LangChain'in Embeddings arayüzüne saran ince bir katman."""

    def __init__(self, model_name: str, cache_dir: str):
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(iter(self._model.query_embed(text))).tolist()


def get_embeddings() -> Embeddings:
    if config.EMBEDDING_PROVIDER == "fastembed":
        return FastEmbedEmbeddings(config.FASTEMBED_MODEL, config.FASTEMBED_CACHE_DIR)

    if config.EMBEDDING_PROVIDER == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=config.OLLAMA_EMBED_MODEL, base_url=config.OLLAMA_BASE_URL)

    raise ValueError(
        f"Bilinmeyen EMBEDDING_PROVIDER: {config.EMBEDDING_PROVIDER!r} (beklenen: ollama | fastembed)"
    )


def embedding_model_name() -> str:
    if config.EMBEDDING_PROVIDER == "fastembed":
        return config.FASTEMBED_MODEL
    return config.OLLAMA_EMBED_MODEL


def llm_model_name() -> str:
    if config.LLM_PROVIDER == "groq":
        return config.GROQ_MODEL
    return config.OLLAMA_CHAT_MODEL


def collection_name() -> str:
    """Embedding modeline göre ayrı Chroma koleksiyonu.

    Farklı modeller farklı boyutta vektör üretir; aynı koleksiyona yazmak
    boyut uyuşmazlığı hatasıyla sonuçlanır. Sağlayıcı/model değiştiğinde
    koleksiyon adı da değiştiği için eski index sessizce devre dışı kalır ve
    yeniden indexleme gerekir (scripts/index_tickets.py veya açılışta otomatik).
    """
    model_slug = embedding_model_name().split("/")[-1]
    raw = f"tickets_{config.EMBEDDING_PROVIDER}_{model_slug}"
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", raw)[:63]
    return safe.rstrip("_-")


def describe_providers() -> dict:
    """/health için, sır içermeyen sağlayıcı özeti."""
    return {
        "llm_provider": config.LLM_PROVIDER,
        "llm_model": llm_model_name(),
        "embedding_provider": config.EMBEDDING_PROVIDER,
        "embedding_model": embedding_model_name(),
    }
