"""Builds and sends the daily engagement report to the administrator."""

from __future__ import annotations

from datetime import date

from src.config import get_settings
from src.database import get_db
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_report(db, on_date: date | None = None) -> dict:
    on_date = on_date or date.today()
    settings = get_settings()

    courses_resp = db.table("courses").select("id, name").eq("start_date", on_date.isoformat()).execute()
    courses = courses_resp.data or []

    total_enrolled = 0
    total_active = 0
    total_low = 0
    total_followup = 0
    total_sent = 0
    total_failed = 0

    for course in courses:
        enr = db.table("enrollments").select("id, status").eq("course_id", course["id"]).execute()
        active = [e for e in (enr.data or []) if e["status"] == "active"]
        total_enrolled += len(active)

        for e in active:
            eng = (
                db.table("engagement_log")
                .select("status")
                .eq("enrollment_id", e["id"])
                .eq("date", on_date.isoformat())
                .limit(1)
                .execute()
            )
            if eng.data:
                s = eng.data[0]["status"]
                if s == "active":
                    total_active += 1
                elif s == "low_engagement":
                    total_low += 1
                else:
                    total_followup += 1

    reminders = db.table("reminder_log").select("delivery_status").gte("sent_at", f"{on_date.isoformat()}T00:00:00").lt("sent_at", f"{on_date.isoformat()}T23:59:59").execute()
    for r in (reminders.data or []):
        if r["delivery_status"] == "sent":
            total_sent += 1
        elif r["delivery_status"] == "failed":
            total_failed += 1

    return {
        "date": on_date.isoformat(),
        "courses_today": len(courses),
        "total_enrolled": total_enrolled,
        "engagement": {"active": total_active, "low_engagement": total_low, "needs_followup": total_followup},
        "reminders": {"sent": total_sent, "failed": total_failed},
    }


def send_report_to_admin(report: dict, channel_name: str | None = None) -> bool:
    settings = get_settings()
    channel_name = channel_name or settings.backup_channel

    lines = [
        f"Daily Report - {report['date']}",
        f"Courses today: {report['courses_today']}",
        f"Total enrolled: {report['total_total'] if 'total_total' in report else report['total_enrolled']}",
        f"Engagement: {report['engagement']}",
        f"Reminders sent: {report['reminders']}",
    ]
    body = "\n".join(lines)

    if settings.admin_email:
        from src.channels.email_channel import EmailChannel
        ch = EmailChannel()
        from src.database.models import Student
        admin = Student(
            id="00000000-0000-0000-0000-000000000000",
            name="Administrator",
            phone=settings.admin_phone,
            email=settings.admin_email,
            created_at=date.today().isoformat(),
        )
        return ch.send(admin, body)

    logger.warning("No admin email configured - report not sent.")
    return False
