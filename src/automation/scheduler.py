"""Determines who needs a reminder today.

Rules (also the idempotency gate):
1. Course has a class scheduled today.
2. Student enrollment is active.
3. No row already exists in reminder_log for that enrollment today.
"""

from __future__ import annotations

import time
from datetime import date

from src.config import get_settings
from src.database import get_db
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
    return [Course(**row) for row in resp.data]


def active_enrollments(db, course_id) -> list[Enrollment]:
    resp = (
        db.table("enrollments")
        .select("id, student_id, course_id, status, enrolled_at")
        .eq("course_id", str(course_id))
        .eq("status", "active")
        .execute()
    )
    return [Enrollment(**row) for row in resp.data]


def already_sent(db, enrollment_id, on_date: date | None = None) -> bool:
    on_date = on_date or date.today()
    resp = (
        db.table("reminder_log")
        .select("id")
        .eq("enrollment_id", str(enrollment_id))
        .gte("sent_at", f"{on_date.isoformat()}T00:00:00")
        .lt("sent_at", f"{on_date.isoformat()}T23:59:59")
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
    """Run the full daily flow: query queue, send, log. Returns count sent."""
    from src.channels.base import get_channel
    from src.automation.reminder_templates import reminder_for
    from src.automation.engagement import classify, days_since_last_submission

    settings = get_settings()
    channel = get_channel(settings.active_channel)
    queue = build_reminder_queue(db, on_date)
    sent = 0

    for enrollment in queue:
        student = get_student(db, enrollment.student_id)
        if not student:
            logger.warning(f"No student found for enrollment {enrollment.id}")
            continue

        pending = days_since_last_submission(db, enrollment.id, on_date)
        status = classify(pending)

        resp = db.table("courses").select("name, class_time").eq("id", str(enrollment.course_id)).limit(1).execute()
        course_name = resp.data[0]["name"] if resp.data else "your course"
        class_time = resp.data[0]["class_time"] if resp.data else "TBD"

        tmpl = reminder_for(student.name, course_name, class_time, status)
        ok = channel.send(student, tmpl.body)

        db.table("reminder_log").insert({
            "enrollment_id": str(enrollment.id),
            "channel": channel.name,
            "message": tmpl.body,
            "delivery_status": "sent" if ok else "failed",
        }).execute()

        if ok:
            sent += 1
            logger.info(f"Reminder sent to {student.name} via {channel.name}")
        else:
            logger.error(f"Reminder failed for {student.name} via {channel.name}")

        if settings.rate_limit_delay_seconds > 0:
            time.sleep(settings.rate_limit_delay_seconds)

    logger.info(f"Daily job complete: {sent}/{len(queue)} sent.")
    return sent
