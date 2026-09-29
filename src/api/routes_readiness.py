"""Authenticated record-entry routes for the Phase 2 weekly readiness notice."""

import logging
import re
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from src.api.readiness_auth import (
    ReadinessActor,
    get_readiness_db,
    require_readiness_learner,
    require_readiness_staff,
)

logger = logging.getLogger(__name__)
router = APIRouter()
_CHANNEL_CODE = re.compile(r"^[a-z][a-z0-9_-]{0,49}$")
_PURPOSE = "device_readiness_weekly"
_CONSENT_VERSION = "device-readiness-v1"
_CONSENT_COPY = (
    "Optional: receive one weekly device-readiness reminder through {channel}. "
    "You can opt out at any time. This choice is separate from course reminders."
)


class PaymentEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["verified", "revoked"]


class ConsentEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["opt_in", "opt_out"]
    channel: str = Field(max_length=50)


class ChannelPreferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_order: list[str] = Field(max_length=16)


def _validate_channel(channel: str) -> None:
    if not _CHANNEL_CODE.fullmatch(channel):
        raise HTTPException(status_code=422, detail="Channel must be a lowercase channel identifier")


def _validate_consent(request: ConsentEventRequest) -> None:
    _validate_channel(request.channel)


def _rows(response: Any) -> list[dict[str, Any]]:
    """Return response rows only when the database result has the expected shape."""
    data = getattr(response, "data", None)
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _require_student(db: Any, student_id: UUID) -> None:
    """Fail clearly when staff selects a student that does not exist."""
    try:
        student_rows = _rows(
            db.table("students")
            .select("id")
            .eq("id", str(student_id))
            .limit(1)
            .execute()
        )
    except Exception:
        logger.error("Could not check a student before recording direct consent.")
        raise HTTPException(status_code=503, detail="Readiness service unavailable") from None
    if not student_rows:
        raise HTTPException(status_code=404, detail="Student not found")


def _insert_event(db: Any, table: str, event: dict[str, Any]) -> None:
    """Append one audit event and fail closed if persistence is unavailable."""
    try:
        db.table(table).insert(event).execute()
    except Exception:
        logger.error("Could not append a Phase 2 readiness event to %s.", table)
        raise HTTPException(status_code=503, detail="Readiness service unavailable") from None


@router.get("/readiness/consent-notice")
def get_consent_notice(channel: str) -> dict[str, str]:
    """Return the versioned sample wording the client must show before opt-in."""
    _validate_channel(channel)
    return {
        "version": _CONSENT_VERSION,
        "text": _CONSENT_COPY.format(channel=channel),
    }


@router.post(
    "/readiness/enrollments/{enrollment_id}/payment-events",
    status_code=status.HTTP_201_CREATED,
)
def record_payment_event(
    enrollment_id: UUID,
    request: PaymentEventRequest,
    actor: ReadinessActor = Depends(require_readiness_staff),
    db: Any = Depends(get_readiness_db),
) -> dict[str, str]:
    """Let an authenticated staff member record payment verification or revocation."""
    try:
        enrollment_rows = _rows(
            db.table("enrollments")
            .select("id")
            .eq("id", str(enrollment_id))
            .limit(1)
            .execute()
        )
    except Exception:
        logger.error("Could not check a Phase 2 enrollment before recording payment.")
        raise HTTPException(status_code=503, detail="Readiness service unavailable") from None
    if not enrollment_rows:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    _insert_event(
        db,
        "enrollment_payment_verification_events",
        {
            "enrollment_id": str(enrollment_id),
            "action": request.action,
            "recorded_by": str(actor.user_id),
        },
    )
    return {"status": "recorded"}


def _record_consent(
    *,
    db: Any,
    actor: ReadinessActor,
    student_id: UUID,
    source: Literal["learner_self_service", "learner_direct_request"],
    request: ConsentEventRequest,
) -> dict[str, str]:
    _validate_consent(request)
    _insert_event(
        db,
        "student_channel_consent_events",
        {
            "student_id": str(student_id),
            "purpose": _PURPOSE,
            "channel": request.channel,
            "action": request.action,
            "consent_version": _CONSENT_VERSION if request.action == "opt_in" else None,
            "source": source,
            "recorded_by": str(actor.user_id),
        },
    )
    return {"status": "recorded"}


@router.post("/readiness/me/consent-events", status_code=status.HTTP_201_CREATED)
def record_own_consent_event(
    request: ConsentEventRequest,
    actor: ReadinessActor = Depends(require_readiness_learner),
    db: Any = Depends(get_readiness_db),
) -> dict[str, str]:
    """Let a learner opt in or out only for their linked student record."""
    if actor.student_id is None:
        raise HTTPException(status_code=403, detail="Learner access required")
    return _record_consent(
        db=db,
        actor=actor,
        student_id=actor.student_id,
        source="learner_self_service",
        request=request,
    )


@router.post(
    "/readiness/students/{student_id}/consent-events",
    status_code=status.HTTP_201_CREATED,
)
def record_direct_consent_event(
    student_id: UUID,
    request: ConsentEventRequest,
    actor: ReadinessActor = Depends(require_readiness_staff),
    db: Any = Depends(get_readiness_db),
) -> dict[str, str]:
    """Let staff record consent explicitly requested by the named learner."""
    _require_student(db, student_id)
    return _record_consent(
        db=db,
        actor=actor,
        student_id=student_id,
        source="learner_direct_request",
        request=request,
    )


@router.post("/readiness/me/channel-preferences", status_code=status.HTTP_201_CREATED)
def record_own_channel_preferences(
    request: ChannelPreferenceRequest,
    actor: ReadinessActor = Depends(require_readiness_learner),
    db: Any = Depends(get_readiness_db),
) -> dict[str, str]:
    """Append the learner's complete preferred/fallback order, or clear it."""
    if actor.student_id is None:
        raise HTTPException(status_code=403, detail="Learner access required")
    order = request.channel_order
    if any(not _CHANNEL_CODE.fullmatch(channel) for channel in order):
        raise HTTPException(status_code=422, detail="Channel order contains an invalid identifier")
    if len(set(order)) != len(order):
        raise HTTPException(status_code=422, detail="A channel may appear only once in the order")

    _insert_event(
        db,
        "student_channel_preference_events",
        {
            "student_id": str(actor.student_id),
            "purpose": _PURPOSE,
            "channel_order": order,
            "recorded_by": str(actor.user_id),
        },
    )
    return {"status": "recorded"}
