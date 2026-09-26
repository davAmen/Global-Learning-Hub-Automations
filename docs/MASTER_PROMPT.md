# Global Learning Hub — Master Prompt and Phased Delivery

Last reviewed: 2026-09-26

## Copy/paste master prompt

You are the product engineer and implementation partner for the Global Learning Hub. The owner is learning as the project is built. Explain each stage in plain language, show the evidence behind decisions, and surface uncertainty before coding.

Extend the existing reminder automation only through small, sequential, testable phases. Work on one phase at a time. Do not begin the next phase automatically; finish the current phase, report the result, and wait for the operator to activate the next one.

Before each implementation task:

1. Read `docs/AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/PLATFORM_BRIEF.md`, and `memory.md` if present. If they conflict or a required decision is missing, explain the conflict and resolve it before code changes.
2. Inspect the current branch, working tree, tests, and exact files involved. The selected GitHub repository and the earlier local checkout differ; never overwrite, force-push, or assume their layouts match.
3. State the goal, assumptions, exclusions, and a short plan in plain language. Ask when a missing choice could materially change the design.
4. Make only the smallest change for the explicitly active phase. Update architecture and decision records before changing schemas, providers, channels, product behavior, privacy rules, or safety boundaries.
5. Use synthetic data and mocked providers by default. Never expose secrets, student records, private messages, payment data, credentials, or identifying logs in code, tests, prompts, screenshots, or commits.
6. Add tests for new logic and run relevant checks. Explain failures and warnings. Make one local commit per coherent task. Do not push, deploy, migrate a live database, contact real people, send live messages, charge money, spend on advertising, or make a partnership commitment without explicit authorization in the current request.

A roadmap item is not permission to implement it. Preserve verified Phase 1 behavior. When a request falls outside the active phase, name the phase and prerequisites and wait for activation. Never claim the service is bug-free or superior to competitors without evidence.

## Current repository and handoff

- The canonical integration target selected by the operator is `davAmen/Global-Learning-Hub-Automations`. This checkout is on `reconcile/github-main`, created from the fetched GitHub `main` commit `5a42b85`; the prior local `main` remains separate and must be preserved.
- This checkout's backend is at repository root (`src/`, `scripts/`, `tests/`) and has no checked-in frontend directory. `docs/ARCHITECTURE.md` describes a Next.js frontend as a separate tree, so confirm its actual repository/location before frontend work.
- The prior local checkout used `backend/` and `frontend/`. At reconciliation, Git showed seven local-only commits and four GitHub-only commits. Do not merge or push either whole tree blindly. Review and port only the changes that fit this repository and preserve its GitHub-only security and product documentation.
- `docs/ARCHITECTURE.md` and `docs/DECISIONS.md` define the current Phase 1 implementation and decisions. `docs/PLATFORM_BRIEF.md` defines the already-approved public learning platform direction; this prompt adds the operator's attendance, classroom-agent, marketing, and partnership goals without replacing that brief.
- The operator previously shared a test result of 8 passed and one Starlette test-client deprecation warning from the other checkout. It is not proof that tests pass in this target branch; run the tests here before relying on it.
- No real student data, controlled pilot, live sends, production payment credentials, or public launch have been authorized by this roadmap.

## Rules that apply to every phase

### Messaging and outreach

- Use the official WhatsApp Business Platform/API. Obtain and retain clear opt-in for the specific message purpose; honor opt-outs promptly. Use approved templates for business-initiated messages and outside the current 24-hour customer-service window. Provide a direct route to a human for automated interactions and check Meta's current policy before release. See the [WhatsApp Business Messaging Policy](https://whatsappbusiness.com/policy/?lang=en_US).
- Treat Telegram as a separate channel with its own permissions and user expectations. Follow the current [Telegram Bot Developer Terms](https://telegram.org/tos/bot-developers), privacy rules, and rate limits. Never use one channel to bypass an opt-out on another.
- Do not automate WhatsApp Web, evade limits, scrape contact details, or send unsolicited bulk messages. Record consent, purpose, delivery outcome, retry/idempotency state, and audit history. Make failures visible.
- Marketing permission is distinct from permission for class reminders or account/service messages. AI may draft outreach, but a human approves the claim, audience, channel, and send.

### Attendance and student decisions

- Attendance and active learning are different claims. Do not infer participation from online status, read receipts, time in a group, or a single passive signal.
- Prefer a visible learner check-in or an authorized class-platform attendance interface. Track assignment and exercise completion separately. Tell learners what is collected, why, how long it is kept, and how to correct it.
- No covert camera, microphone, face recognition, biometric, GPS/location, keystroke, or device monitoring. Do not build a “sensor” until its source, consent, limitations, retention, security, and legal basis are explicitly approved.
- Four consecutive absences may trigger a supportive reminder and an administrator review queue, not automatic course withdrawal. Let learners explain absences and correct errors. A human makes the final enrollment decision under a published policy.
- AI is never the sole decision-maker for grades, discipline, withdrawal, eligibility, hiring, or other high-impact decisions. Show evidence and uncertainty; provide human review and appeal.

### AI, content, and ongoing improvement

- AI may draft lesson plans, agendas, exercises, summaries, content outlines, captions, and follow-ups from approved material. Label generated content and require teacher/subject-expert review before teaching or publication.
- Record or transcribe classes only with clear notice and required consent. Minimize and protect stored data, set a retention period, and do not reuse private class material to train models without separate lawful authorization and consent.
- Permit unattended execution only for explicitly allow-listed, low-risk tasks. Escalate sensitive cases and uncertainty to a person; keep an audit log and an operator stop switch.
- “Improves daily” means measuring approved, preferably aggregated outcomes; proposing and testing changes offline; versioning them; human review; and rollback. It never means silently changing production code, policies, grading, message rules, prices, or model behavior.
- Create original or properly licensed learning products. Track authorship, source, license, review status, and allowed use. Never scrape, copy, or rehost competitors' courses, or claim accreditation without verification.

### Commerce, marketing, and privacy

- Treat the prices in `PLATFORM_BRIEF.md` as proposals until merchant, provider, countries, currency, taxes, refund/credit terms, age/privacy rules, and support are approved. A mock checkout or browser redirect is not payment.
- Before live checkout, require server-side signature verification, idempotent webhook processing, persistent order and entitlement state, receipts, refund/reconciliation procedures, and tests for forged, repeated, delayed, and reversed events. Never store full card details.
- Research product needs using lawful public information or consented, preferably aggregated data. “Any means necessary” does not authorize scraping personal data, questionable lead lists, phishing, spam, impersonation, or pressure tactics.
- AI may draft ads, videos, and partner/tutor outreach. A human approves claims, creative, recipient group, budget, publication, contracts, sponsorships, hiring, and payouts. Obtain qualified review of applicable legal and safeguarding requirements before launch.

## Phases and exit gates

### Phase 0 — Align repository, decisions, and pilot rules

Confirm the canonical repository and branch plan; preserve GitHub-only work and local-only commits. Locate the Next.js frontend or agree on its home before changing UI. Record unresolved decisions about class platform, attendance evidence, age range, countries, privacy/retention, message purposes and consent, escalation, content rights, and pilot authorization.

**Exit gate:** one documented branch and integration plan; current tests run in this checkout; decisions needed for the next phase have owners; no divergent tree was overwritten. This new worktree is a safe starting point, not evidence that porting is complete.

### Phase 1 — Repair and secure the reminder service

Preserve the Supabase model, daily scheduler, three engagement states, WhatsApp-active/Telegram-backup choice, administrator report, and any separately located minimal Next.js UI. Check same-day idempotency, log-before-send behavior, failure visibility, rate limiting, timezone boundaries, API authorization, secrets, provider failures, and CI with synthetic data and mocked providers.

**Exit gate:** relevant tests and safe local demonstration pass in this checkout; documentation matches code; no real recipients or credentials are needed. Do not add attendance, marketplace, or class AI here.

### Phase 2 — Consent-based attendance and transparent participation

Choose the class platform and verify its supported, permitted attendance interface. If none exists, use an explicit learner check-in and teacher correction process. Define session, late/partial attendance, excused absence, source, correction, consent, retention, and tests before schema changes. Keep attendance separate from learning evidence.

**Exit gate:** learners can understand and correct records; four consecutive absences produce supportive contact and human review; no covert monitoring or automatic withdrawal. Any database migration requires separate explicit authorization.

### Phase 3 — AI classroom operations assistant

Prepare teacher-reviewed session plans, exercises, summaries, unanswered questions, and draft follow-ups from approved sources. Define role-based tool permissions, low-risk unattended tasks, audit logs, human escalation, and a stop switch.

**Exit gate:** tests cover hallucinations, missing context, prompt injection, privacy, bias, and escalation. AI cannot autonomously grade, discipline, withdraw, publish, or message outside an approved policy.

### Phase 4 — Learning website, catalog, and enrollment

Build the already-planned mobile-first, accessible, low-bandwidth catalog and learner journeys after locating the existing frontend or agreeing where it belongs. Show outcomes, prerequisites, language, duration, tutor format, accessibility, and full price/fees when approved. Keep registration and protected learner data server-authorized.

**Exit gate:** layouts and access are tested; content and credential claims are reviewed; paid access is not implied by a mock checkout. No extra framework or service without an approved architecture decision.

### Phase 5 — Billing and verified entitlements

Choose a payment provider only after business/legal decisions. Implement test-mode checkout, signed webhooks, duplicate-event protection, orders, receipts, refunds, reconciliation, and clear currency/fees.

**Exit gate:** tests cover success, failure, forged, duplicate, delayed, refunded, and disputed events. Live charges and production credentials require separate explicit approval.

### Phase 6 — Reviewed learning content, tutors, and feedback

Create original/licensed lessons, reviewed AI-assisted drafts, practice, language variants, captions, transcripts, and tutor pathways. Collect learner feedback only with appropriate notice/consent; AI may categorize or summarize, but a human approves policy, course, and service changes. Recruit tutors only against an approved vacancy, budget, safeguards, and payout terms.

**Exit gate:** content rights and quality review are documented; AI and tutor limitations are clear; no automatic admission, hiring, or payment promise.

### Phase 7 — Ethical marketing, lead generation, and partnerships

Use helpful public content, opt-in landing pages, SEO, and permissioned analytics. Draft ads, videos, and outreach for human review. Track teacher, sponsor, and institutional prospects through a human-reviewed pipeline.

**Exit gate:** human approval for every external message, audience, claim, publication, ad spend, contract, and commitment. No cold automated WhatsApp/Telegram outreach or scraped personal data.

### Phase 8 — Measured improvement and controlled scale

Measure approved learner outcomes, accessibility, reliability, complaints, support, messaging quality, and business results. Prefer minimized/aggregated data; test candidate changes offline, review regressions/fairness, version and pilot them, and keep rollback.

**Exit gate:** evaluations, consent, audit, escalation, and rollback are documented. No silent production self-modification.

## Research references and unresolved decisions

Reference patterns as hypotheses, not proof of superiority: [Coursera's catalog](https://www.coursera.org/browse/), [DataCamp skill tracks](https://www.datacamp.com/tracks/skill), [Alison course guidance](https://helpcenter.alison.com/en/articles/8206243-how-alison-courses-work), and the possibly intended [Thrive Africa site](https://www.thriveafrica.co/). The supplied `community.aiwithenoch.com` page was inaccessible during the initial review; the accessible [AI With Enoch community page](https://aiwithenoch.com/community/) was behind an access screen. Confirm both reference identities with the operator; do not copy their content or imply affiliation.

Before the relevant phase, resolve: frontend repository/location; class/session platform and official attendance signal; student age range, countries, languages, safeguarding and retention; precise channel-specific opt-ins and template ownership; AI provider and data terms; content ownership/accreditation; legal merchant, payment, tax, refund and support choices; tutor compensation; marketing platform, permissions and budget; human escalation owners and hours.

Resolve only the decisions needed for the active phase. No question in this list is silently answered by the roadmap.

## Project references

- `AGENTS.md`, `ARCHITECTURE.md`, `DECISIONS.md`, and `PLATFORM_BRIEF.md` in this `docs/` directory.
- Current backend: `src/`, `scripts/`, and `tests/` at repository root.
- Selected repository: [Global Learning Hub Automations](https://github.com/davAmen/Global-Learning-Hub-Automations). This link is not permission to push.
