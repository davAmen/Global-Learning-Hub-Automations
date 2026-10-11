"""GET /payments - list payments, POST /payments - create payment record."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel, Field, validator
from src.database import get_db
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class PaymentCreate(BaseModel):
    student_id: UUID
    course_id: UUID
    amount: float = Field(gt=0)
    currency: str = Field(default="GHS", pattern="^(GHS|USD|EUR)$")
    method: str = Field(pattern="^(momo|telecel|bank|card|cash)$")
    reference: str
    proof_url: Optional[str] = None


class PaymentVerify(BaseModel):
    verify: bool = True
    admin_id: str
    rejection_reason: Optional[str] = None


class PaymentListParams(BaseModel):
    course_id: Optional[UUID] = None
    status: Optional[str] = Query(None, pattern="^(pending|verified|rejected|refunded)$")
    student_id: Optional[UUID] = None
    limit: int = Query(100, le=500)
    offset: int = Query(0, ge=0)


async def verify_admin_auth(
    authorization: Optional[str] = Header(None),
    x_admin_id: Optional[str] = Header(None, alias="X-Admin-ID"),
):
    """Verify admin authentication."""
    if not authorization and not x_admin_id:
        raise HTTPException(401, "Admin authentication required")
    return x_admin_id or "admin"


@router.get("/payments")
def list_payments(
    params: PaymentListParams = Depends(),
    admin_id: str = Depends(verify_admin_auth),
):
    db = get_db()
    query = db.table("payments").select("*, students(name, phone)").order("created_at", desc=True)
    
    if params.course_id:
        query = query.eq("course_id", str(params.course_id))
    if params.status:
        query = query.eq("status", params.status)
    if params.student_id:
        query = query.eq("student_id", str(params.student_id))
    
    query = query.range(params.offset, params.offset + params.limit - 1)
    resp = query.execute()
    return {"payments": resp.data or [], "total": len(resp.data or [])}


@router.get("/payments/{payment_id}")
def get_payment(
    payment_id: UUID,
    admin_id: str = Depends(verify_admin_auth),
):
    db = get_db()
    resp = db.table("payments").select("*, students(name, phone)").eq("id", str(payment_id)).limit(1).execute()
    if not resp.data:
        raise HTTPException(404, "Payment not found")
    return resp.data[0]


@router.post("/payments")
def create_payment(
    payment: PaymentCreate,
    admin_id: str = Depends(verify_admin_auth),
):
    db = get_db()
    
    data = payment.model_dump()
    data["status"] = "pending"
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Convert UUIDs to strings for Supabase
    data["student_id"] = str(data["student_id"])
    data["course_id"] = str(data["course_id"])
    
    resp = db.table("payments").insert(data).execute()
    if not resp.data:
        raise HTTPException(500, "Failed to create payment")
    
    return {"status": "ok", "payment": resp.data[0]}


@router.post("/payments/{payment_id}/verify")
def verify_payment(
    payment_id: UUID,
    verification: PaymentVerify,
    admin_id: str = Depends(verify_admin_auth),
):
    db = get_db()
    
    # Get payment
    payment_resp = db.table("payments").select("*").eq("id", str(payment_id)).limit(1).execute()
    if not payment_resp.data:
        raise HTTPException(404, "Payment not found")
    
    payment = payment_resp.data[0]
    
    # Check if already verified/rejected
    if payment["status"] in ("verified", "rejected"):
        raise HTTPException(400, f"Payment already {payment['status']}")
    
    new_status = "verified" if verification.verify else "rejected"
    update_data = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    if verification.verify:
        update_data["verified_by"] = verification.admin_id
        update_data["verified_at"] = datetime.now(timezone.utc).isoformat()
    else:
        update_data["rejected_by"] = verification.admin_id
        update_data["rejected_at"] = datetime.now(timezone.utc).isoformat()
        update_data["rejection_reason"] = verification.rejection_reason
    
    resp = db.table("payments").update(update_data).eq("id", str(payment_id)).execute()
    if not resp.data:
        raise HTTPException(500, "Failed to update payment")
    
    payment = resp.data[0]
    
    # If verified, add student to class access group
    if verification.verify:
        _add_student_to_class_group(payment)
    
    # Audit log
    db = get_db()
    db.table("audit_log").insert({
        "actor": "admin",
        "action": "payment_verify",
        "entity_type": "payment",
        "entity_id": str(payment_id),
        "details": {"verified": verification.verify, "admin_id": verification.admin_id},
    }).execute()
    
    return {"status": "ok", "payment": payment}


def _add_student_to_class_group(payment: dict):
    """Add verified student to class access group."""
    import httpx
    from src.config import get_settings
    from src.database import get_db
    
    db = get_db()
    
    # Get class_access group (shared across courses, find by type)
    group_resp = db.table("groups").select("whatsapp_jid").eq("type", "class_access").eq("is_active", True).limit(1).execute()
    if not group_resp.data:
        logger.warning("No class_access group found")
        return
    
    group_jid = group_resp.data[0]["whatsapp_jid"]
    
    # Get student phone
    student_resp = db.table("students").select("phone").eq("id", payment["student_id"]).limit(1).execute()
    if not student_resp.data:
        return
    
    student_phone = student_resp.data[0]["phone"]
    
    # Add participant via WasenderAPI - correct endpoint
    settings = get_settings()
    url = f"{settings.wasender_base_url}/api/groups/{group_jid}/participants/add"
    headers = {"Authorization": f"Bearer {settings.wasender_api_key}", "Content-Type": "application/json"}
    payload = {"participants": [student_phone]}
    
    try:
        r = httpx.post(url, headers=headers, json=payload, timeout=15)
        success = r.status_code == 200
    except Exception as e:
        logger.error(f"Failed to add student to group: {e}")
        success = False
    
    # Audit log
    db = get_db()
    db.table("audit_log").insert({
        "actor": "admin",
        "action": "payment_verify_add_student",
        "entity_type": "payment",
        "entity_id": payment["id"],
        "details": {"verified": True, "group_jid": group_jid, "added": success},
    }).execute()