"""GET /courses - returns list of courses."""

from fastapi import APIRouter
from src.database import get_db

router = APIRouter()


@router.get("/courses")
def get_courses():
    db = get_db()
    resp = db.table("courses").select("id, name, start_date, class_time, created_at").execute()
    return {"courses": resp.data or []}