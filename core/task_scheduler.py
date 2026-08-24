"""Interval-based async task scheduler for ECO-IA."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)

TaskFunc = Callable[[], Awaitable[None]]


@dataclass
class ScheduledTask:
    """Metadata and state for a single scheduled task."""

    name: str
    func: TaskFunc
    interval: float  # seconds between executions
    run_count: int = 0
    error_count: int = 0
    _handle: asyncio.Task | None = field(default=None, repr=False, compare=False)


class TaskScheduler:
    """Run async callables on a fixed interval.

    Each task runs in its own ``asyncio.Task``; the scheduler cancels them
    on :meth:`stop`.  ``asyncio.CancelledError`` is **not** counted as an
    error so that graceful shutdown does not inflate :attr:`~ScheduledTask.error_count`.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, ScheduledTask] = {}
        self._running = False

    def register(
        self,
        name: str,
        func: TaskFunc,
        interval: float | None = None,
        *,
        interval_seconds: float | None = None,
        description: str = "",
    ) -> ScheduledTask:
        """Register *func* to be called every *interval* (or *interval_seconds*) seconds."""
        resolved = interval if interval is not None else interval_seconds
        if resolved is None:
            raise ValueError("Either 'interval' or 'interval_seconds' must be provided")
        scheduled = ScheduledTask(name=name, func=func, interval=resolved)
        self._tasks[name] = scheduled
        return scheduled

    def list_tasks(self) -> list[ScheduledTask]:
        """Alias for :meth:`get_tasks`."""
        return list(self._tasks.values())

    def get_tasks(self) -> list[ScheduledTask]:
        return list(self._tasks.values())

    async def start(self) -> None:
        """Start all registered tasks."""
        self._running = True
        for scheduled in self._tasks.values():
            scheduled._handle = asyncio.create_task(
                self._run_loop(scheduled), name=f"scheduler-{scheduled.name}"
            )

    async def stop(self) -> None:
        """Cancel all running tasks and wait for them to finish."""
        self._running = False
        handles = [t._handle for t in self._tasks.values() if t._handle is not None]
        for handle in handles:
            handle.cancel()
        if handles:
            await asyncio.gather(*handles, return_exceptions=True)

    async def _run_loop(self, scheduled: ScheduledTask) -> None:
        """Run *scheduled.func* repeatedly until the scheduler stops."""
        while self._running:
            try:
                await scheduled.func()
                scheduled.run_count += 1
            except asyncio.CancelledError:
                # Graceful shutdown — do NOT increment error_count.
                raise
            except Exception as exc:  # noqa: BLE001
                scheduled.error_count += 1
                logger.error("Task %s raised: %s", scheduled.name, exc)
            try:
                await asyncio.sleep(scheduled.interval)
            except asyncio.CancelledError:
                raise
