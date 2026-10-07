# Global Learning Hub

A mobile-first, low-bandwidth learning platform for learners in Ghana and beyond. Delivers structured courses via web app + optional WhatsApp reminders, with secure enrolment, payment, progress tracking, and completion verification.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Backend README](backend/README.md) | Full setup, API, deployment, architecture |
| [Project Description](docs/PROJECT_DESCRIPTION.md) | Technical overview, API, DB, flows, env vars |
| [Product Readiness](docs/PRODUCT_READINESS.md) | Launch checklist — what's ready, what blocks pilot |
| [Live Test Report](docs/LIVE_TEST_REPORT.md) | Actual test results, evidence, limitations |
| [Architecture](docs/ARCHITECTURE.md) | Technical specification (source of truth) |
| [Decisions](docs/DECISIONS.md) | 20 architectural decisions |
| [Agents](docs/AGENTS.md) | Instructions for AI agents |

---

## Quick Start

```bash
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts\seed_sample_data.py
python scripts\run_daily_job.py
uvicorn src.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

**Backend:** http://localhost:8000  
**Frontend:** http://localhost:3000 (requires `NEXT_PUBLIC_API_URL=http://localhost:8000`)

---

## Current Status

| Area | Status |
|------|--------|
| Backend API | ✅ 56 tests passing |
| Frontend | ⚠️ Partial (home, courses, run-job only) |
| Database | ⚠️ Migrations written, not run live |
| Payments | ⚠️ Adapters ready, provider undecided |
| WhatsApp | ❌ WasenderAPI not configured |
| Auth | ✅ JWT + HttpOnly cookies |
| Enrolment flow | ✅ Seat reserve → pay → verify |
| Daily reminders | ✅ 8am GMT + IELTS 5am GMT |

---

## Next Steps (Priority)

1. **Choose payment provider** — Paystack vs SeefCash vs Stripe
2. **Create Supabase project** → run migrations → seed IELTS course
3. **Build 4 frontend pages** — catalogue, course detail, login, register
4. **Create IELTS lesson content** (5-10 MDX files)
4. **Configure payment sandbox + WasenderAPI**
5. **Deploy preview** → recruit 10-20 pilot learners

See [Product Readiness](docs/PRODUCT_READINESS.md) for full checklist.

---

## Deployment Targets

- **Frontend:** Vercel
- **Backend:** Railway (always-on for APScheduler)
- **Database:** Supabase (PostgreSQL + RLS)
- **WhatsApp:** WasenderAPI
- **Payments:** Paystack / SeefCash / Stripe (choose one)

---

## License

Proprietary — Global Learning Hub