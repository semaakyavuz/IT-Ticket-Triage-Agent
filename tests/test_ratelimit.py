import pytest
from fastapi import HTTPException

from app.ratelimit import SlidingWindowLimiter


def test_allows_requests_up_to_limit():
    limiter = SlidingWindowLimiter(limit=3, window_seconds=60)

    for i in range(3):
        limiter.check("1.2.3.4", now=100 + i)


def test_blocks_request_over_limit_with_retry_after():
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60)
    limiter.check("ip", now=100)
    limiter.check("ip", now=110)

    with pytest.raises(HTTPException) as exc:
        limiter.check("ip", now=120)

    assert exc.value.status_code == 429
    # Pencere ilk istekten (t=100) 60 sn sonra açılır: 100+60-120 = 40 (+1)
    assert exc.value.headers["Retry-After"] == "41"


def test_window_slides_and_old_hits_expire():
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60)
    limiter.check("ip", now=100)
    limiter.check("ip", now=110)

    # 100'deki istek penceresi 160'ta dolar; yeni isteğe yer açılır.
    limiter.check("ip", now=161)


def test_limits_are_per_client():
    limiter = SlidingWindowLimiter(limit=1, window_seconds=60)
    limiter.check("a", now=100)
    limiter.check("b", now=100)  # farklı istemci etkilenmez

    with pytest.raises(HTTPException):
        limiter.check("a", now=101)


def test_zero_limit_disables_rate_limiting():
    limiter = SlidingWindowLimiter(limit=0)
    for i in range(50):
        limiter.check("ip", now=i)
