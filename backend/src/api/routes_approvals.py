"""GET /approvals - list approvals, POST /approvals/{id}/review - review approval."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.database import get_db

router = APIRouter()


class ApprovalReview(BaseModel):
    status: str  # approved | rejected | modified
    review_notes: str | None = None
    modified_content: str | None = None


@router.get("/approvals")
def list_approvals(status: str | None = None):
    db = get_db()
    query = db.table("approvals").select("*").order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    resp = query.limit(50).execute()
    return {"approvals": resp.data or []}


@router.post("/approvals/{approval_id}/review")
def review_approval(approval_id: str, review: ApprovalReview):
    db = get_db()
    
    # Get the approval
    approval_resp = db.table("approvals").select("*").eq("id", approval_id).limit(1).execute()
    if not approval_resp.data:
        raise HTTPException(404, "Approval not found")
    
    approval = approval_resp.data[0]
    
    # Update approval
    update_data = {
        "status": review.status,
        "review_notes": review.review_notes,
        "reviewed_at": "now()",
    }
    if review.modified_content:
        update_data["content"] = review.modified_content
    
    db.table("approvals").update(update_data).eq("id", approval_id).execute()
    
    # If approved and it's a send_message action, send it
    if review.status == "approved" and approval["action_type"] == "send_message":
        from src.channels.base import get_channel
        from src.config import get_settings
        from src.database.models import Student
        from datetime import date
        
        settings = get_settings()
        channel = get_channel("whatsapp")
        
        admin = Student(
            id="00000000-0000-0000-0000-000000000000",
            name="Administrator",
            phone=settings.admin_phone,
            email=settings.admin_email,
            created_at=date.today().isoformat(),
        )
        
        content = review.modified_content or approval["content"]
        target_jid = approval["target_group_jid"]
        
        # Send to group via WasenderAPI
        import httpx
        url = f"{settings.wasender_base_url}/api/send-message"
        headers = {
            "Authorization": f"Bearer {settings.wasender_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"to": target_jid, "text": content}
        r = httpx.post(url, headers=headers, json=payload, timeout=15)
        
        # Log the send
        db.table("reminder_log").insert({
            "enrollment_id": "00000000-0000-0000-0000-000000000000",
            "channel": "whatsapp",
            "message": content,
            "delivery_status": "sent" if r.status_code == 200 else "failed",
            "external_message_id": str(r.json().get("data", {}).get("msgId")) if r.status_code == 200 else None,
        }).execute()
        
        # Audit log
        db.table("audit_log").insert({
            "actor": "admin",
            "action": "approval_send",
            "entity_type": "approval",
            "entity_id": approval_id,
            "details": {"status": review.status, "target_jid": target_jid},
        }).execute()
    
    return {"status": "ok", "approval_id": approval_id}