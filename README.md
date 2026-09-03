---
title: IT Ticket Triage Agent
emoji: 🎫
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# IT Ticket Triage Agent

[![CI](https://github.com/semaakyavuz/IT-Ticket-Triage-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/semaakyavuz/IT-Ticket-Triage-Agent/actions/workflows/ci.yml)
[![Canlı demo](https://img.shields.io/badge/canl%C4%B1%20demo-Hugging%20Face%20Spaces-yellow)](https://huggingface.co/spaces/semaakyavuz/it-ticket-triage-agent)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

IT destek taleplerini **LangGraph tabanlı bir agent** ile otomatik kategorize eden,
önceliklendiren, geçmiş ticket'lardan **RAG** ile çözüm öneren ya da doğru ekibe
yönlendiren uygulama. Kararların **güven yüzdesi**, geçmiş tablosu, manuel düzeltme
ve tekrarlayan sorun uyarısı içeren bir dashboard ile birlikte gelir.

**▶ Canlı demo:** https://huggingface.co/spaces/semaakyavuz/it-ticket-triage-agent
&nbsp;·&nbsp; Local'de tamamen **Ollama** ile (API key'siz) çalışır; canlı demo aynı
kodu **Groq** (Llama 3.3 70B) + sunucu içi embedding ile çalıştırır.

<!-- Ekran görüntüsü / GIF: docs/demo.gif -->

## Neler yapıyor?

| Özellik | Nasıl |
| --- | --- |
| Kategori + öncelik | LangGraph agent'ı (Llama) sorunu `donanım / yazılım / ağ / erişim` olarak sınıflar; `get_priority` tool'u kural tabanlı `düşük / orta / yüksek` döner |
| RAG ile çözüm önerisi | `search_similar_tickets` tool'u geçmiş ticket'ları ChromaDB'de (cosine) arar, en benzer çözümleri getirir |
| Ekibe yönlendirme | Benzer çözüm yoksa `assign_team` tool'u kategoriye göre ekibe yönlendirir |
| Güven yüzdesi | En benzer ticket'ın mesafe skorundan türetilen 0-100 gösterge |
| Ticket geçmişi | Her istek SQLite'a yazılır; ana sayfada tablo, dashboard'da kategori/öncelik dağılımı (Chart.js) |
| Manuel düzeltme | "Kategori yanlış mı?" → düzeltme `corrected_category` olarak kaydedilir (ileride eğitim/eval verisi) |
| Tekrarlayan sorun uyarısı | Son 7 günde bir kategoriden 3'ten fazla ticket → dashboard'da uyarı (basit SQL) |
| Herkese açık demo sertleştirmesi | IP başına rate limit, girdi uzunluk sınırı, `/health`, sağlayıcı hatasında anlaşılır 503 |

## Mimari

```
Kullanıcı ──POST /ticket──▶ FastAPI ──▶ LangGraph agent (ReAct: sadece tool çağırır)
                                          │
                     ┌────────────────────┼────────────────────┐
                     ▼                    ▼                    ▼
              get_priority          assign_team        search_similar_tickets
              (kural tabanlı)       (kategori → ekip)   (ChromaDB + embedding, RAG)
                     │                    │                    │
                     └────────────────────┴────────────────────┘
                                          ▼
                       finalize: yapısal alanlar tool izinden çıkarılır,
                       güven skoru hesaplanır, son cümle AYRI (tool'suz)
                       bir LLM çağrısıyla tek cümle Türkçe üretilir
                                          ▼
                     JSON yanıt + SQLite ticket_history + frontend
```

**Stack:** Python · FastAPI · LangChain / LangGraph · ChromaDB · SQLite ·
Ollama (local) / Groq + fastembed (canlı) · vanilla JS + Chart.js (build aracı yok) ·
Docker · GitHub Actions · pytest.

## Öne çıkan mühendislik kararları

Bunların hepsi gerçek model çıktıları üzerinde denenerek alındı; commit
geçmişinde ölçümleriyle birlikte duruyor.

- **Yapısal alanlar LLM metninden değil, tool izinden çıkarılır.** `category`,
  `priority`, `assigned_team`, `similar_tickets`; agent'ın gerçekte hangi tool'u
  hangi argümanla çağırdığından deterministik olarak türetilir
  (`app/agent/graph.py` → `_finalize_node`). Küçük bir modelin her seferinde
  kusursuz JSON üretmesine bağımlı kalınmaz.
- **Son cümle ayrı, tool'suz bir LLM çağrısıyla üretilir.** Tek bir ReAct
  döngüsüne hem tool-calling hem dil/format kısıtlarını aynı anda uygulatmak
  küçük modelde güvenilir çalışmadı (İngilizce girdi → İngilizce, madde işaretli
  yanıt). Tool'ları hiç görmeyen ayrı bir model, sade bir prompt'la tek cümle
  Türkçe üretiyor; üç senaryoda da (İngilizce girdi dahil) doğrulandı.
- **Sağlayıcı soyutlaması.** `LLM_PROVIDER` / `EMBEDDING_PROVIDER` ile Ollama ↔
  Groq / fastembed arasında geçiş; agent ve RAG kodu sağlayıcıyı bilmez
  (`app/providers.py`). Böylece repo "tamamen local, API key'siz" kalırken canlı
  demo ücretsiz bulut bileşenleriyle çalışır.
- **Cosine mesafe + modele göre koleksiyon adı.** fastembed vektörleri normalize
  olmadığı için L2 mesafeleri 5-17'ye çıkıp güven yüzdesini anlamsızlaştırıyordu;
  cosine ile sağlayıcıdan bağımsız 0-2 aralığı. Farklı boyutlu modeller aynı
  koleksiyona yazamaz.
- **Testler dış servise bağımlı değil.** Sahte embedding / sahte agent grafiği,
  test başına izole SQLite ve Chroma koleksiyonu; CI Ollama'sız yeşil. Bu
  izolasyon, Chroma'nın süreç içinde paylaşılan bellek içi client'ından kaynaklanan
  gizli bir test sızıntısını da ortaya çıkardı ve giderdi.
- **Dürüst sınırlar.** 3B'lik local model yakın kategorileri (ağ/erişim) ara
  sıra karıştırabiliyor; RAG bu durumda bile doğru geçmiş ticket'ı buluyor.
  Canlı demodaki 70B model belirgin şekilde daha tutarlı. Bu tam da manuel
  düzeltme verisinin toplanma nedeni.

## API

| Yöntem | Yol | Açıklama |
| --- | --- | --- |
| `POST` | `/ticket` | Ticket'ı triage eder; kategori, öncelik, güven, benzer ticket'lar, çözüm, ekip, `ticket_id` döner |
| `GET` | `/tickets/history` | Ticket geçmişi (en yeni üstte) |
| `PATCH` | `/tickets/history/{id}` | Manuel kategori düzeltmesi (`{"corrected_category": "ağ"}`) |
| `GET` | `/tickets/alerts` | Son 7 günde eşiği aşan kategoriler |
| `GET` | `/health` | Canlılık + kullanılan sağlayıcı/model (sır içermez) |
| `GET` | `/docs` | OpenAPI arayüzü |

Örnek — gerçek çıktı (local Ollama, `llama3.2` + `nomic-embed-text`):

```bash
curl -X POST http://localhost:8000/ticket -H "Content-Type: application/json" \
  -d '{"text": "Laptopum açılmıyor, güç ışığı hiç yanmıyor"}'
```

```json
{
  "ticket_id": 1,
  "category": "donanım",
  "priority": "orta",
  "confidence": 88,
  "similar_tickets": [
    {
      "ticket_id": 4,
      "title": "Laptop açılmıyor, güç ışığı yanmıyor",
      "category": "donanım",
      "priority": "yüksek",
      "solution": "Adaptör arızalıydı, yenisiyle değiştirildi.",
      "team": "Donanım Destek Ekibi",
      "score": 0.132
    }
  ],
  "solution": "Adaptörün yenilenmesi gerektiği için donanım desteği ekibine yönlendirildi.",
  "assigned_team": "Donanım Destek Ekibi"
}
```

> Windows + Git Bash'te `-d '...'` içindeki Türkçe karakterler bozulabilir; isteği
> UTF-8 bir `.json` dosyasına yazıp `--data-binary @dosya.json` ile gönder.

## Local kurulum (Ollama, API key'siz)

```bash
python -m venv venv
venv\Scripts\activate            # Windows  |  source venv/bin/activate
pip install -r requirements.txt

ollama pull llama3.2             # https://ollama.com kurulu olmalı
ollama pull nomic-embed-text

uvicorn app.main:app --reload    # açılışta DB + vektör index'i otomatik kurulur
# http://localhost:8000
```

`python -m scripts.init_db` ve `python -m scripts.index_tickets` ile aynı işlemler
elle de yapılabilir. `.env.example` → `.env` kopyalayıp sağlayıcı/model
ayarlarını değiştirebilirsin.

## Test

```bash
pytest -q
```

Testler Ollama'ya, Groq'a ya da internete bağımlı değildir: `search_similar_tickets`
için deterministik sahte embedding, `/ticket` için sahte agent grafiği, agent
grafiği için mesaj şekline göre tool çağrısı üreten sahte LLM; her test kendi
geçici SQLite dosyasını ve Chroma koleksiyonunu kullanır. CI aynı suite'i
`.github/workflows/ci.yml` ile çalıştırır.

## Canlı demo & deploy (Hugging Face Spaces)

Canlı demo, local'deki Ollama yerine iki ücretsiz bileşenle çalışır (kod aynı,
sadece ortam değişkenleri farklı — bkz. `app/providers.py`):

| Bileşen    | Local (varsayılan)             | Canlı demo (Dockerfile varsayılanı)                  |
| ---------- | ------------------------------ | ---------------------------------------------------- |
| LLM        | Ollama `llama3.2`              | Groq API, `llama-3.3-70b-versatile` (ücretsiz katman) |
| Embedding  | Ollama `nomic-embed-text`      | fastembed `paraphrase-multilingual-MiniLM-L12-v2` (sunucu içi, CPU) |
| Veri       | `./data` (kalıcı)              | Container diski (yeniden başlatınca sıfırlanır; açılışta otomatik seed + index) |

Adımlar:

1. [console.groq.com](https://console.groq.com) → ücretsiz **API key** al.
2. [huggingface.co/new-space](https://huggingface.co/new-space) → SDK: **Docker**,
   görünürlük: Public (bu proje: `semaakyavuz/it-ticket-triage-agent`).
3. Space → **Settings → Variables and secrets** → Secret: `GROQ_API_KEY`.
   (İsteğe bağlı: `GROQ_MODEL`, `RATE_LIMIT_PER_MINUTE`, `DEMO_SEED_HISTORY`.)
4. Otomatik deploy için GitHub repo → **Settings**:
   - Secret `HF_TOKEN`: Hugging Face **write** yetkili erişim token'ı
   - Variable `HF_SPACE`: `semaakyavuz/it-ticket-triage-agent`
   `main`'e her push'ta CI geçerse `.github/workflows/deploy-hf.yml` repo'yu
   Space'e push eder; Space kendi Docker build'ini yapar (~3-5 dk).
5. Alternatif, elle: `git push https://huggingface.co/spaces/semaakyavuz/it-ticket-triage-agent main`.

Local'de aynı imajı denemek için:

```bash
docker build -t triage-agent .
docker run -p 7860:7860 -e GROQ_API_KEY=gsk_... triage-agent
# http://localhost:7860
```

Notlar: Space 48 saat kullanılmazsa uyur, ilk istekte ~30 sn'de uyanır.
`/ticket` IP başına dakikada 10 istekle sınırlıdır (tek bir ziyaretçinin Groq
kotasını tüketmemesi için). Demo verisi her yeniden başlatmada sıfırlanır.

## Ortam değişkenleri

| Değişken                 | Varsayılan                                   | Açıklama                                                        |
| ------------------------ | -------------------------------------------- | --------------------------------------------------------------- |
| `LLM_PROVIDER`           | `ollama`                                     | `ollama` \| `groq`                                              |
| `EMBEDDING_PROVIDER`     | `ollama`                                     | `ollama` \| `fastembed`                                         |
| `OLLAMA_BASE_URL`        | `http://localhost:11434`                     | Ollama sunucu adresi                                            |
| `OLLAMA_CHAT_MODEL`      | `llama3.2`                                   | Ollama LLM'i (tool-calling + son cümle)                         |
| `OLLAMA_EMBED_MODEL`     | `nomic-embed-text`                           | Ollama embedding modeli                                         |
| `GROQ_API_KEY`           | —                                            | `LLM_PROVIDER=groq` iken zorunlu (secret, commit edilmez)       |
| `GROQ_MODEL`             | `llama-3.3-70b-versatile`                    | Groq modeli                                                     |
| `FASTEMBED_MODEL`        | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Sunucu içi çok dilli embedding modeli          |
| `FASTEMBED_CACHE_DIR`    | `./data/fastembed`                           | fastembed model önbelleği (Docker'da imaja gömülür)             |
| `SQLITE_DB_PATH`         | `./data/tickets.db`                          | Mock ticket verisi + ticket geçmişi (SQLite)                    |
| `CHROMA_PERSIST_DIR`     | `./data/chroma`                              | Chroma'nın kalıcı vector index dizini                           |
| `AUTO_INDEX`             | `true`                                       | Açılışta index boşsa mock ticket'ları otomatik indexle          |
| `DEMO_SEED_HISTORY`      | `false` (Docker'da `true`)                   | Geçmiş boşsa gerçekçi demo geçmişi ekle                         |
| `RATE_LIMIT_PER_MINUTE`  | `10`                                         | `/ticket` için IP başına dakikalık sınır (`0` = kapalı)         |

Embedding sağlayıcısı/modeli değiştiğinde Chroma koleksiyon adı da değişir
(farklı boyutlu vektörler aynı koleksiyona yazılamaz); `AUTO_INDEX` açıksa yeni
koleksiyon açılışta otomatik kurulur.

## Proje yapısı

```
app/
  main.py               FastAPI: /ticket, /tickets/*, /health, static frontend, açılış bootstrap
  config.py             Ortam değişkenleri ve sağlayıcı seçimi
  providers.py          LLM / embedding fabrikaları (ollama | groq, ollama | fastembed)
  ratelimit.py          IP başına kayan-pencere rate limit
  schemas.py            Pydantic request/response modelleri
  agent/
    graph.py            LangGraph grafiği: ReAct tool döngüsü + finalize + ayrı son-cümle çağrısı
    tools.py            search_similar_tickets, get_priority, assign_team
    state.py            Graf state şeması
  rag/vector_store.py   ChromaDB (cosine) index/arama, açılışta ensure_index
  db/
    database.py         SQLite şema, mock seed, ticket_history, düzeltme, uyarı sorgusu
    seed_data.py        28 kayıtlık mock geçmiş ticket
    demo_history.py     Canlı demo için gerçekçi geçmiş
  static/               Vanilla JS + Chart.js frontend (build aracı yok, Chart.js gömülü)
scripts/                init_db, index_tickets (elle çalıştırma için)
tests/                  49 test: tools, rag, agent grafiği, sağlayıcılar, rate limit, DB, API
Dockerfile              HF Spaces uyumlu imaj (embedding modeli gömülü)
.github/workflows/      ci.yml (pytest), deploy-hf.yml (Space'e push)
```

## Yol haritası

- Etiketli bir değerlendirme seti + `scripts/evaluate` (kategori/öncelik doğruluğu,
  model/prompt değişikliklerini sayıyla karşılaştırmak için)
- RAG destekli sınıflandırma (en benzer ticket'ların kategorisi LLM kararını
  desteklesin) ve düzeltmelerin Chroma'ya geri beslenmesi
- Agent adımlarının gerçek zamanlı akışı (SSE) — arayüzdeki zaman çizelgesi şu an
  istek sürerken simüle ediliyor

## Lisans

MIT — bkz. [LICENSE](LICENSE).
