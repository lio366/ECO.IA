"""Analytics agent — aggregates KPIs and detects anomalies."""

from __future__ import annotations

import time
from typing import Any

from core.base_agent import AgentBase
from core.communication import Message, MessageBus


class AnalyticsAgent(AgentBase):
    """Collects metrics, detects anomalies, and generates reports."""

    def __init__(
        self,
        message_bus: MessageBus | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("analytics", config=config)
        self.message_bus = message_bus or MessageBus()
        if self.message_bus:
            self.message_bus.subscribe("analytics", self.on_message)

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        action = task.get("action", "report")
        if action == "report":
            return {"status": "ok", "agent": self.name, "report": self._build_report()}
        return {"status": "ok", "agent": self.name, "task": task}

    async def health_check(self) -> bool:
        return self.is_running

    def _build_report(self) -> dict[str, Any]:
        return {
            "agent": self.name,
            "timestamp": time.time(),
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
        }

    async def on_message(self, message: Message) -> None:
        if message.type == "health.ping":
            pong = Message(
                source=self.name,
                target="orchestrator",
                type="health.pong",
                payload={"timestamp": time.time()},
            )
            await self.message_bus.publish(pong)
