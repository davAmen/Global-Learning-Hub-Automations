"""GET /reports/today - returns today's engagement report as JSON."""

from fastapi import APIRouter, Depends
from src.api.auth import require_admin
from src.database import get_db
from src.reports.daily_report import build_report

router = APIRouter()


@router.get("/reports/today", dependencies=[Depends(require_admin)])
def reports_today():
    db = get_db()
    return build_report(db)
