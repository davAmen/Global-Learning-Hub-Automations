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

    # Check if record exists for today
    existing = (
        db.table("engagement_log")
        .select("id")
        .eq("enrollment_id", str(enrollment_id))
        .eq("date", reference.isoformat())
        .limit(1)
        .execute()
    )

    data = {
        "enrollment_id": str(enrollment_id),
        "date": reference.isoformat(),
        "status": status,
        "assignment_submitted": status == "active",
        "updated_at": date.today().isoformat(),
    }

    if existing.data:
        # Update existing record
        db.table("engagement_log").update(data).eq("id", existing.data[0]["id"]).execute()
    else:
        # Insert new record
        db.table("engagement_log").insert(data).execute()

    return status