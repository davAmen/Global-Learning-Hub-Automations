# Global Learning Hub — Full System Specification
## WhatsApp Community LMS with Autonomous Agent

**Version:** 1.0
**Date:** 2026-10-04
**Status:** DESIGN PHASE — Not yet implemented

---

## 1. Executive Summary

Build a comprehensive Learning Management System centered on WhatsApp Communities, with an autonomous AI agent that monitors source communities, manages courses/payments/students, creates content, and operates with human-in-the-loop approval. Eventually migrate to a standalone web application.

---

## 2. Current System (Phase 1 - COMPLETED)

| Component | Status |
|-----------|--------|
| Daily reminders for Supabase courses | ✅ Done |
| Individual student messages via WasenderAPI | ✅ Done |
| Engagement tracking (active/low/followup) | ✅ Done |
| Daily report to admin | ✅ Done |
| Frontend (Next.js) with run-job button | ✅ Done |
| APScheduler (8 AM daily) | ✅ Done |
| Idempotency, rate limiting, logging | ✅ Done |

**Limitation:** Only sends 1:1 messages, no group support, no webhooks, no agent, no payments, no external integrations.

---

## 3. Target System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        WEB APPLICATION                          │
│  (React + FastAPI) — Admin dashboard, approvals, analytics     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  AGENT CORE   │    │  WHATSAPP     │    │  EXTERNAL     │
│  (LangGraph)  │◄──►│  GATEWAY      │    │  INTEGRATIONS │
│               │    │  (Wasender)   │    │               │
│ - Scheduler   │    │ - Send/Recv   │    │ - Laplage API │
│ - Router      │    │ - Webhooks    │    │ - MoMo/Telecel│
│ - Approval    │    │ - Groups      │    │ - Email/SMS   │
│ - Content Gen │    │ - Communities │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL (Supabase)                        │
│  Students | Courses | Enrollments | Payments | Groups          │
│  Messages | Approvals | AgentState | Content | AuditLog        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Core Components

### 4.1 WhatsApp Gateway (WasenderAPI)
- **Send:** Text, images, documents to groups & individuals
- **Receive:** Webhooks for incoming messages, delivery status, group events
- **Groups:** List, create, manage participants, generate invite links
- **Communities:** Announcement groups, subgroups

### 4.2 Agent Core (LangGraph / LangChain)
```
┌────────────────────────────────────────┐
│           AGENT STATE MACHINE          │
├────────────────────────────────────────┤
│  MONITOR → EXTRACT → ROUTE → APPROVE → │
│  SEND    → LOG    → FOLLOWUP           │
└────────────────────────────────────────┘
```

**Capabilities:**
- Monitor "Official Training Provider" community (282 participants)
- Extract training materials, announcements, new courses
- Route to: Global Learning Hub announcement group OR specific class group
- Generate course flyers (image + text) with admin details
- Create new groups for new courses
- Manage payment verification workflows
- Schedule recurring reminders (cron-like)
- Human-in-the-loop approval before ANY send

### 4.3 External Integrations

| Integration | Purpose | Auth |
|-------------|---------|------|
| `https://app.laplagemetaverse.org` | Training provider dashboard, course mgmt | Email/password |
| `https://student.laplagemetaverse.org/dashboard` | Student accounts, progress | Email/password |
| MoMo (`+233548014157`) | Payment collection | Manual verification |
| Telecel (`+23333206967251`) | Payment collection | Manual verification |
| WasenderAPI | WhatsApp messaging | Bearer token |

### 4.4 Web Application (Phase 3+)
- **Admin Dashboard:** Approve messages, view analytics, manage courses
- **Student Portal:** View courses, submit payments, access materials
- **Agent Monitor:** See agent decisions, override, configure rules
- **Payment Tracker:** Verify proofs, mark paid, grant access

---

## 5. Database Schema (Supabase/PostgreSQL)

```sql
-- Existing (Phase 1)
students, courses, enrollments, engagement_log, reminder_log

-- New Tables
payments (
  id uuid PK,
  student_id uuid FK,
  course_id uuid FK,
  amount decimal,
  currency text, -- 'GHS'
  method text, -- 'momo' | 'telecel'
  reference text, -- 'ILETS'
  proof_url text, -- screenshot upload
  status text, -- 'pending' | 'verified' | 'rejected'
  verified_by uuid FK, -- admin
  verified_at timestamptz,
  created_at timestamptz
)

groups (
  id uuid PK,
  whatsapp_jid text UNIQUE, -- '123456@g.us'
  name text,
  type text, -- 'announcement' | 'class' | 'community'
  parent_community_jid text,
  course_id uuid FK,
  created_at timestamptz
)

agent_state (
  id uuid PK,
  session_id text,
  current_task jsonb,
  last_run timestamptz,
  config jsonb -- rules, schedules, mappings
)

approvals (
  id uuid PK,
  agent_action_id uuid,
  content text,
  target_group_jid text,
  status text, -- 'pending' | 'approved' | 'rejected' | 'modified'
  requested_at timestamptz,
  reviewed_at timestamptz,
  reviewed_by uuid FK,
  notes text
)

content_library (
  id uuid PK,
  type text, -- 'flyer' | 'announcement' | 'material'
  title text,
  content text,
  image_url text,
  course_id uuid FK,
  created_by text, -- 'agent' | 'admin'
  created_at timestamptz
)

audit_log (
  id uuid PK,
  actor text, -- 'agent' | 'admin' | 'system'
  action text,
  entity_type text,
  entity_id uuid,
  details jsonb,
  created_at timestamptz
)
```

---

## 6. Key Workflows

### 6.1 IELTS Class (Oct 15-30, 6-8pm GMT)
```
Daily at 5:00 AM GMT (Oct 1 - Oct 30):
  1. Agent checks: course active? payments open?
  2. Generates reminder with:
     - Date/time reminder
     - Payment: GHS 100 to MoMo +233548014157 or Telecel +23333206967251
     - Reference: "ILETS"
     - Proof submission: Group A (https://chat.whatsapp.com/IPtb2v6EzQUJ6LGLrObDrw)
     - Access granted: Group B (https://chat.whatsapp.com/HZpPBTfKDQq7aVYOgpUFkw)
  3. Sends to Global Learning Hub announcement group
  4. Logs to audit_log
```

### 6.2 Training Provider Monitoring
```
Every 15 minutes (configurable):
  1. Agent logs into laplagemetaverse.org (stored credentials)
  2. Scrapes "Official Training Provider" community
  3. Detects new: materials, announcements, courses, flyers
  4. For each new item:
     a. Classify: general announcement? specific class? new course?
     b. Route to appropriate group(s)
     c. Create approval request
  5. Admin reviews in web app → approve/reject/modify
  6. On approve: agent sends to target group(s)
```

### 6.3 Payment Verification
```
When student sends proof in Group A:
  1. Webhook receives message (image/document)
  2. Agent extracts: student phone, amount, reference
  3. Creates payment record: status='pending'
  4. Notifies admin for verification
  5. Admin verifies in web app → status='verified'
  6. Agent adds student to Group B (class access)
  7. Sends welcome message with schedule
```

### 6.4 New Course Creation
```
When Training Provider posts new course:
  1. Agent detects new course flyer/announcement
  2. Extracts: name, description, schedule, price
  3. Creates course in DB
  4. Creates WhatsApp group via WasenderAPI
  5. Generates flyer with admin details (David Amenuku, amenukudavid20@gmail.com, +233206967251)
  6. Creates approval: "New course detected - create group & announce?"
  7. On admin approve:
     - Creates group in Global Learning Hub community
     - Sends announcement to general page with group link
     - Shares flyer to admin's WhatsApp status (via WasenderAPI)
     - Emails flyer to admin
```

### 6.5 Student Management (via Laplage Dashboard)
```
Agent capabilities (with approval):
- View student enrollments, progress
- Create/enroll students in courses
- Generate course flyers
- Manage student accounts
- Run lead generation campaigns
```

---

## 7. Phased Implementation Plan

### Phase 1: Foundation (Weeks 1-3) ✅ PARTIAL
- [x] Supabase schema, FastAPI, WasenderAPI 1:1 messages
- [ ] **Add: Group messaging, webhook receiver, payment tables**
- [ ] **Add: IELTS course + daily group reminders (5am GMT)**
- [ ] **Add: Admin approval UI (simple)**

### Phase 2: Agent Core (Weeks 4-8)
- [ ] LangGraph agent with monitor/extract/route/approve/send loop
- [ ] Training Provider scraper (laplagemetaverse.org)
- [ ] Payment verification workflow
- [ ] Group management (create, invite, participant sync)
- [ ] Content generation (flyers via template + image API)

### Phase 3: Web Application (Weeks 9-14)
- [ ] Admin dashboard (React + FastAPI)
- [ ] Approval queue UI
- [ ] Course/Student/Payment management
- [ ] Agent configuration & monitoring
- [ ] Analytics & audit logs

### Phase 4: Advanced Features (Weeks 15-20)
- [ ] Student portal (view courses, submit proofs)
- [ ] Automated flyer generation (image templates)
- [ ] WhatsApp Status posting via API
- [ ] Email notifications
- [ ] Multi-course level handling (existing group reuse)

### Phase 5: Migration & Hardening (Weeks 21-26)
- [ ] Full web app replaces WhatsApp for core flows
- [ ] WhatsApp becomes notification layer only
- [ ] Load testing, security audit
- [ ] Documentation, runbooks
- [ ] Production deployment (Railway + Vercel + Supabase)

---

## 8. Tech Stack

| Layer | Choice |
|-------|--------|
| **Agent Framework** | LangGraph (stateful, human-in-the-loop) |
| **LLM** | GPT-4o / Claude 3.5 (for extraction, classification, generation) |
| **Backend** | FastAPI (existing) + new agent services |
| **Frontend** | Next.js (existing) + new admin dashboard |
| **Database** | Supabase/PostgreSQL (existing) |
| **Scheduler** | APScheduler (existing) + Celery for async tasks |
| **WhatsApp** | WasenderAPI (existing) + webhooks |
| **Scraping** | Playwright (for laplagemetaverse.org login) |
| **Image Gen** | DALL-E 3 / Stable Diffusion API for flyers |
| **Hosting** | Railway (backend), Vercel (frontend), Supabase (DB) |
| **Monitoring** | Sentry, structured logs |

---

## 9. Security & Compliance

- **Credentials:** Vault/encrypted env vars (never in code)
- **WhatsApp:** Rate limits, opt-out handling, business policy compliance
- **Payments:** No storage of sensitive payment data, only proofs
- **Approval:** Zero sends without admin approval (configurable)
- **Audit:** Full trail of every agent action
- **Access:** Role-based (admin, agent, viewer)

---

## 10. Immediate Next Steps (This Week)

| Task | Owner | Effort |
|------|-------|--------|
| Get WhatsApp unrestricted & WasenderAPI session connected | You | 1 day |
| Get real Group JIDs for both communities | You | 30 min |
| Add `groups`, `payments`, `approvals` tables to Supabase | Me | 2 hrs |
| Implement IELTS daily group reminder (5am GMT) | Me | 3 hrs |
| Build simple approval endpoint + UI | Me | 4 hrs |
| Test end-to-end: reminder → group → approval → send | Me | 2 hrs |

---

## 11. Questions for Clarification

1. **LaplageMetaverse API:** Does `app.laplagemetaverse.org` have a REST API, or must we scrape via Playwright?
2. **WhatsApp Status API:** Does WasenderAPI support posting to Status? (Check dashboard)
3. **Payment Verification:** Manual only, or integrate with MoMo/Telecel APIs?
4. **Flyer Templates:** Design specifications? Brand assets?
5. **Agent Autonomy Level:** Start with "propose only, admin approves all" — confirm?
6. **Team:** Solo dev, or will others contribute?

---

## 12. Budget Estimate (Rough)

| Phase | Dev Weeks | Est. Cost (Solo Dev) |
|-------|-----------|---------------------|
| Phase 1 Completion | 1 | $2-3k |
| Phase 2: Agent Core | 5 | $10-15k |
| Phase 3: Web App | 6 | $12-18k |
| Phase 4: Advanced | 6 | $12-18k |
| Phase 5: Migration | 6 | $12-18k |
| **Total** | **~24 weeks** | **$50-70k** |

---

**Next Action:** Confirm Phase 1 completion items (Group JIDs, IELTS reminders, approval flow) and I'll start implementation.