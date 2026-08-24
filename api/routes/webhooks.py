"""Webhook routes — Stripe and generic event ingestion."""
import hashlib
import hmac
import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
) -> Dict[str, Any]:
    """Receive Stripe webhook events."""
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    body = await request.body()

    if webhook_secret:
        # Verify Stripe signature
        try:
            import stripe  # type: ignore

            event = stripe.Webhook.construct_event(body, stripe_signature, webhook_secret)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Webhook error: {exc}") from exc
        event_type = event.get("type", "unknown")
    else:
        payload = await request.json()
        event_type = payload.get("type", "unknown")

    logger.info("Stripe webhook received: %s", event_type)
    return {"received": True, "type": event_type}


@router.post("/events")
async def generic_event(request: Request) -> Dict[str, Any]:
    """Receive generic events from external systems."""
    payload: Dict[str, Any] = await request.json()
    event_type = payload.get("type", "unknown")
    logger.info("Generic event received: %s", event_type)
    return {"received": True, "type": event_type}
