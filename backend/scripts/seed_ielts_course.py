"""Seed the IELTS course and test data for pilot."""

import uuid
from datetime import date, datetime, time, timezone

from src.database import get_db


def seed_ielts_course():
    db = get_db()

    # IELTS Course
    course_id = str(uuid.uuid4())
    course_data = {
        "id": course_id,
        "name": "IELTS Preparation (Oct 15-30, 6-8pm GMT)",
        "description": "Intensive 14-day IELTS Academic preparation course covering all 4 skills: Listening, Reading, Writing, and Speaking. Includes daily live sessions, practice materials, mock tests, and personalized feedback.",
        "start_date": date(2026, 10, 15).isoformat(),
        "class_time": "18:00:00",
        "timezone": "GMT",
        "is_active": True,
        "price_minor": 10000,  # GHS 100.00
        "currency": "GHS",
        "capacity": 50,
        "seat_reservation_minor": 1500,  # GHS 15.00
        "expected_study_hours": 28,
        "learning_outcomes": [
            "Achieve target band score in IELTS Academic (typically 6.5-7.5)",
            "Master all 4 skills: Listening, Reading, Writing, Speaking",
            "Apply time management strategies for each test section",
            "Use appropriate vocabulary and grammar for band 7+",
            "Complete full mock tests under exam conditions"
        ],
        "prerequisites": [
            "Basic English proficiency (CEFR B1+ or equivalent)",
            "Commitment to 2 hours daily study for 14 days",
            "Access to WhatsApp for class communication",
            "Headset/microphone for speaking practice"
        ],
        "support_email": "support@globallearninghub.com",
        "support_phone": "+233548014157",
        "whatsapp_group_jid": "120363413380837553@g.us",
        "proof_submission_group_jid": "120363428841556134@g.us",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.table("courses").upsert(course_data, on_conflict="id").execute()

    # Create WhatsApp groups
    groups = [
        {
            "id": str(uuid.uuid4()),
            "whatsapp_jid": "120363418173591450@g.us",
            "name": "GLH IELTS Announcements",
            "type": "announcement",
            "course_id": course_id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "whatsapp_jid": "120363428841556134@g.us",
            "name": "GLH IELTS Payment Proofs",
            "type": "proof_submission",
            "course_id": course_id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "whatsapp_jid": "120363413380837553@g.us",
            "name": "GLH IELTS Class Access",
            "type": "class_access",
            "course_id": course_id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    for group in groups:
        db.table("groups").upsert(group, on_conflict="whatsapp_jid").execute()

    # Test students
    students = [
        {"id": str(uuid.uuid4()), "name": "Kwame Mensah", "phone": "+233548014157", "email": "kwame@example.com", "password_hash": "$2b$12$placeholder", "email_verified": True, "role": "learner", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Ama Boateng", "phone": "+233244567890", "email": "ama@example.com", "password_hash": "$2b$12$placeholder", "email_verified": True, "role": "learner", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Kofi Asante", "phone": "+233206967251", "email": "kofi@example.com", "password_hash": "$2b$12$placeholder", "email_verified": False, "role": "learner", "created_at": datetime.now(timezone.utc).isoformat()},
    ]

    student_ids = []
    for student in students:
        db.table("students").upsert(student, on_conflict="id").execute()
        student_ids.append(student["id"])

    # Admin user
    admin_id = str(uuid.uuid4())
    admin_data = {
        "id": admin_id,
        "name": "David Amenuku",
        "phone": "+233548014157",
        "email": "amenukudavid20@gmail.com",
        "password_hash": "$2b$12$placeholder",
        "email_verified": True,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.table("students").upsert(admin_data, on_conflict="id").execute()

    # Enroll test students
    for student_id in student_ids:
        enrollment_data = {
            "id": str(uuid.uuid4()),
            "student_id": student_id,
            "course_id": course_id,
            "status": "active",
            "enrolled_at": datetime.now(timezone.utc).isoformat(),
        }
        db.table("enrollments").upsert(enrollment_data, on_conflict="id").execute()

    print(f"Seeded IELTS course: {course_id}")
    print(f"Seeded {len(students)} test students + 1 admin")
    print(f"Seeded {len(groups)} WhatsApp groups")


if __name__ == "__main__":
    seed_ielts_course()