"""API key authentication middleware."""
import hmac
import logging
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Paths that do not require authentication
_PUBLIC_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json", "/dashboard"}
_ADMIN_PREFIX = "/api/v1/admin"


def _constant_compare(a: str, b: str) -> bool:
    """Timing-safe string comparison."""
    return hmac.compare_digest(a.encode(), b.encode())


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        path = request.url.path

        # Static files and public endpoints are always allowed
        if path in _PUBLIC_PATHS or path.startswith("/static"):
            return await call_next(request)

        api_key = os.getenv("ECO_IA_API_KEY", "")
        admin_key = os.getenv("ECO_IA_ADMIN_KEY", "")

        # Admin endpoints require the admin key
        if path.startswith(_ADMIN_PREFIX):
            provided = request.headers.get("X-Admin-Key", "")
            if not admin_key or not _constant_compare(provided, admin_key):
                return JSONResponse({"detail": "Invalid or missing admin key"}, status_code=403)
            return await call_next(request)

        # All other /api/ paths require the API key
        if path.startswith("/api/"):
            provided = request.headers.get("X-API-Key", "")
            if not api_key or not _constant_compare(provided, api_key):
                return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)

        return await call_next(request)
