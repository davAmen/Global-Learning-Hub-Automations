"""POST /webhooks/{channel} - receives WasenderAPI webhooks."""

from fastapi import APIRouter, Request
from src.database import get_db
from src.utils.logger import get_logger
from datetime import datetime

router = APIRouter()
logger = get_logger(__name__)

PROOF_GROUP_JID = "120363428841556134@g.us"


@router.post("/webhooks/{channel}")
async def handle_webhook(channel: str, request: Request):
    db = get_db()
    payload = await request.json()
    
    logger.info(f"Webhook received: {channel} - event: {payload.get('event')}")
    
    event = payload.get("event")
    
    # Handle delivery status updates (messages.sent, messages.updated, etc.)
    if event in ("messages.sent", "messages.updated", "messages.deleted"):
        await handle_delivery_status(db, channel, payload)
    
    # Handle incoming messages (payment proofs)
    elif event == "messages.received":
        await handle_incoming_message(db, channel, payload)
    
    # Handle group events
    elif event in ("groups.update", "groups.upsert", "groups.delete", "group.participants.update"):
        logger.info(f"Group event: {event} - {payload}")
    
    else:
        logger.warning(f"Unhandled webhook event: {event}")
    
    return {"status": "ok"}


async def handle_delivery_status(db, channel: str, payload: dict):
    """Handle message delivery status updates."""
    data = payload.get("data", {})
    messages = data.get("messages")
    
    if not messages:
        return
    
    # Handle both single message and array
    msg_list = messages if isinstance(messages, list) else [messages]
    
    for msg in msg_list:
        key = msg.get("key", {})
        message_id = key.get("id")
        status = msg.get("status") or msg.get("messageStatus")
        
        if message_id and status:
            status_mapping = {
                "sent": "sent",
                "delivered": "sent",
                "read": "sent",
                "failed": "failed",
                "pending": "pending",
            }
            mapped_status = status_mapping.get(str(status).lower(), status)
            
            result = db.table("reminder_log").update({"delivery_status": mapped_status}).eq("external_message_id", str(message_id)).execute()
            if not result.data:
                db.table("reminder_log").update({"delivery_status": mapped_status}).eq("id", str(message_id)).execute()
            
            logger.info(f"Delivery status: {channel} message {message_id} -> {mapped_status}")


async def handle_incoming_message(db, channel: str, payload: dict):
    """Handle incoming messages - check for payment proofs in proof submission group."""
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
            await handle_payment_proof(db, sender_phone, remote_jid, message_body, raw_message, message_id)


async def handle_payment_proof(db, sender_phone: str, group_jid: str, message_body: str, raw_message: dict, message_id: str):
    """Process a payment proof submission."""
    try:
        # Find student by phone
        student_resp = db.table("students").select("id").eq("phone", sender_phone).limit(1).execute()
        if not student_resp.data:
            logger.warning(f"Unknown student submitted proof: {sender_phone}")
            # Could auto-create student here if needed
            return
        
        student_id = student_resp.data[0]["id"]
        
        # Find the IELTS course (for now, hardcoded to the active IELTS course)
        course_resp = db.table("courses").select("id").eq("name", "IELTS Preparation (Oct 15-30, 6-8pm GMT)").limit(1).execute()
        if not course_resp.data:
            logger.error("IELTS course not found")
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
            "method": "momo",  # default, could be parsed from message
            "reference": "ILETS",
            "proof_url": proof_url,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        if existing.data:
            # Update existing payment with new proof
            payment_id = existing.data[0]["id"]
            db.table("payments").update({
                "proof_url": proof_url,
                "status": "pending",  # reset to pending for re-verification
            }).eq("id", payment_id).execute()
            logger.info(f"Updated payment proof for student {student_id}: {payment_id}")
        else:
            # Create new payment record
            payment_resp = db.table("payments").insert(payment_data).execute()
            if payment_resp.data:
                payment_id = payment_resp.data[0]["id"]
                logger.info(f"Created payment record for student {student_id}: {payment_id}")
            else:
                logger.error("Failed to create payment record")
                return
        
        # Notify admin via approval system (create approval for verification)
        import uuid
        approval_id = str(uuid.uuid4())
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
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        
        logger.info(f"Created payment verification approval {approval_id} for student {student_id}")
        
        # Send confirmation to student in the group
        await send_confirmation_to_student(db, group_jid, sender_phone, payment_id)
        
    except Exception as e:
        logger.error(f"Error processing payment proof: {e}")


async def send_confirmation_to_student(db, group_jid: str, student_phone: str, payment_id: str):
    """Send confirmation message to student in the proof group."""
    from src.config import get_settings
    import httpx
    
    settings = get_settings()
    message = f"✅ Payment proof received! Your proof has been submitted (ID: {payment_id[:8]}...). Admin will verify shortly. You'll be added to the class group once verified."
    
    url = f"{settings.wasender_base_url}/api/send-message"
    headers = {
        "Authorization": f"Bearer {settings.wasender_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"to": group_jid, "text": message}
    
    try:
        r = httpx.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            logger.info(f"Confirmation sent to {student_phone} in proof group")
        else:
            logger.error(f"Failed to send confirmation: {r.text}")
    except Exception as e:
        logger.error(f"Error sending confirmation: {e}")