# Render (ucretsiz web servisi) ve genel Docker ortamlari icin imaj. Local'de:
#   docker build -t triage-agent .
#   docker run -p 7860:7860 -e GROQ_API_KEY=... triage-agent
FROM python:3.12-slim

# Root olmayan kullanici; dosya izin sorunlarini onlemek icin COPY/indirme
# adimlarindan ONCE olusturulup ona gecilir.
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

# Canli demo varsayilanlari. Hosting panelinden (Render: Environment) ezilebilir;
# GROQ_API_KEY imaja GOMULMEZ, panelde gizli degisken olarak tanimlanir.
# Embedding Gemini API'den gelir (RAM harcamaz): 512 MB'lik ucretsiz sunucuda
# sunucu ici bir modelin OOM verdigi olculmustu.
ENV LLM_PROVIDER=groq \
    EMBEDDING_PROVIDER=gemini \
    SQLITE_DB_PATH=/home/user/app/data/tickets.db \
    CHROMA_PERSIST_DIR=/home/user/app/data/chroma \
    AUTO_INDEX=true \
    DEMO_SEED_HISTORY=true \
    RATE_LIMIT_PER_MINUTE=10

COPY --chown=user app ./app
COPY --chown=user scripts ./scripts
COPY --chown=user pyproject.toml README.md ./
RUN mkdir -p data

EXPOSE 7860

# Render portu PORT ortam degiskeniyle bildirir (varsayilan 10000); yoksa 7860.
# --proxy-headers: reverse proxy arkasinda gercek istemci IP'si (rate limit
# icin) X-Forwarded-For'dan okunur.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} \
    --proxy-headers --forwarded-allow-ips='*'
