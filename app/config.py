"""Tüm ayarlar tek yerde; hepsi ortam değişkeninden (.env) okunur.

Local (varsayılan): Ollama + Ollama, key gerekmez.
Canlı demo (Render):  Groq + Gemini, ikisi de ücretsiz katman (bkz. app/providers.py).
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _env_flag(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# --- Sağlayıcı seçimi ----------------------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()  # ollama | groq
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()  # ollama | gemini

# --- Ollama (local) -------------------------------------------------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# --- Groq (canlı demo LLM'i) -----------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Ücretsiz katmanda Llama 3.x yok; tool-calling'i en tutarlı uygulayan açık model.
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
# Qwen'in "düşünme" token'larını kapatır; desteklemeyen modelde boş bırak.
GROQ_REASONING_EFFORT = os.getenv("GROQ_REASONING_EFFORT", "none")
# Ücretsiz katman dakikada ~1000 çıktı token'ı verir ve her istekte max_tokens
# kadar rezerve eder; tool çağrısı + tek cümle için 256 fazlasıyla yeterli.
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "256"))

# --- Gemini (canlı demo embedding'i) ---------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
GEMINI_EMBED_DIM = int(os.getenv("GEMINI_EMBED_DIM", "768"))

# --- Depolama ------------------------------------------------------------------
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./data/tickets.db")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")

# --- Açılış davranışı / demo -----------------------------------------------------
# Açılışta vektör index'i boşsa mock ticket'ları otomatik indexle.
AUTO_INDEX = _env_flag("AUTO_INDEX", True)
# Geçmiş tablosu boşsa gerçekçi demo geçmişi ekle (canlı demoda dashboard boş kalmasın).
DEMO_SEED_HISTORY = _env_flag("DEMO_SEED_HISTORY", False)
# /ticket için IP başına dakikalık istek sınırı (0 = kapalı).
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

# --- Alan sabitleri --------------------------------------------------------------
CATEGORIES = ["donanım", "yazılım", "ağ", "erişim"]
PRIORITIES = ["düşük", "orta", "yüksek"]
