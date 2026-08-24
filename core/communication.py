"""Inter-agent communication via an in-process async message bus."""
import asyncio
import logging
import uuid
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

    def __post_init__(self) -> None:
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())

    def __str__(self) -> str:
        return f"Message(id={self.message_id}, {self.sender}->{self.target})"


Handler = Callable[["Message"], Coroutine[Any, Any, None]]


class MessageBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Handler]] = {}
        self._history: List[Message] = []
        self._max_history = 1000

    async def subscribe(self, agent_name: str, handler: Handler) -> None:
        # Register only under the agent's own name; "*" is reserved for
        # explicit broadcast subscribers so targeted messages are not
        # inadvertently fanned out to every subscribed handler.
        self._subscribers.setdefault(agent_name, []).append(handler)

    async def unsubscribe(self, agent_name: str, handler: Handler) -> None:
        h = self._subscribers.get(agent_name, [])
        if handler in h:
            h.remove(handler)

    async def publish(self, message: Message) -> None:
        self._store(message)
        if message.target == "*":
            # Broadcast: deliver to every registered handler (deduplicated)
            seen: set = set()
            handlers = []
            for bucket in self._subscribers.values():
                for h in bucket:
                    if id(h) not in seen:
                        seen.add(id(h))
                        handlers.append(h)
        else:
            handlers = list(self._subscribers.get(message.target, []))
        await asyncio.gather(*[h(message) for h in handlers], return_exceptions=True)

    def _store(self, msg: Message) -> None:
        self._history.append(msg)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_history(self, limit: int = 50) -> List[Message]:
        return self._history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_messages": len(self._history),
            "subscribers": {k: len(v) for k, v in self._subscribers.items()},
        }
