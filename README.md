# Global Learning Hub — Reminder & Engagement Automation (Phase 1)

The first automation for the Global Learning Hub learning-hub operation:
a daily job that sends class reminders to students and reports engagement
to the administrator.

**Read first:** `docs/AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`.
Those three files are the source of truth for this repository.

## What it does

1. Every day a scheduled job figures out which students need a reminder.
2. It sends that reminder through exactly **one** delivery channel
   (currently `email`).
3. It logs every send to `reminder_log` and to a log file.
4. It marks students as `active` / `low_engagement` / `needs_followup`.
5. It builds and sends a daily engagement report to the administrator.

## Stack

- Backend: Python + FastAPI
- Database: Supabase (Postgres) — the only data store
- Scheduling: APScheduler
- Delivery: a single active channel, chosen in `config.py`

## Quick start (local, fake data only)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # then fill in placeholders with your real values, or leave for dry-run
python scripts\seed_sample_data.py   # inserts FAKE students/courses — no real data
python scripts\run_daily_job.py      # runs today's job manually, logs results
uvicorn src.main:app --reload        # start the API
```

> **No real student data or live sends happen until the operator explicitly
> authorizes the Week 3 controlled pilot.** Everything uses fake data until
> then. If you're unsure, ask.

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Uptime check |
| `/run-daily-job` | POST | Manually triggers the full daily flow |
| `/webhooks/{channel}` | POST | Receives delivery-status callbacks |
| `/reports/today` | GET | Today's engagement report as JSON |

See `docs/ARCHITECTURE.md` for the full specification.
