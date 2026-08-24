"""ECO-IA FastAPI main application — OVHcloud US b3-8."""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.middleware.auth import APIKeyMiddleware
from api.middleware.rate_limit import RateLimitMiddleware
from api.routes import admin, services, webhooks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("🌱 ECO-IA API starting — OVHcloud US 135.148.232.10")
    yield
    logger.info("ECO-IA API shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ECO-IA API",
        description=(
            "Autonomous AI-Agent server system — self-sustaining, income-generating, sustainable. "
            "OVHcloud US b3-8 | 135.148.232.10"
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(APIKeyMiddleware)

    # ── Static files ─────────────────────────────────────────────────────────
    static_dir = FRONTEND_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(services.router, prefix="/api/v1/services", tags=["Services"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

    # ── Public endpoints ──────────────────────────────────────────────────────
    @app.get("/", tags=["Health"])
    async def root() -> dict:
        return {
            "status": "ok",
            "system": "ECO-IA",
            "version": "1.0.0",
            "server": "135.148.232.10",
            "docs": "/docs",
            "dashboard": "/dashboard",
        }

    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "healthy"}

    @app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
    async def dashboard() -> HTMLResponse:
        """Admin dashboard — ECO-IA control panel."""
        template = FRONTEND_DIR / "templates" / "dashboard.html"
        if template.exists():
            return HTMLResponse(content=template.read_text(), status_code=200)
        return HTMLResponse(content="<h1>ECO-IA Dashboard</h1><p><a href='/docs'>API Docs</a></p>")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",  # noqa: S104
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        workers=int(os.getenv("API_WORKERS", "1")),
    )
