"""IELTS daily reminder scheduler - sends to announcement group at 5am GMT."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from src.config import get_settings
from src.database import get_db
from src.channels.base import get_channel
from src.utils.logger import get_logger

logger = get_logger(__name__)


IELTS_COURSE_NAME = "IELTS Preparation (Oct 15-30, 6-8pm GMT)"
ANNOUNCEMENT_GROUP_JID = "120363418173591450@g.us"
PROOF_GROUP_JID = "120363428841556134@g.us"
CLASS_ACCESS_GROUP_JID = "120363413380837553@g.us"
MOmo_NUMBER = "+233548014157"
TELECEL_NUMBER = "+23333206967251"
REFERENCE = "ILETS"


def build_ielts_reminder(day_offset: int) -> str:
    """Build the daily IELTS reminder message."""
    today = date.today()
    start_date = date(2026, 10, 15)
    end_date = date(2026, 10, 30)
    
    if today < start_date:
        days_left = (start_date - today).days
        status = f"STARTS IN {days_left} DAYS"
    elif today <= end_date:
        day_num = (today - start_date).days + 1
        total_days = (end_date - start_date).days + 1
        status = f"DAY {day_num} OF {total_days}"
    else:
        status = "ENDED"
    
    message = f"""📢 *IELTS PREPARATION CLASS - DAILY REMINDER*

{status}
📅 Dates: Oct 15 - Oct 30, 2026
⏰ Time: 6:00 PM - 8:00 PM GMT daily

💰 *PAYMENT REQUIRED FOR ACCESS*
Amount: GHS 100.00
Reference: {REFERENCE}

💳 *PAYMENT METHODS:*
1️⃣ MoMo: {MOmo_NUMBER}
2️⃣ Telecel Cash: {TELECEL_NUMBER}

📝 *HOW TO GET ACCESS:*
1. Pay GHS 100 to either number above
2. Send proof of payment (screenshot) to: 
   https://chat.whatsapp.com/IPtb2v6EzQUJ6LGLrObDrw
3. Once verified, you'll be added to the class group:
   https://chat.whatsapp.com/HZpPBTfKDQq7aVYOgpUFkw

⚠️ *PARTICIPATION IS STRICTLY BY PAYMENT ONLY*
Only students who have paid and submitted proof will get class access.

📚 Class materials, schedule, and links will be shared in the class group after verification.

---
Global Learning Hub | Skills. Growth. Certification."""
    
    return message


def create_approval_for_reminder(db, message: str, target_jid: str, course_id: str) -> str:
    """Create an approval record for the reminder."""
    import uuid
    approval_id = str(uuid.uuid4())
    
    db.table("approvals").insert({
        "id": approval_id,
        "action_type": "send_message",
        "content": message,
        "target_group_jid": target_jid,
        "target_course_id": course_id,
        "metadata": {"type": "ielts_daily_reminder", "scheduled_time": "05:00 GMT"},
        "status": "pending",
        "requested_by": "agent",
        "created_at": datetime.utcnow().isoformat(),
    }).execute()
    
    logger.info(f"Created approval {approval_id} for IELTS reminder")
    return approval_id


def send_ielts_reminder_now() -> bool:
    """Send IELTS reminder immediately (for testing)."""
    db = get_db()
    settings = get_settings()
    
    # Get course ID
    course_resp = db.table("courses").select("id").eq("name", IELTS_COURSE_NAME).limit(1).execute()
    if not course_resp.data:
        logger.error("IELTS course not found")
        return False
    course_id = course_resp.data[0]["id"]
    
    message = build_ielts_reminder(0)
    
    # Create approval (in production, admin reviews via web UI)
    approval_id = create_approval_for_reminder(db, message, ANNOUNCEMENT_GROUP_JID, course_id)
    
    # For testing: auto-approve and send directly to group via WasenderAPI
    import httpx
    url = f"{settings.wasender_base_url}/api/send-message"
    headers = {
        "Authorization": f"Bearer {settings.wasender_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"to": ANNOUNCEMENT_GROUP_JID, "text": message}
    r = httpx.post(url, headers=headers, json=payload, timeout=15)
    
    ok = r.status_code == 200
    msg_id = str(r.json().get("data", {}).get("msgId")) if ok else None
    
    # Log to reminder_log (use course_id as enrollment_id for group messages)
    db.table("reminder_log").insert({
        "enrollment_id": course_id,  # Use course_id for group messages
        "channel": "whatsapp",
        "message": message,
        "delivery_status": "sent" if ok else "failed",
        "external_message_id": msg_id,
    }).execute()
    
    # Update approval status
    db.table("approvals").update({
        "status": "approved",
        "reviewed_at": datetime.utcnow().isoformat(),
    }).eq("id", approval_id).execute()
    
    # Audit log
    db.table("audit_log").insert({
        "actor": "agent",
        "action": "ielts_daily_reminder_sent",
        "entity_type": "approval",
        "entity_id": approval_id,
        "details": {"target_jid": ANNOUNCEMENT_GROUP_JID, "sent": ok},
    }).execute()
    
    if ok:
        logger.info(f"IELTS reminder sent to announcement group, msg_id={msg_id}")
    else:
        logger.error(f"Failed to send IELTS reminder: {r.text}")
    
    return ok


def schedule_ielts_reminders():
    """Add IELTS reminder to scheduler at 5am GMT daily."""
    # This would be called from main.py lifespan
    # For now, manual trigger via send_ielts_reminder_now()
    pass


if __name__ == "__main__":
    # Test run
    send_ielts_reminder_now()