# DECISIONS.md
### Decisions already made for this project -- do not reopen without explicit human instruction

This file exists because an AI agent has no memory between sessions. Each entry below was decided deliberately, often after considering and rejecting an alternative. If a future session (yours or another agent's) is tempted to suggest something that contradicts an entry here, that is a sign to re-read this file, not a sign the earlier decision was missed by accident.

When a new decision is made during this project, add it to this file in the same format. Do not delete old entries, even superseded ones -- mark them superseded instead, so the history of *why* is preserved.

---

### Data storage: Supabase only, not Google Sheets
**Decided:** Supabase (Postgres) is the single source of truth for all student, course, enrollment, and log data.
**Why:** An earlier draft of this project considered syncing data to Google Sheets alongside a database. This was rejected -- two sources of truth create sync bugs and confusion about which is authoritative. If a human-editable view is needed, Supabase's own table editor serves that purpose without a second data store.
**Scope status (2026-09-27):** This remains the Phase 1 reminder service's data-store decision. It does not yet define how a future hybrid classroom platform can accept local writes during internet outages; do not silently add a local database or assume Supabase alone satisfies offline operation. The local/cloud authority and sync model must be decided before schema changes for that platform.

### Backend framework: FastAPI, not plain scripts
**Decided:** The backend is a FastAPI application, not a standalone script triggered only by cron.
**Why:** FastAPI provides an API surface needed for: a manual trigger endpoint, receiving delivery-status webhooks from the SMS/email/WhatsApp provider, and a `/reports/today` endpoint the frontend can call. A plain script cannot receive incoming webhooks.

### Frontend: added deliberately, kept minimal
**Decided:** A simple Next.js frontend exists, calling the FastAPI backend. It is read-mostly -- the only write action is a single "run job now" button.
**Why:** Added so the non-technical project owner can see and interact with what's being built, for learning and confidence -- not for end-user polish. This reverses an earlier plan to exclude a frontend entirely from Phase 1; the reversal is intentional and the minimal scope is the safeguard against it growing into a full admin product.
**Guardrail:** Do not add editing/write screens beyond the run-job button without this file being updated first.

### Delivery channel: WhatsApp (active), Telegram (backup)
**Decided (2026-09-18):** Phase 1 sends reminders via WhatsApp Business Cloud API as the primary channel. Telegram Bot API is the backup/secondary channel for when WhatsApp is blocked or unavailable. Email and SMS are supported by the channel-adapter interface but not wired/active in Phase 1.
**Why:** The operator (David) chose WhatsApp as the main lesson-delivery channel because students already use it. Telegram is the operator's own backup virtual class (@DavidAmenuku20) in case WhatsApp blocks the automation. Email was briefly considered then superseded by this decision.
**What was rejected:** Email as active channel (superseded). SMS as primary (not chosen). Multi-channel in Phase 1 (rejected -- too much for a first build).
**Status:** WhatsApp = ACTIVE_CHANNEL, Telegram = BACKUP_CHANNEL. Update this entry if the operator changes direction.

### Scope: Phase 1 is ONE automation only
**Decided:** This build is limited to the reminder/engagement automation described in `ARCHITECTURE.md`. Onboarding automation, course detection, engagement scoring beyond three basic states, and the AI operations assistant (from the original project vision) are all explicitly deferred.
**Why:** The original project document described a multi-phase platform requiring a funded team over a year. Attempting more than one automation in the first month risks finishing nothing. Later phases will be scoped separately, after Phase 1 is proven.

### Real data: not used until Week 3's controlled pilot
**Decided:** All development and testing before Week 3 uses `scripts/seed_sample_data.py` fake data. Real student contact information is not used until explicit authorization.
**Why:** Protects real students from bugs in an untested system, and is a data-privacy boundary, not just a convenience.

### Git identity: davAmen
**Decided (2026-09-18):** Local commits are authored as `davAmen` (the operator's GitHub username). Push to GitHub under the `davAmen` account.
**Why:** Operator's explicit instruction.

### ARCHITECTURE.md is the living spec
**Decided (2026-09-18):** ARCHITECTURE.md and DECISIONS.md are the live source of truth. They must be updated BEFORE code changes are made when a decision changes. The operator explicitly requested this.
**Why:** Prevents silent drift between what's decided and what's built.

### Platform expansion requested (2026-09-25)
**Decided:** The operator requests a public learning platform with a website, learner portal, affordable courses, admission workflow, feedback review, AI-supported course drafting, and a human tutor option. The original Phase 1 reminder service remains a component. The earlier Phase 1 scope boundary is superseded for planning and incremental implementation by this explicit request.
**Safeguards:** A displayed price or mock checkout is not a payment. Admission letters and seats are issued only after verified server-side payment confirmation. AI course drafts and service changes require human approval before publication. Hiring depends on an approved budget and human decision. No real student data or live sends are authorized by this request.

### Additional roadmap scope and phase gates (2026-09-26)
**Decided:** The operator additionally requests consent-based class attendance, transparent participation and assignment evidence, an AI class-operations assistant, ethical lead generation and marketing, and partner/sponsor outreach. `MASTER_PROMPT.md` integrates these goals with the existing `PLATFORM_BRIEF.md` in sequential, independently approved phases. Phase 1 remains the active product implementation until a later phase is explicitly activated.
**Safeguards:** Attendance and learning activity are distinct. Four consecutive absences trigger supportive contact and human review, never automatic withdrawal. Do not use covert camera, microphone, biometric, location, or device monitoring. AI may recommend high-impact actions but a human decides. Channel-specific consent, opt-outs, rate limits, and current provider policies apply. No scraping personal data, unsolicited messaging, live payments, external publication, advertising spend, partnerships, deployment, or production changes without the required explicit approval.
**What was rejected:** Building every requested feature in one change; treating the roadmap as authorization for live operations; AI-only discipline decisions; covert surveillance; spam or privacy-invasive lead generation; automatic production self-modification.

### Log administrator report delivery attempts in the existing audit table (2026-09-26)
**Decided:** Record each administrator report send attempt in `reminder_log` before sending and update its status afterward. Use a null `enrollment_id` to distinguish report-level attempts from student reminders; report queries must exclude those rows from student reminder totals.
**Why:** The Phase 1 rules require every send attempt to be auditable, and an administrator report is not tied to one enrollment. Reusing the existing table avoids adding a second source of truth.
**Safeguard:** Update the schema specification only. Do not migrate or otherwise change a live database without separate explicit authorization. If the deployed schema still requires `enrollment_id`, fail closed and do not send an unlogged report.
**What was rejected:** Leaving administrator sends unlogged, assigning them to a fake student enrollment, or introducing another audit table.

### Phase 2 attendance source and login gate (2026-09-27) — superseded in part
**Originally decided:** No class-platform integration was selected; use a visible, learner-initiated check-in only after verified learner login exists, with auditable teacher corrections.
**Status:** The no-platform choice was superseded by the operator's request for an owned local-and-remote class platform. Verified identity, notice/consent, and auditable teacher corrections remain required.
**Why:** The selected repository has no class-platform integration, learner authentication, or attendance model. Accepting a student ID alone could allow someone to record attendance for another learner.
**What was rejected:** Covert sensing, attendance inferred from online/read status, and public check-ins that trust an unverified student ID.
**Still to define before schema/API changes:** Session/timezone rules, late/partial/excused attendance, source and correction audit details, learner notice/consent, retention, and implementation details for local/cloud data ownership and sync. Four consecutive absences may result in supportive contact and human review only, never automatic course withdrawal.

### Phase 2 class-platform deployment model (2026-09-27)
**Approved high-level sync model (operator-confirmed 2026-09-27):** Keep site-origin classroom records under the local hub's authority and remote-origin records under the cloud service's authority. During a site WAN outage, the local class continues on LAN and remote users may continue on the cloud separately, but they are not in the same live room. For reconnect, use a durable app-level outbox with stable event IDs, acknowledgements, idempotent retry, per-origin ordering, and teacher-reviewed amendments/conflicts. This approval does not select a database/vendor or authorize code, a real pilot, real learner data, or deployment; see docs/ARCHITECTURE.md for implementation details that remain open.
**Proposed first-pilot workflow — not approved:** For planning only, start with one site and one class, synthetic accounts/data, explicit learner check-in, separate assignment evidence, and teacher-audited corrections. Proposed reconnect safeguards are visible pending/failed status, stable event identity, acknowledgement before clearing local pending records, duplicate-safe retries, preserved history, and human review of conflicting edits. This does not authorize a real pilot or settle the storage, API, or authentication design.
**Decided:** Build toward an owned hybrid class platform: local classroom use over a local network during internet outages, plus remote access when internet or another approved network path is available. The operator selected this model after considering local-only and remote-connected alternatives.
**Why:** It preserves local classroom operation during outages while allowing learners and organizations elsewhere to connect when online.
**What was rejected:** A permanently isolated system as the sole model, and WhatsApp group management as the classroom platform. Keep the existing Phase 1 WhatsApp reminder channel unchanged.
**Local record authority decided:** Each site's local hub is the authoritative record keeper for class records created at that site during an outage. It syncs those records to the online service when connectivity returns. No silent cloud overwrite of those locally authoritative records.
**Still unresolved:** exact local storage and cloud deployment; event payload/schema and transport security; offline credential provisioning, freshness/expiry and recovery; session/timezone/attendance states; consent/notice/retention; correction workflow and audit; backup/restore and hub operations. The high-level origin ownership/outbox direction is approved above. No schema/API/UI, live pilot, real data, or deployment is authorized until remaining decisions are documented and approved.

**Device direction (operator-confirmed 2026-09-27):** Learners should use devices they own rather than depending on shared classroom devices. Treat this as a BYOD preference; exact device types, browser/app approach, and fallback access for a learner without a suitable or powered device remain undecided. This does not authorize a pilot or select an implementation.

**Device-readiness policy (operator-confirmed 2026-09-27):** Send one weekly reminder asking students to have their personal devices charged for class; where available, a school-provided device is an alternative.

**Additive Phase 2 channel scope (operator-confirmed 2026-09-27):** The weekly device-readiness notice should reach learners across approved student-facing channels, including WhatsApp, email, SMS, and future approved channels. This does not change Phase 1: its daily reminder still uses WhatsApp as `ACTIVE_CHANNEL` and Telegram as its backup. Send only through channels the learner separately opted into for this specific purpose. Provider selection, the day/time and wording, local requirements by country, consent/preferences, logging, retry/idempotency, and rate limits remain unresolved. This authorizes scope and staged design only—not provider integration, code changes, live sends, a pilot, or real learner data. Any future channel must be separately reviewed and approved before activation.

**Delivery strategy (operator-confirmed 2026-09-27):** Each student must choose a preferred channel and rank any fallback channels; try them in the student's chosen order. Do not send simultaneously to every channel. Choosing or ranking channels is not consent: require separate opt-in for this purpose on every channel used, and do not send until required preference and consent are recorded. Never use fallback to bypass an opt-out. Only a provider-confirmed terminal failure permits trying the next opted-in channel; pending or unknown delivery status does not. Provider-specific failure mapping, retry/timeout limits, and reconciliation rules remain to be defined.

**Audience reach (operator-confirmed 2026-09-27; first market specified 2026-09-28):** The intended audience is global, and Ghana is the first country for readiness review. This is a reach goal, not blanket approval or proof of service in every country. Maintain country-by-country checks for channel support, sender registration, prices, local messaging requirements, consent, and delivery-status reliability. Ghana is not an enabled delivery route: provider selection, current NCA international A2P status, sender registration, DPC/privacy obligations, and delivery evidence remain to be verified. Do not enable a country or channel until reviewed. This does not change Phase 1 or authorize worldwide sending.

**Ghana provider review (research recommendation, 2026-09-28; no operator selection):** Keep direct Meta Cloud API as the WhatsApp candidate already present in Phase 1, assess Amazon SES as the low-cost email candidate, and compare Twilio's published SMS rate with Vonage's account-specific rate table before enabling SMS. SMS needs a spend limit because Twilio's public Ghana rate is high per segment; student choice and separate consent still determine whether it may be used for an individual. No account setup, credentials, provider integration, code change, or live send is authorized by this comparison. The existing WhatsApp plain-text request needs approved-template handling verified for scheduled business-initiated messages outside Meta's 24-hour window before live sending.

### Phase 2 first-cohort limit and paid eligibility (2026-09-28)
**Decided:** Target no more than 30 learners in the first cohort for the additive Phase 2 weekly device-readiness notice. Only learners with verified payment for a course are eligible for that notice. Preserve the Phase 1 daily reminder flow unchanged. Require separate opt-in for the notice on each selected channel; payment and channel choice do not imply consent.
**Why:** The operator wants to control initial messaging costs and reserve reminders for learners who have committed to a course.
**What was rejected:** Expanding the first cohort to all 500 prospective learners, sending to unpaid prospects, changing Phase 1 eligibility, or treating payment as messaging consent.
**Still unresolved:** Before any real learner use, authorize a controlled pilot and establish a secure, attributable record-entry process. The append-only local schema design is documented below but has not been applied to live Supabase. Do not infer payment from an active enrollment. This cohort cap is not authorization for live messaging.

### No-cost WhatsApp trial path (research recommendation, 2026-09-28; not selected)
**Recommendation:** For the first small cohort, consider manually sending private one-to-one messages through the free-to-download WhatsApp Business App to learners who separately opted in. For local software testing, use a mocked/no-send channel. Neither option is an automated WhatsApp integration; verify Ghana availability before relying on Business Broadcasts. Treat any proactive Platform API notice as potentially billable and policy-gated.
**Why:** It avoids unofficial WhatsApp automation and API message fees during early learning/testing while keeping the established channel.
**What was rejected:** Calling the official Platform API free, automating WhatsApp Web, or sending to a group that exposes student phone numbers without a reviewed privacy design.

### Manual payment verification for the first cohort (2026-09-28)
**Decided:** For the first cohort of up to 30 learners, an administrator will manually verify course payment; no payment processor or checkout is added in this phase. Only manually verified paid enrollments may qualify for the Phase 2 readiness notice, and they still require separate channel-specific consent.
**Why:** This is the lowest-complexity way to apply the paid-only rule to a small cohort without introducing billing scope prematurely.
**What was rejected:** Adding a payment provider now, waiting for checkout to exist before testing eligibility, or treating an active enrollment as proof of payment.
**Still unresolved:** No live schema change or migration is authorized by this decision.

### Append-only payment and channel-consent records for the Phase 2 notice (2026-09-28)
**Decided:** In the local schema, record manual payment verification as append-only `verified`/`revoked` events tied to an enrollment. Record channel consent as append-only `opt_in`/`opt_out` events tied to a student, the fixed `device_readiness_weekly` purpose, and one channel. Include database event order/time and the recording actor; opt-in also includes a notice-text version and whether it came directly from the learner or was entered by staff from the learner's direct request. Store no payment amount/reference, receipt, or contact details in these logs. The newest event for a key determines current state; a revoked payment or opted-out channel fails closed. Eligibility additionally requires an active enrollment.
**Why:** Separate histories preserve corrections and withdrawals without conflating enrollment, payment, channel choice, and consent. Data minimization avoids retaining unnecessary financial or contact data.
**What was rejected:** A single mutable `paid` flag, one global consent flag for all channels, inferring payment from an active enrollment, or treating channel preference as consent.
**Access boundary:** The local SQL definition enables RLS, gives no direct `anon`/`authenticated` access, and grants only `SELECT`/`INSERT` to the server-side Supabase `service_role`. No write API is added because the current shared admin key does not identify an individual staff actor and learner consent capture is not implemented. Student channel preference/fallback order remains a separate open record. The schema edit is not a live migration; no live learner records or messages are authorized.
**Status:** The no-write-API boundary in this decision was superseded for local weekly-notice recording by the later Supabase Auth decision below. It remains true that this schema has not been migrated live.

### Supabase Auth identities for local Phase 2 notice recording (2026-09-29)
**Decided:** For the Phase 2 weekly device-readiness notice only, use individual Supabase Auth identities for backend writes. The API validates the presented access token with Supabase Auth `get_user(jwt)`, then reads a server-managed profile mapping the auth UUID to `staff` or to one learner/student. Payment verification and revocation are staff-only. Learners can record consent and preferred/fallback order only for their own mapped student; staff can record a learner's direct request using the explicit `learner_direct_request` source. The API derives `recorded_by` and consent source; neither can be chosen in a request body. Missing identity/profile, bad tokens, or unavailable auth/database services fail closed.
**Preference record:** Store each learner's complete channel order as a separate append-only snapshot for `device_readiness_weekly`; an empty list clears the preference and cannot authorize sending. Channel choice remains independent from each channel's opt-in/opt-out event. The existing append-only consent and payment event histories remain authoritative.
**Consent copy:** The local API serves the sample notice as fixed version `device-readiness-v1` and sets that version itself on opt-in events. The copy must be shown for the exact channel before the learner acts. This draft is not legal approval for Ghana or other countries; review appropriate wording before any real learner consent capture or messages.
**Scope/access boundary:** Implement and test routes locally with fake identities/data only. Keep the Phase 1 `ADMIN_API_KEY` routes unchanged. Do not add self-signup, role/profile assignment endpoints, a login UI, attendance access, offline class-platform authentication, any provider/scheduler/send path, or use real accounts/data. Supabase profile rows require trusted provisioning after separate authorization. This decision does not authorize a live Supabase migration, real pilot, message, push, or deployment.
**Why:** A verified account identity lets the server attribute actions to the person who authenticated, while restricting learner actions to their linked record. Append-only preference snapshots preserve the learner's chosen order without conflating it with consent.
**What was rejected:** Treating the shared admin key or a request-supplied actor/student ID as personal identity; letting learner accounts verify payment or write another learner's consent; writing directly from `anon`/`authenticated`; treating a selected channel as permission to message; or using this online notice auth as the class platform's offline sign-in solution.

**Offline sign-in proposal — pending operator approval:** Establish individual accounts before an outage and provision only the active class roster and protected credential-verification data to the local hub. For a first pilot, consider limiting verified offline access to the scheduled class/day; after expiry, approved materials may remain read-only, but new verified attendance writes stop until access is refreshed. Throttle failed sign-ins and use clear sign-out and risk-appropriate session limits even on personal devices, which may be shared within a household. A disconnected hub cannot immediately learn of a cloud-side account revocation, so the proposed expiry limits stale access. The expiry window, identity checks, recovery flow, and local revocation process remain undecided. This proposal does not authorize authentication implementation or real learner data.
