# Product and Safety Readiness Audit

**Review date:** 2026-10-11
**Branch:** `feat/phase-2-attendance`
**Result:** The current code passes its existing tests and builds, but it is not ready to process real learner records, send live messages, or sell courses. The public Vercel site is only an entry page and share QR; it is not a learner, teacher, classroom, or payment application.

## What is actually implemented

- A FastAPI daily reminder service using Supabase, with WhatsApp as the Phase 1 learner channel and Telegram for administrator reports.
- Local-only authenticated record routes and eligibility logic for a separate weekly device-readiness notice. There is no weekly scheduler, provider send path, or learner-facing sign-in/consent screen.
- A static Next.js `/learn` entry page and `/qr` share page deployed at <https://globallearninghub.vercel.app>.
- No course catalog, classroom platform, attendance, tutor tools, AI operations, checkout, receipts, refunds, or paid entitlements.

The deployment contains only the public frontend. The backend, database, real learner data, and messaging are not deployed or authorized for live use.

## Local changes made in this audit

1. Enabled row-level security on the five Phase 1 data tables, revoked direct `PUBLIC`, `anon`, and `authenticated` table access, and explicitly granted the server-only `service_role` the `SELECT`, `INSERT`, and `UPDATE` privileges the backend needs. No client policy was added because the browser has no direct database access.
2. Changed `.env.example` to use the valid SMTP default `587`. Added configuration validation for scheduler hour/minute, SMTP port, and a finite, strictly positive send delay.
3. Made sample IDs deterministic so repeated seeding upserts the same fictional rows. Added a required `--confirm-test-database` command-line flag before the script creates a database client or writes. The flag is a reminder, not proof that the configured database is non-production.
4. Added tests protecting these behaviors. No sample script, live database, provider, recipient, or production deployment was run as part of this audit.

The SQL edits are only local source changes. They do not alter an existing Supabase project. Before any real data is stored, an authorized operator must inspect the actual live table grants/RLS state and separately authorize any migration. Supabase's guidance says exposed `public` tables need explicit RLS and grants; the live project's current state was not inspected ([Supabase table security](https://supabase.com/docs/guides/database/tables)).

## Verification

- Backend: **82 passed**, with one existing Starlette/httpx deprecation warning.
- Python compile check: passed.
- `pip check`: no broken installed requirements.
- Frontend production build: passed; static routes `/`, `/learn`, and `/qr` generated.
- `npm audit --omit=dev` previously reported **0 known vulnerabilities** in the locked frontend dependency graph. The close-out recheck could not reach `registry.npmjs.org` from this environment, so current frontend advisory status is not freshly verified.
- `git diff --check`: passed.
- Tracked-file scan found no `.env`/private-key files or common credential patterns. This pattern scan is not a replacement for a dedicated secret-scanning service.
- A Python dependency advisory query could not complete because the OSV TLS connection failed. Python dependency vulnerabilities therefore remain **unverified**.
- The browser did not confirm the QR PNG download in this audit; test it manually in a regular browser before relying on the saved image.

## Release and safety blockers

### Must resolve before any real WhatsApp reminder

The Phase 1 scheduler currently selects active enrollments and sends WhatsApp reminders without checking a separate, purpose-specific class-reminder opt-in or current opt-out. The existing consent events cover only `device_readiness_weekly`; they cannot authorize a different class-reminder purpose. Meta's current policy requires opt-in permission and honoring opt-outs, and recommends separating consent by message category ([WhatsApp Business Messaging Policy](https://whatsappbusiness.com/policy/?lang=en_US)). Do not add real contacts or enable sending until a separately designed and tested class-reminder consent gate, durable opt-out handling, approved notice wording, and support route exist.

Adding that gate changes Phase 1 send eligibility and needs an explicit, documented data/API design. The operator decision is still pending; until it is resolved and the gate is tested, treat live WhatsApp reminders as blocked. Do not silently reuse readiness-notice consent. No live send was attempted.

### Must resolve before processing Ghana learner data

The project has no published privacy notice/terms, declared data-retention schedule, age/guardian policy, or identified support/privacy contact. Ghana's Data Protection Commission says organizations processing personal data must register, appoint/train a data protection supervisor, publish a privacy policy, and inform people about collection and use. Confirm the business's obligations and wording with the DPC and qualified Ghanaian counsel before a pilot ([DPC for organisations](https://dpc.gov.gh/for-organisations/)). This is a launch gate, not a legal conclusion that the current local-only code is already processing learners.

### Must resolve before backend deployment

- `SUPABASE_KEY` is documented as a legacy `service_role` key. Supabase says legacy `anon`/`service_role` keys are being deprecated by the end of 2026 ([migration guidance](https://supabase.com/docs/guides/getting-started/migrating-to-new-api-keys)). The installed Python client's header behavior must be verified against the new non-JWT secret-key requirements before changing configuration; no key was read, rotated, or migrated here.
- Phase 1 operator endpoints still use one shared admin key. The readiness API has server-side Supabase Auth checks, but there is no safe user-facing staff/learner login, account recovery, or profile provisioning workflow.
- The Supabase schema has not been validated against a live database, and the new RLS statements have not been run.
- Backend dependencies in `requirements.txt` are not locked to exact versions; no Python advisory scan completed. There is no configured CI workflow in this checkout.
- Next.js announced an out-of-band upstream security update scheduled for 2026-10-14. Re-run the dependency audit and use the patched supported release before the next frontend deployment ([Next.js announcement](https://nextjs.org/blog)).

### Must resolve before selling courses

There is no catalog or protected learner portal, no checkout provider, no verified order/entitlement flow, and no receipts/refunds/reconciliation. The existing Phase 2 manual payment event is only an internal eligibility record for the proposed weekly notice; it is not payment acceptance or proof of purchase. Before checkout: approve the business/merchant identity, supported countries and currencies, price/fee/tax display, reservation credit/refund rules, age/privacy terms, customer support, and payment provider. Implement signed webhook verification, deduplication, order state, refunds, and access entitlements in a separately activated phase.

### Must resolve before classroom/attendance launch

The local-first classroom and attendance system is still design-only. Offline identity and expiry, session/time-zone and late/excused states, correction audit, learner notice/consent, retention, device fallback, backup/restore, and site operations remain open in `ARCHITECTURE.md`. No passive device sensing, automated withdrawal, or AI-only learner decision is permissible under the current project rules.

## Recommended next order

1. Finish the consent-gate decision and design the separate Phase 1 class-reminder consent/opt-out record. Keep live sends disabled until the design, notice, migration, and provider policy are reviewed.
2. Confirm the actual Supabase grants and resolve the new API-key compatibility path; separately authorize any live migration or credential operation.
3. Settle the Ghana privacy, age, retention, support, and business-entity gates before real learner data or a pilot.
4. Choose one activated product phase at a time: protected accounts, classroom/attendance, then catalog/enrollment, then payments/entitlements, then reviewed content/tutors/AI, and finally ethical marketing/partnerships. Do not build all of these into the current reminder service at once.
5. Recheck the QR PNG download in a regular browser and re-run dependency scans after the announced Next.js security release.

No GitHub push, backend deployment, migration, real-data entry, external message, payment, or advertisement was performed for this audit.
