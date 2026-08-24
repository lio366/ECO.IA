"""OrchestratorAgent — coordinates all ECO-IA specialist agents."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from core.base_agent import AgentBase
from core.communication import Message, MessageBus
from core.task_scheduler import TaskScheduler

logger = logging.getLogger(__name__)

# How long (seconds) to wait for a health pong before declaring an agent unhealthy.
HEALTH_CHECK_TIMEOUT: float = 5.0


class OrchestratorAgent(AgentBase):
    """Master agent that monitors and coordinates specialist agents.

    Health-check flow
    -----------------
    1. :meth:`_check_agents_health` broadcasts a ``health.ping`` to ``"*"``.
    2. Each specialist agent is expected to reply with a ``health.pong`` message
       addressed to ``"orchestrator"``.
    3. After ``HEALTH_CHECK_TIMEOUT`` seconds the orchestrator marks any agent
       that did not reply as *unhealthy* and increments its consecutive-failure
       counter.
    """

    def __init__(
        self,
        message_bus: MessageBus | None = None,
        scheduler: TaskScheduler | None = None,
        health_check_timeout: float = HEALTH_CHECK_TIMEOUT,
        llm: Any = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("orchestrator", config=config)
        self.message_bus = message_bus or MessageBus()
        self.scheduler = scheduler or TaskScheduler()
        self.health_check_timeout = health_check_timeout
        self.llm = llm

        # Registry of known specialist agents: name -> status dict
        self._agent_registry: dict[str, dict[str, Any]] = {}
        # Tracks agents that have replied to the current ping round
        self._pending_pong: set[str] = set()
        # Consecutive missed-pong counter per agent
        self._missed_pongs: dict[str, int] = {}

        # Subscribe orchestrator to its own address for pong replies
        self.message_bus.subscribe("orchestrator", self._on_message)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        await super().start()
        self.scheduler.register(
            "health_check",
            self._check_agents_health,
            interval=30.0,
        )
        await self.scheduler.start()

    async def stop(self) -> None:
        await self.scheduler.stop()
        await super().stop()

    # ------------------------------------------------------------------
    # Agent registry
    # ------------------------------------------------------------------

    def register_agent(self, name: str) -> None:
        """Add *name* to the set of monitored agents."""
        self._agent_registry[name] = {"status": "unknown", "last_seen": None}
        self._missed_pongs[name] = 0

    def get_agent_status(self, name: str) -> dict[str, Any] | None:
        return self._agent_registry.get(name)

    # ------------------------------------------------------------------
    # AgentBase interface
    # ------------------------------------------------------------------

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok", "agent": self.name, "task": task}

    async def health_check(self) -> bool:
        return self.is_running

    def get_config(self, key: str, default: Any = None) -> Any:  # noqa: ANN401
        """Return a value from the agent config with an optional default."""
        return self.config.get(key, default)

    # ------------------------------------------------------------------
    # Health-check logic
    # ------------------------------------------------------------------

    async def _check_agents_health(self) -> None:
        """Broadcast a health ping and wait for pongs with a timeout.

        After ``self.health_check_timeout`` seconds, agents that have not
        replied are marked as *unhealthy* and their missed-pong counter is
        incremented.
        """
        # Reset pong tracking for this round
        self._pending_pong = set(self._agent_registry.keys())

        health_request = Message(
            source="orchestrator",
            target="*",
            type="health.ping",
            payload={"timestamp": time.time()},
        )
        await self.message_bus.publish(health_request)

        # Wait up to timeout for all agents to respond
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.health_check_timeout
        while self._pending_pong and loop.time() < deadline:
            await asyncio.sleep(0.05)

        # Any agent still pending did not reply in time
        for agent_name in list(self._pending_pong):
            self._missed_pongs[agent_name] = self._missed_pongs.get(agent_name, 0) + 1
            self._agent_registry[agent_name]["status"] = "unhealthy"
            logger.warning("Agent %s did not respond to health ping", agent_name)

    async def _on_message(self, message: Message) -> None:
        """Handle incoming messages (primarily health pongs)."""
        if message.type == "health.pong":
            source = message.source
            if source in self._agent_registry:
                self._agent_registry[source]["status"] = "active"
                self._agent_registry[source]["last_seen"] = time.time()
                self._missed_pongs[source] = 0
                self._pending_pong.discard(source)

    def get_health_report(self) -> dict[str, Any]:
        return {
            "orchestrator": "running" if self.is_running else "stopped",
            "agents": dict(self._agent_registry),
            "missed_pongs": dict(self._missed_pongs),
        }

    async def _generate_executive_report(self) -> None:
        """Log a periodic executive summary of all registered agents."""
        healthy = sum(1 for s in self._agent_registry.values() if s.get("status") == "active")
        total = len(self._agent_registry)
        logger.info(
            "Executive report: %d/%d agents healthy | missed_pongs=%s",
            healthy,
            total,
            dict(self._missed_pongs),
        )
