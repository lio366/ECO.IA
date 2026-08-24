"""Admin router — system management and health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def system_health(request: Request) -> dict:
    """Return a health summary of all registered agents."""
    agent_manager = request.app.state.agent_manager
    orchestrator = agent_manager.agents.get("orchestrator")
    if orchestrator and hasattr(orchestrator, "get_health_report"):
        return orchestrator.get_health_report()
    return {"status": "ok", "agents": len(agent_manager.agents)}


@router.get("/agents")
async def list_agents(request: Request) -> dict:
    """Return the status of every registered agent."""
    agent_manager = request.app.state.agent_manager
    return {
        "agents": {
            name: agent.get_status()
            for name, agent in agent_manager.agents.items()
        }
    }
