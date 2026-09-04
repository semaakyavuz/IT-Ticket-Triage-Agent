"""Seed ticket'ların embedding'lerini hesaplayıp repoya önbellekler.

Kullanım (proje kök dizininden, hedef sağlayıcı ayarlarıyla):
    EMBEDDING_PROVIDER=gemini GEMINI_API_KEY=... python -m scripts.cache_seed_embeddings

Çıktı: app/rag/embedding_cache/<koleksiyon-adı>.json (commit edilir). Sunucu
açılışta index'i bu dosyadan kurar; embedding API'sine sadece kullanıcı
sorguları için gidilir. Seed verisi ya da model değişince yeniden çalıştır.
"""

from app.db.seed_data import TICKETS
from app.providers import describe_providers, embedding_cache_path, get_embeddings
from app.rag.vector_store import ticket_text


def main() -> None:
    embeddings = get_embeddings()
    texts = [ticket_text(t) for t in TICKETS]
    added = embeddings.warm(texts)
    print(
        f"{describe_providers()['embedding_model']}: {added} yeni embedding hesaplandı, "
        f"önbellekte toplam {embeddings.size} kayıt -> {embedding_cache_path()}"
    )


if __name__ == "__main__":
    main()
