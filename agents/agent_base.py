"""Base class for all ECO-IA agents."""
import asyncio, logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from .communication import MessageBus, Message
logger = logging.getLogger(__name__)

class AgentBase(ABC):
    def __init__(self, name, description, message_bus=None, config=None):
        self.name = name; self.description = description
        self.message_bus = message_bus; self.config = config or {}
        self.is_running = False; self.last_heartbeat = None
        self.tasks_completed = 0; self.tasks_failed = 0
        self._logger = logging.getLogger(f"eco_ia.agents.{name}")
    async def start(self):
        self.is_running = True
        if self.message_bus:
            await self.message_bus.subscribe(self.name, self._handle_message)
        await self.on_start()
        asyncio.create_task(self._heartbeat_loop())
    async def stop(self):
        self.is_running = False; await self.on_stop()
    @abstractmethod
    async def on_start(self): pass
    @abstractmethod
    async def on_stop(self): pass
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]: pass
    async def _handle_message(self, message):
        try: await self.on_message(message)
        except Exception as e: self._logger.error("Message error: %s", e)
    async def on_message(self, message): pass
    async def send_message(self, target, content):
        if not self.message_bus: return
        await self.message_bus.publish(Message(sender=self.name, target=target, content=content))
    async def _heartbeat_loop(self):
        interval = self.config.get("heartbeat_interval", 30)
        while self.is_running:
            self.last_heartbeat = datetime.utcnow(); await asyncio.sleep(interval)
    def health_status(self):
        return {"name": self.name, "is_running": self.is_running,
                "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                "tasks_completed": self.tasks_completed, "tasks_failed": self.tasks_failed}
    def get_config(self, key, default=None): return self.config.get(key, default)
