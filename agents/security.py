"""Security agent — audits access events and detects suspicious patterns."""

from __future__ import annotations

import time
from typing import Any

from core.base_agent import AgentBase
from core.communication import Message, MessageBus


class SecurityAgent(AgentBase):
    """Monitors access, verifies firewall policies, and emits security alerts."""

    def __init__(
        self,
        message_bus: MessageBus | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("security", config=config)
        self.message_bus = message_bus or MessageBus()
        self._audit_log: list[dict[str, Any]] = []
        if self.message_bus:
            self.message_bus.subscribe("security", self.on_message)

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        action = task.get("action", "audit")
        if action == "audit":
            return {"status": "ok", "agent": self.name, "events": len(self._audit_log)}
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
        else:
            self._audit_log.append(
                {"type": message.type, "source": message.source, "time": time.time()}
            )
