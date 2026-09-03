"""IP başına basit kayan-pencere rate limit'i.

Herkese açık demoda /ticket her çağrıda harici LLM kotası harcar; tek bir
ziyaretçinin (ya da botun) kotayı tüketmesini engellemek için dakikalık
sınır. Bellek içi ve tek süreçlidir - bu proje için yeterli, çok kopyalı bir
deployment'ta paylaşımlı bir store (Redis vb.) gerekir.

Proxy arkasında (Hugging Face Spaces) gerçek istemci IP'si için uvicorn
`--proxy-headers --forwarded-allow-ips='*'` ile çalıştırılmalıdır; aksi halde
tüm ziyaretçiler proxy'nin IP'sini paylaşır (bkz. Dockerfile).
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app import config


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, now: float | None = None) -> None:
        """Sınır aşıldıysa 429 fırlatır, aksi halde isteği kaydeder."""
        if self.limit <= 0:
            return

        now = time.monotonic() if now is None else now
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window:
            hits.popleft()

        if len(hits) >= self.limit:
            retry_after = int(self.window - (now - hits[0])) + 1
            raise HTTPException(
                status_code=429,
                detail=f"Çok fazla istek gönderildi. {retry_after} saniye sonra tekrar deneyin.",
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)


limiter = SlidingWindowLimiter(config.RATE_LIMIT_PER_MINUTE)


def rate_limit(request: Request) -> None:
    """FastAPI dependency: `Depends(rate_limit)` eklenen endpoint'i sınırlar."""
    client_ip = request.client.host if request.client else "unknown"
    limiter.check(client_ip)
