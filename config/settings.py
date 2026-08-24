"""Application settings — loaded from environment variables."""
import os
from functools import lru_cache
from typing import Any, Optional


class Settings:
    """Holds global application state (agents, connectors)."""

    def __init__(self) -> None:
        self.api_key: str = os.getenv("ECO_IA_API_KEY", "")
        self.admin_key: str = os.getenv("ECO_IA_ADMIN_KEY", "")
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"

        # Runtime objects — populated at startup
        self.orchestrator: Optional[Any] = None
        self.llm_connector: Optional[Any] = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
