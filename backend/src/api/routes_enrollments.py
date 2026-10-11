"""Enrollment API routes - seat reservation, payment, and enrollment management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, status, Body
from pydantic import BaseModel, EmailStr, Field

from src.auth.utils import get_current_user, get_current_user_optional, require_role
from src.database import get_db
from src.payments import payment_registry, PaymentInitRequest
from src.config import get_settings
from src.utils.logger import get_logger

router = APIRouter(prefix="/enrollments", tags=["enrollments"])
logger = get_logger(__name__)


# Request/Response Models
class SeatReservationRequest(BaseModel):
    course_id: UUID
    payment_provider: str = Field(default="mock", pattern="^(paystack|seefcash|stripe|mock)$")


class SeatReservationResponse(BaseModel):
    payment_id: str
    provider_payment_id: str
    authorization_url: str
    amount_minor: int
    currency: str
    reference: str
    expires_at: str


class EnrollmentResponse(BaseModel):
    id: str
    student_id: str
    course_id: str
    status: str
    enrolled_at: str
    payment_id: Optional[str] = None
    seat_reserved: bool = False
    seat_reservation_verified_at: Optional[str] = None


class CourseEnrollmentSummary(BaseModel):
    course: dict
    enrollment: Optional[dict] = None
    can_enroll: bool
    seats_available: Optional[int] = None


# Helper Functions
async def _get_course(course_id: str) -> dict:
    """Get course by ID with validation."""
    db = get_db()
    result = db.table("courses").select("*").eq("id", course_id).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "Course not found")
    course = result.data[0]
    if not course.get("is_active"):
        raise HTTPException(400, "Course is not active")
    return course


async def _check_capacity(course: dict) -> bool:
    """Check if course has available capacity."""
    capacity = course.get("capacity")
    if capacity is None:
        return True  # Unlimited
    db = get_db()
    result = db.table("enrollments").select("id", count="exact").eq("course_id", course["id"]).eq("status", "active").execute()
    return result.count < capacity


async def _create_seat_reservation_payment(
    student_id: str,
    course: dict,
    provider_name: str,
) -> tuple[str, PaymentInitRequest]:
    """Create a seat reservation payment record and init request."""
    db = get_db()
    settings = get_settings()
    
    # Generate unique reference
    import secrets
    reference = f"SEAT-{course['id'][:8]}-{student_id[:8]}-{secrets.token_hex(4)}".upper()
    
    # Seat reservation amount (in minor units)
    seat_amount = course.get("seat_reservation_minor", 1500)  # Default GHS 15 (~$1)
    currency = course.get("currency", "GHS")
    
    # Create payment record
    payment_data = {
        "student_id": student_id,
        "course_id": course["id"],
        "amount": seat_amount / 100,  # Convert to major units for decimal storage
        "currency": currency,
        "method": "card",  # Will be updated by provider
        "reference": reference,
        "status": "pending",
        "provider": provider_name,
        "seat_reservation": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    result = db.table("payments").insert(payment_data).execute()
    if not result.data:
        raise HTTPException(500, "Failed to create seat reservation payment")
    
    payment = result.data[0]
    payment_id = payment["id"]
    
    # Create payment init request
    # Get student info for payment
    student_result = db.table("students").select("email, name, phone").eq("id", student_id).limit(1).execute()
    if not student_result.data:
        raise HTTPException(404, "Student not found")
    
    student = student_result.data[0]
    
    init_request = PaymentInitRequest(
        amount_minor=seat_amount,
        currency=currency,
        reference=reference,
        customer_email=student["email"],
        customer_name=student.get("name"),
        customer_phone=student.get("phone"),
        metadata={
            "course_id": course["id"],
            "course_name": course["name"],
            "payment_type": "seat_reservation",
            "payment_id": payment_id,
        },
        callback_url=f"{settings.app_base_url}/payment/callback?reference={reference}",
        cancel_url=f"{settings.app_base_url}/courses/{course['id']}?cancelled=true",
    )
    
    return payment_id, init_request


# Enrollment Routes
@router.post("/reserve-seat", response_model=SeatReservationResponse, status_code=status.HTTP_201_CREATED)
async def reserve_seat(
    request: SeatReservationRequest,
    user: dict = Depends(get_current_user),
):
    """Reserve a seat in a course (step 1: $1 seat reservation)."""
    student_id = user["sub"]
    
    # Get course
    course = await _get_course(str(request.course_id))
    
    # Check if already enrolled
    db = get_db()
    existing = db.table("enrollments").select("id").eq("student_id", student_id).eq("course_id", str(request.course_id)).limit(1).execute()
    if existing.data:
        raise HTTPException(409, "Already enrolled in this course")
    
    # Check capacity
    if not await _check_capacity(course):
        raise HTTPException(400, "Course is full")
    
    # Check for existing pending seat reservation
    existing_payment = db.table("payments").select("id, status, provider_payment_id").eq("student_id", student_id).eq("course_id", str(request.course_id)).eq("seat_reservation", True).eq("status", "pending").limit(1).execute()
    if existing_payment.data:
        # Return existing reservation
        payment = existing_payment.data[0]
        provider = payment_registry.get(request.payment_provider)
        init_req = PaymentInitRequest(
            amount_minor=course.get("seat_reservation_minor", 1500),
            currency=course.get("currency", "GHS"),
            reference=f"SEAT-{course['id'][:8]}-{student_id[:8]}",  # We don't have the exact reference here
            customer_email=user.get("email", ""),
        )
        # This is a simplified response for existing reservation
        return SeatReservationResponse(
            payment_id=payment["id"],
            provider_payment_id=payment.get("provider_payment_id") or "",
            authorization_url=f"{get_settings().app_base_url}/payment/pending",
            amount_minor=course.get("seat_reservation_minor", 1500),
            currency=course.get("currency", "GHS"),
            reference="",  # Would need to fetch from payment
            expires_at=datetime.now(timezone.utc).isoformat(),
        )
    
    # Create new seat reservation
    provider = payment_registry.get(request.payment_provider)
    payment_id, init_request = await _create_seat_reservation_payment(student_id, course, request.payment_provider)
    
    # Initialize payment with provider
    init_response = await provider.initialize_payment(init_request)
    
    # Update payment with provider response
    db.table("payments").update({
        "provider_payment_id": init_response.provider_payment_id,
        "provider_reference": init_response.reference,
    }).eq("id", payment_id).execute()
    
    # Set expiry (15 minutes)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    logger.info(f"Seat reserved for student {student_id} in course {course['id']} via {request.payment_provider}")
    
    return SeatReservationResponse(
        payment_id=payment_id,
        provider_payment_id=init_response.provider_payment_id,
        authorization_url=init_response.authorization_url,
        amount_minor=init_request.amount_minor,
        currency=init_request.currency,
        reference=init_response.reference,
        expires_at=expires_at.isoformat(),
    )


@router.post("/confirm-seat-reservation", response_model=EnrollmentResponse)
async def confirm_seat_reservation(
    payment_id: str,
    user: dict = Depends(get_current_user),
):
    """Confirm seat reservation after payment callback."""
    student_id = user["sub"]
    db = get_db()
    
    # Get payment
    payment_result = db.table("payments").select("*").eq("id", payment_id).eq("student_id", student_id).limit(1).execute()
    if not payment_result.data:
        raise HTTPException(404, "Payment not found")
    
    payment = payment_result.data[0]
    
    if payment["status"] == "verified" and payment.get("seat_reservation_verified_at"):
        # Already verified
        pass
    
    # Verify payment with provider
    provider = payment_registry.get(payment["provider"])
    verification = await provider.verify_payment(payment["reference"])
    
    if not verification.is_verified:
        raise HTTPException(400, "Seat reservation payment not verified")
    
    # Update payment
    db.table("payments").update({
        "status": "verified",
        "seat_reservation_verified_at": datetime.now(timezone.utc).isoformat(),
        "provider_fees_minor": verification.provider_fees_minor,
        "provider_response": verification.raw_response,
    }).eq("id", payment_id).execute()
    
    logger.info(f"Seat reservation confirmed for student {student_id}, payment {payment_id}")
    
    return EnrollmentResponse(
        id="",
        student_id=student_id,
        course_id=payment["course_id"],
        status="seat_reserved",
        enrolled_at=datetime.now(timezone.utc).isoformat(),
        payment_id=payment_id,
        seat_reserved=True,
        seat_reservation_verified_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/enroll", response_model=EnrollmentResponse)
async def enroll_in_course(
    course_id: str,
    payment_provider: str = "mock",
    user: dict = Depends(get_current_user),
):
    """Full enrollment flow: seat reservation + tuition payment."""
    student_id = user["sub"]
    
    # Get course
    course = await _get_course(course_id)
    
    # Check if already enrolled
    db = get_db()
    existing = db.table("enrollments").select("id, status").eq("student_id", student_id).eq("course_id", course_id).limit(1).execute()
    if existing.data:
        enrollment = existing.data[0]
        if enrollment["status"] == "active":
            raise HTTPException(409, "Already enrolled in this course")
        # Could reactivate if dropped/inactive
    
    # Check capacity
    if not await _check_capacity(course):
        raise HTTPException(400, "Course is full")
    
    # Step 1: Reserve seat
    provider = payment_registry.get(payment_provider)
    payment_id, init_request = await _create_seat_reservation_payment(student_id, course, payment_provider)
    init_response = await provider.initialize_payment(init_request)
    
    # Update payment with provider response
    db.table("payments").update({
        "provider_payment_id": init_response.provider_payment_id,
        "provider_reference": init_response.reference,
    }).eq("id", payment_id).execute()
    
    # For mock/sandbox: auto-verify seat reservation
    if payment_provider == "mock":
        from src.payments.mock import MockPaymentProvider
        mock_provider = payment_registry.get("mock")
        mock_provider.set_payment_status(init_response.reference, "success")
        
        verification = await provider.verify_payment(init_response.reference)
        if verification.is_verified:
            db.table("payments").update({
                "status": "verified",
                "seat_reservation_verified_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", payment_id).execute()
    
    # Return enrollment info with payment URL
    return EnrollmentResponse(
        id="",  # Will be created after tuition payment
        student_id=student_id,
        course_id=course_id,
        status="seat_reserved" if payment_provider == "mock" else "pending_seat_payment",
        enrolled_at=datetime.now(timezone.utc).isoformat(),
        payment_id=payment_id,
        seat_reserved=payment_provider == "mock",
        seat_reservation_verified_at=datetime.now(timezone.utc).isoformat() if payment_provider == "mock" else None,
    )


@router.get("/my-enrollments", response_model=list[EnrollmentResponse])
async def get_my_enrollments(user: dict = Depends(get_current_user)):
    """Get current user's enrollments."""
    student_id = user["sub"]
    db = get_db()
    
    result = db.table("enrollments").select("*, payments(*)").eq("student_id", student_id).execute()
    
    enrollments = []
    for enr in result.data or []:
        payment = enr.get("payments") if enr.get("payments") else None
        payment_id = payment[0]["id"] if payment else None
        enrollments.append(EnrollmentResponse(
            id=enr["id"],
            student_id=enr["student_id"],
            course_id=enr["course_id"],
            status=enr["status"],
            enrolled_at=enr["enrolled_at"],
            payment_id=payment_id,
            seat_reserved=enr.get("status") in ["seat_reserved", "active"],
        ))
    
    return enrollments


@router.get("/course/{course_id}/status", response_model=CourseEnrollmentSummary)
async def get_enrollment_status(
    course_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """Get enrollment status for a course (public or authenticated)."""
    course = await _get_course(course_id)
    
    # Check capacity
    seats_available = None
    capacity = course.get("capacity")
    if capacity is not None:
        db = get_db()
        result = db.table("enrollments").select("id", count="exact").eq("course_id", course_id).eq("status", "active").execute()
        seats_available = max(0, capacity - (result.count or 0))
    
    enrollment = None
    can_enroll = True
    
    if user:
        student_id = user["sub"]
        db = get_db()
        existing = db.table("enrollments").select("id, status, payment_id").eq("student_id", student_id).eq("course_id", course_id).limit(1).execute()
        if existing.data:
            enr = existing.data[0]
            enrollment = {
                "id": enr["id"],
                "status": enr["status"],
                "payment_id": enr.get("payment_id"),
            }
            can_enroll = enr["status"] not in ["active", "seat_reserved"]
        elif capacity is not None and seats_available == 0:
            can_enroll = False
    
    return CourseEnrollmentSummary(
        course={
            "id": course["id"],
            "name": course["name"],
            "description": course.get("description"),
            "start_date": course.get("start_date"),
            "class_time": course.get("class_time"),
            "price_minor": course.get("price_minor"),
            "currency": course.get("currency"),
            "seat_reservation_minor": course.get("seat_reservation_minor"),
            "expected_study_hours": course.get("expected_study_hours"),
            "learning_outcomes": course.get("learning_outcomes"),
            "prerequisites": course.get("prerequisites"),
            "capacity": course.get("capacity"),
            "seats_available": seats_available,
        },
        enrollment=enrollment,
        can_enroll=can_enroll,
        seats_available=seats_available,
    )


# Admin routes
@router.get("/admin/all", dependencies=[Depends(require_role("admin"))])
async def list_all_enrollments(
    course_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Admin: List all enrollments."""
    db = get_db()
    query = db.table("enrollments").select("*, students(name, email), courses(name)").order("enrolled_at", desc=True)
    
    if course_id:
        query = query.eq("course_id", course_id)
    if status:
        query = query.eq("status", status)
    
    query = query.range(offset, offset + limit - 1)
    result = query.execute()
    return {"enrollments": result.data or [], "total": len(result.data or [])}


@router.post("/admin/{enrollment_id}/status", dependencies=[Depends(require_role("admin"))])
async def update_enrollment_status(
    enrollment_id: str,
    new_status: str = Body(..., pattern="^(active|inactive|completed|dropped)$", embed=True),
):
    """Admin: Update enrollment status."""
    db = get_db()
    result = db.table("enrollments").update({"status": new_status}).eq("id", enrollment_id).execute()
    if not result.data:
        raise HTTPException(404, "Enrollment not found")
    return {"status": "ok", "enrollment": result.data[0]}