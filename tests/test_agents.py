"""Tests for core agents and message bus."""
import asyncio
import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.communication import Message, MessageBus
from core.agent_base import AgentBase
from core.scheduler import TaskScheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class DummyAgent(AgentBase):
    async def on_start(self) -> None:
        pass

    async def on_stop(self) -> None:
        pass

    async def execute(self, task):
        return {"status": "ok"}


# ---------------------------------------------------------------------------
# MessageBus tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_message_bus_subscribe_and_publish():
    bus = MessageBus()
    received = []

    async def handler(msg: Message):
        received.append(msg)

    await bus.subscribe("agent_a", handler)
    await bus.publish(Message(sender="agent_b", target="agent_a", content={"hello": 1}))
    assert len(received) == 1
    assert received[0].content == {"hello": 1}


@pytest.mark.asyncio
async def test_message_bus_wildcard():
    bus = MessageBus()
    received = []

    async def handler(msg: Message):
        received.append(msg)

    await bus.subscribe("agent_a", handler)
    await bus.publish(Message(sender="agent_b", target="*", content={"broadcast": True}))
    assert len(received) == 1


@pytest.mark.asyncio
async def test_message_bus_history():
    bus = MessageBus()

    async def noop(msg):
        pass

    await bus.subscribe("a", noop)
    await bus.publish(Message(sender="x", target="a", content={}))
    await bus.publish(Message(sender="x", target="a", content={}))
    assert len(bus.get_history()) == 2


def test_message_id_auto_generated():
    msg = Message(sender="a", target="b", content={})
    assert msg.message_id is not None
    assert len(msg.message_id) > 0


# ---------------------------------------------------------------------------
# AgentBase tests
# ---------------------------------------------------------------------------

def test_agent_health_status():
    agent = DummyAgent(name="test_agent", description="test")
    status = agent.health_status()
    assert status["name"] == "test_agent"
    assert status["is_running"] is False
    assert status["last_heartbeat"] is None
    assert status["tasks_completed"] == 0


def test_agent_get_config():
    agent = DummyAgent(name="a", description="b", config={"foo": "bar"})
    assert agent.get_config("foo") == "bar"
    assert agent.get_config("missing", "default") == "default"


# ---------------------------------------------------------------------------
# TaskScheduler tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scheduler_register_and_list():
    scheduler = TaskScheduler()
    called = []

    async def my_task():
        called.append(1)

    scheduler.register("my_task", my_task, interval_seconds=9999, description="test task")
    tasks = scheduler.list_tasks()
    assert len(tasks) == 1
    assert tasks[0]["name"] == "my_task"


# ---------------------------------------------------------------------------
# OrchestratorAgent tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_orchestrator_register_and_list_agents():
    from agents.orchestrator.agent import OrchestratorAgent

    orch = OrchestratorAgent()
    result = await orch.execute({"type": "register_agent", "agent_name": "analytics", "description": "test"})
    assert result["status"] == "registered"

    result2 = await orch.execute({"type": "list_agents"})
    assert any(a["name"] == "analytics" for a in result2["agents"])


@pytest.mark.asyncio
async def test_orchestrator_health_report():
    from agents.orchestrator.agent import OrchestratorAgent

    orch = OrchestratorAgent()
    result = await orch.execute({"type": "health_report"})
    assert "orchestrator" in result
    assert "registered_agents" in result


@pytest.mark.asyncio
async def test_orchestrator_llm_not_configured():
    from agents.orchestrator.agent import OrchestratorAgent

    orch = OrchestratorAgent()
    result = await orch.execute({"type": "llm_decision", "question": "test?"})
    assert result.get("error") == "LLM not configured"
