# Global Learning Hub — Product Readiness Checklist

**Status:** Pre-pilot — core backend complete, frontend partial, no live payments or WhatsApp configured.

---

## Ready for Pilot (✅ Done)

### Core Infrastructure
- [x] FastAPI backend with APScheduler (8am GMT daily job)
- [x] Supabase/PostgreSQL schema with 11 tables + RLS policies
- [x] JWT authentication (register, login, refresh, logout, forgot/reset password, email verification)
- [x] bcrypt password hashing (12 rounds), HttpOnly cookies
- [x] Rate limiting (60 req/min, in-memory)
- [x] CORS configured for Vercel + localhost
- [x] Idempotency keys for webhook deduplication
- [x] Audit logging for all privileged actions
- [x] Health checks (`/health`, `/health/detailed`)

### Course & Enrolment
- [x] Course catalogue API (active courses only, public)
- [x] Course detail API with pricing (price_minor, currency, capacity, seat reservation)
- [x] Seat reservation flow ($1 → payment → verification)
- [x] Full enrolment flow (seat + tuition)
- [x] Learner enrolment dashboard (`/enrollments/my-enrollments`)
- [x] Course status check (`/enrollments/course/{id}/status`)
- [x] Admin enrolment management (list, status update)

### Payments (Provider-Neutral)
- [x] Abstract `PaymentProvider` interface
- [x] Mock provider (auto-verify for testing)
- [x] Paystack adapter (Checkout + webhook)
- [x] SeefCash adapter (mobile money)
- [x] Stripe adapter (Checkout Session + webhook)
- [x] Registry auto-registers configured providers
- [x] Seat reservation separate from tuition ($1 = admission letter)
- [x] Payment records with provider fields, fees, seat_reservation flag

### WhatsApp Automation
- [x] WasenderAPI channel (text, groups, rate limiting, retries)
- [x] Daily individual reminders (8am GMT)
- [x] IELTS group reminder (5am GMT, approval flow)
- [x] Webhook handler (delivery status, incoming messages, group events)
- [x] HMAC-SHA256 signature verification
- [x] Idempotency + replay protection (5min window)

### Admin & Monitoring
- [x] Approval workflow (send_message, create_group, verify_payment, etc.)
- [x] Payment verification UI (pending/verified/rejected)
- [x] Daily engagement report (active/low/followup + reminder stats)
- [x] Manual job trigger (`POST /run-daily-job`)
- [x] Audit log (actor, action, entity, details)

### Testing
- [x] 56 backend tests passing (pytest + pytest-asyncio)
- [x] Tests for scheduler, channels, engagement, reports, IELTS, API, auth

---

## Not Ready for Public Launch (❌ Blocking)

### Frontend (Learner-Facing)
| Feature | Status | Effort |
|---------|--------|--------|
| Landing page with course catalogue | ❌ Missing | 1 week |
| Course detail page (price, outcomes, prerequisites, content preview) | ❌ Missing | 3 days |
| Login / Register pages | ❌ Missing | 2 days |
| Learner dashboard (my courses, progress, payments) | ❌ Missing | 1 week |
| Course content viewer (lessons, materials) | ❌ Not designed | 2+ weeks |
| Progress tracking & assessments | ❌ Not designed | 2+ weeks |
| Certificate/admission letter generation | ❌ Not designed | 1 week |
| Mobile-responsive, low-bandwidth optimized | ⚠️ Partial | Ongoing |

### Course Content
| Item | Status |
|------|--------|
| Pilot course defined (IELTS) | ✅ Exists in config |
| Lesson materials (MDX/Markdown) | ❌ Not created |
| Learning outcomes, prerequisites, study time | ⚠️ Config only |
| Assessments (quizzes, assignments) | ❌ Not created |
| Certificate template | ❌ Not created |
| Content review/approval workflow | ❌ Not built |

### Payment Provider (Live)
| Provider | Status |
|----------|--------|
| Paystack | ⚠️ Adapter ready, not configured |
| SeefCash | ⚠️ Adapter ready, not configured |
| Stripe | ⚠️ Adapter ready, not configured |
| **Decision needed** | ❌ Paystack vs SeefCash vs Stripe |

### WhatsApp Integration
| Feature | Status |
|---------|--------|
| WasenderAPI account | ❌ Not created |
| Webhook URL configured | ❌ Needs Railway URL |
| Opt-in preference (learner) | ❌ Missing column + UI |
| Group management UI | ❌ Admin only API |

### Admin Frontend
| Feature | Status |
|---------|--------|
| Approvals dashboard | ❌ API only |
| Payments verification UI | ❌ API only |
| Course management (CRUD) | ❌ API only |
| Student management | ❌ API only |
| Analytics/dashboard | ❌ Not built |

### Security & Compliance
| Item | Status |
|------|--------|
| RLS policies tested against real Supabase auth | ❌ Not tested |
| Backup/restore procedure | ❌ Not documented |
| Disaster recovery test | ❌ Not done |
| Privacy policy / Terms of Service | ❌ Not written |
| Cookie consent / GDPR | ⚠️ Not implemented |
| Data retention policy | ❌ Not defined |
| Support contact page | ❌ Missing |
| Refund policy page | ❌ Missing |

### Deployment & Operations
| Item | Status |
|------|--------|
| Railway backend deployed | ❌ Not deployed |
| Vercel frontend deployed | ❌ Not deployed |
| Supabase migrations run | ⚠️ Phase 1 run, Phase 2 pending |
| WasenderAPI webhook registered | ❌ Needs Railway URL |
| CI/CD pipeline | ✅ GitHub Actions configured |
| Load testing | ❌ Not done |
| Monitoring/alerting | ❌ Not configured |

---

## Pilot Course Readiness (IELTS Preparation)

| Component | Status | Notes |
|-----------|--------|-------|
| Course metadata in config | ✅ | Name, dates, price, groups, MoMo/Telecel |
| Course in Supabase | ⚠️ | Needs insert via migration |
| Price: GHS 100 (≈$6-7) | ✅ | Within $2-50 range |
| Seat reservation: GHS 15 (~$1) | ✅ | Admission letter on verification |
| MoMo: +233548014157 | ✅ | In config |
| Telecel: +23333206967251 | ✅ | In config |
| Reference: ILETS | ✅ | In config |
| Proof group: IPtb2v6EzQUJ6LGLrObDrw | ✅ | In config |
| Access group: HZpPBTfKDQq7aVYOgpUFkw | ✅ | In config |
| Lesson materials | ❌ | Need to create |
| Assessments | ❌ | Need to create |
| Certificate template | ❌ | Need to create |
| Support email/phone | ⚠️ | Config has placeholders |

---

## Recommended Pilot Launch Sequence

1. **Choose payment provider** (Paystack vs SeefCash vs Stripe) — 1 day
2. **Create Supabase records** for IELTS course + test student — 1 day
3. **Build 3-4 frontend pages** (catalogue, course detail, login, register) — 1 week
4. **Create 5-10 lesson MDX files** for pilot — 3 days
5. **Configure payment provider sandbox** — 2 days
6. **Test full enrolment flow** with mock/sandbox — 2 days
7. **Deploy preview** (Vercel + Railway) — 1 day
8. **Recruit 10-20 pilot learners** — 1 week
9. **Run 2-week pilot** — 2 weeks
10. **Measure & decide** — 1 week

**Total to pilot launch: ~3-4 weeks**

---

## Go/No-Go Criteria for Pilot Launch

| Criterion | Must Pass |
|-----------|-----------|
| All 56 backend tests pass | ✅ |
| Frontend builds without errors | ❌ |
| Full enrolment flow works (mock payment) | ⚠️ Partial |
| Admin can verify payment → enrolment created | ✅ |
| Daily job runs without errors | ✅ |
| IELTS reminder creates approval → sends | ✅ |
| No secrets in repo | ✅ |
| RLS blocks cross-user access | ⚠️ Untested |
| Privacy/terms pages exist | ❌ |
| Support email monitored | ❌ |

---

## Sign-Off Required Before Public Launch

- [ ] Payment provider selected and live credentials configured
- [ ] WasenderAPI account created, webhook registered
- [ ] Supabase Phase 2 migration run, RLS verified
- [ ] Frontend deployed to Vercel preview, tested on mobile
- [ ] Backend deployed to Railway, health checks pass
- [ ] Privacy policy, terms, refund policy published
- [ ] Support email monitored, response SLA defined
- [ ] Pilot course content reviewed and approved
- [ ] Backup/restore tested
- [ ] Load test: 100 concurrent learners, daily job < 5 min