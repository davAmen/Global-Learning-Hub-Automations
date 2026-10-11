# Global Learning Hub - Audit Report
**Date:** 2026-10-07  
**Auditor:** opencode (senior product engineer)

---

## Executive Summary

The repository contains a **partially implemented Phase 1+** automation system with significant additional infrastructure (payments, groups, approvals, audit logs) that goes beyond the original Phase 1 scope. However, **critical learner-facing features are missing** — no course catalogue, no enrollment flow, no student dashboard, no authentication, and no payment provider integration.

**Test Status:** 56/56 backend tests passing (after fixing config validation and test mocking issues). Frontend has no tests.

---

## Claims vs. Reality

| Claim (from SPEC_FULL_SYSTEM.md) | Reality | Evidence |
|----------------------------------|---------|----------|
| "Phase 1 COMPLETED" | **Partially true** — Core reminder automation works, but README says "currently email" while code uses WhatsApp | `backend/README.md` line 14 vs `config.py` line 21 |
| "Daily reminders for Supabase courses" | ✅ **Implemented** | `scheduler.py`, `main.py` APScheduler |
| "Individual student messages via WasenderAPI" | ✅ **Implemented** | `whatsapp_channel.py` |
| "Engagement tracking (active/low/followup)" | ✅ **Implemented** | `engagement.py` |
| "Daily report to admin" | ✅ **Implemented** | `daily_report.py`, `/reports/today` |
| "Frontend (Next.js) with run-job button" | ✅ **Implemented** | `frontend/app/run/page.tsx` |
| "APScheduler (8 AM daily)" | ✅ **Implemented** | `main.py` lifespan |
| "Idempotency, rate limiting, logging" | ✅ **Implemented** | `scheduler.py` already_sent check, 6s delay |
| "Only sends 1:1 messages, no group support" | ❌ **False** — Group messaging implemented | `ielts_reminder.py` sends to groups, `payments.py` adds to groups |
| "No webhooks" | ❌ **False** — Webhooks fully implemented | `routes_webhooks.py` with HMAC verification |
| "No payments" | ❌ **False** — Payment tables, API, webhook handling exist | `routes_payments.py`, `routes_webhooks.py` handle_payment_proof |
| "No agent" | ✅ **True** — No LangGraph agent yet | Only scheduler-based automation |
| "Payments table with MoMo/Telecel" | ✅ **Implemented** (schema + API) | `schema.sql`, `routes_payments.py` |
| "Groups table with WhatsApp JIDs" | ✅ **Implemented** | `schema.sql`, `routes_groups.py` |
| "Approvals system" | ✅ **Implemented** | `routes_approvals.py`, `approvals` table |
| "Audit log" | ✅ **Implemented** | `audit_log` table, used in payments/webhooks |
| "Content library" | ✅ **Schema only** — No API/content yet | `schema.sql` table exists |
| "Agent state table" | ✅ **Schema only** — Not in current schema | Not in `schema.sql` |

---

## Critical Gaps for Learner-Facing Platform

### 1. **No Learner Authentication/Accounts**
- No user registration, login, session management
- No JWT/OAuth/OIDC integration
- No password reset, email verification

### 2. **No Course Catalogue (Public or Authenticated)**
- No `/courses` public listing with descriptions, prices, prerequisites
- No course detail pages
- No enrollment UI

### 3. **No Enrollment/Payment Flow**
- No learner-initiated enrollment
- No payment provider integration (Paystack/SeevCash)
- No $1 seat reservation vs full tuition distinction
- No admission/enrollment confirmation documents

### 4. **No Student Learning Experience**
- No lesson content delivery (text, video, interactive)
- No assessments/quizzes
- No progress tracking
- No completion certificates

### 5. **No RLS (Row Level Security)**
- Supabase tables have no RLS policies
- Frontend could access all data if connected directly

### 6. **Payment Integration Missing**
- Only manual MoMo/Telecel via webhook
- No Paystack/SeevCash provider adapters
- No sandbox/live mode separation
- No idempotent payment verification via provider API

### 6. **Bugs Found**
| File | Issue | Severity |
|------|-------|----------|
| `routes_payments.py:174` | `logger` used but not imported | High |
| `routes_payments.py:139` | `updated_at` column handling workaround | Medium |
| `config.py` | `smtp_port` validation fails on empty string | Fixed |
| Tests | `@pytest.mark.asyncio` on sync functions | Low (warnings) |

---

## Security Gaps

1. **No RLS policies** — Any authenticated Supabase client can read/write all tables
2. **Admin auth is header-based only** — `X-Admin-ID` header, no real auth
3. **No rate limiting on auth endpoints** — Could brute force
4. **No CORS restriction in production** — Allows `https://*.vercel.app` wildcard
5. **Webhook secret fallback** — Now fixed to require explicit secret
6. **No input validation on payment amounts** — Float used for money (should be integer minor units)

---

## Database Schema Issues

| Table | Issue |
|-------|-------|
| `payments` | `amount` is `decimal(10,2)` — OK, but API uses `float` |
| `courses` | No price, currency, enrollment capacity fields |
| `students` | No auth fields (password_hash, email_verified, etc.) |
| `enrollments` | No payment_status, enrollment_date vs start_date logic |
| `groups` | `type` check constraint doesn't include 'class' (SPEC uses 'class') |

---

## Staged Implementation Plan

### Stage 1: Foundation Fixes (Week 1) — **START HERE**
1. Fix `routes_payments.py` logger import bug
2. Add `price`, `currency`, `capacity` fields to courses
3. Add auth fields to students (password_hash, email_verified, role)
4. Create RLS policies for all tables
5. Add payment provider adapter interface (provider-neutral)

### Stage 2: Pilot Course & Catalogue (Week 2)
1. Define one pilot course with full metadata (outcomes, modules, assessments)
2. Build public course catalogue API + frontend pages
3. Implement learner registration/login (JWT + HttpOnly cookies)
4. Build enrollment API with seat reservation logic

### Stage 3: Payment Integration (Week 3)
1. Clarify: **Paystack or SeevCash?** (user mentioned "Haystack or SeevCash" — likely Paystack)
2. Implement chosen provider adapter with sandbox mode
3. Add idempotent webhook verification
4. Build payment flow: reserve → pay → verify → enroll

### Stage 4: Learning Experience (Week 4)
1. Lesson content delivery API
2. Progress tracking
3. Simple assessments
4. Completion certificate generation

### Stage 5: Pilot Launch (Week 5)
1. Deploy preview, test mobile/desktop
2. Recruit 10-20 pilot learners
3. Run 2-week pilot, measure metrics
4. Decide on expansion

---

## Recommended First Pilot Course

Based on existing IELTS infrastructure:
- **Course:** "IELTS Preparation (Oct 15-30, 6-8pm GMT)"
- **Price:** GHS 100 (≈ $6-7 USD) — within $2-50 range
- **Seat reservation:** $1 USD (≈ GHS 15)
- **Duration:** 2 weeks, 14 sessions
- **Outcome:** Ready for IELTS exam
- **Prerequisites:** Basic English proficiency
- **Support:** WhatsApp group + email

---

## Immediate Next Steps (This Session)

1. ✅ Fix test suite (DONE — 56/56 passing)
2. **Fix `routes_payments.py` logger bug**
3. **Add RLS policies migration**
4. **Add course pricing fields migration**
5. **Create provider-neutral payment adapter**
6. Document decisions in `DECISIONS.md`

---

## Files to Review/Modify Next

1. `backend/src/api/routes_payments.py` — Fix logger import
2. `backend/supabase_migration.sql` — Add RLS policies, course pricing fields, student auth fields
3. `backend/src/config.py` — Add payment provider config
4. `backend/src/payments/` (new) — Provider adapter interface
5. `frontend/app/courses/` (new) — Catalogue pages
6. `frontend/app/auth/` (new) — Login/register pages

---

## Questions Requiring User Decision

1. **Payment Provider:** Did you mean **Paystack** or **SeevCash**? (You mentioned "Haystack or SeevCash")
2. **Seat Reservation Policy:** Is $1 reservation separate from tuition? Does verified reservation = admission letter, or does full payment = admission letter?
3. **Authentication:** Email/password only, or add Google/OAuth?
4. **Course Content Format:** Markdown files in repo, CMS, or database-stored?
5. **Deployment Target:** Vercel for frontend confirmed. Backend on Railway confirmed?