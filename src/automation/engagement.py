"""Engagement triage - three simple states only.

Kept deliberately minimal per DECISIONS.md:
- active: submitted within the window
- low_engagement: hasn't submitted in a while
- needs_followup: clearly falling behind
"""

from __future__ import annotations

from datetime import date

LOW_ENGAGEMENT_DAYS = 7
NEEDS_FOLLOWUP_DAYS = 14


def classify(pending_days: int) -> str:
    if pending_days <= LOW_ENGAGEMENT_DAYS:
        return "active"
    if pending_days <= NEEDS_FOLLOWUP_DAYS:
        return "low_engagement"
    return "needs_followup"


def days_since_last_submission(db, enrollment_id, reference: date | None = None) -> int:
    reference = reference or date.today()
    resp = (
        db.table("engagement_log")
        .select("date")
        .eq("enrollment_id", str(enrollment_id))
        .eq("assignment_submitted", True)
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    if not resp.data:
        return NEEDS_FOLLOWUP_DAYS + 1
    last = date.fromisoformat(resp.data[0]["date"])
    return (reference - last).days


def update_engagement(db, enrollment_id, reference: date | None = None) -> str:
    reference = reference or date.today()
    status = classify(days_since_last_submission(db, enrollment_id, reference))
    db.table("engagement_log").upsert(
        {
            "enrollment_id": str(enrollment_id),
            "date": reference.isoformat(),
            "status": status,
        },
        on_conflict="enrollment_id,date",
    ).execute()
    return status
