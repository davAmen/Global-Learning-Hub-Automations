"""Determines who needs a reminder today.

Rules (also the idempotency gate):
1. Course has a class scheduled today (in course timezone).
2. Student enrollment is active.
3. No row already exists in reminder_log for that enrollment today.
"""

from __future__ import annotations

import asyncio
import time
from datetime import date, datetime, time, timezone
from typing import Optional
from uuid import UUID

from src.config import get_settings
from src.database import get_db
from src.database.models import Course, Enrollment
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_gmt_now() -> datetime:
    """Get current time in GMT."""
    return datetime.now(timezone.utc)


def get_gmt_date() -> date:
    """Get current date in GMT."""
    return datetime.now(timezone.utc).date()


def parse_course_time(class_time_str: str, tz_name: str = "GMT") -> time:
    """Parse class time string to time object."""
    try:
        return time.fromisoformat(class_time_str)
    except ValueError:
        # Fallback for formats like "9:00" or "18:00"
        for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p"):
            try:
                return datetime.strptime(class_time_str, fmt).time()
            except ValueError:
                continue
        return time(9, 0)  # Default


def classes_today(db, on_date: Optional[date] = None, tz_name: str = "GMT") -> list[Course]:
    """Get courses that have class today in the given timezone."""
    on_date = on_date or get_gmt_date()
    resp = (
        db.table("courses")
        .select("id, name, start_date, class_time, timezone, is_active, created_at")
        .eq("start_date", on_date.isoformat())
        .eq("is_active", True)
        .execute()
    )
    courses = [Course(**row) for row in resp.data]
    return courses


def active_enrollments(db, course_id: UUID) -> list[Enrollment]:
    resp = (
        db.table("enrollments")
        .select("id, student_id, course_id, status, enrolled_at")
        .eq("course_id", str(course_id))
        .eq("status", "active")
        .execute()
    )
    return [Enrollment(**row) for row in resp.data]


def already_sent(db, enrollment_id: UUID, on_date: Optional[date] = None) -> bool:
    on_date = on_date or get_gmt_date()
    resp = (
        db.table("reminder_log")
        .select("id")
        .eq("enrollment_id", str(enrollment_id))
        .gte("sent_at", f"{on_date.isoformat()}T00:00:00")
        .lt("sent_at", f"{on_date.isoformat()}T23:59:59")
        .execute()
    )
    return bool(resp.data)


def already_sent_course(db, course_id: UUID, on_date: Optional[date] = None) -> bool:
    """Check if group reminder already sent for course today."""
    on_date = on_date or get_gmt_date()
    resp = (
        db.table("reminder_log")
        .select("id")
        .eq("course_id", str(course_id))
        .gte("sent_at", f"{on_date.isoformat()}T00:00:00")
        .lt("sent_at", f"{on_date.isoformat()}T23:59:59")
        .execute()
    )
    return bool(resp.data)


def get_student(db, student_id: UUID):
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


def build_reminder_queue(db, on_date: Optional[date] = None, tz_name: str = "GMT") -> list[tuple]:
    """Returns list of (enrollment, course) tuples for courses today."""
    on_date = on_date or get_gmt_date()
    queue: list[tuple] = []
    for course in classes_today(db, on_date, tz_name):
        for enrollment in active_enrollments(db, course.id):
            if not already_sent(db, enrollment.id, on_date):
                queue.append((enrollment, course))
    return queue


async def send_reminders_async(db, on_date: Optional[date] = None, tz_name: str = "GMT") -> int:
    """Async version of send_reminders with proper rate limiting."""
    from src.channels.base import get_channel
    from src.automation.reminder_templates import reminder_for
    from src.automation.engagement import classify, days_since_last_submission, update_engagement

    settings = get_settings()
    channel = get_channel(settings.active_channel)
    queue = build_reminder_queue(db, on_date, tz_name)
    sent = 0

    for enrollment, course in queue:
        student = get_student(db, enrollment.student_id)
        if not student:
            logger.warning(f"No student found for enrollment {enrollment.id}")
            continue

        engagement_status = update_engagement(db, enrollment.id, on_date)

        pending = days_since_last_submission(db, enrollment.id, on_date)
        status = classify(pending)

        course_name = course.name
        class_time = course.class_time or "TBD"

        tmpl = reminder_for(student.name, course_name, class_time, status)
        ok, external_msg_id = await channel.send(recipient=student.phone, message=tmpl.body)

        insert_data = {
            "enrollment_id": str(enrollment.id),
            "channel": channel.name,
            "message": tmpl.body,
            "delivery_status": "sent" if ok else "failed",
        }
        if external_msg_id:
            insert_data["external_message_id"] = external_msg_id
        db.table("reminder_log").insert(insert_data).execute()

        if ok:
            sent += 1
            logger.info(f"Reminder sent to {student.name} via {channel.name}")
        else:
            logger.error(f"Reminder failed for {student.name} via {channel.name}")

        if settings.rate_limit_delay_seconds > 0:
            await asyncio.sleep(settings.rate_limit_delay_seconds)

    logger.info(f"Daily job complete: {sent}/{len(queue)} sent.")
    return sent


def send_reminders(db, on_date: Optional[date] = None, tz_name: str = "GMT") -> int:
    """Sync wrapper for backward compatibility."""
    return asyncio.run(send_reminders_async(db, on_date, tz_name))