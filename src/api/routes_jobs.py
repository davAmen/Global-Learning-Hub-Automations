"""POST /run-daily-job - manually triggers the full daily flow."""

from fastapi import APIRouter, Depends
from src.api.auth import require_admin
from src.database import get_db
from src.automation.scheduler import send_reminders

router = APIRouter()


@router.post("/run-daily-job", dependencies=[Depends(require_admin)])
def run_daily_job():
    db = get_db()
    sent = send_reminders(db)
    return {"status": "ok", "reminders_sent": sent}
