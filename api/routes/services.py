"""Services router — manage and invoke ECO-IA agent services."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/")
async def list_services(request: Request) -> dict:
    """Return the list of running agents and their status."""
    agent_manager = request.app.state.agent_manager
    agents = {
        name: agent.get_status()
        for name, agent in agent_manager.agents.items()
    }
    return {"status": "ok", "agents": agents}


@router.post("/{agent_name}/execute")
async def execute_service(agent_name: str, task: dict, request: Request) -> JSONResponse:
    """Execute a task on the named agent."""
    agent_manager = request.app.state.agent_manager
    agent = agent_manager.agents.get(agent_name)
    if agent is None:
        return JSONResponse({"detail": f"Agent '{agent_name}' not found"}, status_code=404)
    result = await agent.execute(task)
    return JSONResponse(result)
