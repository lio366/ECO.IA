"""AgentManager — lifecycle coordinator for all ECO-IA agents."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from core.communication import MessageBus

if TYPE_CHECKING:
    from core.llm_connector import LLMConnector

logger = logging.getLogger(__name__)


class AgentManager:
    """Creates, registers, starts, and stops all specialist agents.

    Usage
    -----
    manager = AgentManager(message_bus=bus, llm=llm)
    await manager.initialize_all()   # creates + starts all agents
    ...
    await manager.stop_all()
    """

    def __init__(
        self,
        message_bus: MessageBus | None = None,
        llm: LLMConnector | None = None,
    ) -> None:
        self.message_bus: MessageBus = message_bus or MessageBus()
        self.llm = llm
        self.config: dict[str, Any] = {}
        self.agents: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_default_agents(self) -> None:
        from agents.analytics import AnalyticsAgent
        from agents.devops import DevOpsAgent
        from agents.monetization import MonetizationAgent
        from agents.orchestrator import OrchestratorAgent
        from agents.resources import ResourcesAgent
        from agents.security import SecurityAgent

        self.agents = {
            "orchestrator": OrchestratorAgent(
                message_bus=self.message_bus,
                llm=self.llm,
                config=self.config.get("orchestrator", {}),
            ),
            "monetization": MonetizationAgent(
                message_bus=self.message_bus,
                config=self.config.get("monetization", {}),
            ),
            "devops": DevOpsAgent(
                message_bus=self.message_bus,
                config=self.config.get("devops", {}),
            ),
            "resources": ResourcesAgent(
                message_bus=self.message_bus,
                config=self.config.get("resources", {}),
            ),
            "security": SecurityAgent(
                message_bus=self.message_bus,
                config=self.config.get("security", {}),
            ),
            "analytics": AnalyticsAgent(
                message_bus=self.message_bus,
                config=self.config.get("analytics", {}),
            ),
        }

    def _register_agents(self) -> None:
        """Subscribe every agent handler to the message bus."""
        for name, agent in self.agents.items():
            self.message_bus.subscribe(name, agent.on_message)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize_all(self) -> None:
        """Create (if needed), register, and start all agents."""
        if not self.agents:
            self._create_default_agents()
        self._register_agents()
        for agent in self.agents.values():
            await agent.start()
        logger.info("All agents initialized (%d total)", len(self.agents))

    async def stop_all(self) -> None:
        """Stop all running agents gracefully."""
        for agent in self.agents.values():
            await agent.stop()
        logger.info("All agents stopped")
