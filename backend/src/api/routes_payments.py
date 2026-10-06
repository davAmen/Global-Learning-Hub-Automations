"""GET /payments - list payments, POST /payments - create payment record."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from src.database import get_db

router = APIRouter()


class PaymentCreate(BaseModel):
    student_id: str
    course_id: str
    amount: float
    currency: str = "GHS"
    method: str  # momo | telecel | bank
    reference: str
    proof_url: str | None = None


@router.get("/payments")
def list_payments(course_id: str | None = None, status: str | None = None):
    db = get_db()
    query = db.table("payments").select("*, students(name, phone)").order("created_at", desc=True)
    if course_id:
        query = query.eq("course_id", course_id)
    if status:
        query = query.eq("status", status)
    resp = query.limit(100).execute()
    return {"payments": resp.data or []}


@router.post("/payments")
def create_payment(payment: PaymentCreate):
    db = get_db()
    
    data = payment.model_dump()
    data["status"] = "pending"
    data["created_at"] = datetime.utcnow().isoformat()
    
    resp = db.table("payments").insert(data).execute()
    if not resp.data:
        raise HTTPException(500, "Failed to create payment")
    
    return {"status": "ok", "payment": resp.data[0]}


@router.post("/payments/{payment_id}/verify")
def verify_payment(payment_id: str, verify: bool = True, admin_id: str = "00000000-0000-0000-0000-000000000000"):
    db = get_db()
    
    new_status = "verified" if verify else "rejected"
    resp = db.table("payments").update({
        "status": new_status,
        "verified_by": admin_id,
        "verified_at": datetime.utcnow().isoformat(),
    }).eq("id", payment_id).execute()
    
    if not resp.data:
        raise HTTPException(404, "Payment not found")
    
    payment = resp.data[0]
    
    # If verified, add student to class access group
    if verify:
        # Get course's class_access group
        group_resp = db.table("groups").select("whatsapp_jid").eq("course_id", payment["course_id"]).eq("type", "class_access").eq("is_active", True).limit(1).execute()
        if group_resp.data:
            group_jid = group_resp.data[0]["whatsapp_jid"]
            # Get student phone
            student_resp = db.table("students").select("phone").eq("id", payment["student_id"]).limit(1).execute()
            if student_resp.data:
                student_phone = student_resp.data[0]["phone"]
                
                # Add participant via WasenderAPI
                import httpx
                from src.config import get_settings
                settings = get_settings()
                url = f"{settings.wasender_base_url}/api/groups/{group_jid}/participants"
                headers = {"Authorization": f"Bearer {settings.wasender_api_key}", "Content-Type": "application/json"}
                payload = {"participants": [student_phone], "action": "add"}
                r = httpx.post(url, headers=headers, json=payload, timeout=15)
                
                # Audit log
                db.table("audit_log").insert({
                    "actor": "admin",
                    "action": "payment_verify_add_student",
                    "entity_type": "payment",
                    "entity_id": payment_id,
                    "details": {"verified": verify, "group_jid": group_jid, "added": r.status_code == 200},
                }).execute()
    
    return {"status": "ok", "payment": resp.data[0]}