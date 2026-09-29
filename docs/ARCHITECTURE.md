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
      weekly_readiness.py       # Phase 2 paid-and-consented channel eligibility check

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
    test_weekly_readiness.py    # synthetic Phase 2 eligibility tests

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

**First-cohort eligibility request (2026-09-28):** The operator set an initial cohort target of no more than 30 learners, limited to learners with verified payment for a course. This applies only to the separate Phase 2 weekly device-readiness notice, not the Phase 1 daily reminders. Payment is never a substitute for separate purpose- and channel-specific opt-in. The local schema below now defines the payment and consent event records; do not infer either from `enrollments.status = active`. Manual administrator verification was selected for the first cohort; do not add a checkout provider. These definitions have not been applied to live Supabase. Until a controlled-pilot authorization and a secure, attributable record-entry process exist, use synthetic data and do not send live messages.

### Phase 2 weekly-notice payment and consent records — local design only

The source schema defines two separate append-only event logs for the weekly device-readiness notice:

- `enrollment_payment_verification_events` records `verified` or `revoked` for a specific enrollment, with the event time and the identifier of the staff member who recorded it. Do not store amounts, bank/card details, receipts, or payment-provider data. An enrollment qualifies only when it is active and its newest event is `verified`; no event, or a newest `revoked` event, fails closed.
- `student_channel_consent_events` records an `opt_in` or `opt_out` for one student, the fixed purpose `device_readiness_weekly`, and one channel. An opt-in records the notice-text version, how the learner expressed consent (`learner_self_service` or `learner_direct_request`), the actor who entered the record, and the event time. Do not store phone numbers, email addresses, or copies of identity documents in this log. The newest event for that exact student/purpose/channel tuple controls; the newest `opt_out` blocks that channel.

Both tables use increasing event IDs so the latest state can be derived without overwriting history. The local schema enables row-level security, grants no access to `anon` or `authenticated`, and grants the backend `service_role` only `SELECT` and `INSERT`; it grants no update/delete permission. Keep the service-role secret on the server. There is no write API in this change. The existing shared `ADMIN_API_KEY` does not identify an individual staff member, so do not treat it as `recorded_by` or build a write route until authenticated actor identity and the approved learner-consent capture path are available. An opt-in must reflect the learner's own explicit choice, never an administrator's assumption.

Student channel preference and fallback order are separate from consent and are not included in these records. Before any live weekly notice, the system must also check the learner's recorded preference, separate consent for each attempted channel, the paid/active enrollment gate, the 30-learner cap, and country/provider approval. This design does not wire a scheduler, provider, or send path and does not change Phase 1. Editing this schema file is not a live migration; no live database change or message is authorized.

**Channel safeguards and open design:** each student must choose a preferred channel and rank any fallback channels; try them in the student's chosen order. Choosing or ranking a channel is not consent. Require a separate opt-in for this message purpose on every channel used, and do not send if the required preference and consent are missing. Attempt a fallback only after a provider-confirmed terminal failure on the current channel, and only if the learner has opted into the fallback; never bypass an opt-out. Pending or unknown delivery status is not failure and must not trigger fallback until reconciled, to avoid duplicates. Provider-specific failure mapping, retry/timeout limits, reconciliation timing, day/time, wording, locale, student-facing status of Telegram, email/SMS providers, country-specific requirements, student-preference capture, consent capture/authentication, deduplication, rate limits, costs, and support remain unresolved. The local schema defines append-only consent and payment events, but no write route or provider is implemented. Do not add providers/dependencies, alter the Phase 1 scheduler, migrate a live database, or send live messages until remaining details are documented and separately approved. This scope decision is not authorization for a real pilot or use of real learner data.

**Global reach research (checked 2026-09-28; providers not selected):** Treat “global” as the intended audience, not as proof every channel works in every country. Twilio's [international SMS guide](https://www.twilio.com/docs/messaging/guides/sending-international-sms-guide) says destination-country A2P rules and sender identities vary. Vonage's [country-specific SMS guide](https://developer.vonage.com/en/messaging/sms/guides/country-specific-features) and [delivery-receipt guide](https://developer.vonage.com/en/messaging/sms/guides/delivery-receipts) document country differences; an API acceptance means queued, and delivery receipts may not be available or conclusive in every market. For email, Amazon SES requires a plan for bounce/complaint handling and new accounts start in a restricted [sandbox](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html); its [sending-activity guidance](https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html) distinguishes delivery, delay, bounce, and complaint events. These official docs support a per-country capability and cost review before enabling routes, not a blanket global claim. Ghana is the first market for readiness review; evaluate provider options only after the country checks below, and do not infer provider choice from this research.

**Ghana first-market readiness (checked 2026-09-28; research only, not legal advice or permission to send):** The Ghana [Data Protection Commission's compliance guidance](https://dpc.gov.gh/compliance/) says registration is required before processing personal data and highlights lawfulness, transparency, data minimisation, and purpose limitation. Before any learner-data pilot, confirm the responsible organisation's registration/status, notices, processor arrangements, data locations/transfers, retention, and age/guardian requirements with the DPC and qualified Ghanaian counsel. The National Communications Authority's [unwanted calls and texts guidance](https://nca.org.gh/2021/08/06/management-of-unwanted-calls-and-text-messages/) says providers should transmit texts only to consumers who consented to the service; the separate per-purpose, per-channel opt-in and opt-out safeguards above remain mandatory project gates. The NCA's [March 2026 international A2P consultation](https://nca.org.gh/2026/03/12/public-consultation-on-regulatory-framework-for-the-management-monitoring-and-monetisation-of-international-application-to-person-a2p-messaging-traffic-in-ghana/) proposed a framework and states the comment period ended 2026-04-10. That page is a consultation, not proof the proposal became a rule; verify the current instrument and routing requirements with the NCA and a locally licensed provider before any SMS integration. As one provider-specific example only, [Twilio's Ghana SMS guidance](https://www.twilio.com/en-us/guidelines/gh/sms) reports alphanumeric Sender ID registration for MTN and states unregistered IDs would be blocked from 2026-07-08; independently confirm current requirements for each network and provider. Meta's [WhatsApp Business Messaging Policy](https://whatsappbusiness.com/policy/?lang=en_US), last updated 2026-09-23, requires permission before messaging and respecting opt-outs; it recommends distinct opt-ins by message category. Business-initiated WhatsApp Platform messages use approved templates, per [Meta's platform overview](https://whatsappbusiness.com/products/business-platform-features/). No channel/provider route is approved or enabled by this research.

**Ghana provider comparison (checked 2026-09-28; recommendation only, not a selection):**

| Channel | Existing or named candidates | Cost and Ghana-specific notes | Assessment |
|---|---|---|---|
| WhatsApp | Direct Meta Cloud API is already used by the Phase 1 adapter; Twilio is an optional intermediary, not selected. | Meta prices delivered messages by recipient market and category; use its [live pricing page](https://whatsappbusiness.com/products/platform-pricing/) at selection time because the Ghana rate/category was not reliably exposed in the reviewed page. Twilio states it adds $0.005 per message on top of Meta's template fee on its [WhatsApp pricing page](https://www.twilio.com/en-us/whatsapp/pricing). | Prefer preserving the existing direct Meta route for a separate Phase 2 adapter if it meets needs; this avoids adding an intermediary, but does not alter Phase 1. Have Meta classify/approve the weekly reminder template and verify the current rate before estimating cost. |
| Email | Amazon SES is the named low-cost candidate. | Current SES pricing lists $0.16 per 1,000 messages on Essentials or $0.10 per 1,000 à la carte. New SES accounts start in a sandbox: recipients must be verified, with limits of 200 messages per 24 hours and 1 per second. Production access requires a verified sender/domain and an explicit-request and bounce/complaint-handling process. See [pricing](https://aws.amazon.com/ses/pricing/) and [sandbox rules](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html). | Lowest published per-message cost among the reviewed options, but requires more AWS setup and a Ghana privacy/data-location review. For illustration, 100 opted-in learners receiving four messages in a month is about $0.064 at Essentials rates, excluding add-ons/other AWS charges. |
| SMS | Compare Twilio and Vonage; neither is selected. | Twilio lists $0.3741 per outbound SMS segment to Ghana and says additional carrier fees may apply. At 100 opted-in learners × 4 weekly reminders per month, assuming one segment per reminder, that is about $149.64 before such fees. [Twilio's Ghana guidance](https://www.twilio.com/en-us/guidelines/gh/sms) requires MTN Sender ID registration. [Vonage's Ghana guidance](https://api.support.vonage.com/hc/en-us/articles/204017233-Ghana-SMS-Features-and-Restrictions) also says MTN pre-registration is mandatory and generic IDs are prohibited; its [pricing instructions](https://developer.vonage.com/en/dashboard/control/pricing) require the account-specific, country/network price table. | Keep SMS available only to learners who choose and separately opt into it; set an approved spend limit before activation. Compare Twilio's current published rate (and any account-specific quote) against Vonage's account-specific rate table, and confirm network registration and the NCA's current A2P position before deciding. Keep message text short because billing is per segment. |

**Practical recommendation:** Keep the student's choice and consent as the routing rule, rather than imposing a universal preferred channel. For the first Ghana readiness pass, use direct Meta as the WhatsApp candidate, SES as the email cost candidate, and compare Twilio's current published rate against Vonage's account-specific rate table before enabling SMS. Do not create provider accounts or configure any integration as part of this comparison. Meta rates and channel terms can change, so re-check them immediately before implementation.

**No-cost pilot option (research recommendation, not an integration decision):** The WhatsApp Business App is free to download and can be used for manual, private one-to-one messages to a small, opted-in cohort; this avoids Business Platform API message fees but is not automated by this program and still requires staff time and internet/data access. Meta's Business Broadcasts feature is limited to eligible users in selected countries, so Ghana availability must be confirmed before relying on it. Do not automate WhatsApp Web. For local software tests, a mocked/no-send channel is the free and safe option. The WhatsApp Business Platform charges per delivered message by market and category; service messages and utility messages sent in response to a user are free, but a proactive weekly notice should be treated as potentially billable and use approved templates when required. See [WhatsApp Business App information](https://faq.whatsapp.com/641572844337957), [Business Broadcast feature availability](https://whatsappbusiness.com/products/business-app-features/), [Platform pricing](https://whatsappbusiness.com/products/platform-pricing/), and the [Business Messaging Policy](https://whatsappbusiness.com/policy/?lang=en_US).

**Existing WhatsApp code check:** `src/channels/whatsapp_channel.py` currently builds a plain `type: text` request. Meta's current [Business Messaging Policy](https://whatsappbusiness.com/policy/?lang=en_US) says business-initiated conversations must use approved templates, and plain replies are permitted only within the 24-hour service window. Therefore the existing sender has not been shown compliant for scheduled outbound reminders outside that window. Resolve and test template handling before any live scheduled send; this review did not modify the code or authorize a send.

**Recommended rollout:** retain a country-by-country approval matrix for each channel (coverage, sender/number registration, provider price, required consent, delivery-status quality, and operational support). Start with Ghana, then add countries after review. Keep the existing Phase 1 WhatsApp daily reminder flow untouched. A route with unverified coverage or unclear delivery state is unavailable for automatic fallback.

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
