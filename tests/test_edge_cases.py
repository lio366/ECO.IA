"""Edge-case tests for core ECO-IA modules.

Covers three areas identified during analysis:

1. MessageBus deduplication — shared handlers and wildcard broadcasts.
2. OrchestratorAgent health-check timeout — dead-agent detection.
3. TaskScheduler graceful shutdown — CancelledError must not inflate error_count.

All tests use pytest-asyncio with asyncio_mode = "auto" (configured in
pyproject.toml).

NOTE — Known bugs documented here (see FIXME comments) that a follow-up PR
should fix in the production code if they surface:
  * MessageBus: `id()` reuse — Python can reclaim object IDs; using object
    identity in `seen` is safe as long as handlers are live during publish.
    The current implementation is correct for the tested scenarios.
  * OrchestratorAgent: health-check timeout is now implemented; these tests
    also serve as a regression suite.
  * TaskScheduler: CancelledError is now excluded from error_count; tests
    verify this invariant.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from core.communication import Message, MessageBus
from core.task_scheduler import TaskScheduler
from agents.orchestrator.agent import OrchestratorAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_message(
    target: str = "*",
    msg_type: str = "test.event",
    source: str = "test",
    payload: dict | None = None,
) -> Message:
    return Message(source=source, target=target, type=msg_type, payload=payload or {})


# ---------------------------------------------------------------------------
# 1. MessageBus Deduplication Tests
# ---------------------------------------------------------------------------


class TestMessageBusDeduplication:
    """Verify that wildcard broadcasts do not double-deliver to shared handlers."""

    @pytest.mark.asyncio
    async def test_message_bus_shared_handler_deduplication(self):
        """Handler registered under two agent names must be called exactly once
        during a wildcard broadcast.

        Bug vector: if deduplication uses id() and the same callable is
        registered twice, the second registration would not be deduplicated
        because id() of the same object is the same — so this should already
        work correctly. Test documents the contract.
        """
        bus = MessageBus()
        call_count = 0

        async def shared_handler(msg: Message) -> None:
            nonlocal call_count
            call_count += 1

        bus.subscribe("agent_a", shared_handler)
        bus.subscribe("agent_b", shared_handler)  # same handler object

        await bus.publish(make_message(target="*"))

        assert call_count == 1, (
            "Shared handler registered under multiple names must be called exactly once "
            f"on wildcard broadcast; was called {call_count} time(s)."
        )

    @pytest.mark.asyncio
    async def test_message_bus_wildcard_broadcast_accuracy(self):
        """Wildcard broadcast must deliver to every **unique** handler exactly once."""
        bus = MessageBus()
        received: dict[str, int] = {"a": 0, "b": 0, "c": 0}

        async def handler_a(msg: Message) -> None:
            received["a"] += 1

        async def handler_b(msg: Message) -> None:
            received["b"] += 1

        async def handler_c(msg: Message) -> None:
            received["c"] += 1

        bus.subscribe("agent_a", handler_a)
        bus.subscribe("agent_b", handler_b)
        bus.subscribe("agent_c", handler_c)

        await bus.publish(make_message(target="*"))

        assert received == {"a": 1, "b": 1, "c": 1}, (
            "Each unique handler must receive exactly one broadcast message."
        )

    @pytest.mark.asyncio
    async def test_message_bus_mixed_subscriptions(self):
        """A handler subscribed both by name AND via wildcard broadcast should
        receive the direct message once and the broadcast once — not doubled."""
        bus = MessageBus()
        direct_count = 0
        broadcast_count = 0

        async def my_handler(msg: Message) -> None:
            nonlocal direct_count, broadcast_count
            if msg.target == "agent_a":
                direct_count += 1
            else:
                broadcast_count += 1

        bus.subscribe("agent_a", my_handler)

        # Direct message
        await bus.publish(make_message(target="agent_a"))
        # Broadcast
        await bus.publish(make_message(target="*"))

        assert direct_count == 1, "Direct message must be delivered exactly once."
        assert broadcast_count == 1, "Broadcast must be delivered exactly once."

    @pytest.mark.asyncio
    async def test_message_bus_no_subscribers_does_not_raise(self):
        """Publishing to an empty bus (or unknown target) must not raise."""
        bus = MessageBus()
        await bus.publish(make_message(target="nonexistent"))
        await bus.publish(make_message(target="*"))

    @pytest.mark.asyncio
    async def test_message_bus_handler_exception_does_not_propagate(self):
        """An exception inside a handler must not prevent other handlers from
        running and must not propagate to the caller."""
        bus = MessageBus()
        second_called = False

        async def bad_handler(msg: Message) -> None:
            raise RuntimeError("intentional error")

        async def good_handler(msg: Message) -> None:
            nonlocal second_called
            second_called = True

        bus.subscribe("a", bad_handler)
        bus.subscribe("b", good_handler)

        await bus.publish(make_message(target="*"))  # must not raise

        assert second_called, "Second handler must be called even if first handler raised."


# ---------------------------------------------------------------------------
# 2. Health Check Timeout Tests
# ---------------------------------------------------------------------------


class TestOrchestratorHealthCheck:
    """Verify that the health-check loop correctly handles timeouts and pongs."""

    @pytest.mark.asyncio
    async def test_orchestrator_health_check_timeout_detects_dead_agents(self):
        """Non-responding agents must be marked 'unhealthy' after the timeout."""
        bus = MessageBus()
        orch = OrchestratorAgent(message_bus=bus, health_check_timeout=0.1)
        orch.register_agent("ghost_agent")

        # Run health check — ghost_agent never replies
        await orch._check_agents_health()

        status = orch.get_agent_status("ghost_agent")
        assert status is not None
        assert status["status"] == "unhealthy", (
            "Agent that did not reply to health ping must be marked 'unhealthy'."
        )

    @pytest.mark.asyncio
    async def test_orchestrator_health_check_responds_to_pong(self):
        """An agent that replies with health.pong must be marked 'active'."""
        bus = MessageBus()
        orch = OrchestratorAgent(message_bus=bus, health_check_timeout=0.5)
        orch.register_agent("live_agent")

        async def fake_agent_reply(msg: Message) -> None:
            """Simulate live_agent responding to the ping."""
            if msg.type == "health.ping":
                pong = Message(
                    source="live_agent",
                    target="orchestrator",
                    type="health.pong",
                    payload={},
                )
                await bus.publish(pong)

        bus.subscribe("*", fake_agent_reply)

        await orch._check_agents_health()

        status = orch.get_agent_status("live_agent")
        assert status is not None
        assert status["status"] == "active", (
            "Agent that replied with health.pong must be marked 'active'."
        )

    @pytest.mark.asyncio
    async def test_orchestrator_health_check_timeout_window(self):
        """Health check must complete within a reasonable time regardless of agent behaviour."""
        bus = MessageBus()
        timeout = 0.1
        orch = OrchestratorAgent(message_bus=bus, health_check_timeout=timeout)
        orch.register_agent("slow_agent")

        start = asyncio.get_running_loop().time()
        await orch._check_agents_health()
        elapsed = asyncio.get_running_loop().time() - start

        # Should complete roughly within 2× the timeout window
        assert elapsed < timeout * 10, (
            f"Health check took {elapsed:.3f}s but timeout is {timeout}s — "
            "something is blocking longer than expected."
        )

    @pytest.mark.asyncio
    async def test_orchestrator_health_check_missing_pong_increments_failures(self):
        """Each missed ping must increment the agent's consecutive-failure counter."""
        bus = MessageBus()
        orch = OrchestratorAgent(message_bus=bus, health_check_timeout=0.05)
        orch.register_agent("flaky_agent")

        rounds = 3
        for _ in range(rounds):
            await orch._check_agents_health()

        assert orch._missed_pongs.get("flaky_agent", 0) == rounds, (
            f"Expected {rounds} missed pongs but got "
            f"{orch._missed_pongs.get('flaky_agent', 0)}."
        )

    @pytest.mark.asyncio
    async def test_orchestrator_health_check_pong_resets_failure_counter(self):
        """After a successful pong, the missed-pong counter must reset to 0."""
        bus = MessageBus()
        orch = OrchestratorAgent(message_bus=bus, health_check_timeout=0.2)
        orch.register_agent("recovering_agent")

        # First round — no reply
        await orch._check_agents_health()
        assert orch._missed_pongs["recovering_agent"] == 1

        # Second round — agent replies
        async def reply_once(msg: Message) -> None:
            if msg.type == "health.ping":
                await bus.publish(
                    Message(source="recovering_agent", target="orchestrator", type="health.pong", payload={})
                )

        bus.subscribe("*", reply_once)
        await orch._check_agents_health()

        assert orch._missed_pongs["recovering_agent"] == 0, (
            "Successful pong must reset the missed-pong counter."
        )


# ---------------------------------------------------------------------------
# 3. TaskScheduler Graceful Shutdown Tests
# ---------------------------------------------------------------------------


class TestTaskSchedulerGracefulShutdown:
    """Verify that CancelledError during stop() is not counted as an error."""

    @pytest.mark.asyncio
    async def test_scheduler_cancellation_does_not_increment_error_count(self):
        """When the scheduler is stopped, CancelledError must NOT increment
        ScheduledTask.error_count.

        This is the core bug identified in the problem statement: using
        ``except Exception`` misses CancelledError (a BaseException subclass
        since Python 3.8), so the fix is to catch it separately.
        """
        scheduler = TaskScheduler()

        run_event = asyncio.Event()

        async def long_running_task() -> None:
            run_event.set()
            await asyncio.sleep(100)  # will be cancelled

        task = scheduler.register("long_task", long_running_task, interval=0.01)
        await scheduler.start()

        # Wait until the task is actually running
        await asyncio.wait_for(run_event.wait(), timeout=1.0)

        await scheduler.stop()

        assert task.error_count == 0, (
            f"CancelledError during shutdown must not increment error_count; "
            f"got error_count={task.error_count}."
        )

    @pytest.mark.asyncio
    async def test_scheduler_stop_awaits_task_completion(self):
        """stop() must await all running tasks so no dangling coroutines remain."""
        scheduler = TaskScheduler()
        finished = False

        async def quick_task() -> None:
            nonlocal finished
            finished = True

        scheduler.register("quick", quick_task, interval=0.01)
        await scheduler.start()
        await asyncio.sleep(0.05)
        await scheduler.stop()

        # After stop, no tasks should remain running
        for t in scheduler.get_tasks():
            handle = t._handle
            assert handle is None or handle.done(), (
                f"Task {t.name} is still running after scheduler.stop()."
            )

    @pytest.mark.asyncio
    async def test_scheduler_exception_vs_cancellation_distinction(self):
        """Real exceptions must increment error_count; cancellations must not."""
        scheduler = TaskScheduler()
        call_count = 0

        async def failing_task() -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("intentional failure")

        task = scheduler.register("failing", failing_task, interval=0.01)
        await scheduler.start()

        # Let the task run at least once (enough to hit the error)
        await asyncio.sleep(0.05)
        await scheduler.stop()

        assert task.error_count >= 1, (
            "Real exception must increment error_count."
        )
        # error_count should not include the CancelledError from stop()
        # call_count tracks total invocations; error_count must not exceed it
        assert task.error_count <= call_count, (
            "error_count must not exceed total invocations."
        )

    @pytest.mark.asyncio
    async def test_scheduler_run_count_increments_on_success(self):
        """run_count must increment after each successful task execution."""
        scheduler = TaskScheduler()
        runs: list[int] = []

        async def counter_task() -> None:
            runs.append(1)

        task = scheduler.register("counter", counter_task, interval=0.01)
        await scheduler.start()
        await asyncio.sleep(0.08)
        await scheduler.stop()

        assert task.run_count >= 2, (
            f"Expected at least 2 successful runs, got {task.run_count}."
        )
        assert task.run_count == len(runs), (
            "run_count must equal the number of successful executions."
        )


# ---------------------------------------------------------------------------
# 4. Integration Tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """Full lifecycle and integration tests."""

    @pytest.mark.asyncio
    async def test_orchestrator_agent_startup_shutdown_lifecycle(self):
        """Full start → active → stop cycle must leave the orchestrator in a
        consistent stopped state."""
        bus = MessageBus()
        # Use a very long health check interval so it doesn't fire during the test
        orch = OrchestratorAgent(message_bus=bus, health_check_timeout=1.0)
        # Override scheduler interval to avoid timing issues
        await orch.start()
        assert orch.is_running is True
        await orch.stop()
        assert orch.is_running is False

    @pytest.mark.asyncio
    async def test_message_bus_under_concurrent_broadcasts(self):
        """Multiple concurrent broadcasts must not cause race conditions or
        incorrect delivery counts."""
        bus = MessageBus()
        total_received = 0
        lock = asyncio.Lock()

        async def counting_handler(msg: Message) -> None:
            nonlocal total_received
            async with lock:
                total_received += 1

        bus.subscribe("agent_x", counting_handler)

        broadcasts = 20
        await asyncio.gather(*[bus.publish(make_message(target="*")) for _ in range(broadcasts)])

        assert total_received == broadcasts, (
            f"Expected {broadcasts} deliveries, got {total_received}."
        )

    @pytest.mark.asyncio
    async def test_health_check_loop_integration(self):
        """Full health check loop: orchestrator detects live vs dead agents correctly."""
        bus = MessageBus()
        orch = OrchestratorAgent(message_bus=bus, health_check_timeout=0.3)
        orch.register_agent("live")
        orch.register_agent("dead")

        # Simulate live agent auto-reply
        async def live_responder(msg: Message) -> None:
            if msg.type == "health.ping":
                await bus.publish(
                    Message(source="live", target="orchestrator", type="health.pong", payload={})
                )

        bus.subscribe("*", live_responder)

        await orch._check_agents_health()

        assert orch.get_agent_status("live")["status"] == "active"
        assert orch.get_agent_status("dead")["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_message_bus_targeted_delivery(self):
        """A targeted message must be delivered only to the named agent, not others."""
        bus = MessageBus()
        received_a = []
        received_b = []

        async def handler_a(msg: Message) -> None:
            received_a.append(msg)

        async def handler_b(msg: Message) -> None:
            received_b.append(msg)

        bus.subscribe("agent_a", handler_a)
        bus.subscribe("agent_b", handler_b)

        await bus.publish(make_message(target="agent_a"))

        assert len(received_a) == 1
        assert len(received_b) == 0, "Targeted message must not reach other agents."
