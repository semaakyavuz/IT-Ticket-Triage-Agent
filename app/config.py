import os

from dotenv import load_dotenv

load_dotenv()

# Sağlayıcı seçimi: local geliştirmede "ollama" (API key gerekmez), canlı demoda
# (Hugging Face Spaces) "groq" + "fastembed". Uygulama kodu sağlayıcıyı bilmez,
# bkz. app/providers.py
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Ücretsiz katmanda Llama 3.x yok (2026); tool-calling'i en tutarlı uygulayan ve
# Türkçe'de güçlü açık model olarak Qwen seçildi (gpt-oss-120b RAG adımını atlıyordu).
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
# Qwen'in "düşünme" token'ları gecikmeyi 30 sn'ye çıkarabiliyor; "none" kapatır.
# Boş bırakılırsa parametre gönderilmez (reasoning desteklemeyen modeller için).
GROQ_REASONING_EFFORT = os.getenv("GROQ_REASONING_EFFORT", "none")
# Ücretsiz katman dakikada ~1000 çıktı token'ı verir ve her istekte max_tokens
# kadar rezerve eder; tool çağrısı + tek cümle için 256 fazlasıyla yeterli.
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "256"))

# Türkçe metin için çok dilli, sunucu içinde (ONNX, CPU) çalışan hafif bir model.
# Not: ~350 MB RAM ister; 512 MB'lık ücretsiz sunucularda (Render) OOM verir.
FASTEMBED_MODEL = os.getenv(
    "FASTEMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
FASTEMBED_CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR", "./data/fastembed")

# Google Gemini embedding API (ücretsiz katman, kart gerekmez): RAM harcamaz,
# 512 MB'lık ücretsiz sunucuda çalışan canlı demo için tercih edilen seçenek.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
# 3072 varsayılanı gereksiz büyük; 768 hem kaliteli hem küçük (önbellek dosyası + Chroma).
GEMINI_EMBED_DIM = int(os.getenv("GEMINI_EMBED_DIM", "768"))

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./data/tickets.db")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")


def _env_flag(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# Açılışta mock ticket'ları vektör index'ine otomatik ekle (index boşsa).
AUTO_INDEX = _env_flag("AUTO_INDEX", True)
# Canlı demo: geçmiş tablosu boşsa gerçekçi örnek geçmiş ekle (dashboard boş kalmasın).
DEMO_SEED_HISTORY = _env_flag("DEMO_SEED_HISTORY", False)

# /ticket için IP başına dakikalık istek sınırı (0 = kapalı). Herkese açık demoda
# tek bir ziyaretçinin LLM kotasını tüketmesini engeller.
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

CATEGORIES = ["donanım", "yazılım", "ağ", "erişim"]
PRIORITIES = ["düşük", "orta", "yüksek"]
