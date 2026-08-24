"""🛡️ Security Agent — dynamic firewall, intrusion detection, audits."""
import logging
from typing import Any, Dict

from core.agent_base import AgentBase

logger = logging.getLogger(__name__)


class SecurityAgent(AgentBase):
    """Manages dynamic firewall rules and intrusion detection."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="security",
            description="Dynamic firewall, intrusion detection, security audits",
            **kwargs,
        )

    async def on_start(self) -> None:
        self._logger.info("SecurityAgent started.")

    async def on_stop(self) -> None:
        self._logger.info("SecurityAgent stopped.")

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type", "unknown")
        self._logger.info("SecurityAgent executing task: %s", task_type)
        self.tasks_completed += 1
        return {"status": "ok", "agent": self.name, "task": task_type}
