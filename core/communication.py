"""Async pub/sub message bus for inter-agent communication."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)

MessageHandler = Callable[["Message"], Awaitable[None]]


@dataclass
class Message:
    """A message routed through the MessageBus."""

    source: str
    target: str  # agent name or "*" for broadcast
    type: str
    payload: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: str | None = None

    def __post_init__(self) -> None:
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())

    @property
    def sender(self) -> str:
        return self.source

    @sender.setter
    def sender(self, value: str) -> None:
        self.source = value

    @property
    def content(self) -> dict:
        return self.payload

    @content.setter
    def content(self, value: dict) -> None:
        self.payload = value

    @property
    def id(self) -> str:
        return self.message_id or ""


class _NoopAwaitable:
    """Awaitable no-op result to support optional awaiting on subscriptions."""

    def __await__(self):
        async def _noop() -> None:
            return None

        return _noop().__await__()


class MessageBus:
    """Async publish/subscribe message bus.

    Agents subscribe with a name (or ``"*"`` to receive all messages).
    Wildcard (``target="*"``) broadcasts are deduplicated so that a handler
    registered under multiple names is invoked only once.
    """

    def __init__(self) -> None:
        # Maps agent_name -> list of handlers
        self._subscribers: dict[str, list[MessageHandler]] = {}
        self._history: list[Message] = []
        self._max_history = 1000

    def subscribe(self, agent_name: str, handler: MessageHandler) -> _NoopAwaitable:
        """Register *handler* to receive messages addressed to *agent_name*."""
        self._subscribers.setdefault(agent_name, [])
        self._subscribers[agent_name].append(handler)
        return _NoopAwaitable()

    def unsubscribe(self, agent_name: str, handler: MessageHandler) -> _NoopAwaitable:
        """Remove *handler* from *agent_name* subscriptions."""
        bucket = self._subscribers.get(agent_name, [])
        if handler in bucket:
            bucket.remove(handler)
        return _NoopAwaitable()

    async def publish(self, message: Message) -> None:
        """Deliver *message* to the appropriate subscriber(s).

        If ``message.target == "*"`` every **unique** handler object
        receives exactly one copy of the message, regardless of how many
        agent names it is registered under.
        """
        self._store(message)

        if message.target == "*":
            seen: set[int] = set()
            handlers: list[MessageHandler] = []
            for bucket in self._subscribers.values():
                for h in bucket:
                    if id(h) not in seen:
                        seen.add(id(h))
                        handlers.append(h)
        else:
            handlers = list(self._subscribers.get(message.target, []))
            for handler in self._subscribers.get("*", []):
                if handler not in handlers:
                    handlers.append(handler)

        results = await asyncio.gather(
            *(handler(message) for handler in handlers),
            return_exceptions=True,
        )
        for handler, result in zip(handlers, results, strict=False):
            if isinstance(result, Exception):
                logger.exception("Handler %r raised for message %s", handler, message.id, exc_info=result)

    def _store(self, message: Message) -> None:
        self._history.append(message)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

    def get_history(self, limit: int = 50) -> list[Message]:
        return self._history[-limit:]

    def get_stats(self) -> dict[str, object]:
        return {
            "total_messages": len(self._history),
            "subscribers": {name: len(handlers) for name, handlers in self._subscribers.items()},
        }
