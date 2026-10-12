"""Insert FAKE students/courses/enrollments for local testing.

NO real student data is used here. This script is the only way to populate
the database during Phase 1 development.
"""

import argparse
import uuid
from datetime import date, time
from typing import Any

from src.database import get_db


def _sample_id(record_type: str, key: str) -> str:
    """Return a stable, synthetic ID so rerunning the seed updates the same row."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://globallearninghub.example/sample/{record_type}/{key}"))


def seed(*, confirm_test_database: bool = False, db: Any | None = None) -> None:
    """Upsert synthetic records after an explicit test-database confirmation."""
    if not confirm_test_database:
        raise SystemExit(
            "Refusing to write sample records. Verify this is a non-production "
            "database, then pass --confirm-test-database."
        )
    if db is None:
        db = get_db()

    courses = [
        {"id": _sample_id("course", "introduction-to-python"), "name": "Introduction to Python", "start_date": date.today().isoformat(), "class_time": str(time(9, 0))},
        {"id": _sample_id("course", "web-development-basics"), "name": "Web Development Basics", "start_date": date.today().isoformat(), "class_time": str(time(14, 0))},
    ]
    for c in courses:
        db.table("courses").upsert(c, on_conflict="id").execute()

    students = [
        {"id": _sample_id("student", "kwame-mensah"), "name": "Kwame Mensah", "phone": "+15555550101", "email": "kwame@example.com"},
        {"id": _sample_id("student", "ama-boateng"), "name": "Ama Boateng", "phone": "+15555550102", "email": "ama@example.com"},
        {"id": _sample_id("student", "kofi-asante"), "name": "Kofi Asante", "phone": "+15555550103", "email": "kofi@example.com"},
    ]
    for s in students:
        db.table("students").upsert(s, on_conflict="id").execute()

    enrollments = []
    for c in courses:
        for s in students:
            enrollments.append({
                "id": _sample_id("enrollment", f"{c['id']}:{s['id']}"),
                "student_id": s["id"],
                "course_id": c["id"],
                "status": "active",
            })
    for e in enrollments:
        db.table("enrollments").upsert(e, on_conflict="id").execute()

    print(f"Seeded {len(courses)} courses, {len(students)} students, {len(enrollments)} enrollments.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add synthetic sample records to a test database.")
    parser.add_argument(
        "--confirm-test-database",
        action="store_true",
        help="confirm that the configured Supabase project is non-production",
    )
    arguments = parser.parse_args()
    seed(confirm_test_database=arguments.confirm_test_database)
