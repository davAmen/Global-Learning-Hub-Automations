"""Eligibility checks for the separate Phase 2 weekly readiness notice."""

from collections.abc import Callable, Mapping, Sequence
from uuid import UUID

WEEKLY_READINESS_PURPOSE = "device_readiness_weekly"


def _latest_event(
    events: Sequence[Mapping[str, object]],
    matches: Callable[[Mapping[str, object]], bool],
) -> Mapping[str, object] | None:
    """Return the matching event with the greatest database event ID."""
    latest: Mapping[str, object] | None = None
    latest_id = -1
    for event in events:
        event_id = event.get("id")
        if (
            not isinstance(event_id, int)
            or isinstance(event_id, bool)
            or event_id <= latest_id
            or not matches(event)
        ):
            continue
        latest = event
        latest_id = event_id
    return latest


def _same_id(value: object, expected: object) -> bool:
    """Compare database UUID values represented as strings or UUID objects."""
    return value is not None and expected is not None and str(value) == str(expected)


def _has_actor(event: Mapping[str, object]) -> bool:
    actor = event.get("recorded_by")
    return isinstance(actor, str) and bool(actor.strip())


def eligible_for_weekly_readiness_channel(
    *,
    enrollment: Mapping[str, object],
    channel: str,
    payment_events: Sequence[Mapping[str, object]],
    consent_events: Sequence[Mapping[str, object]],
) -> bool:
    """Check active enrollment, current payment verification, and exact channel consent.

    This checks only one channel candidate. It does not check channel preference,
    the 30-learner cohort cap, provider approval, or authorize sending.
    """
    enrollment_id = enrollment.get("id")
    student_id = enrollment.get("student_id")
    if (
        enrollment.get("status") != "active"
        or not isinstance(enrollment_id, (str, UUID))
        or not str(enrollment_id).strip()
        or not isinstance(student_id, (str, UUID))
        or not str(student_id).strip()
        or not isinstance(channel, str)
        or not channel
        or channel != channel.strip().lower()
    ):
        return False

    payment = _latest_event(
        payment_events,
        lambda event: _same_id(event.get("enrollment_id"), enrollment_id),
    )
    if not payment or payment.get("action") != "verified" or not _has_actor(payment):
        return False

    consent = _latest_event(
        consent_events,
        lambda event: (
            _same_id(event.get("student_id"), student_id)
            and event.get("purpose") == WEEKLY_READINESS_PURPOSE
            and event.get("channel") == channel
        ),
    )
    return bool(
        consent
        and consent.get("action") == "opt_in"
        and isinstance(consent.get("consent_version"), str)
        and bool(consent.get("consent_version").strip())
        and consent.get("source") in ("learner_self_service", "learner_direct_request")
        and _has_actor(consent)
    )
