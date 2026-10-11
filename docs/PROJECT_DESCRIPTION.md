# Global Learning Hub — Project Description

## What This Product Does

Global Learning Hub is a **mobile-first, low-bandwidth learning platform** for learners in Ghana and similar regions. It delivers structured courses via a web application and optional WhatsApp reminders, with secure enrolment, payment, progress tracking, and completion verification.

**Target users:**
- Individual learners seeking affordable, structured courses (IELTS prep, professional skills, academic subjects)
- Course administrators who manage content, enrolments, and payments
- The platform operator (David) who oversees operations

**Key value:** Courses in the $2–$50 USD range with a $1 USD seat reservation. WhatsApp integration for reminders where learners already communicate. No requirement for high-speed internet or expensive devices.

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend       │────▶│   Database      │
│   (Next.js)     │     │   (FastAPI)     │     │   (Supabase)    │
│   Vercel        │     │   Railway       │     │   PostgreSQL    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌────────────┐ ┌──────────┐ ┌─────────────┐
             │  WhatsApp  │ │ Payment  │ │  File/Asset │
             │  Gateway   │ │ Adapters │ │  Storage    │
             │ (Wasender) │ │(Paystack/ │ │  (Supabase) │
             └────────────┘ │ Stripe/  │ └─────────────┘
                            │ Mock)    │
                            └──────────┘
```

**Data flow:**
1. Learner visits catalogue → reads from Supabase via FastAPI
2. Learner registers/logs in → JWT in HttpOnly cookies, password hashed with bcrypt
3. Learner enrols → seat reservation ($1) → payment provider → webhook verification → enrolment created
4. Daily job runs → checks classes today → sends WhatsApp reminders via WasenderAPI
5. Admin approves actions → audit log → execution

---

## Directory Structure

```
.
├── AGENTS.md                    # Instructions for AI agents
├── ARCHITECTURE.md              # Technical specification (source of truth)
├── DECISIONS.md                 # 20 architectural decisions
├── SPEC_FULL_SYSTEM.md          # Full system design (future phases)
├── AUDIT_REPORT.md              # Gap analysis of claims vs code
├── PHASE2_AGENT_ARCHITECTURE.md # LangGraph agent design
├── LEARNING_DATABASE_MONETIZATION.md # Content database strategy
├── docs/
│   ├── PROJECT_DESCRIPTION.md   # This file
│   ├── PRODUCT_READINESS.md     # Launch checklist
│   └── LIVE_TEST_REPORT.md      # Test results
├── backend/
│   ├── .env.example             # Environment variable template
│   ├── requirements.txt         # Python dependencies
│   ├── supabase_migration.sql   # Phase 1+ schema
│   ├── supabase_migration_phase2.sql # Phase 2 RLS + new fields
│   ├── src/
│   │   ├── main.py              # FastAPI app + scheduler + middleware
│   │   ├── config.py            # Pydantic Settings (all env vars)
│   │   ├── database/
│   │   │   ├── client.py        # Supabase client (lazy, testable)
│   │   │   ├── models.py        # Pydantic models (not ORM)
│   │   │   └── schema.sql       # Canonical DDL
│   │   ├── auth/
│   │   │   ├── utils.py         # JWT, bcrypt, cookies, tokens
│   │   │   └── routes.py        # /auth/register, /login, /refresh, /forgot-password
│   │   ├── payments/
│   │   │   ├── base.py          # Provider interface (PaymentProvider ABC)
│   │   │   ├── mock.py          # Mock provider for testing
│   │   │   ├── paystack.py      # Paystack adapter
│   │   │   ├── seefcash.py      # SeefCash adapter
│   │   │   ├── stripe.py        # Stripe adapter
│   │   │   └── __init__.py      # Registry (auto-registers configured providers)
│   │   ├── channels/
│   │   │   ├── base.py          # Channel interface (Channel ABC)
│   │   │   ├── whatsapp_channel.py # WasenderAPI implementation
│   │   │   ├── telegram_channel.py
│   │   │   ├── email_channel.py
│   │   │   └── sms_channel.py
│   │   ├── automation/
│   │   │   ├── scheduler.py     # Daily job: who needs reminder, idempotency
│   │   │   ├── engagement.py    # active/low_engagement/needs_followup
│   │   │   ├── reminder_templates.py # Message copy
│   │   │   └── ielts_reminder.py # IELTS group reminder at 5am GMT
│   │   ├── reports/
│   │   │   └── daily_report.py  # Engagement + reminder stats
│   │   └── api/
│   │       ├── routes_health.py     # /health, /health/detailed
│   │       ├── routes_jobs.py       # POST /run-daily-job
│   │       ├── routes_reports.py    # GET /reports/today
│   │       ├── routes_students.py   # GET /students (admin)
│   │       ├── routes_courses.py    # GET /courses, /courses/{id}
│   │       ├── routes_approvals.py  # GET/POST /approvals, /approvals/{id}/review
│   │       ├── routes_payments.py   # GET/POST /payments, /payments/{id}/verify
│   │       ├── routes_groups.py     # GET/POST /groups
│   │       ├── routes_webhooks.py   # POST /webhooks/{channel}
│   │       └── routes_enrollments.py # Seat reserve, confirm, enrol, my-enrolments
│   ├── scripts/
│   │   ├── seed_sample_data.py    # Fake data for local dev
│   │   ├── run_daily_job.py       # Manual CLI trigger
│   │   └── verify_data.py
│   └── tests/                     # 56 tests (pytest + pytest-asyncio)
├── frontend/
│   ├── package.json               # Next.js 14, React 18
│   ├── next.config.js
│   ├── .env.local.example         # NEXT_PUBLIC_API_URL
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx               # Home: today's report
│   │   ├── courses/page.tsx       # Course catalogue
│   │   ├── courses/[id]/page.tsx  # Course detail (TODO)
│   │   ├── auth/login/page.tsx    # Login (TODO)
│   │   ├── auth/register/page.tsx # Register (TODO)
│   │   ├── dashboard/page.tsx     # Learner dashboard (TODO)
│   │   └── run/page.tsx           # Manual job trigger
│   ├── components/
│   │   ├── ReportCard.tsx
│   │   ├── StudentTable.tsx
│   │   └── RunJobButton.tsx
│   └── lib/api.ts                 # fetch wrappers for backend
└── .github/workflows/ci.yml       # CI: pytest + npm build + deploy
```

---

## API Routes & Responsibilities

| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/health` | GET | None | Basic uptime |
| `/health/detailed` | GET | None | DB + config check |
| `/run-daily-job` | POST | None | Manual trigger for daily reminders |
| `/reports/today` | GET | None | Engagement + reminder stats |
| `/students` | GET | Admin | List all students |
| `/courses` | GET | Public | Course catalogue (active only) |
| `/courses/{id}` | GET | Public | Course detail with pricing |
| `/approvals` | GET | Admin | List pending/approved/rejected |
| `/approvals/{id}/review` | POST | Admin | Approve/reject/modify action |
| `/payments` | GET/POST | Admin | List/create payment records |
| `/payments/{id}/verify` | POST | Admin | Verify/reject payment |
| `/groups` | GET/POST | Admin | WhatsApp group management |
| `/webhooks/{channel}` | POST | Signature | WasenderAPI callbacks |
| `/enrollments/reserve-seat` | POST | Learner | $1 seat reservation → payment URL |
| `/enrollments/confirm-seat-reservation` | POST | Learner | Verify seat payment |
| `/enrollments/enroll` | POST | Learner | Full enrolment flow |
| `/enrollments/my-enrollments` | GET | Learner | My courses + status |
| `/enrollments/course/{id}/status` | GET | Public/Learner | Enrolment status + seat availability |
| `/auth/register` | POST | Public | Create account, set cookies |
| `/auth/login` | POST | Public | Verify password, set cookies |
| `/auth/logout` | POST | Learner | Clear cookies |
| `/auth/refresh` | POST | Learner | New access token |
| `/auth/forgot-password` | POST | Public | Request reset token |
| `/auth/reset-password` | POST | Public | Reset with token |
| `/auth/verify-email` | POST | Public | Verify with token |
| `/auth/me` | GET | Learner | Current user profile |

---

## Database Tables (Supabase/PostgreSQL)

| Table | Purpose | Key Fields | RLS |
|-------|---------|------------|-----|
| `students` | Learner accounts | id, name, email, phone, password_hash, email_verified, role, last_login_at | ✅ |
| `courses` | Course catalogue | id, name, description, price_minor, currency, capacity, seat_reservation_minor, start_date, is_active | ✅ |
| `enrollments` | Learner ↔ Course | id, student_id, course_id, status (active/inactive/completed/dropped) | ✅ |
| `engagement_log` | Daily engagement | id, enrollment_id, date, status, assignment_submitted | ✅ |
| `reminder_log` | Sent reminders | id, enrollment_id/course_id, channel, message, delivery_status, external_message_id | ✅ |
| `payments` | Payment records | id, student_id, course_id, amount, currency, status, provider, seat_reservation, seat_reservation_verified_at | ✅ |
| `approvals` | Human-in-the-loop | id, action_type, content, target_group_jid, status, requested_by | ✅ |
| `groups` | WhatsApp groups | id, whatsapp_jid, name, type, course_id, is_active | ✅ |
| `content_library` | Course materials | id, type, title, content, image_url, course_id, created_by | ✅ |
| `audit_log` | Full action trail | id, actor, action, entity_type, entity_id, details | ✅ |
| `system_config` | Key-value config | key, value, description | ✅ |
| `agent_state` | (Future) Agent persistence | session_id, current_task, last_run, config | — |

**RLS policies:** Every table has policies for `learner` (own data), `admin` (all data), `service_role` (backend). See `supabase_migration_phase2.sql`.

---

## Key Flows

### 1. Authentication & Account Recovery
```
Register: POST /auth/register → hash password → create student → JWT access+refresh → HttpOnly cookies
Login:    POST /auth/login → verify bcrypt → JWT tokens → cookies
Refresh:  POST /auth/refresh → validate refresh token → new access token
Forgot:   POST /auth/forgot-password → generate token → log (email in prod) → 1hr expiry
Reset:    POST /auth/reset-password → validate token → hash new password → clear token
Verify:   POST /auth/verify-email → validate token → email_verified=true
```

### 2. Enrolment & Payment
```
1. GET /enrollments/course/{id}/status → check capacity, existing enrolment
2. POST /enrollments/reserve-seat → create payment (seat_reservation=true) → provider.initialize_payment() → return authorization_url
3. Learner pays at provider → provider webhook OR callback → POST /webhooks/{provider} → verify signature → update payment status
4. POST /enrollments/confirm-seat-reservation → provider.verify_payment() → if verified: seat_reservation_verified_at=now
5. (Optional) POST /enrollments/enroll → tuition payment → verified → create enrollment (status=active)
```

### 3. Daily Reminder Job (APScheduler, 8am GMT)
```
scheduler.py → send_reminders():
  1. classes_today() → active courses with start_date=today
  2. active_enrollments(course) → students with status=active
  3. already_sent(enrollment, today) → idempotency check
  4. update_engagement() → active/low_engagement/needs_followup
  4. reminder_templates.reminder_for() → message per status
  5. channel.send() → WasenderAPI (6s delay between sends)
  6. reminder_log insert (delivery_status, external_message_id)
  7. daily_report.build_report() → engagement + reminder stats
  8. send_report_to_admin() → WhatsApp to admin
```

### 4. IELTS Group Reminder (5am GMT)
```
ielts_reminder.py → send_ielts_reminder_scheduled():
  1. Build message with dates, price, MoMo/Telecel numbers, proof/access group links
  2. Create approval (action_type=send_message, target=announcement_group)
  3. If auto_approve_reminders=true → send immediately via WasenderAPI
  4. Else wait for admin approval via /approvals/{id}/review
```

---

## Environment Variables

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `SUPABASE_URL` | Supabase project URL | All environments |
| `SUPABASE_KEY` | Supabase anon/service key | All environments |
| `ACTIVE_CHANNEL` | `whatsapp` (default) | All |
| `WASENDER_API_KEY` | WasenderAPI Bearer token | WhatsApp sending |
| `WASENDER_WEBHOOK_SECRET` | HMAC secret for webhooks | Webhook verification |
| `JWT_SECRET_KEY` | HS256 signing key (32+ chars) | Auth |
| `PAYSTACK_SECRET_KEY` / `PAYSTACK_PUBLIC_KEY` / `PAYSTACK_WEBHOOK_SECRET` | Paystack credentials | Paystack payments |
| `SEEFCASH_SECRET_KEY` / `SEEFCASH_WEBHOOK_SECRET` | SeefCash credentials | SeefCash payments |
| `STRIPE_SECRET_KEY` / `STRIPE_PUBLIC_KEY` / `STRIPE_WEBHOOK_SECRET` | Stripe credentials | Stripe payments |
| `APP_BASE_URL` | Frontend URL for callbacks | Payment redirects |
| `ADMIN_EMAIL` / `ADMIN_PHONE` | Daily report recipient | Reports |
| `SMTP_*` | Email channel (backup) | Email sending |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_ADMIN_CHAT_ID` | Telegram backup | Telegram |
| `RATE_LIMIT_DELAY_SECONDS` | Delay between sends (default 6) | Scheduler |
| `JOB_HOUR` / `JOB_MINUTE` | Daily job time (GMT) | Scheduler |

**Never commit `.env`.** Use `.env.example` as template. Production secrets go in Railway/Vercel/Supabase dashboard env vars.

---

## Local Development

```bash
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # Fill in values
python scripts\seed_sample_data.py
python scripts\run_daily_job.py
uvicorn src.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

**Health check:** `GET http://localhost:8000/health/detailed`

---

## Deployment

| Component | Platform | Notes |
|-----------|----------|-------|
| Frontend | Vercel | `NEXT_PUBLIC_API_URL` = Railway URL |
| Backend | Railway | Always-on for APScheduler; `uvicorn src.main:app` |
| Database | Supabase | Run `supabase_migration.sql` + `supabase_migration_phase2.sql` in SQL Editor |
| WhatsApp | WasenderAPI | Configure webhook: `https://<railway-url>/webhooks/whatsapp` |

**Before deploying:**
1. Run `supabase_migration.sql` then `supabase_migration_phase2.sql` in Supabase
2. Set all env vars in Railway (backend) and Vercel (frontend)
3. Configure WasenderAPI webhook URL in Wasender dashboard
4. Verify `APP_BASE_URL` matches frontend URL
5. Test `/health/detailed` returns all OK

---

## Known Limits & Incomplete Features

| Area | Status | Notes |
|------|--------|-------|
| **Frontend pages** | Partial | Only home, courses list, run-job exist. Login/register/dashboard/course detail missing. |
| **Course content delivery** | Not built | No lesson viewer, progress tracking, assessments, certificates. |
| **WhatsApp opt-in** | Missing | No preference storage; reminders sent to all active enrolments. |
| **Payment provider** | Undecided | Paystack/SeefCash/Stripe adapters exist; none configured live. |
| **Admin UI** | API only | No frontend for approvals, payments, courses management. |
| **File uploads** | Not built | No Supabase Storage integration for materials/images. |
| **Email verification** | Log only | Tokens logged; no SMTP configured. |
| **Rate limiting** | In-memory | Resets on restart; use Redis for production. |
| **RLS testing** | Untested | Policies written; not verified against real Supabase auth. |
| **Backups/recovery** | None | No automated backup or restore procedure documented. |

---

## Next Recommended Work

1. **Build missing frontend pages** (login, register, course detail, dashboard)
2. **Implement course content delivery** (MDX lessons, progress, assessments)
3. **Choose payment provider** (Paystack vs SeefCash vs Stripe) and configure live
4. **Add WhatsApp opt-in** (preference column + UI)
5. **Test RLS policies** against real Supabase auth
6. **Add admin frontend** (approvals, payments, courses)
7. **Document backup/restore** and test recovery
8. **Load test** daily job at scale

---

## Security Assumptions

- **JWT in HttpOnly cookies** — mitigates XSS token theft
- **bcrypt(12 rounds)** — password hashing
- **HMAC-SHA256 webhook verification** — prevents spoofed callbacks
- **RLS on every table** — learners see only own data
- **Rate limiting** — 60 req/min per IP (in-memory)
- **Idempotency keys** — webhook deduplication
- **No secrets in code** — all via env vars
- **Audit log** — every privileged action recorded