"""GET /courses - returns list of courses."""

from fastapi import APIRouter, Query
from src.database import get_db

router = APIRouter()


@router.get("/courses")
def get_courses(
    include_inactive: bool = Query(False, description="Include inactive courses (admin only)"),
):
    """Get all courses. Public endpoint returns only active courses."""
    db = get_db()
    query = db.table("courses").select(
        "id, name, description, start_date, class_time, timezone, "
        "price_minor, currency, capacity, seat_reservation_minor, "
        "expected_study_hours, learning_outcomes, prerequisites, "
        "support_email, support_phone, is_active, created_at"
    )
    
    if not include_inactive:
        query = query.eq("is_active", True)
    
    resp = query.order("start_date").execute()
    return {"courses": resp.data or []}


@router.get("/courses/{course_id}")
def get_course(course_id: str):
    """Get a single course by ID."""
    db = get_db()
    resp = db.table("courses").select(
        "id, name, description, start_date, class_time, timezone, "
        "price_minor, currency, capacity, seat_reservation_minor, "
        "expected_study_hours, learning_outcomes, prerequisites, "
        "support_email, support_phone, whatsapp_group_jid, proof_submission_group_jid, "
        "is_active, created_at"
    ).eq("id", course_id).limit(1).execute()
    
    if not resp.data:
        from fastapi import HTTPException
        raise HTTPException(404, "Course not found")
    
    return resp.data[0]