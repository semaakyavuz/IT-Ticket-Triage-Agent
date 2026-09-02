# IT Ticket Triage Agent

IT destek taleplerini otomatik olarak kategorize eden, önceliklendiren ve geçmiş
ticket'lardan (RAG) yola çıkarak çözüm öneren ya da doğru ekibe yönlendiren bir
agent. Tamamen local çalışır — LLM ve embedding modelleri Ollama üzerinden
sağlanır, harici bir API key gerekmez.

## Stack

- **API**: Python + FastAPI
- **Agent orkestrasyonu**: LangChain + LangGraph (tool calling)
- **Vector search / RAG**: ChromaDB
- **LLM**: Ollama (`llama3.2`) + Ollama embedding modeli (`nomic-embed-text`)
- **Veri**: SQLite (mock ticket verisi, 28 kayıt)

## Mimari

```
Kullanıcı ──POST /ticket──▶ FastAPI ──▶ LangGraph agent
                                          │
                     ┌────────────────────┼────────────────────┐
                     ▼                    ▼                    ▼
              get_priority          assign_team        search_similar_tickets
              (kural tabanlı)       (kategori → ekip)   (ChromaDB + Ollama
                                                          embeddings ile RAG)
                     │                    │                    │
                     └────────────────────┴────────────────────┘
                                          ▼
                                  JSON yanıt (kategori,
                                  öncelik, benzer ticket'lar,
                                  çözüm/yönlendirme)
```

Akış:

1. `/ticket` endpoint'ine kullanıcı bir IT sorunu yazar (örn. "VPN bağlanmıyor").
2. LangGraph agent'ı (Ollama üzerinden çalışan `llama3.2`), sorunu **donanım /
   yazılım / ağ / erişim** kategorilerinden birine atar.
3. Agent, kendi kararıyla sırayla şu tool'ları çağırır:
   - `get_priority(category, keywords)` — anahtar kelime + kategoriye göre
     kural tabanlı öncelik (**düşük / orta / yüksek**) döndürür.
   - `search_similar_tickets(query)` — ChromaDB'de, Ollama'nın
     `nomic-embed-text` modeliyle embed edilmiş 28 geçmiş ticket arasında
     semantik olarak en benzerlerini bulur (RAG).
   - `assign_team(category)` — yeterince benzer ticket bulunamazsa, kategoriye
     göre ilgili destek ekibine yönlendirir.
4. Sonuç; kategori, öncelik, bulunan benzer ticket'lar, önerilen çözüm ve/veya
   yönlendirilen ekibi içeren bir JSON olarak döner.

Yapısal alanlar (`category`, `priority`, `assigned_team`, `similar_tickets`)
LLM'in serbest metin çıktısını ayrıştırmak yerine, agent'ın gerçekte hangi
tool'ları hangi argümanlarla çağırdığından deterministik olarak çıkarılır
(`app/agent/graph.py` içindeki `_finalize_node`). Bu sayede küçük, local bir
modelin (`llama3.2`) her seferinde birebir aynı formatta JSON üretmesine bağımlı
kalınmaz; LLM sadece kategoriyi belirlemek, doğru tool'ları doğru argümanlarla
çağırmak ve kısa bir çözüm/yönlendirme cümlesi yazmaktan sorumludur.

## Proje yapısı

```
app/
  main.py              FastAPI uygulaması, /ticket endpoint
  config.py            Ortam değişkenleri (Ollama, SQLite, Chroma yolları)
  schemas.py           Pydantic request/response modelleri
  db/
    database.py        SQLite bağlantısı, şema, seed
    seed_data.py        28 kayıtlık mock ticket verisi
  rag/
    vector_store.py     ChromaDB + Ollama embeddings (RAG)
  agent/
    tools.py            search_similar_tickets, get_priority, assign_team
    state.py             LangGraph state şeması
    graph.py             LangGraph grafiği (agent ↔ tools döngüsü)
  static/               Vanilla JS + Chart.js frontend (build aracı yok)
    index.html           Triage ve Dashboard sekmeleri
    css/styles.css        Koyu tema, özgün stil
    js/app.js              Form, adım animasyonu, grafikler
    vendor/chart.min.js    Chart.js (CDN'siz, local'e gömülü)
scripts/
  init_db.py            SQLite'ı oluşturur ve mock veriyle doldurur
  index_tickets.py      Mock ticket'ları Chroma'ya embed'ler
tests/
  test_tools.py          get_priority / assign_team birim testleri
  test_rag.py             Sahte embedding ile Chroma indeksleme/arama testi
  test_api.py             Sahte agent grafiğiyle /ticket endpoint testi
.github/workflows/ci.yml  push/PR'da pytest çalıştıran GitHub Actions
```

## Kurulum

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

[Ollama](https://ollama.com) kurulu olmalı ve şu modeller indirilmiş olmalı:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

Gerekirse `.env.example` dosyasını `.env` olarak kopyalayıp Ollama adresi/model
adlarını özelleştirebilirsin.

## Çalıştırma

```bash
# 1) SQLite'ı mock ticket verisiyle doldur
python -m scripts.init_db

# 2) Mock ticket'ları ChromaDB'ye embed'le (Ollama çalışıyor olmalı)
python -m scripts.index_tickets

# 3) API'yi başlat
uvicorn app.main:app --reload
```

Sonra tarayıcıda **http://localhost:8000** adresini aç — build aracı gerektirmeyen
vanilla JS + Chart.js bir arayüz açılır:

- **Triage** sekmesi: ticket metnini yazıp gönder; kategori/öncelik renkli
  badge'lerin yanında bir güven yüzdesi (`confidence`), agent'ın adımları
  (kategori → öncelik → RAG araması → ekip ataması) küçük bir zaman çizelgesi
  animasyonuyla, bulunan benzer ticket'lar benzerlik yüzdesiyle kart listesi
  halinde gösterilir. Sonucun altında, backend'deki `ticket_history` tablosundan
  gelen (en yeni üstte) bir **ticket geçmişi tablosu** listelenir.
- **Dashboard** sekmesi: `GET /tickets/history`'den gelen gerçek veriye göre
  kategori dağılımı (pasta grafik) ve öncelik dağılımı (bar grafik) — Chart.js
  ile. Veri artık `localStorage` değil, backend'deki SQLite tablosu; yani tüm
  kullanıcılar/oturumlar arasında paylaşılır.

### Örnek istek

```bash
curl -X POST http://localhost:8000/ticket \
  -H "Content-Type: application/json" \
  -d '{"text": "VPN bağlantısı sürekli kopuyor, uzaktan çalışamıyorum"}'
```

> Windows + Git Bash kullanıyorsan `-d '...'` içindeki Türkçe karakterler shell
> tarafından bozulabilir ("There was an error parsing the body" hatası). Bu
> durumda isteği bir `.json` dosyasına UTF-8 olarak yazıp
> `--data-binary @dosya.json` ile göndermek sorunu çözer.

Aşağıdaki yanıt, **gerçek Ollama** (`llama3.2` + `nomic-embed-text`, Ollama
0.33.2) çalışırken bu isteğe verilen gerçek çıktıdır (uydurma/örnek değildir):

```json
{
  "category": "erişim",
  "priority": "düşük",
  "similar_tickets": [
    {
      "ticket_id": 1,
      "title": "VPN bağlantısı kurulamıyor",
      "category": "ağ",
      "priority": "yüksek",
      "solution": "VPN istemcisi güncellendi ve kullanıcı profili yeniden oluşturuldu, sorun çözüldü.",
      "team": "Network Operasyon Ekibi",
      "score": 0.162
    },
    {
      "ticket_id": 2,
      "title": "Wi-Fi sürekli kopuyor",
      "category": "ağ",
      "priority": "orta",
      "solution": "Kat için ayrı access point tanımlandı, kanal çakışması giderildi.",
      "team": "Network Operasyon Ekibi",
      "score": 0.455
    },
    {
      "ticket_id": 18,
      "title": "Uzaktan masaüstü bağlantısı kopuyor",
      "category": "ağ",
      "priority": "orta",
      "solution": "VPN MTU ayarı düşürülerek paket parçalanması giderildi.",
      "team": "Network Operasyon Ekibi",
      "score": 0.463
    }
  ],
  "solution": "VPN bağlantısı sürekli kopuyor, uzaktan çalışamıyorum. Bu sorun için Erişim ve Kimlik Yönetimi Ekibi ile temas edin.",
  "assigned_team": "Erişim ve Kimlik Yönetimi Ekibi"
}
```

RAG kısmı (`similar_tickets`) mükemmel çalıştı: en düşük (en benzer) skor,
neredeyse birebir aynı geçmiş ticket'a (id 1) ait. Ancak `llama3.2` bu istekte
kategoriyi "ağ" yerine "erişim" olarak etiketledi — 3B parametrelik küçük bir
local modelin ara sıra yakın kategoriler arasında (ağ/erişim gibi) hata
yapması beklenen bir durumdur, kodda bir hata değildir. Aynı uçtan uca akış
donanım kategorisindeki bir örnekte ("Laptopum açılmıyor, güç ışığı hiç
yanmıyor") kategoriyi, önceliği ve ekibi birebir doğru üretti (en benzer
ticket skoru: 0.13).

## Test

```bash
pytest -q
```

Testler Ollama'ya bağımlı değildir: `search_similar_tickets` testlerinde
gerçek `OllamaEmbeddings` yerine deterministik sahte bir embedding fonksiyonu,
`/ticket` endpoint testlerinde ise gerçek LLM çağrısı yerine sahte bir agent
grafiği kullanılır. `get_priority`/`assign_team` zaten kural tabanlı olduğu
için doğrudan test edilir. Bu yüzden CI, Ollama kurulu olmadan da (bkz.
`.github/workflows/ci.yml`) çalışır.

## Ortam değişkenleri

| Değişken             | Varsayılan                | Açıklama                                |
| -------------------- | -------------------------- | ---------------------------------------- |
| `OLLAMA_BASE_URL`     | `http://localhost:11434`   | Ollama sunucu adresi                     |
| `OLLAMA_CHAT_MODEL`   | `llama3.2`                 | Kategorizasyon/tool-calling için LLM     |
| `OLLAMA_EMBED_MODEL`  | `nomic-embed-text`         | RAG embedding modeli                     |
| `SQLITE_DB_PATH`      | `./data/tickets.db`        | Mock ticket verisinin tutulduğu SQLite   |
| `CHROMA_PERSIST_DIR`  | `./data/chroma`            | Chroma'nın kalıcı vector index dizini    |
