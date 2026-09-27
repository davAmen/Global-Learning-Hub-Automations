# DECISIONS.md
### Decisions already made for this project -- do not reopen without explicit human instruction

This file exists because an AI agent has no memory between sessions. Each entry below was decided deliberately, often after considering and rejecting an alternative. If a future session (yours or another agent's) is tempted to suggest something that contradicts an entry here, that is a sign to re-read this file, not a sign the earlier decision was missed by accident.

When a new decision is made during this project, add it to this file in the same format. Do not delete old entries, even superseded ones -- mark them superseded instead, so the history of *why* is preserved.

---

### Data storage: Supabase only, not Google Sheets
**Decided:** Supabase (Postgres) is the single source of truth for all student, course, enrollment, and log data.
**Why:** An earlier draft of this project considered syncing data to Google Sheets alongside a database. This was rejected -- two sources of truth create sync bugs and confusion about which is authoritative. If a human-editable view is needed, Supabase's own table editor serves that purpose without a second data store.

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
