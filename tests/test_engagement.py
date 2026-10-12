"""Classification must not invent assignment submissions."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_update_does_not_mark_submission():
    from src.automation.engagement import update_engagement
    db = MagicMock()
    with patch("src.automation.engagement.days_since_last_submission", return_value=0):
        assert update_engagement(db, "enrollment", date(2026, 9, 25)) == "active"
    payload = db.table.return_value.upsert.call_args.args[0]
    assert "assignment_submitted" not in payload


def test_schema_has_unique_key_for_daily_engagement_upsert():
    schema = (Path(__file__).parents[1] / "src" / "database" / "schema.sql").read_text()
    assert "unique (enrollment_id, date)" in schema.lower()


def test_schema_has_unique_key_for_cross_process_send_idempotency():
    schema = (Path(__file__).parents[1] / "src" / "database" / "schema.sql").read_text()
    assert "idempotency_key text unique" in schema.lower()
