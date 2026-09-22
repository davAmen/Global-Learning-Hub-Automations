"""Clear all test data and re-seed."""
import sys
sys.path.insert(0, ".")
from src.database import get_db

db = get_db()

# Clear old data
db.table("reminder_log").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
db.table("enrollments").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
db.table("students").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
db.table("courses").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

print("Cleared all test data.")
