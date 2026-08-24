"""Abstract base class for all ECO-IA agents."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any


class AgentBase(ABC):
    """Base class every ECO-IA agent must inherit from.

    Subclasses must implement :meth:`execute` and :meth:`health_check`.
    """

    def __init__(self, name: str, config: dict[str, Any] | None = None) -> None:
        self.name = name
        self.config: dict[str, Any] = config or {}
        self.is_running = False
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.last_heartbeat: float | None = None
        self.logger = logging.getLogger(f"eco_ia.agent.{name}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the agent."""
        self.is_running = True
        self.logger.info("Agent %s started", self.name)

    async def stop(self) -> None:
        """Stop the agent."""
        self.is_running = False
        self.logger.info("Agent %s stopped", self.name)

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a task and return the result."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return *True* when the agent is healthy."""

    # ------------------------------------------------------------------
    # Messaging helpers
    # ------------------------------------------------------------------

    async def on_message(self, message: Any) -> None:  # noqa: ANN401
        """Called when a message arrives for this agent (override as needed)."""

    async def send_message(self, bus: Any, target: str, msg_type: str, payload: dict) -> None:  # noqa: ANN401
        """Publish a message on *bus* addressed to *target*."""
        from core.communication import Message

        await bus.publish(Message(source=self.name, target=target, type=msg_type, payload=payload))

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "is_running": self.is_running,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "last_heartbeat": self.last_heartbeat,
        }
