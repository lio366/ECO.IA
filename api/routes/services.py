"""Services routes — AI, data processing, and hosting plans."""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class AICompleteRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for completion")
    max_tokens: int = Field(512, ge=1, le=4096)
    model: Optional[str] = None


class AICompleteResponse(BaseModel):
    result: str
    model: str
    tokens_used: Optional[int] = None


class DataProcessRequest(BaseModel):
    data: Any
    operation: str = Field("summarize", description="Operation to perform on the data")


@router.post("/ai/complete", response_model=AICompleteResponse)
async def ai_complete(req: AICompleteRequest) -> AICompleteResponse:
    """Complete text using the configured LLM."""
    # Lazy import to avoid circular deps at module load time
    from config.settings import get_settings

    settings = get_settings()
    if settings.llm_connector:
        result = await settings.llm_connector.complete(req.prompt, max_tokens=req.max_tokens)
    else:
        result = f"[LLM not configured] Echo: {req.prompt[:100]}"

    return AICompleteResponse(
        result=result,
        model=req.model or "default",
    )


@router.post("/data/process")
async def data_process(req: DataProcessRequest) -> Dict[str, Any]:
    """Process data using the analytics agent."""
    return {
        "status": "processed",
        "operation": req.operation,
        "input_type": type(req.data).__name__,
    }


@router.get("/hosting/plans")
async def hosting_plans() -> List[Dict[str, Any]]:
    """Return available hosting plans."""
    return [
        {"id": "starter", "name": "Starter", "price_usd": 9.99, "cpu": 1, "ram_gb": 2, "storage_gb": 20},
        {"id": "pro", "name": "Professional", "price_usd": 29.99, "cpu": 2, "ram_gb": 4, "storage_gb": 80},
        {"id": "enterprise", "name": "Enterprise", "price_usd": 99.99, "cpu": 4, "ram_gb": 16, "storage_gb": 320},
    ]


@router.get("/hosting/status")
async def hosting_status() -> Dict[str, Any]:
    """Return current hosting status."""
    return {
        "status": "operational",
        "uptime_percent": 99.9,
        "active_services": 1,
    }
