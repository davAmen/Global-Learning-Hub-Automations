# ARCHITECTURE.md
### Student Engagement & Reminder Automation — Global Learning Hub, Phase 1

This is the technical specification for this repository. Any code written must conform to this structure. If a change requires deviating from it, that deviation must be discussed and this document updated first — do not silently drift from it.

---

## Stack

| Layer | Choice |
|---|---|
| Backend | Python + FastAPI |
| Frontend | Next.js (App Router), calls the backend API — no direct database access from the frontend |
| Database | Supabase (Postgres) — the ONLY data store. No Google Sheets, no local files, no second source of truth. |
| Scheduling | APScheduler running inside the FastAPI app, or a hosted cron service calling `POST /run-daily-job` |
| Delivery | Pluggable channel adapter — see `DECISIONS.md` for which single channel is active |

---

## Backend Directory Structure

```
backend/
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
│
├── src/
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # loads settings/env vars
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_jobs.py           # POST /run-daily-job
│   │   ├── routes_webhooks.py       # POST /webhooks/{channel}
│   │   ├── routes_reports.py        # GET /reports/today
│   │   └── routes_health.py         # GET /health
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── client.py                # Supabase connection
│   │   ├── models.py                # Student, Course, Enrollment, ReminderLog
│   │   └── schema.sql               # table definitions (source of truth for schema)
│   │
│   ├── channels/
│   │   ├── __init__.py
│   │   ├── base.py                  # abstract Channel interface — all channels implement this
│   │   ├── sms_channel.py
│   │   ├── email_channel.py
│   │   └── whatsapp_channel.py      # only the ACTIVE_CHANNEL from config is wired live
│   │
│   ├── automation/
│   │   ├── __init__.py
│   │   ├── scheduler.py             # determines who needs a reminder today
│   │   ├── engagement.py            # marks active / low_engagement / needs_followup
│   │   └── reminder_templates.py    # message text, kept separate from logic
│   │
│   ├── reports/
│   │   ├── __init__.py
│   │   └── daily_report.py          # builds and sends "Today's Class Report"
│   │
│   └── utils/
│       ├── __init__.py
│       └── logger.py
│
├── scripts/
│   ├── seed_sample_data.py          # fake students/courses — used until real-data authorization
│   └── run_daily_job.py             # manual CLI trigger, for local testing
│
├── tests/
│   ├── test_scheduler.py
│   ├── test_channels.py
│   ├── test_reports.py
│   └── test_api.py
│
└── docs/
    ├── ARCHITECTURE.md              # this file
    ├── AGENTS.md
    └── DECISIONS.md
```

## Frontend Directory Structure

```
frontend/
├── package.json
├── .env.local.example
├── app/
│   ├── page.tsx                     # home — today's report
│   ├── students/page.tsx            # student list (read-only)
│   ├── courses/page.tsx             # course list (read-only)
│   ├── run/page.tsx                 # manual "run today's job" button — the ONLY write action in the frontend
│   └── layout.tsx
├── components/
│   ├── ReportCard.tsx
│   ├── StudentTable.tsx
│   └── RunJobButton.tsx
└── lib/
    └── api.ts                       # fetch wrapper for backend endpoints
```

---

## Database Schema

```sql
-- students
id            uuid primary key
name          text
phone         text
email         text
created_at    timestamp

-- courses
id            uuid primary key
name          text
start_date    date
class_time    time
created_at    timestamp

-- enrollments
id            uuid primary key
student_id    uuid references students(id)
course_id     uuid references courses(id)
status        text        -- active / inactive
enrolled_at   timestamp

-- engagement_log
id              uuid primary key
enrollment_id   uuid references enrollments(id)
date            date
status          text       -- active / low_engagement / needs_followup
assignment_submitted  boolean
updated_at      timestamp

-- reminder_log
id              uuid primary key
enrollment_id   uuid references enrollments(id)
channel         text        -- sms / email / whatsapp
message         text
sent_at         timestamp
delivery_status text        -- sent / failed / pending
```

Do not add new tables or columns without updating this file first.

---

## Channel Adapter Interface

```python
# channels/base.py
class ReminderChannel:
    def send(self, student, message: str) -> bool:
        """Send a message. Return True if sent, False if failed."""
        raise NotImplementedError
```

Every channel implementation (`sms_channel.py`, `email_channel.py`, `whatsapp_channel.py`) must implement this exact interface. `scheduler.py` calls only `channel.send(student, message)` — it must never contain channel-specific logic (no `if channel == "sms"` branching inside the scheduler). The active channel is selected once, in `config.py`, via `ACTIVE_CHANNEL`.

---

## Daily Flow

```
APScheduler fires (or POST /run-daily-job is called)
        │
        ▼
scheduler.py — query today's classes + enrolled active students
        │
        ▼
engagement.py — check status, write to engagement_log
        │
        ▼
reminder_templates.py — select message per student status
        │
        ▼
channels/[ACTIVE_CHANNEL].py — send, write result to reminder_log
        │
        ▼
daily_report.py — compile report, send to administrator, expose via /reports/today
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Uptime check |
| `/run-daily-job` | POST | Manually triggers the full daily flow |
| `/webhooks/{channel}` | POST | Receives delivery-status callbacks from the provider; updates `reminder_log` |
| `/reports/today` | GET | Returns today's engagement report as JSON |

---

## Configuration

`.env` (never committed; `.env.example` documents the shape with placeholder values only):
```
SUPABASE_URL=
SUPABASE_KEY=
ACTIVE_CHANNEL=
SMS_API_KEY=
EMAIL_API_KEY=
WHATSAPP_API_KEY=
ADMIN_EMAIL=
ADMIN_PHONE=
```

---

## Hosting

- Backend: an always-on host (Railway, Render, or Fly.io) — required because FastAPI must stay running, unlike a one-off script.
- Frontend: Vercel.
- These choices are fixed for this phase; do not introduce a different hosting approach without discussion.
