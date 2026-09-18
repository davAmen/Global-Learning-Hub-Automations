"""Insert FAKE students/courses/enrollments for local testing.

NO real student data is used here. This script is the only way to populate
the database during Phase 1 development.
"""

import uuid
from datetime import date, datetime, time

from src.database import get_db


def seed():
    db = get_db()

    courses = [
        {"id": str(uuid.uuid4()), "name": "Introduction to Python", "start_date": date.today().isoformat(), "class_time": str(time(9, 0))},
        {"id": str(uuid.uuid4()), "name": "Web Development Basics", "start_date": date.today().isoformat(), "class_time": str(time(14, 0))},
    ]
    for c in courses:
        db.table("courses").upsert(c, on_conflict="id").execute()

    students = [
        {"id": str(uuid.uuid4()), "name": "Kwame Mensah", "phone": "+233501234567", "email": "kwame@example.com"},
        {"id": str(uuid.uuid4()), "name": "Ama Boateng", "phone": "+233502345678", "email": "ama@example.com"},
        {"id": str(uuid.uuid4()), "name": "Kofi Asante", "phone": "+233503456789", "email": "kofi@example.com"},
    ]
    for s in students:
        s["created_at"] = datetime.now().isoformat()
        db.table("students").upsert(s, on_conflict="id").execute()

    enrollments = []
    for c in courses:
        for s in students:
            enrollments.append({
                "id": str(uuid.uuid4()),
                "student_id": s["id"],
                "course_id": c["id"],
                "status": "active",
            })
    for e in enrollments:
        db.table("enrollments").upsert(e, on_conflict="id").execute()

    print(f"Seeded {len(courses)} courses, {len(students)} students, {len(enrollments)} enrollments.")


if __name__ == "__main__":
    seed()
