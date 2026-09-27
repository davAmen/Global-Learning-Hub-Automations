# ARCHITECTURE.md
> The Phase 1 implementation below remains current. `PLATFORM_BRIEF.md` records the approved product expansion, and `MASTER_PROMPT.md` sequences it with the operator's additional attendance, classroom-agent, marketing, and partnership goals. This roadmap does not itself activate later-phase implementation. New tables, providers, frontend locations, and public endpoints require documented designs before code is changed; deployment, live database migrations, and other external actions require separate approval.
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

`reminder_log.enrollment_id` is nullable for administrator-level report delivery attempts that are not associated with one student enrollment. Updating this SQL file does not migrate an existing Supabase database; that requires separate explicit authorization.

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
  enrollment_id   uuid references enrollments(id),
  channel         text not null,
  message         text,
  sent_at         timestamptz not null default now(),
  delivery_status text not null default 'pending'
);
```

Do not add new tables or columns without updating this file first.

---

## Phase 2 — Hybrid local and remote class platform (design target)

On 2026-09-27, the operator selected an owned class platform for local classroom use plus remote online access. The intended local arrangement is a classroom server reachable over a local Wi-Fi/LAN network even when that network has no internet connection. Remote learners and other sites require an internet or private-network path; a local hub cannot provide a live session to disconnected remote users.

This target supersedes the earlier proposal to use WhatsApp group management as the classroom platform. Keep the existing Phase 1 WhatsApp reminder service unchanged unless separately reconsidered. The word “interlink” has not been confirmed as a particular product or technology; until clarified, interpret the network requirement as a local LAN/intranet.

**Decision:** each site's local hub is the planned authority for class records created at that site while offline; it sends those records to the remote online service when connectivity returns. This choice does not change the Phase 1 Supabase schema or authorize a live database change.

**Still to design before implementation:** local persistence technology; how remote-origin records are owned; durable event IDs, acknowledgements and idempotent retries; ordering and clock handling; how conflicting teacher corrections are reviewed without silently overwriting the local record; local account and access control; encryption; backup/restore; and hub update/operations. Phase 1 currently specifies Supabase as its only database and does not provide offline writes. Do not add a second database, schema, endpoints, or platform screens until the relationship between local storage and the remote service is documented and approved. Do not run live cross-site synchronization or expose real learner data during development.

The initial platform scope is classroom teaching and learning: teacher-managed lesson/resource delivery, learner activities, and transparent attendance/participation. Keep the public marketplace, billing, marketing, partnerships, and autonomous AI administration in their later roadmap phases. Attendance must be an explicit, consent-based record, require verified identity, and remain separate from assignment/exercise completion. A teacher must be able to correct records with an audit trail; no automatic withdrawal.

**Research checked 2026-09-27:** Offline learning is not itself a new product category. Ghana's [CENDLOS iBox](https://cendlos.gov.gh/innovation) describes offline educational browsing, assessment, and resource sharing; [Kolibri](https://learningequality.org/kolibri/about-kolibri/) is designed to serve learners over a LAN without internet and distribute content offline; [Moodle's mobile app](https://docs.moodle.org/501/en/Moodle_app_offline_features) supports downloaded offline course work but documents unsupported activities and synchronization limitations. These are learning references, not endorsements or evidence that this project will outperform them. Do not claim “world first” or superior outcomes without validation.

### Research-informed architecture recommendation — pending operator approval

The following is a recommendation, not an adopted platform or database decision. Existing offline-learning systems are evidence that local-first learning can work, but also show that offline feature support and synchronization limits must be tested explicitly: [Kolibri's user guide](https://kolibri.readthedocs.io/en/latest/) describes a LAN-served offline learning platform, and its developer docs describe facility sync with certificate-based authentication and change tracking; [Moodle's offline feature guide](https://docs.moodle.org/501/en/Moodle_app_offline_features) documents unsupported activities and notes that some offline actions are recorded at sync time rather than when they occurred. Use these as benchmarks, not as proof that our custom platform is better.

**Recommended operating model:** Treat the site's hub as the authority for records created by the on-site class, and the cloud service as the authority for records created by remote learners while online. During a site internet outage, the on-site class continues on its LAN; remote learners may still reach the independently hosted cloud service and do remote/cloud work, but that is a separate online activity—not a live connection to the disconnected room. Do not combine attendance across the two modes without clearly identifying the session and source. If the requirement is to keep the same teacher and remote learners together live through a site outage, the site needs an independent backup internet path; application sync cannot replace a missing network route.

**Recommended synchronization model:** Use a small application-level outbox, not general-purpose multi-master editing. When the hub records an offline action, it saves the record and its pending sync event together. Each event carries a stable unique ID, origin site, session, actor, action, local occurrence time/time zone, server receipt time when known, and a per-origin sequence. On reconnection, the hub sends pending events; the cloud stores each event once by ID and acknowledges it; the hub clears only acknowledged events and retries safely after a lost response. This is at-least-once delivery with idempotent processing, not a promise of exactly-once network delivery. The [IETF HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) caution against automatic retries when a request is not idempotent; AWS's [transactional outbox guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) describes durable event records, duplicate handling, and ordering considerations.

Treat corrections as new, attributed amendments to the original record. Preserve both versions and route disagreements to a teacher; never apply last-write-wins to attendance. Cache approved, versioned course resources at the hub before class. Keep event origin and source timestamps visible, because device clocks and synchronization times are not interchangeable.

**Technology boundaries:** Do not assume hosted Supabase provides classroom-hub offline synchronization. Its [documented database replication](https://supabase.com/docs/guides/database/replication) focuses on Postgres replicas and change-data-capture pipelines, not this application's record ownership and conflict workflow; that conclusion is an inference from the documented scope. Do not introduce a second database or select a sync library until this relationship is approved. If SQLite is considered for a single hub process, clients must reach it through the app/API; SQLite's [official guidance](https://www.sqlite.org/useovernet.html) warns against opening one database file directly from multiple computers over a network share. Apache CouchDB demonstrates replication but its [conflict model](https://docs.couchdb.org/en/stable/replication/conflicts.html) still requires application-level resolution, so selecting a replicating database alone would not solve attendance correctness.

For the first synthetic-data pilot, test: (1) download approved class resources, (2) disconnect the site's WAN but keep its Wi-Fi/LAN active, (3) record check-ins and work locally, (4) restart the hub while still offline, (5) reconnect and force a retry after an acknowledgement is lost, and (6) create a conflicting teacher correction and verify it is held for review. Pass only if records survive restart, repeated sync creates no duplicates, source/times remain visible, and no record silently disappears or changes owner. Do not use real learner data until separately authorized.

### Proposed first pilot workflow — not approved for implementation

Use one learning site and one class as a provisional planning assumption only. This is not confirmation that a pilot has started or that real learner data may be used. Begin any build/test with synthetic accounts and records; obtain separate approval before a controlled pilot with real learners.

1. **Prepare while online:** a teacher signs in to the online service, selects the class, and makes approved, rights-cleared lesson materials available to that site's hub. The hub shows whether required materials and the minimum necessary class roster are ready for local use.
2. **Teach on the local network:** learners and the teacher connect to the site's LAN and sign in with verified accounts. A learner deliberately checks in; the teacher can correct an attendance record with a reason and an audit entry. Exercise and assignment submissions are recorded as learning evidence, not treated as attendance or proof of attention.
3. **Continue through an internet outage:** devices that can still reach the local hub may use already available materials and create class records there. The interface must plainly show local-only operation and unsynchronized changes. A device that cannot reach the local hub cannot submit through it; remote learners without another network path cannot join that live local session.
4. **Reconnect and synchronize:** proposed safe behavior is for the hub to keep each locally created event until the online service acknowledges it, retry unacknowledged events, and let the online service recognize a repeated event without creating a duplicate. Use stable event identity and preserve origin/history. A sync must never silently replace a hub-owned offline record with a cloud copy.
5. **Handle disagreement visibly:** if a remote edit or another record conflicts with a locally owned attendance event, retain both histories and place the case in a teacher review queue. Do not resolve attendance by “last write wins,” silently change a learner's status, or send a disciplinary message automatically. Show pending/failed sync counts and last successful sync time to an authorized teacher.
6. **Close the class:** the teacher reviews missing, corrected, and unsynchronized records. Any four-absence threshold may create a supportive human-review item only; it is not an automatic withdrawal. Any WhatsApp message requires its own purpose-specific permission and approved sending flow; this attendance design does not authorize a live message.

These steps describe product behavior, not a selected database, API, sync protocol, or authentication vendor. Before implementation, the operator must review and approve the pilot scope and settle learner/teacher identity and offline access, data minimization and consent, session/timezone and attendance states, remote learner submissions, ownership of each record type, event identifiers/order, retry/acknowledgement behavior, conflict correction, encryption, backup/restore, and hub operations. Until then, do not add attendance/platform tables, endpoints, UI, or live synchronization. Keep the Phase 1 reminder database and service separate and unchanged.

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
