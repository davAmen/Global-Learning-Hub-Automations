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

### Approved hybrid architecture direction (2026-09-27; implementation details open)

The operator confirmed this high-level operating and synchronization model on 2026-09-27. This approves local-versus-cloud record authority by origin, separate local and remote operation during a site outage, and an application-level outbox with stable event IDs, acknowledgements, duplicate-safe retries, per-origin ordering, and teacher review of conflicts. It does not select a database, vendor, authentication method, deployment, or authorize code, a real pilot, or real learner data.

Research basis: existing offline-learning systems show local-first learning can work, but offline feature support and synchronization limits must be tested explicitly: [Kolibri's user guide](https://kolibri.readthedocs.io/en/latest/) describes LAN-served offline learning, and its developer docs describe facility sync with certificate-based authentication and change tracking; [Moodle's offline feature guide](https://docs.moodle.org/501/en/Moodle_app_offline_features) documents unsupported activities and notes that some offline actions are recorded at sync time rather than when they occurred. Use these as benchmarks, not as proof that our custom platform is better.

**Approved operating model:** Treat the site's hub as the authority for records created by the on-site class, and the cloud service as the authority for records created by remote learners while online. During a site internet outage, the on-site class continues on its LAN; remote learners may still reach the independently hosted cloud service and do remote/cloud work, but that is a separate online activity—not a live connection to the disconnected room. Do not combine attendance across the two modes without clearly identifying the session and source. If the requirement is to keep the same teacher and remote learners together live through a site outage, the site needs an independent backup internet path; application sync cannot replace a missing network route.

**Approved high-level synchronization model:** Use a small application-level outbox, not general-purpose multi-master editing. When the hub records an offline action, it saves the record and its pending sync event together. Each event carries a stable unique ID, origin site, session, actor, action, local occurrence time/time zone, server receipt time when known, and a per-origin sequence. On reconnection, the hub sends pending events; the cloud stores each event once by ID and acknowledges it; the hub clears only acknowledged events and retries safely after a lost response. This is at-least-once delivery with idempotent processing, not a promise of exactly-once network delivery. The [IETF HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) caution against automatic retries when a request is not idempotent; AWS's [transactional outbox guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) describes durable event records, duplicate handling, and ordering considerations.

Treat corrections as new, attributed amendments to the original record. Preserve both versions and route disagreements to a teacher; never apply last-write-wins to attendance. Cache approved, versioned course resources at the hub before class. Keep event origin and source timestamps visible, because device clocks and synchronization times are not interchangeable.

**Technology boundaries:** Do not assume hosted Supabase provides classroom-hub offline synchronization. Its [documented database replication](https://supabase.com/docs/guides/database/replication) focuses on Postgres replicas and change-data-capture pipelines, not this application's record ownership and conflict workflow; that conclusion is an inference from the documented scope. Do not introduce a second database or select a sync library until this relationship is approved. If SQLite is considered for a single hub process, clients must reach it through the app/API; SQLite's [official guidance](https://www.sqlite.org/useovernet.html) warns against opening one database file directly from multiple computers over a network share. Apache CouchDB demonstrates replication but its [conflict model](https://docs.couchdb.org/en/stable/replication/conflicts.html) still requires application-level resolution, so selecting a replicating database alone would not solve attendance correctness.

For the first synthetic-data pilot, test: (1) download approved class resources, (2) disconnect the site's WAN but keep its Wi-Fi/LAN active, (3) record check-ins and work locally, (4) restart the hub while still offline, (5) reconnect and force a retry after an acknowledgement is lost, and (6) create a conflicting teacher correction and verify it is held for review. Pass only if records survive restart, repeated sync creates no duplicates, source/times remain visible, and no record silently disappears or changes owner. Do not use real learner data until separately authorized.

### Offline identity and sign-in — recommendation pending operator approval

**Device direction confirmed by the operator (2026-09-27):** learners should use devices they own rather than relying on a shared classroom device. Treat this as a BYOD preference, not a decision about phones versus tablets/computers, native app versus browser, or an assumption that every learner has a suitable, charged device. Device support and a fallback for learners without access remain to be planned; this does not authorize a pilot.

**Device-readiness policy confirmed by the operator (2026-09-27):** send one weekly reminder for learners to charge their own devices for class, and use a school-provided device where one is available. The operator explicitly expanded the Phase 2 scope on 2026-09-27: the notice should reach learners across approved student-facing channels, including WhatsApp, email, SMS, and future approved channels. This is a separate addition; do not alter the Phase 1 daily reminder's WhatsApp active channel or Telegram backup.

**Channel safeguards and open design:** the operator selected preferred-channel-first delivery with fallback rather than simultaneous delivery. Attempt a fallback only when the preferred channel has a defined failure, and only if the learner has opted into that channel for this purpose; an opt-out must never be bypassed. For an ambiguous delivery status, define how to verify the result before falling back so the student does not receive duplicates. Channel priority, failure/unknown-status rules, day/time, wording, locale, student-facing status of Telegram, email/SMS providers, country-specific requirements, consent/preference records, duplicate prevention, retry, audit, rate limits, costs, and support remain unresolved. Do not add providers/dependencies, alter schemas or the Phase 1 scheduler, or send live messages until these details are documented and separately approved. This scope decision is not authorization for a real pilot or use of real learner data.

**Recommended for the first synthetic pilot:** establish each account through an approved online enrollment process before the outage, then provision only the active class roster and required credential-verification data to the site hub. The hub should authenticate learners locally during the outage; it must not depend on a live cloud login. Every learner and teacher gets an individual account. A student number, shared class password, or QR code by itself is not proof of identity.

Use protected password verifiers rather than storing passwords, throttle failed attempts, and require a clear sign-out and risk-appropriate session limits even on personal devices (a device may be shared within a household). Prefer keeping sensitive roster and attendance records on the hub instead of unnecessarily copying them to learner devices; exact session and cache rules remain open. OWASP recommends adaptive password hashing (Argon2id, or scrypt if Argon2id is unavailable) and login throttling; NIST guidance says session lifetime and reauthentication depend on risk and that compromised authenticators should be invalidated promptly. See [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [OWASP authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html), and [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html). No new authentication library or password-hashing dependency is selected by this recommendation.

**Important offline limit:** while disconnected, the hub cannot learn that a cloud administrator just disabled an account. For a small first pilot, I recommend authorizing the cached class roster only for the scheduled class/day; after that, keep approved course materials available read-only but stop new verified attendance writes until authorization is refreshed. This is a conservative proposal, not an adopted expiry policy. Longer offline authorization improves continuity but increases the time a stale account might still work; site-local revocation is another option but adds a second authority that must later reconcile.

Do not allow new account enrollment, password reset, role changes, or verified attendance based only on a student number while offline. If a learner cannot sign in, record an exception for later human review rather than impersonating the learner. Before real-data use, decide learner age range, supported device types and fallback access, the enrollment/identity-verification process, account recovery, the acceptable offline authorization window, and how local account disable/revocation works. Use synthetic accounts until those decisions are approved.

### Proposed first pilot workflow — not approved for implementation

Use one learning site and one class as a provisional planning assumption only. This is not confirmation that a pilot has started or that real learner data may be used. Begin any build/test with synthetic accounts and records; obtain separate approval before a controlled pilot with real learners.

1. **Prepare while online:** a teacher signs in to the online service, selects the class, and makes approved, rights-cleared lesson materials available to that site's hub. The hub shows whether required materials and the minimum necessary class roster are ready for local use.
2. **Teach on the local network:** learners and the teacher connect to the site's LAN and sign in with verified accounts. A learner deliberately checks in; the teacher can correct an attendance record with a reason and an audit entry. Exercise and assignment submissions are recorded as learning evidence, not treated as attendance or proof of attention.
3. **Continue through an internet outage:** devices that can still reach the local hub may use already available materials and create class records there. The interface must plainly show local-only operation and unsynchronized changes. A device that cannot reach the local hub cannot submit through it; remote learners without another network path cannot join that live local session.
4. **Reconnect and synchronize:** the approved high-level direction is for the hub to keep each locally created event until the online service acknowledges it, retry unacknowledged events, and let the online service recognize a repeated event without creating a duplicate. Use stable event identity and preserve origin/history. A sync must never silently replace a hub-owned offline record with a cloud copy.
5. **Handle disagreement visibly:** if a remote edit or another record conflicts with a locally owned attendance event, retain both histories and place the case in a teacher review queue. Do not resolve attendance by “last write wins,” silently change a learner's status, or send a disciplinary message automatically. Show pending/failed sync counts and last successful sync time to an authorized teacher.
6. **Close the class:** the teacher reviews missing, corrected, and unsynchronized records. Any four-absence threshold may create a supportive human-review item only; it is not an automatic withdrawal. Any WhatsApp message requires its own purpose-specific permission and approved sending flow; this attendance design does not authorize a live message.

These steps describe approved product direction, not a selected database, API, authentication vendor, or deployed sync protocol. Before implementation, review and approve the pilot scope and settle account enrollment/recovery and offline-authorization expiry, data minimization and consent, session/timezone and attendance states, exact event schema/transport security, correction audit, encryption, backup/restore, and hub operations. The one-site/one-class scope remains provisional; do not use real learner data, add attendance/platform tables or endpoints, or run live synchronization until the remaining design and pilot are explicitly approved. Keep the Phase 1 reminder database and service separate and unchanged.

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
