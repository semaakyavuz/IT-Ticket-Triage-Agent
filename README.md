# IT Ticket Triage Agent

[![CI](https://github.com/semaakyavuz/IT-Ticket-Triage-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/semaakyavuz/IT-Ticket-Triage-Agent/actions/workflows/ci.yml)
[![Canlı demo](https://img.shields.io/badge/canl%C4%B1%20demo-Render-46E3B7)](https://it-ticket-triage-agent.onrender.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Bir IT destek talebini yazarsın; **LangGraph tabanlı agent** onu kategorize eder
(donanım / yazılım / ağ / erişim), önceliklendirir, geçmiş ticket'larda **RAG**
ile benzer çözüm arar ve ya çözüm önerir ya da doğru ekibe yönlendirir. Sonuçlar
güven yüzdesi, geçmiş tablosu, manuel düzeltme ve tekrarlayan sorun uyarısı olan
bir dashboard'da görünür.

**▶ Canlı demo:** https://it-ticket-triage-agent.onrender.com — ücretsiz sunucu 15 dk
boş kalınca uyur, ilk açılış ~1 dk sürebilir.

<!-- Ekran görüntüsü / GIF: docs/demo.gif -->

## Nasıl çalışıyor?

```
Tarayıcı ──POST /ticket──▶ FastAPI (app/main.py)
                               │  rate limit, ticket geçmişine yaz
                               ▼
                    LangGraph agent (app/agent/graph.py)
                     ├─ get_priority            kural tabanlı öncelik
                     ├─ search_similar_tickets  ChromaDB'de RAG (cosine)
                     ├─ assign_team             kategori → ekip
                     └─ finalize                alanları tool izinden çıkar,
                                                güven skoru, tek cümle Türkçe
                               ▼
                    JSON yanıt + SQLite (ticket_history) + frontend
```

Modeli kim sağlıyor? Tek dosya: `app/providers.py`, iki ortam değişkeni:

| | Local (varsayılan, key yok) | Canlı demo (ücretsiz, kart yok) |
| --- | --- | --- |
| LLM (`LLM_PROVIDER`) | Ollama `llama3.2` | Groq `qwen/qwen3.8-27b` |
| Embedding (`EMBEDDING_PROVIDER`) | Ollama `nomic-embed-text` | Gemini `gemini-embedding-001` (768d) |

Seed ticket'ların embedding'leri repoda önbelleklidir (`app/rag/embedding_cache/`);
sunucu her açılışta index'i API'ye gitmeden kurar, API'ye sadece sorgular gider.

## Çalıştırma

**Local (Ollama):**

```bash
python -m venv venv && venv\Scripts\activate      # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2 && ollama pull nomic-embed-text
uvicorn app.main:app --reload                    # http://localhost:8000
```

Açılışta SQLite ve vektör index'i otomatik kurulur; ayrı bir script gerekmez.

**Groq + Gemini ile local:** `.env.example`'ı `.env` olarak kopyala, `GROQ_API_KEY`,
`GEMINI_API_KEY` gir ve `LLM_PROVIDER=groq`, `EMBEDDING_PROVIDER=gemini` yap.

**Docker:**

```bash
docker build -t triage-agent .
docker run -p 7860:7860 --env-file .env triage-agent   # http://localhost:7860
```

**Test:** `pytest -q` — 55 test; Ollama, Groq, Gemini ya da internet gerekmez
(sahte embedding / sahte agent, test başına izole SQLite ve Chroma).

## API

| Yöntem | Yol | Açıklama |
| --- | --- | --- |
| `POST` | `/ticket` | Triage: kategori, öncelik, güven, benzer ticket'lar, çözüm, ekip, `ticket_id` |
| `GET` | `/tickets/history` | Ticket geçmişi (en yeni üstte) |
| `PATCH` | `/tickets/history/{id}` | Manuel kategori düzeltmesi `{"corrected_category": "ağ"}` |
| `GET` | `/tickets/alerts` | Son 7 günde 3'ten fazla ticket gelen kategoriler |
| `GET` | `/health` | Canlılık + kullanılan sağlayıcı/model |
| `GET` | `/docs` | OpenAPI |

Örnek yanıt (Groq `qwen/qwen3.8-27b` ile gerçek çalıştırmadan; `score` temsilî):

```json
{
  "ticket_id": 19,
  "category": "donanım",
  "priority": "orta",
  "confidence": 91,
  "similar_tickets": [
    {"ticket_id": 4, "title": "Laptop açılmıyor, güç ışığı yanmıyor", "category": "donanım",
     "priority": "yüksek", "solution": "Adaptör arızalıydı, yenisiyle değiştirildi.",
     "team": "Donanım Destek Ekibi", "score": 0.099}
  ],
  "solution": "Adaptör arızalı olabilir, lütfen yenisiyle değiştirin.",
  "assigned_team": "Donanım Destek Ekibi"
}
```

## Deploy (Render, ücretsiz)

1. [console.groq.com](https://console.groq.com) → Groq API key;
   [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → Gemini API key.
2. [render.com](https://render.com) → GitHub ile giriş → **New → Blueprint** → bu repo.
   `render.yaml` servisi ücretsiz planda, Dockerfile ile tanımlar.
3. Sorulan `GROQ_API_KEY` ve `GEMINI_API_KEY` alanlarına key'leri yapıştır. İlk
   build ~3-5 dk; `main`'e her push otomatik deploy olur.

Seed verisi ya da embedding modeli değişirse önbelleği yenile ve commit'le:
`python -m scripts.cache_seed_embeddings` (`EMBEDDING_PROVIDER=gemini` + key ile).

## Ortam değişkenleri

| Değişken | Varsayılan | Açıklama |
| --- | --- | --- |
| `LLM_PROVIDER` | `ollama` | `ollama` \| `groq` |
| `EMBEDDING_PROVIDER` | `ollama` | `ollama` \| `gemini` |
| `OLLAMA_BASE_URL` / `OLLAMA_CHAT_MODEL` / `OLLAMA_EMBED_MODEL` | `http://localhost:11434` / `llama3.2` / `nomic-embed-text` | Local Ollama |
| `GROQ_API_KEY` | — | `groq` için zorunlu (secret) |
| `GROQ_MODEL` | `qwen/qwen3.8-27b` | Ücretsiz katmanda erişilebilen, tool-calling'i tutarlı model |
| `GROQ_REASONING_EFFORT` | `none` | Qwen "düşünme" token'larını kapatır |
| `GROQ_MAX_TOKENS` | `256` | İstek başına çıktı sınırı (ücretsiz kota ~1000 token/dk) |
| `GEMINI_API_KEY` | — | `gemini` için zorunlu (secret) |
| `GEMINI_EMBED_MODEL` / `GEMINI_EMBED_DIM` | `gemini-embedding-001` / `768` | Embedding modeli ve boyutu |
| `SQLITE_DB_PATH` / `CHROMA_PERSIST_DIR` | `./data/tickets.db` / `./data/chroma` | Depolama (commit edilmez) |
| `AUTO_INDEX` | `true` | Açılışta index boşsa kur |
| `DEMO_SEED_HISTORY` | `false` (Docker'da `true`) | Geçmiş boşsa demo kayıtları ekle |
| `RATE_LIMIT_PER_MINUTE` | `10` | `/ticket` için IP başına sınır (`0` = kapalı) |

## Proje yapısı

```
app/
  main.py          FastAPI endpoint'leri, açılışta DB + index kurulumu, static frontend
  config.py        Tüm ayarlar (ortam değişkenleri)
  providers.py     LLM / embedding sağlayıcı seçimi (+ Gemini istemcisi, embedding önbelleği)
  ratelimit.py     IP başına istek sınırı
  schemas.py       İstek/yanıt modelleri
  agent/           graph.py (LangGraph), tools.py (3 tool), state.py
  rag/             vector_store.py (ChromaDB), embedding_cache/ (seed embedding'leri)
  db/              database.py (SQLite), seed_data.py (28 mock ticket), demo_history.py
  static/          Frontend: index.html, css/, js/, vendor/chart.min.js
scripts/           cache_seed_embeddings.py
tests/             55 test
Dockerfile · render.yaml · .github/workflows/ci.yml
```

## Öne çıkan kararlar

- **Yapısal alanlar LLM metninden değil, tool izinden çıkarılır** — modelin kusursuz
  JSON üretmesine bağımlı kalınmaz (`_finalize_node`).
- **Son cümle ayrı, tool'suz bir LLM çağrısıyla üretilir** — tek döngüde hem tool-calling
  hem dil/format kısıtı küçük modelde güvenilir çalışmadı; bu ayrımla İngilizce girdi
  dahil hep tek cümle Türkçe.
- **Ücretsiz katmana göre ölçülerek tasarlandı** — Groq ücretsiz katmanında Llama yok;
  erişilebilen modeller ölçüldü, Qwen seçildi. Dakikada ~1000 çıktı token'ı kotası için
  `max_tokens`, kısa cümle ve plan tamamlanınca gereksiz agent turunu atlayan yönlendirme
  (LLM çağrısı 4 → 2): 5 ticket 7.2 sn. Sunucu içi embedding 512 MB'ta OOM verince
  Gemini API + repo içi embedding önbelleği.
- **Testler dış servise bağımlı değil**; CI Ollama'sız yeşil.
- **Dürüst sınırlar** — 3B'lik local model yakın kategorileri ara sıra karıştırır;
  RAG yine doğru geçmiş ticket'ı bulur. Manuel düzeltme verisi bunun için toplanır.

## Lisans

MIT — bkz. [LICENSE](LICENSE).
