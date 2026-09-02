# IT Ticket Triage Agent

IT destek taleplerini otomatik olarak kategorize eden, önceliklendiren ve geçmiş
ticket'lardan (RAG) yola çıkarak çözüm öneren ya da doğru ekibe yönlendiren bir
agent. Tamamen local çalışır — LLM ve embedding modelleri Ollama üzerinden
sağlanır, harici bir API key gerekmez.

> Durum: Geliştirme aşamasında. İlerleme adım adım commit'lenip GitHub'a
> push'lanıyor — aşağıdaki bölümler proje büyüdükçe genişletilecek.

## Stack

- **API**: Python + FastAPI
- **Agent orkestrasyonu**: LangChain + LangGraph (tool calling)
- **Vector search / RAG**: ChromaDB
- **LLM**: Ollama (`llama3.2`) + Ollama embedding modeli (`nomic-embed-text`)
- **Veri**: SQLite (mock ticket verisi)

## Kurulum (özet)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Ollama modellerini indir (Ollama kurulu olmalı: https://ollama.com)
ollama pull llama3.2
ollama pull nomic-embed-text
```

Detaylı mimari açıklaması ve API kullanım örnekleri, agent ve endpoint
tamamlandıktan sonra bu dosyaya eklenecek.
