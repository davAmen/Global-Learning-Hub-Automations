"""Build and deliver the daily reminder queue safely and idempotently."""

from __future__ import annotations

import time
from datetime import date, datetime, time as dt_time, timedelta, timezone

from src.config import get_settings
from src.database.models import Course, Enrollment
from src.utils.logger import get_logger

logger = get_logger(__name__)


def classes_today(db, on_date: date | None = None) -> list[Course]:
    on_date = on_date or date.today()
    resp = (
        db.table("courses")
        .select("id, name, start_date, class_time, created_at")
        .eq("start_date", on_date.isoformat())
        .execute()
    )
    return [Course(**row) for row in (resp.data or [])]


def active_enrollments(db, course_id) -> list[Enrollment]:
    resp = (
        db.table("enrollments")
        .select("id, student_id, course_id, status, enrolled_at")
        .eq("course_id", str(course_id))
        .eq("status", "active")
        .execute()
    )
    return [Enrollment(**row) for row in (resp.data or [])]


def _utc_day_bounds(on_date: date) -> tuple[str, str]:
    start = datetime.combine(on_date, dt_time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def already_sent(db, enrollment_id, on_date: date | None = None) -> bool:
    """Return True when this enrollment already has any reminder attempt today."""
    on_date = on_date or date.today()
    start, end = _utc_day_bounds(on_date)
    resp = (
        db.table("reminder_log")
        .select("id")
        .eq("enrollment_id", str(enrollment_id))
        .gte("sent_at", start)
        .lt("sent_at", end)
        .limit(1)
        .execute()
    )
    return bool(resp.data)


def get_student(db, student_id):
    resp = (
        db.table("students")
        .select("id, name, phone, email, created_at")
        .eq("id", str(student_id))
        .limit(1)
        .execute()
    )
    if resp.data:
        from src.database.models import Student
        return Student(**resp.data[0])
    return None


def build_reminder_queue(db, on_date: date | None = None) -> list[Enrollment]:
    on_date = on_date or date.today()
    queue: list[Enrollment] = []
    for course in classes_today(db, on_date):
        for enrollment in active_enrollments(db, course.id):
            if not already_sent(db, enrollment.id, on_date):
                queue.append(enrollment)
    return queue


def send_reminders(db, on_date: date | None = None) -> int:
    """Run the daily flow and return the number of successful deliveries."""
    from src.channels.base import get_channel
    from src.automation.reminder_templates import reminder_for
    from src.automation.engagement import update_engagement

    settings = get_settings()
    channel = get_channel(settings.active_channel)
    queue = build_reminder_queue(db, on_date)
    sent = 0

    for enrollment in queue:
        student = get_student(db, enrollment.student_id)
        if not student:
            logger.warning("No student found for enrollment %s", enrollment.id)
            continue

        # Re-check immediately before delivery to narrow the race window between
        # concurrent workers. The database unique index is the final safeguard.
        if already_sent(db, enrollment.id, on_date):
            logger.info("Skipping duplicate reminder attempt for enrollment %s", enrollment.id)
            continue

        status = update_engagement(db, enrollment.id, on_date)
        resp = (
            db.table("courses")
            .select("name, class_time")
            .eq("id", str(enrollment.course_id))
            .limit(1)
            .execute()
        )
        course_name = resp.data[0]["name"] if resp.data else "your course"
        class_time = str(resp.data[0]["class_time"]) if resp.data and resp.data[0]["class_time"] else "TBD"
        tmpl = reminder_for(student.name, course_name, class_time, status)

        # Claim the day's unique slot BEFORE contacting the provider. A second
        # worker cannot pass this insert, even when both passed already_sent().
        try:
            claim = db.table("reminder_log").insert({
                "enrollment_id": str(enrollment.id),
                "channel": channel.name,
                "message": tmpl.body,
                "delivery_status": "pending",
            }).execute()
            claim_id = claim.data[0]["id"]
        except Exception:
            logger.warning("Reminder claim unavailable for enrollment %s", enrollment.id)
            continue

        ok = False
        try:
            ok = channel.send(student, tmpl.body)
        except Exception:
            logger.exception("Channel raised while sending enrollment %s", enrollment.id)

        try:
            db.table("reminder_log").update({
                "delivery_status": "sent" if ok else "failed",
            }).eq("id", claim_id).execute()
        except Exception:
            logger.exception("Could not persist reminder log for enrollment %s", enrollment.id)
            # Never count an unlogged delivery as a successful automated run.
            ok = False

        if ok:
            sent += 1
            logger.info("Reminder sent to %s via %s", student.name, channel.name)
        else:
            logger.error("Reminder failed for %s via %s", student.name, channel.name)

        if settings.rate_limit_delay_seconds > 0:
            time.sleep(settings.rate_limit_delay_seconds)

    logger.info("Daily job complete: %d/%d sent.", sent, len(queue))
    return sent
