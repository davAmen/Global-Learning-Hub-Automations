# DECISIONS.md
### Key architectural decisions for the Global Learning Hub automation

This file records deliberate choices. Do not silently revert these — if you think a decision is wrong, discuss it first.

---

## 1. Data Store: Supabase (PostgreSQL) Only
**Decision:** All persistent data lives in Supabase. No Google Sheets, no local JSON/CSV, no second database.
**Rationale:** Single source of truth, relational integrity, row-level security, real-time subscriptions, generous free tier.
**Revisit when:** Data volume exceeds Supabase free tier or requires specialized analytics warehouse.

---

## 2. Backend Framework: FastAPI
**Decision:** Python + FastAPI for the backend API and scheduler.
**Rationale:** Type hints, automatic OpenAPI docs, async support, excellent Supabase client compatibility, easy to test.
**Revisit when:** Team lacks Python expertise or needs different performance profile.

---

## 3. Frontend Framework: Next.js (App Router)
**Decision:** Next.js on Vercel, calling backend API only — no direct database access.
**Rationale:** Zero-config deployment, React ecosystem, App Router is stable, clear separation of concerns.
**Revisit when:** Frontend needs complex real-time features better served by Supabase Realtime directly.

---

## 4. Scheduling: APScheduler Inside FastAPI
**Decision:** BackgroundScheduler runs inside the long-lived FastAPI process (on Railway/Render/Fly.io).
**Rationale:** Simpler than external cron, survives deploys if configured correctly, single process to monitor.
**Alternative considered:** External cron (cron-job.org, GitHub Actions) calling `POST /run-daily-job`.
**Revisit when:** Need to scale scheduler independently or survive process restarts without missing runs.

---

## 5. Delivery Channel: WhatsApp via WasenderAPI (Phase 1 ACTIVE)
**Decision:** Exactly ONE channel is wired live in Phase 1: WhatsApp using WasenderAPI.
**Backup:** Telegram (operator's personal bot) — only used if WhatsApp fails.
**Out of scope for Phase 1:** Email, SMS, second WhatsApp provider, in-app notifications.
**Rationale:** Operator's students are on WhatsApp; WasenderAPI is reliable and affordable; adding channels later is trivial via the adapter interface.
**Revisit when:** Phase 1 is complete and operator requests a second channel.

---

## 6. Message Templates: Separate File, No Logic
**Decision:** `reminder_templates.py` contains only string formatting. No business logic.
**Rationale:** Non-technical operator can edit copy without touching code. Templates are pure functions.

---

## 7. Engagement Model: Three States Only
**Decision:** `active` / `low_engagement` / `needs_followup` — driven solely by days since last submission.
**Thresholds:** ≤7 days = active, 8–14 = low_engagement, >14 = needs_followup.
**Out of scope:** Scoring algorithms, ML predictions, multi-factor engagement.
**Rationale:** Simple, explainable, actionable. Can be enriched later without schema change.

---

## 8. Idempotency: Check `reminder_log` Before Every Send
**Decision:** The daily job queries `reminder_log` for today's date + enrollment_id before sending. If a row exists, skip.
**Rationale:** Prevents duplicate reminders if job runs twice (scheduler drift, manual trigger, retry).
**Implementation:** `scheduler.already_sent()` — single source of truth.

---

## 9. Rate Limiting: Fixed Delay Between Sends
**Decision:** Configurable delay (default 6 seconds) between each outbound message in the daily job.
**Rationale:** WasenderAPI and WhatsApp Business API enforce rate limits; blasting risks ban. 6s = ~10/min, well within limits.
**Revisit when:** Volume grows; consider token bucket or provider-specific limits.

---

## 10. Secrets: Environment Variables Only
**Decision:** All credentials in `.env` (never committed). `.env.example` has placeholders only.
**Rationale:** Standard 12-factor practice. Prevents accidental exposure in git history.
**Enforcement:** CI checks for `.env` in gitignore; pre-commit hooks recommended.

---

## 11. No Real Student Data Until Explicit Authorization
**Decision:** `scripts/seed_sample_data.py` populates fake data. Real data only after operator says "Week 3 pilot started."
**Rationale:** Privacy, compliance, trust. Operator is non-technical — clear gate prevents accidents.

---

## 12. Human-in-the-Loop for Agent Actions (Future)
**Decision:** When the autonomous agent is built (Phase 2+), NO message is sent without admin approval.
**Rationale:** WhatsApp Business Policy requires opt-in; operator wants control; prevents spam/brand risk.
**Implementation:** `approvals` table + review endpoint; agent creates approval, admin approves, then send.

---

## 13. Webhook Security: HMAC-SHA256 Verification Required
**Decision:** All WasenderAPI webhooks must verify `X-Signature` header using a dedicated webhook secret.
**Rationale:** Prevents spoofed webhooks from triggering payments, approvals, or group changes.
**Implementation:** `routes_webhooks.py` verifies signature before processing; 5-min timestamp replay protection.

---

## 14. Database Schema: Source of Truth in `schema.sql`
**Decision:** All tables, columns, constraints, indexes defined in `schema.sql`. Models mirror it.
**Rationale:** Single source of truth for DDL. Migrations are explicit SQL, not ORM-generated.

---

## 15. Testing: Every New Automation Unit Gets a Test
**Decision:** `tests/` mirrors `src/` structure. Scheduler, channels, reports, API all have tests.
**Rationale:** Non-technical operator will modify code; tests catch regressions immediately.
**Standard:** `pytest` with `unittest.mock` for external dependencies.

---

## 16. Hosting: Railway (Backend) + Vercel (Frontend)
**Decision:** Fixed for this phase. Backend needs always-on for APScheduler; Vercel is zero-config for Next.js.
**Revisit when:** Cost, latency, or compliance requires different provider.

---

## 17. IELTS Course: Hardcoded Config for Phase 1
**Decision:** IELTS course details (dates, groups, payment info) live in `.env` via config.py.
**Rationale:** Single course, known schedule. Avoids building full course management UI in Phase 1.
**Revisit when:** Multiple courses need dynamic scheduling.

---

## 18. Payment Verification: Manual Admin Review
**Decision:** Student submits proof in WhatsApp group → webhook creates payment record → admin verifies in web UI → system adds to class group.
**Rationale:** No MoMo/Telecel API integration yet; manual review is secure and auditable.
**Revisit when:** Payment provider APIs are available and approved.

---

## 19. Audit Trail: Every Agent/Admin Action Logged
**Decision:** `audit_log` table captures actor, action, entity, details, timestamp.
**Rationale:** Compliance, debugging, trust. Required for financial/payment flows.

---

## 20. Group Types: Four Fixed Categories
**Decision:** `announcement`, `proof_submission`, `class_access`, `community`.
**Rationale:** Maps to WhatsApp Community structure. Extensible via `settings` JSONB.

---

## 21. Payment Provider: SeefCash (Phase 2)
**Decision:** SeefCash is the chosen payment provider for Ghana Mobile Money integration.
**Rationale:** Local Ghana provider, supports MoMo directly, lower fees than international alternatives, supports the exact payment flow needed (reference-based verification).
**Configuration:** Requires `SEEFCASH_PUBLIC_KEY`, `SEEFCASH_SECRET_KEY`, `SEEFCASH_WEBHOOK_SECRET` in `.env`.
**Fallback:** Mock provider for testing; Paystack/Stripe adapters remain available if needed later.
**Status:** Selected 2026-10-07. Awaiting operator account setup.