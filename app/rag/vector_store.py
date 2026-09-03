from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import CHROMA_PERSIST_DIR
from app.db.database import fetch_all_tickets
from app.providers import collection_name, get_embeddings

_default_store: Chroma | None = None


def get_vector_store(
    embeddings=None,
    persist_directory: str = CHROMA_PERSIST_DIR,
    name: str | None = None,
) -> Chroma:
    """`name` verilmezse koleksiyon adı embedding modelinden türetilir.

    Testler izole, benzersiz bir ad verir: Chroma'nın bellek içi client'ı aynı
    süreçte paylaşıldığı için aynı ada yazan testler birbirini etkiler.
    """
    embeddings = embeddings or get_embeddings()
    return Chroma(
        collection_name=name or collection_name(),
        embedding_function=embeddings,
        persist_directory=persist_directory,
        # Cosine: vektör normundan bağımsız, sağlayıcılar arasında tutarlı 0-2 aralığı.
        # Chroma'nın varsayılanı L2 idi; normalize edilmemiş embedding'lerde (fastembed)
        # mesafeler 5-17'ye çıkıp güven/benzerlik yüzdesini anlamsızlaştırıyordu.
        collection_metadata={"hnsw:space": "cosine"},
    )


def get_default_vector_store() -> Chroma:
    """Agent tool'larının kullandığı, lazy oluşturulan paylaşımlı vector store."""
    global _default_store
    if _default_store is None:
        _default_store = get_vector_store()
    return _default_store


def ensure_index(vector_store: Chroma | None = None, tickets: list[dict] | None = None) -> int:
    """Koleksiyon boşsa ticket'ları indexler. Eklenen kayıt sayısını döner.

    Açılışta çağrılır; her yeniden başlatmada diski sıfırlayan ortamlarda
    (Hugging Face Spaces) index'in elle kurulmasına gerek kalmaz.
    """
    vector_store = vector_store or get_default_vector_store()
    if vector_store.get(limit=1)["ids"]:
        return 0
    return index_tickets(vector_store, tickets)


def _ticket_to_document(ticket: dict) -> Document:
    content = f"{ticket['title']}\n{ticket['description']}"
    metadata = {
        "ticket_id": ticket["id"],
        "category": ticket["category"],
        "priority": ticket["priority"],
        "solution": ticket["solution"],
        "team": ticket["team"],
    }
    return Document(page_content=content, metadata=metadata)


def index_tickets(vector_store: Chroma, tickets: list[dict] | None = None) -> int:
    """Mock ticket'ları embed edip vector store'a ekler. Eklenen kayıt sayısını döner."""
    tickets = tickets if tickets is not None else fetch_all_tickets()
    if not tickets:
        return 0

    documents = [_ticket_to_document(t) for t in tickets]
    ids = [str(t["id"]) for t in tickets]
    vector_store.add_documents(documents=documents, ids=ids)
    return len(documents)


def search_similar(vector_store: Chroma, query: str, k: int = 3) -> list[dict]:
    """Sorguya en benzer geçmiş ticket'ları döner (score küçük = daha benzer)."""
    results = vector_store.similarity_search_with_score(query, k=k)
    return [
        {
            "ticket_id": doc.metadata["ticket_id"],
            "title": doc.page_content.split("\n", 1)[0],
            "category": doc.metadata["category"],
            "priority": doc.metadata["priority"],
            "solution": doc.metadata["solution"],
            "team": doc.metadata["team"],
            "score": score,
        }
        for doc, score in results
    ]
