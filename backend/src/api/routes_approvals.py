"""GET /approvals - list approvals, POST /approvals/{id}/review - review approval."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, Field, validator
from src.database import get_db

router = APIRouter()


class ApprovalReview(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected|modified)$")
    review_notes: Optional[str] = None
    modified_content: Optional[str] = None


class ApprovalListParams(BaseModel):
    status: Optional[str] = Query(None, pattern="^(pending|approved|rejected|modified|cancelled)$")
    action_type: Optional[str] = Query(None)
    limit: int = Query(50, le=100)
    offset: int = Query(0, ge=0)


async def verify_admin_auth(
    authorization: Optional[str] = Header(None),
    x_admin_id: Optional[str] = Header(None, alias="X-Admin-ID"),
):
    """Verify admin authentication."""
    if not authorization and not x_admin_id:
        raise HTTPException(401, "Admin authentication required")
    
    # In production, validate JWT or API key
    # For now, accept X-Admin-ID header
    if x_admin_id:
        return x_admin_id
    
    # Could validate Bearer token here
    return "admin"


@router.get("/approvals")
def list_approvals(
    params: ApprovalListParams = Depends(),
    admin_id: str = Depends(verify_admin_auth),
):
    db = get_db()
    query = db.table("approvals").select("*").order("created_at", desc=True)
    
    if params.status:
        query = query.eq("status", params.status)
    if params.action_type:
        query = query.eq("action_type", params.action_type)
    
    query = query.range(params.offset, params.offset + params.limit - 1)
    resp = query.execute()
    return {"approvals": resp.data or [], "total": len(resp.data or [])}


@router.get("/approvals/{approval_id}")
def get_approval(
    approval_id: UUID,
    admin_id: str = Depends(verify_admin_auth),
):
    db = get_db()
    resp = db.table("approvals").select("*").eq("id", str(approval_id)).limit(1).execute()
    if not resp.data:
        raise HTTPException(404, "Approval not found")
    return resp.data[0]


@router.post("/approvals/{approval_id}/review")
def review_approval(
    approval_id: UUID,
    review: ApprovalReview,
    admin_id: str = Depends(verify_admin_auth),
):
    db = get_db()
    
    # Get the approval
    approval_resp = db.table("approvals").select("*").eq("id", str(approval_id)).limit(1).execute()
    if not approval_resp.data:
        raise HTTPException(404, "Approval not found")
    
    approval = approval_resp.data[0]
    
    # Validate status transition
    valid_transitions = {
        "pending": ["approved", "rejected", "modified", "cancelled"],
        "modified": ["approved", "rejected", "cancelled"],
    }
    current_status = approval["status"]
    new_status = review.status
    
    if current_status not in valid_transitions or new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(400, f"Invalid status transition from {current_status} to {new_status}")
    
    # Update approval
    update_data = {
        "status": new_status,
        "review_notes": review.review_notes,
        "reviewed_by": admin_id,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if review.modified_content:
        update_data["content"] = review.modified_content
    
    db.table("approvals").update(update_data).eq("id", str(approval_id)).execute()
    
    # If approved and it's a send_message action, send it
    if new_status == "approved" and approval["action_type"] == "send_message":
        return _send_approved_message(approval, review.modified_content, admin_id)
    
    elif new_status == "approved" and approval["action_type"] == "verify_payment":
        return _verify_approved_payment(approval, admin_id)
    
    # Audit log
    db.table("audit_log").insert({
        "actor": "admin",
        "action": "approval_review",
        "entity_type": "approval",
        "entity_id": str(approval_id),
        "details": {"status": new_status, "admin_id": admin_id},
    }).execute()
    
    return {"status": "ok", "approval_id": str(approval_id)}


def _send_approved_message(approval: dict, modified_content: Optional[str], admin_id: str):
    """Send approved message to target group."""
    import asyncio
    import httpx
    from src.config import get_settings
    from src.channels.base import get_channel
    
    settings = get_settings()
    channel = get_channel("whatsapp")
    
    content = modified_content or approval["content"]
    target_jid = approval["target_group_jid"]
    
    # Send to group via WasenderAPI
    ok, msg_id = asyncio.run(channel.send(recipient=target_jid, message=content))
    
    db = get_db()
    
    # Log the send
    db.table("reminder_log").insert({
        "course_id": approval.get("target_course_id"),
        "channel": "whatsapp",
        "message": content,
        "delivery_status": "sent" if ok else "failed",
        "external_message_id": msg_id,
    }).execute()
    
    # Audit log
    db.table("audit_log").insert({
        "actor": "admin",
        "action": "approval_send",
        "entity_type": "approval",
        "entity_id": approval["id"],
        "details": {"status": "approved", "target_jid": target_jid, "admin_id": admin_id},
    }).execute()
    
    return {"status": "ok", "approval_id": approval["id"], "sent": ok, "message_id": msg_id}


def _verify_approved_payment(approval: dict, admin_id: str):
    """Handle approved payment verification."""
    import httpx
    from src.config import get_settings
    
    db = get_db()
    metadata = approval.get("metadata", {})
    payment_id = metadata.get("payment_id")
    
    if not payment_id:
        raise HTTPException(400, "Payment ID missing from approval metadata")
    
    # Update payment status
    resp = db.table("payments").update({
        "status": "verified",
        "verified_by": admin_id,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", payment_id).execute()
    
    if not resp.data:
        raise HTTPException(404, "Payment not found")
    
    payment = resp.data[0]
    
    # Add student to class access group
    group_resp = db.table("groups").select("whatsapp_jid").eq("course_id", payment["course_id"]).eq("type", "class_access").eq("is_active", True).limit(1).execute()
    if group_resp.data:
        group_jid = group_resp.data[0]["whatsapp_jid"]
        student_resp = db.table("students").select("phone").eq("id", payment["student_id"]).limit(1).execute()
        if student_resp.data:
            student_phone = student_resp.data[0]["phone"]
            
            # Add participant via WasenderAPI
            settings = get_settings()
            url = f"{settings.wasender_base_url}/api/groups/{group_jid}/participants/add"
            headers = {"Authorization": f"Bearer {settings.wasender_api_key}", "Content-Type": "application/json"}
            payload = {"participants": [student_phone]}
            r = httpx.post(url, headers=headers, json=payload, timeout=15)
            
            # Audit log
            db.table("audit_log").insert({
                "actor": "admin",
                "action": "payment_verify_add_student",
                "entity_type": "payment",
                "entity_id": payment_id,
                "details": {"verified": True, "group_jid": group_jid, "added": r.status_code == 200},
            }).execute()
    
    # Audit log
    db.table("audit_log").insert({
        "actor": "admin",
        "action": "payment_verify",
        "entity_type": "payment",
        "entity_id": payment_id,
        "details": {"verified": True, "admin_id": admin_id},
    }).execute()
    
    return {"status": "ok", "payment_id": payment_id, "verified": True}