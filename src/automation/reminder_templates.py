"""Message templates. Kept separate from logic so a non-technical operator can
edit copy without touching code behavior.
"""

from __future__ import annotations


class ReminderTemplate:
    def __init__(self, subject: str, body: str):
        self.subject = subject
        self.body = body


def reminder_for(student_name: str, course_name: str, class_time: str, status: str) -> ReminderTemplate:
    when = class_time
    if status == "needs_followup":
        return ReminderTemplate(
            subject="Global Learning Hub - quick check-in",
            body=(
                f"Hi {student_name}, we noticed you've been quiet in {course_name} "
                f"lately. Your next class is today at {when}. Want us to help you "
                "get back on track? Just reply and let us know what's blocking you."
            ),
        )
    if status == "low_engagement":
        return ReminderTemplate(
            subject="Global Learning Hub - class reminder",
            body=(
                f"Hi {student_name}, this is a friendly reminder that {course_name} "
                f"is on today at {when}. We've missed a couple of your recent "
                "submissions - see you in class!"
            ),
        )
    return ReminderTemplate(
        subject="Global Learning Hub - class reminder",
        body=(
            f"Hi {student_name}, {course_name} is on today at {when}. "
            "See you in class! - Global Learning Hub"
        ),
    )
