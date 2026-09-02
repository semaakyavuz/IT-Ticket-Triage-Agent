import json

from langchain_core.tools import tool

from app.rag.vector_store import get_default_vector_store, search_similar

HIGH_PRIORITY_KEYWORDS = [
    "üretim",
    "production",
    "çöktü",
    "kesildi",
    "erişilemiyor",
    "erişilemez",
    "tüm ekip",
    "tüm ofis",
    "kritik",
    "acil",
    "risk altında",
]

LOW_PRIORITY_KEYWORDS = [
    "talep",
    "nasıl yapılır",
    "bilgi almak istiyorum",
    "yeni işe başlayan",
    "kurulum talebi",
]

# Kategoriye göre varsayılan öncelik: hiçbir anahtar kelime eşleşmediğinde kullanılır.
CATEGORY_DEFAULT_PRIORITY = {
    "ağ": "orta",
    "donanım": "orta",
    "yazılım": "orta",
    "erişim": "düşük",
}

TEAM_BY_CATEGORY = {
    "donanım": "Donanım Destek Ekibi",
    "yazılım": "Uygulama Destek Ekibi",
    "ağ": "Network Operasyon Ekibi",
    "erişim": "Erişim ve Kimlik Yönetimi Ekibi",
}
DEFAULT_TEAM = "Service Desk"


@tool
def search_similar_tickets(query: str) -> str:
    """Geçmiş ticket'lar arasında (RAG ile) semantik olarak en benzer olanları bulur.

    Args:
        query: Kullanıcının bildirdiği IT sorununun metni.
    """
    results = search_similar(get_default_vector_store(), query)
    return json.dumps(results, ensure_ascii=False)


@tool
def get_priority(category: str, keywords: str) -> str:
    """Kategori ve ticket metnindeki anahtar kelimelere göre öncelik döndürür.

    Args:
        category: Ticket'ın kategorisi (donanım/yazılım/ağ/erişim).
        keywords: Önceliği etkileyebilecek anahtar kelimeler veya ticket metninin kendisi.

    Returns:
        "düşük", "orta" veya "yüksek".
    """
    text = keywords.lower()
    if any(k in text for k in HIGH_PRIORITY_KEYWORDS):
        return "yüksek"
    if any(k in text for k in LOW_PRIORITY_KEYWORDS):
        return "düşük"
    return CATEGORY_DEFAULT_PRIORITY.get(category, "orta")


@tool
def assign_team(category: str) -> str:
    """Kategoriye göre ticket'ın yönlendirileceği destek ekibini döndürür.

    Args:
        category: Ticket'ın kategorisi (donanım/yazılım/ağ/erişim).
    """
    return TEAM_BY_CATEGORY.get(category, DEFAULT_TEAM)
