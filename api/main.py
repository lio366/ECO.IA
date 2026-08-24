"""ECO-IA FastAPI application."""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from agents.analytics import AnalyticsAgent
from agents.devops import DevOpsAgent
from agents.monetization import MonetizationAgent
from agents.orchestrator import OrchestratorAgent
from agents.resources import ResourcesAgent
from agents.security import SecurityAgent
from core.agent_manager import AgentManager
from core.communication import MessageBus
from core.llm_connector import LLMConnector

from .middleware.auth import APIKeyMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .routes import admin, services, webhooks

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def _build_fallback_manager() -> AgentManager:
    message_bus = MessageBus()
    try:
        llm: LLMConnector | None = LLMConnector(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        )
    except Exception:  # noqa: BLE001
        llm = None
    manager = AgentManager(message_bus=message_bus, llm=llm)
    manager.agents = {
        "orchestrator": OrchestratorAgent(
            message_bus=message_bus,
            llm=llm,
            config=manager.config.get("orchestrator", {}),
        ),
        "monetization": MonetizationAgent(
            message_bus=message_bus,
            config=manager.config.get("monetization", {}),
        ),
        "devops": DevOpsAgent(
            message_bus=message_bus,
            config=manager.config.get("devops", {}),
        ),
        "resources": ResourcesAgent(
            message_bus=message_bus,
            config=manager.config.get("resources", {}),
        ),
        "security": SecurityAgent(
            message_bus=message_bus,
            config=manager.config.get("security", {}),
        ),
        "analytics": AnalyticsAgent(
            message_bus=message_bus,
            config=manager.config.get("analytics", {}),
        ),
    }
    orchestrator = manager.agents["orchestrator"]
    if not orchestrator.scheduler.list_tasks():
        orchestrator.scheduler.register(
            "health_check",
            orchestrator._check_agents_health,  # noqa: SLF001
            interval_seconds=orchestrator.get_config("health_check_interval", 60),
            description="Periodic health check of all registered agents",
        )
        orchestrator.scheduler.register(
            "executive_report",
            orchestrator._generate_executive_report,  # noqa: SLF001
            interval_seconds=orchestrator.get_config("report_interval", 3600),
            description="Hourly executive report",
        )
    manager._register_agents()  # noqa: SLF001
    return manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("🌱 ECO-IA API starting")
    message_bus = MessageBus()
    llm = LLMConnector(
        provider=os.getenv("LLM_PROVIDER", "openai"),
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    )
    agent_manager = AgentManager(message_bus=message_bus, llm=llm)
    await agent_manager.initialize_all()
    app.state.message_bus = message_bus
    app.state.agent_manager = agent_manager
    try:
        yield
    finally:
        await agent_manager.stop_all()
        logger.info("ECO-IA API shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ECO-IA API",
        description="Autonomous AI-Agent server system",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.message_bus = MessageBus()
    app.state.agent_manager = _build_fallback_manager()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(APIKeyMiddleware)

    static_dir = FRONTEND_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(services.router, prefix="/api/v1/services", tags=["Services"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

    @app.get("/", tags=["Health"])
    async def root() -> dict:
        return {
            "status": "ok",
            "system": "ECO-IA",
            "version": "1.0.0",
            "server": os.getenv("SERVER_IP", "135.148.232.10"),
            "docs": "/docs",
            "dashboard": "/dashboard",
        }

    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "healthy"}

    @app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
    async def dashboard() -> HTMLResponse:
        template = FRONTEND_DIR / "templates" / "dashboard.html"
        if template.exists():
            return HTMLResponse(content=template.read_text(encoding="utf-8"), status_code=200)
        return HTMLResponse(content="<h1>ECO-IA Dashboard</h1><p><a>API Docs</a></p>")

    return app


app = create_app()
