"""POST /webhooks/{channel} - receives WasenderAPI webhooks."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Header
from src.database import get_db
from src.utils.logger import get_logger
from src.config import get_settings

router = APIRouter()
logger = get_logger(__name__)

PROOF_GROUP_JID = "120363428841556134@g.us"


async def verify_webhook_signature(
    payload: bytes,
    signature: Optional[str],
    secret: str,
) -> bool:
    """Verify WasenderAPI webhook signature."""
    if not signature or not secret:
        logger.warning("Missing webhook signature or secret")
        return False
    
    # WasenderAPI uses HMAC-SHA256
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures (constant-time comparison)
    return hmac.compare_digest(expected, signature)


async def get_webhook_secret() -> str:
    """Get webhook secret from config."""
    settings = get_settings()
    # Try to get from system_config first
    try:
        db = get_db()
        config_resp = db.table("system_config").select("value").eq("key", "wasender_webhook_secret").limit(1).execute()
        if config_resp.data:
            secret = config_resp.data[0]["value"].get("secret")
            if secret:
                return secret
    except Exception:
        pass  # Table may not exist yet
    
    # Fallback to environment variable (must be set separately from API key)
    if settings.wasender_webhook_secret:
        return settings.wasender_webhook_secret
    
    # No secret configured - reject webhook
    raise RuntimeError("Webhook secret not configured. Set WASENDER_WEBHOOK_SECRET in .env or system_config.")


@router.post("/webhooks/{channel}")
async def handle_webhook(
    channel: str,
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
):
    """Handle WasenderAPI webhooks with signature verification."""
    db = get_db()
    
    # Get raw body for signature verification
    body = await request.body()
    
    # Handle Header objects from direct calls
    sig = x_signature if isinstance(x_signature, str) else (x_signature.headers.get("X-Signature") if hasattr(x_signature, 'headers') else None)
    
    # Verify signature
    secret = await get_webhook_secret()
    if not await verify_webhook_signature(body, sig, secret):
        logger.warning(f"Invalid webhook signature for channel {channel}")
        raise HTTPException(401, "Invalid signature")
    
    # Check timestamp for replay protection (5 min window)
    if x_timestamp:
        try:
            ts = int(x_timestamp)
            now = int(datetime.now(timezone.utc).timestamp())
            if abs(now - ts) > 300:  # 5 minutes
                logger.warning(f"Webhook timestamp too old: {x_timestamp}")
                raise HTTPException(401, "Timestamp expired")
        except ValueError:
            logger.warning(f"Invalid timestamp header: {x_timestamp}")
    
    # Check idempotency key
    idempotency_key = request.headers.get("X-Idempotency-Key")
    if idempotency_key:
        existing = db.table("audit_log").select("id").eq("details->>idempotency_key", idempotency_key).limit(1).execute()
        if existing.data:
            logger.info(f"Duplicate webhook ignored: {idempotency_key}")
            return {"status": "ok", "duplicate": True}
    
    payload = json.loads(body)
    
    logger.info(f"Webhook received: {channel} - event: {payload.get('event')}")
    
    event = payload.get("event")
    
    try:
        # Handle delivery status updates
        if event in ("messages.sent", "messages.updated", "messages.deleted"):
            await handle_delivery_status(channel, payload)
        
        # Handle incoming messages (payment proofs)
        elif event == "messages.received":
            await handle_incoming_message(channel, payload)
        
        # Handle group events
        elif event in ("groups.update", "groups.upsert", "groups.delete", "group.participants.update"):
            logger.info(f"Group event: {event}")
            await handle_group_event(channel, payload)
        
        else:
            logger.warning(f"Unhandled webhook event: {event}")
        
        # Log successful processing for idempotency
        if idempotency_key:
            db.table("audit_log").insert({
                "actor": "system",
                "action": "webhook_processed",
                "entity_type": "webhook",
                "entity_id": idempotency_key,
                "details": {
                    "channel": channel,
                    "event": event,
                    "idempotency_key": idempotency_key,
                },
            }).execute()
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(500, "Internal server error")
    
    return {"status": "ok"}


async def handle_delivery_status(channel: str, payload: dict):
    """Handle message delivery status updates."""
    db = get_db()
    data = payload.get("data", {})
    messages = data.get("messages")
    
    if not messages:
        return
    
    msg_list = messages if isinstance(messages, list) else [messages]
    
    for msg in msg_list:
        key = msg.get("key", {})
        message_id = key.get("id")
        status = msg.get("status") or msg.get("messageStatus")
        
        if message_id and status:
            status_mapping = {
                "sent": "sent",
                "delivered": "delivered",
                "read": "read",
                "failed": "failed",
                "pending": "pending",
            }
            mapped_status = status_mapping.get(str(status).lower(), status)
            
            result = db.table("reminder_log").update({"delivery_status": mapped_status}).eq("external_message_id", str(message_id)).execute()
            if not result.data:
                db.table("reminder_log").update({"delivery_status": mapped_status}).eq("id", str(message_id)).execute()
            
            logger.info(f"Delivery status: {channel} message {message_id} -> {mapped_status}")


async def handle_incoming_message(channel: str, payload: dict):
    """Handle incoming messages - check for payment proofs in proof submission group."""
    db = get_db()
    data = payload.get("data", {})
    messages = data.get("messages")
    
    if not messages:
        return
    
    msg_list = messages if isinstance(messages, list) else [messages]
    
    for msg in msg_list:
        key = msg.get("key", {})
        message_body = msg.get("messageBody", "")
        raw_message = msg.get("message", {})
        
        # Get sender phone (use cleanedParticipantPn for groups, cleanedSenderPn for private)
        sender_phone = key.get("cleanedParticipantPn") or key.get("cleanedSenderPn") or key.get("remoteJid")
        message_id = key.get("id")
        remote_jid = key.get("remoteJid")  # group JID
        from_me = key.get("fromMe", False)
        
        # Skip messages from ourselves
        if from_me:
            continue
        
        # Normalize phone number
        if sender_phone and not sender_phone.startswith("+"):
            sender_phone = "+" + sender_phone.lstrip("+")
        
        logger.info(f"Incoming message from {sender_phone} in {remote_jid}: {message_body[:100]}")
        
        # Check if this is in the proof submission group
        if remote_jid == PROOF_GROUP_JID:
            await handle_payment_proof(sender_phone, remote_jid, message_body, raw_message, message_id)


async def handle_payment_proof(sender_phone: str, group_jid: str, message_body: str, raw_message: dict, message_id: str):
    """Process a payment proof submission."""
    db = get_db()
    
    try:
        # Find student by phone
        student_resp = db.table("students").select("id").eq("phone", sender_phone).limit(1).execute()
        if not student_resp.data:
            logger.warning(f"Unknown student submitted proof: {sender_phone}")
            # Could auto-create student here if needed
            return
        
        student_id = student_resp.data[0]["id"]
        
        # Find the active course for this proof group
        course_resp = db.table("courses").select("id").eq("name", "IELTS Preparation (Oct 15-30, 6-8pm GMT)").eq("is_active", True).limit(1).execute()
        if not course_resp.data:
            logger.error("No active IELTS course found")
            return
        course_id = course_resp.data[0]["id"]
        
        # Check if payment already exists for this student/course
        existing = db.table("payments").select("id, status").eq("student_id", student_id).eq("course_id", course_id).limit(1).execute()
        
        # Extract media URL if present (image/document)
        proof_url = None
        if "imageMessage" in raw_message:
            proof_url = raw_message["imageMessage"].get("url")
        elif "documentMessage" in raw_message:
            proof_url = raw_message["documentMessage"].get("url")
        elif "videoMessage" in raw_message:
            proof_url = raw_message["videoMessage"].get("url")
        
        payment_data = {
            "student_id": student_id,
            "course_id": course_id,
            "amount": 100.00,
            "currency": "GHS",
            "method": "momo",
            "reference": "ILETS",
            "proof_url": proof_url,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        if existing.data:
            payment_id = existing.data[0]["id"]
            db.table("payments").update({
                "proof_url": proof_url,
                "status": "pending",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", payment_id).execute()
            logger.info(f"Updated payment proof for student {student_id}: {payment_id}")
        else:
            payment_resp = db.table("payments").insert(payment_data).execute()
            if payment_resp.data:
                payment_id = payment_resp.data[0]["id"]
                logger.info(f"Created payment record for student {student_id}: {payment_id}")
            else:
                logger.error("Failed to create payment record")
                return
        
        # Create approval for verification
        from uuid import uuid4
        approval_id = str(uuid4())
        db.table("approvals").insert({
            "id": approval_id,
            "action_type": "verify_payment",
            "content": f"Payment proof received from {sender_phone} (Student ID: {student_id}) for IELTS course. Proof URL: {proof_url}",
            "target_group_jid": group_jid,
            "target_course_id": course_id,
            "metadata": {
                "payment_id": payment_id,
                "student_phone": sender_phone,
                "message_body": message_body,
                "proof_url": proof_url,
            },
            "status": "pending",
            "requested_by": "agent",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        
        logger.info(f"Created payment verification approval {approval_id} for student {student_id}")
        
        # Send confirmation to student in the group
        await send_confirmation_to_student(group_jid, sender_phone, payment_id)
        
    except Exception as e:
        logger.error(f"Error processing payment proof: {e}")


async def send_confirmation_to_student(group_jid: str, student_phone: str, payment_id: str):
    """Send confirmation message to student in the proof group."""
    from src.config import get_settings
    from src.channels.base import get_channel
    
    settings = get_settings()
    message = f"✅ Payment proof received! Your proof has been submitted (ID: {payment_id[:8]}...). Admin will verify shortly. You'll be added to the class group once verified."
    
    channel = get_channel("whatsapp")
    ok, _ = await channel.send(recipient=group_jid, message=message)
    
    if ok:
        logger.info(f"Confirmation sent to {student_phone} in proof group")
    else:
        logger.error(f"Failed to send confirmation")


async def handle_group_event(channel: str, payload: dict):
    """Handle group events (create, update, delete, participants)."""
    db = get_db()
    event = payload.get("event")
    data = payload.get("data", {})
    
    # Sync group info to local DB
    if event in ("groups.upsert", "groups.update"):
        groups = data.get("groups", [])
        for group in groups:
            db.table("groups").upsert({
                "whatsapp_jid": group.get("id"),
                "name": group.get("name", group.get("subject", "Unknown")),
                "type": "community" if group.get("isCommunity") else "announcement",
                "is_active": True,
                "settings": group,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }, on_conflict="whatsapp_jid").execute()


def verify_webhook_signature(payload: bytes, signature: Optional[str], secret: str) -> bool:
    """Verify WasenderAPI webhook signature using HMAC-SHA256."""
    import hmac
    import hashlib
    
    if not signature or not secret:
        return False
    
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)