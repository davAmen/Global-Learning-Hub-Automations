# AGENTS.md
### Instructions for any AI coding agent working in this repository

Read this file, `ARCHITECTURE.md`, and `DECISIONS.md` in full before writing or changing any code. These three files are the source of truth for this project -- not assumptions, not "best practice," not what a similar project usually looks like.

---

## 1. What This Project Is

A daily automation that sends class reminders to students and reports engagement to the administrator (David). It is the FIRST of several planned automations for a larger learning-hub operation -- but only this one is being built right now.

**The person directing you is non-technical.** He is learning by doing this with your help -- do not assume he understands infrastructure, APIs, or code unless he demonstrates it in the conversation. Explain briefly what you're doing and why when it isn't obvious, but do not lecture at length unprompted.

---

## 2. Active Phase Boundary -- Read This Before Building Anything

The operator activated Phase 2 (consent-based attendance) on 2026-09-27, then selected an owned class platform that supports local classroom use and remote access when online. On 2026-09-27 the operator confirmed the high-level hybrid and sync direction recorded in `ARCHITECTURE.md` and `DECISIONS.md`: site hubs own records created locally, the cloud owns remote-origin records, and reconnection uses an acknowledged, duplicate-safe event outbox with human review of conflicts. This supersedes the earlier no-platform and WhatsApp-group classroom directions. Preserve the Phase 1 WhatsApp reminder service. Treat “local” as a classroom LAN/intranet that still connects devices to a nearby server; remote sites cannot join a live local session while disconnected. This approval does not select a database, API, authentication method, or deployment, and does not authorize implementation, a real pilot, or real learner data. The current repository has no learner login or attendance model, so do not expose attendance writes or accept a student ID alone. Before schema, API, or frontend changes, settle offline identity/access and expiry, session/status rules, correction audit, consent/notice, retention, security, and recovery in `ARCHITECTURE.md` and `DECISIONS.md`. Do not start Phase 3 or later until the operator explicitly activates it.

**Phase 1 baseline to preserve without expanding it during Phase 2:**
- Student, course, and enrollment data in Supabase (see `ARCHITECTURE.md` for schema)
- A daily scheduled job that determines who needs a reminder
- Sending that reminder through exactly ONE delivery channel (WhatsApp active, Telegram backup)
- A daily report of engagement, sent to the administrator
- A simple Next.js frontend that displays this data and can manually trigger the job -- nothing more

**Active Phase 2 boundary:**
- Design an owned classroom platform for teachers and learners to share lessons/resources and complete classroom activities, usable on a local LAN without internet and remotely when internet is available.
- Prefer learners' own devices (BYOD); do not assume every learner has the same device or select a native app/browser architecture yet. Plan accessible fallback access before any pilot.
- Include one weekly device-readiness notice asking learners to charge their devices for class and use a school-provided device where available. Day/time and delivery channel remain undecided; this is not permission to send messages or add a channel.
- Keep attendance explicit, consent-based, and separate from assignment/exercise evidence. Require verified identity and auditable teacher corrections; do not infer attendance or active learning from presence, message counts, read receipts, or passive device signals.
- The high-level sync direction is documented and approved; exact event fields, transport security, offline credential freshness/expiry, session/status rules, correction audit, consent/notice, retention, and recovery remain open. Do not add attendance/platform schema, APIs, or screens until those implementation decisions and the pilot scope are documented and approved.
- A disconnected local hub can serve only devices connected to its local network; remote teaching during an internet outage is not promised.
- Four consecutive absences may trigger supportive contact and human review; never automatically withdraw a student.

**Later phases -- do not build or scaffold these until their phase is activated:**
- A second or third delivery channel as active (Telegram is the only backup)
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
