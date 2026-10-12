"""Regression checks for direct Supabase Data API access boundaries."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_TABLES = (
    "students",
    "courses",
    "enrollments",
    "engagement_log",
    "reminder_log",
)


def test_phase_one_tables_are_server_only_in_schema_and_architecture() -> None:
    files = (
        ROOT / "src" / "database" / "schema.sql",
        ROOT / "docs" / "ARCHITECTURE.md",
    )
    revoke_statement = (
        "revoke all on table students, courses, enrollments, engagement_log, "
        "reminder_log from public, anon, authenticated;"
    )
    grant_statement = (
        "grant select, insert, update on table students, courses, enrollments, "
        "engagement_log, reminder_log to service_role;"
    )

    for path in files:
        source = " ".join(path.read_text(encoding="utf-8").lower().split())
        for table in CORE_TABLES:
            assert f"alter table {table} enable row level security;" in source
        assert revoke_statement in source
        assert grant_statement in source
