# Global Learning Hub — Reminder & Engagement Automation (Phase 1)

The first automation for the Global Learning Hub learning-hub operation:
a daily job that sends class reminders to students and reports engagement
to the administrator.

**Read first:** `docs/AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`.
Those three files are the source of truth for this repository.

The requested learning platform expansion is specified in `docs/PLATFORM_BRIEF.md`.
The current code is the reminder service, not a deployed course marketplace.

## What it does

1. Every day a scheduled job figures out which students need a reminder.
2. It sends that reminder through exactly **one** delivery channel
   (currently `whatsapp`).
3. It logs every send to `reminder_log` and to a log file.
4. It marks students as `active` / `low_engagement` / `needs_followup`.
5. It builds a daily engagement report and sends it to the configured Telegram administrator chat during scheduled runs.

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

> **Use synthetic student data and test credentials only until a controlled pilot is explicitly authorized.** A configured provider credential can send live messages, so leave provider tokens unset during local tests.

Set a long random `ADMIN_API_KEY` in `.env` and send it in the `X-Admin-Key`
header for `/run-daily-job` and `/reports/today`. Never expose that key in a
public web page. The delivery webhook currently responds 501 until signed
provider payload verification and provider-message-ID mapping are built.

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Uptime check |
| `/run-daily-job` | POST | Manually triggers the full daily flow |
| `/webhooks/{channel}` | POST | Receives delivery-status callbacks |
| `/reports/today` | GET | Today's engagement report as JSON |

See `docs/ARCHITECTURE.md` for the full specification.
