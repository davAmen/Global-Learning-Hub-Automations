"""Synthetic tests for authenticated Phase 2 readiness-record routes."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.api.readiness_auth import get_readiness_db

STAFF_ID = "00000000-0000-4000-8000-000000000001"
LEARNER_ID = "00000000-0000-4000-8000-000000000002"
UNMAPPED_ID = "00000000-0000-4000-8000-000000000003"
STUDENT_ID = "00000000-0000-4000-8000-000000000101"
OTHER_STUDENT_ID = "00000000-0000-4000-8000-000000000102"
ENROLLMENT_ID = "00000000-0000-4000-8000-000000000201"


class FakeAuthError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


class FakeResult:
    def __init__(self, data: list[dict] | None = None) -> None:
        self.data = data or []


class FakeQuery:
    def __init__(self, db: "FakeReadinessDb", table: str) -> None:
        self.db = db
        self.table_name = table
        self.filters: dict[str, str] = {}
        self.inserted: dict | None = None

    def select(self, _columns: str) -> "FakeQuery":
        return self

    def eq(self, column: str, value: str) -> "FakeQuery":
        self.filters[column] = value
        return self

    def limit(self, _count: int) -> "FakeQuery":
        return self

    def insert(self, row: dict) -> "FakeQuery":
        self.inserted = row
        return self

    def execute(self) -> FakeResult:
        if self.inserted is not None:
            self.db.events.setdefault(self.table_name, []).append(self.inserted)
            return FakeResult([self.inserted])

        rows = self.db.rows.get(self.table_name, [])
        selected = [
            row
            for row in rows
            if all(str(row.get(key)) == value for key, value in self.filters.items())
        ]
        return FakeResult(selected)


class FakeReadinessDb:
    def __init__(self) -> None:
        self.users = {
            "staff-token": STAFF_ID,
            "learner-token": LEARNER_ID,
            "unmapped-token": UNMAPPED_ID,
        }
        self.rows = {
            "app_user_profiles": [
                {"auth_user_id": STAFF_ID, "role": "staff", "student_id": None},
                {"auth_user_id": LEARNER_ID, "role": "learner", "student_id": STUDENT_ID},
            ],
            "enrollments": [{"id": ENROLLMENT_ID}],
            "students": [{"id": STUDENT_ID}, {"id": OTHER_STUDENT_ID}],
        }
        self.events: dict[str, list[dict]] = {}
        self.auth_failure: int | None = None

    def auth_get_user(self, access_token: str) -> SimpleNamespace:
        if self.auth_failure is not None:
            raise FakeAuthError(self.auth_failure)
        user_id = self.users.get(access_token)
        if user_id is None:
            raise FakeAuthError(401)
        return SimpleNamespace(user=SimpleNamespace(id=user_id))

    def table(self, table_name: str) -> FakeQuery:
        return FakeQuery(self, table_name)


@pytest.fixture
def api_client():
    from src.main import app

    db = FakeReadinessDb()
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_readiness_db] = lambda: db
    try:
        yield TestClient(app), db
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_readiness_routes_require_a_bearer_token(api_client) -> None:
    client, _db = api_client
    response = client.post(
        f"/readiness/enrollments/{ENROLLMENT_ID}/payment-events",
        json={"action": "verified"},
    )
    assert response.status_code == 401


def test_invalid_token_is_rejected(api_client) -> None:
    client, _db = api_client
    response = client.post(
        f"/readiness/enrollments/{ENROLLMENT_ID}/payment-events",
        headers=auth("not-a-token"),
        json={"action": "verified"},
    )
    assert response.status_code == 401


def test_auth_service_failure_fails_closed(api_client) -> None:
    client, db = api_client
    db.auth_failure = 503
    response = client.post(
        f"/readiness/enrollments/{ENROLLMENT_ID}/payment-events",
        headers=auth("staff-token"),
        json={"action": "verified"},
    )
    assert response.status_code == 503


def test_user_without_a_server_profile_is_rejected(api_client) -> None:
    client, _db = api_client
    response = client.post(
        f"/readiness/enrollments/{ENROLLMENT_ID}/payment-events",
        headers=auth("unmapped-token"),
        json={"action": "verified"},
    )
    assert response.status_code == 403


def test_staff_payment_event_uses_verified_actor_id(api_client) -> None:
    client, db = api_client
    response = client.post(
        f"/readiness/enrollments/{ENROLLMENT_ID}/payment-events",
        headers=auth("staff-token"),
        json={"action": "verified"},
    )
    assert response.status_code == 201
    assert db.events["enrollment_payment_verification_events"] == [
        {
            "enrollment_id": ENROLLMENT_ID,
            "action": "verified",
            "recorded_by": STAFF_ID,
        }
    ]


def test_learner_cannot_verify_payment(api_client) -> None:
    client, db = api_client
    response = client.post(
        f"/readiness/enrollments/{ENROLLMENT_ID}/payment-events",
        headers=auth("learner-token"),
        json={"action": "verified"},
    )
    assert response.status_code == 403
    assert "enrollment_payment_verification_events" not in db.events


def test_payment_event_requires_an_existing_enrollment(api_client) -> None:
    client, db = api_client
    missing_id = "00000000-0000-4000-8000-000000000299"
    response = client.post(
        f"/readiness/enrollments/{missing_id}/payment-events",
        headers=auth("staff-token"),
        json={"action": "verified"},
    )
    assert response.status_code == 404
    assert "enrollment_payment_verification_events" not in db.events


def test_actor_id_cannot_be_supplied_in_payment_request(api_client) -> None:
    client, db = api_client
    response = client.post(
        f"/readiness/enrollments/{ENROLLMENT_ID}/payment-events",
        headers=auth("staff-token"),
        json={"action": "verified", "recorded_by": UNMAPPED_ID},
    )
    assert response.status_code == 422
    assert "enrollment_payment_verification_events" not in db.events


def test_learner_consent_is_bound_to_their_profile_and_actor(api_client) -> None:
    client, db = api_client
    response = client.post(
        "/readiness/me/consent-events",
        headers=auth("learner-token"),
        json={
            "action": "opt_in",
            "channel": "email",
        },
    )
    assert response.status_code == 201
    assert db.events["student_channel_consent_events"] == [
        {
            "student_id": STUDENT_ID,
            "purpose": "device_readiness_weekly",
            "channel": "email",
            "action": "opt_in",
            "consent_version": "device-readiness-v1",
            "source": "learner_self_service",
            "recorded_by": LEARNER_ID,
        }
    ]


def test_learner_cannot_supply_another_student_id_or_actor(api_client) -> None:
    client, db = api_client
    response = client.post(
        "/readiness/me/consent-events",
        headers=auth("learner-token"),
        json={
            "action": "opt_in",
            "channel": "email",
            "student_id": OTHER_STUDENT_ID,
            "recorded_by": UNMAPPED_ID,
        },
    )
    assert response.status_code == 422
    assert "student_channel_consent_events" not in db.events


def test_learner_can_opt_out_without_a_notice_version(api_client) -> None:
    client, db = api_client
    response = client.post(
        "/readiness/me/consent-events",
        headers=auth("learner-token"),
        json={"action": "opt_out", "channel": "whatsapp"},
    )
    assert response.status_code == 201
    event = db.events["student_channel_consent_events"][0]
    assert event["action"] == "opt_out"
    assert event["consent_version"] is None
    assert event["source"] == "learner_self_service"


def test_client_cannot_choose_a_consent_text_version(api_client) -> None:
    client, db = api_client
    response = client.post(
        "/readiness/me/consent-events",
        headers=auth("learner-token"),
        json={"action": "opt_in", "channel": "email", "consent_version": "forged-version"},
    )
    assert response.status_code == 422
    assert "student_channel_consent_events" not in db.events


def test_staff_can_record_a_learner_direct_request_with_staff_attribution(api_client) -> None:
    client, db = api_client
    response = client.post(
        f"/readiness/students/{STUDENT_ID}/consent-events",
        headers=auth("staff-token"),
        json={
            "action": "opt_in",
            "channel": "sms",
        },
    )
    assert response.status_code == 201
    event = db.events["student_channel_consent_events"][0]
    assert event["student_id"] == STUDENT_ID
    assert event["source"] == "learner_direct_request"
    assert event["recorded_by"] == STAFF_ID


def test_staff_direct_consent_requires_an_existing_student(api_client) -> None:
    client, db = api_client
    missing_student_id = "00000000-0000-4000-8000-000000000199"
    response = client.post(
        f"/readiness/students/{missing_student_id}/consent-events",
        headers=auth("staff-token"),
        json={"action": "opt_out", "channel": "sms"},
    )
    assert response.status_code == 404
    assert "student_channel_consent_events" not in db.events


def test_learner_cannot_record_direct_consent_for_another_student(api_client) -> None:
    client, db = api_client
    response = client.post(
        f"/readiness/students/{OTHER_STUDENT_ID}/consent-events",
        headers=auth("learner-token"),
        json={
            "action": "opt_in",
            "channel": "sms",
        },
    )
    assert response.status_code == 403
    assert "student_channel_consent_events" not in db.events


def test_consent_notice_returns_the_server_owned_copy_version() -> None:
    from src.main import app

    response = TestClient(app).get("/readiness/consent-notice?channel=email")
    assert response.status_code == 200
    assert response.json() == {
        "version": "device-readiness-v1",
        "text": (
            "Optional: receive one weekly device-readiness reminder through email. "
            "You can opt out at any time. This choice is separate from course reminders."
        ),
    }


def test_learner_preference_snapshot_preserves_their_channel_order(api_client) -> None:
    client, db = api_client
    response = client.post(
        "/readiness/me/channel-preferences",
        headers=auth("learner-token"),
        json={"channel_order": ["email", "whatsapp", "sms"]},
    )
    assert response.status_code == 201
    assert db.events["student_channel_preference_events"] == [
        {
            "student_id": STUDENT_ID,
            "purpose": "device_readiness_weekly",
            "channel_order": ["email", "whatsapp", "sms"],
            "recorded_by": LEARNER_ID,
        }
    ]


def test_empty_preference_snapshot_clears_selection_without_changing_consent(api_client) -> None:
    client, db = api_client
    response = client.post(
        "/readiness/me/channel-preferences",
        headers=auth("learner-token"),
        json={"channel_order": []},
    )
    assert response.status_code == 201
    assert db.events["student_channel_preference_events"][0]["channel_order"] == []
    assert "student_channel_consent_events" not in db.events


@pytest.mark.parametrize(
    "channel_order",
    [["email", "email"], ["WhatsApp"], [" bad"], [""], ["email", "sms", "bad/channel"]],
)
def test_invalid_channel_preference_order_is_rejected(api_client, channel_order: list[str]) -> None:
    client, db = api_client
    response = client.post(
        "/readiness/me/channel-preferences",
        headers=auth("learner-token"),
        json={"channel_order": channel_order},
    )
    assert response.status_code == 422
    assert "student_channel_preference_events" not in db.events


def test_staff_cannot_change_learner_preferences(api_client) -> None:
    client, db = api_client
    response = client.post(
        "/readiness/me/channel-preferences",
        headers=auth("staff-token"),
        json={"channel_order": ["email"]},
    )
    assert response.status_code == 403
    assert "student_channel_preference_events" not in db.events
