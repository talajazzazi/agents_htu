"""
Minimal Twilio WhatsApp send.
Uses Django settings: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
TWILIO_WHATSAPP_NUMBER (from), TWILIO_WHATSAPP_TO (recipient).
"""
from __future__ import annotations

import logging
from typing import List

from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    _TWILIO_AVAILABLE = True
except ImportError:
    Client = None
    TwilioRestException = None
    _TWILIO_AVAILABLE = False


def get_twilio_client():
    """Create Twilio client using settings."""
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    if not sid or not token:
        raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in settings/.env")
    return Client(sid, token)


def send_whatsapp_messages(to: str, messages: List[dict]) -> List[str]:
    """
    Send WhatsApp messages via Twilio.
    messages: [{"text": str, "image": str | None}, ...]
    Returns: list of Twilio message SIDs, or raises.
    """
    if not _TWILIO_AVAILABLE:
        raise RuntimeError("twilio not installed. Run: pip install twilio")

    client = get_twilio_client()
    from_ = settings.TWILIO_WHATSAPP_NUMBER
    if not from_:
        raise ValueError("TWILIO_WHATSAPP_NUMBER must be set in settings/.env")
    if not from_.startswith("whatsapp:"):
        from_ = f"whatsapp:{from_}"
    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    sids = []
    try:
        for msg in messages:
            body = msg.get("text") or ""
            media = msg.get("image")
            media_urls = [media] if media else None
            resp = client.messages.create(
                body=body,
                from_=from_,
                to=to,
                media_url=media_urls,
            )
            sids.append(resp.sid)
        return sids
    except TwilioRestException as e:
        if e.code == 63007:
            raise RuntimeError(
                "Twilio error 63007: Invalid WhatsApp 'From' number. "
                "Use the WhatsApp Sandbox number (e.g. +14155238886) from "
                "Twilio Console → Messaging → Try it out → Send a WhatsApp message, "
                "or an approved WhatsApp Sender. Set it as TWILIO_WHATSAPP_NUMBER."
            ) from e
        raise
