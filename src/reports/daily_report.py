"""Builds and sends the daily engagement report to the administrator."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.config import get_settings
from src.database import get_db
from src.channels.base import get_channel, send_and_log
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_report(db, on_date: date | None = None) -> dict:
    on_date = on_date or date.today()
    next_day = on_date + timedelta(days=1)

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

    reminders = (
        db.table("reminder_log")
        .select("delivery_status, enrollment_id")
        .gte("sent_at", f"{on_date.isoformat()}T00:00:00")
        .lt("sent_at", f"{next_day.isoformat()}T00:00:00")
        .execute()
    )
    for r in (reminders.data or []):
        if not r.get("enrollment_id"):
            continue
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


def send_report_to_admin(
    report: dict,
    db: Any | None = None,
    channel_name: str | None = None,
) -> bool:
    settings = get_settings()
    channel_name = channel_name or settings.backup_channel
    if channel_name != "telegram":
        logger.error("Administrator report requires the configured Telegram channel")
        return False

    if db is None:
        db = get_db()

    report_date = date.fromisoformat(report["date"])
    next_day = report_date + timedelta(days=1)
    previous_attempt = (
        db.table("reminder_log")
        .select("id")
        .is_("enrollment_id", "null")
        .gte("sent_at", f"{report_date.isoformat()}T00:00:00")
        .lt("sent_at", f"{next_day.isoformat()}T00:00:00")
        .execute()
    )
    if previous_attempt.data:
        logger.info(f"Daily report for {report_date.isoformat()} was already attempted.")
        return False

    lines = [
        f"Daily Report - {report['date']}",
        f"Courses today: {report['courses_today']}",
        f"Total enrolled: {report['total_enrolled']}",
        (
            "Engagement: "
            f"{report['engagement']['active']} active, "
            f"{report['engagement']['low_engagement']} low engagement, "
            f"{report['engagement']['needs_followup']} need follow-up"
        ),
        f"Reminders sent: {report['reminders']['sent']}",
        f"Reminders failed: {report['reminders']['failed']}",
    ]
    body = "\n".join(lines)

    channel = get_channel(channel_name)
    return send_and_log(db, channel, None, body, None)
