"""DevOps agent — supervises deployments, backups, and container health."""

from __future__ import annotations

import time
from typing import Any

from core.base_agent import AgentBase
from core.communication import Message, MessageBus


class DevOpsAgent(AgentBase):
    """Handles deployments, restarts, backups, and container health checks."""

    def __init__(
        self,
        message_bus: MessageBus | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("devops", config=config)
        self.message_bus = message_bus or MessageBus()
        if self.message_bus:
            self.message_bus.subscribe("devops", self.on_message)

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        action = task.get("action", "status")
        if action == "status":
            return {"status": "ok", "agent": self.name, "is_running": self.is_running}
        return {"status": "ok", "agent": self.name, "task": task}

    async def health_check(self) -> bool:
        return self.is_running

    async def on_message(self, message: Message) -> None:
        if message.type == "health.ping":
            pong = Message(
                source=self.name,
                target="orchestrator",
                type="health.pong",
                payload={"timestamp": time.time()},
            )
            await self.message_bus.publish(pong)
