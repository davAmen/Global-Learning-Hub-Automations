"""Local, synthetic tests for Phase 2 weekly-notice eligibility."""

from src.automation.weekly_readiness import eligible_for_weekly_readiness_channel

ENROLLMENT_ID = "enrollment-1"
STUDENT_ID = "student-1"


def payment_event(event_id: int, action: str, enrollment_id: str = ENROLLMENT_ID) -> dict:
    return {
        "id": event_id,
        "enrollment_id": enrollment_id,
        "action": action,
        "recorded_by": "staff-1",
    }


def consent_event(
    event_id: int,
    action: str,
    *,
    student_id: str = STUDENT_ID,
    purpose: str = "device_readiness_weekly",
    channel: str = "whatsapp",
) -> dict:
    return {
        "id": event_id,
        "student_id": student_id,
        "purpose": purpose,
        "channel": channel,
        "action": action,
        "consent_version": "weekly-readiness-v1" if action == "opt_in" else None,
        "source": "learner_direct_request",
        "recorded_by": "staff-1",
    }


def eligible(
    payment_events: list[dict],
    consent_events: list[dict],
    *,
    enrollment_status: str = "active",
    enrollment_student_id: str = STUDENT_ID,
    channel: str = "whatsapp",
) -> bool:
    return eligible_for_weekly_readiness_channel(
        enrollment={
            "id": ENROLLMENT_ID,
            "student_id": enrollment_student_id,
            "status": enrollment_status,
        },
        channel=channel,
        payment_events=payment_events,
        consent_events=consent_events,
    )


def test_eligible_when_paid_enrollment_and_exact_channel_are_opted_in() -> None:
    assert eligible(
        [payment_event(1, "verified")],
        [consent_event(1, "opt_in")],
    )


def test_active_enrollment_does_not_imply_payment() -> None:
    assert not eligible([], [consent_event(1, "opt_in")])


def test_payment_verification_is_tied_to_the_enrollment() -> None:
    assert not eligible(
        [payment_event(1, "verified", enrollment_id="another-enrollment")],
        [consent_event(1, "opt_in")],
    )


def test_newest_payment_revocation_overrides_verification() -> None:
    assert not eligible(
        [payment_event(2, "revoked"), payment_event(1, "verified")],
        [consent_event(1, "opt_in")],
    )


def test_payment_does_not_imply_channel_consent() -> None:
    assert not eligible([payment_event(1, "verified")], [])


def test_newest_opt_out_overrides_prior_opt_in_for_that_channel() -> None:
    assert not eligible(
        [payment_event(1, "verified")],
        [consent_event(2, "opt_out"), consent_event(1, "opt_in")],
    )


def test_consent_for_other_channel_student_or_purpose_does_not_qualify() -> None:
    other_consent = [
        consent_event(1, "opt_in", channel="email"),
        consent_event(2, "opt_in", student_id="another-student"),
        consent_event(3, "opt_in", purpose="another_purpose"),
    ]
    assert not eligible([payment_event(1, "verified")], other_consent)


def test_inactive_enrollment_does_not_qualify() -> None:
    assert not eligible(
        [payment_event(1, "verified")],
        [consent_event(1, "opt_in")],
        enrollment_status="inactive",
    )


def test_malformed_opt_in_fails_closed() -> None:
    invalid = consent_event(1, "opt_in")
    invalid["consent_version"] = " "
    assert not eligible([payment_event(1, "verified")], [invalid])


def test_noncanonical_channel_name_fails_closed() -> None:
    assert not eligible(
        [payment_event(1, "verified")],
        [consent_event(1, "opt_in", channel="WhatsApp")],
        channel="WhatsApp",
    )
