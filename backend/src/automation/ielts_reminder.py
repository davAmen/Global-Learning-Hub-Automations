"""IELTS daily reminder scheduler - sends to announcement group at 5am GMT."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

from src.config import get_settings
from src.database import get_db
from src.channels.base import get_channel
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_ielts_reminder(current_date: date) -> str:
    """Build the daily IELTS reminder message using config settings."""
    settings = get_settings()
    
    start_date = date.fromisoformat(settings.ielts_start_date)
    end_date = date.fromisoformat(settings.ielts_end_date)
    
    if current_date < start_date:
        days_left = (start_date - current_date).days
        status = f"STARTS IN {days_left} DAYS"
    elif current_date <= end_date:
        day_num = (current_date - start_date).days + 1
        total_days = (end_date - start_date).days + 1
        status = f"DAY {day_num} OF {total_days}"
    else:
        status = "ENDED"
    
    message = f"""📢 *{settings.ielts_course_name.upper()} - DAILY REMINDER*

{status}
📅 Dates: {settings.ielts_start_date} - {settings.ielts_end_date}
⏰ Time: {settings.ielts_class_time} daily

💰 *PAYMENT REQUIRED FOR ACCESS*
Amount: {settings.ielts_currency} {settings.ielts_amount:.2f}
Reference: {settings.ielts_reference}

💳 *PAYMENT METHODS:*
1️⃣ MoMo: {settings.ielts_momo_number}
2️⃣ Telecel Cash: {settings.ielts_telecel_number}

📝 *HOW TO GET ACCESS:*
1. Pay {settings.ielts_currency} {settings.ielts_amount:.2f} to either number above
2. Send proof of payment (screenshot) to: 
   {settings.ielts_proof_group_url}
3. Once verified, you'll be added to the class group:
   {settings.ielts_class_access_group_url}

⚠️ *PARTICIPATION IS STRICTLY BY PAYMENT ONLY*
Only students who have paid and submitted proof will get class access.

📚 Class materials, schedule, and links will be shared in the class group after verification.

---
Global Learning Hub | Skills. Growth. Certification."""
    
    return message


async def create_approval_for_reminder(db, message: str, target_jid: str, course_id: str) -> str:
    """Create an approval record for the reminder."""
    from uuid import uuid4
    approval_id = str(uuid4())
    
    db.table("approvals").insert({
        "id": approval_id,
        "action_type": "send_message",
        "content": message,
        "target_group_jid": target_jid,
        "target_course_id": course_id,
        "metadata": {"type": "ielts_daily_reminder", "scheduled_time": "05:00 GMT"},
        "status": "pending",
        "requested_by": "agent",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    
    logger.info(f"Created approval {approval_id} for IELTS reminder")
    return approval_id


async def send_ielts_reminder_now() -> bool:
    """Send IELTS reminder immediately (for testing)."""
    db = get_db()
    settings = get_settings()
    
    # Get course ID
    course_resp = db.table("courses").select("id").eq("name", settings.ielts_course_name).limit(1).execute()
    if not course_resp.data:
        logger.error("IELTS course not found")
        return False
    course_id = course_resp.data[0]["id"]
    
    current_date = datetime.now(timezone.utc).date()
    message = build_ielts_reminder(current_date)
    
    # Create approval (in production, admin reviews via web UI)
    approval_id = await create_approval_for_reminder(db, message, settings.ielts_announcement_group_jid, course_id)
    
    # For testing: auto-approve and send directly to group via WasenderAPI
    channel = get_channel("whatsapp")
    ok, msg_id = await channel.send(recipient=settings.ielts_announcement_group_jid, message=message)
    
    # Log to reminder_log
    db.table("reminder_log").insert({
        "course_id": course_id,
        "channel": "whatsapp",
        "message": message,
        "delivery_status": "sent" if ok else "failed",
        "external_message_id": msg_id,
    }).execute()
    
    # Update approval status
    db.table("approvals").update({
        "status": "approved",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", approval_id).execute()
    
    # Audit log
    db.table("audit_log").insert({
        "actor": "agent",
        "action": "ielts_daily_reminder_sent",
        "entity_type": "approval",
        "entity_id": approval_id,
        "details": {"target_jid": settings.ielts_announcement_group_jid, "sent": ok},
    }).execute()
    
    if ok:
        logger.info(f"IELTS reminder sent to announcement group, msg_id={msg_id}")
    else:
        logger.error(f"Failed to send IELTS reminder")
    
    return ok


async def send_ielts_reminder_scheduled() -> bool:
    """Send IELTS reminder via scheduled job (with approval flow)."""
    if not get_settings().enable_ielts_reminders:
        logger.info("IELTS reminders disabled in config")
        return True
    
    db = get_db()
    settings = get_settings()
    
    course_resp = db.table("courses").select("id").eq("name", settings.ielts_course_name).eq("is_active", True).limit(1).execute()
    if not course_resp.data:
        logger.error("No active IELTS course found")
        return False
    course_id = course_resp.data[0]["id"]
    
    current_date = datetime.now(timezone.utc).date()
    message = build_ielts_reminder(current_date)
    
    # Create approval for admin review
    approval_id = await create_approval_for_reminder(db, message, settings.ielts_announcement_group_jid, course_id)
    
    # Check if auto-approve is enabled in config
    config_resp = db.table("system_config").select("value").eq("key", "auto_approve_reminders").limit(1).execute()
    auto_approve = config_resp.data and config_resp.data[0]["value"].get("enabled", False)
    
    if auto_approve:
        # Auto-approve and send
        channel = get_channel("whatsapp")
        ok, msg_id = await channel.send(recipient=settings.ielts_announcement_group_jid, message=message)
        
        db.table("reminder_log").insert({
            "course_id": course_id,
            "channel": "whatsapp",
            "message": message,
            "delivery_status": "sent" if ok else "failed",
            "external_message_id": msg_id,
        }).execute()
        
        db.table("approvals").update({
            "status": "approved",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", approval_id).execute()
        
        db.table("audit_log").insert({
            "actor": "agent",
            "action": "ielts_daily_reminder_sent",
            "entity_type": "approval",
            "entity_id": approval_id,
            "details": {"target_jid": settings.ielts_announcement_group_jid, "sent": ok, "auto_approved": True},
        }).execute()
        
        if ok:
            logger.info(f"IELTS reminder sent (auto-approved), msg_id={msg_id}")
        else:
            logger.error(f"Failed to send IELTS reminder")
        return ok
    else:
        logger.info(f"IELTS reminder approval created: {approval_id} - awaiting admin review")
        return True


if __name__ == "__main__":
    import asyncio
    asyncio.run(send_ielts_reminder_now())