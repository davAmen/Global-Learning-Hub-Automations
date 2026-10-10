# AGENTS.md
### Instructions for any AI coding agent working in this repository

Read this file, `ARCHITECTURE.md`, and `DECISIONS.md` in full before writing or changing any code. These three files are the source of truth for this project -- not assumptions, not "best practice," not what a similar project usually looks like.

---

## 1. What This Project Is

A daily automation that sends class reminders to students and reports engagement to the administrator (David). It is the FIRST of several planned automations for a larger learning-hub operation -- but only this one is being built right now.

**The person directing you is non-technical.** He is learning by doing this with your help -- do not assume he understands infrastructure, APIs, or code unless he demonstrates it in the conversation. Explain briefly what you're doing and why when it isn't obvious, but do not lecture at length unprompted.

---

## 2. Active Phase Boundary -- Read This Before Building Anything

The operator activated Phase 2 (consent-based attendance) on 2026-09-27, then selected an owned class platform that supports local classroom use and remote access when online. On 2026-09-27 the operator confirmed the high-level hybrid and sync direction recorded in `ARCHITECTURE.md` and `DECISIONS.md`: site hubs own records created locally, the cloud owns remote-origin records, and reconnection uses an acknowledged, duplicate-safe event outbox with human review of conflicts. The operator has also added a separate weekly device-readiness notice to Phase 2 with a multi-channel, worldwide reach goal, including WhatsApp, email, SMS, and future approved channels. Ghana is the first country for readiness review, not an enabled delivery route. This is additive: preserve the Phase 1 WhatsApp daily reminder service. Telegram currently targets the administrator's chat for reports and is not a safe learner fallback. The operator approved local-only implementation of an online Supabase Auth identity and record-capture API for this notice. It does not select providers, authorize a live database migration, real accounts/data, attendance APIs, offline class-platform sign-in, live sends, or pushes. On 2026-10-07, the operator separately approved a narrow public-entry milestone: a static `/learn` page and a QR that carries only its URL. This is not the class platform and does not add sign-in, attendance, learner records, payments, or social-account connectors. On 2026-10-10, the operator explicitly authorized production deployment of the existing public-entry frontend only; this does not authorize deployment of the backend, database changes, real learner data, messaging, or later-phase features. A worldwide QR needs a stable public HTTPS host; local QR use is limited to devices that can reach that LAN host. A worldwide goal is not blanket country coverage: assess and enable destinations individually, based on provider reach, local rules, sender registration, delivery reporting, cost, and consent. Notices must respect per-purpose, per-channel consent and opt-outs. Treat “local” as a classroom LAN/intranet that still connects devices to a nearby server; remote sites cannot join a live local session while disconnected. Before class-platform attendance/authentication changes, settle offline identity/access and expiry, session/status rules, correction audit, retention, security, provider/jurisdiction requirements, and recovery in `ARCHITECTURE.md` and `DECISIONS.md`. This QR page is the only Phase 4 work activated; do not start other Phase 3, Phase 4, or later work until the operator explicitly activates it.

**Phase 1 baseline to preserve without expanding it during Phase 2:**
- Student, course, and enrollment data in Supabase (see `ARCHITECTURE.md` for schema)
- A daily scheduled job that determines who needs a reminder
- Sending that reminder through exactly ONE delivery channel (WhatsApp active); Telegram is for administrator reports only unless a safe learner destination is separately designed and approved
- A daily report of engagement, sent to the administrator
- A simple Next.js frontend that displays this data and can manually trigger the job -- nothing more

**Active Phase 2 boundary:**
- Design an owned classroom platform for teachers and learners to share lessons/resources and complete classroom activities, usable on a local LAN without internet and remotely when internet is available.
- Prefer learners' own devices (BYOD); do not assume every learner has the same device or select a native app/browser architecture yet. Plan accessible fallback access before any pilot.
- Include one weekly device-readiness notice asking learners to charge their devices for class and use a school-provided device where available. The intended audience is global; Ghana is the first market for readiness review, and no route is enabled until its country-specific provider, sender-registration, cost, policy, and legal checks are complete. Each student must choose a preferred student-facing channel and rank any fallback channels; try them in that order. Choosing or ranking channels is not consent: require a separate opt-in for this purpose on every channel used, and do not send until preference and consent are recorded. Candidate channels include WhatsApp, email, SMS, and future approved channels. Use fallback only after a provider-confirmed terminal failure; pending or unknown delivery status is not failure. Preferences are stored as append-only ordered snapshots, separate from per-channel consent events. Never bypass an opt-out or send simultaneously across channels. Provider status mapping, retry/timeout rules, provider, day/time, and approved consent wording remain open. No live send is authorized.
- The operator's first cohort target is at most 30 learners with verified paid course enrollment. Payment for this cohort will be manually verified; do not add a checkout provider. This applies only to the additive Phase 2 weekly notice; preserve the Phase 1 daily reminder unchanged. Local-only write routes use Supabase Auth-verified identities and a server-managed `app_user_profiles` role/student mapping: staff may record payment events and learner-reported consent; learners may record consent and preference for only their linked student account. The API derives `recorded_by` from the verified account and never accepts it or a learner's identity from request bodies. The schema includes append-only payment, consent, and preference events; it has not been migrated live. Do not create or assign real accounts/data until separately authorized. Never infer paid status or consent from an active enrollment. Record consent only after the learner explicitly opts in for the specific notice and channel. Use synthetic identities/data until a controlled-pilot authorization is in place.
- Keep attendance explicit, consent-based, and separate from assignment/exercise evidence. Require verified identity and auditable teacher corrections; do not infer attendance or active learning from presence, message counts, read receipts, or passive device signals.
- The high-level sync direction is documented and approved; exact event fields, transport security, offline credential freshness/expiry, session/status rules, correction audit, consent/notice, retention, and recovery remain open. Do not add attendance/platform schema, APIs, or screens until those implementation decisions and the pilot scope are documented and approved. Supabase Auth in the notice-recording API is online-only and does not resolve offline class-platform sign-in or authorize attendance features.
- A disconnected local hub can serve only devices connected to its local network; remote teaching during an internet outage is not promised.
- Four consecutive absences may trigger supportive contact and human review; never automatically withdraw a student.

**Later phases -- do not build or scaffold these until their phase is activated:**
- A second or third delivery channel for the Phase 1 daily reminder; the separate Phase 2 device-readiness notice is the explicitly approved multi-channel addition described above.
- Engagement scoring beyond three simple states: active / low_engagement / needs_followup
- A polished or styled admin UI/dashboard -- functional and plain is correct
- Classroom AI operations, catalog/marketplace, billing, marketing, partnerships, or anything else assigned to a later phase in `MASTER_PROMPT.md`
- Any new third-party service, library, or architectural pattern not already named in `ARCHITECTURE.md`

**If a task requires work outside the active phase, stop and identify the phase and prerequisites instead of proceeding.**

---

## 3. Do Not Re-Decide What's Already Decided

`DECISIONS.md` contains choices that were made deliberately, often after ruling out alternatives. Do not silently reopen these unless the human operator explicitly asks you to reconsider one. If you think a past decision is wrong, say so and explain why -- don't just build the alternative.

---

## 4. Non-Negotiable Engineering Rules

- **Idempotency:** the daily job must never send a duplicate reminder if run twice in the same day. Check `reminder_log` for an existing send before sending again.
- **Logging:** every send attempt (success or failure) must be logged, both to the log file and to `reminder_log`. Silent failures are not acceptable.
- **Rate limiting:** when sending to multiple students, add delays between sends. Do not blast all messages simultaneously.
- **Secrets:** never hardcode an API key, password, or credential anywhere in code. Always read from environment variables via `.env`. Never write a real key into `.env.example` -- only placeholder text.
- **No real student data before explicit authorization:** use `scripts/seed_sample_data.py` and fake data until the human operator explicitly says the controlled pilot (Week 3) has started.
- **Small, scoped commits:** one logical change per commit, with a message explaining what and why.
- **Do not refactor code you weren't asked to touch**, even if you notice something you'd do differently. Flag it instead.

---

## 5. Code Conventions

- Python: type hints on function signatures, docstrings on anything non-trivial, small functions over large ones.
- Follow the file/folder structure in `ARCHITECTURE.md` exactly.
- Every new piece of automation logic needs a corresponding test in `tests/`.
- Prefer explicit, readable code over clever code.

---

## 6. When Uncertain

Ask, don't guess. Specifically ask when:
- A request seems to require a new library, service, or architectural change
- Real student data or a live send is about to happen and you're not sure it's authorized
- The instruction is ambiguous enough that two reasonable implementations would look very different
- Something in `DECISIONS.md` or `ARCHITECTURE.md` seems to conflict with what's being asked

Getting this wrong by proceeding silently costs more time than a clarifying question does.
