# ARCHITECTURE.md
### Student Engagement & Reminder Automation -- Global Learning Hub, Phase 1

This is the technical specification for this repository. Any code written must conform to this structure. If a change requires deviating from it, that deviation must be discussed and this document updated first -- do not silently drift from it.

---

## Stack

| Layer | Choice |
|---|---|
| Backend | Python + FastAPI |
| Frontend | Next.js (App Router), calls the backend API -- no direct database access from the frontend |
| Database | Supabase (Postgres) -- the ONLY data store. No Google Sheets, no local files, no second source of truth. |
| Scheduling | APScheduler running inside the FastAPI app, or a hosted cron service calling `POST /run-daily-job` |
| Primary delivery | WhatsApp Business Cloud API (Meta) |
| Backup delivery | Telegram Bot API (operator's own channel @DavidAmenuku20) |
| Other channels | Email and SMS adapters exist in code but are NOT wired/active in Phase 1 |

---

## Backend Directory Structure

```
global-learning-hub-automation/
  README.md
  .env.example
  .gitignore
  requirements.txt

  src/
    __init__.py
    main.py                     # FastAPI app entry point
    config.py                   # loads settings/env vars

    api/
      __init__.py
      routes_jobs.py            # POST /run-daily-job
      routes_webhooks.py        # POST /webhooks/{channel}
      routes_reports.py         # GET /reports/today
      routes_health.py          # GET /health

    database/
      __init__.py
      client.py                 # Supabase connection
      models.py                 # Student, Course, Enrollment, ReminderLog
      schema.sql                # table definitions (source of truth for schema)

    channels/
      __init__.py
      base.py                   # abstract Channel interface -- all channels implement this
      whatsapp_channel.py       # ACTIVE (Meta Business Cloud API)
      telegram_channel.py       # BACKUP (Bot API, operator's @DavidAmenuku20)
      email_channel.py          # NOT WIRED in Phase 1
      sms_channel.py            # NOT WIRED in Phase 1

    automation/
      __init__.py
      scheduler.py              # determines who needs a reminder today
      engagement.py             # marks active / low_engagement / needs_followup
      reminder_templates.py     # message text, kept separate from logic

    reports/
      __init__.py
      daily_report.py           # builds and sends "Today's Class Report"

    utils/
      __init__.py
      logger.py

  scripts/
    seed_sample_data.py         # fake students/courses -- used until real-data authorization
    run_daily_job.py            # manual CLI trigger, for local testing

  tests/
    test_scheduler.py
    test_channels.py
    test_reports.py
    test_api.py

  docs/
    ARCHITECTURE.md
    AGENTS.md
    DECISIONS.md
```

## Frontend Directory Structure

```
global-learning-hub-frontend/
  package.json
  .env.local.example
  .gitignore
  next.config.js
  tsconfig.json
  app/
    layout.tsx
    page.tsx                     # home -- today's report
    students/page.tsx            # student list (read-only)
    courses/page.tsx             # course list (read-only)
    run/page.tsx                 # manual "run today's job" button
  components/
    ReportCard.tsx
    StudentTable.tsx
    RunJobButton.tsx
  lib/
    api.ts                       # fetch wrapper for backend endpoints
```

---

## Database Schema

```sql
-- students
create table if not exists students (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  phone      text,
  email      text,
  created_at timestamptz not null default now()
);

-- courses
create table if not exists courses (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  start_date date,
  class_time time,
  created_at timestamptz not null default now()
);

-- enrollments
create table if not exists enrollments (
  id          uuid primary key default gen_random_uuid(),
  student_id  uuid not null references students(id),
  course_id   uuid not null references courses(id),
  status      text not null default 'active',
  enrolled_at timestamptz not null default now()
);

-- engagement_log
create table if not exists engagement_log (
  id                   uuid primary key default gen_random_uuid(),
  enrollment_id        uuid not null references enrollments(id),
  date                 date not null,
  status               text not null default 'active',
  assignment_submitted boolean not null default false,
  updated_at           timestamptz not null default now()
);

-- reminder_log
create table if not exists reminder_log (
  id              uuid primary key default gen_random_uuid(),
  enrollment_id   uuid not null references enrollments(id),
  channel         text not null,
  message         text,
  sent_at         timestamptz not null default now(),
  delivery_status text not null default 'pending'
);
```

Do not add new tables or columns without updating this file first.

---

## Channel Adapter Interface

```python
# channels/base.py
class Channel:
    def send(self, student, message: str) -> bool:
        """Send a message. Return True if sent, False if failed."""
        raise NotImplementedError
```

Every channel implementation (`whatsapp_channel.py`, `telegram_channel.py`, `email_channel.py`, `sms_channel.py`) must implement this exact interface. `scheduler.py` calls only `channel.send(student, message)` -- it must never contain channel-specific logic (no `if channel == "sms"` branching inside the scheduler). The active channel is selected once, in `config.py`, via `ACTIVE_CHANNEL`. The backup is `BACKUP_CHANNEL`.

---

## Daily Flow

```
APScheduler fires (or POST /run-daily-job is called)
        |
        v
scheduler.py -- query today's classes + enrolled active students
        |
        v
engagement.py -- check status, write to engagement_log
        |
        v
reminder_templates.py -- select message per student status
        |
        v
channels/[ACTIVE_CHANNEL].py -- send, write result to reminder_log
        |
        v
daily_report.py -- compile report, send to administrator, expose via /reports/today
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
ACTIVE_CHANNEL=whatsapp
BACKUP_CHANNEL=telegram

WHATSAPP_TOKEN=
WHATSAPP_PHONE_ID=

TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_CHAT_ID=

EMAIL_API_KEY=
ADMIN_EMAIL=
ADMIN_PHONE=

RATE_LIMIT_DELAY_SECONDS=60
JOB_HOUR=8
```

---

## Hosting

- Backend: an always-on host (Railway, Render, or Fly.io) -- required because FastAPI must stay running, unlike a one-off script.
- Frontend: Vercel.
- Database: Supabase (hosted Postgres).
- These choices are fixed for this phase; do not introduce a different hosting approach without discussion.
