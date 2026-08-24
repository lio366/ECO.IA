"""Simple async task scheduler for periodic agent tasks."""
import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)

TaskFunc = Callable[[], Coroutine[Any, Any, None]]


class ScheduledTask:
    def __init__(
        self,
        name: str,
        func: TaskFunc,
        interval_seconds: int,
        description: str = "",
    ) -> None:
        self.name = name
        self.func = func
        self.interval_seconds = interval_seconds
        self.description = description
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
        self._task: Optional[asyncio.Task] = None  # type: ignore[type-arg]


class TaskScheduler:
    def __init__(self) -> None:
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False

    def register(
        self,
        name: str,
        func: TaskFunc,
        interval_seconds: int,
        description: str = "",
    ) -> None:
        self._tasks[name] = ScheduledTask(name, func, interval_seconds, description)
        logger.debug("Registered scheduled task '%s' every %ds.", name, interval_seconds)

    async def start(self) -> None:
        self._running = True
        for task in self._tasks.values():
            task._task = asyncio.create_task(self._run_loop(task))

    async def stop(self) -> None:
        self._running = False
        for task in self._tasks.values():
            if task._task and not task._task.done():
                task._task.cancel()

    async def _run_loop(self, task: ScheduledTask) -> None:
        while self._running:
            await asyncio.sleep(task.interval_seconds)
            try:
                await task.func()
                task.last_run = datetime.utcnow()
                task.run_count += 1
            except Exception as exc:
                task.error_count += 1
                logger.error("Scheduled task '%s' failed: %s", task.name, exc)

    def list_tasks(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "interval_seconds": t.interval_seconds,
                "last_run": t.last_run.isoformat() if t.last_run else None,
                "run_count": t.run_count,
                "error_count": t.error_count,
            }
            for t in self._tasks.values()
        ]
