"""Verify seeded data in Supabase."""
import sys
sys.path.insert(0, ".")

from src.database.client import get_db

db = get_db()

courses = db.table("courses").select("id, name, start_date, class_time").execute()
print("=== COURSES ===")
for c in courses.data:
    print(f"  {c['name']} | Date: {c['start_date']} | Time: {c['class_time']}")

students = db.table("students").select("id, name, phone, email").execute()
print("\n=== STUDENTS ===")
for s in students.data:
    print(f"  {s['name']} | {s['phone']} | {s['email']}")

enrollments = db.table("enrollments").select("id, student_id, course_id, status").execute()
print(f"\n=== ENROLLMENTS: {len(enrollments.data)} total ===")
for e in enrollments.data:
    print(f"  {e['student_id'][:8]}... -> {e['course_id'][:8]}... | {e['status']}")
