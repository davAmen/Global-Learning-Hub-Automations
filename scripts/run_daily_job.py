"""Manual CLI trigger for the daily job. For local testing only."""

from src.database import get_db
from src.automation.scheduler import send_reminders


def main():
    db = get_db()
    sent = send_reminders(db)
    print(f"Daily job complete. Reminders sent: {sent}")


if __name__ == "__main__":
    main()
