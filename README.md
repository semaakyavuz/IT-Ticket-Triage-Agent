# IT Ticket Triage Agent

[![CI](https://github.com/semaakyavuz/IT-Ticket-Triage-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/semaakyavuz/IT-Ticket-Triage-Agent/actions/workflows/ci.yml)
[![Canlı demo](https://img.shields.io/badge/canl%C4%B1%20demo-Render-46E3B7)](https://it-ticket-triage-agent.onrender.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

IT destek taleplerini **LangGraph tabanlı bir agent** ile otomatik kategorize eden,
önceliklendiren, geçmiş ticket'lardan **RAG** ile çözüm öneren ya da doğru ekibe
yönlendiren uygulama. Kararların **güven yüzdesi**, geçmiş tablosu, manuel düzeltme
ve tekrarlayan sorun uyarısı içeren bir dashboard ile birlikte gelir.

**▶ Canlı demo:** https://it-ticket-triage-agent.onrender.com
&nbsp;·&nbsp; Local'de tamamen **Ollama** ile (API key'siz) çalışır; canlı demo aynı
kodu **Groq** (Qwen 3.8 27B) + **Gemini embedding** ile — ikisi de ücretsiz
katman, kart yok — çalıştırır. Ücretsiz sunucu 15 dk boş kalınca uyur; ilk
açılış ~1 dk sürebilir.

<!-- Ekran görüntüsü / GIF: docs/demo.gif -->

## Neler yapıyor?

| Özellik | Nasıl |
| --- | --- |
| Kategori + öncelik | LangGraph agent'ı sorunu `donanım / yazılım / ağ / erişim` olarak sınıflar; `get_priority` tool'u kural tabanlı `düşük / orta / yüksek` döner |
| RAG ile çözüm önerisi | `search_similar_tickets` tool'u geçmiş ticket'ları ChromaDB'de (cosine) arar, en benzer çözümleri getirir |
| Ekibe yönlendirme | Benzer çözüm yoksa `assign_team` tool'u kategoriye göre ekibe yönlendirir; varsa en benzer ticket'ı çözen ekip "ilgili ekip" olur |
| Güven yüzdesi | En benzer ticket'ın mesafe skorundan türetilen 0-100 gösterge |
| Ticket geçmişi | Her istek SQLite'a yazılır; ana sayfada tablo, dashboard'da kategori/öncelik dağılımı (Chart.js) |
| Manuel düzeltme | "Kategori yanlış mı?" → düzeltme `corrected_category` olarak kaydedilir (ileride eğitim/eval verisi) |
| Tekrarlayan sorun uyarısı | Son 7 günde bir kategoriden 3'ten fazla ticket → dashboard'da uyarı (basit SQL) |
| Herkese açık demo sertleştirmesi | IP başına rate limit, girdi uzunluk sınırı, `/health`, sağlayıcı hatasında anlaşılır 429/503 |

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
                 plan tamamsa agent'a dönmeden finalize: yapısal alanlar
                 tool izinden çıkarılır, güven skoru hesaplanır, son cümle
                 AYRI (tool'suz) bir LLM çağrısıyla tek cümle Türkçe üretilir
                                          ▼
                     JSON yanıt + SQLite ticket_history + frontend
```

**Stack:** Python · FastAPI · LangChain / LangGraph · ChromaDB · SQLite ·
Ollama (local) / Groq + fastembed (canlı) · vanilla JS + Chart.js (build aracı yok) ·
Docker · Render · GitHub Actions · pytest.

## Öne çıkan mühendislik kararları

Hepsi gerçek model çıktıları üzerinde ölçülerek alındı; ayrıntılar commit
geçmişinde.

- **Yapısal alanlar LLM metninden değil, tool izinden çıkarılır.** `category`,
  `priority`, `assigned_team`, `similar_tickets`; agent'ın gerçekte hangi tool'u
  hangi argümanla çağırdığından deterministik olarak türetilir
  (`app/agent/graph.py` → `_finalize_node`). Modelin her seferinde kusursuz
  JSON üretmesine bağımlı kalınmaz.
- **Son cümle ayrı, tool'suz bir LLM çağrısıyla üretilir.** Tek bir ReAct
  döngüsüne hem tool-calling hem dil/format kısıtlarını aynı anda uygulatmak
  küçük modelde güvenilir çalışmadı (İngilizce girdi → İngilizce, madde işaretli
  yanıt). Tool'ları hiç görmeyen ayrı bir model sade bir prompt'la tek cümle
  Türkçe üretir; İngilizce girdi dahil doğrulandı.
- **Ücretsiz katman gerçekleriyle tasarım.** Groq'un ücretsiz katmanında Llama 3.x
  yok ve dakikada ~1000 çıktı token'ı sınırı var. Erişilebilen modeller ölçüldü:
  `gpt-oss-120b` RAG adımını 3/4 atladı, `qwen3.8-27b` 9/9 doğru sınıfladı ve her
  seferinde RAG çağırdı → varsayılan Qwen. 30-36 sn'lik gecikmelerin kaynağı
  "düşünme" değil, kotaya takılan SDK retry'larıydı: `max_tokens=256`,
  ≤25 kelimelik son cümle ve **plan tamamlanınca gereksiz agent turunu atlayan**
  yönlendirme (`_after_tools`, LLM çağrısı 4 → 2) ile 5 ticket 7.2 sn'ye
  (~0.8 sn/ticket) düştü, 429 kalmadı.
- **Sağlayıcı soyutlaması.** `LLM_PROVIDER` / `EMBEDDING_PROVIDER` ile Ollama ↔
  Groq / fastembed / Gemini arasında geçiş; agent ve RAG kodu sağlayıcıyı bilmez
  (`app/providers.py`). Repo "tamamen local, API key'siz" kalırken canlı demo
  ücretsiz bulut bileşenleriyle çalışır.
- **512 MB'a sığmak.** Sunucu içi embedding (fastembed/ONNX) Docker'da 512 MB
  sınırıyla ölçüldü: açılışta OOM (exit 137). Çözüm: RAM harcamayan Gemini
  embedding API'si + seed ticket embedding'lerinin repoda önbelleklenmesi
  (`app/rag/embedding_cache/`, `CachedEmbeddings`). Uyuyan ücretsiz sunucu her
  uyanışında index'i API'ye hiç gitmeden kurar; API'ye sadece sorgular gider.
- **Cosine mesafe + modele göre koleksiyon adı.** fastembed vektörleri normalize
  olmadığı için L2 mesafeleri 5-17'ye çıkıp güven yüzdesini anlamsızlaştırıyordu;
  cosine ile sağlayıcıdan bağımsız 0-2 aralığı. Farklı boyutlu modeller aynı
  koleksiyona yazamaz.
- **Testler dış servise bağımlı değil.** Sahte embedding / sahte agent grafiği,
  test başına izole SQLite ve Chroma koleksiyonu; CI Ollama'sız yeşil. Bu
  izolasyon, Chroma'nın süreç içinde paylaşılan bellek içi client'ından kaynaklanan
  gizli bir test sızıntısını da ortaya çıkardı ve giderdi.
- **Dürüst sınırlar.** 3B'lik local model yakın kategorileri (ağ/erişim) ara sıra
  karıştırabiliyor; RAG bu durumda bile doğru geçmiş ticket'ı buluyor. Canlı
  demodaki 27B model belirgin şekilde daha tutarlı. Bu tam da manuel düzeltme
  verisinin toplanma nedeni.

## API

| Yöntem | Yol | Açıklama |
| --- | --- | --- |
| `POST` | `/ticket` | Ticket'ı triage eder; kategori, öncelik, güven, benzer ticket'lar, çözüm, ekip, `ticket_id` döner |
| `GET` | `/tickets/history` | Ticket geçmişi (en yeni üstte) |
| `PATCH` | `/tickets/history/{id}` | Manuel kategori düzeltmesi (`{"corrected_category": "ağ"}`) |
| `GET` | `/tickets/alerts` | Son 7 günde eşiği aşan kategoriler |
| `GET` | `/health` | Canlılık + kullanılan sağlayıcı/model (sır içermez) |
| `GET` | `/docs` | OpenAPI arayüzü |

Örnek yanıt (kategori/öncelik/güven/çözüm değerleri Groq `qwen/qwen3.8-27b` ile
gerçek çalıştırmadan; `ticket_id` ve `score` temsilî):

```bash
curl -X POST https://it-ticket-triage-agent.onrender.com/ticket \
  -H "Content-Type: application/json" \
  -d '{"text": "Laptopum açılmıyor, güç ışığı hiç yanmıyor"}'
```

```json
{
  "ticket_id": 19,
  "category": "donanım",
  "priority": "orta",
  "confidence": 91,
  "similar_tickets": [
    {
      "ticket_id": 4,
      "title": "Laptop açılmıyor, güç ışığı yanmıyor",
      "category": "donanım",
      "priority": "yüksek",
      "solution": "Adaptör arızalıydı, yenisiyle değiştirildi.",
      "team": "Donanım Destek Ekibi",
      "score": 0.099
    }
  ],
  "solution": "Adaptör arızalı olabilir, lütfen yenisiyle değiştirin.",
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

Groq ile denemek için `.env` dosyasına `GROQ_API_KEY=...` yazıp
`LLM_PROVIDER=groq` (ve istersen `EMBEDDING_PROVIDER=fastembed`) ver.
`python -m scripts.init_db` ve `python -m scripts.index_tickets` ile açılış
işlemleri elle de yapılabilir; `.env.example` tüm ayarları açıklar.

## Test

```bash
pytest -q
```

Testler Ollama'ya, Groq'a ya da internete bağımlı değildir: `search_similar_tickets`
için deterministik sahte embedding, `/ticket` için sahte agent grafiği, agent
grafiği için mesaj şekline göre tool çağrısı üreten sahte LLM; her test kendi
geçici SQLite dosyasını ve Chroma koleksiyonunu kullanır. CI aynı suite'i
`.github/workflows/ci.yml` ile çalıştırır.

## Canlı demo & deploy (Render, ücretsiz)

Canlı demo, local'deki Ollama yerine iki ücretsiz bileşenle çalışır (kod aynı,
sadece ortam değişkenleri farklı — bkz. `app/providers.py`):

| Bileşen    | Local (varsayılan)             | Canlı demo (Dockerfile varsayılanı)                  |
| ---------- | ------------------------------ | ---------------------------------------------------- |
| LLM        | Ollama `llama3.2`              | Groq API, `qwen/qwen3.8-27b` (ücretsiz katman)        |
| Embedding  | Ollama `nomic-embed-text`      | Gemini API `gemini-embedding-001` (768d, ücretsiz katman); seed embedding'leri repoda önbellekli |
| Veri       | `./data` (kalıcı)              | Container diski (yeniden başlatınca sıfırlanır; açılışta otomatik seed + index) |

Üçüncü seçenek `EMBEDDING_PROVIDER=fastembed` (sunucu içi ONNX modeli) local'de
çalışır ama ~350 MB RAM ister; 512 MB'lık ücretsiz Render sunucusunda OOM verdiği
ölçüldü, o yüzden canlı demoda Gemini kullanılır.

Adımlar (kart gerekmez):

1. [console.groq.com](https://console.groq.com) → ücretsiz **Groq API key**.
2. [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → ücretsiz
   **Gemini API key** (embedding için).
3. [render.com](https://render.com) → GitHub ile giriş → **New → Blueprint** → bu
   repo'yu seç. `render.yaml` servisi ücretsiz planda, Dockerfile ile tanımlar.
4. Blueprint uygulanırken `GROQ_API_KEY` ve `GEMINI_API_KEY` sorulur (gizli
   değişkenler); yapıştır.
5. İlk build ~3-5 dk. URL: `https://<servis-adı>.onrender.com`. `main`'e her
   push otomatik deploy olur. Seed verisi ya da embedding modeli değişirse
   `python -m scripts.cache_seed_embeddings` ile önbelleği yenileyip commit'le.

Local'de aynı imajı denemek için:

```bash
docker build -t triage-agent .
docker run -p 7860:7860 -e GROQ_API_KEY=gsk_... triage-agent
# http://localhost:7860
```

Notlar: Ücretsiz Render servisi 15 dk trafik almayınca uyur, ilk istekte ~1 dk'da
uyanır. `/ticket` IP başına dakikada 10 istekle sınırlıdır; Groq'un ücretsiz
katmanı da dakikada ~1000 çıktı token'ı verir (≈ 5-6 ticket/dk) — aşılırsa
arayüz "kota doldu, biraz sonra deneyin" der. Demo verisi her yeniden
başlatmada sıfırlanır.

## Ortam değişkenleri

| Değişken                 | Varsayılan                                   | Açıklama                                                        |
| ------------------------ | -------------------------------------------- | --------------------------------------------------------------- |
| `LLM_PROVIDER`           | `ollama`                                     | `ollama` \| `groq`                                              |
| `EMBEDDING_PROVIDER`     | `ollama`                                     | `ollama` \| `gemini` \| `fastembed`                             |
| `OLLAMA_BASE_URL`        | `http://localhost:11434`                     | Ollama sunucu adresi                                            |
| `OLLAMA_CHAT_MODEL`      | `llama3.2`                                   | Ollama LLM'i (tool-calling + son cümle)                         |
| `OLLAMA_EMBED_MODEL`     | `nomic-embed-text`                           | Ollama embedding modeli                                         |
| `GROQ_API_KEY`           | —                                            | `LLM_PROVIDER=groq` iken zorunlu (secret, commit edilmez)       |
| `GROQ_MODEL`             | `qwen/qwen3.8-27b`                           | Groq modeli (ücretsiz katmanda erişilebilen, tool-calling'i tutarlı) |
| `GROQ_REASONING_EFFORT`  | `none`                                       | Qwen "düşünme" token'larını kapatır; desteklemeyen modelde boş bırak |
| `GROQ_MAX_TOKENS`        | `256`                                        | İstek başına çıktı token sınırı (ücretsiz kota her istekte bunu rezerve eder) |
| `GEMINI_API_KEY`         | —                                            | `EMBEDDING_PROVIDER=gemini` iken zorunlu (secret)               |
| `GEMINI_EMBED_MODEL`     | `gemini-embedding-001`                       | Gemini embedding modeli                                         |
| `GEMINI_EMBED_DIM`       | `768`                                        | Çıktı boyutu (`outputDimensionality`)                           |
| `FASTEMBED_MODEL`        | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Sunucu içi çok dilli embedding modeli (~350 MB RAM) |
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
    graph.py            LangGraph grafiği: ReAct tool döngüsü, _after_tools, finalize, ayrı son-cümle çağrısı
    tools.py            search_similar_tickets, get_priority, assign_team
    state.py            Graf state şeması
  rag/vector_store.py   ChromaDB (cosine) index/arama, açılışta ensure_index
  rag/embedding_cache/  Seed ticket embedding'leri (model başına JSON; API'siz açılış)
  db/
    database.py         SQLite şema, mock seed, ticket_history, düzeltme, uyarı sorgusu
    seed_data.py        28 kayıtlık mock geçmiş ticket
    demo_history.py     Canlı demo için gerçekçi geçmiş
  static/               Vanilla JS + Chart.js frontend (build aracı yok, Chart.js gömülü)
scripts/                init_db, index_tickets, cache_seed_embeddings
tests/                  51 test: tools, rag, agent grafiği, sağlayıcılar, rate limit, DB, API
Dockerfile              Root'suz, $PORT'a duyarlı imaj (embedding modeli gömülü)
render.yaml             Render Blueprint (ücretsiz web servisi)
.github/workflows/ci.yml  pytest
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
