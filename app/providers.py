"""LLM ve embedding sağlayıcı fabrikaları.

Local geliştirmede Ollama (varsayılan; API key gerekmez, her şey makinede
çalışır). Canlı demoda LLM için Groq'un ücretsiz API'si, embedding için ya
sunucu içinde CPU'da çalışan fastembed (ONNX, ~350 MB RAM) ya da RAM harcamayan
Google Gemini embedding API'si (ücretsiz katman; 512 MB'lık ücretsiz sunucular
için tercih edilen).

Seçim tamamen ortam değişkenleriyle yapılır (LLM_PROVIDER, EMBEDDING_PROVIDER);
agent/RAG kodu hangi sağlayıcının kullanıldığını bilmez. Sağlayıcı paketleri
fonksiyon içinde import edilir ki kullanılmayan sağlayıcının bağımlılığı
(ör. testlerde fastembed modeli) yüklenmek zorunda kalmasın.

Seed ticket'ların embedding'leri `app/rag/embedding_cache/<model>.json` içinde
repoya önbelleklenir (scripts/cache_seed_embeddings.py): sunucu her uyanışında
index'i API'ye hiç gitmeden kurar, sadece kullanıcı sorguları embed edilir.
"""

import hashlib
import json
import re
from pathlib import Path

import httpx
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app import config

EMBEDDING_CACHE_DIR = Path(__file__).resolve().parent / "rag" / "embedding_cache"


def get_chat_model(temperature: float = 0) -> BaseChatModel:
    if config.LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq

        if not config.GROQ_API_KEY:
            raise RuntimeError("LLM_PROVIDER=groq için GROQ_API_KEY ortam değişkeni tanımlı olmalı")
        extra = {}
        if config.GROQ_REASONING_EFFORT:
            extra["reasoning_effort"] = config.GROQ_REASONING_EFFORT
        return ChatGroq(
            model=config.GROQ_MODEL,
            api_key=config.GROQ_API_KEY,
            temperature=temperature,
            max_tokens=config.GROQ_MAX_TOKENS,
            **extra,
        )

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


class GeminiEmbeddings(Embeddings):
    """Google Gemini embedding REST API; ek SDK bağımlılığı yok (httpx zaten var).

    Belge/sorgu için farklı task type kullanılır (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY),
    boyut `output_dimensionality` ile küçültülür. Vektörler normalize değildir;
    Chroma koleksiyonu cosine kullandığı için sorun olmaz.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    BATCH_SIZE = 100

    def __init__(self, api_key: str, model: str, dimensions: int, client: httpx.Client | None = None):
        if not api_key:
            raise RuntimeError("EMBEDDING_PROVIDER=gemini için GEMINI_API_KEY ortam değişkeni tanımlı olmalı")
        self._model = model
        self._dimensions = dimensions
        # Key URL'de değil header'da: loglara/URL geçmişine sızmasın.
        self._client = client or httpx.Client(timeout=30, headers={"x-goog-api-key": api_key})
        if client is not None:
            self._client.headers["x-goog-api-key"] = api_key

    def _post(self, method: str, body: dict) -> dict:
        response = self._client.post(f"{self.BASE_URL}/{self._model}:{method}", json=body)
        response.raise_for_status()
        return response.json()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.BATCH_SIZE):
            chunk = texts[start : start + self.BATCH_SIZE]
            body = {
                "requests": [
                    {
                        "model": f"models/{self._model}",
                        "content": {"parts": [{"text": text}]},
                        "taskType": "RETRIEVAL_DOCUMENT",
                        "outputDimensionality": self._dimensions,
                    }
                    for text in chunk
                ]
            }
            data = self._post("batchEmbedContents", body)
            vectors.extend(item["values"] for item in data["embeddings"])
        return vectors

    def embed_query(self, text: str) -> list[float]:
        body = {
            "content": {"parts": [{"text": text}]},
            "taskType": "RETRIEVAL_QUERY",
            "outputDimensionality": self._dimensions,
        }
        return self._post("embedContent", body)["embedding"]["values"]


class CachedEmbeddings(Embeddings):
    """Belge embedding'lerini metin hash'iyle önbellekten okuyan sarmalayıcı.

    Önbellekte olmayan metinler alttaki sağlayıcıya gider; sorgular her zaman
    sağlayıcıya gider. `warm()` eksikleri hesaplayıp dosyaya yazar.
    """

    def __init__(self, inner: Embeddings, cache_path: Path):
        self._inner = inner
        self._path = cache_path
        self._cache: dict[str, list[float]] = {}
        if cache_path.exists():
            self._cache = json.loads(cache_path.read_text(encoding="utf-8"))

    @staticmethod
    def key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @property
    def size(self) -> int:
        return len(self._cache)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float] | None] = [self._cache.get(self.key(t)) for t in texts]
        missing = [i for i, v in enumerate(vectors) if v is None]
        if missing:
            fresh = self._inner.embed_documents([texts[i] for i in missing])
            for i, vector in zip(missing, fresh):
                vectors[i] = vector
        return vectors  # type: ignore[return-value]

    def embed_query(self, text: str) -> list[float]:
        return self._inner.embed_query(text)

    def warm(self, texts: list[str], decimals: int = 6) -> int:
        """Eksik metinleri embed edip önbelleği diske yazar; eklenen sayısını döner."""
        missing = [t for t in texts if self.key(t) not in self._cache]
        if missing:
            for text, vector in zip(missing, self._inner.embed_documents(missing)):
                self._cache[self.key(text)] = [round(x, decimals) for x in vector]
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._cache), encoding="utf-8")
        return len(missing)


def _raw_embeddings() -> Embeddings:
    if config.EMBEDDING_PROVIDER == "fastembed":
        return FastEmbedEmbeddings(config.FASTEMBED_MODEL, config.FASTEMBED_CACHE_DIR)

    if config.EMBEDDING_PROVIDER == "gemini":
        return GeminiEmbeddings(config.GEMINI_API_KEY, config.GEMINI_EMBED_MODEL, config.GEMINI_EMBED_DIM)

    if config.EMBEDDING_PROVIDER == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=config.OLLAMA_EMBED_MODEL, base_url=config.OLLAMA_BASE_URL)

    raise ValueError(
        f"Bilinmeyen EMBEDDING_PROVIDER: {config.EMBEDDING_PROVIDER!r} (beklenen: ollama | fastembed | gemini)"
    )


def embedding_cache_path() -> Path:
    return EMBEDDING_CACHE_DIR / f"{collection_name()}.json"


def get_embeddings() -> Embeddings:
    """Seçili sağlayıcı, seed ticket önbelleğiyle sarılmış olarak."""
    return CachedEmbeddings(_raw_embeddings(), embedding_cache_path())


def embedding_model_name() -> str:
    if config.EMBEDDING_PROVIDER == "fastembed":
        return config.FASTEMBED_MODEL
    if config.EMBEDDING_PROVIDER == "gemini":
        return f"{config.GEMINI_EMBED_MODEL}-{config.GEMINI_EMBED_DIM}d"
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
