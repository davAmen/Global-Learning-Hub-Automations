# Project memory

## 2026-09-26, Reconcile through an isolated GitHub-based branch

**What was decided:** Use `reconcile/github-main`, based on the selected GitHub repository's fetched `main`, as the safe place to integrate reviewed work. Preserve the earlier local `main`; port changes selectively after review.
**Why:** The local and GitHub branches diverged and use different layouts. The GitHub branch contains newer platform/security documentation and root-level `src/`, while the local branch contains `backend/` and `frontend/`.
**What was rejected:** Force-pushing or merging the entire local tree over GitHub, which could discard remote-only work or introduce incompatible paths.

## 2026-09-26, Log administrator report delivery attempts

**What was decided:** Use `reminder_log` for administrator report attempts, with a null `enrollment_id`; keep report attempts out of student reminder counts. Update the schema file only and do not migrate Supabase without explicit authorization.
**Why:** The send-attempt logging rule applies to administrator reports too, but those messages are not associated with a learner enrollment.
**What was rejected:** Sending without an audit record, inventing an enrollment, or creating a second log table.

## 2026-09-26, Use non-routable sample recipients for local tests

**What was decided:** Seed fake students with fictional 555-01xx phone placeholders and keep provider credentials blank during local tests.
**Why:** Plausible Ghanaian phone numbers in sample data could belong to real people and a configured provider could contact them accidentally.
**What was rejected:** Keeping realistic-looking local phone numbers or telling users to add live messaging credentials before a controlled pilot.

## 2026-09-26, Phase 1 hardening handoff on the selected GitHub branch

**What was decided:** Keep the reviewed changes on local branch `reconcile/github-main`, based on the selected repository's fetched `main`; preserve the old local `main`. The branch currently includes the roadmap, reminder pre-send logging, report-attempt logging, missing WhatsApp-recipient guard, and fictional seed recipients. Latest full test run: 18 passed, 1 Starlette deprecation warning.
**Why:** These changes address auditability and accidental-contact risks while retaining GitHub-only work and the staged scope.
**What was rejected:** Pushing before current-request authorization, force-pushing/merging the divergent local tree, and applying the nullable `reminder_log.enrollment_id` change to a live Supabase database without explicit authorization.

## 2026-09-27, Phase 2 attendance check-in direction — superseded in part

**Originally decided:** Phase 2 is activated for consent-based attendance. No class platform was selected; the initial design proposed visible learner-initiated check-in after verified learner login, with auditable teacher corrections. The no-platform direction was later superseded by the owned hybrid-platform decision below; the identity and correction safeguards remain.
**Why:** The repository has no class-platform integration, learner authentication, or attendance model; accepting a student ID alone could allow impersonation.
**What was rejected:** Covert sensing, attendance inferred from online/read status, and public check-ins using an unverified student ID. Define session, attendance-status, consent, correction, and retention rules before schema/API work.

## 2026-09-27, Hybrid local and remote classroom platform selected

**What was decided:** The operator wants an owned class platform that supports local classroom use over a LAN when internet is unavailable and remote online access when connectivity exists. This supersedes WhatsApp group management as the class-platform direction; the existing WhatsApp reminder service remains unchanged.
**Why:** The operator wants teachers and learners to exchange lessons and resources locally while still enabling remote access.
**What was rejected:** A permanently isolated platform as the only mode and a WhatsApp group as the classroom platform. “Interlink” remains undefined; assume LAN/intranet until clarified. The local/cloud source of truth, offline write ownership, synchronization/conflict rules, security, backup, and attendance policies must be decided before code or schema changes.

## 2026-09-27, Local classroom hub authority selected

**What was decided:** For each site, its local hub is the authoritative record keeper for class records created there during internet outages; it syncs those records to the online service after connectivity returns.
**Why:** This allows local classes to continue and record work without internet while retaining remote access when online.
**What was rejected:** Requiring the cloud to be reachable for every classroom write, or silently letting the cloud overwrite locally authoritative records.
**Still unresolved:** Sync acknowledgements/retries, duplicate handling, event ordering, remote-origin record ownership, corrections/conflicts, local storage, and backup/restore.

## 2026-09-27, Draft one-site classroom pilot workflow (proposal only)

**What was decided:** Record one learning site and one class as a provisional planning assumption, not as confirmed pilot scope or authorization to use real learner data. Recommend explicit learner check-in, separate assignment evidence, teacher-audited corrections, visible offline/sync status, duplicate-safe acknowledged retries, and human review of conflicting edits.
**Why:** A small synthetic-data exercise can test the core local-classroom and reconnect flow without pretending that unresolved security, account, conflict, or recovery decisions are settled.
**What was rejected:** Treating the planning assumption as a launched pilot; using passive signals as attendance; silently overwriting local records; or automatically disciplining/withdrawing learners.

## 2026-09-27, Research-informed hybrid sync recommendation (operator-confirmed)

**What was decided:** The operator confirmed the high-level direction: the site hub is authoritative for locally created class records and the cloud for remote-origin records. If the site's internet is down, the onsite class continues locally and remote users may use the cloud separately, but the platform must not claim they are in the same live room. Sync direction is a durable outbox, stable event IDs, acknowledgements, duplicate-safe retries, per-origin ordering, and human review of conflicts. This is not approval of code, schema, deployment, a real pilot, or real learner data.
**Why:** Official offline-learning references show local serving and syncing are feasible, while Moodle's documented limitations and CouchDB's documented conflict handling show offline activity timestamps and merge behavior need explicit application rules.
**What was rejected:** Assuming Supabase replication alone solves offline application sync, silently applying “winning” edits to attendance, or requiring disconnected sites to reach the cloud for each write.

## 2026-09-27, Offline sign-in recommendation (pending approval)

**What was decided:** No sign-in policy has been selected. Recommend individual accounts established before an outage, with the minimum active-class roster and protected credential-verification data available to the local hub. As a conservative first-pilot proposal, cached access would expire at the end of the scheduled class/day; after expiry, learners could read already-approved materials but could not create verified attendance records until access is refreshed. Failed sign-ins should be throttled; shared devices should use short, inactivity-limited sessions.
**Why:** A disconnected hub cannot learn immediately about a cloud-side account revocation. Limiting offline authorization reduces stale-access risk while allowing a class to finish.
**What was rejected:** Student ID alone, shared class passwords, QR codes alone, offline account enrollment/reset/role changes, and impersonating a learner who cannot sign in. At the time this recommendation was recorded, the device model was undecided; the operator later preferred learner-owned devices (see below). The expiry window, learner identity checks, recovery, and local revocation process remain undecided; this recommendation is not authorization to implement authentication or use real learner data.

## 2026-09-27, Learner-owned devices preferred

**What was decided:** The operator prefers learners to use the devices they own rather than depending on shared classroom devices. Treat BYOD as the default design direction, without assuming every learner has a suitable or charged device or selecting phones/tablets/computers, a browser/native app, or a fallback process.
**Why:** Learners should be able to access class resources on their own devices.
**What was rejected:** Making shared classroom devices the default. Accessibility fallback, supported device types, and secure offline session/cache behavior remain to be designed; this does not authorize implementation or a real pilot.

## 2026-09-27, Device-readiness reminders and school-device fallback

**What was decided:** Remind students to charge their own devices before class; use a school-provided device where available. At first, the cadence was left open; the operator later selected a weekly reminder (see below). Wording, day/time, and delivery channel remain open, and no live message is authorized.
**Why:** A charged personal device supports class participation, while school equipment can help when available.
**What was rejected:** Assuming every learner will always have a charged, working personal device, or treating this policy as permission for unsolicited or immediate messaging. Any future notice must follow the chosen channel's consent and opt-out rules.

## 2026-09-27, Weekly cadence selected for device-readiness reminders

**What was decided:** Send one device-readiness reminder weekly, asking learners to charge their devices for class and use a school-provided device where available.
**Why:** The operator prefers a less frequent reminder rather than a message before every class.
**What was rejected:** A reminder before every class. The exact day/time, wording, and channel remain undecided; this decision does not authorize sending messages or adding a channel.

## 2026-09-27, Add multi-channel device-readiness notices to Phase 2

**What was decided:** Add a separate weekly device-readiness notice to Phase 2, with the goal of reaching learners through approved student-facing channels including WhatsApp, email, SMS, and future approved channels. Preserve the Phase 1 WhatsApp daily reminder and Telegram backup unchanged. Use only channels each learner has opted into for this specific purpose.
**Why:** The operator wants reliable reach across current and future communication options, particularly email and SMS, without disrupting the existing automation.
**What was rejected:** Replacing or refactoring the Phase 1 reminder flow, blindly sending to every channel regardless of consent, or treating this scope change as permission to configure providers or send real messages. At the time this scope was recorded, channel preferences/fallback behavior were open; the operator later selected preferred-channel-first with fallback (see below). Provider/country rules, schedule details, audit, retry, and rate limits must be designed before implementation.

## 2026-09-27, Preferred channel with fallback selected for device notices

**What was decided:** Send the weekly device-readiness notice through the learner's preferred channel first, then use a permitted fallback only if needed. Do not send simultaneously on all channels. Fallback must be separately opted into for this notice and must never bypass an opt-out.
**Why:** The operator prefers a primary route with a backup rather than duplicate messages across every platform.
**What was rejected:** Simultaneous broadcasts to every channel. At the time, whether each student must select a preferred channel was open; the operator later required it (see below). The fallback-channel ranking was also open and is resolved in the next entry. Confirmed-failure criteria, wait period, and handling of uncertain delivery status remain open to prevent duplicates; this decision does not authorize provider setup or live sends.

## 2026-09-27, Students choose their preferred notice channel

**What was decided:** Each student must choose a preferred channel for the weekly device-readiness notice. Try that channel first, then use a permitted fallback if needed. The preference selection is separate from consent; require purpose-specific opt-in on every channel used, and do not send until both required preference and consent are recorded.
**Why:** The operator wants students to choose how they are contacted rather than having the system impose a default.
**What was rejected:** Assigning a default preferred channel or treating channel selection as consent. At first, fallback order was left open; the operator later required students to choose it (see below). Failure/unknown-status rules remain open; do not bypass opt-outs or send duplicate notices across channels.

## 2026-09-27, Students choose their fallback-channel order

**What was decided:** Each student chooses and ranks any opted-in fallback channels behind their preferred channel; attempts follow that order. No simultaneous cross-channel broadcast. Channel ranking does not replace separate consent for each channel.
**Why:** The operator wants students—not a system default—to decide the order in which their selected channels are tried.
**What was rejected:** A fixed system-wide fallback order. At the time, handling of uncertain delivery remained open; the operator later approved requiring confirmed failure before fallback (see below). This decision does not authorize provider setup or live sends.

## 2026-09-27, Confirmed failure required before channel fallback

**What was decided:** Try a student's next ranked, opted-in channel only after the current provider confirms a terminal delivery failure. Pending or unknown status is not failure and must not trigger fallback until the result is reconciled.
**Why:** Falling back while the first provider may still deliver could cause the student to receive duplicate reminders.
**What was rejected:** Treating a timeout, pending status, or ambiguous provider response as proof of failure. Provider-specific failure mapping, retry limits, and reconciliation timing remain to be designed; no provider integration or live send is authorized.

## 2026-09-27, Global audience with country-by-country channel approval

**What was decided:** The intended student audience is global. Treat this as a reach goal, not proof that every channel/provider works in every country. Review each destination for coverage, sender registration, cost, local messaging requirements, consent, and delivery-status reliability before enabling it. Preserve Phase 1 unchanged; no provider is selected.
**Why:** Official provider documentation shows international SMS sender rules and delivery receipts vary by country, while email providers require delivery and bounce/complaint operations.
**What was rejected:** Assuming one SMS sender/provider covers the world or automatically enabling worldwide routes. Provider comparisons should start once the first learner markets are known; no provider integration or live sending is authorized.

## 2026-09-28, Ghana selected for first channel-readiness review

**What was decided:** Ghana is the first market to assess for the global weekly device-readiness notice. This is not authorization to enable WhatsApp, SMS, email, any provider, a pilot, or live messages. Check local consent/privacy rules, the NCA's current international A2P position, network-specific sender registration, provider cost and delivery evidence before an implementation decision.
**Why:** The operator identified Ghana as the first learner market; official sources show opt-in and data-protection duties and evolving provider/regulatory SMS requirements.
**What was rejected:** Treating Ghana as automatically covered or treating one provider's routing notes as Ghana-wide legal approval.

## 2026-09-28, Ghana channel shortlist researched but not selected

**What was decided:** For the Ghana weekly notice, retain direct Meta Cloud API as the WhatsApp candidate already in the project, evaluate Amazon SES for low-cost email, and compare Twilio's published SMS rate against Vonage's account-specific rate table before any activation. Require a pre-approved SMS spend limit while preserving each student's channel choice and separate consent. This is research guidance, not a provider decision or permission to configure or send.
**Why:** Meta already serves the Phase 1 WhatsApp path; SES has low published per-email prices but has sandbox and setup requirements; Twilio's Ghana SMS per-segment rate is high and Vonage requires an account-specific quote.
**What was rejected:** Adding an unreviewed vendor, treating SMS as a default, or selecting a route solely on headline price. The existing WhatsApp sender uses a plain text request; verify approved-template support before scheduled messages outside the 24-hour service window.

## 2026-09-28, Cap first Phase 2 notice cohort at 30 paid learners

**What was decided:** The first cohort for the additive weekly device-readiness notice should be no more than 30 learners, with verified course payment required for eligibility. Keep the Phase 1 daily reminder system unchanged. Each learner still needs separate purpose- and channel-specific consent; payment is not consent. This is not authorization for real learner data or live messages.
**Why:** The operator wants to control initial costs and direct reminders to learners committed to a course.
**What was rejected:** Sending to all 500 prospective learners, changing Phase 1 reminder eligibility, or treating payment as permission to message.

## 2026-09-28, Use manual WhatsApp or a mock for a no-cost trial

**What was decided:** The free-to-download WhatsApp Business App is a possible manual one-to-one route for a small opted-in pilot; for local software tests, use a mocked/no-send channel. Neither is an automated Platform API integration, and Business Broadcast availability in Ghana is unconfirmed.
**Why:** It allows low-cost learning without unofficial WhatsApp Web automation or assuming that proactive API messages are free.
**What was rejected:** Describing the official WhatsApp Business Platform as free for scheduled proactive reminders, or automating WhatsApp Web.

## 2026-09-28, Manually verify payment for the first 30-learner cohort

**What was decided:** An administrator will manually verify course payment for the first cohort of up to 30 learners; do not add a checkout/payment provider now. Payment eligibility applies only to the new Phase 2 weekly notice and does not replace separate channel-specific consent. The record and audit design was resolved in the following decision; no live migration or send is authorized.
**Why:** Manual verification keeps the initial pilot simple and avoids introducing billing scope before the later payment phase.
**What was rejected:** Treating an active enrollment as proof of payment or adding a payment gateway before the billing phase.

## 2026-09-28, Store payment and channel consent as separate append-only events

**What was decided:** For the Phase 2 weekly notice, track payment verification/revocation per enrollment and opt-in/opt-out per learner, purpose, and channel in separate append-only event logs. The latest event controls current state; require an active enrollment, latest payment verification, and a current opt-in for each attempted channel. Keep these changes local until separately authorized migration; do not add a write endpoint until actor identity and learner consent capture are safe.
**Why:** Separate histories preserve auditability and withdrawals without treating payment or channel preference as consent.
**What was rejected:** One mutable paid flag, global consent, or inferring payment/consent from active enrollment.

## 2026-09-29, Use Supabase Auth identities for local Phase 2 notice recording

**What was decided:** For weekly device-readiness records only, locally implement server-verified Supabase Auth identities mapped to staff or one learner/student. Staff can verify/revoke payment and enter a learner's direct consent request; learners can update consent and an append-only ordered channel-preference snapshot only for their mapped student. The API derives actor/source and fails closed. An empty channel-order snapshot means no preference and never grants consent.
**Consent copy:** The API serves fixed sample version `device-readiness-v1` and assigns it to opt-ins rather than trusting a client-supplied version. This wording is not legal approval; review it for each market before real consent capture or sending.
**Why:** The shared operator API key cannot safely attribute actions to a person, and request-supplied student IDs could let a learner modify someone else's records.
**What was rejected:** Using the shared key as an audit actor, letting clients supply actor IDs, combining preference with consent, or treating online notice authentication as offline class-platform sign-in.
**Boundary:** Build/test with fake accounts locally only. No sign-up, role-management endpoint, login UI, live migration, real data, attendance API, message provider, send, push, or deployment is authorized. The memory CLI is unavailable in this PowerShell environment; continue maintaining this repository `memory.md`.

## 2026-09-30, Harden Phase 1 job idempotency and safe messaging

**What was decided:** Require a database unique constraint for daily engagement upserts and a deterministic unique send key per learner/enrollment/date or administrator-report/date, written before provider calls. Do not send on key conflicts or log-write failures; expose uncertain `pending` outcomes in the report. The manual run route must also build and send the administrator report.
**Why:** A process-local lock and check-before-send query do not prevent concurrent workers from racing, and the current report hides pending outcomes.
**What was rejected:** Assuming one server process forever, retrying an uncertain delivery automatically, or treating HTTP acceptance as proof of final delivery.

**WhatsApp safeguard:** Scheduled reminders must use a configured approved template and an explicitly configured supported Graph API version; free-form text is unsafe because the scheduler cannot verify the recipient's 24-hour window. Do not send a student-specific reminder to the administrator's Telegram chat.
**Boundary:** Implement only local schema/code/tests. No live migration, provider account/API call, recipient send, push, or deploy. The currently observed Git `origin` is a local Desktop path rather than the selected GitHub repository, so do not push to it.

## 2026-09-30, Keep learner and administrator delivery separated

**What was decided:** WhatsApp is the only Phase 1 learner-reminder channel. The configured Telegram chat belongs to the administrator and is used only for reports; reject any attempt to send a learner-specific reminder there. Treat timeouts, server errors, or provider responses without a message ID as unknown/pending, never as permission to retry or fall back.
**Why:** The system must not expose a learner's private reminder to the administrator or create duplicates after uncertain delivery.
**What was rejected:** Telegram as an assumed learner backup, and treating a failed network response as proof the provider did not accept the message.

## 2026-09-30, Frontend is on a divergent local branch

**What was found:** The Next.js frontend exists in the sibling local `main` worktree, which is seven commits ahead of the configured local `origin`; it is absent from the Phase 2 branch and from GitHub's canonical repository `main`. That local branch also restructures the backend under `backend/` and differs by many backend/docs files, so merging it wholesale would risk losing Phase 2 work.
**Integration blockers:** The frontend expects `students` and `courses` arrays that the current report API does not return. It calls admin-protected endpoints without authentication; putting `ADMIN_API_KEY` in browser-visible configuration would expose it. Do not copy/merge/deploy the UI until the exact files and a safe admin-auth approach are agreed.
**What was rejected:** Merging all of local `main` just to retrieve the frontend, or exposing the shared admin key to browser JavaScript.

## 2026-09-30, Design staff sign-in before implementation

**What was decided:** The user chose to design the staff sign-in flow first. This is design-only approval; no frontend/backend auth changes, dependency installation, live schema change, external account setup, push, or deployment is approved yet.
**Proposed direction, pending review:** Use Supabase Auth for pre-created staff identities, a same-origin Next.js server route to relay authenticated requests, and backend verification of the Supabase identity plus the existing staff role mapping. Never expose the shared admin key or Supabase server secret in browser code. Confirm compatibility with the repo's Next.js version and the current Supabase SSR package status before implementation.
**Why:** Existing dashboard calls are unauthenticated, while the API requires a shared admin key; sending that key from the browser would disclose it.
**What was rejected:** Treating the proposed technical design as already approved, putting a long-lived admin credential in frontend configuration, or making public staff sign-up/role assignment.

## 2026-10-07, QR opens the owned learning platform

**What was decided:** The operator approved a narrow local-only public `/learn` entry page and `/qr` page. The QR contains only the absolute `/learn` URL from the app's current origin; it does not authenticate, enroll, check attendance, connect social accounts, or contain personal data or credentials. Use `qrcode.react` to render it locally as SVG, not an external QR service.
**Why:** This offers a single easy link into the owned platform without pretending that one QR can integrate with every social-media account.
**What was rejected:** A universal cross-platform login QR, a QR containing bearer credentials, or sending QR contents to a third-party generator.
**Boundary:** Only this static public entry milestone is approved. The app must be reachable from the device scanning it; `localhost` is computer-only, a classroom LAN address is local-network-only, and global access requires a stable public HTTPS deployment. Deployment, course catalog, learner login/data, attendance, payments, and social connectors are not approved in this step.

## 2026-10-07, Implement and verify the local public QR entry preview

**What was decided:** Add a separate root `frontend/` Next.js app with `/learn` and `/qr`; generate the QR locally from the current site origin and provide a PNG download. Keep the page transparent that courses and classroom features are not available yet. The implementation uses Next.js 16.4.0 and `qrcode.react` 4.2.0.
**Why:** This completes the approved QR entry milestone without merging the unrelated, divergent admin dashboard or changing the reminder backend.
**What was rejected:** Exposing authentication or learner data in a QR, using a third-party QR image service, modifying Phase 1 reminders, or deploying before a stable public URL and separate authorization.
**Verification and handoff:** `npm install` completed with zero reported vulnerabilities; `npm run build` passed and generated `/`, `/learn`, and `/qr`; local HTTP smoke tests returned 200 for all three. Documentation commit: `686a331`; implementation commit: `7547e77`. Neither commit has been pushed.

## 2026-10-10, Public QR production deploy and PNG format

**What was decided:** The operator authorized production deployment of only the existing public frontend routes (`/`, `/learn`, `/qr`) to Vercel. The operator also confirmed PNG as the QR download format for cross-platform social sharing. Keep the backend, live database, real learner data, messaging, and later phases out of this deployment.
**Why:** A stable public HTTPS URL is needed for the reusable QR, and PNG is convenient to share on social platforms.
**What was rejected:** Publishing the backend or learner data, making live database changes, or replacing the PNG download with SVG-only output.

## 2026-10-10, Progress audit baseline

**Status:** The active `feat/phase-2-attendance` worktree was clean before this audit. Baseline checks: backend `68 passed, 1 Starlette/httpx deprecation warning`; frontend `npm run build` passed and prerendered `/`, `/learn`, and `/qr`. The production server returned `/learn` 200, `/qr` 200, root 307 to `/learn`, and unknown route 404. The QR rendered and the narrow viewport had no horizontal overflow. The Codex in-app browser did not surface a PNG download event, so download behavior still needs verification in a normal browser; this is not proof that a user-facing browser download fails.
**Deployment setup at audit start:** The Vercel CLI and project link were absent, and no `VERCEL_TOKEN` environment variable was set. The CLI could not access its standard settings folder until narrow filesystem permission was granted; it then authenticated successfully. See the deployment completion below.

## 2026-10-10, QR audit completion

**Changes:** Replaced deprecated `qrcode.react` `includeMargin` with `marginSize={4}` and attached the temporary PNG download link to the document before clicking it, then removed it.
**Verification:** Backend: `68 passed, 1 warning`. Frontend: final `npm run build` passed and prerendered `/`, `/learn`, and `/qr`; `npm audit` found 0 vulnerabilities. Vercel preview and production builds passed. Production smoke test: `/learn` 200, `/qr` 200, `/` 307 to `/learn`; Vercel's production error-log query returned no logs. The live `/qr` DOM contains a canvas, PNG button, and `https://globallearninghub.vercel.app/learn` link. The root `git diff --check` passed.
**Unverified limitation:** The Codex in-app browser emitted no download event and the local Downloads file timestamp did not change after clicking. Do not overwrite or infer the existing Downloads file; manually test PNG saving in a regular browser before claiming that behavior is verified.
**Deployment status:** The official Vercel CLI was fetched into a temporary cache. After listing the account's projects, the existing exact-name `global_learning_hub` project was linked to `frontend/`. Its “Other” preset and `public` output expectation caused an initial preview build failure; changing only the framework preset to Next.js fixed it. Both preview and production builds passed. Production is live at <https://globallearninghub.vercel.app>; public checks returned `/learn` 200, `/qr` 200, and `/` 307 to `/learn`. A production error-log query returned no logs. The preview is protected by Vercel authentication, as expected.
**Deployment boundary:** Only the static public-entry frontend was deployed. No backend, live database, real learner data, or messaging was included. Vercel's generated local `.env.local` contains CLI authentication state and is ignored by Git; do not read, print, stage, or commit it.

## 2026-10-10, Production public QR deployment

**What was decided:** Deploy only the public entry pages to the existing Vercel project `global_learning_hub`; make Next.js the project's detected framework and use automatic build/output settings.
**Why:** The initial Vercel build failed because the project was configured as “Other” and expected a `public` folder even though this app builds as Next.js.
**What was rejected:** Creating another project, changing domains or environment variables, deploying the backend/data, or publishing classroom features.
**Result:** Production deployment is READY at <https://globallearninghub.vercel.app>. `/learn` and `/qr` return HTTP 200; `/` redirects to `/learn`; no production errors were found in the last-five-minute log query. The QR canvas and PNG button are present in the live page DOM, and its QR URL uses the stable HTTPS production origin. PNG download was not confirmed through the Codex in-app browser; that browser did not emit a download event on the local preview. Confirm manually in a regular browser.

## 2026-10-10, GitHub branch handoff

**What was decided:** Point the active worktree's `origin` to `https://github.com/davAmen/Global-Learning-Hub-Automations.git` and publish only `feat/phase-2-attendance`; keep `main` and the original local worktree unchanged.
**Why:** The previous `origin` pointed to a local Desktop folder, so a push could not reach the selected GitHub repository.
**What was rejected:** Pushing to the old Desktop-folder remote, force-pushing, or merging the feature branch into `main`.
**Status:** Commit `7c8323b` is local and the GitHub repository is reachable with OpenSSL, but the push is waiting for GitHub authentication. No credential or private information was written to the repository.
