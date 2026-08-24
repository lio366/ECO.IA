"""Monetization agent — manages the service catalogue and billing."""

from __future__ import annotations

import time
from typing import Any

from core.base_agent import AgentBase
from core.communication import Message, MessageBus


class MonetizationAgent(AgentBase):
    """Manages catalogue, dynamic pricing, and Stripe billing coordination."""

    def __init__(
        self,
        message_bus: MessageBus | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("monetization", config=config)
        self.message_bus = message_bus or MessageBus()
        if self.message_bus:
            self.message_bus.subscribe("monetization", self.on_message)

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        action = task.get("action", "catalogue")
        if action == "catalogue":
            return {"status": "ok", "agent": self.name, "services": []}
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
