# Global Learning Hub — Learning Platform (Phase 2+)

A mobile-first, low-bandwidth learning platform for learners in Ghana and beyond. Delivers structured courses via web app + optional WhatsApp reminders, with secure enrolment, payment, progress tracking, and completion verification.

**Read first:** `docs/AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/PROJECT_DESCRIPTION.md`, `docs/PRODUCT_READINESS.md`, `docs/LIVE_TEST_REPORT.md`.

---

## What It Does

1. **Course Catalogue** — Public browsing of courses with pricing, outcomes, prerequisites, capacity
2. **Learner Accounts** — Email/password registration, JWT auth (HttpOnly cookies), email verification, password reset
3. **Enrolment & Payment** — $1 seat reservation → payment provider → verification → full enrolment
4. **Course Delivery** — Lessons (MDX), progress tracking, assessments, certificates (planned)
5. **WhatsApp Reminders** — Daily individual (8am GMT) + IELTS group (5am GMT), opt-in
5. **Admin Dashboard** — Approvals, payment verification, course management, analytics (API ready)

---

## Stack

| Layer | Technology | Hosting |
|-------|------------|---------|
| Frontend | Next.js 14 (App Router), React 18, TypeScript | Vercel |
| Backend | FastAPI, Python 3.10+, APScheduler | Railway (always-on) |
| Database | Supabase (PostgreSQL), RLS on all tables | Supabase |
| WhatsApp | WasenderAPI (text, groups, webhooks) | WasenderAPI |
| Payments | Provider-neutral: Paystack / SeefCash / Stripe / Mock | Respective dashboards |
| CI/CD | GitHub Actions (pytest, npm build, deploy) | GitHub → Railway/Vercel |

---

## Quick Start (Local, Fake Data Only)

```bash
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # fill in placeholders, or leave for dry-run
python scripts\seed_sample_data.py   # inserts FAKE students/courses — no real data
python scripts\run_daily_job.py      # runs today's job manually, logs results
uvicorn src.main:app --reload        # start API on http://localhost:8000

# Frontend
cd frontend
npm install
npm run dev    # http://localhost:3000 (requires NEXT_PUBLIC_API_URL=http://localhost:8000)
```

> **No real student data or live sends happen until the operator explicitly authorizes the paid pilot.** Everything uses fake data until then. If you're unsure, ask.

---

## Documentation

| File | Purpose |
|------|---------|
| `docs/AGENTS.md` | Instructions for AI agents working in this repo |
| `docs/ARCHITECTURE.md` | Technical specification (source of truth) |
| `docs/DECISIONS.md` | 20 architectural decisions |
| `docs/PROJECT_DESCRIPTION.md` | Full project overview, API, DB, flows, setup |
| `docs/PRODUCT_READINESS.md` | Launch checklist (what's ready, what blocks pilot) |
| `docs/LIVE_TEST_REPORT.md` | Actual test results, evidence, limitations |
| `docs/PHASE2_AGENT_ARCHITECTURE.md` | Future LangGraph agent design |
| `docs/LEARNING_DATABASE_MONETIZATION.md` | Content database strategy |

---

## API Routes

| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/health` | GET | None | Basic uptime |
| `/health/detailed` | GET | None | DB + config check |
| `/run-daily-job` | POST | None | Manual daily job trigger |
| `/reports/today` | GET | None | Engagement + reminder stats |
| `/students` | GET | Admin | List all students |
| `/courses` | GET | Public | Course catalogue (active only) |
| `/courses/{id}` | GET | Public | Course detail with pricing |
| `/approvals` | GET | Admin | List approvals |
| `/approvals/{id}/review` | POST | Admin | Approve/reject/modify |
| `/payments` | GET/POST | Admin | List/create payments |
| `/payments/{id}/verify` | POST | Admin | Verify/reject payment |
| `/groups` | GET/POST | Admin | WhatsApp group mgmt |
| `/webhooks/{channel}` | POST | Signature | WasenderAPI callbacks |
| `/enrollments/reserve-seat` | POST | Learner | $1 seat reservation |
| `/enrollments/confirm-seat-reservation` | POST | Learner | Verify seat payment |
| `/enrollments/enroll` | POST | Learner | Full enrolment |
| `/enrollments/my-enrollments` | GET | Learner | My courses |
| `/enrollments/course/{id}/status` | GET | Public/Learner | Enrolment status |
| `/auth/register` | POST | Public | Create account |
| `/auth/login` | POST | Public | Login |
| `/auth/logout` | POST | Learner | Logout |
| `/auth/refresh` | POST | Learner | New access token |
| `/auth/forgot-password` | POST | Public | Request reset |
| `/auth/reset-password` | POST | Public | Reset password |
| `/auth/verify-email` | POST | Public | Verify email |
| `/auth/me` | GET | Learner | Current user |

See `docs/PROJECT_DESCRIPTION.md` for full flow details.

---

## Environment Variables

All in `.env` (never committed). See `.env.example` for template.

**Required for all environments:**
- `SUPABASE_URL`, `SUPABASE_KEY`
- `JWT_SECRET_KEY` (32+ chars, `openssl rand -hex 32`)
- `ACTIVE_CHANNEL=whatsapp`
- `WASENDER_API_KEY`, `WASENDER_WEBHOOK_SECRET`
- `APP_BASE_URL` (frontend URL for payment callbacks)

**Payment providers (choose one or more):**
- Paystack: `PAYSTACK_PUBLIC_KEY`, `PAYSTACK_SECRET_KEY`, `PAYSTACK_WEBHOOK_SECRET`
- SeefCash: `SEEFCASH_PUBLIC_KEY`, `SEEFCASH_SECRET_KEY`, `SEEFCASH_WEBHOOK_SECRET`
- Stripe: `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`

**Optional / backup:**
- `ADMIN_EMAIL`, `ADMIN_PHONE` (daily reports)
- `SMTP_*`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`
- `RATE_LIMIT_DELAY_SECONDS=6`, `JOB_HOUR=8`, `JOB_MINUTE=0`

---

## Deployment

| Component | Platform | Command |
|-----------|----------|---------|
| Frontend | Vercel | `vercel --prod` (set `NEXT_PUBLIC_API_URL`) |
| Backend | Railway | `uvicorn src.main:app` (always-on) |
| Database | Supabase | Run `supabase_migration.sql` + `supabase_migration_phase2.sql` in SQL Editor |
| WhatsApp | WasenderAPI | Configure webhook: `https://<railway-url>/webhooks/whatsapp` |

**Before deploying:**
1. Run both migrations in Supabase SQL Editor
2. Set all env vars in Railway (backend) and Vercel (frontend)
3. Configure WasenderAPI webhook URL in Wasender dashboard
4. Verify `APP_BASE_URL` matches frontend URL
5. Test `/health/detailed` returns all OK

---

## Roadmap

### Phase 2: Pilot Launch (3-4 weeks)
- [ ] Choose payment provider (Paystack vs SeefCash vs Stripe)
- [ ] Create Supabase project, run both migrations, seed IELTS course
- [ ] Verify RLS policies against real Supabase auth
- [ ] Build 4 frontend pages: catalogue, course detail, login, register
- [ ] Create 5-10 lesson MDX files for IELTS pilot
- [ ] Configure payment provider sandbox + WasenderAPI account
- [ ] Deploy preview (Vercel + Railway), test E2E
- [ ] Recruit 10-20 pilot learners, run 2-week trial

### Phase 3: Course Delivery (4-6 weeks)
- [ ] Lesson viewer (MDX rendering, mobile-friendly)
- [ ] Progress tracking (lesson completion, time spent)
- [ ] Assessments (quizzes, assignments, auto-grading)
- [ ] Certificate/admission letter generation (PDF)
- [ ] WhatsApp opt-in preference + UI
- [ ] Admin frontend (approvals, payments, courses, analytics)

### Phase 4: Scale & Monetize (8-12 weeks)
- [ ] Multiple courses, categories, search/filter
- [ ] Corporate/B2B licensing (white-label)
- [ ] Subscription + per-course pricing
- [ ] Affiliate/referral program
- [ ] Load testing, auto-scaling, Redis rate limiting
- [ ] Backup/restore automation, monitoring/alerting
- [ ] Multi-language (start with English + Twi)

### Phase 5: AI Agent (Future)
- [ ] LangGraph agent monitoring training provider community
- [ ] Auto-extract materials, create approvals
- [ ] Auto-generate flyers, course drafts
- [ ] Personalized learning paths

---

## Security & Compliance

- **JWT in HttpOnly cookies** — mitigates XSS
- **bcrypt(12 rounds)** — password hashing
- **HMAC-SHA256 webhook verification** — prevents spoofed callbacks
- **RLS on every table** — learners see only own data
- **Rate limiting** — 60 req/min per IP (in-memory, use Redis in prod)
- **Idempotency keys** — webhook deduplication
- **No secrets in code** — all via env vars
- **Audit log** — every privileged action recorded

---

## Known Limits

- Frontend: only home, courses list, run-job exist (login/register/dashboard/course detail missing)
- Course content delivery not built (no lesson viewer, progress, assessments)
- Payment provider undecided (adapters ready, none live)
- WhatsApp opt-in missing (reminders sent to all active enrolments)
- Admin UI: API only, no frontend
- RLS policies written but untested against real Supabase auth
- No backup/restore procedure, no monitoring
- In-memory rate limiter (resets on restart)

---

## Support

- **Admin:** David Amenuku (`amenukudavid20@gmail.com`, +233548014157)
- **Issues:** GitHub Issues (this repo)
- **Docs:** `docs/` folder

---

*Last updated: 2026-10-07*