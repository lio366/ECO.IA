"""Simple in-memory rate limiter (100 req/min per IP)."""
import logging
import time
from collections import defaultdict
from typing import DefaultDict, Deque
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

_WINDOW = 60  # seconds
_MAX_REQUESTS = 100


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app, **kwargs)
        self._requests: DefaultDict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = self._requests[ip]

        # Remove timestamps outside the window
        while window and window[0] < now - _WINDOW:
            window.popleft()

        if len(window) >= _MAX_REQUESTS:
            logger.warning("Rate limit exceeded for IP %s", ip)
            return JSONResponse(
                {"detail": "Rate limit exceeded. Try again in a minute."},
                status_code=429,
            )

        window.append(now)
        return await call_next(request)
