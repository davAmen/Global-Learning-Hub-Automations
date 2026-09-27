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
