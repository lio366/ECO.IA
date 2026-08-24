"""Simple in-memory sliding-window rate limiter."""

from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_DEFAULT_RPM = 60
_WINDOW = 60.0  # seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Allow at most *requests_per_minute* requests per client IP."""

    def __init__(self, app: object, requests_per_minute: int = _DEFAULT_RPM) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._limit = requests_per_minute
        self._log: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: object) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        cutoff = now - _WINDOW

        timestamps = self._log[client_ip]
        # Drop timestamps outside the current window
        self._log[client_ip] = [t for t in timestamps if t > cutoff]

        if len(self._log[client_ip]) >= self._limit:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

        self._log[client_ip].append(now)
        return await call_next(request)  # type: ignore[arg-type]
