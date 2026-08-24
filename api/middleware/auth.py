"""API-Key authentication middleware."""

from __future__ import annotations

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_OPEN_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json", "/dashboard"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Reject requests that lack a valid X-API-Key header (when API_KEY is set)."""

    async def dispatch(self, request: Request, call_next: object) -> Response:
        path = request.url.path
        if path in _OPEN_PATHS or path.startswith("/static"):
            return await call_next(request)  # type: ignore[arg-type]

        expected = os.getenv("API_KEY")
        if expected:
            provided = request.headers.get("X-API-Key") or request.query_params.get("api_key")
            if provided != expected:
                return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)

        return await call_next(request)  # type: ignore[arg-type]
