"""GET /students - returns list of students."""

from fastapi import APIRouter
from src.database import get_db

router = APIRouter()


@router.get("/students")
def get_students():
    db = get_db()
    resp = db.table("students").select("id, name, phone, email, created_at").execute()
    return {"students": resp.data or []}