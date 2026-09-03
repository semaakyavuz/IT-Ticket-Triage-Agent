# Hugging Face Spaces (Docker SDK) icin imaj. Local'de de calisir:
#   docker build -t triage-agent .
#   docker run -p 7860:7860 -e GROQ_API_KEY=... triage-agent
FROM python:3.12-slim

# HF Spaces container'i UID 1000 ile calisir; dosya izin sorunlarini onlemek
# icin kullaniciyi COPY/indirme adimlarindan ONCE olusturup ona gec.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR $HOME/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Canli demo varsayilanlari. Space ayarlarindan (Variables/Secrets) ezilebilir;
# GROQ_API_KEY imaja GOMULMEZ, Space'te secret olarak tanimlanir.
ENV LLM_PROVIDER=groq \
    EMBEDDING_PROVIDER=fastembed \
    FASTEMBED_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
    FASTEMBED_CACHE_DIR=/home/user/app/models \
    SQLITE_DB_PATH=/home/user/app/data/tickets.db \
    CHROMA_PERSIST_DIR=/home/user/app/data/chroma \
    AUTO_INDEX=true \
    DEMO_SEED_HISTORY=true \
    RATE_LIMIT_PER_MINUTE=10

# Embedding modelini (~220 MB) build aninda imaja gom: her acilista indirme yok,
# soguk baslangic kisa. Uygulama kodundan once gelir ki kod degisince bu
# katman cache'ten gelsin.
RUN python -c "import os; from fastembed import TextEmbedding; \
TextEmbedding(model_name=os.environ['FASTEMBED_MODEL'], cache_dir=os.environ['FASTEMBED_CACHE_DIR'])"

COPY --chown=user app ./app
COPY --chown=user scripts ./scripts
COPY --chown=user pyproject.toml README.md ./
RUN mkdir -p data

EXPOSE 7860

# --proxy-headers: HF'in reverse proxy'si arkasinda gercek istemci IP'si
# (rate limit icin) X-Forwarded-For'dan okunur.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", \
     "--proxy-headers", "--forwarded-allow-ips=*"]
