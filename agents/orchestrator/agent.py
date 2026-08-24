"""🧠 Orchestrator Agent - Master coordinator for all ECO-IA agents."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.agent_base import AgentBase
from core.communication import Message, MessageBus
from core.llm_connector import LLMConnector
from core.scheduler import TaskScheduler


logger = logging.getLogger(__name__)


class OrchestratorAgent(AgentBase):
    """Master agent that coordinates all other agents.

    Responsibilities:
    - Monitor the health of every agent.
    - Route tasks to the appropriate specialist agent.
    - Take high-level decisions using an LLM.
    - Generate executive reports.
    - Resolve conflicts between agents.
    """

    SYSTEM_PROMPT = (
        "You are the master orchestrator of ECO-IA, an autonomous server system. "
        "Your role is to coordinate specialist agents (Monetization, DevOps, Resources, "
        "Security, Analytics), make high-level decisions, resolve conflicts, and ensure "
        "the system is self-sustaining, generates income, and remains sustainable. "
        "Always respond concisely and provide actionable instructions."
    )

    def __init__(
        self,
        message_bus: Optional[MessageBus] = None,
        llm: Optional[LLMConnector] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            name="orchestrator",
            description="Master coordinator for all ECO-IA agents",
            message_bus=message_bus,
            config=config,
        )
        self.llm = llm
        self.scheduler = TaskScheduler()
        self._agent_registry: Dict[str, Dict[str, Any]] = {}
        self._decisions_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def on_start(self) -> None:
        self.scheduler.register(
            "health_check",
            self._check_agents_health,
            interval_seconds=self.get_config("health_check_interval", 60),
            description="Periodic health check of all registered agents",
        )
        self.scheduler.register(
            "executive_report",
            self._generate_executive_report,
            interval_seconds=self.get_config("report_interval", 3600),
            description="Hourly executive report",
        )
        await self.scheduler.start()

    async def on_stop(self) -> None:
        await self.scheduler.stop()

    # ------------------------------------------------------------------
    # Task execution
    # ------------------------------------------------------------------

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route a task to the appropriate agent or handle it directly."""
        task_type = task.get("type", "unknown")
        self._logger.info("Orchestrator received task: %s", task_type)

        if task_type == "llm_decision":
            return await self._make_llm_decision(task)
        if task_type == "health_report":
            return self._get_health_report()
        if task_type == "register_agent":
            return self._register_agent(task)
        if task_type == "list_agents":
            return {"agents": list(self._agent_registry.values())}

        # Default: broadcast to all agents
        await self.send_message("*", task)
        return {"status": "broadcasted", "task": task_type}

    # ------------------------------------------------------------------
    # Agent registry
    # ------------------------------------------------------------------

    def _register_agent(self, task: Dict[str, Any]) -> Dict[str, Any]:
        agent_name = task.get("agent_name", "unknown")
        self._agent_registry[agent_name] = {
            "name": agent_name,
            "description": task.get("description", ""),
            "registered_at": datetime.utcnow().isoformat(),
            "status": "active",
        }
        self._logger.info("Agent '%s' registered.", agent_name)
        return {"status": "registered", "agent": agent_name}

    def _get_health_report(self) -> Dict[str, Any]:
        return {
            "orchestrator": self.health_status(),
            "registered_agents": self._agent_registry,
            "scheduler_tasks": self.scheduler.list_tasks(),
            "recent_decisions": self._decisions_log[-10:],
        }

    # ------------------------------------------------------------------
    # Scheduled tasks
    # ------------------------------------------------------------------

    async def _check_agents_health(self) -> None:
        self._logger.info("Running agent health check.")
        if self.message_bus:
            health_request = Message(
                sender=self.name,
                target="*",
                content={"type": "health_ping"},
            )
            await self.message_bus.publish(health_request)

    async def _generate_executive_report(self) -> None:
        if not self.llm:
            return

        context = {
            "agents": list(self._agent_registry.keys()),
            "scheduler_tasks": self.scheduler.list_tasks(),
        }
        prompt = (
            f"Generate a concise executive report for the ECO-IA autonomous server system. "
            f"Current state: {context}. "
            "Include: system health summary, income generation status, resource efficiency, "
            "and top 3 recommended actions."
        )
        try:
            report = await self.llm.complete(prompt)
            decision: Dict[str, Any] = {
                "type": "executive_report",
                "timestamp": datetime.utcnow().isoformat(),
                "report": report,
            }
            self._decisions_log.append(decision)
            self._logger.info("Executive report generated.")
        except Exception as exc:  # noqa: BLE001
            self._logger.error("Failed to generate executive report: %s", exc)

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    async def on_message(self, message: Message) -> None:
        content = message.content
        msg_type = content.get("type")

        if msg_type == "health_pong":
            agent_name = content.get("agent_name", message.sender)
            if agent_name in self._agent_registry:
                self._agent_registry[agent_name]["last_seen"] = datetime.utcnow().isoformat()
                self._agent_registry[agent_name]["status"] = "active"

        elif msg_type == "alert":
            await self._handle_alert(message)

    async def _handle_alert(self, message: Message) -> None:
        alert = message.content
        self._logger.warning("Alert from '%s': %s", message.sender, alert.get("message"))
        decision: Dict[str, Any] = {
            "type": "alert_response",
            "timestamp": datetime.utcnow().isoformat(),
            "from_agent": message.sender,
            "alert": alert,
        }
        self._decisions_log.append(decision)

        if self.llm:
            prompt = (
                f"An alert was raised by agent '{message.sender}': {alert.get('message')}. "
                "Provide a brief action plan to resolve it."
            )
            try:
                action_plan = await self.llm.complete(prompt)
                self._logger.info("LLM action plan: %s", action_plan)
                decision["action_plan"] = action_plan
            except Exception as exc:  # noqa: BLE001
                self._logger.error("LLM error during alert handling: %s", exc)

    # ------------------------------------------------------------------
    # LLM decision
    # ------------------------------------------------------------------

    async def _make_llm_decision(self, task: Dict[str, Any]) -> Dict[str, Any]:
        if not self.llm:
            return {"error": "LLM not configured"}
        question = task.get("question", "")
        context = task.get("context", "")
        prompt = f"Context: {context}\n\nQuestion: {question}"
        answer = await self.llm.chat(
            [{"role": "user", "content": prompt}],
            system_prompt=self.SYSTEM_PROMPT,
        )
        decision: Dict[str, Any] = {
            "type": "llm_decision",
            "timestamp": datetime.utcnow().isoformat(),
            "question": question,
            "answer": answer,
        }
        self._decisions_log.append(decision)
        return decision
