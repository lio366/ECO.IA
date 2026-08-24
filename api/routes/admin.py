"""Admin routes — health, metrics, agents, scheduler."""
import logging
import os
import platform
from typing import Any, Dict, List

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def admin_health() -> Dict[str, Any]:
    """Detailed health status of all agents."""
    from config.settings import get_settings

    settings = get_settings()
    report: Dict[str, Any] = {"status": "healthy", "agents": {}}

    if settings.orchestrator:
        report = settings.orchestrator._get_health_report()
        report["status"] = "healthy"

    return report


@router.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """Real-time server metrics."""
    try:
        import psutil  # type: ignore

        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "cpu_percent": cpu,
            "memory": {
                "total_gb": round(mem.total / 1e9, 2),
                "used_gb": round(mem.used / 1e9, 2),
                "percent": mem.percent,
            },
            "disk": {
                "total_gb": round(disk.total / 1e9, 2),
                "used_gb": round(disk.used / 1e9, 2),
                "percent": disk.percent,
            },
            "platform": platform.system(),
            "python": platform.python_version(),
        }
    except ImportError:
        return {"error": "psutil not installed", "platform": platform.system()}


@router.get("/agents")
async def list_agents() -> Dict[str, Any]:
    """List all registered agents."""
    from config.settings import get_settings

    settings = get_settings()
    if settings.orchestrator:
        result = await settings.orchestrator.execute({"type": "list_agents"})
        return result
    return {"agents": []}


@router.get("/scheduler/tasks")
async def scheduler_tasks() -> Dict[str, Any]:
    """List all scheduled tasks."""
    from config.settings import get_settings

    settings = get_settings()
    if settings.orchestrator:
        return {"tasks": settings.orchestrator.scheduler.list_tasks()}
    return {"tasks": []}
