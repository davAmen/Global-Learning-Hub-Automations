"""GET /reports/today - returns today's engagement report as JSON."""

from fastapi import APIRouter
from src.database import get_db
from src.reports.daily_report import build_report

router = APIRouter()


@router.get("/reports/today")
def reports_today():
    db = get_db()
    return build_report(db)
