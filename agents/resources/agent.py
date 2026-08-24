"""🌿 Resources Agent — CPU/RAM optimisation and auto-scaling."""
import logging
from typing import Any, Dict

from core.agent_base import AgentBase

logger = logging.getLogger(__name__)


class ResourcesAgent(AgentBase):
    """Optimises CPU/RAM usage and handles auto-scaling."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="resources",
            description="Resource optimisation and auto-scaling",
            **kwargs,
        )

    async def on_start(self) -> None:
        self._logger.info("ResourcesAgent started.")

    async def on_stop(self) -> None:
        self._logger.info("ResourcesAgent stopped.")

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type", "unknown")
        self._logger.info("ResourcesAgent executing task: %s", task_type)
        self.tasks_completed += 1
        return {"status": "ok", "agent": self.name, "task": task_type}
