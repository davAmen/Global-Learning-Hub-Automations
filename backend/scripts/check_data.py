"""Check what data is in the database."""
import sys
sys.path.insert(0, ".")
from src.database import get_db

db = get_db()

courses = db.table("courses").select("*").execute()
print(f"Courses: {len(courses.data)}")
for c in courses.data:
    print(f"  {c['name']} - start_date: {c['start_date']}")

students = db.table("students").select("*").execute()
print(f"\nStudents: {len(students.data)}")
for s in students.data:
    print(f"  {s['name']} - {s['phone']}")

enrollments = db.table("enrollments").select("*").execute()
print(f"\nEnrollments: {len(enrollments.data)}")
for e in enrollments.data:
    print(f"  enrollment_id: {e['id'][:8]}... student: {e['student_id'][:8]}... course: {e['course_id'][:8]}... status: {e['status']}")
