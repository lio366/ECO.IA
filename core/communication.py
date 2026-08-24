"""Async pub/sub message bus for inter-agent communication."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
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
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class MessageBus:
    """Async publish/subscribe message bus.

    Agents subscribe with a name (or ``"*"`` to receive all messages).
    Wildcard (``target="*"``) broadcasts are deduplicated so that a handler
    registered under multiple names is invoked only once.
    """

    def __init__(self) -> None:
        # Maps agent_name -> list of handlers
        self._subscribers: dict[str, list[MessageHandler]] = {}

    def subscribe(self, agent_name: str, handler: MessageHandler) -> None:
        """Register *handler* to receive messages addressed to *agent_name*."""
        self._subscribers.setdefault(agent_name, [])
        self._subscribers[agent_name].append(handler)

    def unsubscribe(self, agent_name: str, handler: MessageHandler) -> None:
        """Remove *handler* from *agent_name* subscriptions."""
        bucket = self._subscribers.get(agent_name, [])
        if handler in bucket:
            bucket.remove(handler)

    async def publish(self, message: Message) -> None:
        """Deliver *message* to the appropriate subscriber(s).

        If ``message.target == "*"`` every **unique** handler object
        receives exactly one copy of the message, regardless of how many
        agent names it is registered under.
        """
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

        for handler in handlers:
            try:
                await handler(message)
            except Exception:  # noqa: BLE001
                logger.exception("Handler %r raised for message %s", handler, message.id)
