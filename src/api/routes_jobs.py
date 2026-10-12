"""POST /run-daily-job - manually triggers the full daily flow."""

from datetime import date

from fastapi import APIRouter, Depends
from src.api.auth import require_admin
from src.database import get_db
from src.automation.scheduler import send_reminders
from src.reports.daily_report import build_report, send_report_to_admin

router = APIRouter()


@router.post("/run-daily-job", dependencies=[Depends(require_admin)])
def run_daily_job():
    db = get_db()
    run_date = date.today()
    sent = send_reminders(db, run_date)
    report = build_report(db, run_date)
    report_sent = send_report_to_admin(report, db=db)
    return {"status": "ok", "reminders_sent": sent, "report_sent": report_sent}
