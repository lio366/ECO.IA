"""Webhooks router — receive external event notifications."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(request: Request) -> JSONResponse:
    """Handle incoming Stripe webhook events."""
    try:
        payload: dict[str, Any] = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"detail": "Invalid JSON payload"}, status_code=400)

    event_type = payload.get("type", "unknown")
    logger.info("Received Stripe webhook: %s", event_type)

    message_bus = request.app.state.message_bus
    from core.communication import Message

    await message_bus.publish(
        Message(source="webhook.stripe", target="monetization", type="stripe.event", payload=payload)
    )
    return JSONResponse({"received": True})


@router.post("/generic")
async def generic_webhook(request: Request) -> JSONResponse:
    """Receive a generic webhook and publish it to the message bus."""
    try:
        payload: dict[str, Any] = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"detail": "Invalid JSON payload"}, status_code=400)

    logger.info("Received generic webhook: %s", payload.get("type", "unknown"))
    return JSONResponse({"received": True})
