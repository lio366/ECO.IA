"""Inter-agent communication via an in-process async message bus."""
import asyncio, logging, uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Optional
logger = logging.getLogger(__name__)

@dataclass
class Message:
    sender: str
    target: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: Optional[str] = None
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
    def __str__(self):
        return f"Message(id={self.message_id}, {self.sender}->{self.target})"

Handler = Callable[["Message"], Coroutine[Any, Any, None]]

class MessageBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Handler]] = {}
        self._history: List[Message] = []
        self._max_history = 1000
    async def subscribe(self, agent_name: str, handler: Handler):
        for key in (agent_name, "*"):
            self._subscribers.setdefault(key, []).append(handler)
    async def unsubscribe(self, agent_name: str, handler: Handler):
        for key in (agent_name, "*"):
            h = self._subscribers.get(key, [])
            if handler in h: h.remove(handler)
    async def publish(self, message: Message):
        self._store(message)
        handlers = list(self._subscribers.get(message.target, []))
        if message.target != "*":
            for h in self._subscribers.get("*", []):
                if h not in handlers: handlers.append(h)
        await asyncio.gather(*[h(message) for h in handlers], return_exceptions=True)
    def _store(self, msg: Message):
        self._history.append(msg)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
    def get_history(self, limit: int = 50): return self._history[-limit:]
    def get_stats(self):
        return {"total_messages": len(self._history),
                "subscribers": {k: len(v) for k, v in self._subscribers.items()}}
