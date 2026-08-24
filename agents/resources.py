"""Resources agent — monitors CPU / RAM / Disk / Network usage."""

from __future__ import annotations

import time
from typing import Any

from core.base_agent import AgentBase
from core.communication import Message, MessageBus


class ResourcesAgent(AgentBase):
    """Monitors system resources and suggests or performs optimisations."""

    def __init__(
        self,
        message_bus: MessageBus | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("resources", config=config)
        self.message_bus = message_bus or MessageBus()
        if self.message_bus:
            self.message_bus.subscribe("resources", self.on_message)

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        action = task.get("action", "metrics")
        if action == "metrics":
            return {"status": "ok", "agent": self.name, "metrics": self._collect_metrics()}
        return {"status": "ok", "agent": self.name, "task": task}

    async def health_check(self) -> bool:
        return self.is_running

    def _collect_metrics(self) -> dict[str, Any]:
        try:
            import psutil  # type: ignore[import]

            return {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
            }
        except Exception:  # noqa: BLE001
            return {}

    async def on_message(self, message: Message) -> None:
        if message.type == "health.ping":
            pong = Message(
                source=self.name,
                target="orchestrator",
                type="health.pong",
                payload={"timestamp": time.time()},
            )
            await self.message_bus.publish(pong)
