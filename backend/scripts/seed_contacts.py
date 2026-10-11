"""Seed the provided WhatsApp class contacts as students."""

import uuid
from datetime import datetime

from src.database import get_db


def seed_contacts():
    db = get_db()

    # Provided contacts
    contacts = [
        "+233 20 230 3143", "+233 20 319 7048", "+233 20 569 2091", "+233 20 595 3215",
        "+233 24 089 3033", "+233 24 098 1548", "+233 24 274 2593", "+233 24 368 9287",
        "+233 24 390 6252", "+233 24 403 2515", "+233 24 479 2152", "+233 24 491 3340",
        "+233 24 494 2660", "+233 24 512 7699", "+233 24 522 3605", "+233 24 526 5075",
        "+233 24 549 2774", "+233 24 634 2049", "+233 24 676 2861", "+233 24 727 8294",
        "+233 24 787 7181", "+233 24 800 0596", "+233 24 804 0626", "+233 24 805 9394",
        "+233 24 810 9174", "+233 24 875 2771", "+233 24 882 6182", "+233 24 914 0820",
        "+233 24 914 7503", "+233 24 923 2924", "+233 24 938 6621", "+233 24 944 9692",
        "+233 24 962 3243", "+233 24 963 7091", "+233 25 744 2120", "+233 26 483 7701",
        "+233 26 518 5031", "+233 27 262 6466", "+233 27 284 3223", "+233 27 377 1665",
        "+233 27 786 1874", "+233 50 423 0796", "+233 50 745 0461", "+233 50 848 5422",
        "+233 53 820 8434", "+233 53 999 2123", "+233 54 102 0326", "+233 54 135 7379",
        "+233 54 189 7224", "+233 54 242 0720", "+233 54 320 9023", "+233 54 411 4198",
        "+233 54 480 6171", "+233 54 626 9342", "+233 54 675 1762", "+233 54 683 8544",
        "+233 54 735 8187", "+233 54 772 8563", "+233 54 813 2267", "+233 54 823 0762",
        "+233 54 982 7694", "+233 55 083 9099", "+233 55 141 1120", "+233 55 220 5739",
        "+233 55 277 8232", "+233 55 611 3449", "+233 55 655 8863", "+233 55 741 5788",
        "+233 55 741 7981", "+233 55 829 8141", "+233 55 833 2056", "+233 55 874 4637",
        "+233 55 875 3777", "+233 55 986 2391", "+233 57 281 0000", "+233 57 419 1765",
        "+233 59 277 9591", "+233 59 441 6356", "+233 59 483 0697", "+233 59 875 3568",
        "+233 59 911 2483", "+233 59 989 3999", "+256 704 902934",
    ]

    students = []
    for i, phone in enumerate(contacts):
        # Normalize phone number
        clean_phone = phone.replace(" ", "")
        students.append({
            "id": str(uuid.uuid4()),
            "name": f"Student {i+1}",
            "phone": clean_phone,
            "email": f"student{i+1}@example.com",
            "created_at": datetime.now().isoformat(),
        })

    for s in students:
        db.table("students").upsert(s, on_conflict="id").execute()

    print(f"Seeded {len(students)} students.")

    # Also enroll them in today's courses
    from datetime import date
    courses_resp = db.table("courses").select("id").eq("start_date", date.today().isoformat()).execute()
    courses = courses_resp.data or []
    
    if courses:
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
        print(f"Enrolled {len(enrollments)} students in {len(courses)} courses.")
    else:
        print("No courses found for today - skipping enrollment.")


if __name__ == "__main__":
    seed_contacts()